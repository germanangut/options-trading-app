from pathlib import Path

from backend.services.scan_store import clear_scan_store, save_scan_result
from history import get_historical_intelligence_summary, load_all_history_runs


def _build_persisted_scan(scan_id: str, timestamp: str, ticker: str) -> dict:
    trade = {
        "trade_id": f"trade_{ticker.lower()}",
        "ticker": ticker,
        "strategy_type": "bull put spread",
        "strategy_label": "Bull Put Spread",
        "adjusted_score": 72.5,
        "score": 70.0,
        "POP": 66.0,
        "ROR": 21.0,
        "label": "High Quality",
        "volatility_context": "balanced_premium",
        "stability_level": "new",
        "stability_count": 1,
        "status_reason": "Synthetic history test trade.",
        "decision_summary": "Synthetic history test trade.",
    }

    return {
        "scan_metadata": {
            "scan_id": scan_id,
            "generated_at": timestamp,
            "profile": "balanced",
            "ticker_group": "tech",
            "selected_strategy_keys": ["bull_put_spread"],
            "dte_range": {"dte_min": 20, "dte_max": 35},
            "scoring_weights": {"pop_weight": 0.6, "ror_weight": 0.4},
            "alert_thresholds": {"min_score": 65, "min_consistency": 3},
            "execution_time_seconds": 1.0,
            "provider": "alpaca-mock-fallback",
            "request": {},
        },
        "summary": {
            "qualified_count": 1,
            "near_miss_count": 0,
            "top_overall": dict(trade),
            "top_bull_put": dict(trade),
            "top_bear_call": None,
        },
        "qualified_trades": [dict(trade)],
        "alerts": [dict(trade)],
        "near_miss_trades": [],
        "ticker_diagnostics": [],
        "portfolio_summary": {},
        "history_context": {},
        "daily_summary": {},
        "diagnostics": {
            "missing_tickers": [],
            "provider_errors": [],
            "alerts_export_path": None,
            "top_overall_identity": None,
        },
    }


def test_history_reads_from_persisted_scan_records(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("HISTORY_DIR", str(tmp_path / "history"))
    monkeypatch.setenv(
        "SCAN_DATABASE_PATH",
        str(tmp_path / "history" / "scan_store.sqlite"),
    )
    clear_scan_store()

    save_scan_result(_build_persisted_scan("scan_history_1", "2026-04-16T08:00:00Z", "AAPL"))
    save_scan_result(_build_persisted_scan("scan_history_2", "2026-04-16T09:00:00Z", "MSFT"))

    runs = load_all_history_runs(include_fallback_dirs=False)
    assert len(runs) == 2
    assert [run["timestamp"] for run in runs] == [
        "2026-04-16T09:00:00Z",
        "2026-04-16T08:00:00Z",
    ]
    assert runs[0]["scan_id"] == "scan_history_2"
    assert runs[0].get("stored_at")

    intelligence = get_historical_intelligence_summary(limit=5)
    metadata = intelligence["metadata"]

    assert metadata["runs_analyzed"] == 2
    assert metadata["history_available"] is True
    assert metadata["latest_run_timestamp"] == "2026-04-16T09:00:00Z"