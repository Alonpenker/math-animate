from celery import Celery
from celery.signals import worker_process_init, worker_process_shutdown
from pathlib import Path
import hashlib
import shutil
import subprocess

from app.dependencies.db import init_db_pool, close_db_pool, get_worker_cursor
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

# TODO: move the connections to .env file
# TODO: use consts for all the scattered strings
BROKER = "amqp://guest:guest@rabbitmq:5672//"
BACKEND = "redis://redis:6379/0"

app = Celery('manim-generator-planner',broker=BROKER, backend=BACKEND)

@worker_process_init.connect
def init_worker(**kwargs) -> None:
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

# TODO: delete this crap and use a more clean way (implement a feature in the ArtifactType)
def _artifact_type_for_path(path: Path) -> ArtifactType:
    suffix = path.suffix.lower()
    if suffix == ".mp4":
        return ArtifactType.MP4
    if suffix == ".log":
        return ArtifactType.LOG
    if suffix == ".json":
        return ArtifactType.JSON
    if suffix == ".zip":
        return ArtifactType.ZIP
    if suffix == ".txt":
        return ArtifactType.TXT
    if suffix == ".py":
        return ArtifactType.PYTHON_FILE
    return ArtifactType.METADATA

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
        # TODO: need to find an approach to save in one file multiple scenes and than save it do
        # TODO: rendering proccess can corrrectly run the same file multiple time one for each scene
        code = dummy_codegen_call(job_request.data)
        job_dir = Path("job_artifacts") / str(job_request.job_id)
        job_dir.mkdir(parents=True, exist_ok=True)
        file_path = job_dir / "code.py"
        file_bytes = code.encode("utf-8")
        file_path.write_bytes(file_bytes)
        object_path = FilesStorageService().save_artifact(job_request.job_id, str(file_path))
        artifact = Artifact(
            job_id=job_request.job_id,
            artifact_type=ArtifactType.PYTHON_FILE,
            path=object_path,
            size=len(file_bytes),
            sha256=hashlib.sha256(file_bytes).hexdigest(),
        )
        with get_worker_cursor() as cursor:
            ArtifactsRepository.create_artifact(cursor, artifact)
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

    render_root = Path("/tmp/render") / str(job_request.job_id)
    input_dir = render_root / "input"
    output_dir = render_root / "output"
    storage = FilesStorageService()

    try:
        with get_worker_cursor() as cursor:
            artifacts = ArtifactsRepository.get_artifacts(cursor, job_request.job_id)
        if artifacts is None:
            raise RuntimeError("No input artifacts found for render.")

        input_dir.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)

        for item in artifacts:
            object_path = item["path"]
            dest_path = input_dir / Path(object_path).name
            storage.download_artifact(object_path, str(dest_path))

        code_files = list(input_dir.glob("*.py"))
        if not code_files:
            raise RuntimeError("No python code artifact found for render.")

        code_path = code_files[0]
        # TODO: the worker image is not able to run docker commands, needs to change the Dockerfile
        # TODO: the command should run multiple times, one for each scene and save all
        # TODO: No need for logs from the docker for now
        command = [
            "docker","run","--rm","--network","none","--cpus","1","--memory","2g","-v",
            f"{input_dir}:/input:ro","-v",
            f"{output_dir}:/output:rw",
            "manimcommunity/manim:latest",
            "/bin/sh","-c",
            f"manim -qh --media_dir /output /input/{code_path.name} > /output/render.log 2>&1",
        ]
        subprocess.run(command, check=True)

        output_files = [p for p in output_dir.rglob("*") if p.is_file()]
        if not output_files:
            raise RuntimeError("No render outputs produced.")

        for output_file in output_files:
            file_bytes = output_file.read_bytes()
            object_path = storage.save_artifact(job_request.job_id, str(output_file))
            artifact = Artifact(
                job_id=job_request.job_id,
                artifact_type=_artifact_type_for_path(output_file),
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
