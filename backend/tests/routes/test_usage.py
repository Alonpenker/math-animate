from datetime import date, datetime, timezone
from uuid import uuid4

from app.configs.llm_settings import DAILY_TOKEN_LIMIT, SOFT_THRESHOLD_RATIO
from app.schemas.token_usage import TokenUsageResponse


def _today() -> date:
    return datetime.now(timezone.utc).date()


def _ledger_row(
    *,
    state: str,
    consumed_tokens: int = 0,
    reserved_tokens: int = 0,
    provider: str = "openai",
    model: str = "gpt-5.2",
    stage: str = "planning",
    day: date | None = None,
) -> dict:
    return {
        "call_id": uuid4(),
        "day": day or _today(),
        "job_id": uuid4(),
        "stage": stage,
        "provider": provider,
        "model": model,
        "reserved_tokens": reserved_tokens,
        "consumed_tokens": consumed_tokens,
        "state": state,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Normal state
# ─────────────────────────────────────────────────────────────────────────────

def test_get_usage_aggregates_consumed_and_reserved_from_ledger(
    usage_routes_with_mocks,
    fake_cursor,
    test_store,
):
    # Given
    test_store["token_ledger"].extend([
        _ledger_row(state="RELEASED", consumed_tokens=50_000, reserved_tokens=60_000, stage="planning"),
        _ledger_row(state="ACTIVE", reserved_tokens=10_000, stage="codegen"),
        _ledger_row(state="RELEASED", consumed_tokens=20_000, reserved_tokens=25_000, stage="codegen"),
    ])

    # When
    result = usage_routes_with_mocks.get_usage(cursor=fake_cursor)

    # Then
    assert isinstance(result, TokenUsageResponse)
    assert result.consumed == 70_000
    assert result.reserved == 10_000
    assert result.remaining == DAILY_TOKEN_LIMIT - 70_000 - 10_000
    assert len(result.breakdown) > 0
    assert result.day == _today()


# ─────────────────────────────────────────────────────────────────────────────
# Empty state
# ─────────────────────────────────────────────────────────────────────────────

def test_get_usage_returns_full_remaining_when_no_tokens_used(
    usage_routes_with_mocks,
    fake_cursor,
):
    # Given — empty ledger

    # When
    result = usage_routes_with_mocks.get_usage(cursor=fake_cursor)

    # Then
    assert result.consumed == 0
    assert result.reserved == 0
    assert result.remaining == DAILY_TOKEN_LIMIT
    assert result.breakdown == []
    assert result.soft_threshold_exceeded is False


# ─────────────────────────────────────────────────────────────────────────────
# Concurrent active reservations
# ─────────────────────────────────────────────────────────────────────────────

def test_get_usage_active_reservations_reduce_remaining_capacity(
    usage_routes_with_mocks,
    fake_cursor,
    test_store,
):
    # Given
    test_store["token_ledger"].extend([
        _ledger_row(state="ACTIVE", reserved_tokens=30_000, stage="planning"),
        _ledger_row(state="ACTIVE", reserved_tokens=20_000, stage="codegen"),
    ])

    # When
    result = usage_routes_with_mocks.get_usage(cursor=fake_cursor)

    # Then
    assert result.reserved == 50_000
    assert result.consumed == 0
    assert result.remaining == DAILY_TOKEN_LIMIT - 50_000


# ─────────────────────────────────────────────────────────────────────────────
# Soft threshold
# ─────────────────────────────────────────────────────────────────────────────

def test_get_usage_detects_soft_threshold_exceeded(
    usage_routes_with_mocks,
    fake_cursor,
    test_store,
):
    # Given
    soft_threshold = int(DAILY_TOKEN_LIMIT * SOFT_THRESHOLD_RATIO)
    test_store["token_ledger"].append(
        _ledger_row(state="RELEASED", consumed_tokens=soft_threshold, reserved_tokens=soft_threshold)
    )

    # When
    result = usage_routes_with_mocks.get_usage(cursor=fake_cursor)

    # Then
    assert result.soft_threshold_exceeded is True


# ─────────────────────────────────────────────────────────────────────────────
# Hard limit
# ─────────────────────────────────────────────────────────────────────────────

def test_get_usage_remaining_is_zero_at_hard_limit(
    usage_routes_with_mocks,
    fake_cursor,
    test_store,
):
    # Given
    test_store["token_ledger"].append(
        _ledger_row(
            state="RELEASED",
            consumed_tokens=DAILY_TOKEN_LIMIT,
            reserved_tokens=DAILY_TOKEN_LIMIT,
        )
    )

    # When
    result = usage_routes_with_mocks.get_usage(cursor=fake_cursor)

    # Then
    assert result.remaining == 0
    assert result.soft_threshold_exceeded is True
