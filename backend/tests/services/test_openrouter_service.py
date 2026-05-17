from contextlib import contextmanager
from uuid import uuid4

import pytest
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

from app.configs.llm_settings import OPENROUTER_DAILY_CALL_LIMIT, OPENROUTER_MODELS
from app.domain.job_state import JobStatus
from app.exceptions.llm_usage_exception import LLMUsageException
from app.exceptions.quota_exceeded_error import QuotaExceededError
from app.services.llm_service import CallType
from app.services.openrouter_service import OpenRouterService, OpenRouterTokenUsage


class SampleStructuredResponse(BaseModel):
    value: str


@contextmanager
def _cursor_ctx():
    yield object()


def test_claim_call_locks_counts_and_inserts_when_below_limit(monkeypatch: pytest.MonkeyPatch):
    # Given
    from app.services import openrouter_service as service_module

    call_order: list[str] = []
    captured: dict = {}
    monkeypatch.setattr(service_module, "get_worker_cursor", _cursor_ctx)
    monkeypatch.setattr(
        service_module.TokenLedgerRepository,
        "acquire_daily_lock",
        staticmethod(lambda cursor: call_order.append("lock")),
    )
    monkeypatch.setattr(
        service_module.TokenLedgerRepository,
        "count_openrouter_calls",
        staticmethod(lambda cursor, day: call_order.append("count") or OPENROUTER_DAILY_CALL_LIMIT - 1),
    )
    monkeypatch.setattr(
        service_module.TokenLedgerRepository,
        "claim_openrouter_call",
        staticmethod(lambda cursor, **kwargs: (call_order.append("claim"), captured.update(kwargs))),
    )

    job_id = uuid4()

    # When
    call_id = OpenRouterService.claim_call(
        job_id=job_id,
        stage=JobStatus.CODEGEN,
        call_type=CallType.CODEGEN,
        model=OPENROUTER_MODELS.CODING_MODEL,
    )

    # Then
    assert call_order == ["lock", "count", "claim"]
    assert captured["call_id"] == call_id
    assert captured["job_id"] == job_id
    assert captured["stage"] == JobStatus.CODEGEN.value
    assert captured["call_type"] == CallType.CODEGEN.value
    assert captured["model"] == OPENROUTER_MODELS.CODING_MODEL.value


def test_claim_call_raises_quota_exceeded_at_limit(monkeypatch: pytest.MonkeyPatch):
    # Given
    from app.services import openrouter_service as service_module

    claim_called = {"called": False}
    monkeypatch.setattr(service_module, "get_worker_cursor", _cursor_ctx)
    monkeypatch.setattr(
        service_module.TokenLedgerRepository,
        "acquire_daily_lock",
        staticmethod(lambda cursor: None),
    )
    monkeypatch.setattr(
        service_module.TokenLedgerRepository,
        "count_openrouter_calls",
        staticmethod(lambda cursor, day: OPENROUTER_DAILY_CALL_LIMIT),
    )
    monkeypatch.setattr(
        service_module.TokenLedgerRepository,
        "claim_openrouter_call",
        staticmethod(lambda cursor, **kwargs: claim_called.update({"called": True})),
    )

    # When / Then
    with pytest.raises(QuotaExceededError):
        OpenRouterService.claim_call(
            job_id=uuid4(),
            stage=JobStatus.CODEGEN,
            call_type=CallType.CODEGEN,
            model=OPENROUTER_MODELS.CODING_MODEL,
        )

    assert claim_called["called"] is False


def test_invoke_records_token_telemetry(monkeypatch: pytest.MonkeyPatch):
    # Given
    from app.services import openrouter_service as service_module

    call_id = uuid4()
    recorded = {}

    class FakeResponse:
        content = "from manim import *"
        usage_metadata = {
            "input_tokens": 10,
            "output_tokens": 20,
            "total_tokens": 35,
            "output_token_details": {"reasoning": 5},
        }

    class FakeClient:
        def invoke(self, messages):
            return FakeResponse()

    monkeypatch.setattr(
        OpenRouterService,
        "claim_call",
        staticmethod(lambda **kwargs: call_id),
    )
    monkeypatch.setattr(
        OpenRouterService,
        "get_client",
        staticmethod(lambda **kwargs: FakeClient()),
    )
    monkeypatch.setattr(
        service_module.TokenLedgerRepository,
        "record_openrouter_usage",
        staticmethod(lambda cursor, **kwargs: recorded.update(kwargs)),
    )
    monkeypatch.setattr(service_module, "get_worker_cursor", _cursor_ctx)

    # When
    response, usage = OpenRouterService.invoke(
        job_id=uuid4(),
        stage=JobStatus.CODEGEN,
        call_type=CallType.CODEGEN,
        model=OPENROUTER_MODELS.CODING_MODEL,
        messages=[HumanMessage(content="generate code")],
        max_tokens=100,
    )

    # Then
    assert response.content == "from manim import *"
    assert usage.input_tokens == 10
    assert usage.output_tokens == 20
    assert usage.reasoning_tokens == 5
    assert usage.total_tokens == 35
    assert recorded["call_id"] == call_id
    assert recorded["usage"] == usage


def test_invoke_structured_returns_schema_instance_and_records_token_telemetry(monkeypatch: pytest.MonkeyPatch):
    # Given
    from app.services import openrouter_service as service_module

    call_id = uuid4()
    recorded = {}

    class FakeRawResponse:
        usage_metadata = {
            "input_tokens": 12,
            "output_tokens": 8,
            "total_tokens": 20,
            "output_token_details": {"reasoning": 3},
        }

    class FakeStructuredClient:
        def invoke(self, messages):
            return {
                "parsed": SampleStructuredResponse(value="ok"),
                "raw": FakeRawResponse(),
            }

    class FakeClient:
        def with_structured_output(self, schema, include_raw):
            assert schema is SampleStructuredResponse
            assert include_raw is True
            return FakeStructuredClient()

    monkeypatch.setattr(
        OpenRouterService,
        "claim_call",
        staticmethod(lambda **kwargs: call_id),
    )
    monkeypatch.setattr(
        OpenRouterService,
        "get_client",
        staticmethod(lambda **kwargs: FakeClient()),
    )
    monkeypatch.setattr(
        service_module.TokenLedgerRepository,
        "record_openrouter_usage",
        staticmethod(lambda cursor, **kwargs: recorded.update(kwargs)),
    )
    monkeypatch.setattr(service_module, "get_worker_cursor", _cursor_ctx)

    # When
    parsed, usage = OpenRouterService.invoke_structured(
        job_id=uuid4(),
        stage=JobStatus.CODEGEN,
        call_type=CallType.DOCUMENT_SELECTION,
        model=OPENROUTER_MODELS.CODING_MODEL,
        messages=[HumanMessage(content="select docs")],
        schema=SampleStructuredResponse,
        max_tokens=100,
    )

    # Then
    assert parsed == SampleStructuredResponse(value="ok")
    assert usage.input_tokens == 12
    assert usage.output_tokens == 8
    assert usage.reasoning_tokens == 3
    assert usage.total_tokens == 20
    assert recorded["call_id"] == call_id
    assert recorded["usage"] == usage


def test_invoke_structured_raises_when_parsed_value_does_not_match_schema(monkeypatch: pytest.MonkeyPatch):
    # Given
    from app.services import openrouter_service as service_module

    call_id = uuid4()
    parsing_error = ValueError("bad structured output")

    class FakeRawResponse:
        usage_metadata = {
            "input_tokens": 4,
            "output_tokens": 6,
            "total_tokens": 10,
            "output_token_details": {},
        }

    class FakeStructuredClient:
        def invoke(self, messages):
            return {
                "parsed": {"value": "not a pydantic instance"},
                "raw": FakeRawResponse(),
                "parsing_error": parsing_error,
            }

    class FakeClient:
        def with_structured_output(self, schema, include_raw):
            return FakeStructuredClient()

    monkeypatch.setattr(
        OpenRouterService,
        "claim_call",
        staticmethod(lambda **kwargs: call_id),
    )
    monkeypatch.setattr(
        OpenRouterService,
        "get_client",
        staticmethod(lambda **kwargs: FakeClient()),
    )
    monkeypatch.setattr(
        service_module.TokenLedgerRepository,
        "record_openrouter_usage",
        staticmethod(lambda cursor, **kwargs: None),
    )
    monkeypatch.setattr(service_module, "get_worker_cursor", _cursor_ctx)

    # When / Then
    with pytest.raises(LLMUsageException) as exc_info:
        OpenRouterService.invoke_structured(
            job_id=uuid4(),
            stage=JobStatus.CODEGEN,
            call_type=CallType.DOCUMENT_SELECTION,
            model=OPENROUTER_MODELS.CODING_MODEL,
            messages=[HumanMessage(content="select docs")],
            schema=SampleStructuredResponse,
            max_tokens=100,
        )

    assert exc_info.value.__cause__ is parsing_error


def test_invoke_records_empty_usage_when_response_usage_cannot_be_extracted(monkeypatch: pytest.MonkeyPatch):
    # Given
    from app.services import openrouter_service as service_module

    call_id = uuid4()
    recorded = {}

    class FakeResponse:
        content = "from manim import *"

    class FakeClient:
        def invoke(self, messages):
            return FakeResponse()

    monkeypatch.setattr(
        OpenRouterService,
        "claim_call",
        staticmethod(lambda **kwargs: call_id),
    )
    monkeypatch.setattr(
        OpenRouterService,
        "get_client",
        staticmethod(lambda **kwargs: FakeClient()),
    )
    monkeypatch.setattr(
        service_module.TokenLedgerRepository,
        "record_openrouter_usage",
        staticmethod(lambda cursor, **kwargs: recorded.update(kwargs)),
    )
    monkeypatch.setattr(service_module, "get_worker_cursor", _cursor_ctx)

    # When
    response, usage = OpenRouterService.invoke(
        job_id=uuid4(),
        stage=JobStatus.CODEGEN,
        call_type=CallType.CODEGEN,
        model=OPENROUTER_MODELS.CODING_MODEL,
        messages=[HumanMessage(content="generate code")],
        max_tokens=100,
    )

    # Then
    assert response.content == "from manim import *"
    assert usage == OpenRouterTokenUsage()
    assert recorded["call_id"] == call_id
    assert recorded["usage"] == OpenRouterTokenUsage()
