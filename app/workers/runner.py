from app.domain.job_state import JobStatus
from app.schemas.jobs import JobRequest
from app.workers.planner import generate_plan

class WorkerRunner:
    """Coordinates job steps; actual implementations live in planner.py and render.py"""
    
    @staticmethod
    def advance(job_request: JobRequest) -> None:
        if job_request.status == JobStatus.CREATED:
            WorkerRunner.handle_planning(job_request)
        elif job_request.status == JobStatus.PLANNED:
            WorkerRunner.handle_codegen(job_request)
        elif job_request.status == JobStatus.CODED:
            WorkerRunner.handle_render(job_request)
        else:
            raise NotImplementedError
    
    @staticmethod
    def handle_planning(job_request: JobRequest) -> None:
        generate_plan.delay(job_request.model_dump(mode="json"))
    
    @staticmethod
    def handle_codegen(job_request: JobRequest) -> None:
        # TODO: Implement codegen step orchestration.
        pass

    @staticmethod
    def handle_render(job_request: JobRequest) -> None:
        # TODO: Implement render step orchestration.
        pass