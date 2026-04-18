"""First backend service seam for running scans.

Compatibility note:
The current Streamlit app can later replace its direct `run_scan_engine(...)`
call with `run_scan(ScanRequest(...))` and continue rendering the returned
payload after mapping from the canonical top-level sections it needs.
"""

import logging
import time
from typing import Any

from backend.contracts.scan_result import ScanRequest, build_scan_result
from backend.observability.logging import get_logger, log_event
from backend.services.scan_store import (
    list_scan_results,
    load_latest_scan_result,
    load_scan_result,
    save_scan_result,
)
from engine import run_scan_engine
from history import get_historical_intelligence_summary


logger = get_logger(__name__)


def run_scan(
    request: ScanRequest,
    *,
    user_id: str | None = None,
) -> dict:
    """Run the existing scan engine and return the canonical ScanResult."""
    selected_strategy_keys = request.selected_strategy_keys or None
    log_event(
        logger,
        "scan_started",
        user_id=user_id,
        profile=request.profile,
        ticker_group=request.ticker_group,
        selected_strategy_count=len(selected_strategy_keys or []),
    )

    try:
        started_at = time.perf_counter()
        raw_output = run_scan_engine(
            profile_name=request.profile,
            group_name=request.ticker_group,
            dte_min=request.dte_min,
            dte_max=request.dte_max,
            min_score=request.min_score,
            min_consistency=request.min_consistency,
            export_csv=False,
            selected_strategy_keys=selected_strategy_keys,
            persist_history=False,
        )

        scan_result = build_scan_result(raw_output, request)
        history_started_at = time.perf_counter()
        scan_result["history_context"] = {
            "historical_intelligence_summary": get_historical_intelligence_summary(
                limit=5,
                user_id=user_id,
            ),
        }
        history_duration_ms = round((time.perf_counter() - history_started_at) * 1000, 2)
        diagnostics = scan_result.setdefault("diagnostics", {})
        performance = diagnostics.setdefault("performance", {})
        performance["history_duration_ms"] = history_duration_ms

        persistence_started_at = time.perf_counter()
        persisted = save_scan_result(scan_result, user_id=user_id)
        persistence_duration_ms = round(
            (time.perf_counter() - persistence_started_at) * 1000, 2
        )
        log_event(
            logger,
            "scan_completed",
            user_id=user_id,
            scan_id=((persisted.get("scan_metadata") or {}).get("scan_id")),
            qualified_count=((persisted.get("summary") or {}).get("qualified_count")),
            alerts_count=len(persisted.get("alerts", []) or []),
            provider=((persisted.get("diagnostics") or {}).get("provider") or (persisted.get("scan_metadata") or {}).get("provider")),
            partial_result=((persisted.get("diagnostics") or {}).get("partial_result", False)),
            provider_duration_ms=((persisted.get("diagnostics") or {}).get("performance", {}) or {}).get("provider_duration_ms"),
            persistence_duration_ms=persistence_duration_ms,
            history_duration_ms=history_duration_ms,
            scan_duration_ms=round((time.perf_counter() - started_at) * 1000, 2),
        )
        return persisted
    except Exception as exc:
        log_event(
            logger,
            "scan_failed",
            level=logging.ERROR,
            user_id=user_id,
            error_type=type(exc).__name__,
        )
        raise


def get_latest_scan(*, user_id: str | None = None) -> dict[str, Any] | None:
    return load_latest_scan_result(user_id=user_id)


def get_scan_by_id(scan_id: str, *, user_id: str | None = None) -> dict[str, Any] | None:
    return load_scan_result(scan_id, user_id=user_id)


def get_trade_by_id(scan_result: dict[str, Any], trade_id: str) -> dict[str, Any] | None:
    if not scan_result or not trade_id:
        log_event(
            logger,
            "persistence_read",
            level=logging.WARNING,
            operation="trade_lookup",
            found=False,
        )
        return None

    for collection_name in ("qualified_trades", "alerts", "near_miss_trades"):
        for trade in scan_result.get(collection_name, []) or []:
            if trade.get("trade_id") == trade_id:
                log_event(
                    logger,
                    "persistence_read",
                    operation="trade_lookup",
                    scan_id=((scan_result.get("scan_metadata") or {}).get("scan_id")),
                    trade_id=trade_id,
                    found=True,
                )
                return trade

    log_event(
        logger,
        "persistence_read",
        level=logging.WARNING,
        operation="trade_lookup",
        scan_id=((scan_result.get("scan_metadata") or {}).get("scan_id")),
        trade_id=trade_id,
        found=False,
    )
    return None


def list_scans(
    limit: int | None = None,
    *,
    user_id: str | None = None,
) -> list[dict[str, Any]]:
    return list_scan_results(limit=limit, newest_first=True, user_id=user_id)
