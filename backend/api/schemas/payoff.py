from __future__ import annotations

from pydantic import BaseModel, Field


class PayoffPointResponse(BaseModel):
    underlying_price: float
    expiration_payoff: float


class PayoffAnalysisResponse(BaseModel):
    strategy_key: str
    ticker: str | None = None
    quantity: int
    underlying_price_reference: float
    short_strike: float
    long_strike: float
    net_credit: float
    spread_width: float
    max_profit: float
    max_loss: float
    breakeven_low: float | None = None
    breakeven_high: float | None = None
    profit_zone: str
    loss_zone: str
    expiration_summary: str
    price_grid: list[float] = Field(default_factory=list)
    payoff_points: list[PayoffPointResponse] = Field(default_factory=list)


class PayoffEnvelopeResponse(BaseModel):
    source_type: str
    source_id: str
    payoff: PayoffAnalysisResponse
