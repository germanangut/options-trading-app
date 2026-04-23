from __future__ import annotations

from dataclasses import dataclass


TRADE_LIFECYCLE_STATES: tuple[str, ...] = (
    "new",
    "saved",
    "watching",
    "execution_ready",
    "paper_submitted",
    "paper_filled",
    "paper_closed",
    "dismissed",
)

ACTIVE_LIFECYCLE_STATES: tuple[str, ...] = (
    "new",
    "saved",
    "watching",
    "execution_ready",
    "dismissed",
)

DEFAULT_LIFECYCLE_STATE = "new"

VALID_LIFECYCLE_TRANSITIONS: dict[str, set[str]] = {
    "new": {"new", "saved", "watching", "execution_ready", "dismissed"},
    "saved": {"saved", "watching", "execution_ready", "dismissed"},
    "watching": {"watching", "saved", "execution_ready", "dismissed"},
    "execution_ready": {
        "execution_ready",
        "watching",
        "saved",
        "dismissed",
        "paper_submitted",
    },
    "paper_submitted": {
        "paper_submitted",
        "paper_filled",
        "paper_closed",
        "dismissed",
    },
    "paper_filled": {"paper_filled", "paper_closed", "dismissed"},
    "paper_closed": {"paper_closed"},
    "dismissed": {"dismissed", "saved", "watching", "execution_ready"},
}


def is_valid_lifecycle_state(state: str) -> bool:
    return state in TRADE_LIFECYCLE_STATES


@dataclass(frozen=True)
class TradeLifecycleRecord:
    owner_user_id: str
    trade_id: str
    lifecycle_state: str
    state_updated_at: str
    note: str | None
    tags: list[str]
    source_scan_id: str | None
    created_at: str
    updated_at: str
