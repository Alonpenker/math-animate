from celery import Celery
from celery.signals import worker_process_init, worker_process_shutdown, worker_ready, setup_logging
from pathlib import Path
from uuid import uuid4
import tempfile
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from psycopg2.errors import UniqueViolation
from langchain_core.messages import HumanMessage, SystemMessage

from app.configs.app_settings import settings
from app.configs.llm_settings import (
    LLM_PROVIDER,
    LLM_CODE_MODEL,
    LLM_PLAN_MODEL,
    LLM_PLAN_OUTPUT_MAX_TOKENS,
    OPENROUTER_MODELS,
    PLAN_SYSTEM_PROMPT,
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
    LLMKNOWLEDGE_DIR,
    REGISTRY,
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
from app.schemas.video_plan import VideoPlan
from app.services.agent_service import AgentService
from app.services.openrouter_service import CallType, OpenRouterService
from app.services.rag_service import RAGService
from app.workers.worker_helpers import (
    transition_job,
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

    try:
        logger.info(WorkerLog(
            operation="generate_plan",
            event="Planning started",
            job_id=str(job_id),
        ))
        transition_job(job_id, job_request.job.status, JobStatus.PLANNING)

        system_prompt = PLAN_SYSTEM_PROMPT
        user_query = str(job_request.user_request)
        started_at = time.perf_counter()
        plan, usage = OpenRouterService.invoke_structured(
            job_id=job_id,
            stage=JobStatus.PLANNING,
            call_type=CallType.PLAN,
            model=OPENROUTER_MODELS.PLAN_MODEL,
            messages=[
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_query),
            ],
            schema=VideoPlan,
            max_tokens=LLM_PLAN_OUTPUT_MAX_TOKENS,
        )
        logger.info(WorkerLog(
            operation="generate_plan",
            event="OpenRouter call completed",
            job_id=str(job_id),
            context={
                "provider": LLM_PROVIDER.OPENROUTER.value,
                "model": OPENROUTER_MODELS.PLAN_MODEL.value,
                "call_type": CallType.PLAN.value,
                "duration_ms": round((time.perf_counter() - started_at) * 1000, 2),
                "input_tokens": usage.input_tokens,
                "reasoning_tokens": usage.reasoning_tokens,
                "output_tokens": usage.output_tokens,
                "total_tokens": usage.total_tokens,
            },
        ))

        with get_worker_cursor() as cursor:
            PlansRepository.create_plan(cursor, job_id, plan)

        transition_job(job_id, JobStatus.PLANNING, JobStatus.PLANNED)
        logger.info(WorkerLog(
            operation="generate_plan",
            event="Planning completed",
            job_id=str(job_id),
        ))

    except QuotaExceededError as exc:
        transition_job(job_id, JobStatus.PLANNING, JobStatus.FAILED_QUOTA_EXCEEDED)
        logger.error(WorkerLog(
            operation="generate_plan",
            event="Planning quota exceeded",
            job_id=str(job_id),
            error=Logger.serialize_error(exc),
        ), exc_info=exc)
        raise

    except LLMUsageException as exc:
        transition_job(job_id, JobStatus.PLANNING, JobStatus.FAILED_LLM_USAGE)
        logger.error(WorkerLog(
            operation="generate_plan",
            event="Planning failed due to LLM usage error",
            job_id=str(job_id),
            error=Logger.serialize_error(exc),
        ), exc_info=exc)
        raise

    except Exception as exc:
        transition_job(job_id, JobStatus.PLANNING, JobStatus.FAILED_PLANNING)
        logger.error(WorkerLog(
            operation="generate_plan",
            event="Planning failed due to unexpected error",
            job_id=str(job_id),
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

    AgentService.run_codegen(job_request)


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
