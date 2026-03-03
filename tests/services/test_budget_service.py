from uuid import uuid4

import pytest

from app.configs.llm_settings import DAILY_TOKEN_LIMIT, PLANNING_OUTPUT_BUFFER, CODEGEN_OUTPUT_BUFFER
from app.exceptions.quota_exceeded_error import QuotaExceededError
from app.services.budget_service import BudgetService


# ─────────────────────────────────────────────────────────────────────────────
# BudgetService.reserve
# ─────────────────────────────────────────────────────────────────────────────

def test_reserve_acquires_lock_checks_total_then_creates_reservation(
    monkeypatch: pytest.MonkeyPatch,
):
    # Given
    from app.services import budget_service as budget_module

    call_order: list[str] = []
    captured: dict = {}

    monkeypatch.setattr(BudgetService, "_count_tokens", staticmethod(lambda text, model: 123))

    monkeypatch.setattr(
        budget_module.TokenLedgerRepository, "acquire_daily_lock",
        staticmethod(lambda cursor: call_order.append("lock")),
    )
    monkeypatch.setattr(
        budget_module.TokenLedgerRepository, "get_current_total",
        staticmethod(lambda cursor: call_order.append("total") or 10_000),
    )
    monkeypatch.setattr(
        budget_module.TokenLedgerRepository, "reserve",
        staticmethod(lambda cursor, **kwargs: (call_order.append("reserve"), captured.update({"kwargs": kwargs}))),
    )

    call_id = uuid4()
    job_id = uuid4()

    # When
    reserved_tokens = BudgetService.reserve(
        cursor=object(),
        call_id=call_id,
        job_id=job_id,
        stage="planning",
        provider="openai",
        model="gpt-5.2",
        prompt_text="x + 3 = 7",
    )

    # Then — operations run in the correct order
    assert call_order == ["lock", "total", "reserve"]

    # Reservation includes input tokens + planning output buffer
    assert reserved_tokens == 123 + PLANNING_OUTPUT_BUFFER

    # All required fields passed to the ledger
    kwargs = captured["kwargs"]
    assert kwargs["call_id"] == call_id
    assert kwargs["job_id"] == job_id
    assert kwargs["stage"] == "planning"
    assert kwargs["provider"] == "openai"
    assert kwargs["model"] == "gpt-5.2"
    assert kwargs["reserved_tokens"] == reserved_tokens


def test_reserve_uses_codegen_output_buffer_for_non_planning_stages(
    monkeypatch: pytest.MonkeyPatch,
):
    # Given
    from app.services import budget_service as budget_module

    captured: dict = {}
    monkeypatch.setattr(BudgetService, "_count_tokens", staticmethod(lambda text, model: 100))
    monkeypatch.setattr(
        budget_module.TokenLedgerRepository, "acquire_daily_lock",
        staticmethod(lambda cursor: None),
    )
    monkeypatch.setattr(
        budget_module.TokenLedgerRepository, "get_current_total",
        staticmethod(lambda cursor: 0),
    )
    monkeypatch.setattr(
        budget_module.TokenLedgerRepository, "reserve",
        staticmethod(lambda cursor, **kwargs: captured.update({"reserved": kwargs["reserved_tokens"]})),
    )

    # When
    reserved = BudgetService.reserve(
        cursor=object(),
        call_id=uuid4(), job_id=uuid4(),
        stage="codegen", provider="openai", model="gpt-5.1-codex",
        prompt_text="some code prompt",
    )

    # Then
    assert reserved == 100 + CODEGEN_OUTPUT_BUFFER
    assert captured["reserved"] == reserved


def test_reserve_raises_quota_exceeded_when_daily_limit_reached(
    monkeypatch: pytest.MonkeyPatch,
):
    # Given
    from app.services import budget_service as budget_module

    reserve_called = {"called": False}

    monkeypatch.setattr(BudgetService, "_count_tokens", staticmethod(lambda text, model: 5_000))
    monkeypatch.setattr(
        budget_module.TokenLedgerRepository, "acquire_daily_lock",
        staticmethod(lambda cursor: None),
    )
    monkeypatch.setattr(
        budget_module.TokenLedgerRepository, "get_current_total",
        staticmethod(lambda cursor: DAILY_TOKEN_LIMIT),  # already at limit
    )
    monkeypatch.setattr(
        budget_module.TokenLedgerRepository, "reserve",
        staticmethod(lambda cursor, **kwargs: reserve_called.update({"called": True})),
    )

    # When / Then
    with pytest.raises(QuotaExceededError):
        BudgetService.reserve(
            cursor=object(),
            call_id=uuid4(), job_id=uuid4(),
            stage="planning", provider="openai", model="gpt-5.2",
            prompt_text="example prompt",
        )

    # Reservation must NOT be created when the limit is exceeded
    assert reserve_called["called"] is False


# ─────────────────────────────────────────────────────────────────────────────
# BudgetService.reconcile
# ─────────────────────────────────────────────────────────────────────────────

def test_reconcile_delegates_to_token_ledger_repository(
    monkeypatch: pytest.MonkeyPatch,
):
    # Given
    from app.services import budget_service as budget_module

    captured: dict = {}
    monkeypatch.setattr(
        budget_module.TokenLedgerRepository, "reconcile",
        staticmethod(lambda cursor, call_id, consumed: captured.update({"call_id": call_id, "consumed": consumed})),
    )
    call_id = uuid4()

    # When
    BudgetService.reconcile(cursor=object(), call_id=call_id, consumed_tokens=350)

    # Then
    assert captured["call_id"] == call_id
    assert captured["consumed"] == 350


# ─────────────────────────────────────────────────────────────────────────────
# BudgetService.release_on_error
# ─────────────────────────────────────────────────────────────────────────────

def test_release_on_error_delegates_to_reconcile_with_reserved_amount(
    monkeypatch: pytest.MonkeyPatch,
):
    # Given
    from app.services import budget_service as budget_module

    captured: dict = {}
    monkeypatch.setattr(
        budget_module.TokenLedgerRepository, "reconcile",
        staticmethod(lambda cursor, call_id, consumed: captured.update({"call_id": call_id, "consumed": consumed})),
    )
    call_id = uuid4()

    # When
    BudgetService.release_on_error(cursor=object(), call_id=call_id, reserved_tokens=1000)

    # Then — release_on_error settles with the reserved amount
    assert captured["call_id"] == call_id
    assert captured["consumed"] == 1000
