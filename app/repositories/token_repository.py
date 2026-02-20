from datetime import date, datetime
from typing import List
from uuid import UUID

from app.configs.llm_settings import DAILY_TOKEN_LIMIT, SOFT_THRESHOLD_RATIO
from app.repositories.repository import Repository
from app.schemas.token_ledger import TokenLedgerSchema
from app.schemas.token_usage import BreakdownEntry, DailySummary


class TokenLedgerRepository(Repository):

    TABLE_NAME = "token_ledger"
    SCHEMA = TokenLedgerSchema
    PRIMARY_KEY = "call_id"

    @classmethod
    def _create_index(cls):
        return (
            f"CREATE INDEX IF NOT EXISTS idx_{cls.TABLE_NAME}_{cls.SCHEMA.DAY.name} "
            f"ON {cls.TABLE_NAME} ({cls.SCHEMA.DAY.name})"
        )

    @classmethod
    def reserve(
        cls,
        cursor,
        call_id: UUID,
        day: date,
        job_id: UUID,
        stage: str,
        provider: str,
        model: str,
        reserved_tokens: int,
    ) -> None:
        cursor.execute(
            cls.insert(),
            (str(call_id), day, str(job_id), stage, provider, model,
             reserved_tokens, 0, "ACTIVE"),
        )

    @classmethod
    def reconcile(cls, cursor, call_id: UUID, consumed_tokens: int) -> None:
        cursor.execute(
            f"UPDATE {cls.TABLE_NAME} "
            f"SET {cls.SCHEMA.CONSUMED_TOKENS.name} = %s, "
            f"{cls.SCHEMA.RESERVED_TOKENS.name} = 0, "
            f"{cls.SCHEMA.STATE.name} = 'RELEASED', "
            f"{cls.SCHEMA.UPDATED_AT.name} = NOW() "
            f"WHERE {cls.SCHEMA.CALL_ID.name} = %s",
            (consumed_tokens, str(call_id)),
        )

    @classmethod
    def get_daily_summary(cls, cursor, day: date) -> DailySummary:
        cursor.execute(
            f"SELECT "
            f"{cls.SCHEMA.PROVIDER.name}, {cls.SCHEMA.MODEL.name}, {cls.SCHEMA.STAGE.name}, "
            f"COALESCE(SUM(CASE WHEN {cls.SCHEMA.STATE.name} = 'RELEASED' "
            f"THEN {cls.SCHEMA.CONSUMED_TOKENS.name} ELSE 0 END), 0) AS consumed, "
            f"COALESCE(SUM(CASE WHEN {cls.SCHEMA.STATE.name} = 'ACTIVE' "
            f"THEN {cls.SCHEMA.RESERVED_TOKENS.name} ELSE 0 END), 0) AS reserved "
            f"FROM {cls.TABLE_NAME} "
            f"WHERE {cls.SCHEMA.DAY.name} = %s "
            f"GROUP BY {cls.SCHEMA.PROVIDER.name}, {cls.SCHEMA.MODEL.name}, {cls.SCHEMA.STAGE.name}",
            (day,),
        )
        rows = cursor.fetchall()

        breakdown: List[BreakdownEntry] = []
        total_consumed = 0
        total_reserved = 0

        for row in rows:
            consumed = row[cls.SCHEMA.CONSUMED_TOKENS.name]
            reserved = row[cls.SCHEMA.RESERVED_TOKENS.name]
            breakdown.append(
                BreakdownEntry(
                    provider=row[cls.SCHEMA.PROVIDER.name],
                    model=row[cls.SCHEMA.MODEL.name],
                    stage=row[cls.SCHEMA.STAGE.name],
                    consumed=consumed,
                    reserved=reserved,
                )
            )
            total_consumed += consumed
            total_reserved += reserved

        used = total_consumed + total_reserved
        remaining = max(0, DAILY_TOKEN_LIMIT - used)
        remaining_pct = round((remaining / DAILY_TOKEN_LIMIT) * 100, 2) if DAILY_TOKEN_LIMIT > 0 else 0.0
        soft_threshold = int(DAILY_TOKEN_LIMIT * SOFT_THRESHOLD_RATIO)

        return DailySummary(
            daily_limit=DAILY_TOKEN_LIMIT,
            consumed=total_consumed,
            reserved=total_reserved,
            remaining=remaining,
            remaining_pct=remaining_pct,
            soft_threshold_exceeded=used >= soft_threshold,
            breakdown=breakdown,
        )

    @classmethod
    def get_current_total(cls, cursor) -> int:
        """Sum of consumed + reserved tokens for today (RELEASED + ACTIVE rows)."""
        cursor.execute(
            f"SELECT "
            f"COALESCE(SUM({cls.SCHEMA.CONSUMED_TOKENS.name}), 0) "
            f"+ COALESCE(SUM({cls.SCHEMA.RESERVED_TOKENS.name}), 0) "
            f"FROM {cls.TABLE_NAME} "
            f"WHERE {cls.SCHEMA.DAY.name} = current_date "
            f"AND {cls.SCHEMA.STATE.name} IN ('RELEASED', 'ACTIVE')",
        )
        row = cursor.fetchone()
        return list(row.values())[0] if row else 0

    @classmethod
    def acquire_daily_lock(cls, cursor) -> None:
        """Acquire a per-day PostgreSQL advisory lock inside the current transaction."""
        cursor.execute(
            "SELECT pg_advisory_xact_lock(extract(epoch from current_date)::bigint)"
        )

    @classmethod
    def expire_stale(cls, cursor, before_timestamp: datetime) -> None:
        cursor.execute(
            f"UPDATE {cls.TABLE_NAME} "
            f"SET {cls.SCHEMA.STATE.name} = 'EXPIRED', "
            f"{cls.SCHEMA.UPDATED_AT.name} = NOW() "
            f"WHERE {cls.SCHEMA.STATE.name} = 'ACTIVE' "
            f"AND {cls.SCHEMA.CREATED_AT.name} < %s",
            (before_timestamp,),
        )
