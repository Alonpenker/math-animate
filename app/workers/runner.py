from app.domain.job_state import JobStatus
from app.schemas.jobs import JobRequest
from app.workers.worker import generate_plan, generate_code, generate_render

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
            raise NotImplementedError
    
    @staticmethod
    def handle_planning(job_request: JobRequest) -> None:
        generate_plan.delay(job_request.model_dump(mode="json"))
    
    @staticmethod
    def handle_codegen(job_request: JobRequest) -> None:
        generate_code.delay(job_request.model_dump(mode="json"))

    @staticmethod
    def handle_render(job_request: JobRequest) -> None:
        generate_render.delay(job_request.model_dump(mode="json"))
