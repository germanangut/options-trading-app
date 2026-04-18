from backend.contracts.scan_result import ScanRequest
from backend.services.scan_service import get_latest_scan, get_scan_by_id, run_scan
from backend.services.scan_store import clear_scan_store
import data_provider
from engine import run_scan_engine
from pathlib import Path
import shutil
import uuid


def _force_mock_mode(monkeypatch, workspace_tmp_dir):
    monkeypatch.setattr(data_provider, "ALPACA_API_KEY", None)
    monkeypatch.setattr(data_provider, "ALPACA_API_SECRET", None)
    monkeypatch.setenv("HISTORY_DIR", str(workspace_tmp_dir / "history"))
    monkeypatch.setenv("CACHE_DIR", str(workspace_tmp_dir / "cache"))


def test_run_scan_matches_current_engine_core_semantics(monkeypatch):
    workspace_tmp_dir = Path("tmp_test_scan_service") / str(uuid.uuid4())
    workspace_tmp_dir.mkdir(parents=True, exist_ok=True)
    _force_mock_mode(monkeypatch, workspace_tmp_dir)
    clear_scan_store()

    try:
        request = ScanRequest(
            profile="balanced",
            ticker_group="tech",
            selected_strategy_keys=["bull_put_spread", "bear_call_spread"],
            dte_min=20,
            dte_max=35,
            min_score=65,
            min_consistency=3,
        )

        raw_output = run_scan_engine(
            profile_name=request.profile,
            group_name=request.ticker_group,
            dte_min=request.dte_min,
            dte_max=request.dte_max,
            min_score=request.min_score,
            min_consistency=request.min_consistency,
            export_csv=False,
            selected_strategy_keys=request.selected_strategy_keys,
        )

        scan_result = run_scan(request)
        scan_id = scan_result["scan_metadata"]["scan_id"]

        assert scan_id.startswith("scan_")
        assert scan_result["summary"]["qualified_count"] == raw_output["summary"]["qualified_count"]
        assert scan_result["summary"]["near_miss_count"] == raw_output["summary"]["near_miss_count"]

        service_top = scan_result["summary"].get("top_overall")
        raw_top = raw_output["summary"].get("top_overall")
        if raw_top:
            assert service_top is not None
            assert service_top.get("ticker") == raw_top.get("ticker")
            assert service_top.get("strategy_type") == raw_top.get("strategy_type")
        else:
            assert service_top is None

        assert len(scan_result["qualified_trades"]) == len(raw_output["qualified"])
        assert len(scan_result["alerts"]) == len(raw_output["alerts"])
        assert scan_result["diagnostics"]["missing_tickers"] == raw_output["missing_tickers"]
        assert scan_result["diagnostics"]["provider_errors"] == raw_output["provider_errors"]
        assert "performance" in scan_result["diagnostics"]
        assert scan_result["diagnostics"]["performance"]["scan_duration_ms"] >= 0
        assert scan_result["diagnostics"]["performance"]["provider_duration_ms"] >= 0
        assert scan_result["diagnostics"]["performance"]["history_duration_ms"] >= 0

        portfolio_summary = scan_result["portfolio_summary"]
        assert portfolio_summary["exposure"] == raw_output["portfolio_exposure_summary"]
        assert portfolio_summary["position_sizing"] == raw_output["position_sizing_summary"]
        assert portfolio_summary["overlap"] == raw_output["exposure_overlap_summary"]
        assert portfolio_summary["decision"] == raw_output["portfolio_decision_summary"]

        assert "historical_intelligence_summary" in scan_result["history_context"]

        for trade in scan_result["qualified_trades"]:
            assert trade["trade_id"].startswith("trade_")

        latest_scan = get_latest_scan()
        stored_scan = get_scan_by_id(scan_id)

        assert latest_scan is not None
        assert stored_scan is not None
        assert latest_scan["scan_metadata"]["scan_id"] == scan_id
        assert stored_scan["scan_metadata"]["scan_id"] == scan_id
        assert stored_scan["summary"] == scan_result["summary"]
        assert stored_scan["daily_summary"] == scan_result["daily_summary"]
        assert stored_scan["diagnostics"]["performance"] == scan_result["diagnostics"]["performance"]

        if scan_result["qualified_trades"]:
            rerun_scan = run_scan(request)
            first_run_ids = {
                trade["trade_id"]
                for trade in scan_result["qualified_trades"]
            }
            rerun_ids = {
                trade["trade_id"]
                for trade in rerun_scan["qualified_trades"]
            }
            assert first_run_ids == rerun_ids
    finally:
        shutil.rmtree(workspace_tmp_dir, ignore_errors=True)
