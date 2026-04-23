from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.api.dependencies.auth import require_current_user
from backend.api.schemas.payoff import PayoffEnvelopeResponse
from backend.repositories.factory import get_ticket_repository
from backend.services.payoff_engine import (
    calculate_payoff,
    payoff_analysis_to_dict,
    payoff_input_from_ticket,
    payoff_input_from_trade,
)
from backend.services.scan_service import get_scan_by_id, get_trade_by_id


router = APIRouter(prefix="/api/v1/payoff", tags=["payoff"])


@router.get("/scans/{scan_id}/trades/{trade_id}", response_model=PayoffEnvelopeResponse)
def get_trade_payoff(
    scan_id: str,
    trade_id: str,
    point_count: int = Query(default=41, ge=5, le=301),
    current_user: dict[str, str | None] = Depends(require_current_user),
) -> dict[str, object]:
    scan_result = get_scan_by_id(scan_id, user_id=current_user["user_id"])
    if scan_result is None:
        raise HTTPException(status_code=404, detail=f"Scan '{scan_id}' was not found.")

    trade = get_trade_by_id(scan_result, trade_id)
    if trade is None:
        raise HTTPException(status_code=404, detail=f"Trade '{trade_id}' was not found in scan '{scan_id}'.")

    try:
        payoff_input = payoff_input_from_trade(trade)
        analysis = calculate_payoff(payoff_input, point_count=point_count)
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "source_type": "qualified_trade",
        "source_id": trade_id,
        "payoff": payoff_analysis_to_dict(analysis),
    }


@router.get("/tickets/{ticket_id}", response_model=PayoffEnvelopeResponse)
def get_ticket_payoff(
    ticket_id: str,
    point_count: int = Query(default=41, ge=5, le=301),
    current_user: dict[str, str | None] = Depends(require_current_user),
) -> dict[str, object]:
    ticket = get_ticket_repository().get_ticket(ticket_id, user_id=current_user["user_id"])
    if ticket is None:
        raise HTTPException(status_code=404, detail=f"Ticket '{ticket_id}' not found.")

    try:
        payoff_input = payoff_input_from_ticket({
            "strategy_key": ticket.strategy_key,
            "ticker": ticket.ticker,
            "underlying_price_at_creation": ticket.underlying_price_at_creation,
            "short_strike": ticket.short_strike,
            "long_strike": ticket.long_strike,
            "net_credit_estimate": ticket.net_credit_estimate,
            "quantity": ticket.quantity,
        })
        analysis = calculate_payoff(payoff_input, point_count=point_count)
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "source_type": "execution_ticket",
        "source_id": ticket_id,
        "payoff": payoff_analysis_to_dict(analysis),
    }
