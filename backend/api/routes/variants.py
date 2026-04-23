"""Variant analysis API routes for PU-15B.2.

Provides analytical strategy variants (baseline, conservative, max_credit)
for a selected qualified trade. These are analytical only — not execution-ready.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from backend.api.dependencies.auth import require_current_user
from backend.api.schemas.variants import VariantSetResponse
from backend.services.scan_service import get_scan_by_id, get_trade_by_id
from backend.services.variant_comparison_service import build_variant_comparisons
from backend.services.variant_service import generate_variants


router = APIRouter(prefix="/api/v1/variants", tags=["variants"])


def _variant_set_to_dict(variant_set) -> dict:
    variants_payload = []
    for v in variant_set.variants:
        v_dict = {
            "variant_type": v.variant_type,
            "strategy_key": v.strategy_key,
            "reference_trade_id": v.reference_trade_id,
            "short_strike": v.short_strike,
            "long_strike": v.long_strike,
            "expiration_date": v.expiration_date,
            "net_credit": v.net_credit,
            "spread_width": v.spread_width,
            "max_profit": v.max_profit,
            "max_loss": v.max_loss,
            "breakeven": v.breakeven,
            "label": v.label,
            "rationale": v.rationale,
            "is_credit_estimated": v.is_credit_estimated,
            "comparison": None,
            "payoff": None,
        }
        if v.payoff is not None:
            p = v.payoff
            v_dict["payoff"] = {
                "strategy_key": p.strategy_key,
                "ticker": p.ticker,
                "quantity": p.quantity,
                "underlying_price_reference": p.underlying_price_reference,
                "short_strike": p.short_strike,
                "long_strike": p.long_strike,
                "net_credit": p.net_credit,
                "spread_width": p.spread_width,
                "max_profit": p.max_profit,
                "max_loss": p.max_loss,
                "breakeven_low": p.breakeven_low,
                "breakeven_high": p.breakeven_high,
                "profit_zone": p.profit_zone,
                "loss_zone": p.loss_zone,
                "expiration_summary": p.expiration_summary,
                "price_grid": p.price_grid,
                "payoff_points": [
                    {"underlying_price": pt.underlying_price, "expiration_payoff": pt.expiration_payoff}
                    for pt in p.payoff_points
                ],
            }
        variants_payload.append(v_dict)

    variants_payload = build_variant_comparisons(variants_payload)

    return {
        "scan_id": variant_set.scan_id,
        "trade_id": variant_set.trade_id,
        "strategy_key": variant_set.strategy_key,
        "underlying_price_reference": variant_set.underlying_price_reference,
        "ticker": variant_set.ticker,
        "variants": variants_payload,
    }


@router.get(
    "/scans/{scan_id}/trades/{trade_id}",
    response_model=VariantSetResponse,
)
def get_trade_variants(
    scan_id: str,
    trade_id: str,
    current_user: dict[str, str | None] = Depends(require_current_user),
) -> dict:
    scan_result = get_scan_by_id(scan_id, user_id=current_user["user_id"])
    if scan_result is None:
        raise HTTPException(status_code=404, detail=f"Scan '{scan_id}' was not found.")

    trade = get_trade_by_id(scan_result, trade_id)
    if trade is None:
        raise HTTPException(
            status_code=404,
            detail=f"Trade '{trade_id}' was not found in scan '{scan_id}'.",
        )

    try:
        variant_set = generate_variants(trade, scan_id=scan_id, trade_id=trade_id)
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return _variant_set_to_dict(variant_set)
