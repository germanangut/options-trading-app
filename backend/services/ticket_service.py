from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from backend.contracts.ticket_models import (
    DEFAULT_ORDER_INTENT,
    DEFAULT_QUANTITY,
    EXECUTION_TICKET_STATUSES,
    OPERATOR_PATCHABLE_STATUSES,
    ExecutionTicket,
    is_operator_patchable_status,
    is_valid_execution_status,
)
from backend.repositories.factory import get_ticket_repository


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _new_ticket_id() -> str:
    return f"ticket_{uuid4().hex}"


def _serialize_ticket(ticket: ExecutionTicket) -> dict[str, object]:
    return {
        "ticket_id": ticket.ticket_id,
        "trade_id": ticket.trade_id,
        "source_scan_id": ticket.source_scan_id,
        "ticker": ticket.ticker,
        "strategy_key": ticket.strategy_key,
        "strategy_label": ticket.strategy_label,
        "directional_bias": ticket.directional_bias,
        "expiration_date": ticket.expiration_date,
        "short_strike": ticket.short_strike,
        "long_strike": ticket.long_strike,
        "underlying_price_at_creation": ticket.underlying_price_at_creation,
        "net_credit_estimate": ticket.net_credit_estimate,
        "max_risk_estimate": ticket.max_risk_estimate,
        "adjusted_score_at_creation": ticket.adjusted_score_at_creation,
        "quantity": ticket.quantity,
        "order_intent": ticket.order_intent,
        "execution_status": ticket.execution_status,
        "note": ticket.note,
        "created_at": ticket.created_at,
        "updated_at": ticket.updated_at,
    }


def create_execution_ticket(
    *,
    user_id: str,
    trade_id: str,
    source_scan_id: str | None,
    ticker: str,
    strategy_key: str,
    strategy_label: str,
    directional_bias: str | None,
    expiration_date: str | None,
    short_strike: float | None,
    long_strike: float | None,
    underlying_price_at_creation: float | None,
    net_credit_estimate: float | None,
    max_risk_estimate: float | None,
    adjusted_score_at_creation: float | None,
    quantity: int = DEFAULT_QUANTITY,
    order_intent: str = DEFAULT_ORDER_INTENT,
    note: str | None = None,
) -> dict[str, object]:
    if not trade_id or not trade_id.strip():
        raise ValueError("trade_id is required.")
    if not ticker or not ticker.strip():
        raise ValueError("ticker is required.")
    if not strategy_key or not strategy_key.strip():
        raise ValueError("strategy_key is required.")
    if not strategy_label or not strategy_label.strip():
        raise ValueError("strategy_label is required.")
    if quantity < 1:
        raise ValueError("quantity must be at least 1.")

    now = _utc_now_iso()
    ticket = ExecutionTicket(
        ticket_id=_new_ticket_id(),
        owner_user_id=user_id,
        trade_id=trade_id.strip(),
        source_scan_id=source_scan_id,
        ticker=ticker.strip().upper(),
        strategy_key=strategy_key.strip(),
        strategy_label=strategy_label.strip(),
        directional_bias=directional_bias,
        expiration_date=expiration_date,
        short_strike=short_strike,
        long_strike=long_strike,
        underlying_price_at_creation=underlying_price_at_creation,
        net_credit_estimate=net_credit_estimate,
        max_risk_estimate=max_risk_estimate,
        adjusted_score_at_creation=adjusted_score_at_creation,
        quantity=quantity,
        order_intent=order_intent,
        execution_status="draft",
        note=note,
        created_at=now,
        updated_at=now,
    )

    stored = get_ticket_repository().create_ticket(ticket)
    return _serialize_ticket(stored)


def get_execution_ticket(ticket_id: str, *, user_id: str) -> dict[str, object] | None:
    ticket_id = (ticket_id or "").strip()
    if not ticket_id:
        raise ValueError("ticket_id is required.")

    ticket = get_ticket_repository().get_ticket(ticket_id, user_id=user_id)
    if ticket is None:
        return None

    return _serialize_ticket(ticket)


def get_tickets_by_trade(trade_id: str, *, user_id: str) -> list[dict[str, object]]:
    trade_id = (trade_id or "").strip()
    if not trade_id:
        raise ValueError("trade_id is required.")

    tickets = get_ticket_repository().get_tickets_by_trade(trade_id, user_id=user_id)
    return [_serialize_ticket(t) for t in tickets]


def list_execution_tickets(
    *,
    user_id: str,
    execution_status: str | None = None,
    limit: int | None = None,
) -> list[dict[str, object]]:
    if execution_status is not None and not is_valid_execution_status(execution_status):
        raise ValueError(
            f"Unsupported execution_status '{execution_status}'. "
            f"Valid values: {', '.join(EXECUTION_TICKET_STATUSES)}."
        )

    tickets = get_ticket_repository().list_tickets(
        user_id=user_id,
        execution_status=execution_status,
        limit=limit,
    )
    return [_serialize_ticket(t) for t in tickets]


def patch_execution_ticket(
    ticket_id: str,
    *,
    user_id: str,
    quantity: int | None = None,
    note: str | None = None,
    clear_note: bool = False,
    execution_status: str | None = None,
) -> dict[str, object] | None:
    ticket_id = (ticket_id or "").strip()
    if not ticket_id:
        raise ValueError("ticket_id is required.")

    if quantity is not None and quantity < 1:
        raise ValueError("quantity must be at least 1.")

    if execution_status is not None:
        if not is_operator_patchable_status(execution_status):
            raise ValueError(
                f"execution_status '{execution_status}' cannot be set directly. "
                f"Operator-settable values: {', '.join(OPERATOR_PATCHABLE_STATUSES)}."
            )

    existing = get_ticket_repository().get_ticket(ticket_id, user_id=user_id)
    if existing is None:
        return None

    updated = get_ticket_repository().update_ticket(
        ticket_id,
        user_id=user_id,
        quantity=quantity,
        note=note,
        clear_note=clear_note,
        execution_status=execution_status,
        updated_at=_utc_now_iso(),
    )
    if updated is None:
        return None

    return _serialize_ticket(updated)
