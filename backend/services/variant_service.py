"""Variant generation service for PU-15B.2.

Generates conservative and max-credit analytical variants for a selected
baseline spread trade (bull_put_spread, bear_call_spread).

Design rules:
- Variants are analytical only — not execution-ready.
- Strikes are derived from the baseline trade; never invented.
- Credits are estimated using a documented moneyness-scaling formula.
  is_credit_estimated=True on all variants where real chain data is absent.
- If a valid variant cannot be constructed, it is omitted rather than guessed.
- Delta-neutral is NOT part of this phase (PU-15B.2).
"""

from __future__ import annotations

from typing import Any

from backend.contracts.payoff_models import PayoffInput
from backend.contracts.variant_models import (
    SUPPORTED_VARIANT_STRATEGIES,
    VARIANT_LABELS,
    StrategyVariant,
    VariantSet,
)
from backend.services.payoff_engine import calculate_payoff


# ---------------------------------------------------------------------------
# Credit estimation helpers
# ---------------------------------------------------------------------------

_MIN_CREDIT = 0.01
_MIN_OTM_BUFFER = 0.01


def _normalize_strategy_key(value: str) -> str:
    normalized = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    alias_map = {
        "bull_put_spread": "bull_put_spread",
        "bull_put": "bull_put_spread",
        "bear_call_spread": "bear_call_spread",
        "bear_call": "bear_call_spread",
    }
    return alias_map.get(normalized, normalized)


def _estimate_shifted_credit(
    baseline_credit: float,
    baseline_otm_buffer: float,
    shift: float,
    *,
    direction: int,  # +1 = more OTM (conservative), -1 = more ATM (max_credit)
    spread_width: float,
) -> float | None:
    """Estimate credit after shifting both legs by `shift` in `direction`.

    Uses a moneyness-ratio approximation:
        new_credit ≈ baseline_credit * (baseline_otm_buffer / new_otm_buffer)

    Returns None when the estimate would be invalid (e.g., division by zero,
    negative credit, or credit >= spread_width).
    """
    new_otm_buffer = baseline_otm_buffer + direction * shift

    if new_otm_buffer < _MIN_OTM_BUFFER:
        return None

    ratio = baseline_otm_buffer / new_otm_buffer
    estimated = round(baseline_credit * ratio, 3)

    if estimated < _MIN_CREDIT:
        return None

    # Credit must be strictly less than spread width (positive max loss required).
    if estimated >= spread_width:
        estimated = round(spread_width * 0.90, 3)
        if estimated < _MIN_CREDIT:
            return None

    return estimated


def _breakeven_for(strategy_key: str, short_strike: float, net_credit: float) -> float:
    if strategy_key == "bull_put_spread":
        return round(short_strike - net_credit, 4)
    return round(short_strike + net_credit, 4)


# ---------------------------------------------------------------------------
# Per-strategy variant construction
# ---------------------------------------------------------------------------

def _build_payoff(
    strategy_key: str,
    ticker: str | None,
    underlying_price: float,
    short_strike: float,
    long_strike: float,
    net_credit: float,
) -> Any:
    """Run the payoff engine on a variant's strikes/credit."""
    try:
        payoff_input = PayoffInput(
            strategy_key=strategy_key,
            ticker=ticker,
            underlying_price_reference=underlying_price,
            short_strike=short_strike,
            long_strike=long_strike,
            net_credit=net_credit,
        )
        return calculate_payoff(payoff_input)
    except (ValueError, TypeError):
        return None


def _make_variant(
    *,
    variant_type: str,
    strategy_key: str,
    reference_trade_id: str | None,
    ticker: str | None,
    underlying_price: float,
    short_strike: float,
    long_strike: float,
    expiration_date: str | None,
    net_credit: float,
    is_credit_estimated: bool,
    rationale: str,
) -> StrategyVariant | None:
    """Build a StrategyVariant, running the payoff engine; returns None on failure."""
    spread_width = round(abs(short_strike - long_strike), 4)
    if spread_width <= 0:
        return None
    if net_credit < _MIN_CREDIT or net_credit >= spread_width:
        return None

    max_profit = round(net_credit * 100, 2)
    max_loss = round((spread_width - net_credit) * 100, 2)
    breakeven = _breakeven_for(strategy_key, short_strike, net_credit)

    payoff = _build_payoff(
        strategy_key,
        ticker,
        underlying_price,
        short_strike,
        long_strike,
        net_credit,
    )

    return StrategyVariant(
        variant_type=variant_type,
        strategy_key=strategy_key,
        reference_trade_id=reference_trade_id,
        short_strike=short_strike,
        long_strike=long_strike,
        expiration_date=expiration_date,
        net_credit=net_credit,
        spread_width=spread_width,
        max_profit=max_profit,
        max_loss=max_loss,
        breakeven=breakeven,
        label=VARIANT_LABELS[variant_type],
        rationale=rationale,
        is_credit_estimated=is_credit_estimated,
        payoff=payoff,
    )


def _determine_shift(spread_width: float, underlying_price: float) -> float:
    """Derive a sensible one-increment strike shift from the spread geometry."""
    half_width = spread_width / 2.0
    # Round to nearest common strike ladder: 0.5, 1, 2.5, 5
    for rung in (0.5, 1.0, 2.5, 5.0):
        if half_width >= rung:
            return rung
    return max(0.5, round(half_width, 1))


# ---------------------------------------------------------------------------
# Bull Put Spread variants
# ---------------------------------------------------------------------------

def _bull_put_variants(
    trade: dict[str, Any],
    *,
    trade_id: str | None,
) -> list[StrategyVariant]:
    """Generate conservative and max-credit variants for a bull put spread."""
    strategy_key = "bull_put_spread"
    ticker = trade.get("ticker")
    underlying = float(trade.get("underlying_price", 0))
    short_strike = float(trade.get("short_strike", 0))
    long_strike = float(trade.get("long_strike", 0))
    net_credit = float(trade.get("net_credit", 0))
    spread_width = abs(short_strike - long_strike)
    expiration_date = trade.get("expiration_date")

    # For bull put spread: short_strike > long_strike (short put is higher)
    # OTM buffer = how far the short put is from current underlying price
    otm_buffer = underlying - short_strike  # positive when underlying > short_strike (OTM)

    if underlying <= 0 or short_strike <= 0 or long_strike <= 0 or net_credit < _MIN_CREDIT:
        return []

    shift = _determine_shift(spread_width, underlying)
    variants: list[StrategyVariant] = []

    # Conservative: shift both strikes DOWN (further OTM for a put spread = lower strikes)
    # More room before the underlying hits the short strike.
    cons_short = round(short_strike - shift, 2)
    cons_long = round(long_strike - shift, 2)
    if cons_long > 0:
        cons_credit = _estimate_shifted_credit(
            net_credit,
            max(otm_buffer, _MIN_OTM_BUFFER),
            shift,
            direction=+1,  # OTM buffer increases → less credit
            spread_width=spread_width,
        )
        if cons_credit is not None:
            v = _make_variant(
                variant_type="conservative",
                strategy_key=strategy_key,
                reference_trade_id=trade_id,
                ticker=ticker,
                underlying_price=underlying,
                short_strike=cons_short,
                long_strike=cons_long,
                expiration_date=expiration_date,
                net_credit=cons_credit,
                is_credit_estimated=True,
                rationale=(
                    f"Short strike shifted down from {short_strike:.2f} to {cons_short:.2f} "
                    f"({shift:.2f} points further OTM). "
                    f"Estimated credit: {cons_credit:.2f} (lower). "
                    "More cushion before the trade goes in-the-money."
                ),
            )
            if v:
                variants.append(v)

    # Max Credit: shift both strikes UP (closer to ATM = higher short strike = more premium)
    mc_short = round(short_strike + shift, 2)
    mc_long = round(long_strike + shift, 2)
    # Max credit variant is only valid when the new short strike is still OTM
    if mc_short < underlying:
        mc_credit = _estimate_shifted_credit(
            net_credit,
            max(otm_buffer, _MIN_OTM_BUFFER),
            shift,
            direction=-1,  # OTM buffer decreases → more credit
            spread_width=spread_width,
        )
        if mc_credit is not None:
            v = _make_variant(
                variant_type="max_credit",
                strategy_key=strategy_key,
                reference_trade_id=trade_id,
                ticker=ticker,
                underlying_price=underlying,
                short_strike=mc_short,
                long_strike=mc_long,
                expiration_date=expiration_date,
                net_credit=mc_credit,
                is_credit_estimated=True,
                rationale=(
                    f"Short strike shifted up from {short_strike:.2f} to {mc_short:.2f} "
                    f"({shift:.2f} points closer to spot). "
                    f"Estimated credit: {mc_credit:.2f} (higher). "
                    "Captures more premium but leaves less room if the underlying declines."
                ),
            )
            if v:
                variants.append(v)

    return variants


# ---------------------------------------------------------------------------
# Bear Call Spread variants
# ---------------------------------------------------------------------------

def _bear_call_variants(
    trade: dict[str, Any],
    *,
    trade_id: str | None,
) -> list[StrategyVariant]:
    """Generate conservative and max-credit variants for a bear call spread."""
    strategy_key = "bear_call_spread"
    ticker = trade.get("ticker")
    underlying = float(trade.get("underlying_price", 0))
    short_strike = float(trade.get("short_strike", 0))
    long_strike = float(trade.get("long_strike", 0))
    net_credit = float(trade.get("net_credit", 0))
    spread_width = abs(long_strike - short_strike)
    expiration_date = trade.get("expiration_date")

    # For bear call spread: short_strike < long_strike (short call is lower)
    # OTM buffer = how far the short call is above the underlying price
    otm_buffer = short_strike - underlying  # positive when short_strike > underlying (OTM)

    if underlying <= 0 or short_strike <= 0 or long_strike <= 0 or net_credit < _MIN_CREDIT:
        return []

    shift = _determine_shift(spread_width, underlying)
    variants: list[StrategyVariant] = []

    # Conservative: shift both strikes UP (further OTM for a call spread = higher strikes)
    cons_short = round(short_strike + shift, 2)
    cons_long = round(long_strike + shift, 2)
    cons_credit = _estimate_shifted_credit(
        net_credit,
        max(otm_buffer, _MIN_OTM_BUFFER),
        shift,
        direction=+1,
        spread_width=spread_width,
    )
    if cons_credit is not None:
        v = _make_variant(
            variant_type="conservative",
            strategy_key=strategy_key,
            reference_trade_id=trade_id,
            ticker=ticker,
            underlying_price=underlying,
            short_strike=cons_short,
            long_strike=cons_long,
            expiration_date=expiration_date,
            net_credit=cons_credit,
            is_credit_estimated=True,
            rationale=(
                f"Short strike shifted up from {short_strike:.2f} to {cons_short:.2f} "
                f"({shift:.2f} points further OTM). "
                f"Estimated credit: {cons_credit:.2f} (lower). "
                "More cushion before the underlying reaches the short call."
            ),
        )
        if v:
            variants.append(v)

    # Max Credit: shift both strikes DOWN (closer to ATM = lower short strike = more premium)
    mc_short = round(short_strike - shift, 2)
    mc_long = round(long_strike - shift, 2)
    # Max credit variant is only valid when the new short strike is still OTM
    if mc_short > underlying and mc_long > 0:
        mc_credit = _estimate_shifted_credit(
            net_credit,
            max(otm_buffer, _MIN_OTM_BUFFER),
            shift,
            direction=-1,
            spread_width=spread_width,
        )
        if mc_credit is not None:
            v = _make_variant(
                variant_type="max_credit",
                strategy_key=strategy_key,
                reference_trade_id=trade_id,
                ticker=ticker,
                underlying_price=underlying,
                short_strike=mc_short,
                long_strike=mc_long,
                expiration_date=expiration_date,
                net_credit=mc_credit,
                is_credit_estimated=True,
                rationale=(
                    f"Short strike shifted down from {short_strike:.2f} to {mc_short:.2f} "
                    f"({shift:.2f} points closer to spot). "
                    f"Estimated credit: {mc_credit:.2f} (higher). "
                    "Captures more premium but leaves less room if the underlying rallies."
                ),
            )
            if v:
                variants.append(v)

    return variants


# ---------------------------------------------------------------------------
# Baseline variant builder
# ---------------------------------------------------------------------------

def _build_baseline_variant(
    trade: dict[str, Any],
    *,
    trade_id: str | None,
    strategy_key: str,
) -> StrategyVariant | None:
    """Wrap the scanned trade as the baseline variant."""
    ticker = trade.get("ticker")
    underlying = float(trade.get("underlying_price", 0))
    short_strike = float(trade.get("short_strike", 0))
    long_strike = float(trade.get("long_strike", 0))
    net_credit = float(trade.get("net_credit", 0))
    expiration_date = trade.get("expiration_date")

    return _make_variant(
        variant_type="baseline",
        strategy_key=strategy_key,
        reference_trade_id=trade_id,
        ticker=ticker,
        underlying_price=underlying,
        short_strike=short_strike,
        long_strike=long_strike,
        expiration_date=expiration_date,
        net_credit=net_credit,
        is_credit_estimated=False,
        rationale="The original scanned candidate as selected by the engine.",
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_variants(
    trade: dict[str, Any],
    *,
    scan_id: str,
    trade_id: str | None = None,
) -> VariantSet:
    """Generate a VariantSet for the given scanned trade dict.

    Supported strategies: bull_put_spread, bear_call_spread.
    Unsupported strategies return a VariantSet with only the baseline.
    Invalid or incomplete trades return an empty VariantSet.
    """
    raw_strategy = str(trade.get("strategy_type") or trade.get("strategy_key") or "")
    strategy_key = _normalize_strategy_key(raw_strategy)

    ticker = trade.get("ticker")
    underlying_raw = trade.get("underlying_price")
    try:
        underlying = float(underlying_raw) if underlying_raw is not None else 0.0
    except (TypeError, ValueError):
        underlying = 0.0

    variants: list[StrategyVariant] = []

    baseline = _build_baseline_variant(trade, trade_id=trade_id, strategy_key=strategy_key)
    if baseline is not None:
        variants.append(baseline)

    if strategy_key in SUPPORTED_VARIANT_STRATEGIES:
        if strategy_key == "bull_put_spread":
            variants.extend(_bull_put_variants(trade, trade_id=trade_id))
        elif strategy_key == "bear_call_spread":
            variants.extend(_bear_call_variants(trade, trade_id=trade_id))

    return VariantSet(
        scan_id=scan_id,
        trade_id=trade_id or "",
        strategy_key=strategy_key,
        underlying_price_reference=underlying,
        ticker=ticker,
        variants=tuple(variants),
    )
