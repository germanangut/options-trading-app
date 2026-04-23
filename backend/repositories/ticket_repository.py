from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from backend.contracts.ticket_models import ExecutionTicket


class TicketRepository(ABC):
    """Storage abstraction for user-owned execution preparation tickets."""

    @abstractmethod
    def create_ticket(self, ticket: ExecutionTicket) -> ExecutionTicket:
        """Persist a new execution ticket and return the stored record."""

    @abstractmethod
    def get_ticket(self, ticket_id: str, *, user_id: str) -> ExecutionTicket | None:
        """Load one execution ticket owned by the given user."""

    @abstractmethod
    def get_tickets_by_trade(
        self,
        trade_id: str,
        *,
        user_id: str,
    ) -> list[ExecutionTicket]:
        """Return all tickets for a specific trade, newest first."""

    @abstractmethod
    def list_tickets(
        self,
        *,
        user_id: str,
        execution_status: str | None = None,
        limit: int | None = None,
    ) -> list[ExecutionTicket]:
        """List all tickets for a user, ordered by updated_at desc."""

    @abstractmethod
    def update_ticket(
        self,
        ticket_id: str,
        *,
        user_id: str,
        quantity: int | None,
        note: str | None,
        clear_note: bool,
        execution_status: str | None,
        updated_at: str,
    ) -> ExecutionTicket | None:
        """
        Patch mutable fields on one ticket.  Returns None if not found.
        Pass clear_note=True to explicitly set note to NULL.
        """

    @abstractmethod
    def clear(self, *, user_id: str | None = None) -> None:
        """Remove tickets.  Intended for tests and local reset flows."""

    @abstractmethod
    def record_submission_result(
        self,
        ticket_id: str,
        *,
        user_id: str,
        execution_status: str,
        broker_order_id: str | None,
        broker_status_raw: str | None,
        broker_submitted_at: str | None,
        broker_updated_at: str | None,
        last_submission_payload: dict[str, Any] | None,
        last_submission_response: dict[str, Any] | None,
        submission_error_message: str | None,
        updated_at: str,
    ) -> ExecutionTicket | None:
        """Persist broker submission metadata and resulting execution status."""
