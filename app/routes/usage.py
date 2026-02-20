from datetime import timezone, datetime

from fastapi import APIRouter, Depends

from app.configs.llm_settings import DAILY_TOKEN_LIMIT, SOFT_THRESHOLD_RATIO
from app.dependencies.db import get_cursor
from app.repositories.token_repository import TokenLedgerRepository
from app.schemas.token_usage import TokenUsageResponse

router = APIRouter(prefix="/usage", tags=["usage"])


@router.get("")
def get_usage(cursor=Depends(get_cursor)) -> TokenUsageResponse:
    today = datetime.now(timezone.utc).date()
    summary = TokenLedgerRepository.get_daily_summary(cursor, today)

    return TokenUsageResponse(
        day=today,
        daily_limit=summary.daily_limit,
        soft_threshold=int(DAILY_TOKEN_LIMIT * SOFT_THRESHOLD_RATIO),
        consumed=summary.consumed,
        reserved=summary.reserved,
        remaining=summary.remaining,
        soft_threshold_exceeded=summary.soft_threshold_exceeded,
        breakdown=summary.breakdown,
    )
