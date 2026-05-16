from datetime import timezone, datetime

from fastapi import APIRouter, Depends, Request

from app.configs.llm_settings import OPENROUTER_DAILY_CALL_LIMIT
from app.configs.limiter_config import LimitConfig
from app.dependencies.db import get_cursor
from app.dependencies.limiter import limiter
from app.repositories.token_repository import TokenLedgerRepository
from app.schemas.token_usage import TokenUsageResponse

router = APIRouter(prefix="/usage", tags=["Usage"])


@router.get("")
@limiter.limit(LimitConfig.LIGHT)
def get_usage(request: Request, cursor=Depends(get_cursor)) -> TokenUsageResponse:
    today = datetime.now(timezone.utc).date()
    summary = TokenLedgerRepository.get_daily_summary(cursor, today)

    return TokenUsageResponse(
        day=today,
        openrouter_calls=summary.openrouter_calls,
        openrouter_call_limit=OPENROUTER_DAILY_CALL_LIMIT,
        openrouter_calls_remaining=max(0, OPENROUTER_DAILY_CALL_LIMIT - summary.openrouter_calls),
        token_totals=summary.token_totals,
        breakdown=summary.breakdown,
    )
