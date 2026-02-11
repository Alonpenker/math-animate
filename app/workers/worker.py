from typing import Optional
from celery import Celery, current_task
from celery.signals import worker_process_init, worker_process_shutdown
from pathlib import Path
from uuid import uuid4
import tempfile
import hashlib
import shutil
import subprocess
import os

from app.configs.app_settings import settings
from app.workers.worker_settings import PathNames, DockerCommands
from app.dependencies.db import init_db_pool, close_db_pool, get_worker_cursor
from app.dependencies.storage import init_storage, get_storage_client
from app.domain.job_state import JobStatus, require_transition
from app.repositories.jobs_repository import JobsRepository
from app.repositories.plans_repository import PlansRepository
from app.repositories.artifacts_repository import ArtifactsRepository
from app.schemas.jobs import JobUserRequest, JobPlanRequest, JobRequest, Job
from app.schemas.artifact import Artifact, ArtifactType
from app.schemas.video_plan import VideoPlan
from app.services.llm_service import LLMService
from app.services.files_storage_service import FilesStorageService
from app.utils.logging import get_logger

app = Celery('manim-generator-worker',
             broker=settings.broker_url, 
             backend=settings.backend_url)

logger = get_logger(__name__)

def log_context(job_id: Optional[str] = None) -> str:
    parts: list[str] = [f"pid={os.getpid()}"]
    if current_task is not None and getattr(current_task, "request", None) is not None:
        hostname = getattr(current_task.request, "hostname", None)
        if hostname:
            parts.append(f"worker={hostname}")
    if job_id:
        parts.append(f"job_id={job_id}")
    return " ".join(parts)

@worker_process_init.connect
def init_worker(**kwargs) -> None:
    init_storage()
    init_db_pool()

@worker_process_shutdown.connect
def shutdown_worker(**kwargs) -> None:
    close_db_pool()


@app.task(max_retries=1)
def generate_plan(job_request_payload: dict) -> None:
    try:
        job_request = JobUserRequest(**job_request_payload)
    except Exception:
        logger.exception("Invalid user request payload (%s)", log_context())
        raise
    
    try:
        logger.info("Planning started (%s)", log_context(str(job_request.job.job_id)))
        require_transition(job_request.job.status, JobStatus.PLANNING)
        with get_worker_cursor() as cursor:
            JobsRepository.update_job_status(
                cursor, job_request.job.job_id, JobStatus.PLANNING
            )
        logger.info("LLM planning call started (%s)", log_context(str(job_request.job.job_id)))
        plan: VideoPlan = LLMService.plan_call(job_request.user_request)
        require_transition(JobStatus.PLANNING, JobStatus.PLANNED)
        with get_worker_cursor() as cursor:
            PlansRepository.create_plan(cursor, job_request.job.job_id, plan)
            JobsRepository.update_job_status(
                cursor, job_request.job.job_id, JobStatus.PLANNED
            )
        logger.info("Planning completed (%s)", log_context(str(job_request.job.job_id)))


    except Exception:
        require_transition(JobStatus.PLANNING, JobStatus.FAILED_PLANNING)
        with get_worker_cursor() as cursor:
            logger.exception("Planning failed (%s)", log_context(str(job_request.job.job_id)))
            JobsRepository.update_job_status(
                cursor, job_request.job.job_id, JobStatus.FAILED_PLANNING
            )
        raise

    
@app.task(max_retries=1)
def generate_code(job_request_payload: dict) -> None:
    try:
        job_request = JobPlanRequest(**job_request_payload)
    except Exception:
        logger.exception("Invalid plan request payload (%s)", log_context())
        raise
    
    try: 
        require_transition(job_request.job.status, JobStatus.CODEGEN)
        with get_worker_cursor() as cursor:
            JobsRepository.update_job_status(
                cursor, job_request.job.job_id, JobStatus.CODEGEN
            )

    
        logger.info("Codegen LLM call started (%s)", log_context(str(job_request.job.job_id)))
        code = LLMService.codegen_call(job_request.plan)
        job_dir = Path(PathNames.ARTIFACTS_FOLDER) / str(job_request.job.job_id)
        job_dir.mkdir(parents=True, exist_ok=True)
        file_bytes = code.encode("utf-8")
        file_path = None
        try:
            with tempfile.NamedTemporaryFile(
                suffix=f".{ArtifactType.PYTHON_FILE.value}",
                dir=job_dir,
                delete=False,
            ) as tmp:
                tmp.write(file_bytes)
                file_path = Path(tmp.name)
            storage = FilesStorageService(
                        client=get_storage_client(),
                        bucket=settings.storage_bucket,
                    )
            object_path = storage.save_artifact(job_request.job.job_id, file_path)
            artifact = Artifact(
                artifact_id=uuid4(),
                job_id=job_request.job.job_id,
                artifact_type=ArtifactType.PYTHON_FILE,
                path=object_path,
                size=len(file_bytes),
                sha256=hashlib.sha256(file_bytes).hexdigest(),
            )
            with get_worker_cursor() as cursor:
                ArtifactsRepository.create_artifact(cursor, artifact)
        finally:
            if file_path is not None and file_path.exists():
                file_path.unlink()

        require_transition(JobStatus.CODEGEN, JobStatus.CODED)
        with get_worker_cursor() as cursor:
            JobsRepository.update_job_status(
                cursor, job_request.job.job_id, JobStatus.CODED
            )
        logger.info("Codegen completed; render enqueued (%s)", log_context(str(job_request.job.job_id)))
        generate_render.delay(
            JobRequest(job=Job(job_id=job_request.job.job_id, 
                               status=JobStatus.CODED)).model_dump(mode="json")
        )
    except Exception:
        require_transition(JobStatus.CODEGEN, JobStatus.FAILED_CODEGEN)
        with get_worker_cursor() as cursor:
            logger.exception("Codegen failed (%s)", log_context(str(job_request.job.job_id)))
            JobsRepository.update_job_status(
                cursor, job_request.job.job_id, JobStatus.FAILED_CODEGEN
            )
        raise

@app.task(max_retries=1)
def generate_render(job_request_payload: dict) -> None:
    try:
        job_request = JobRequest(**job_request_payload)
    except Exception:
        logger.exception("Invalid job request payload (%s)", log_context())
        raise
    
    try:
        require_transition(job_request.job.status, JobStatus.RENDERING)
        with get_worker_cursor() as cursor:
            JobsRepository.update_job_status(
                cursor, job_request.job.job_id, JobStatus.RENDERING
            )
        logger.info("Render started (%s)", log_context(str(job_request.job.job_id)))

        render_root = Path(PathNames.TMP_RENDER_FOLDER)
        input_dir = render_root / str(job_request.job.job_id) / PathNames.INPUT_FOLDER
        
        storage = FilesStorageService(
                        client=get_storage_client(),
                        bucket=settings.storage_bucket,
                    )
        
        with get_worker_cursor() as cursor:
            plan = PlansRepository.get_plan(cursor, job_request.job.job_id)
        if plan is None:
            raise RuntimeError("No plan found for render.")
        video_plan = VideoPlan.model_validate_json(plan.plan)
        if not video_plan.scenes:
            raise RuntimeError("No plan scenes found for render.")

        with get_worker_cursor() as cursor:
            artifacts = ArtifactsRepository.get_artifacts(cursor, job_request.job.job_id)
        if not artifacts:
            raise RuntimeError("No input artifacts found for render.")

        input_dir.mkdir(parents=True, exist_ok=True)

        for artifact in artifacts:
            dest_path = input_dir / Path(artifact.path).name
            storage.download_artifact(artifact.path, str(dest_path))

        code_files = list(input_dir.glob(f"*.{ArtifactType.PYTHON_FILE.value}"))
        if not code_files:
            raise RuntimeError("No python code artifact found for render.")
        if len(code_files) > 1:
            raise RuntimeError("Multiple python code artifacts were found for render.")

        code_path = code_files.pop()
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
        try:
            subprocess.run(
                command,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        except subprocess.CalledProcessError as exc:
            logger.error(
                "Docker render failed (%s) exit=%s",
                log_context(str(job_request.job.job_id)),
                exc.returncode,
            )
            logger.error(
                "Docker stdout (%s) size=%s",
                log_context(str(job_request.job.job_id)),
                len(exc.stdout or ""),
            )
            logger.error(
                "Docker stderr (%s) size=%s",
                log_context(str(job_request.job.job_id)),
                len(exc.stderr or ""),
            )
            raise
        
        videos_dir = media_dir / PathNames.VIDEOS_FOLDER / code_path.stem / PathNames.RESOLUTION_FOLDER
        if not videos_dir.exists():
            raise RuntimeError(f"Render output folder not found: {videos_dir}.")

        output_files = [
            path
            for path in videos_dir.glob(f"*.{ArtifactType.MP4.value}")
            if path.is_file()
        ]
        scene_count = len(video_plan.scenes)
        if len(output_files) != scene_count:
            raise RuntimeError(
                "Render output count mismatch: "
                f"expected {scene_count} mp4 files, got {len(output_files)}."
            )
        
        artifacts = []
        for output_file in output_files:
            file_bytes = output_file.read_bytes()
            object_path = storage.save_artifact(job_request.job.job_id, output_file)
            artifact = Artifact(
                artifact_id=uuid4(),
                job_id=job_request.job.job_id,
                artifact_type=ArtifactType.from_path(output_file),
                path=object_path,
                size=len(file_bytes),
                sha256=hashlib.sha256(file_bytes).hexdigest(),
            )
            artifacts.append(artifact)
            
        with get_worker_cursor() as cursor:
            for artifact in artifacts:
                ArtifactsRepository.create_artifact(cursor, artifact)

        require_transition(JobStatus.RENDERING, JobStatus.RENDERED)
        with get_worker_cursor() as cursor:
            JobsRepository.update_job_status(
                cursor, job_request.job.job_id, JobStatus.RENDERED
            )
        logger.info("Render completed (%s)", log_context(str(job_request.job.job_id)))
    except Exception:
        logger.exception("Render failed (%s)", log_context(str(job_request.job.job_id)))
        require_transition(JobStatus.RENDERING, JobStatus.FAILED_RENDER)
        with get_worker_cursor() as cursor:
            JobsRepository.update_job_status(
                cursor, job_request.job.job_id, JobStatus.FAILED_RENDER
            )
        raise
    finally:
        if input_dir.exists():
            shutil.rmtree(input_dir, ignore_errors=True)
