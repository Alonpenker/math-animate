from celery import Celery
from celery.signals import worker_process_init, worker_process_shutdown, worker_ready
from pathlib import Path
from uuid import UUID, uuid4
import json
import tempfile
import shutil
import subprocess

from app.configs.app_settings import settings
from app.configs.llm_settings import LLM_PLAN_MODEL, LLM_CODE_MODEL
from app.workers.worker_settings import PathNames, DockerCommands, RENDER_TIMEOUT_SECONDS, SQS_VISIBILITY_TIMEOUT, SQS_POLLING_INTERVAL
from app.dependencies.db import init_db_pool, close_db_pool, get_worker_cursor
from app.dependencies.redis_client import init_redis_pool, close_redis_pool
from app.dependencies.storage import init_storage
from app.domain.job_state import JobStatus, require_transition
from app.exceptions.quota_exceeded_error import QuotaExceededError
from app.repositories.jobs_repository import JobsRepository
from app.repositories.knowledge_repository import KnowledgeRepository
from app.repositories.plans_repository import PlansRepository
from app.repositories.artifacts_repository import ArtifactsRepository
from app.schemas.jobs import JobUserRequest, JobPlanRequest, JobRequest, Job, JobCodeRequest, JobFixRequest
from app.schemas.artifact import ArtifactType
from app.schemas.video_plan import VideoPlan
from app.services.llm_service import LLMService
from app.services.rag_service import RAGService
import psycopg2
from app.workers.worker_helpers import (
    log_context,
    transition_job,
    reserve_budget,
    reconcile_budget,
    release_budget_on_error,
    get_storage,
    save_artifact_to_storage,
    store_render_logs,
    dry_run_docker,
)
from app.utils.llm_stubs import IS_E2E_MODE
from app.utils.logging import get_logger

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

logger = get_logger(__name__)

if IS_E2E_MODE:
    logger.warning("E2E mode enabled — LLM calls will be stubbed. No real API calls will be made.")


@worker_process_init.connect
def init_worker(**kwargs) -> None:
    init_storage()
    init_db_pool()
    init_redis_pool()


@worker_ready.connect
def on_worker_ready(**kwargs) -> None:
    init_db_pool()
    try:
        seed_knowledge_task()
    except Exception:
        logger.warning("Knowledge auto-seed on startup failed; worker will continue.", exc_info=True)
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
    except Exception:
        logger.exception("Invalid user request payload (%s)", log_context())
        raise

    job_id = job_request.job.job_id
    call_id = uuid4()
    reserved = 0
    total_tokens = 0

    try:
        logger.info("Planning started (%s)", log_context(str(job_id)))
        transition_job(job_id, job_request.job.status, JobStatus.PLANNING)

        system_prompt, user_query = LLMService.render_plan_prompt(job_request.user_request)
        reserved = reserve_budget(
            call_id, job_id, JobStatus.PLANNING.value, LLM_PLAN_MODEL,
            f"{system_prompt}\n{user_query}",
        )

        logger.info("LLM planning call started (%s)", log_context(str(job_id)))
        plan, total_tokens = LLMService.plan_call(system_prompt, user_query)
        reconcile_budget(call_id, total_tokens)

        with get_worker_cursor() as cursor:
            PlansRepository.create_plan(cursor, job_id, plan)
        transition_job(job_id, JobStatus.PLANNING, JobStatus.PLANNED)
        logger.info("Planning completed (%s)", log_context(str(job_id)))

    except QuotaExceededError:
        logger.exception("Planning quota exceeded (%s)", log_context(str(job_id)))
        transition_job(job_id, JobStatus.PLANNING, JobStatus.FAILED_QUOTA_EXCEEDED)
        raise

    except Exception as exc:
        total_tokens = max(total_tokens, int(getattr(exc, "total_tokens", 0) or 0))
        release_budget_on_error(call_id, reserved, total_tokens)
        logger.exception("Planning failed (%s)", log_context(str(job_id)))
        transition_job(job_id, JobStatus.PLANNING, JobStatus.FAILED_PLANNING)
        raise


@app.task()
def generate_code(job_request_payload: dict) -> None:
    try:
        job_request = JobPlanRequest(**job_request_payload)
    except Exception:
        logger.exception("Invalid plan request payload (%s)", log_context())
        raise

    job_id = job_request.job.job_id
    call_id = uuid4()
    reserved = 0
    total_tokens = 0

    try:
        transition_job(job_id, job_request.job.status, JobStatus.CODEGEN)

        system_prompt, user_query = LLMService.render_codegen_prompt(job_request.plan)
        reserved = reserve_budget(
            call_id, job_id, JobStatus.CODEGEN.value, LLM_CODE_MODEL,
            f"{system_prompt}\n{user_query}",
        )

        logger.info("Codegen LLM call started (%s)", log_context(str(job_id)))
        code, total_tokens = LLMService.codegen_call(system_prompt, user_query)
        reconcile_budget(call_id, total_tokens)

        transition_job(job_id, JobStatus.CODEGEN, JobStatus.CODED)
        logger.info("Codegen completed; verification enqueued (%s)", log_context(str(job_id)))
        verify_code_task.delay(
            JobCodeRequest(job=Job(job_id=job_id, status=JobStatus.CODED), code=code, is_retry=False).model_dump(mode="json")
        )

    except QuotaExceededError:
        logger.exception("Codegen quota exceeded (%s)", log_context(str(job_id)))
        transition_job(job_id, JobStatus.CODEGEN, JobStatus.FAILED_QUOTA_EXCEEDED)
        raise

    except Exception as exc:
        total_tokens = max(total_tokens, int(getattr(exc, "total_tokens", 0) or 0))
        release_budget_on_error(call_id, reserved, total_tokens)
        logger.exception("Codegen failed (%s)", log_context(str(job_id)))
        transition_job(job_id, JobStatus.CODEGEN, JobStatus.FAILED_CODEGEN)
        raise


@app.task()
def verify_code_task(job_request_payload: dict) -> None:
    try:
        job_request = JobCodeRequest(**job_request_payload)
    except Exception:
        logger.exception("Invalid code request payload (%s)", log_context())
        raise

    job_id = job_request.job.job_id
    code = job_request.code
    is_retry = job_request.is_retry

    render_root = Path(PathNames.TMP_RENDER_FOLDER)
    input_dir = render_root / str(job_id) / PathNames.INPUT_FOLDER
    input_dir.mkdir(parents=True, exist_ok=True)
    code_path = input_dir / PathNames.MANIM_CODE
    code_path.write_text(code, encoding="utf-8")

    try:
        transition_job(job_id, job_request.job.status, JobStatus.VERIFYING)
        logger.info("Verification started (is_retry=%s) (%s)", is_retry, log_context(str(job_id)))

        from app.workers.worker_helpers import verify_code as static_verify
        failure: str | None = static_verify(code, code_path)

        if failure is None:
            media_dir = input_dir / PathNames.MEDIA_FOLDER
            media_dir.mkdir(parents=True, exist_ok=True)
            media_dir.chmod(0o777)
            passed, error_output, is_fixable = dry_run_docker(code_path, media_dir)
            if not passed:
                if not is_fixable:
                    logger.error(
                        "Dry-run aborted due to infrastructure error (is_retry=%s) (%s): %s",
                        is_retry, log_context(str(job_id)), error_output,
                    )
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
            logger.info("Verification passed; render enqueued (%s)", log_context(str(job_id)))
            generate_render.delay(
                JobRequest(job=Job(job_id=job_id, status=JobStatus.VERIFIED)).model_dump(mode="json")
            )
        else:
            failure_summary = failure.strip().splitlines()[-1] if failure.strip() else failure
            logger.warning("Verification failed (is_retry=%s) (%s): %s", is_retry, log_context(str(job_id)), failure_summary)

            if is_retry:
                transition_job(job_id, JobStatus.VERIFYING, JobStatus.FAILED_VERIFICATION)
                logger.error("Verification exhausted; job failed (%s)", log_context(str(job_id)))
            else:
                transition_job(job_id, JobStatus.VERIFYING, JobStatus.FIXING)
                logger.info("Fix enqueued (%s)", log_context(str(job_id)))
                fix_code_task.delay(
                    JobFixRequest(
                        job=Job(job_id=job_id, status=JobStatus.FIXING),
                        code=code,
                        error_context=failure,
                    ).model_dump(mode="json")
                )

    except Exception:
        logger.exception("Verification task failed unexpectedly (%s)", log_context(str(job_id)))
        transition_job(job_id, JobStatus.VERIFYING, JobStatus.FAILED_VERIFICATION)
        raise

    finally:
        shutil.rmtree(input_dir, ignore_errors=True)


@app.task()
def fix_code_task(job_request_payload: dict) -> None:
    try:
        job_request = JobFixRequest(**job_request_payload)
    except Exception:
        logger.exception("Invalid fix request payload (%s)", log_context())
        raise

    job_id = job_request.job.job_id
    call_id = uuid4()
    reserved = 0
    total_tokens = 0

    try:
        system_prompt, user_query = LLMService.render_fix_prompt(job_request.code, job_request.error_context)
        reserved = reserve_budget(
            call_id, job_id, JobStatus.FIXING.value, LLM_CODE_MODEL,
            f"{system_prompt}\n{user_query}",
        )

        logger.info("Fix LLM call started (%s)", log_context(str(job_id)))
        fixed_code, total_tokens = LLMService.fix_call(system_prompt, user_query)
        reconcile_budget(call_id, total_tokens)

        logger.info("Fix completed; re-verification enqueued (%s)", log_context(str(job_id)))
        verify_code_task.delay(
            JobCodeRequest(
                job=Job(job_id=job_id, status=JobStatus.FIXING),
                code=fixed_code,
                is_retry=True,
            ).model_dump(mode="json")
        )

    except QuotaExceededError:
        logger.exception("Fix quota exceeded (%s)", log_context(str(job_id)))
        release_budget_on_error(call_id, reserved, total_tokens)
        transition_job(job_id, JobStatus.FIXING, JobStatus.FAILED_QUOTA_EXCEEDED)

    except Exception as exc:
        total_tokens = max(total_tokens, int(getattr(exc, "total_tokens", 0) or 0))
        release_budget_on_error(call_id, reserved, total_tokens)
        logger.exception("Fix task failed (%s)", log_context(str(job_id)))
        transition_job(job_id, JobStatus.FIXING, JobStatus.FAILED_VERIFICATION)
        raise


@app.task()
def generate_render(job_request_payload: dict) -> None:
    try:
        job_request = JobRequest(**job_request_payload)
    except Exception:
        logger.exception("Invalid job request payload (%s)", log_context())
        raise

    job_id = job_request.job.job_id
    render_root = Path(PathNames.TMP_RENDER_FOLDER)
    input_dir = render_root / str(job_id) / PathNames.INPUT_FOLDER

    try:
        transition_job(job_id, job_request.job.status, JobStatus.RENDERING)
        logger.info("Render started (%s)", log_context(str(job_id)))

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
            logger.error("Docker render failed (%s): %s", log_context(str(job_id)), render_failed)
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
        logger.info("Render completed (%s)", log_context(str(job_id)))

    except Exception:
        logger.exception("Render failed (%s)", log_context(str(job_id)))
        transition_job(job_id, JobStatus.RENDERING, JobStatus.FAILED_RENDER)
        raise

    finally:
        if input_dir.exists():
            shutil.rmtree(input_dir, ignore_errors=True)


@app.task()
def seed_knowledge_task() -> None:
    examples_dir = Path(__file__).resolve().parent.parent / "examples"
    index = json.loads((examples_dir / "index.json").read_text(encoding="utf-8"))
    inserted = skipped = 0
    for entry in index:
        document_id = UUID(entry["document_id"])
        with get_worker_cursor() as cursor:
            if KnowledgeRepository.document_exists(cursor, document_id):
                skipped += 1
                continue
        content = (examples_dir / entry["file"]).read_text(encoding="utf-8")
        embedding = RAGService.embed_text(content)
        try:
            with get_worker_cursor() as cursor:
                KnowledgeRepository.create_document(
                    cursor, document_id, content, entry["doc_type"], entry["title"], embedding
                )
            inserted += 1
        except psycopg2.errors.UniqueViolation:
            skipped += 1
    logger.info("Seed complete: inserted=%d skipped=%d", inserted, skipped)


@app.task()
def create_knowledge_document_task(payload: dict) -> None:
    document_id = UUID(payload["document_id"])
    content = payload["content"]
    doc_type = payload["doc_type"]
    title = payload["title"]
    embedding = RAGService.embed_text(content)
    with get_worker_cursor() as cursor:
        KnowledgeRepository.create_document(cursor, document_id, content, doc_type, title, embedding)
    logger.info("Knowledge document created: document_id=%s", document_id)
