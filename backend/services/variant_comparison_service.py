from __future__ import annotations

from typing import Any


def _safe_ratio(numerator: float, denominator: float) -> float | None:
    if denominator <= 0:
        return None
    return round(numerator / denominator, 4)


def _to_currency_delta(value: float) -> float:
    return round(value, 2)


def _room_to_work_summary(*, strategy_key: str, baseline_short: float, current_short: float) -> str:
    if current_short == baseline_short:
        return "No structural change from baseline."

    if strategy_key == "bull_put_spread":
        if current_short < baseline_short:
            return "Further out-of-the-money short strike, lower credit, more room to work."
        return "Closer short strike, richer premium, tighter room for error."

    if strategy_key == "bear_call_spread":
        if current_short > baseline_short:
            return "Further out-of-the-money short strike, lower credit, more room to work."
        return "Closer short strike, richer premium, tighter room for error."

    return "Variant changes trade-offs versus baseline."


def build_variant_comparisons(variants: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Attach deterministic comparison deltas to each variant relative to baseline."""
    baseline = next((variant for variant in variants if variant.get("variant_type") == "baseline"), None)
    if baseline is None:
        for variant in variants:
            variant["comparison"] = None
        return variants

    baseline_credit = float(baseline.get("net_credit", 0.0) or 0.0)
    baseline_profit = float(baseline.get("max_profit", 0.0) or 0.0)
    baseline_loss = float(baseline.get("max_loss", 0.0) or 0.0)
    baseline_breakeven = float(baseline.get("breakeven", 0.0) or 0.0)
    baseline_width = float(baseline.get("spread_width", 0.0) or 0.0)
    baseline_short = float(baseline.get("short_strike", 0.0) or 0.0)
    strategy_key = str(baseline.get("strategy_key") or "")

    baseline_rr = _safe_ratio(baseline_profit, baseline_loss)

    for variant in variants:
        variant_type = variant.get("variant_type")
        if variant_type == "baseline":
            variant["comparison"] = {
                "is_baseline": True,
                "delta_net_credit": 0.0,
                "delta_max_profit": 0.0,
                "delta_max_loss": 0.0,
                "delta_breakeven": 0.0,
                "delta_spread_width": 0.0,
                "risk_reward_ratio": baseline_rr,
                "delta_risk_reward_ratio": 0.0 if baseline_rr is not None else None,
                "summary": "Current scanned setup.",
                "safety_tradeoff": "Reference trade.",
            }
            continue

        current_credit = float(variant.get("net_credit", 0.0) or 0.0)
        current_profit = float(variant.get("max_profit", 0.0) or 0.0)
        current_loss = float(variant.get("max_loss", 0.0) or 0.0)
        current_breakeven = float(variant.get("breakeven", 0.0) or 0.0)
        current_width = float(variant.get("spread_width", 0.0) or 0.0)
        current_short = float(variant.get("short_strike", 0.0) or 0.0)

        current_rr = _safe_ratio(current_profit, current_loss)
        delta_rr = None
        if current_rr is not None and baseline_rr is not None:
            delta_rr = round(current_rr - baseline_rr, 4)

        variant["comparison"] = {
            "is_baseline": False,
            "delta_net_credit": _to_currency_delta(current_credit - baseline_credit),
            "delta_max_profit": _to_currency_delta(current_profit - baseline_profit),
            "delta_max_loss": _to_currency_delta(current_loss - baseline_loss),
            "delta_breakeven": round(current_breakeven - baseline_breakeven, 4),
            "delta_spread_width": round(current_width - baseline_width, 4),
            "risk_reward_ratio": current_rr,
            "delta_risk_reward_ratio": delta_rr,
            "summary": _room_to_work_summary(
                strategy_key=strategy_key,
                baseline_short=baseline_short,
                current_short=current_short,
            ),
            "safety_tradeoff": _room_to_work_summary(
                strategy_key=strategy_key,
                baseline_short=baseline_short,
                current_short=current_short,
            ),
        }

    return variants
