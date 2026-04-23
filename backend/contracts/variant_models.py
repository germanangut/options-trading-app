from __future__ import annotations

from dataclasses import dataclass, field

from backend.contracts.payoff_models import PayoffAnalysis


SUPPORTED_VARIANT_STRATEGIES: tuple[str, ...] = (
    "bull_put_spread",
    "bear_call_spread",
)

VARIANT_TYPES: tuple[str, ...] = (
    "baseline",
    "conservative",
    "max_credit",
)

VARIANT_LABELS: dict[str, str] = {
    "baseline": "Current scanned setup",
    "conservative": "Lower credit, more room for the trade to work",
    "max_credit": "Higher premium, tighter room for error",
}


@dataclass(frozen=True)
class StrategyVariant:
    """A single analytical variant of a spread trade.

    All credit values are either real (from the baseline trade) or
    explicitly estimated (is_credit_estimated=True). Never fabricated.
    """

    variant_type: str
    strategy_key: str
    reference_trade_id: str | None
    short_strike: float
    long_strike: float
    expiration_date: str | None
    net_credit: float
    spread_width: float
    max_profit: float
    max_loss: float
    breakeven: float
    label: str
    rationale: str
    is_credit_estimated: bool
    payoff: PayoffAnalysis | None = None


@dataclass(frozen=True)
class VariantSet:
    """The full set of analytical variants for a selected trade."""

    scan_id: str
    trade_id: str
    strategy_key: str
    underlying_price_reference: float
    ticker: str | None
    variants: tuple[StrategyVariant, ...] = field(default_factory=tuple)
