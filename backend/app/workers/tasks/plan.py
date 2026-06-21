import time

from langchain_core.messages import HumanMessage, SystemMessage

from app.configs.llm_settings import (
    LLM_PROVIDER,
    LLM_PLAN_OUTPUT_MAX_TOKENS,
    OPENROUTER_MODELS,
    PLAN_SYSTEM_PROMPT,
)
from app.dependencies.db import get_worker_cursor
from app.domain.job_state import JobStatus
from app.exceptions.llm_call_exception import LLMCallException
from app.exceptions.llm_usage_exception import LLMUsageException
from app.exceptions.quota_exceeded_error import QuotaExceededError
from app.repositories.plans_repository import PlansRepository
from app.schemas.jobs import JobUserRequest
from app.schemas.video_plan import VideoPlan
from app.services.openrouter_service import CallType, OpenRouterService
from app.workers.worker_helpers import load_planning_capabilities, transition_job
from app.utils.logging import Logger, WorkerLog

logger = Logger.get_logger("worker")


def generate_plan(job_request_payload: dict) -> None:
    try:
        job_request = JobUserRequest(**job_request_payload)
    except Exception as exc:
        logger.error(WorkerLog(
            operation="generate_plan",
            event="Invalid request payload",
            error=Logger.serialize_error(exc),
        ), exc_info=exc)
        raise

    job_id = job_request.job.job_id

    try:
        logger.info(WorkerLog(
            operation="generate_plan",
            event="Planning started",
            job_id=str(job_id),
        ))
        transition_job(job_id, job_request.job.status, JobStatus.PLANNING)

        system_prompt = PLAN_SYSTEM_PROMPT
        user_query = str(job_request.user_request)
        planning_capabilities = load_planning_capabilities(user_query)
        if planning_capabilities:
            human_content = f"{user_query}\n\n{planning_capabilities}"
        else:
            human_content = user_query
        started_at = time.perf_counter()
        plan, usage = OpenRouterService.invoke_structured(
            job_id=job_id,
            stage=JobStatus.PLANNING,
            call_type=CallType.PLAN,
            model=OPENROUTER_MODELS.PLAN_MODEL,
            messages=[
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_content),
            ],
            schema=VideoPlan,
            max_tokens=LLM_PLAN_OUTPUT_MAX_TOKENS,
        )
        logger.info(WorkerLog(
            operation="generate_plan",
            event="OpenRouter call completed",
            job_id=str(job_id),
            context={
                "provider": LLM_PROVIDER.OPENROUTER.value,
                "model": OPENROUTER_MODELS.PLAN_MODEL.value,
                "call_type": CallType.PLAN.value,
                "duration_ms": round((time.perf_counter() - started_at) * 1000, 2),
                "input_tokens": usage.input_tokens,
                "reasoning_tokens": usage.reasoning_tokens,
                "output_tokens": usage.output_tokens,
                "total_tokens": usage.total_tokens,
            },
        ))

        with get_worker_cursor() as cursor:
            PlansRepository.create_plan(cursor, job_id, plan)

        transition_job(job_id, JobStatus.PLANNING, JobStatus.PLANNED)
        logger.info(WorkerLog(
            operation="generate_plan",
            event="Planning completed",
            job_id=str(job_id),
        ))

    except QuotaExceededError as exc:
        transition_job(job_id, JobStatus.PLANNING, JobStatus.FAILED_QUOTA_EXCEEDED)
        logger.error(WorkerLog(
            operation="generate_plan",
            event="Planning quota exceeded",
            job_id=str(job_id),
            error=Logger.serialize_error(exc),
        ), exc_info=exc)
        raise

    except LLMCallException as exc:
        transition_job(job_id, JobStatus.PLANNING, JobStatus.FAILED_LLM_CALL)
        logger.error(WorkerLog(
            operation="generate_plan",
            event="Planning failed due to LLM call error",
            job_id=str(job_id),
            error=Logger.serialize_error(exc),
        ), exc_info=exc)
        raise

    except LLMUsageException as exc:
        transition_job(job_id, JobStatus.PLANNING, JobStatus.FAILED_LLM_USAGE)
        logger.error(WorkerLog(
            operation="generate_plan",
            event="Planning failed due to LLM usage error",
            job_id=str(job_id),
            error=Logger.serialize_error(exc),
        ), exc_info=exc)
        raise

    except Exception as exc:
        transition_job(job_id, JobStatus.PLANNING, JobStatus.FAILED_PLANNING)
        logger.error(WorkerLog(
            operation="generate_plan",
            event="Planning failed due to unexpected error",
            job_id=str(job_id),
            error=Logger.serialize_error(exc),
        ), exc_info=exc)
        raise
