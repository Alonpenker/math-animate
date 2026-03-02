from datetime import date
from uuid import UUID

import tiktoken

from app.configs.llm_settings import (
    DAILY_TOKEN_LIMIT,
    PLANNING_OUTPUT_BUFFER,
    CODEGEN_OUTPUT_BUFFER,
)
from app.exceptions.quota_exceeded_error import QuotaExceededError
from app.repositories.token_repository import TokenLedgerRepository


class BudgetService:

    @staticmethod
    def _count_tokens(text: str, model_name: str) -> int:
        try:
            encoding = tiktoken.encoding_for_model(model_name)
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))

    @staticmethod
    def reserve(
        cursor,
        call_id: UUID,
        job_id: UUID,
        stage: str,
        provider: str,
        model: str,
        prompt_text: str,
    ) -> int:
        input_tokens = BudgetService._count_tokens(prompt_text, model)

        if stage == "planning":
            output_buffer = PLANNING_OUTPUT_BUFFER
        else:
            output_buffer = CODEGEN_OUTPUT_BUFFER

        reserved_tokens = input_tokens + output_buffer

        TokenLedgerRepository.acquire_daily_lock(cursor)

        current_total = TokenLedgerRepository.get_current_total(cursor)

        if current_total + reserved_tokens > DAILY_TOKEN_LIMIT:
            raise QuotaExceededError(
                limit=DAILY_TOKEN_LIMIT,
                consumed=current_total,
                reserved=0,
                requested=reserved_tokens,
            )

        TokenLedgerRepository.reserve(
            cursor,
            call_id=call_id,
            day=date.today(),
            job_id=job_id,
            stage=stage,
            provider=provider,
            model=model,
            reserved_tokens=reserved_tokens,
        )

        return reserved_tokens

    @staticmethod
    def reconcile(cursor, call_id: UUID, consumed_tokens: int) -> None:
        TokenLedgerRepository.reconcile(cursor, call_id, consumed_tokens)

    @staticmethod
    def release_on_error(cursor, call_id: UUID, reserved_tokens: int) -> None:
        TokenLedgerRepository.reconcile(cursor, call_id, reserved_tokens)
