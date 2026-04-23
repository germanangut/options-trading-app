from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import requests

from backend.contracts.ticket_models import ExecutionTicket
from backend.observability.logging import get_logger, log_event
from backend.repositories.factory import get_ticket_repository
from backend.services.ticket_service import serialize_execution_ticket
from settings import get_settings


logger = get_logger(__name__)


class TicketSubmissionError(RuntimeError):
    def __init__(self, message: str, *, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


class TicketBrokerRejectedError(TicketSubmissionError):
    def __init__(
        self,
        message: str,
        *,
        response_payload: dict[str, Any] | None,
        broker_status_raw: str | None,
    ):
        super().__init__(message, status_code=400)
        self.response_payload = response_payload
        self.broker_status_raw = broker_status_raw


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _sanitize_error_message(message: str | None) -> str | None:
    if not message:
        return None
    cleaned = " ".join(str(message).strip().split())
    if len(cleaned) <= 280:
        return cleaned
    return f"{cleaned[:277]}..."


def _is_paper_trading_url(base_url: str) -> bool:
    normalized = (base_url or "").strip().lower()
    return normalized.startswith("https://paper-api.alpaca.markets")


def _alpaca_credentials_and_url() -> tuple[str, str, str]:
    settings = get_settings()
    key = str(settings.get("alpaca_api_key") or "").strip()
    secret = str(settings.get("alpaca_api_secret") or "").strip()
    trading_base = str(settings.get("alpaca_trading_base_url") or "").strip()

    if not key or not secret:
        raise TicketSubmissionError(
            "Paper trading credentials are not configured. Set ALPACA_API_KEY and ALPACA_API_SECRET.",
            status_code=400,
        )

    if not _is_paper_trading_url(trading_base):
        raise TicketSubmissionError(
            "Paper-only guardrail blocked submission because ALPACA_TRADING_BASE_URL is not a paper endpoint.",
            status_code=400,
        )

    return key, secret, trading_base


def _ticket_is_submittable(ticket: ExecutionTicket) -> None:
    if ticket.quantity < 1:
        raise TicketSubmissionError("Ticket quantity must be greater than zero.", status_code=400)

    if ticket.execution_status not in {"draft", "ready"}:
        raise TicketSubmissionError(
            f"Ticket status '{ticket.execution_status}' is not eligible for submission.",
            status_code=400,
        )

    if not ticket.expiration_date or ticket.short_strike is None or ticket.long_strike is None:
        raise TicketSubmissionError(
            "Ticket is missing required option snapshot fields (expiration_date, short_strike, long_strike).",
            status_code=400,
        )


def _strategy_option_right(ticket: ExecutionTicket) -> str:
    key = ticket.strategy_key.strip().lower()
    if key == "bull_put_spread":
        return "P"
    if key == "bear_call_spread":
        return "C"
    raise TicketSubmissionError(
        f"Strategy '{ticket.strategy_key}' is not yet supported for paper submission in PU-15A.4.",
        status_code=400,
    )


def _format_option_symbol(*, ticker: str, expiration_date: str, right: str, strike: float) -> str:
    compact_exp = expiration_date.replace("-", "")
    if len(compact_exp) != 8 or not compact_exp.isdigit():
        raise TicketSubmissionError("expiration_date must be in YYYY-MM-DD format.", status_code=400)
    yymmdd = compact_exp[2:]
    strike_component = int(round(float(strike) * 1000))
    return f"{ticker.upper()}{yymmdd}{right}{strike_component:08d}"


def _build_submission_payload(ticket: ExecutionTicket) -> dict[str, Any]:
    _ticket_is_submittable(ticket)
    right = _strategy_option_right(ticket)

    if ticket.order_intent not in {"open_credit", "open_debit"}:
        raise TicketSubmissionError(
            f"order_intent '{ticket.order_intent}' is not supported for broker submission in PU-15A.4.",
            status_code=400,
        )

    short_side = "sell_to_open" if ticket.order_intent == "open_credit" else "buy_to_open"
    long_side = "buy_to_open" if ticket.order_intent == "open_credit" else "sell_to_open"

    short_symbol = _format_option_symbol(
        ticker=ticket.ticker,
        expiration_date=ticket.expiration_date or "",
        right=right,
        strike=ticket.short_strike or 0,
    )
    long_symbol = _format_option_symbol(
        ticker=ticket.ticker,
        expiration_date=ticket.expiration_date or "",
        right=right,
        strike=ticket.long_strike or 0,
    )

    payload: dict[str, Any] = {
        "order_class": "mleg",
        "type": "market",
        "time_in_force": "day",
        "qty": str(ticket.quantity),
        "client_order_id": f"{ticket.ticket_id}-{int(datetime.now(UTC).timestamp())}",
        "legs": [
            {"symbol": short_symbol, "ratio_qty": "1", "side": short_side},
            {"symbol": long_symbol, "ratio_qty": "1", "side": long_side},
        ],
    }

    # For credit/debit intent, include limit when the ticket has an estimate.
    if ticket.net_credit_estimate is not None:
        payload["type"] = "limit"
        payload["limit_price"] = str(abs(float(ticket.net_credit_estimate)))

    return payload


def _map_broker_status_to_execution_status(raw_status: str | None) -> str:
    normalized = (raw_status or "").strip().lower()

    if normalized in {"filled"}:
        return "filled"

    if normalized in {"rejected", "suspended"}:
        return "rejected"

    if normalized in {"canceled", "expired", "done_for_day", "pending_cancel"}:
        return "canceled"

    if normalized in {
        "new",
        "accepted",
        "pending_new",
        "partially_filled",
        "pending_replace",
        "replaced",
        "calculated",
        "stopped",
    }:
        return "accepted"

    return "submitted"


def _alpaca_headers(key: str, secret: str) -> dict[str, str]:
    return {
        "APCA-API-KEY-ID": key,
        "APCA-API-SECRET-KEY": secret,
        "Content-Type": "application/json",
    }


def _extract_message(payload: dict[str, Any] | None) -> str | None:
    if not payload:
        return None
    if isinstance(payload.get("message"), str):
        return payload["message"]
    if isinstance(payload.get("detail"), str):
        return payload["detail"]
    return None


def _submit_order_to_paper(
    payload: dict[str, Any],
    *,
    key: str,
    secret: str,
    trading_base_url: str,
) -> dict[str, Any]:
    url = f"{trading_base_url.rstrip('/')}/v2/orders"
    timeout_seconds = max(1.0, float(get_settings().get("provider_timeout_seconds", 12)))

    try:
        response = requests.post(
            url,
            headers=_alpaca_headers(key, secret),
            json=payload,
            timeout=timeout_seconds,
        )
    except requests.RequestException as exc:
        raise TicketSubmissionError(
            "Paper broker request failed before receiving a response.",
            status_code=502,
        ) from exc

    try:
        body = response.json()
    except ValueError:
        body = {"raw": response.text[:300] if response.text else ""}

    if response.status_code >= 400:
        broker_status_raw = str(body.get("status") or f"http_{response.status_code}")
        message = _extract_message(body) or "Paper broker rejected the order request."
        raise TicketBrokerRejectedError(
            message,
            response_payload=body if isinstance(body, dict) else None,
            broker_status_raw=broker_status_raw,
        )

    if not isinstance(body, dict):
        raise TicketSubmissionError("Paper broker response could not be parsed.", status_code=502)

    return body


def _fetch_order_status_from_paper(*, order_id: str, key: str, secret: str, trading_base_url: str) -> dict[str, Any]:
    url = f"{trading_base_url.rstrip('/')}/v2/orders/{order_id}"
    timeout_seconds = max(1.0, float(get_settings().get("provider_timeout_seconds", 12)))

    try:
        response = requests.get(
            url,
            headers=_alpaca_headers(key, secret),
            timeout=timeout_seconds,
        )
    except requests.RequestException as exc:
        raise TicketSubmissionError(
            "Paper broker status refresh failed before receiving a response.",
            status_code=502,
        ) from exc

    try:
        body = response.json()
    except ValueError:
        body = {"raw": response.text[:300] if response.text else ""}

    if response.status_code >= 400:
        message = _extract_message(body if isinstance(body, dict) else None) or "Unable to refresh paper broker status."
        raise TicketSubmissionError(_sanitize_error_message(message) or "Unable to refresh paper broker status.", status_code=400)

    if not isinstance(body, dict):
        raise TicketSubmissionError("Paper broker status response could not be parsed.", status_code=502)

    return body


def _record_submission_failure(
    *,
    ticket: ExecutionTicket,
    user_id: str,
    request_payload: dict[str, Any] | None,
    response_payload: dict[str, Any] | None,
    broker_status_raw: str | None,
    status_after_failure: str,
    message: str,
) -> None:
    now = _utc_now_iso()
    get_ticket_repository().record_submission_result(
        ticket.ticket_id,
        user_id=user_id,
        execution_status=status_after_failure,
        broker_order_id=ticket.broker_order_id,
        broker_status_raw=broker_status_raw,
        broker_submitted_at=now,
        broker_updated_at=now,
        last_submission_payload=request_payload,
        last_submission_response=response_payload,
        submission_error_message=_sanitize_error_message(message),
        updated_at=now,
    )


def submit_ticket_to_paper(ticket_id: str, *, user_id: str) -> dict[str, Any] | None:
    ticket = get_ticket_repository().get_ticket(ticket_id, user_id=user_id)
    if ticket is None:
        return None

    key, secret, trading_base_url = _alpaca_credentials_and_url()

    payload = _build_submission_payload(ticket)

    try:
        broker_response = _submit_order_to_paper(
            payload,
            key=key,
            secret=secret,
            trading_base_url=trading_base_url,
        )
    except TicketBrokerRejectedError as exc:
        _record_submission_failure(
            ticket=ticket,
            user_id=user_id,
            request_payload=payload,
            response_payload=exc.response_payload,
            broker_status_raw=exc.broker_status_raw,
            status_after_failure="rejected",
            message=str(exc),
        )
        raise
    except TicketSubmissionError as exc:
        _record_submission_failure(
            ticket=ticket,
            user_id=user_id,
            request_payload=payload,
            response_payload=None,
            broker_status_raw="submission_error",
            status_after_failure=ticket.execution_status,
            message=str(exc),
        )
        raise

    broker_status_raw = str(broker_response.get("status") or "submitted")
    mapped_status = _map_broker_status_to_execution_status(broker_status_raw)
    now = _utc_now_iso()

    updated = get_ticket_repository().record_submission_result(
        ticket.ticket_id,
        user_id=user_id,
        execution_status=mapped_status,
        broker_order_id=str(broker_response.get("id") or "") or None,
        broker_status_raw=broker_status_raw,
        broker_submitted_at=str(broker_response.get("submitted_at") or now),
        broker_updated_at=str(broker_response.get("updated_at") or now),
        last_submission_payload=payload,
        last_submission_response=broker_response,
        submission_error_message=None,
        updated_at=now,
    )
    if updated is None:
        return None

    log_event(
        logger,
        "ticket_submitted_to_paper",
        ticket_id=ticket.ticket_id,
        trade_id=ticket.trade_id,
        execution_status=mapped_status,
        broker_status_raw=broker_status_raw,
    )
    return serialize_execution_ticket(updated)


def refresh_ticket_broker_status(ticket_id: str, *, user_id: str) -> dict[str, Any] | None:
    ticket = get_ticket_repository().get_ticket(ticket_id, user_id=user_id)
    if ticket is None:
        return None

    if not ticket.broker_order_id:
        raise TicketSubmissionError(
            "Ticket has no broker_order_id yet. Submit to paper before refreshing broker status.",
            status_code=400,
        )

    key, secret, trading_base_url = _alpaca_credentials_and_url()

    broker_response = _fetch_order_status_from_paper(
        order_id=ticket.broker_order_id,
        key=key,
        secret=secret,
        trading_base_url=trading_base_url,
    )

    broker_status_raw = str(broker_response.get("status") or "submitted")
    mapped_status = _map_broker_status_to_execution_status(broker_status_raw)
    now = _utc_now_iso()

    updated = get_ticket_repository().record_submission_result(
        ticket.ticket_id,
        user_id=user_id,
        execution_status=mapped_status,
        broker_order_id=ticket.broker_order_id,
        broker_status_raw=broker_status_raw,
        broker_submitted_at=ticket.broker_submitted_at,
        broker_updated_at=str(broker_response.get("updated_at") or now),
        last_submission_payload=ticket.last_submission_payload,
        last_submission_response=broker_response,
        submission_error_message=None,
        updated_at=now,
    )

    if updated is None:
        return None

    return serialize_execution_ticket(updated)


def map_broker_status_for_tests(raw_status: str | None) -> str:
    """Test-facing helper to validate mapping behavior without network calls."""
    return _map_broker_status_to_execution_status(raw_status)
