from app.domain.job_state import JobStatus
from app.schemas.jobs import JobRequest
from app.utils.llm_stubs import IS_E2E_MODE
from app.workers.worker import (
    generate_code,
    generate_code_langgraph,
    generate_plan,
    generate_render,
    seed_knowledge,
)

class WorkerRunner:
    """Coordinates job steps; actual implementations live in planner.py and render.py"""
    
    @staticmethod
    def advance(job_request: JobRequest) -> None:
        if job_request.job.status == JobStatus.CREATED:
            WorkerRunner.handle_planning(job_request)
        elif job_request.job.status == JobStatus.APPROVED:
            WorkerRunner.handle_codegen(job_request)
        elif job_request.job.status == JobStatus.CODED:
            WorkerRunner.handle_render(job_request)
        else:
            raise ValueError(f"Unsupported job status: {job_request.job.status}")
    
    @staticmethod
    def handle_planning(job_request: JobRequest) -> None:
        generate_plan.delay(job_request.model_dump(mode="json"))
    
    @staticmethod
    def handle_codegen(job_request: JobRequest) -> None:
        if IS_E2E_MODE:
            generate_code_langgraph.delay(job_request.model_dump(mode="json"))
        else:
            generate_code.delay(job_request.model_dump(mode="json"))

    @staticmethod
    def handle_render(job_request: JobRequest) -> None:
        generate_render.delay(job_request.model_dump(mode="json"))

    @staticmethod
    def handle_seed() -> None:
        seed_knowledge.delay()
