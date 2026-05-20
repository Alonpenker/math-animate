from datetime import date
from typing import Any, List
from uuid import UUID

from app.configs.llm_settings import LLM_PROVIDER, OPENROUTER_DAILY_CALL_LIMIT
from app.repositories.repository import Repository
from app.schemas.token_ledger import TokenLedgerSchema, State
from app.schemas.token_usage import BreakdownEntry, DailySummary, TokenTotals


class TokenLedgerRepository(Repository):

    TABLE_NAME = "token_ledger"
    SCHEMA = TokenLedgerSchema
    PRIMARY_KEY = TokenLedgerSchema.CALL_ID.name
    INDEX_FIELDS = (TokenLedgerSchema.DAY.name,)
    
    CALLS_COLUMN = "calls"

    @classmethod
    def count_openrouter_calls(cls, cursor, day: date) -> int:
        cursor.execute(
            f"SELECT COUNT(*) AS {cls.CALLS_COLUMN} "
            f"FROM {cls.TABLE_NAME} "
            f"WHERE {cls.SCHEMA.DAY.name} = %s "
            f"AND {cls.SCHEMA.PROVIDER.name} = %s",
            (day, LLM_PROVIDER.OPENROUTER.value),
        )
        row = cursor.fetchone()
        return int(row[cls.CALLS_COLUMN]) if row else 0

    @classmethod
    def claim_openrouter_call(
        cls,
        cursor,
        *,
        call_id: UUID,
        day: date,
        job_id: UUID,
        stage: str,
        call_type: str,
        model: str,
    ) -> None:
        cursor.execute(
            cls.insert(),
            (
                str(call_id),
                day,
                str(job_id),
                stage,
                LLM_PROVIDER.OPENROUTER.value,
                model,
                call_type,
                0,
                0,
                0,
                0,
                State.ACTIVE,
            ),
        )

    @classmethod
    def record_openrouter_usage(
        cls,
        cursor,
        *,
        call_id: UUID,
        usage: Any,
    ) -> None:
        cursor.execute(
            f"UPDATE {cls.TABLE_NAME} "
            f"SET {cls.SCHEMA.INPUT_TOKENS.name} = %s, "
            f"{cls.SCHEMA.OUTPUT_TOKENS.name} = %s, "
            f"{cls.SCHEMA.REASONING_TOKENS.name} = %s, "
            f"{cls.SCHEMA.TOTAL_TOKENS.name} = %s, "
            f"{cls.SCHEMA.STATE.name} = '{State.RELEASED}', "
            f"{cls.SCHEMA.UPDATED_AT.name} = NOW() "
            f"WHERE {cls.SCHEMA.CALL_ID.name} = %s",
            (
                usage.input_tokens,
                usage.output_tokens,
                usage.reasoning_tokens,
                usage.total_tokens,
                str(call_id),
            ),
        )

    @classmethod
    def get_daily_summary(cls, cursor, day: date) -> DailySummary:
        cursor.execute(
            f"SELECT "
            f"{cls.SCHEMA.PROVIDER.name}, {cls.SCHEMA.MODEL.name}, {cls.SCHEMA.STAGE.name}, "
            f"{cls.SCHEMA.CALL_TYPE.name}, "
            f"COUNT(*) AS {cls.CALLS_COLUMN}, "
            f"COALESCE(SUM({cls.SCHEMA.INPUT_TOKENS.name}), 0) AS {cls.SCHEMA.INPUT_TOKENS.name}, "
            f"COALESCE(SUM({cls.SCHEMA.OUTPUT_TOKENS.name}), 0) AS {cls.SCHEMA.OUTPUT_TOKENS.name}, "
            f"COALESCE(SUM({cls.SCHEMA.REASONING_TOKENS.name}), 0) AS {cls.SCHEMA.REASONING_TOKENS.name}, "
            f"COALESCE(SUM({cls.SCHEMA.TOTAL_TOKENS.name}), 0) AS {cls.SCHEMA.TOTAL_TOKENS.name} "
            f"FROM {cls.TABLE_NAME} "
            f"WHERE {cls.SCHEMA.DAY.name} = %s "
            f"AND {cls.SCHEMA.PROVIDER.name} = %s "
            f"GROUP BY {cls.SCHEMA.PROVIDER.name}, {cls.SCHEMA.MODEL.name}, "
            f"{cls.SCHEMA.STAGE.name}, {cls.SCHEMA.CALL_TYPE.name} "
            f"ORDER BY {cls.SCHEMA.PROVIDER.name}, {cls.SCHEMA.MODEL.name}, "
            f"{cls.SCHEMA.STAGE.name}, {cls.SCHEMA.CALL_TYPE.name}",
            (day, LLM_PROVIDER.OPENROUTER.value),
        )
        rows = cursor.fetchall()

        breakdown: List[BreakdownEntry] = []
        calls = 0
        input_tokens = 0
        output_tokens = 0
        reasoning_tokens = 0
        total_tokens = 0

        for row in rows:
            row_calls = int(row[cls.CALLS_COLUMN])
            row_input = int(row[cls.SCHEMA.INPUT_TOKENS.name])
            row_output = int(row[cls.SCHEMA.OUTPUT_TOKENS.name])
            row_reasoning = int(row[cls.SCHEMA.REASONING_TOKENS.name])
            row_total = int(row[cls.SCHEMA.TOTAL_TOKENS.name])
            breakdown.append(
                BreakdownEntry(
                    provider=row[cls.SCHEMA.PROVIDER.name],
                    model=row[cls.SCHEMA.MODEL.name],
                    stage=row[cls.SCHEMA.STAGE.name],
                    call_type=row[cls.SCHEMA.CALL_TYPE.name],
                    calls=row_calls,
                    input_tokens=row_input,
                    output_tokens=row_output,
                    reasoning_tokens=row_reasoning,
                    total_tokens=row_total,
                )
            )
            calls += row_calls
            input_tokens += row_input
            output_tokens += row_output
            reasoning_tokens += row_reasoning
            total_tokens += row_total

        return DailySummary(
            openrouter_calls=calls,
            openrouter_call_limit=OPENROUTER_DAILY_CALL_LIMIT,
            openrouter_calls_remaining=max(0, OPENROUTER_DAILY_CALL_LIMIT - calls),
            token_totals=TokenTotals(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                reasoning_tokens=reasoning_tokens,
                total_tokens=total_tokens,
            ),
            breakdown=breakdown,
        )

    @classmethod
    def get_current_total(cls, cursor) -> int:
        """Sum of total tokens used today (both RELEASED and ACTIVE rows)."""
        cursor.execute(
            f"SELECT "
            f"COALESCE(SUM({cls.SCHEMA.TOTAL_TOKENS.name}), 0) "
            f"FROM {cls.TABLE_NAME} "
            f"WHERE {cls.SCHEMA.DAY.name} = current_date "
            f"AND {cls.SCHEMA.STATE.name} IN ('{State.RELEASED}', '{State.ACTIVE}')",
        )
        row = cursor.fetchone()
        return list(row.values())[0] if row else 0

    @classmethod
    def acquire_daily_lock(cls, cursor) -> None:
        """Acquire a per-day PostgreSQL advisory lock inside the current transaction."""
        cursor.execute(
            "SELECT pg_advisory_xact_lock(extract(epoch from current_date)::bigint)"
        )

