from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from backend.contracts.ticket_models import ExecutionTicket
from backend.repositories.factory import get_ticket_repository
from backend.services.ticket_service import serialize_execution_ticket
from backend.services.ticket_submission_service import (
    TicketSubmissionError,
    fetch_open_paper_positions,
    fetch_recent_paper_orders,
    get_paper_broker_configuration,
    refresh_ticket_broker_status,
)


PENDING_TICKET_STATUSES = {"draft", "ready", "submitted", "accepted"}
TERMINAL_TICKET_STATUSES = {"rejected", "canceled", "filled"}


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _to_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _extract_ticker_from_option_symbol(symbol: str | None) -> str | None:
    if not symbol:
        return None
    token = str(symbol).strip().upper()
    letters = []
    for char in token:
        if char.isalpha():
            letters.append(char)
            continue
        break
    return "".join(letters) if letters else None


def _build_position_rows(
    live_positions: list[dict[str, Any]],
    filled_tickets_by_ticker: dict[str, list[ExecutionTicket]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for position in live_positions:
        symbol = str(position.get("symbol") or "").strip().upper()
        ticker = _extract_ticker_from_option_symbol(symbol)
        ticket_candidates = filled_tickets_by_ticker.get(ticker or "", [])
        linked_ticket = ticket_candidates[0] if ticket_candidates else None

        rows.append(
            {
                "symbol": symbol or None,
                "ticker": ticker,
                "qty": _to_int(position.get("qty")),
                "side": position.get("side"),
                "avg_entry_price": _to_float(position.get("avg_entry_price")),
                "market_value": _to_float(position.get("market_value")),
                "cost_basis": _to_float(position.get("cost_basis")),
                "unrealized_pl": _to_float(position.get("unrealized_pl")),
                "unrealized_plpc": _to_float(position.get("unrealized_plpc")),
                "realized_pl": None,
                "broker_updated_at": position.get("updated_at") or position.get("lastday_price_date"),
                "linked_ticket_id": linked_ticket.ticket_id if linked_ticket else None,
                "strategy_label": linked_ticket.strategy_label if linked_ticket else None,
                "directional_bias": linked_ticket.directional_bias if linked_ticket else None,
                "ticket_execution_status": linked_ticket.execution_status if linked_ticket else None,
                "estimated_credit_or_debit": linked_ticket.net_credit_estimate if linked_ticket else None,
            }
        )

    return rows


def _build_closed_history_rows(
    tickets: list[ExecutionTicket],
    open_position_tickers: set[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for ticket in tickets:
        if ticket.execution_status not in TERMINAL_TICKET_STATUSES:
            continue

        if ticket.execution_status == "filled" and ticket.ticker in open_position_tickers:
            continue

        payload = serialize_execution_ticket(ticket)
        payload["history_outcome"] = ticket.execution_status
        payload["realized_pl"] = None
        payload["unrealized_pl"] = None
        rows.append(payload)

    return rows


def _build_recent_order_rows(orders: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for order in orders:
        rows.append(
            {
                "broker_order_id": order.get("id"),
                "symbol": order.get("symbol"),
                "status": order.get("status"),
                "order_type": order.get("type"),
                "side": order.get("side"),
                "qty": _to_int(order.get("qty")),
                "filled_qty": _to_int(order.get("filled_qty")),
                "filled_avg_price": _to_float(order.get("filled_avg_price")),
                "submitted_at": order.get("submitted_at"),
                "updated_at": order.get("updated_at"),
            }
        )
    return rows


def get_paper_dashboard(
    *,
    user_id: str,
    refresh_status: bool = False,
    limit: int = 250,
) -> dict[str, Any]:
    repository = get_ticket_repository()

    # App-owned history source of truth.
    tickets = repository.list_tickets(user_id=user_id, limit=max(1, min(limit, 500)))

    refresh_errors: list[str] = []
    if refresh_status:
        for ticket in tickets:
            if ticket.execution_status in {"submitted", "accepted"} and ticket.broker_order_id:
                try:
                    refresh_ticket_broker_status(ticket.ticket_id, user_id=user_id)
                except TicketSubmissionError as exc:
                    refresh_errors.append(str(exc))
        tickets = repository.list_tickets(user_id=user_id, limit=max(1, min(limit, 500)))

    pending_orders = [serialize_execution_ticket(ticket) for ticket in tickets if ticket.execution_status in PENDING_TICKET_STATUSES]

    filled_tickets_by_ticker: dict[str, list[ExecutionTicket]] = {}
    for ticket in tickets:
        if ticket.execution_status != "filled":
            continue
        bucket = filled_tickets_by_ticker.setdefault(ticket.ticker, [])
        bucket.append(ticket)

    for ticket_list in filled_tickets_by_ticker.values():
        ticket_list.sort(key=lambda item: item.updated_at or "", reverse=True)

    live_positions: list[dict[str, Any]] = []
    recent_orders: list[dict[str, Any]] = []
    broker_live_data_available = False
    broker_live_data_warning: str | None = None

    try:
        key, secret, trading_base_url = get_paper_broker_configuration()
        broker_live_data_available = True
        live_positions = fetch_open_paper_positions(key=key, secret=secret, trading_base_url=trading_base_url)
        recent_orders = fetch_recent_paper_orders(key=key, secret=secret, trading_base_url=trading_base_url, limit=100)
    except TicketSubmissionError as exc:
        broker_live_data_warning = str(exc)

    open_positions = _build_position_rows(live_positions, filled_tickets_by_ticker)
    open_position_tickers = {
        str(position.get("ticker") or "").upper()
        for position in open_positions
        if position.get("ticker")
    }

    closed_history = _build_closed_history_rows(tickets, open_position_tickers)

    return {
        "pending_orders": pending_orders,
        "open_positions": open_positions,
        "closed_trades": closed_history,
        "recent_orders": _build_recent_order_rows(recent_orders),
        "summary": {
            "pending_count": len(pending_orders),
            "open_positions_count": len(open_positions),
            "closed_count": len(closed_history),
            "recent_orders_count": len(recent_orders),
        },
        "data_source": {
            "mode": "hybrid",
            "app_history_source": "execution_ticket",
            "broker_live_data_available": broker_live_data_available,
            "broker_live_data_warning": broker_live_data_warning,
            "status_refresh_attempted": refresh_status,
            "status_refresh_errors": refresh_errors,
            "generated_at": _utc_now_iso(),
        },
    }
