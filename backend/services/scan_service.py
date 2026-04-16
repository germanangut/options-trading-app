"""First backend service seam for running scans.

Compatibility note:
The current Streamlit app can later replace its direct `run_scan_engine(...)`
call with `run_scan(ScanRequest(...))` and continue rendering the returned
payload after mapping from the canonical top-level sections it needs.
"""

from typing import Any

from backend.contracts.scan_result import ScanRequest, build_scan_result
from backend.services.scan_store import (
    load_latest_scan_result,
    load_scan_result,
    save_scan_result,
)
from engine import run_scan_engine


def run_scan(request: ScanRequest) -> dict:
    """Run the existing scan engine and return the canonical ScanResult."""
    selected_strategy_keys = request.selected_strategy_keys or None

    raw_output = run_scan_engine(
        profile_name=request.profile,
        group_name=request.ticker_group,
        dte_min=request.dte_min,
        dte_max=request.dte_max,
        min_score=request.min_score,
        min_consistency=request.min_consistency,
        export_csv=False,
        selected_strategy_keys=selected_strategy_keys,
    )

    scan_result = build_scan_result(raw_output, request)
    return save_scan_result(scan_result)


def get_latest_scan() -> dict[str, Any] | None:
    return load_latest_scan_result()


def get_scan_by_id(scan_id: str) -> dict[str, Any] | None:
    return load_scan_result(scan_id)


def get_trade_by_id(scan_result: dict[str, Any], trade_id: str) -> dict[str, Any] | None:
    if not scan_result or not trade_id:
        return None

    for collection_name in ("qualified_trades", "alerts", "near_miss_trades"):
        for trade in scan_result.get(collection_name, []) or []:
            if trade.get("trade_id") == trade_id:
                return trade

    return None
