from __future__ import annotations

from pydantic import BaseModel, Field

from backend.api.schemas.payoff import PayoffAnalysisResponse


class StrategyVariantResponse(BaseModel):
    variant_type: str
    strategy_key: str
    reference_trade_id: str | None = None
    short_strike: float
    long_strike: float
    expiration_date: str | None = None
    net_credit: float
    spread_width: float
    max_profit: float
    max_loss: float
    breakeven: float
    label: str
    rationale: str
    is_credit_estimated: bool
    payoff: PayoffAnalysisResponse | None = None


class VariantSetResponse(BaseModel):
    scan_id: str
    trade_id: str
    strategy_key: str
    underlying_price_reference: float
    ticker: str | None = None
    variants: list[StrategyVariantResponse] = Field(default_factory=list)
