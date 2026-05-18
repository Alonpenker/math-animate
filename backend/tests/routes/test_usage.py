from datetime import date, datetime, timezone
from uuid import uuid4

from app.configs.llm_settings import LLM_PROVIDER, OPENROUTER_DAILY_CALL_LIMIT
from app.schemas.token_usage import TokenUsageResponse


def _today() -> date:
    return datetime.now(timezone.utc).date()


def _ledger_row(
    *,
    provider: str = LLM_PROVIDER.OPENROUTER.value,
    model: str = "openai/gpt-oss-120b:free",
    stage: str = "PLANNING",
    call_type: str = "plan",
    input_tokens: int = 0,
    output_tokens: int = 0,
    reasoning_tokens: int = 0,
    total_tokens: int = 0,
    day: date | None = None,
) -> dict:
    return {
        "call_id": uuid4(),
        "day": day or _today(),
        "job_id": uuid4(),
        "stage": stage,
        "provider": provider,
        "model": model,
        "call_type": call_type,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "reasoning_tokens": reasoning_tokens,
        "reserved_tokens": 0,
        "consumed_tokens": total_tokens,
        "state": "RELEASED",
    }


def test_get_usage_returns_openrouter_call_quota_and_token_telemetry(
    usage_routes_with_mocks,
    fake_cursor,
    test_store,
):
    test_store["token_ledger"].extend([
        _ledger_row(
            call_type="plan",
            input_tokens=100,
            output_tokens=200,
            reasoning_tokens=25,
            total_tokens=325,
        ),
        _ledger_row(
            model="poolside/laguna-m.1:free",
            stage="CODEGEN",
            call_type="document_selection",
            input_tokens=50,
            output_tokens=20,
            total_tokens=70,
        ),
        _ledger_row(
            model="poolside/laguna-m.1:free",
            stage="CODEGEN",
            call_type="codegen",
            input_tokens=300,
            output_tokens=700,
            reasoning_tokens=80,
            total_tokens=1080,
        ),
    ])

    result = usage_routes_with_mocks.get_usage(request=object(), cursor=fake_cursor)

    assert isinstance(result, TokenUsageResponse)
    assert result.day == _today()
    assert result.openrouter_calls == 3
    assert result.openrouter_call_limit == OPENROUTER_DAILY_CALL_LIMIT
    assert result.openrouter_calls_remaining == OPENROUTER_DAILY_CALL_LIMIT - 3
    assert result.token_totals.input_tokens == 450
    assert result.token_totals.output_tokens == 920
    assert result.token_totals.reasoning_tokens == 105
    assert result.token_totals.total_tokens == 1475
    assert {row.call_type for row in result.breakdown} == {"plan", "document_selection", "codegen"}


def test_get_usage_returns_full_call_capacity_when_no_openrouter_calls(
    usage_routes_with_mocks,
    fake_cursor,
):
    result = usage_routes_with_mocks.get_usage(request=object(), cursor=fake_cursor)

    assert result.openrouter_calls == 0
    assert result.openrouter_calls_remaining == OPENROUTER_DAILY_CALL_LIMIT
    assert result.token_totals.total_tokens == 0
    assert result.breakdown == []


def test_get_usage_ignores_legacy_openai_budget_rows(
    usage_routes_with_mocks,
    fake_cursor,
    test_store,
):
    test_store["token_ledger"].append(
        _ledger_row(
            provider=LLM_PROVIDER.OPENAI.value,
            model="gpt-5.2",
            call_type="unknown",
            input_tokens=1_000,
            output_tokens=1_000,
            total_tokens=2_000,
        )
    )

    result = usage_routes_with_mocks.get_usage(request=object(), cursor=fake_cursor)

    assert result.openrouter_calls == 0
    assert result.token_totals.total_tokens == 0
    assert result.breakdown == []


def test_get_usage_remaining_calls_never_goes_below_zero(
    usage_routes_with_mocks,
    fake_cursor,
    test_store,
):
    for _ in range(OPENROUTER_DAILY_CALL_LIMIT + 2):
        test_store["token_ledger"].append(_ledger_row())

    result = usage_routes_with_mocks.get_usage(request=object(), cursor=fake_cursor)

    assert result.openrouter_calls == OPENROUTER_DAILY_CALL_LIMIT + 2
    assert result.openrouter_calls_remaining == 0
