from contextlib import contextmanager
from uuid import uuid4

import pytest
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

from app.configs.llm_settings import OPENROUTER_DAILY_CALL_LIMIT, OPENROUTER_MODELS
from app.domain.job_state import JobStatus
from app.exceptions.llm_call_exception import LLMCallException
from app.exceptions.llm_usage_exception import LLMUsageException
from app.exceptions.quota_exceeded_error import QuotaExceededError
from app.services.openrouter_service import CallType
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
        def with_structured_output(self, schema, method, strict, include_raw):
            assert schema is SampleStructuredResponse
            assert method == "json_schema"
            assert strict is True
            assert include_raw is True
            return FakeStructuredClient()

    captured_client_kwargs = {}
    monkeypatch.setattr(
        OpenRouterService,
        "claim_call",
        staticmethod(lambda **kwargs: call_id),
    )
    monkeypatch.setattr(
        OpenRouterService,
        "get_client",
        staticmethod(
            lambda **kwargs: captured_client_kwargs.update(kwargs) or FakeClient()
        ),
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
    assert captured_client_kwargs["reasoning_effort"] is None
    assert captured_client_kwargs["require_parameters"] is True


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
        def with_structured_output(self, schema, method, strict, include_raw):
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
    with pytest.raises(LLMCallException) as exc_info:
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


def test_usage_from_response_extracts_all_token_types():
    # Given
    class FakeResponse:
        usage_metadata = {
            "input_tokens": 25,
            "output_tokens": 75,
            "total_tokens": 105,
            "output_token_details": {"reasoning": 40},
        }

    # When
    usage = OpenRouterService._usage_from_response(FakeResponse())

    # Then
    assert usage.input_tokens == 25
    assert usage.output_tokens == 75
    assert usage.reasoning_tokens == 40
    assert usage.total_tokens == 105


def test_usage_from_response_defaults_to_zero_when_fields_missing():
    # Given
    class FakeResponse:
        usage_metadata = {}

    # When
    usage = OpenRouterService._usage_from_response(FakeResponse())

    # Then
    assert usage.input_tokens == 0
    assert usage.output_tokens == 0
    assert usage.reasoning_tokens == 0
    assert usage.total_tokens == 0


def test_usage_from_response_raises_when_no_usage_metadata():
    # Given
    class FakeResponse:
        usage_metadata = None

    # When / Then
    with pytest.raises(RuntimeError, match="Could not extract token usage"):
        OpenRouterService._usage_from_response(FakeResponse())


def test_usage_from_exc_extracts_from_dict_usage():
    # Given
    class FakeExc(Exception):
        def __init__(self):
            self.response = None
            self.body = {
                "usage": {
                    "prompt_tokens": 30,
                    "completion_tokens": 70,
                    "total_tokens": 100,
                    "completion_tokens_details": {"reasoning_tokens": 25},
                }
            }

    # When
    usage = OpenRouterService._usage_from_exc(FakeExc())

    # Then
    assert usage.input_tokens == 30
    assert usage.output_tokens == 70
    assert usage.total_tokens == 100
    assert usage.reasoning_tokens == 25


def test_usage_from_exc_extracts_from_object_usage():
    # Given
    class FakeUsage:
        prompt_tokens = 40
        completion_tokens = 60
        total_tokens = 100
        completion_tokens_details = type('obj', (), {'reasoning_tokens': 20})()

    class FakeExc(Exception):
        def __init__(self):
            self.response = None
            self.body = None
            self.data = None
            self.usage = FakeUsage()

    # When
    usage = OpenRouterService._usage_from_exc(FakeExc())

    # Then
    assert usage.input_tokens == 40
    assert usage.output_tokens == 60
    assert usage.total_tokens == 100
    assert usage.reasoning_tokens == 20


def test_usage_from_exc_raises_when_no_usage_found():
    # Given
    class FakeExc(Exception):
        def __init__(self):
            self.response = None
            self.body = None
            self.data = None
            self.usage = None

    # When / Then
    with pytest.raises(RuntimeError, match="Could not extract token usage from OpenRouter exception"):
        OpenRouterService._usage_from_exc(FakeExc())


def test_raise_if_output_limit_hit_raises_when_output_exceeds_max():
    # Given
    usage = OpenRouterTokenUsage(
        input_tokens=10,
        output_tokens=100,
        reasoning_tokens=0,
        total_tokens=110,
    )

    # When / Then
    with pytest.raises(LLMUsageException, match="hit the max token limit"):
        OpenRouterService._raise_if_output_limit_hit(
            call_type=CallType.CODEGEN,
            usage=usage,
            max_tokens=100,
        )


def test_raise_if_output_limit_hit_does_not_raise_when_below_limit():
    # Given
    usage = OpenRouterTokenUsage(
        input_tokens=10,
        output_tokens=50,
        reasoning_tokens=0,
        total_tokens=60,
    )

    # When / Then - should not raise
    OpenRouterService._raise_if_output_limit_hit(
        call_type=CallType.CODEGEN,
        usage=usage,
        max_tokens=100,
    )


def test_raise_if_output_limit_hit_does_not_raise_when_max_tokens_is_none():
    # Given
    usage = OpenRouterTokenUsage(
        input_tokens=10,
        output_tokens=5000,
        reasoning_tokens=0,
        total_tokens=5010,
    )

    # When / Then - should not raise
    OpenRouterService._raise_if_output_limit_hit(
        call_type=CallType.CODEGEN,
        usage=usage,
        max_tokens=None,
    )


def test_content_length_returns_length_for_string():
    # When
    result = OpenRouterService._content_length("hello world")

    # Then
    assert result == 11


def test_content_length_returns_sum_for_list():
    # When
    result = OpenRouterService._content_length(["hello", " ", "world"])

    # Then
    assert result == 11


def test_content_length_returns_zero_for_none():
    # When
    result = OpenRouterService._content_length(None)

    # Then
    assert result == 0


def test_get_client_includes_reasoning_when_effort_provided():
    # When
    client = OpenRouterService.get_client(
        model=OPENROUTER_MODELS.CODING_MODEL,
        max_tokens=1000,
        reasoning_effort=None,
    )

    # Then
    assert client is not None


def test_invoke_raises_llm_usage_exception_on_length_finish_reason_error(monkeypatch: pytest.MonkeyPatch):
    # Given — LengthFinishReasonError means the provider cut the response short due to token budget
    from app.services import openrouter_service as service_module

    class FakeLengthFinishReasonError(Exception):
        def __init__(self):
            super().__init__("length")
            self.response = None
            self.body = None
            self.data = None
            self.usage = None

    class FakeClient:
        def invoke(self, messages):
            raise FakeLengthFinishReasonError()

    monkeypatch.setattr(service_module, "LengthFinishReasonError", FakeLengthFinishReasonError)
    monkeypatch.setattr(OpenRouterService, "claim_call", staticmethod(lambda **kwargs: uuid4()))
    monkeypatch.setattr(OpenRouterService, "get_client", staticmethod(lambda **kwargs: FakeClient()))
    monkeypatch.setattr(
        service_module.TokenLedgerRepository,
        "record_openrouter_usage",
        staticmethod(lambda cursor, **kwargs: None),
    )
    monkeypatch.setattr(service_module, "get_worker_cursor", _cursor_ctx)

    # When / Then
    with pytest.raises(LLMUsageException, match="exhausted"):
        OpenRouterService.invoke(
            job_id=uuid4(),
            stage=JobStatus.CODEGEN,
            call_type=CallType.CODEGEN,
            model=OPENROUTER_MODELS.CODING_MODEL,
            messages=[HumanMessage(content="test")],
            max_tokens=100,
        )


def test_invoke_raises_llm_call_exception_on_client_failure(monkeypatch: pytest.MonkeyPatch):
    # Given
    from app.services import openrouter_service as service_module

    class FakeClient:
        def invoke(self, messages):
            exc = Exception("Client error")
            exc.response = None
            exc.body = None
            exc.data = None
            exc.usage = None
            raise exc

    monkeypatch.setattr(
        OpenRouterService,
        "claim_call",
        staticmethod(lambda **kwargs: uuid4()),
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
    with pytest.raises(LLMCallException, match="failed before producing usable output"):
        OpenRouterService.invoke(
            job_id=uuid4(),
            stage=JobStatus.CODEGEN,
            call_type=CallType.CODEGEN,
            model=OPENROUTER_MODELS.CODING_MODEL,
            messages=[HumanMessage(content="test")],
            max_tokens=100,
        )


