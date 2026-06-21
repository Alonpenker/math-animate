import shutil
from pathlib import Path

from app.dependencies.db import get_worker_cursor
from app.domain.job_state import JobStatus
from app.repositories.plans_repository import PlansRepository
from app.repositories.artifacts_repository import ArtifactsRepository
from app.schemas.jobs import JobRequest
from app.schemas.artifact import ArtifactType
from app.workers.worker_helpers import (
    get_storage,
    save_artifact_to_storage,
    store_render_logs,
    transition_job,
)
from app.workers.worker_settings import (
    PathNames,
    DockerCommands,
    RENDER_TIMEOUT_SECONDS,
)
from app.utils.logging import Logger, WorkerLog
import subprocess

logger = Logger.get_logger("worker")


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
