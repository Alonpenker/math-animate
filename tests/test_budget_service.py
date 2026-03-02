from uuid import uuid4

import pytest

from app.configs.llm_settings import (
    DAILY_TOKEN_LIMIT,
    PLANNING_OUTPUT_BUFFER,
)
from app.exceptions.quota_exceeded_error import QuotaExceededError
from app.services.budget_service import BudgetService


def test_reserve_locks_then_checks_total_then_creates_reservation(
    monkeypatch: pytest.MonkeyPatch,
):
    from app.services import budget_service as budget_module

    call_order: list[str] = []
    captured: dict[str, object] = {}

    monkeypatch.setattr(BudgetService, "_count_tokens", staticmethod(lambda text, model: 123))

    def fake_acquire_daily_lock(cursor):
        call_order.append("lock")

    def fake_get_current_total(cursor):
        call_order.append("total")
        return 10_000

    def fake_reserve(cursor, **kwargs):
        call_order.append("reserve")
        captured["kwargs"] = kwargs

    monkeypatch.setattr(
        budget_module.TokenLedgerRepository,
        "acquire_daily_lock",
        staticmethod(fake_acquire_daily_lock),
    )
    monkeypatch.setattr(
        budget_module.TokenLedgerRepository,
        "get_current_total",
        staticmethod(fake_get_current_total),
    )
    monkeypatch.setattr(
        budget_module.TokenLedgerRepository,
        "reserve",
        staticmethod(fake_reserve),
    )

    call_id = uuid4()
    job_id = uuid4()
    reserved_tokens = BudgetService.reserve(
        cursor=object(),
        call_id=call_id,
        job_id=job_id,
        stage="planning",
        provider="openai",
        model="gpt-5.2",
        prompt_text="x + 3 = 7",
    )

    assert call_order == ["lock", "total", "reserve"]
    assert reserved_tokens == 123 + PLANNING_OUTPUT_BUFFER

    kwargs = captured["kwargs"]
    assert kwargs["call_id"] == call_id
    assert kwargs["job_id"] == job_id
    assert kwargs["stage"] == "planning"
    assert kwargs["provider"] == "openai"
    assert kwargs["model"] == "gpt-5.2"
    assert kwargs["reserved_tokens"] == reserved_tokens


def test_reserve_blocks_when_limit_exceeded(
    monkeypatch: pytest.MonkeyPatch,
):
    from app.services import budget_service as budget_module

    called = {"reserve": False}

    monkeypatch.setattr(BudgetService, "_count_tokens", staticmethod(lambda text, model: 5_000))

    monkeypatch.setattr(
        budget_module.TokenLedgerRepository,
        "acquire_daily_lock",
        staticmethod(lambda cursor: None),
    )

    monkeypatch.setattr(
        budget_module.TokenLedgerRepository,
        "get_current_total",
        staticmethod(lambda cursor: DAILY_TOKEN_LIMIT),
    )

    def fake_reserve(cursor, **kwargs):
        called["reserve"] = True

    monkeypatch.setattr(
        budget_module.TokenLedgerRepository,
        "reserve",
        staticmethod(fake_reserve),
    )

    with pytest.raises(QuotaExceededError):
        BudgetService.reserve(
            cursor=object(),
            call_id=uuid4(),
            job_id=uuid4(),
            stage="planning",
            provider="openai",
            model="gpt-5.2",
            prompt_text="example prompt",
        )

    assert called["reserve"] is False
