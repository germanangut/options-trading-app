from __future__ import annotations

from dataclasses import dataclass


EXECUTION_TICKET_STATUSES: tuple[str, ...] = (
    "draft",
    "ready",
    "submitted",
    "accepted",
    "rejected",
    "canceled",
    "filled",
)

# Statuses the operator can transition to via PATCH (broker-facing statuses are reserved)
OPERATOR_PATCHABLE_STATUSES: tuple[str, ...] = ("draft", "ready")

ORDER_INTENTS: tuple[str, ...] = ("open_credit", "open_debit", "other")

DEFAULT_EXECUTION_STATUS = "draft"
DEFAULT_ORDER_INTENT = "open_credit"
DEFAULT_QUANTITY = 1


def is_valid_execution_status(status: str) -> bool:
    return status in EXECUTION_TICKET_STATUSES


def is_operator_patchable_status(status: str) -> bool:
    return status in OPERATOR_PATCHABLE_STATUSES


@dataclass(frozen=True)
class ExecutionTicket:
    """
    Persistent, auditable execution preparation record for a single trade candidate.

    An execution ticket represents the operator's intent to execute a specific
    trade structure.  It captures a frozen snapshot of the key trade parameters
    at creation time so the record remains meaningful even if a later scan
    re-evaluates the same ticker with different numbers.

    Lifecycle relationship:
      - lifecycle_state "execution_ready" is the intended precondition for
        ticket creation, but this is a UI convention, not enforced at the model
        layer.  The ticket and lifecycle record are separate objects with
        separate identifiers.

    Status progression (PU-15A.3, operator-managed):
      draft → ready

    Status progression (PU-15A.4, broker-managed — deferred):
      ready → submitted → accepted/rejected → filled → (implicit close)

    Broker submission is NOT implemented in this phase.
    """

    ticket_id: str
    owner_user_id: str
    trade_id: str
    source_scan_id: str | None

    # ── Frozen trade snapshot ──────────────────────────────────────────────
    ticker: str
    strategy_key: str
    strategy_label: str
    directional_bias: str | None
    expiration_date: str | None
    short_strike: float | None
    long_strike: float | None
    underlying_price_at_creation: float | None
    net_credit_estimate: float | None
    max_risk_estimate: float | None
    adjusted_score_at_creation: float | None

    # ── Execution parameters ───────────────────────────────────────────────
    quantity: int
    order_intent: str  # open_credit | open_debit | other
    execution_status: str  # draft | ready | submitted | …
    note: str | None

    # ── Audit ─────────────────────────────────────────────────────────────
    created_at: str
    updated_at: str
