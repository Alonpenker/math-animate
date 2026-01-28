from celery import Celery
from celery.signals import worker_process_init, worker_process_shutdown

from app.dependencies.db import init_db_pool, close_db_pool, get_worker_cursor
from app.domain.job_state import JobStatus, require_transition
from app.repositories.jobs_repository import JobsRepository
from app.repositories.plans_repository import PlansRepository
from app.schemas.jobs import JobUserRequest
from app.schemas.scene_plan import ScenePlan
from app.schemas.user_request import UserRequest
from app.schemas.video_plan import VideoPlan
from app.schemas.artifact import Artifact, ArtifactType
from services.file_system_storage import FileSystemStorage

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

def dummy_codegen_call() -> str:
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
    job_request = JobUserRequest(**job_request_payload)
    
    require_transition(job_request.status, JobStatus.CODEGEN)
    with get_worker_cursor() as cursor:
        JobsRepository.update_job_status(
            cursor, job_request.job_id, JobStatus.CODEGEN.value
        )

    try:
        code = dummy_codegen_call()
        #TODO: create an artifact from the python code and fill all parameters, 
        # should save the artifact data in the database using the repository and the real file
        # exists in the MiniIO
        # artifact = Artifact(artifcat_type=ArtifactType.PYTHON_FILE,)
        
        FileSystemStorage.save_artifact(job_request.job_id, code)
        require_transition(JobStatus.CODEGEN, JobStatus.CODED)
        with get_worker_cursor() as cursor:
            JobsRepository.update_job_status(
                cursor, job_request.job_id, JobStatus.CODED.value
            )
    except Exception:
        require_transition(JobStatus.CODEGEN, JobStatus.FAILED_CODEGEN)
        with get_worker_cursor() as cursor:
            JobsRepository.update_job_status(
                cursor, job_request.job_id, JobStatus.FAILED_CODEGEN.value
            )
        raise
