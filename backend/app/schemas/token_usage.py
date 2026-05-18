from datetime import date
from pydantic import BaseModel


class BreakdownEntry(BaseModel):
    provider: str
    model: str
    stage: str
    call_type: str
    calls: int
    input_tokens: int
    output_tokens: int
    reasoning_tokens: int
    total_tokens: int


class TokenTotals(BaseModel):
    input_tokens: int
    output_tokens: int
    reasoning_tokens: int
    total_tokens: int


class DailySummary(BaseModel):
    openrouter_calls: int
    openrouter_call_limit: int
    openrouter_calls_remaining: int
    token_totals: TokenTotals
    breakdown: list[BreakdownEntry]


class TokenUsageResponse(BaseModel):
    day: date
    openrouter_calls: int
    openrouter_call_limit: int
    openrouter_calls_remaining: int
    token_totals: TokenTotals
    breakdown: list[BreakdownEntry]
