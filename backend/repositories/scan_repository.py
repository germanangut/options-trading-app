from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ScanRepository(ABC):
    """Storage abstraction for durable canonical scan retrieval.

    Canonical persisted scans are the authoritative backend source once they
    exist. Legacy JSONL history remains a compatibility fallback outside this
    contract. Future storage backends may extend the persisted model with
    ownership metadata, such as a user identifier, without changing the public
    repository methods.
    """

    @abstractmethod
    def save_scan(
        self,
        scan_result: dict[str, Any],
        *,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        """Persist a canonical scan result."""

    @abstractmethod
    def get_scan(
        self,
        scan_id: str,
        *,
        user_id: str | None = None,
    ) -> dict[str, Any] | None:
        """Load a scan result by its stable scan id."""

    @abstractmethod
    def get_latest_scan(self, *, user_id: str | None = None) -> dict[str, Any] | None:
        """Load the latest completed persisted scan result."""

    @abstractmethod
    def list_scans(
        self,
        *,
        limit: int | None = None,
        newest_first: bool = True,
        user_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """List persisted scan results with explicit deterministic ordering."""

    @abstractmethod
    def get_trade(
        self,
        scan_id: str,
        trade_id: str,
        *,
        user_id: str | None = None,
    ) -> dict[str, Any] | None:
        """Load a trade from a persisted scan result."""

    @abstractmethod
    def clear(self, *, user_id: str | None = None) -> None:
        """Remove all persisted scan records."""
