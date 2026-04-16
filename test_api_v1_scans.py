import shutil
import uuid
from pathlib import Path

import data_provider
import pytest


pytest.importorskip("fastapi")
pytest.importorskip("uvicorn")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from backend.api.main import app
from backend.services.scan_store import clear_scan_store


def _force_mock_mode(monkeypatch, workspace_tmp_dir):
    monkeypatch.setattr(data_provider, "ALPACA_API_KEY", None)
    monkeypatch.setattr(data_provider, "ALPACA_API_SECRET", None)
    monkeypatch.setenv("HISTORY_DIR", str(workspace_tmp_dir / "history"))
    monkeypatch.setenv("CACHE_DIR", str(workspace_tmp_dir / "cache"))


def test_v1_scan_endpoints_expose_stable_ids_and_screen_shapes(monkeypatch):
    workspace_tmp_dir = Path("tmp_test_api_v1_scans") / str(uuid.uuid4())
    workspace_tmp_dir.mkdir(parents=True, exist_ok=True)
    _force_mock_mode(monkeypatch, workspace_tmp_dir)
    clear_scan_store()

    try:
        client = TestClient(app)
        payload = {
            "profile": "balanced",
            "ticker_group": "tech",
            "selected_strategy_keys": ["bull_put_spread", "bear_call_spread"],
            "dte_min": 20,
            "dte_max": 35,
            "min_score": 65,
            "min_consistency": 3,
        }

        create_response = client.post("/api/v1/scans", json=payload)
        assert create_response.status_code == 200
        created_scan = create_response.json()

        scan_id = created_scan["scan_metadata"]["scan_id"]
        assert scan_id.startswith("scan_")

        latest_response = client.get("/api/v1/scans/latest")
        by_id_response = client.get(f"/api/v1/scans/{scan_id}")

        assert latest_response.status_code == 200
        assert by_id_response.status_code == 200
        assert latest_response.json()["scan_metadata"]["scan_id"] == scan_id
        assert by_id_response.json()["scan_metadata"]["scan_id"] == scan_id
        assert latest_response.json()["summary"] == by_id_response.json()["summary"]

        qualified_response = client.get(f"/api/v1/scans/{scan_id}/qualified-trades")
        assert qualified_response.status_code == 200
        qualified_rows = qualified_response.json()

        if qualified_rows:
            trade_row = qualified_rows[0]
            assert trade_row["trade_id"].startswith("trade_")

            trade_detail_response = client.get(
                f"/api/v1/scans/{scan_id}/trades/{trade_row['trade_id']}"
            )
            assert trade_detail_response.status_code == 200
            trade_detail = trade_detail_response.json()
            assert trade_detail["scan_id"] == scan_id
            assert trade_detail["trade"]["trade_id"] == trade_row["trade_id"]

        alerts_response = client.get(f"/api/v1/scans/{scan_id}/alerts")
        history_response = client.get(f"/api/v1/scans/{scan_id}/history")
        portfolio_response = client.get(f"/api/v1/scans/{scan_id}/portfolio")
        daily_summary_response = client.get(f"/api/v1/scans/{scan_id}/daily-summary")

        assert alerts_response.status_code == 200
        assert history_response.status_code == 200
        assert portfolio_response.status_code == 200
        assert daily_summary_response.status_code == 200

        history_body = history_response.json()
        portfolio_body = portfolio_response.json()
        daily_body = daily_summary_response.json()

        assert history_body["scan_id"] == scan_id
        assert "summary_cards" in history_body
        assert "recent_patterns" in history_body

        assert portfolio_body["scan_id"] == scan_id
        assert "summary_cards" in portfolio_body
        assert "positions" in portfolio_body

        assert daily_body["scan_id"] == scan_id
        assert "headline" in daily_body
        assert "alert_signals" in daily_body
    finally:
        shutil.rmtree(workspace_tmp_dir, ignore_errors=True)
