from celery import Celery
from celery.signals import worker_process_init, worker_process_shutdown
from pathlib import Path
from uuid import uuid4
import tempfile
import hashlib
import shutil
import subprocess

from app.configs.app_settings import settings
from app.workers.worker_settings import PathNames, DockerCommands
from app.dependencies.db import init_db_pool, close_db_pool, get_worker_cursor
from app.dependencies.storage import init_storage, get_storage_client
from app.domain.job_state import JobStatus, require_transition
from app.repositories.jobs_repository import JobsRepository
from app.repositories.plans_repository import PlansRepository
from app.repositories.artifacts_repository import ArtifactsRepository
from app.schemas.jobs import JobUserRequest, JobPlanRequest, JobRequest
from app.schemas.scene_plan import ScenePlan
from app.schemas.user_request import UserRequest
from app.schemas.video_plan import VideoPlan
from app.schemas.artifact import Artifact, ArtifactType
from app.services.files_storage_service import FilesStorageService
from app.workers.runner import WorkerRunner

app = Celery('manim-generator-worker',
             broker=settings.broker_url, 
             backend=settings.backend_url)

@worker_process_init.connect
def init_worker(**kwargs) -> None:
    init_storage()
    init_db_pool()

@worker_process_shutdown.connect
def shutdown_worker(**kwargs) -> None:
    close_db_pool()

def dummy_openai_call(user_request: UserRequest) -> VideoPlan:
    scenes = []
    for scene_number in range(1, user_request.number_of_scenes + 1):
        scenes.append(
            ScenePlan(
                learning_objective=f"Learn {user_request.topic} (scene {scene_number})",
                visual_storyboard=f"Show {user_request.topic} example {scene_number}.",
                voice_notes=f"Explain {user_request.topic} step {scene_number}.",
                scene_number=scene_number,
            )
        )
    return VideoPlan(scenes=scenes)

def dummy_codegen_call(data) -> str:
    return "def main():\n    print('hello world')\n"


@app.task(max_retries=1)
def generate_plan(job_request_payload: dict) -> None:
    job_request = JobUserRequest(**job_request_payload)
    
    require_transition(job_request.status, JobStatus.PLANNING)
    with get_worker_cursor() as cursor:
        JobsRepository.update_job_status(
            cursor, job_request.job_id, JobStatus.PLANNING.value
        )

    try:
        plan = dummy_openai_call(job_request.data)
        require_transition(JobStatus.PLANNING, JobStatus.PLANNED)
        with get_worker_cursor() as cursor:
            PlansRepository.create_plan(cursor, job_request.job_id, plan)
            JobsRepository.update_job_status(
                cursor, job_request.job_id, JobStatus.PLANNED.value
            )


    except Exception as error:
        require_transition(JobStatus.PLANNING, JobStatus.FAILED_PLANNING)
        with get_worker_cursor() as cursor:
            JobsRepository.update_job_status(
                cursor, job_request.job_id, JobStatus.FAILED_PLANNING.value
            )
        raise

    
@app.task(max_retries=2)
def generate_code(job_request_payload: dict) -> None:
    job_request = JobPlanRequest(**job_request_payload)
    
    require_transition(job_request.status, JobStatus.CODEGEN)
    with get_worker_cursor() as cursor:
        JobsRepository.update_job_status(
            cursor, job_request.job_id, JobStatus.CODEGEN.value
        )

    try: 
        code = dummy_codegen_call(job_request.data)
        job_dir = Path(PathNames.ARTIFACTS_FOLDER) / str(job_request.job_id)
        job_dir.mkdir(parents=True, exist_ok=True)
        file_bytes = code.encode("utf-8")
        file_path = None
        try:
            with tempfile.NamedTemporaryFile(
                suffix=f"{PathNames.MANIM_CODE}",
                dir=job_dir,
                delete=False,
            ) as tmp:
                tmp.write(file_bytes)
                file_path = Path(tmp.name)
            storage = FilesStorageService(
                        client=get_storage_client(),
                        bucket=settings.storage_bucket,
                    )
            object_path = storage.save_artifact(job_request.job_id, str(file_path))
            artifact = Artifact(
                artifact_id=uuid4(),
                job_id=job_request.job_id,
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
                cursor, job_request.job_id, JobStatus.CODED.value
            )
        WorkerRunner.advance(JobRequest(job_id=job_request.job_id,status=JobStatus.CODED))
    except Exception:
        require_transition(JobStatus.CODEGEN, JobStatus.FAILED_CODEGEN)
        with get_worker_cursor() as cursor:
            JobsRepository.update_job_status(
                cursor, job_request.job_id, JobStatus.FAILED_CODEGEN.value
            )
        raise

@app.task(max_retries=1)
def generate_render(job_request_payload: dict) -> None:
    job_request = JobRequest(**job_request_payload)

    require_transition(job_request.status, JobStatus.RENDERING)
    with get_worker_cursor() as cursor:
        JobsRepository.update_job_status(
            cursor, job_request.job_id, JobStatus.RENDERING.value
        )

    render_root = Path(PathNames.TMP_RENDER_FOLDER) / str(job_request.job_id)
    input_dir = render_root / PathNames.INPUT_FOLDER
    output_dir = render_root / PathNames.OUTPUT_FOLDER
    
    storage = FilesStorageService(
                    client=get_storage_client(),
                    bucket=settings.storage_bucket,
                )
    try:
        with get_worker_cursor() as cursor:
            artifacts = ArtifactsRepository.get_artifacts(cursor, job_request.job_id)
        with get_worker_cursor() as cursor:
            plan = PlansRepository.get_plan(cursor, job_request.job_id)
        if not artifacts:
            raise RuntimeError("No input artifacts found for render.")
        if plan is None or not plan.scenes:
            raise RuntimeError("No plan scenes found for render.")

        input_dir.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)

        for item in artifacts:
            object_path = item.path
            dest_path = input_dir / Path(object_path).name
            storage.download_artifact(object_path, str(dest_path))

        code_files = list(input_dir.glob("*.py"))
        if not code_files:
            raise RuntimeError("No python code artifact found for render.")

        code_path = code_files[0]
        scene_count = len(plan.scenes)
        for scene_number in range(1, scene_count + 1):
            scene_name = f"Scene{scene_number}"
            command = [
                *DockerCommands.BIN,
                *DockerCommands.NETWORK,
                *DockerCommands.CPU,
                *DockerCommands.MEMORY,
                *DockerCommands.volume(input_dir, "/input", "ro"),
                *DockerCommands.volume(output_dir, "/output", "rw"),
                *DockerCommands.IMAGE,
                *DockerCommands.SHELL,
                DockerCommands.manim_command(code_path.name, scene_name),
            ]
            subprocess.run(command, check=True)

            base_videos_dir = output_dir / "media" / "videos" / code_path.stem
            scene_mp4s = list(base_videos_dir.rglob(f"{scene_name}.mp4"))
            if not scene_mp4s:
                raise RuntimeError(f"No render output produced for {scene_name}.")
            if len(scene_mp4s) > 1:
                raise RuntimeError(f"Multiple render outputs produced for {scene_name}.")

            output_file = scene_mp4s.pop()
            normalized_output = output_dir / f"{scene_name}.mp4"
            if normalized_output.exists():
                normalized_output.unlink()
            shutil.move(str(output_file), str(normalized_output))

            file_bytes = normalized_output.read_bytes()
            object_path = storage.save_artifact(job_request.job_id, str(normalized_output))
            artifact = Artifact(
                artifact_id=uuid4(),
                job_id=job_request.job_id,
                artifact_type=ArtifactType.from_path(normalized_output),
                path=object_path,
                size=len(file_bytes),
                sha256=hashlib.sha256(file_bytes).hexdigest(),
            )
            with get_worker_cursor() as cursor:
                ArtifactsRepository.create_artifact(cursor, artifact)

        require_transition(JobStatus.RENDERING, JobStatus.RENDERED)
        with get_worker_cursor() as cursor:
            JobsRepository.update_job_status(
                cursor, job_request.job_id, JobStatus.RENDERED.value
            )
    except Exception:
        require_transition(JobStatus.RENDERING, JobStatus.FAILED_RENDER)
        with get_worker_cursor() as cursor:
            JobsRepository.update_job_status(
                cursor, job_request.job_id, JobStatus.FAILED_RENDER.value
            )
        raise
    finally:
        if render_root.exists():
            shutil.rmtree(render_root, ignore_errors=True)
