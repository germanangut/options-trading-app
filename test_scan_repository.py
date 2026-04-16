from pathlib import Path

import sqlite3

from backend.repositories.sqlite_scan_repository import SQLiteScanRepository


def _build_scan_result(scan_id: str, generated_at: str, trade_id: str, ticker: str) -> dict:
    trade = {
        "trade_id": trade_id,
        "ticker": ticker,
        "strategy_type": "bull put spread",
        "strategy_label": "Bull Put Spread",
        "expiration_date": "2026-05-15",
        "short_strike": 500,
        "long_strike": 495,
        "POP": 68.4,
        "ROR": 21.1,
        "score": 70.0,
        "adjusted_score": 73.2,
        "label": "High Quality",
        "decision_summary": "Synthetic persisted trade for repository tests.",
    }

    return {
        "scan_metadata": {
            "scan_id": scan_id,
            "generated_at": generated_at,
            "profile": "balanced",
            "ticker_group": "tech",
            "selected_strategy_keys": ["bull_put_spread"],
            "dte_range": {"dte_min": 20, "dte_max": 35},
            "scoring_weights": {"pop_weight": 0.6, "ror_weight": 0.4},
            "alert_thresholds": {"min_score": 65, "min_consistency": 3},
            "execution_time_seconds": 1.23,
            "provider": "alpaca-mock-fallback",
            "request": {
                "profile": "balanced",
                "ticker_group": "tech",
                "selected_strategy_keys": ["bull_put_spread"],
                "dte_min": 20,
                "dte_max": 35,
                "min_score": 65,
                "min_pop": None,
                "min_ror": None,
                "min_consistency": 3,
                "alerts_only": False,
                "use_mock_data": True,
            },
        },
        "summary": {
            "qualified_count": 1,
            "near_miss_count": 0,
            "top_overall": dict(trade),
            "top_bull_put": dict(trade),
            "top_bear_call": None,
        },
        "qualified_trades": [dict(trade)],
        "alerts": [],
        "near_miss_trades": [],
        "ticker_diagnostics": [],
        "portfolio_summary": {},
        "history_context": {
            "historical_intelligence_summary": {
                "metadata": {
                    "runs_analyzed": 1,
                    "signals_analyzed": 1,
                    "history_available": True,
                    "signal_history_available": True,
                    "latest_run_timestamp": generated_at,
                },
                "signal_quality_summary": {},
                "feature_summary": {},
            }
        },
        "daily_summary": {
            "scan_id": scan_id,
            "profile": "balanced",
            "ticker_group": "tech",
            "qualified_count": 1,
            "near_miss_count": 0,
            "alerts_count": 0,
            "top_overall": dict(trade),
            "stable_alert_count": 0,
            "emerging_alert_count": 0,
            "new_alert_count": 0,
            "most_stable_alert": None,
        },
        "diagnostics": {
            "missing_tickers": [],
            "provider_errors": [],
            "alerts_export_path": None,
            "top_overall_identity": {
                "ticker": ticker,
                "strategy_type": "bull put spread",
                "expiration_date": "2026-05-15",
                "short_strike": 500,
                "long_strike": 495,
            },
        },
    }


def test_sqlite_repository_save_and_lookup(tmp_path: Path):
    repository = SQLiteScanRepository(tmp_path / "scan_store.sqlite")
    scan_result = _build_scan_result(
        scan_id="scan_001",
        generated_at="2026-04-16T12:00:00Z",
        trade_id="trade_alpha",
        ticker="AAPL",
    )

    repository.save_scan(scan_result)

    loaded = repository.get_scan("scan_001")
    assert loaded is not None
    assert loaded["scan_metadata"]["scan_id"] == "scan_001"
    assert loaded["qualified_trades"][0]["trade_id"] == "trade_alpha"
    assert loaded["storage_metadata"]["schema_version"] == 1
    assert loaded["storage_metadata"]["storage_backend"] == "sqlite"
    assert loaded["storage_metadata"].get("stored_at")


def test_sqlite_repository_latest_list_trade_and_restart_behavior(tmp_path: Path):
    database_path = tmp_path / "scan_store.sqlite"
    repository = SQLiteScanRepository(database_path)

    older_scan = _build_scan_result(
        scan_id="scan_older",
        generated_at="2026-04-16T09:00:00Z",
        trade_id="trade_older",
        ticker="MSFT",
    )
    latest_scan = _build_scan_result(
        scan_id="scan_latest",
        generated_at="2026-04-16T10:00:00Z",
        trade_id="trade_latest",
        ticker="NVDA",
    )

    repository.save_scan(older_scan)
    repository.save_scan(latest_scan)

    listed_scans = repository.list_scans()
    assert [scan["scan_metadata"]["scan_id"] for scan in listed_scans] == [
        "scan_latest",
        "scan_older",
    ]

    latest_loaded = repository.get_latest_scan()
    assert latest_loaded is not None
    assert latest_loaded["scan_metadata"]["scan_id"] == "scan_latest"

    trade = repository.get_trade("scan_latest", "trade_latest")
    assert trade is not None
    assert trade["ticker"] == "NVDA"

    restarted_repository = SQLiteScanRepository(database_path)
    restarted_latest = restarted_repository.get_latest_scan()
    assert restarted_latest is not None
    assert restarted_latest["scan_metadata"]["scan_id"] == "scan_latest"


def test_sqlite_repository_skips_unreadable_rows_when_listing_and_loading_latest(tmp_path: Path):
    database_path = tmp_path / "scan_store.sqlite"
    repository = SQLiteScanRepository(database_path)

    valid_scan = _build_scan_result(
        scan_id="scan_valid",
        generated_at="2026-04-16T09:00:00Z",
        trade_id="trade_valid",
        ticker="MSFT",
    )
    repository.save_scan(valid_scan)

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            INSERT INTO scans (
                scan_id,
                generated_at,
                stored_at,
                schema_version,
                storage_backend,
                owner_user_id,
                profile,
                ticker_group,
                scan_result_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "scan_broken",
                "2026-04-16T11:00:00Z",
                "2026-04-16T11:00:00Z",
                1,
                "sqlite",
                None,
                "balanced",
                "tech",
                "{not-json",
            ),
        )

    listed_scans = repository.list_scans()
    assert [scan["scan_metadata"]["scan_id"] for scan in listed_scans] == [
        "scan_valid",
    ]

    latest_loaded = repository.get_latest_scan()
    assert latest_loaded is not None
    assert latest_loaded["scan_metadata"]["scan_id"] == "scan_valid"


def test_sqlite_repository_normalizes_missing_sections_in_persisted_payload(tmp_path: Path):
    repository = SQLiteScanRepository(tmp_path / "scan_store.sqlite")
    repository.save_scan(
        {
            "scan_metadata": {
                "scan_id": "scan_minimal",
                "generated_at": "2026-04-16T12:00:00Z",
            }
        }
    )

    loaded = repository.get_scan("scan_minimal")
    assert loaded is not None
    assert loaded["summary"] == {}
    assert loaded["qualified_trades"] == []
    assert loaded["alerts"] == []
    assert loaded["near_miss_trades"] == []
    assert loaded["portfolio_summary"] == {}
    assert loaded["history_context"] == {}
    assert loaded["storage_metadata"]["schema_version"] == 1
    assert repository.get_trade("scan_minimal", "missing") is None
