from datetime import date
from pydantic import BaseModel


class BreakdownEntry(BaseModel):
    provider: str
    model: str
    stage: str
    consumed: int
    reserved: int


class DailySummary(BaseModel):
    daily_limit: int
    consumed: int
    reserved: int
    remaining: int
    remaining_pct: float
    soft_threshold_exceeded: bool
    breakdown: list[BreakdownEntry]


class TokenUsageResponse(BaseModel):
    day: date
    daily_limit: int
    soft_threshold: int
    consumed: int
    reserved: int
    remaining: int
    soft_threshold_exceeded: bool
    breakdown: list[BreakdownEntry]
