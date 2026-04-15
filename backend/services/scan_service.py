"""First backend service seam for running scans.

Compatibility note:
The current Streamlit app can later replace its direct `run_scan_engine(...)`
call with `run_scan(ScanRequest(...))` and continue rendering the returned
payload after mapping from the canonical top-level sections it needs.
"""

from backend.contracts.scan_result import ScanRequest, build_scan_result
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

    return build_scan_result(raw_output, request)
