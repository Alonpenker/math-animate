import time
from datetime import datetime, timezone
from typing import TypeVar
from uuid import UUID, uuid4

from langchain_core.messages import AIMessage, BaseMessage
from langchain_openai import ChatOpenAI
from openai import LengthFinishReasonError
from pydantic import BaseModel

from app.configs.app_settings import settings
from app.configs.llm_settings import (
    LLM_REASONING_EFFORT,
    OPENROUTER_BASE_URL,
    OPENROUTER_DAILY_CALL_LIMIT,
    OPENROUTER_MODELS,
)
from app.dependencies.db import get_worker_cursor
from app.domain.job_state import JobStatus
from app.exceptions.llm_usage_exception import LLMUsageException
from app.exceptions.quota_exceeded_error import QuotaExceededError
from app.repositories.token_repository import TokenLedgerRepository
from app.services.llm_service import CallType
from app.utils.llm_stubs import IS_E2E_MODE, STUB_BROKEN_CODE, STUB_FIXED_CODE, STUB_PLAN
from app.utils.logging import Logger, WorkerLog, WorkerOperation

logger = Logger.get_logger("worker")
StructuredModel = TypeVar("StructuredModel", bound=BaseModel)


class OpenRouterTokenUsage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0
    total_tokens: int = 0


class OpenRouterService:
    @staticmethod
    def get_client(
        *,
        model: OPENROUTER_MODELS,
        max_tokens: int | None = None,
    ) -> ChatOpenAI:
        kwargs = {
            "model": model.value,
            "base_url": OPENROUTER_BASE_URL,
            "api_key": settings.openrouter_api_key.get_secret_value(),
            "max_tokens": max_tokens,
            "extra_body": {
                "reasoning": {
                    "effort": LLM_REASONING_EFFORT.HIGH.value,
                }
            },
        }
        return ChatOpenAI(**kwargs)

    @staticmethod
    def claim_call(
        *,
        job_id: UUID,
        stage: JobStatus,
        call_type: CallType,
        model: OPENROUTER_MODELS,
    ) -> UUID:
        call_id = uuid4()
        day = datetime.now(timezone.utc).date()
        with get_worker_cursor() as cursor:
            TokenLedgerRepository.acquire_daily_lock(cursor)
            count = TokenLedgerRepository.count_openrouter_calls(cursor, day)
            if count >= OPENROUTER_DAILY_CALL_LIMIT:
                raise QuotaExceededError(
                    limit=OPENROUTER_DAILY_CALL_LIMIT,
                    consumed=count,
                    reserved=0,
                    requested=1,
                )
            TokenLedgerRepository.claim_openrouter_call(
                cursor,
                call_id=call_id,
                day=day,
                job_id=job_id,
                stage=stage.value,
                call_type=call_type.value,
                model=model.value,
            )
        return call_id

    @staticmethod
    def _record_usage(call_id: UUID, usage: OpenRouterTokenUsage) -> None:
        with get_worker_cursor() as cursor:
            TokenLedgerRepository.record_openrouter_usage(
                cursor,
                call_id=call_id,
                usage=usage,
            )

    @staticmethod
    def _usage_from_response(response) -> OpenRouterTokenUsage:
        usage_metadata = getattr(response, "usage_metadata", None)
        if usage_metadata is None:
            raise RuntimeError(
                "Could not extract token usage from OpenRouter response. "
                f"response_type={type(response).__name__}"
            )
        input_tokens = int(usage_metadata.get("input_tokens", 0))
        output_tokens = int(usage_metadata.get("output_tokens", 0))
        total_tokens = int(usage_metadata.get("total_tokens", 0))
        output_details = usage_metadata.get("output_token_details", {})
        reasoning_tokens = int(output_details.get("reasoning", 0))
        return OpenRouterTokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            reasoning_tokens=reasoning_tokens,
            total_tokens=total_tokens or input_tokens + output_tokens,
        )

    @staticmethod
    def _usage_from_exc(exc: BaseException) -> OpenRouterTokenUsage:
        completion = getattr(exc, "completion", None)
        usage = getattr(completion, "usage", None)
        if usage is None:
            raise RuntimeError(
                "Could not extract token usage from OpenRouter exception. "
                f"exception_type={type(exc).__name__}"
            )
        input_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
        output_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
        total_tokens = int(getattr(usage, "total_tokens", 0) or 0)
        completion_details = getattr(usage, "completion_tokens_details", None)
        reasoning_tokens = int(getattr(completion_details, "reasoning_tokens", 0) or 0)
        return OpenRouterTokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            reasoning_tokens=reasoning_tokens,
            total_tokens=total_tokens or input_tokens + output_tokens,
        )

    @staticmethod
    def _raise_if_output_limit_hit(
        *,
        call_type: CallType,
        usage: OpenRouterTokenUsage,
        max_tokens: int | None,
    ) -> None:
        if max_tokens is not None and usage.output_tokens >= max_tokens:
            raise LLMUsageException(
                f"LLM call '{call_type.value}' hit the max token limit ({max_tokens}). "
                "Output is likely truncated and unusable.",
                total_tokens=usage.total_tokens,
            )

    @staticmethod
    def _extract_structured_response(
        *,
        result,
        schema: type[StructuredModel],
        usage: OpenRouterTokenUsage,
        operation: WorkerOperation,
    ) -> StructuredModel:
        if isinstance(result, schema):
            return result

        parsing_error = None
        parsed = result
        if isinstance(result, dict):
            parsed = result.get("parsed")
            parsing_error = result.get("parsing_error")
            if isinstance(parsed, schema):
                return parsed

        logger.warning(WorkerLog(
            operation=operation,
            event="LLM output validation failed: response is not a valid instance",
            context={
                "parsed_type": type(parsed).__name__,
                "expected_type": schema.__name__,
            },
        ))
        exception = LLMUsageException(
            f"LLM output validation failed: response is not a valid instance (parsed_type={type(parsed).__name__}, expected {schema.__name__}).",
            total_tokens=usage.total_tokens,
        )
        if isinstance(parsing_error, BaseException):
            raise exception from parsing_error
        raise exception

    @staticmethod
    def invoke(
        *,
        job_id: UUID,
        stage: JobStatus,
        call_type: CallType,
        model: OPENROUTER_MODELS,
        messages: list[BaseMessage],
        max_tokens: int | None = None,
    ) -> tuple[BaseMessage, OpenRouterTokenUsage]:
        if IS_E2E_MODE:
            content = STUB_FIXED_CODE if call_type == CallType.FIX else STUB_BROKEN_CODE
            return AIMessage(content=content), OpenRouterTokenUsage()

        operation: WorkerOperation = (
            "generate_plan_openrouter"
            if call_type == CallType.PLAN
            else "generate_code_langgraph"
        )
        call_id = OpenRouterService.claim_call(
            job_id=job_id,
            stage=stage,
            call_type=call_type,
            model=model,
        )
        started_at = time.perf_counter()
        try:
            client = OpenRouterService.get_client(model=model, max_tokens=max_tokens)
            response = client.invoke(messages)
        except Exception as exc:
            try:
                usage = OpenRouterService._usage_from_exc(exc)
            except Exception as usage_exc:
                logger.warning(WorkerLog(
                    operation=operation,
                    event="Failed to extract OpenRouter token usage",
                    job_id=str(job_id),
                    call_id=str(call_id),
                    error=Logger.serialize_error(usage_exc),
                    context={"call_type": call_type.value, "source": "exception"},
                ), exc_info=usage_exc)
                usage = OpenRouterTokenUsage()
            try:
                OpenRouterService._record_usage(call_id, usage)
            except Exception:
                logger.warning(WorkerLog(
                    operation=operation,
                    event="Failed to record OpenRouter usage after call failure",
                    job_id=str(job_id),
                    call_id=str(call_id),
                    context={"call_type": call_type.value},
                ), exc_info=True)
            message = (
                f"LLM call '{call_type.value}' exhausted its output token budget "
                f"({max_tokens}) before producing usable output."
                if isinstance(exc, LengthFinishReasonError)
                else f"LLM call '{call_type.value}' failed before producing usable output."
            )
            duration_ms = int((time.perf_counter() - started_at) * 1000)
            logger.warning(WorkerLog(
                operation=operation,
                event="OpenRouter call failed",
                job_id=str(job_id),
                call_id=str(call_id),
                error=Logger.serialize_error(exc),
                context={"call_type": call_type.value, "duration_ms": duration_ms},
            ), exc_info=exc)
            raise LLMUsageException(message, total_tokens=usage.total_tokens) from exc

        try:
            usage = OpenRouterService._usage_from_response(response)
        except Exception as usage_exc:
            logger.warning(WorkerLog(
                operation=operation,
                event="Failed to extract OpenRouter token usage",
                job_id=str(job_id),
                call_id=str(call_id),
                error=Logger.serialize_error(usage_exc),
                context={"call_type": call_type.value, "source": "response"},
            ), exc_info=usage_exc)
            usage = OpenRouterTokenUsage()
        OpenRouterService._record_usage(call_id, usage)
        OpenRouterService._raise_if_output_limit_hit(
            call_type=call_type,
            usage=usage,
            max_tokens=max_tokens,
        )
        return response, usage

    @staticmethod
    def invoke_structured(
        *,
        job_id: UUID,
        stage: JobStatus,
        call_type: CallType,
        model: OPENROUTER_MODELS,
        messages: list[BaseMessage],
        schema: type[StructuredModel],
        max_tokens: int | None = None,
    ) -> tuple[StructuredModel, OpenRouterTokenUsage]:
        operation: WorkerOperation = (
            "generate_plan_openrouter"
            if call_type == CallType.PLAN
            else "generate_code_langgraph"
        )
        if IS_E2E_MODE:
            if schema.__name__ == "VideoPlan":
                parsed = STUB_PLAN
            else:
                parsed = schema(selected_titles=[])
            usage = OpenRouterTokenUsage()
            return OpenRouterService._extract_structured_response(
                result={"parsed": parsed, "raw": AIMessage(content="")},
                schema=schema,
                usage=usage,
                operation=operation,
            ), usage

        call_id = OpenRouterService.claim_call(
            job_id=job_id,
            stage=stage,
            call_type=call_type,
            model=model,
        )
        started_at = time.perf_counter()
        try:
            client = OpenRouterService.get_client(model=model, max_tokens=max_tokens)
            structured_client = client.with_structured_output(schema, include_raw=True)
            result = structured_client.invoke(messages)
        except Exception as exc:
            try:
                usage = OpenRouterService._usage_from_exc(exc)
            except Exception as usage_exc:
                logger.warning(WorkerLog(
                    operation=operation,
                    event="Failed to extract OpenRouter token usage",
                    job_id=str(job_id),
                    call_id=str(call_id),
                    error=Logger.serialize_error(usage_exc),
                    context={"call_type": call_type.value, "source": "exception"},
                ), exc_info=usage_exc)
                usage = OpenRouterTokenUsage()
            try:
                OpenRouterService._record_usage(call_id, usage)
            except Exception:
                logger.warning(WorkerLog(
                    operation=operation,
                    event="Failed to record OpenRouter usage after call failure",
                    job_id=str(job_id),
                    call_id=str(call_id),
                    context={"call_type": call_type.value},
                ), exc_info=True)
            message = (
                f"LLM call '{call_type.value}' exhausted its output token budget "
                f"({max_tokens}) before producing usable output."
                if isinstance(exc, LengthFinishReasonError)
                else f"LLM call '{call_type.value}' failed before producing usable output."
            )
            duration_ms = int((time.perf_counter() - started_at) * 1000)
            logger.warning(WorkerLog(
                operation=operation,
                event="OpenRouter call failed",
                job_id=str(job_id),
                call_id=str(call_id),
                error=Logger.serialize_error(exc),
                context={"call_type": call_type.value, "duration_ms": duration_ms},
            ), exc_info=exc)
            raise LLMUsageException(message, total_tokens=usage.total_tokens) from exc

        raw_response = result.get("raw") if isinstance(result, dict) else result
        try:
            usage = OpenRouterService._usage_from_response(raw_response)
        except Exception as usage_exc:
            logger.warning(WorkerLog(
                operation=operation,
                event="Failed to extract OpenRouter token usage",
                job_id=str(job_id),
                call_id=str(call_id),
                error=Logger.serialize_error(usage_exc),
                context={"call_type": call_type.value, "source": "response"},
            ), exc_info=usage_exc)
            usage = OpenRouterTokenUsage()
        OpenRouterService._record_usage(call_id, usage)
        OpenRouterService._raise_if_output_limit_hit(
            call_type=call_type,
            usage=usage,
            max_tokens=max_tokens,
        )
        return OpenRouterService._extract_structured_response(
            result=result,
            schema=schema,
            usage=usage,
            operation=operation,
        ), usage
