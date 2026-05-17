import shutil
import tempfile
import time
from enum import StrEnum
from pathlib import Path
from typing import Annotated, TypedDict
from uuid import UUID

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from pydantic import BaseModel

from app.configs.llm_settings import (
    CODEGEN_SYSTEM_PROMPT,
    LLM_CODEGEN_OUTPUT_MAX_TOKENS,
    LLM_PROVIDER,
    OPENROUTER_MODELS,
)
from app.dependencies.db import get_worker_cursor
from app.domain.job_state import JobStatus
from app.exceptions.llm_usage_exception import LLMUsageException
from app.exceptions.quota_exceeded_error import QuotaExceededError
from app.llm_knowledge.skill_documents import CORE_DOCUMENTS, REGISTRY_BY_ID, read_knowledge_file
from app.schemas.artifact import ArtifactType
from app.schemas.jobs import Job, JobPlanRequest, JobRequest
from app.schemas.knowledge import KnowledgeDocumentSeed
from app.schemas.video_plan import VideoPlan
from app.services.llm_service import CallType, LLMService
from app.services.openrouter_service import OpenRouterService, OpenRouterTokenUsage
from app.services.skill_retrieval_service import SkillRetrievalService
from app.utils.logging import Logger, WorkerLog
from app.workers.worker_helpers import (
    dry_run_docker,
    get_storage,
    save_artifact_to_storage,
    summarize_verification_failure,
    transition_job,
)
from app.workers.worker_settings import MAX_FIX_ATTEMPTS, PathNames

logger = Logger.get_logger("worker")


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


class AgentService:
    @staticmethod
    def run_codegen(job_request: JobPlanRequest) -> None:
        job_id = job_request.job.job_id
        current_status = job_request.job.status
        call_number = 0
        candidates_by_title: dict[str, KnowledgeDocumentSeed] = {}
        selected_titles: list[str] = []

        def set_status(from_status: JobStatus, to_status: JobStatus) -> None:
            nonlocal current_status
            transition_job(job_id, from_status, to_status)
            current_status = to_status

        default_failure_statuses = {
            JobStatus.CODEGEN: JobStatus.FAILED_CODEGEN,
            JobStatus.CODED: JobStatus.FAILED_VERIFICATION,
            JobStatus.VERIFYING: JobStatus.FAILED_VERIFICATION,
            JobStatus.FIXING: JobStatus.FAILED_VERIFICATION,
        }
        llm_call_failure_statuses = {
            JobStatus.CODEGEN: JobStatus.FAILED_LLM_USAGE,
            JobStatus.FIXING: JobStatus.FAILED_LLM_USAGE,
        }
        quota_failure_statuses = {
            JobStatus.CODEGEN: JobStatus.FAILED_QUOTA_EXCEEDED,
            JobStatus.FIXING: JobStatus.FAILED_QUOTA_EXCEEDED,
        }

        def mark_failed(overrides: dict[JobStatus, JobStatus] | None = None) -> None:
            to_status = (overrides or {}).get(current_status) or default_failure_statuses.get(current_status)
            if to_status is not None:
                set_status(current_status, to_status)

        def log_node_started(name: NodesNames) -> None:
            logger.info(WorkerLog(
                operation="generate_code_langgraph",
                event=f"Node: {name} started",
                job_id=str(job_id),
            ))

        def log_openrouter_call(
            call_type: CallType,
            started_at: float,
            usage: OpenRouterTokenUsage,
            extra_context: dict | None = None,
        ) -> None:
            nonlocal call_number
            call_number += 1
            context = {
                "provider": LLM_PROVIDER.OPENROUTER.value,
                "model": OPENROUTER_MODELS.CODING_MODEL.value,
                "call_type": call_type.value,
                "call_number": call_number,
                "duration_ms": int((time.perf_counter() - started_at) * 1000),
                "input_tokens": usage.input_tokens,
                "reasoning_tokens": usage.reasoning_tokens,
                "output_tokens": usage.output_tokens,
                "total_tokens": usage.total_tokens,
            }
            if extra_context:
                context.update(extra_context)
            logger.info(WorkerLog(
                operation="generate_code_langgraph",
                event="OpenRouter call completed",
                job_id=str(job_id),
                context=context,
            ))

        def extract_code(response: BaseMessage, usage: OpenRouterTokenUsage) -> str:
            try:
                text = LLMService._extract_text_content(response)
            except ValueError as exc:
                raise LLMUsageException(
                    "LLM output validation failed: response did not contain plain text code.",
                    total_tokens=usage.total_tokens,
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

            started_at = time.perf_counter()
            parsed, usage = OpenRouterService.invoke_structured(
                job_id=job_id,
                stage=JobStatus.CODEGEN,
                call_type=CallType.DOCUMENT_SELECTION,
                model=OPENROUTER_MODELS.CODING_MODEL,
                messages=[HumanMessage(content=selection_prompt)],
                schema=SelectedSkillDocuments,
                max_tokens=LLM_CODEGEN_OUTPUT_MAX_TOKENS,
            )
            selected_count = len(parsed.selected_titles)
            log_openrouter_call(
                CallType.DOCUMENT_SELECTION,
                started_at,
                usage,
                {
                    "candidate_count": len(candidate_documents),
                    "selected_count": selected_count,
                },
            )
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
            response, usage = OpenRouterService.invoke(
                job_id=job_id,
                stage=JobStatus.CODEGEN,
                call_type=CallType.CODEGEN,
                model=OPENROUTER_MODELS.CODING_MODEL,
                messages=[*state["messages"], human_message],
                max_tokens=LLM_CODEGEN_OUTPUT_MAX_TOKENS,
            )
            log_openrouter_call(CallType.CODEGEN, started_at, usage)
            code = extract_code(response, usage)
            set_status(JobStatus.CODEGEN, JobStatus.CODED)
            logger.info(WorkerLog(
                operation="generate_code_langgraph",
                event="Code generation completed",
                job_id=str(job_id),
            ))
            return {"messages": [human_message, response], "code": code}
        
        def route_after_verify(state: LangGraphCodegenState) -> str:
            if not state["verification_failure"]:
                return NodesNames.SAVE_AND_RENDER
            if not state["verification_fixable"]:
                return NodesNames.FAIL
            if state["fix_attempt"] >= MAX_FIX_ATTEMPTS:
                return NodesNames.FAIL
            return NodesNames.FIX_CODE

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
                response, usage = OpenRouterService.invoke(
                    job_id=job_id,
                    stage=JobStatus.FIXING,
                    call_type=CallType.FIX,
                    model=OPENROUTER_MODELS.CODING_MODEL,
                    messages=[*state["messages"], fix_instruction],
                    max_tokens=LLM_CODEGEN_OUTPUT_MAX_TOKENS,
                )
                log_openrouter_call(
                    CallType.FIX,
                    started_at,
                    usage,
                    {"attempt": attempt, "max_fix_attempts": MAX_FIX_ATTEMPTS},
                )
                fixed_code = extract_code(response, usage)
            except (LLMUsageException, QuotaExceededError):
                raise
            except Exception:
                set_status(JobStatus.FIXING, JobStatus.FAILED_VERIFICATION)
                raise

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
            from app.workers.worker import generate_render
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
        except QuotaExceededError as exc:
            try:
                mark_failed(quota_failure_statuses)
            except Exception:
                logger.warning(WorkerLog(
                    operation="generate_code_langgraph",
                    event="Failed to transition job after LangGraph quota exception",
                    job_id=str(job_id),
                ), exc_info=True)
            logger.error(WorkerLog(
                operation="generate_code_langgraph",
                event="LangGraph quota exceeded",
                job_id=str(job_id),
                error=Logger.serialize_error(exc),
            ), exc_info=exc)
            raise
        except LLMUsageException as exc:
            try:
                mark_failed(llm_call_failure_statuses)
            except Exception:
                logger.warning(WorkerLog(
                    operation="generate_code_langgraph",
                    event="Failed to transition job after LangGraph LLM usage exception",
                    job_id=str(job_id),
                ), exc_info=True)
            logger.error(WorkerLog(
                operation="generate_code_langgraph",
                event="LangGraph failed due to LLM usage error",
                job_id=str(job_id),
                error=Logger.serialize_error(exc),
            ), exc_info=exc)
            raise
        except Exception as exc:
            try:
                mark_failed()
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
