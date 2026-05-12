from celery import Celery
from celery.signals import worker_process_init, worker_process_shutdown, worker_ready, setup_logging
from pathlib import Path
from uuid import uuid4
import tempfile
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor
from psycopg2.errors import UniqueViolation

from app.configs.app_settings import settings
from app.configs.llm_settings import LLM_PLAN_MODEL, LLM_CODE_MODEL
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
from app.llm_knowledge.skill_documents import LLMKNOWLEDGE_DIR, REGISTRY
from app.repositories.knowledge_repository import KnowledgeRepository
from app.repositories.plans_repository import PlansRepository
from app.repositories.artifacts_repository import ArtifactsRepository
from app.schemas.jobs import JobUserRequest, JobPlanRequest, JobRequest, Job, JobCodeRequest, JobFixRequest
from app.schemas.artifact import ArtifactType
from app.services.llm_service import LLMService
from app.services.rag_service import RAGService
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
