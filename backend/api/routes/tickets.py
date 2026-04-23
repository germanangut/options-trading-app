"""Execution ticket routes for user-managed trade execution preparation."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.api.dependencies.auth import require_current_user
from backend.api.schemas.ticket import (
    CreateExecutionTicketBody,
    ExecutionTicketListResponse,
    ExecutionTicketResponse,
    PatchExecutionTicketBody,
)
from backend.services.ticket_service import (
    create_execution_ticket,
    get_execution_ticket,
    get_tickets_by_trade,
    list_execution_tickets,
    patch_execution_ticket,
)
from backend.services.ticket_submission_service import (
    TicketSubmissionError,
    submit_ticket_to_paper,
    refresh_ticket_broker_status,
)


router = APIRouter(prefix="/api/v1/tickets", tags=["tickets"])


@router.post("", response_model=ExecutionTicketResponse, status_code=201)
def create_ticket(
    payload: CreateExecutionTicketBody,
    current_user: dict[str, str | None] = Depends(require_current_user),
) -> dict[str, object]:
    try:
        return create_execution_ticket(
            user_id=current_user["user_id"],
            trade_id=payload.trade_id,
            source_scan_id=payload.source_scan_id,
            ticker=payload.ticker,
            strategy_key=payload.strategy_key,
            strategy_label=payload.strategy_label,
            directional_bias=payload.directional_bias,
            expiration_date=payload.expiration_date,
            short_strike=payload.short_strike,
            long_strike=payload.long_strike,
            underlying_price_at_creation=payload.underlying_price_at_creation,
            net_credit_estimate=payload.net_credit_estimate,
            max_risk_estimate=payload.max_risk_estimate,
            adjusted_score_at_creation=payload.adjusted_score_at_creation,
            quantity=payload.quantity,
            order_intent=payload.order_intent,
            note=payload.note,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("", response_model=ExecutionTicketListResponse)
def list_tickets(
    execution_status: str | None = Query(default=None),
    limit: int | None = Query(default=None, ge=1, le=500),
    current_user: dict[str, str | None] = Depends(require_current_user),
) -> dict[str, list[dict[str, object]]]:
    try:
        items = list_execution_tickets(
            user_id=current_user["user_id"],
            execution_status=execution_status,
            limit=limit,
        )
        return {"items": items}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/by-trade/{trade_id}", response_model=ExecutionTicketListResponse)
def get_tickets_for_trade(
    trade_id: str,
    current_user: dict[str, str | None] = Depends(require_current_user),
) -> dict[str, list[dict[str, object]]]:
    try:
        items = get_tickets_by_trade(trade_id, user_id=current_user["user_id"])
        return {"items": items}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{ticket_id}", response_model=ExecutionTicketResponse)
def get_ticket(
    ticket_id: str,
    current_user: dict[str, str | None] = Depends(require_current_user),
) -> dict[str, object]:
    try:
        ticket = get_execution_ticket(ticket_id, user_id=current_user["user_id"])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if ticket is None:
        raise HTTPException(status_code=404, detail=f"Ticket '{ticket_id}' not found.")
    return ticket


@router.patch("/{ticket_id}", response_model=ExecutionTicketResponse)
def patch_ticket(
    ticket_id: str,
    payload: PatchExecutionTicketBody,
    current_user: dict[str, str | None] = Depends(require_current_user),
) -> dict[str, object]:
    if payload.quantity is None and payload.note is None and not payload.clear_note and payload.execution_status is None:
        raise HTTPException(
            status_code=400,
            detail="At least one patchable field is required: quantity, note, clear_note, or execution_status.",
        )

    try:
        ticket = patch_execution_ticket(
            ticket_id,
            user_id=current_user["user_id"],
            quantity=payload.quantity,
            note=payload.note,
            clear_note=payload.clear_note,
            execution_status=payload.execution_status,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if ticket is None:
        raise HTTPException(status_code=404, detail=f"Ticket '{ticket_id}' not found.")
    return ticket


@router.post("/{ticket_id}/submit-paper", response_model=ExecutionTicketResponse)
def submit_ticket(
    ticket_id: str,
    current_user: dict[str, str | None] = Depends(require_current_user),
) -> dict[str, object]:
    try:
        ticket = submit_ticket_to_paper(ticket_id, user_id=current_user["user_id"])
    except TicketSubmissionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

    if ticket is None:
        raise HTTPException(status_code=404, detail=f"Ticket '{ticket_id}' not found.")

    return ticket


@router.post("/{ticket_id}/refresh-paper", response_model=ExecutionTicketResponse)
def refresh_ticket(
    ticket_id: str,
    current_user: dict[str, str | None] = Depends(require_current_user),
) -> dict[str, object]:
    try:
        ticket = refresh_ticket_broker_status(ticket_id, user_id=current_user["user_id"])
    except TicketSubmissionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

    if ticket is None:
        raise HTTPException(status_code=404, detail=f"Ticket '{ticket_id}' not found.")

    return ticket
