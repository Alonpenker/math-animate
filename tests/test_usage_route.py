from datetime import date, timezone, datetime
from uuid import uuid4

import pytest

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
    model: str = "gpt-4o",
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


# ── Normal state ───────────────────────────────────────────────


def test_normal_state_mixed_released_and_active(
    usage_routes_with_mocks,
    fake_cursor,
    test_store,
):
    test_store["token_ledger"].extend([
        _ledger_row(state="RELEASED", consumed_tokens=50_000, reserved_tokens=60_000,
                    stage="planning"),
        _ledger_row(state="ACTIVE", reserved_tokens=10_000, stage="codegen"),
        _ledger_row(state="RELEASED", consumed_tokens=20_000, reserved_tokens=25_000,
                    stage="codegen"),
    ])

    result = usage_routes_with_mocks.get_usage(cursor=fake_cursor)

    assert isinstance(result, TokenUsageResponse)
    assert result.consumed == 70_000
    assert result.reserved == 10_000
    assert result.remaining == DAILY_TOKEN_LIMIT - 70_000 - 10_000
    assert len(result.breakdown) > 0
    assert result.day == _today()


# ── Empty state ────────────────────────────────────────────────


def test_empty_state_no_rows(
    usage_routes_with_mocks,
    fake_cursor,
    test_store,
):
    result = usage_routes_with_mocks.get_usage(cursor=fake_cursor)

    assert result.consumed == 0
    assert result.reserved == 0
    assert result.remaining == DAILY_TOKEN_LIMIT
    assert result.breakdown == []
    assert result.soft_threshold_exceeded is False


# ── Concurrent state ──────────────────────────────────────────


def test_concurrent_state_active_rows_reduce_remaining(
    usage_routes_with_mocks,
    fake_cursor,
    test_store,
):
    test_store["token_ledger"].extend([
        _ledger_row(state="ACTIVE", reserved_tokens=30_000, stage="planning"),
        _ledger_row(state="ACTIVE", reserved_tokens=20_000, stage="codegen"),
    ])

    result = usage_routes_with_mocks.get_usage(cursor=fake_cursor)

    assert result.reserved == 50_000
    assert result.consumed == 0
    assert result.remaining == DAILY_TOKEN_LIMIT - 50_000


# ── Soft threshold breach ─────────────────────────────────────


def test_soft_threshold_exceeded(
    usage_routes_with_mocks,
    fake_cursor,
    test_store,
):
    soft_threshold = int(DAILY_TOKEN_LIMIT * SOFT_THRESHOLD_RATIO)

    test_store["token_ledger"].extend([
        _ledger_row(state="RELEASED", consumed_tokens=soft_threshold,
                    reserved_tokens=soft_threshold),
    ])

    result = usage_routes_with_mocks.get_usage(cursor=fake_cursor)

    assert result.soft_threshold_exceeded is True


# ── At hard limit ─────────────────────────────────────────────


def test_at_hard_limit_remaining_is_zero(
    usage_routes_with_mocks,
    fake_cursor,
    test_store,
):
    test_store["token_ledger"].extend([
        _ledger_row(state="RELEASED", consumed_tokens=DAILY_TOKEN_LIMIT,
                    reserved_tokens=DAILY_TOKEN_LIMIT),
    ])

    result = usage_routes_with_mocks.get_usage(cursor=fake_cursor)

    assert result.remaining == 0
    assert result.soft_threshold_exceeded is True
