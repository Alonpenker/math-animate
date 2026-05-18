import time
from datetime import datetime, timezone
from typing import TypeVar
from uuid import UUID, uuid4

from langchain_core.messages import AIMessage, BaseMessage
from langchain_openrouter import ChatOpenRouter
import openrouter
from openrouter.utils import BackoffStrategy, RetryConfig
from openai import LengthFinishReasonError
from pydantic import BaseModel

from app.configs.app_settings import APP_NAME, settings
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
        reasoning_effort: LLM_REASONING_EFFORT | None = LLM_REASONING_EFFORT.HIGH,
        require_parameters: bool = False,
    ) -> ChatOpenRouter:
        client = openrouter.OpenRouter(
            api_key=settings.openrouter_api_key.get_secret_value(),
            server_url=OPENROUTER_BASE_URL,
            http_referer=settings.frontend_url,
            x_open_router_title=APP_NAME,
            retry_config=RetryConfig(
                strategy="backoff",
                backoff=BackoffStrategy(
                    initial_interval=500,
                    max_interval=60000,
                    exponent=1.5,
                    max_elapsed_time=2 * 150_000,
                ),
                retry_connection_errors=True,
            ),
        )
        kwargs = {
            "model": model.value,
            "api_key": settings.openrouter_api_key.get_secret_value(),
            "client": client,
            "app_url": None,
            "app_title": None,
            "max_tokens": max_tokens,
        }
        if reasoning_effort is not None:
            kwargs["reasoning"] = {
                "effort": reasoning_effort.value,
            }
        if require_parameters:
            kwargs["openrouter_provider"] = {"require_parameters": True}
        return ChatOpenRouter(**kwargs)

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
        reasoning_tokens = int(output_details.get("reasoning") or 0)
        return OpenRouterTokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            reasoning_tokens=reasoning_tokens,
            total_tokens=total_tokens or input_tokens + output_tokens,
        )

    @staticmethod
    def _usage_from_exc(exc: BaseException) -> OpenRouterTokenUsage:
        response = getattr(exc, "response", None)
        usage = getattr(response, "usage", None)
        if usage is None:
            body = getattr(exc, "body", None)
            if isinstance(body, dict):
                usage = body.get("usage")
        if usage is None:
            data = getattr(exc, "data", None)
            if isinstance(data, dict):
                usage = data.get("usage")
        if usage is None:
            usage = getattr(exc, "usage", None)
        if usage is None:
            raise RuntimeError(
                "Could not extract token usage from OpenRouter exception. "
                f"exception_type={type(exc).__name__}"
            )
        if isinstance(usage, dict):
            input_tokens = int(usage.get("prompt_tokens", 0) or 0)
            output_tokens = int(usage.get("completion_tokens", 0) or 0)
            total_tokens = int(usage.get("total_tokens", 0) or 0)
            completion_details = usage.get("completion_tokens_details") or {}
            reasoning_tokens = int(completion_details.get("reasoning_tokens") or 0)
        else:
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
    def _content_length(content) -> int:
        if isinstance(content, str):
            return len(content)
        if isinstance(content, list):
            return sum(len(str(part)) for part in content)
        if content is None:
            return 0
        return len(str(content))

    @staticmethod
    def _structured_failure_context(
        *,
        parsed,
        schema: type[StructuredModel],
        raw_response,
        parsing_error,
        usage: OpenRouterTokenUsage,
    ) -> dict:
        context = {
            "parsed_type": type(parsed).__name__,
            "expected_type": schema.__name__,
            "input_tokens": usage.input_tokens,
            "reasoning_tokens": usage.reasoning_tokens,
            "output_tokens": usage.output_tokens,
            "total_tokens": usage.total_tokens,
        }
        if raw_response is not None:
            content = getattr(raw_response, "content", None)
            content_length = OpenRouterService._content_length(content)
            additional_kwargs = getattr(raw_response, "additional_kwargs", {}) or {}
            reasoning_content = additional_kwargs.get("reasoning_content")
            response_metadata = getattr(raw_response, "response_metadata", {}) or {}
            context.update({
                "raw_type": type(raw_response).__name__,
                "raw_content_type": type(content).__name__,
                "raw_content_length": content_length,
                "raw_content_empty": content_length == 0,
                "reasoning_content_length": OpenRouterService._content_length(
                    reasoning_content
                ),
                "additional_kwargs_keys": sorted(additional_kwargs.keys()),
                "finish_reason": response_metadata.get("finish_reason"),
                "native_finish_reason": response_metadata.get("native_finish_reason"),
                "tool_call_count": len(getattr(raw_response, "tool_calls", []) or []),
                "invalid_tool_call_count": len(
                    getattr(raw_response, "invalid_tool_calls", []) or []
                ),
            })
        if isinstance(parsing_error, BaseException):
            context.update({
                "parsing_error_type": type(parsing_error).__name__,
                "parsing_error_message": str(parsing_error)[:500],
            })
        return context

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
        raw_response = None
        if isinstance(result, dict):
            parsed = result.get("parsed")
            raw_response = result.get("raw")
            parsing_error = result.get("parsing_error")
            if isinstance(parsed, schema):
                return parsed

        context = OpenRouterService._structured_failure_context(
            parsed=parsed,
            schema=schema,
            raw_response=raw_response,
            parsing_error=parsing_error,
            usage=usage,
        )
        logger.warning(WorkerLog(
            operation=operation,
            event="LLM output validation failed: response is not a valid instance",
            context=context,
        ))
        message = (
            f"LLM output validation failed: response is not a valid instance "
            f"(parsed_type={type(parsed).__name__}, expected {schema.__name__})."
        )
        if (
            context.get("raw_content_empty") is True
            and usage.reasoning_tokens > 0
            and usage.reasoning_tokens >= usage.output_tokens
        ):
            message = (
                "LLM output validation failed: provider returned reasoning tokens "
                f"but no assistant content to parse (expected {schema.__name__})."
            )
        exception = LLMUsageException(
            message,
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
        reasoning_effort: LLM_REASONING_EFFORT | None = LLM_REASONING_EFFORT.HIGH,
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
            client = OpenRouterService.get_client(
                model=model,
                max_tokens=max_tokens,
                reasoning_effort=reasoning_effort,
            )
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
            client = OpenRouterService.get_client(
                model=model,
                max_tokens=max_tokens,
                reasoning_effort=None,
                require_parameters=True,
            )
            structured_client = client.with_structured_output(
                schema,
                method="json_schema",
                strict=True,
                include_raw=True,
            )
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
