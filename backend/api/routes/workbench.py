"""What-If Workbench API routes for PU-15B.4.

Provides a controlled analytical what-if workbench for a selected trade.
Supports GET with query params for strike_shift and width_adjustment.
These are analytical endpoints only — not execution-ready.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.api.dependencies.auth import require_current_user
from backend.api.schemas.workbench import (
    WorkbenchComparisonResponse,
    WorkbenchResultResponse,
    WorkbenchScenarioResponse,
)
from backend.contracts.workbench_models import (
    STRIKE_SHIFT_LABELS,
    STRIKE_SHIFT_OPTIONS,
    WIDTH_LABELS,
    WIDTH_OPTIONS,
    WorkbenchParams,
)
from backend.services.scan_service import get_scan_by_id, get_trade_by_id
from backend.services.workbench_service import generate_workbench


router = APIRouter(prefix="/api/v1/workbench", tags=["workbench"])


def _scenario_to_response(scenario) -> WorkbenchScenarioResponse:
    payoff_response = None
    if scenario.payoff is not None:
        p = scenario.payoff
        from backend.api.schemas.payoff import PayoffAnalysisResponse, PayoffPointResponse
        payoff_response = PayoffAnalysisResponse(
            strategy_key=p.strategy_key,
            ticker=p.ticker,
            quantity=p.quantity,
            underlying_price_reference=p.underlying_price_reference,
            short_strike=p.short_strike,
            long_strike=p.long_strike,
            net_credit=p.net_credit,
            spread_width=p.spread_width,
            max_profit=p.max_profit,
            max_loss=p.max_loss,
            breakeven_low=p.breakeven_low,
            breakeven_high=p.breakeven_high,
            profit_zone=p.profit_zone,
            loss_zone=p.loss_zone,
            expiration_summary=p.expiration_summary,
            price_grid=p.price_grid,
            payoff_points=[
                PayoffPointResponse(
                    underlying_price=pt.underlying_price,
                    expiration_payoff=pt.expiration_payoff,
                )
                for pt in p.payoff_points
            ],
        )

    return WorkbenchScenarioResponse(
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
        payoff=payoff_response,
    )


@router.get(
    "/scans/{scan_id}/trades/{trade_id}",
    response_model=WorkbenchResultResponse,
    summary="Get what-if workbench scenario for a trade",
)
async def get_workbench_scenario(
    scan_id: str,
    trade_id: str,
    strike_shift: str = Query(
        default="baseline",
        description="Strike shift choice: further_otm | baseline | closer_atm",
    ),
    width_adjustment: str = Query(
        default="baseline",
        description="Width adjustment choice: narrower | baseline | wider",
    ),
    current_user: dict[str, str | None] = Depends(require_current_user),
):
    """Return a what-if workbench result for the selected trade.

    Query parameters control the analytical adjustments:
    - strike_shift: 'further_otm' | 'baseline' | 'closer_atm'
    - width_adjustment: 'narrower' | 'baseline' | 'wider'

    The baseline is always included. The scenario is included when the
    chosen parameter combination produces a valid spread. An
    unavailable_reason is returned when it cannot be built cleanly.
    """
    if strike_shift not in STRIKE_SHIFT_OPTIONS:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid strike_shift '{strike_shift}'. Must be one of: {', '.join(STRIKE_SHIFT_OPTIONS)}",
        )
    if width_adjustment not in WIDTH_OPTIONS:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid width_adjustment '{width_adjustment}'. Must be one of: {', '.join(WIDTH_OPTIONS)}",
        )

    scan = get_scan_by_id(scan_id, user_id=current_user["user_id"])
    if scan is None:
        raise HTTPException(status_code=404, detail=f"Scan '{scan_id}' not found.")

    trade = get_trade_by_id(scan, trade_id)
    if trade is None:
        raise HTTPException(status_code=404, detail=f"Trade '{trade_id}' not found in scan '{scan_id}'.")

    params = WorkbenchParams(
        strike_shift=strike_shift,
        width_adjustment=width_adjustment,
    )

    result = generate_workbench(trade, scan_id=scan_id, trade_id=trade_id, params=params)

    baseline_response = _scenario_to_response(result.baseline)
    scenario_response = _scenario_to_response(result.scenario) if result.scenario is not None else None

    comparison_response: WorkbenchComparisonResponse | None = None
    if result.comparison is not None:
        c = result.comparison
        comparison_response = WorkbenchComparisonResponse(
            delta_net_credit=c.delta_net_credit,
            delta_max_profit=c.delta_max_profit,
            delta_max_loss=c.delta_max_loss,
            delta_breakeven=c.delta_breakeven,
            delta_spread_width=c.delta_spread_width,
            risk_reward_ratio=c.risk_reward_ratio,
            delta_risk_reward_ratio=c.delta_risk_reward_ratio,
            summary=c.summary,
        )

    return WorkbenchResultResponse(
        scan_id=result.scan_id,
        trade_id=result.trade_id,
        strategy_key=result.strategy_key,
        underlying_price_reference=result.underlying_price_reference,
        ticker=result.ticker,
        strike_shift=result.strike_shift,
        width_adjustment=result.width_adjustment,
        baseline=baseline_response,
        scenario=scenario_response,
        comparison=comparison_response,
        unavailable_reason=result.unavailable_reason,
        strike_shift_options=[
            {"value": k, "label": v} for k, v in STRIKE_SHIFT_LABELS.items()
        ],
        width_options=[
            {"value": k, "label": v} for k, v in WIDTH_LABELS.items()
        ],
    )
