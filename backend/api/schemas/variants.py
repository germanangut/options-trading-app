from __future__ import annotations

from pydantic import BaseModel, Field

from backend.api.schemas.payoff import PayoffAnalysisResponse


class VariantComparisonResponse(BaseModel):
    is_baseline: bool
    delta_net_credit: float
    delta_max_profit: float
    delta_max_loss: float
    delta_breakeven: float
    delta_spread_width: float
    risk_reward_ratio: float | None = None
    delta_risk_reward_ratio: float | None = None
    summary: str
    safety_tradeoff: str


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
    comparison: VariantComparisonResponse | None = None
    payoff: PayoffAnalysisResponse | None = None


class VariantSetResponse(BaseModel):
    scan_id: str
    trade_id: str
    strategy_key: str
    underlying_price_reference: float
    ticker: str | None = None
    variants: list[StrategyVariantResponse] = Field(default_factory=list)
