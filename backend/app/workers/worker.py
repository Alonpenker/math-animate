from celery import Celery
from celery.signals import worker_process_init, worker_process_shutdown, worker_ready, setup_logging
from pathlib import Path
from uuid import UUID, uuid4
import tempfile
import shutil
import subprocess
import os
import time
from concurrent.futures import ThreadPoolExecutor
from enum import StrEnum
from typing import Annotated, TypedDict
from psycopg2.errors import UniqueViolation
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from pydantic import BaseModel

from app.configs.app_settings import settings
from app.configs.llm_settings import (
    CODEGEN_SYSTEM_PROMPT,
    LLM_PROVIDER,
    LLM_CODEGEN_OUTPUT_MAX_TOKENS,
    LLM_CODE_MODEL,
    LLM_PLAN_MODEL,
    LLM_REASONING_EFFORT
)
from app.workers.worker_settings import (
    PathNames,
    DockerCommands,
    RENDER_TIMEOUT_SECONDS,
    SQS_VISIBILITY_TIMEOUT,
    SQS_POLLING_INTERVAL,
    MAX_FIX_ATTEMPTS,
)
from app.dependencies.db import init_db_pool, close_db_pool, get_worker_cursor
from app.dependencies.redis_client import init_redis_pool, close_redis_pool
from app.dependencies.storage import init_storage
from app.domain.job_state import JobStatus
from app.exceptions.llm_usage_exception import LLMUsageException
from app.exceptions.quota_exceeded_error import QuotaExceededError
from app.llm_knowledge.skill_documents import (
    CORE_DOCUMENTS,
    LLMKNOWLEDGE_DIR,
    REGISTRY,
    REGISTRY_BY_ID,
    read_knowledge_file,
)
from app.repositories.knowledge_repository import KnowledgeRepository
from app.repositories.plans_repository import PlansRepository
from app.repositories.artifacts_repository import ArtifactsRepository
from app.schemas.jobs import (
    Job,
    JobCodeRequest,
    JobFixRequest,
    JobPlanRequest,
    JobRequest,
    JobUserRequest,
)
from app.schemas.artifact import ArtifactType
from app.schemas.knowledge import KnowledgeDocumentSeed
from app.schemas.video_plan import VideoPlan
from app.services.llm_service import CallType, LLMService
from app.services.rag_service import RAGService
from app.services.skill_retrieval_service import SkillRetrievalService
from app.workers.worker_helpers import (
    transition_job,
    reserve_budget,
    reconcile_budget,
    release_budget_on_error,
    get_storage,
    save_artifact_to_storage,
    store_render_logs,
    dry_run_docker,
    summarize_verification_failure,
)
from app.utils.llm_stubs import IS_E2E_MODE
from app.utils.logging import Logger, WorkerLog
from app.utils.seq_processor import SeqProcessor

app = Celery('mathanimate-worker',
             broker=settings.broker_url,
             backend=settings.redis_url)

if settings.environment == "prod":
    app.conf.update(
        broker_transport_options={
            'region': settings.aws_region,
            'visibility_timeout': SQS_VISIBILITY_TIMEOUT,
            'polling_interval': SQS_POLLING_INTERVAL,
            'predefined_queues': {
                'celery': {
                    'url': settings.sqs_queue_url,
                }
            }
        },
        task_default_queue='celery',
    )

logger = Logger.get_logger("worker")

if IS_E2E_MODE:
    logger.warning(WorkerLog(
        operation="e2e_mode",
        event="E2E mode enabled - LLM calls will be stubbed",
    ))


OPENROUTER_MODEL = "poolside/laguna-m.1:free"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class NodesNames(StrEnum):
    DOCUMENT_SELECTION = "document_selection"
    LOAD_SELECTED_DOCUMENTS = "load_selected_documents"
    GENERATE_CODE = "generate_code"
    VERIFY = "verify"
    FIX_CODE = "fix_code"
    SAVE_AND_RENDER = "save_and_render"
    FAIL = "fail"

    @classmethod
    def non_loop_nodes(cls) -> tuple["NodesNames", ...]:
        return (
            cls.DOCUMENT_SELECTION,
            cls.LOAD_SELECTED_DOCUMENTS,
            cls.GENERATE_CODE,
            cls.VERIFY,
            cls.SAVE_AND_RENDER,
            cls.FAIL,
        )

    @classmethod
    def loop_nodes_per_fix_attempt(cls) -> tuple["NodesNames", ...]:
        return (
            cls.FIX_CODE,
            cls.VERIFY,
        )


class SelectedSkillDocuments(BaseModel):
    selected_titles: list[str]


class LangGraphCodegenState(TypedDict):
    job_id: UUID
    plan: VideoPlan
    messages: Annotated[list[BaseMessage], add_messages]
    code: str
    verification_failure: str
    fix_attempt: int
    verification_fixable: bool


def _get_openrouter_client() -> ChatOpenAI:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "OPENROUTER_API_KEY is not set. "
            "Set it in the backend .env or process environment to use the LangGraph workflow."
        )
    return ChatOpenAI(
        model=OPENROUTER_MODEL,
        base_url=OPENROUTER_BASE_URL,
        api_key=api_key,
        max_tokens=LLM_CODEGEN_OUTPUT_MAX_TOKENS,
        extra_body={
            "reasoning": {
                "effort": LLM_REASONING_EFFORT.HIGH.value
            }
        }
    )


def route_after_verify(state: LangGraphCodegenState) -> str:
    if not state["verification_failure"]:
        return NodesNames.SAVE_AND_RENDER
    if not state["verification_fixable"]:
        return NodesNames.FAIL
    if state["fix_attempt"] >= MAX_FIX_ATTEMPTS:
        return NodesNames.FAIL
    return NodesNames.FIX_CODE


@setup_logging.connect
def _suppress_celery_logging(**kwargs):
    pass  # prevent Celery from overwriting structlog configuration


@worker_process_init.connect
def init_worker(**kwargs) -> None:
    SeqProcessor._executor = ThreadPoolExecutor(max_workers=1)
    init_storage()
    init_db_pool()
    init_redis_pool()


@worker_ready.connect
def on_worker_ready(**kwargs) -> None:
    init_db_pool()
    try:
        seed_knowledge()
    except Exception:
        logger.warning(WorkerLog(
            operation="seed_knowledge",
            event="Knowledge auto-seed on startup failed; worker will continue",
        ), exc_info=True)
    finally:
        close_db_pool()


@worker_process_shutdown.connect
def shutdown_worker(**kwargs) -> None:
    close_db_pool()
    close_redis_pool()


@app.task()
def generate_plan(job_request_payload: dict) -> None:
    try:
        job_request = JobUserRequest(**job_request_payload)
    except Exception as exc:
        logger.error(WorkerLog(
            operation="generate_plan",
            event="Invalid request payload",
            error=Logger.serialize_error(exc),
        ), exc_info=exc)
        raise

    job_id = job_request.job.job_id
    call_id = uuid4()
    reserved = 0
    total_tokens = 0

    try:
        logger.info(WorkerLog(
            operation="generate_plan",
            event="Planning started",
            job_id=str(job_id),
            call_id=str(call_id),
        ))
        transition_job(job_id, job_request.job.status, JobStatus.PLANNING)

        system_prompt, user_query = LLMService.render_plan_prompt(job_request.user_request)
        reserved = reserve_budget(
            call_id, job_id, JobStatus.PLANNING, LLM_PLAN_MODEL,
            f"{system_prompt}\n{user_query}",
            operation="generate_plan",
        )

        plan, total_tokens = LLMService.plan_call(system_prompt, user_query)
        reconcile_budget(call_id, total_tokens, reserved, operation="generate_plan")

        with get_worker_cursor() as cursor:
            PlansRepository.create_plan(cursor, job_id, plan)

        transition_job(job_id, JobStatus.PLANNING, JobStatus.PLANNED)
        logger.info(WorkerLog(
            operation="generate_plan",
            event="Planning completed",
            job_id=str(job_id),
            call_id=str(call_id),
        ))

    except QuotaExceededError as exc:
        transition_job(job_id, JobStatus.PLANNING, JobStatus.FAILED_QUOTA_EXCEEDED)
        logger.error(WorkerLog(
            operation="generate_plan",
            event="Planning quota exceeded",
            job_id=str(job_id),
            call_id=str(call_id),
            error=Logger.serialize_error(exc),
        ), exc_info=exc)
        raise

    except LLMUsageException as exc:
        reconcile_budget(call_id, exc.total_tokens, reserved, operation="generate_plan")
        transition_job(job_id, JobStatus.PLANNING, JobStatus.FAILED_LLM_USAGE)
        logger.error(WorkerLog(
            operation="generate_plan",
            event="Planning failed due to LLM usage error",
            job_id=str(job_id),
            call_id=str(call_id),
            error=Logger.serialize_error(exc),
        ), exc_info=exc)
        raise

    except Exception as exc:
        release_budget_on_error(call_id, reserved, total_tokens, operation="generate_plan")
        transition_job(job_id, JobStatus.PLANNING, JobStatus.FAILED_PLANNING)
        logger.error(WorkerLog(
            operation="generate_plan",
            event="Planning failed due to unexpected error",
            job_id=str(job_id),
            call_id=str(call_id),
            error=Logger.serialize_error(exc),
        ), exc_info=exc)
        raise


@app.task()
def generate_code(job_request_payload: dict) -> None:
    try:
        job_request = JobPlanRequest(**job_request_payload)
    except Exception as exc:
        logger.error(WorkerLog(
            operation="generate_code",
            event="Invalid request payload",
            error=Logger.serialize_error(exc),
        ), exc_info=exc)
        raise

    job_id = job_request.job.job_id
    call_id = uuid4()
    reserved = 0
    total_tokens = 0

    try:
        logger.info(WorkerLog(
            operation="generate_code",
            event="Codegen started",
            job_id=str(job_id),
            call_id=str(call_id),
        ))
        transition_job(job_id, job_request.job.status, JobStatus.CODEGEN)

        system_prompt, user_query, tools = LLMService.render_codegen_prompt(job_request.plan)
        reserved = reserve_budget(
            call_id, job_id, JobStatus.CODEGEN, LLM_CODE_MODEL,
            f"{system_prompt}\n{user_query}",
            operation="generate_code",
        )

        code, total_tokens = LLMService.codegen_call(system_prompt, user_query, tools)
        reconcile_budget(call_id, total_tokens, reserved, operation="generate_code")

        transition_job(job_id, JobStatus.CODEGEN, JobStatus.CODED)
        logger.info(WorkerLog(
            operation="generate_code",
            event="Codegen completed",
            job_id=str(job_id),
            call_id=str(call_id),
        ))
        verify_code.delay(
            JobCodeRequest(job=Job(job_id=job_id, status=JobStatus.CODED), code=code).model_dump(mode="json")
        )

    except QuotaExceededError as exc:
        transition_job(job_id, JobStatus.CODEGEN, JobStatus.FAILED_QUOTA_EXCEEDED)
        logger.error(WorkerLog(
            operation="generate_code",
            event="Codegen quota exceeded",
            job_id=str(job_id),
            call_id=str(call_id),
            error=Logger.serialize_error(exc),
        ), exc_info=exc)
        raise

    except LLMUsageException as exc:
        reconcile_budget(call_id, exc.total_tokens, reserved, operation="generate_code")
        transition_job(job_id, JobStatus.CODEGEN, JobStatus.FAILED_LLM_USAGE)
        logger.error(WorkerLog(
            operation="generate_code",
            event="Codegen failed due to LLM usage error",
            job_id=str(job_id),
            call_id=str(call_id),
            error=Logger.serialize_error(exc),
        ), exc_info=exc)
        raise

    except Exception as exc:
        release_budget_on_error(call_id, reserved, total_tokens, operation="generate_code")
        transition_job(job_id, JobStatus.CODEGEN, JobStatus.FAILED_CODEGEN)
        logger.error(WorkerLog(
            operation="generate_code",
            event="Codegen failed",
            job_id=str(job_id),
            call_id=str(call_id),
            error=Logger.serialize_error(exc),
        ), exc_info=exc)
        raise


@app.task()
def verify_code(job_request_payload: dict) -> None:
    try:
        job_request = JobCodeRequest(**job_request_payload)
    except Exception as exc:
        logger.error(WorkerLog(
            operation="verify_code",
            event="Invalid request payload",
            error=Logger.serialize_error(exc),
        ), exc_info=exc)
        raise

    job_id = job_request.job.job_id
    code = job_request.code
    fix_attempt = job_request.fix_attempt

    render_root = Path(PathNames.TMP_RENDER_FOLDER)
    input_dir = render_root / str(job_id) / PathNames.INPUT_FOLDER
    input_dir.mkdir(parents=True, exist_ok=True)
    code_path = input_dir / PathNames.MANIM_CODE
    code_path.write_text(code, encoding="utf-8")

    try:
        transition_job(job_id, job_request.job.status, JobStatus.VERIFYING)
        logger.info(WorkerLog(
            operation="verify_code",
            event="Verification started",
            job_id=str(job_id),
            context={"fix_attempt": fix_attempt},
        ))

        from app.workers.worker_helpers import verify_code as static_verify
        failure: str | None = static_verify(code, code_path)

        if failure is None:
            media_dir = input_dir / PathNames.MEDIA_FOLDER
            media_dir.mkdir(parents=True, exist_ok=True)
            media_dir.chmod(0o777)
            passed, error_output, is_fixable = dry_run_docker(code_path, media_dir)
            if not passed:
                if not is_fixable:
                    logger.error(WorkerLog(
                        operation="verify_code",
                        event="Dry-run aborted due to infrastructure error",
                        job_id=str(job_id),
                        context={"fix_attempt": fix_attempt, "error_output": error_output},
                    ))
                    transition_job(job_id, JobStatus.VERIFYING, JobStatus.FAILED_VERIFICATION)
                    return
                failure = f"Dry-run failed:\n{error_output}"

        if failure is None:
            storage = get_storage()
            job_dir = Path(PathNames.ARTIFACTS_FOLDER) / str(job_id)
            job_dir.mkdir(parents=True, exist_ok=True)
            file_path = None
            try:
                with tempfile.NamedTemporaryFile(
                    suffix=f".{ArtifactType.PYTHON_FILE.value}",
                    dir=job_dir,
                    delete=False,
                ) as tmp:
                    tmp.write(code.encode("utf-8"))
                    file_path = Path(tmp.name)
                save_artifact_to_storage(job_id, file_path, ArtifactType.PYTHON_FILE, storage)
            finally:
                if job_dir.exists():
                    shutil.rmtree(job_dir, ignore_errors=True)

            transition_job(job_id, JobStatus.VERIFYING, JobStatus.VERIFIED)
            logger.info(WorkerLog(
                operation="verify_code",
                event="Verification passed",
                job_id=str(job_id),
            ))
            generate_render.delay(
                JobRequest(job=Job(job_id=job_id, status=JobStatus.VERIFIED)).model_dump(mode="json")
            )
        else:
            failure_summary = summarize_verification_failure(failure)
            logger.warning(WorkerLog(
                operation="verify_code",
                event="Verification failed",
                job_id=str(job_id),
                context={"fix_attempt": fix_attempt, "failure_summary": failure_summary},
            ))

            if fix_attempt >= MAX_FIX_ATTEMPTS:
                transition_job(job_id, JobStatus.VERIFYING, JobStatus.FAILED_VERIFICATION)
                logger.error(WorkerLog(
                    operation="verify_code",
                    event="Verification exhausted; job failed",
                    job_id=str(job_id),
                    context={"fix_attempt": fix_attempt, "max_fix_attempts": MAX_FIX_ATTEMPTS},
                ))
            else:
                transition_job(job_id, JobStatus.VERIFYING, JobStatus.FIXING)
                logger.info(WorkerLog(
                    operation="verify_code",
                    event="Fix enqueued",
                    job_id=str(job_id),
                    context={"fix_attempt": fix_attempt + 1, "max_fix_attempts": MAX_FIX_ATTEMPTS},
                ))
                fix_code.delay(
                    JobFixRequest(
                        job=Job(job_id=job_id, status=JobStatus.FIXING),
                        code=code,
                        error_context=failure,
                        fix_attempt=fix_attempt + 1,
                    ).model_dump(mode="json")
                )

    except Exception as exc:
        transition_job(job_id, JobStatus.VERIFYING, JobStatus.FAILED_VERIFICATION)
        logger.error(WorkerLog(
            operation="verify_code",
            event="Verification task failed unexpectedly",
            job_id=str(job_id),
            error=Logger.serialize_error(exc),
        ), exc_info=exc)
        raise

    finally:
        shutil.rmtree(input_dir, ignore_errors=True)


@app.task()
def fix_code(job_request_payload: dict) -> None:
    try:
        job_request = JobFixRequest(**job_request_payload)
    except Exception as exc:
        logger.error(WorkerLog(
            operation="fix_code",
            event="Invalid request payload",
            error=Logger.serialize_error(exc),
        ), exc_info=exc)
        raise

    job_id = job_request.job.job_id
    call_id = uuid4()
    reserved = 0
    total_tokens = 0

    try:
        logger.info(WorkerLog(
            operation="fix_code",
            event="Fix started",
            job_id=str(job_id),
            call_id=str(call_id),
        ))

        system_prompt, user_query = LLMService.render_fix_prompt(job_request.code, job_request.error_context)
        reserved = reserve_budget(
            call_id, job_id, JobStatus.FIXING, LLM_CODE_MODEL,
            f"{system_prompt}\n{user_query}",
            operation="fix_code",
        )

        fixed_code, total_tokens = LLMService.fix_call(system_prompt, user_query)
        reconcile_budget(call_id, total_tokens, reserved, operation="fix_code")

        logger.info(WorkerLog(
            operation="fix_code",
            event="Fix completed",
            job_id=str(job_id),
            call_id=str(call_id),
        ))
        verify_code.delay(
            JobCodeRequest(
                job=Job(job_id=job_id, status=JobStatus.FIXING),
                code=fixed_code,
                fix_attempt=job_request.fix_attempt,
            ).model_dump(mode="json")
        )

    except QuotaExceededError as exc:
        release_budget_on_error(call_id, reserved, total_tokens, operation="fix_code")
        transition_job(job_id, JobStatus.FIXING, JobStatus.FAILED_QUOTA_EXCEEDED)
        logger.error(WorkerLog(
            operation="fix_code",
            event="Fix quota exceeded",
            job_id=str(job_id),
            call_id=str(call_id),
            error=Logger.serialize_error(exc),
        ), exc_info=exc)
        raise

    except LLMUsageException as exc:
        reconcile_budget(call_id, exc.total_tokens, reserved, operation="fix_code")
        transition_job(job_id, JobStatus.FIXING, JobStatus.FAILED_LLM_USAGE)
        logger.error(WorkerLog(
            operation="fix_code",
            event="Fix failed due to LLM usage error",
            job_id=str(job_id),
            call_id=str(call_id),
            error=Logger.serialize_error(exc),
        ), exc_info=exc)
        raise

    except Exception as exc:
        release_budget_on_error(call_id, reserved, total_tokens, operation="fix_code")
        transition_job(job_id, JobStatus.FIXING, JobStatus.FAILED_VERIFICATION)
        logger.error(WorkerLog(
            operation="fix_code",
            event="Fix task failed",
            job_id=str(job_id),
            call_id=str(call_id),
            error=Logger.serialize_error(exc),
        ), exc_info=exc)
        raise


@app.task()
def generate_code_langgraph(job_request_payload: dict) -> None:
    try:
        job_request = JobPlanRequest(**job_request_payload)
    except Exception as exc:
        logger.error(WorkerLog(
            operation="generate_code_langgraph",
            event="Invalid request payload",
            error=Logger.serialize_error(exc),
        ), exc_info=exc)
        raise

    job_id = job_request.job.job_id
    current_status = job_request.job.status
    call_number = 0
    candidates_by_title: dict[str, KnowledgeDocumentSeed] = {}
    selected_titles: list[str] = []

    def set_status(from_status: JobStatus, to_status: JobStatus) -> None:
        nonlocal current_status
        transition_job(job_id, from_status, to_status)
        current_status = to_status

    def mark_failed_after_exception() -> None:
        if current_status == JobStatus.CODEGEN:
            set_status(JobStatus.CODEGEN, JobStatus.FAILED_CODEGEN)
        elif current_status == JobStatus.CODED:
            set_status(JobStatus.CODED, JobStatus.FAILED_VERIFICATION)
        elif current_status in {JobStatus.VERIFYING, JobStatus.FIXING}:
            set_status(current_status, JobStatus.FAILED_VERIFICATION)

    def log_node_started(name: NodesNames) -> None:
        logger.info(WorkerLog(
            operation="generate_code_langgraph",
            event=f"Node: {name} started",
            job_id=str(job_id),
        ))

    def log_openrouter_call(
        call_type: CallType,
        started_at: float,
        response,
        extra_context: dict | None = None,
    ) -> None:
        nonlocal call_number
        call_number += 1
        input_tokens, output_tokens, total_tokens, reasoning_tokens = LLMService._extract_token_usage(response)
        context = {
            "provider": LLM_PROVIDER.OPENROUTER.value,
            "model": OPENROUTER_MODEL,
            "call_type": call_type.value,
            "call_number": call_number,
            "duration_ms": round((time.perf_counter() - started_at) * 1000, 2),
            "input_tokens": input_tokens,
            "reasoning_tokens": reasoning_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
        }
        if extra_context:
            context.update(extra_context)
        logger.info(WorkerLog(
            operation="generate_code_langgraph",
            event="OpenRouter call completed",
            job_id=str(job_id),
            context=context,
        ))

    def extract_code(response: BaseMessage) -> str:
        try:
            text = LLMService._extract_text_content(response)
        except ValueError as exc:
            _, _, total_tokens, _ = LLMService._extract_token_usage(response)
            raise LLMUsageException(
                "LLM output validation failed: response did not contain plain text code.",
                total_tokens=total_tokens,
            ) from exc

        stripped = text.strip()
        if stripped.startswith("```"):
            lines = stripped.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            stripped = "\n".join(lines).strip()
        return stripped

    def build_system_messages(valid_titles: list[str]) -> list[SystemMessage]:
        core_content = "\n\n".join(read_knowledge_file(doc.path) for doc in CORE_DOCUMENTS)
        prompt_content = CODEGEN_SYSTEM_PROMPT
        core_section_start = prompt_content.find("\n# Core Skill Guidance")
        output_contract_start = prompt_content.find("\n# Output Contract")
        if core_section_start != -1 and output_contract_start != -1:
            prompt_content = (
                prompt_content[:core_section_start]
                + prompt_content[output_contract_start:]
            )
        else:
            prompt_content = (
                prompt_content
                .replace("{core_content}", "")
                .replace("{candidate_metadata}", "")
            )

        document_sections = []
        for title in valid_titles:
            content = read_knowledge_file(candidates_by_title[title].path)
            document_sections.append(f"# {title}\n\n{content}")
        selected_document_content = (
            "\n\n".join(document_sections)
            if document_sections
            else "(No selected optional skill documents.)"
        )
        return [
            SystemMessage(content=prompt_content.strip()),
            SystemMessage(content=f"# Core Skill Documents\n\n{core_content}"),
            SystemMessage(content=f"# Selected Skill Documents\n\n{selected_document_content}"),
        ]

    def node_document_selection(state: LangGraphCodegenState) -> dict:
        nonlocal candidates_by_title, selected_titles
        log_node_started(NodesNames.DOCUMENT_SELECTION)
        plan_text = state["plan"].model_dump_json()
        with get_worker_cursor() as cursor:
            candidates = SkillRetrievalService.retrieve(cursor, plan_text)

        candidate_documents = [
            doc for doc in candidates.all_candidates
            if doc.document_id in REGISTRY_BY_ID
        ]
        candidates_by_title = {
            doc.title: REGISTRY_BY_ID[doc.document_id]
            for doc in candidate_documents
        }
        candidate_metadata = (
            "\n".join(doc.to_metadata() for doc in candidate_documents)
            if candidate_documents
            else "(No candidate skill documents retrieved.)"
        )
        selection_prompt = (
            "From this list, return only the document titles needed to generate "
            "reliable Manim code for the lesson plan.\n\n"
            f"Lesson plan JSON:\n{plan_text}\n\n"
            f"Candidate documents:\n{candidate_metadata}\n\n"
            "Return exact titles from the list. Select an empty list if none are useful."
        )

        structured_client = client.with_structured_output(SelectedSkillDocuments, include_raw=True)
        started_at = time.perf_counter()
        result = structured_client.invoke([HumanMessage(content=selection_prompt)])
        raw_response = result.get("raw") if isinstance(result, dict) else result
        parsed = result.get("parsed") if isinstance(result, dict) else result
        selected_count = (
            len(parsed.selected_titles)
            if isinstance(parsed, SelectedSkillDocuments)
            else 0
        )
        log_openrouter_call(
            CallType.DOCUMENT_SELECTION,
            started_at,
            raw_response,
            {
                "candidate_count": len(candidate_documents),
                "selected_count": selected_count,
            },
        )
        if not isinstance(parsed, SelectedSkillDocuments):
            parsing_error = result.get("parsing_error") if isinstance(result, dict) else None
            _, _, total_tokens, _ = LLMService._extract_token_usage(raw_response)
            exception = LLMUsageException(
                "LLM output validation failed: document selection response was not valid.",
                total_tokens=total_tokens,
            )
            if isinstance(parsing_error, BaseException):
                raise exception from parsing_error
            raise exception

        selected_titles = list(dict.fromkeys(parsed.selected_titles))
        logger.info(WorkerLog(
            operation="generate_code_langgraph",
            event="Document selection completed",
            job_id=str(job_id),
            context={
                "candidate_count": len(candidate_documents),
                "selected_count": len(selected_titles),
                "selected_titles": selected_titles,
            },
        ))
        return {}

    def node_load_selected_documents(state: LangGraphCodegenState) -> dict:
        log_node_started(NodesNames.LOAD_SELECTED_DOCUMENTS)
        valid_titles = [title for title in selected_titles if title in candidates_by_title]
        invalid_titles = [title for title in selected_titles if title not in candidates_by_title]
        if invalid_titles:
            logger.warning(WorkerLog(
                operation="generate_code_langgraph",
                event="Ignoring unknown selected skill document titles",
                job_id=str(job_id),
                context={"invalid_titles": invalid_titles},
            ))

        try:
            system_messages = build_system_messages(valid_titles)
        except Exception as exc:
            logger.error(WorkerLog(
                operation="generate_code_langgraph",
                event="Selected skill document load failed",
                job_id=str(job_id),
                error=Logger.serialize_error(exc),
            ), exc_info=exc)
            raise
        return {"messages": system_messages}

    def node_generate_code(state: LangGraphCodegenState) -> dict:
        log_node_started(NodesNames.GENERATE_CODE)
        plan_text = state["plan"].model_dump_json()
        human_message = HumanMessage(
            content=f"Generate Manim code for this lesson plan:\n\n{plan_text}"
        )
        started_at = time.perf_counter()
        response: AIMessage = client.invoke([*state["messages"], human_message])
        code = extract_code(response)
        log_openrouter_call(CallType.CODEGEN, started_at, response)
        set_status(JobStatus.CODEGEN, JobStatus.CODED)
        logger.info(WorkerLog(
            operation="generate_code_langgraph",
            event="Code generation completed",
            job_id=str(job_id),
        ))
        return {"messages": [human_message, response], "code": code}

    def node_verify(state: LangGraphCodegenState) -> dict:
        log_node_started(NodesNames.VERIFY)
        expected_from = JobStatus.CODED if state["fix_attempt"] == 0 else JobStatus.FIXING
        set_status(expected_from, JobStatus.VERIFYING)

        render_root = Path(PathNames.TMP_RENDER_FOLDER)
        input_dir = render_root / str(job_id) / PathNames.INPUT_FOLDER
        input_dir.mkdir(parents=True, exist_ok=True)
        code_path = input_dir / PathNames.MANIM_CODE
        code_path.write_text(state["code"], encoding="utf-8")

        try:
            from app.workers.worker_helpers import verify_code as static_verify
            failure = static_verify(state["code"], code_path)
            is_fixable = True

            if failure is None:
                media_dir = input_dir / PathNames.MEDIA_FOLDER
                media_dir.mkdir(parents=True, exist_ok=True)
                media_dir.chmod(0o777)
                passed, error_output, is_fixable = dry_run_docker(code_path, media_dir)
                if not passed:
                    failure = (
                        f"Dry-run failed:\n{error_output}"
                        if is_fixable
                        else f"Dry-run infrastructure error:\n{error_output}"
                    )

            if failure is None:
                logger.info(WorkerLog(
                    operation="generate_code_langgraph",
                    event="Verification passed",
                    job_id=str(job_id),
                    context={"fix_attempt": state["fix_attempt"]},
                ))
                return {"verification_failure": "", "verification_fixable": True}

            failure_summary = summarize_verification_failure(failure)
            logger.warning(WorkerLog(
                operation="generate_code_langgraph",
                event="Verification failed",
                job_id=str(job_id),
                context={
                    "fix_attempt": state["fix_attempt"],
                    "failure_summary": failure_summary,
                    "is_fixable": is_fixable,
                },
            ))
            return {"verification_failure": failure, "verification_fixable": is_fixable}
        except Exception:
            set_status(JobStatus.VERIFYING, JobStatus.FAILED_VERIFICATION)
            raise
        finally:
            shutil.rmtree(input_dir, ignore_errors=True)

    def node_fix_code(state: LangGraphCodegenState) -> dict:
        log_node_started(NodesNames.FIX_CODE)
        set_status(JobStatus.VERIFYING, JobStatus.FIXING)
        attempt = state["fix_attempt"] + 1
        fix_instruction = HumanMessage(
            content=(
                f"Attempt {attempt} of {MAX_FIX_ATTEMPTS}: verification failed.\n\n"
                f"{state['verification_failure']}\n\n"
                "Return a complete corrected Python script only."
            )
        )
        started_at = time.perf_counter()
        try:
            response: AIMessage = client.invoke([*state["messages"], fix_instruction])
            fixed_code = extract_code(response)
        except Exception:
            set_status(JobStatus.FIXING, JobStatus.FAILED_VERIFICATION)
            raise

        log_openrouter_call(
            CallType.FIX,
            started_at,
            response,
            {"attempt": attempt, "max_fix_attempts": MAX_FIX_ATTEMPTS},
        )
        return {"messages": [fix_instruction, response], "code": fixed_code, "fix_attempt": attempt}

    def node_save_and_render(state: LangGraphCodegenState) -> dict:
        log_node_started(NodesNames.SAVE_AND_RENDER)
        storage = get_storage()
        job_dir = Path(PathNames.ARTIFACTS_FOLDER) / str(job_id)
        job_dir.mkdir(parents=True, exist_ok=True)
        try:
            with tempfile.NamedTemporaryFile(
                suffix=f".{ArtifactType.PYTHON_FILE.value}",
                dir=job_dir,
                delete=False,
            ) as tmp:
                tmp.write(state["code"].encode("utf-8"))
                file_path = Path(tmp.name)
            save_artifact_to_storage(job_id, file_path, ArtifactType.PYTHON_FILE, storage)
        finally:
            if job_dir.exists():
                shutil.rmtree(job_dir, ignore_errors=True)

        set_status(JobStatus.VERIFYING, JobStatus.VERIFIED)
        logger.info(WorkerLog(
            operation="generate_code_langgraph",
            event="Verification completed and render enqueued",
            job_id=str(job_id),
        ))
        generate_render.delay(
            JobRequest(job=Job(job_id=job_id, status=JobStatus.VERIFIED)).model_dump(mode="json")
        )
        return {}

    def node_fail(state: LangGraphCodegenState) -> dict:
        log_node_started(NodesNames.FAIL)
        logger.error(WorkerLog(
            operation="generate_code_langgraph",
            event="Verification failed; job failed",
            job_id=str(job_id),
            context={
                "fix_attempt": state["fix_attempt"],
                "max_fix_attempts": MAX_FIX_ATTEMPTS,
                "verification_fixable": state["verification_fixable"],
                "failure_summary": summarize_verification_failure(state["verification_failure"]),
            },
        ))
        set_status(JobStatus.VERIFYING, JobStatus.FAILED_VERIFICATION)
        return {}

    try:
        logger.info(WorkerLog(
            operation="generate_code_langgraph",
            event="LangGraph task started",
            job_id=str(job_id),
        ))
        set_status(job_request.job.status, JobStatus.CODEGEN)
        client = _get_openrouter_client()

        graph = StateGraph(LangGraphCodegenState)
        graph.add_node(NodesNames.DOCUMENT_SELECTION, node_document_selection)
        graph.add_node(NodesNames.LOAD_SELECTED_DOCUMENTS, node_load_selected_documents)
        graph.add_node(NodesNames.GENERATE_CODE, node_generate_code)
        graph.add_node(NodesNames.VERIFY, node_verify)
        graph.add_node(NodesNames.FIX_CODE, node_fix_code)
        graph.add_node(NodesNames.SAVE_AND_RENDER, node_save_and_render)
        graph.add_node(NodesNames.FAIL, node_fail)

        graph.set_entry_point(NodesNames.DOCUMENT_SELECTION)
        graph.add_edge(NodesNames.DOCUMENT_SELECTION, NodesNames.LOAD_SELECTED_DOCUMENTS)
        graph.add_edge(NodesNames.LOAD_SELECTED_DOCUMENTS, NodesNames.GENERATE_CODE)
        graph.add_edge(NodesNames.GENERATE_CODE, NodesNames.VERIFY)
        graph.add_conditional_edges(NodesNames.VERIFY, route_after_verify)
        graph.add_edge(NodesNames.FIX_CODE, NodesNames.VERIFY)
        graph.add_edge(NodesNames.SAVE_AND_RENDER, END)
        graph.add_edge(NodesNames.FAIL, END)

        compiled = graph.compile()
        initial_state: LangGraphCodegenState = {
            "job_id": job_id,
            "plan": job_request.plan,
            "messages": [],
            "code": "",
            "verification_failure": "",
            "fix_attempt": 0,
            "verification_fixable": True,
        }
        recursion_limit = (
            len(NodesNames.non_loop_nodes())
            + MAX_FIX_ATTEMPTS * len(NodesNames.loop_nodes_per_fix_attempt())
        )
        compiled.invoke(initial_state, config={"recursion_limit": recursion_limit})
        logger.info(WorkerLog(
            operation="generate_code_langgraph",
            event="LangGraph task completed",
            job_id=str(job_id),
        ))
    except Exception as exc:
        try:
            mark_failed_after_exception()
        except Exception:
            logger.warning(WorkerLog(
                operation="generate_code_langgraph",
                event="Failed to transition job after LangGraph exception",
                job_id=str(job_id),
            ), exc_info=True)
        logger.error(WorkerLog(
            operation="generate_code_langgraph",
            event="LangGraph task failed",
            job_id=str(job_id),
            error=Logger.serialize_error(exc),
        ), exc_info=exc)
        raise


@app.task()
def generate_render(job_request_payload: dict) -> None:
    try:
        job_request = JobRequest(**job_request_payload)
    except Exception as exc:
        logger.error(WorkerLog(
            operation="generate_render",
            event="Invalid request payload",
            error=Logger.serialize_error(exc),
        ), exc_info=exc)
        raise

    job_id = job_request.job.job_id
    render_root = Path(PathNames.TMP_RENDER_FOLDER)
    input_dir = render_root / str(job_id) / PathNames.INPUT_FOLDER

    try:
        transition_job(job_id, job_request.job.status, JobStatus.RENDERING)
        logger.info(WorkerLog(
            operation="generate_render",
            event="Render started",
            job_id=str(job_id),
        ))

        storage = get_storage()

        with get_worker_cursor() as cursor:
            plan = PlansRepository.get_plan(cursor, job_id)
        if plan is None:
            raise RuntimeError("No plan found for render.")
        video_plan = plan.plan
        if not video_plan.scenes:
            raise RuntimeError("No plan scenes found for render.")

        with get_worker_cursor() as cursor:
            python_artifacts = ArtifactsRepository.get_all_artifacts(
                cursor,
                artifact_type=ArtifactType.PYTHON_FILE,
                job_id=job_id,
            )
        if not python_artifacts:
            raise RuntimeError("No python code artifact found for render.")
        if len(python_artifacts) > 1:
            raise RuntimeError("Multiple python code artifacts were found for render.")

        input_dir.mkdir(parents=True, exist_ok=True)
        python_artifact = python_artifacts[0]
        code_path = input_dir / Path(python_artifact.path).name
        storage.download_artifact(python_artifact.path, str(code_path))

        media_dir = input_dir / PathNames.MEDIA_FOLDER
        media_dir.mkdir(parents=True, exist_ok=True)
        media_dir.chmod(0o777)

        command = [
            *DockerCommands.BIN,
            *DockerCommands.NETWORK,
            *DockerCommands.CPU,
            *DockerCommands.MEMORY,
            *DockerCommands.PIDS,
            *DockerCommands.SECURITY,
            *DockerCommands.volume(str(render_root), render_root, "rw"),
            *DockerCommands.IMAGE,
            *DockerCommands.manim_command(code_path=code_path, media_dir=media_dir),
        ]

        render_failed: Exception | None = None
        try:
            result = subprocess.run(
                command, capture_output=True, text=True, timeout=RENDER_TIMEOUT_SECONDS,
            )
            render_stdout, render_stderr = result.stdout or "", result.stderr or ""
            if result.returncode != 0:
                render_failed = RuntimeError(f"Docker render exited with code {result.returncode}")
        except subprocess.TimeoutExpired as exc:
            render_stdout = exc.stdout if isinstance(exc.stdout, str) else (bytes(exc.stdout).decode() if exc.stdout else "")
            render_stderr = exc.stderr if isinstance(exc.stderr, str) else (bytes(exc.stderr).decode() if exc.stderr else "")
            render_failed = exc

        store_render_logs(storage, job_id, render_stdout, render_stderr)

        if render_failed is not None:
            logger.error(WorkerLog(
                operation="generate_render",
                event="Docker render failed",
                job_id=str(job_id),
                error=Logger.serialize_error(render_failed),
            ))
            raise render_failed

        videos_dir = media_dir / PathNames.VIDEOS_FOLDER / code_path.stem / PathNames.RESOLUTION_FOLDER
        if not videos_dir.exists():
            raise RuntimeError(f"Render output folder not found, should have been created by the renderer: {videos_dir}.")

        output_files = [p for p in videos_dir.glob(f"*.{ArtifactType.MP4.value}") if p.is_file()]
        if len(output_files) != len(video_plan.scenes):
            raise RuntimeError(
                f"Render output count mismatch: "
                f"expected {len(video_plan.scenes)} mp4 files, got {len(output_files)}."
            )

        for output_file in output_files:
            save_artifact_to_storage(job_id, output_file, ArtifactType.from_path(output_file), storage)

        transition_job(job_id, JobStatus.RENDERING, JobStatus.RENDERED)
        logger.info(WorkerLog(
            operation="generate_render",
            event="Render completed",
            job_id=str(job_id),
        ))

    except Exception as exc:
        transition_job(job_id, JobStatus.RENDERING, JobStatus.FAILED_RENDER)
        logger.error(WorkerLog(
            operation="generate_render",
            event="Render failed",
            job_id=str(job_id),
            error=Logger.serialize_error(exc),
        ), exc_info=exc)
        raise

    finally:
        if input_dir.exists():
            shutil.rmtree(input_dir, ignore_errors=True)


@app.task()
def seed_knowledge() -> None:
    inserted = skipped = 0
    with get_worker_cursor() as cursor:
        for entry in REGISTRY:
            if KnowledgeRepository.document_exists(cursor, entry.document_id):
                skipped += 1
                continue

            content = (LLMKNOWLEDGE_DIR / entry.path).read_text(encoding="utf-8")
            embedding = RAGService.embed_text(content)
            try:
                KnowledgeRepository.create_document(
                    cursor,
                    document_id=entry.document_id,
                    doc_type=entry.doc_type.value,
                    title=entry.title,
                    embedding=embedding,
                    category=entry.category,
                    priority=entry.priority,
                    tags=entry.tags,
                )
                inserted += 1
            except UniqueViolation:
                skipped += 1
    logger.info(WorkerLog(
        operation="seed_knowledge",
        event="Seed complete",
        context={"inserted": inserted, "skipped": skipped},
    ))
