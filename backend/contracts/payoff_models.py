from __future__ import annotations

from dataclasses import dataclass


SUPPORTED_PAYOFF_STRATEGIES: tuple[str, ...] = (
    "bull_put_spread",
    "bear_call_spread",
)


@dataclass(frozen=True)
class PayoffPoint:
    underlying_price: float
    expiration_payoff: float


@dataclass(frozen=True)
class PayoffAnalysis:
    strategy_key: str
    ticker: str | None
    quantity: int
    underlying_price_reference: float
    short_strike: float
    long_strike: float
    net_credit: float
    spread_width: float
    max_profit: float
    max_loss: float
    breakeven_low: float | None
    breakeven_high: float | None
    profit_zone: str
    loss_zone: str
    expiration_summary: str
    price_grid: list[float]
    payoff_points: list[PayoffPoint]


@dataclass(frozen=True)
class PayoffInput:
    strategy_key: str
    ticker: str | None
    underlying_price_reference: float
    short_strike: float
    long_strike: float
    net_credit: float
    quantity: int = 1
