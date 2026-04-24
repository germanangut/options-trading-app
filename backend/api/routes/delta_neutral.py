"""Delta-neutral exploration API routes for PU-15B.5."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from backend.api.dependencies.auth import require_current_user
from backend.api.schemas.delta_neutral import (
    DeltaNeutralComparisonResponse,
    DeltaNeutralExplorationResponse,
    DeltaNeutralScenarioResponse,
)
from backend.api.schemas.payoff import PayoffAnalysisResponse, PayoffPointResponse
from backend.services.delta_neutral_service import generate_delta_neutral_exploration
from backend.services.scan_service import get_scan_by_id, get_trade_by_id


router = APIRouter(prefix="/api/v1/delta-neutral", tags=["delta-neutral"])


def _to_payoff_response(payoff) -> PayoffAnalysisResponse | None:
    if payoff is None:
        return None
    return PayoffAnalysisResponse(
        strategy_key=payoff.strategy_key,
        ticker=payoff.ticker,
        quantity=payoff.quantity,
        underlying_price_reference=payoff.underlying_price_reference,
        short_strike=payoff.short_strike,
        long_strike=payoff.long_strike,
        net_credit=payoff.net_credit,
        spread_width=payoff.spread_width,
        max_profit=payoff.max_profit,
        max_loss=payoff.max_loss,
        breakeven_low=payoff.breakeven_low,
        breakeven_high=payoff.breakeven_high,
        profit_zone=payoff.profit_zone,
        loss_zone=payoff.loss_zone,
        expiration_summary=payoff.expiration_summary,
        price_grid=payoff.price_grid,
        payoff_points=[
            PayoffPointResponse(
                underlying_price=point.underlying_price,
                expiration_payoff=point.expiration_payoff,
            )
            for point in payoff.payoff_points
        ],
    )


def _to_scenario_response(scenario) -> DeltaNeutralScenarioResponse:
    return DeltaNeutralScenarioResponse(
        strategy_key=scenario.strategy_key,
        ticker=scenario.ticker,
        short_strike=scenario.short_strike,
        long_strike=scenario.long_strike,
        expiration_date=scenario.expiration_date,
        net_credit=scenario.net_credit,
        spread_width=scenario.spread_width,
        max_profit=scenario.max_profit,
        max_loss=scenario.max_loss,
        breakeven=scenario.breakeven,
        label=scenario.label,
        is_credit_estimated=scenario.is_credit_estimated,
        net_delta=scenario.net_delta,
        payoff=_to_payoff_response(scenario.payoff),
    )


@router.get(
    "/scans/{scan_id}/trades/{trade_id}",
    response_model=DeltaNeutralExplorationResponse,
    summary="Get delta-neutral exploration for a selected trade",
)
async def get_delta_neutral_exploration(
    scan_id: str,
    trade_id: str,
    current_user: dict[str, str | None] = Depends(require_current_user),
):
    scan = get_scan_by_id(scan_id, user_id=current_user["user_id"])
    if scan is None:
        raise HTTPException(status_code=404, detail=f"Scan '{scan_id}' not found.")

    trade = get_trade_by_id(scan, trade_id)
    if trade is None:
        raise HTTPException(status_code=404, detail=f"Trade '{trade_id}' not found in scan '{scan_id}'.")

    result = generate_delta_neutral_exploration(trade, scan_id=scan_id, trade_id=trade_id)

    comparison_response: DeltaNeutralComparisonResponse | None = None
    if result.comparison is not None:
        c = result.comparison
        comparison_response = DeltaNeutralComparisonResponse(
            baseline_net_delta=c.baseline_net_delta,
            candidate_net_delta=c.candidate_net_delta,
            delta_reduction=c.delta_reduction,
            delta_reduction_pct=c.delta_reduction_pct,
            delta_max_profit=c.delta_max_profit,
            delta_max_loss=c.delta_max_loss,
            delta_breakeven=c.delta_breakeven,
            summary=c.summary,
        )

    candidate_response = (
        _to_scenario_response(result.neutral_candidate)
        if result.neutral_candidate is not None
        else None
    )

    return DeltaNeutralExplorationResponse(
        scan_id=result.scan_id,
        trade_id=result.trade_id,
        baseline_trade_id=result.baseline_trade_id,
        strategy_key=result.strategy_key,
        ticker=result.ticker,
        underlying_price_reference=result.underlying_price_reference,
        baseline=_to_scenario_response(result.baseline),
        neutral_candidate_available=result.neutral_candidate_available,
        neutral_candidate=candidate_response,
        comparison=comparison_response,
        rationale=result.rationale,
        limitation_note=result.limitation_note,
        unavailable_reason=result.unavailable_reason,
    )
