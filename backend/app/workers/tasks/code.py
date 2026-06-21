from app.schemas.jobs import JobPlanRequest
from app.services.agent_service import AgentService
from app.utils.logging import Logger, WorkerLog

logger = Logger.get_logger("worker")


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

    AgentService.run_codegen(job_request)
