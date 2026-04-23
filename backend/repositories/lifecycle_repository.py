from __future__ import annotations

from abc import ABC, abstractmethod

from backend.contracts.lifecycle_models import TradeLifecycleRecord


class LifecycleRepository(ABC):
    """Storage abstraction for user-managed trade lifecycle state."""

    @abstractmethod
    def get_trade_lifecycle(
        self,
        trade_id: str,
        *,
        user_id: str,
    ) -> TradeLifecycleRecord | None:
        """Load a lifecycle record for a single user-owned trade id."""

    @abstractmethod
    def upsert_trade_lifecycle(
        self,
        *,
        trade_id: str,
        lifecycle_state: str,
        state_updated_at: str,
        note: str | None,
        tags: list[str],
        source_scan_id: str | None,
        created_at: str,
        updated_at: str,
        user_id: str,
    ) -> TradeLifecycleRecord:
        """Insert or update one user-owned lifecycle record by trade id."""

    @abstractmethod
    def list_trade_lifecycles(
        self,
        *,
        user_id: str,
        lifecycle_state: str | None = None,
        limit: int | None = None,
    ) -> list[TradeLifecycleRecord]:
        """List lifecycle records for one user."""

    @abstractmethod
    def clear(self, *, user_id: str | None = None) -> None:
        """Remove lifecycle records. Intended for tests and local reset flows."""
