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
from backend.repositories.factory import get_auth_repository
from backend.services.scan_store import clear_scan_store


def _force_mock_mode(monkeypatch, workspace_tmp_dir):
    monkeypatch.setattr(data_provider, "ALPACA_API_KEY", None)
    monkeypatch.setattr(data_provider, "ALPACA_API_SECRET", None)
    monkeypatch.setenv("HISTORY_DIR", str(workspace_tmp_dir / "history"))
    monkeypatch.setenv("CACHE_DIR", str(workspace_tmp_dir / "cache"))
    monkeypatch.setenv(
        "SCAN_DATABASE_PATH",
        str(workspace_tmp_dir / "history" / "scan_store.sqlite"),
    )


def _register_and_get_headers(client: TestClient, email: str) -> dict[str, str]:
    response = client.post(
        "/auth/register",
        json={"email": email, "password": "Password123!"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_v1_scan_endpoints_expose_stable_ids_and_screen_shapes(monkeypatch):
    workspace_tmp_dir = Path("tmp_test_api_v1_scans") / str(uuid.uuid4())
    workspace_tmp_dir.mkdir(parents=True, exist_ok=True)
    _force_mock_mode(monkeypatch, workspace_tmp_dir)
    clear_scan_store()
    get_auth_repository().clear()

    try:
        client = TestClient(app)
        headers = _register_and_get_headers(client, f"bob-{uuid.uuid4().hex}@example.com")
        payload = {
            "profile": "balanced",
            "ticker_group": "tech",
            "selected_strategy_keys": ["bull_put_spread", "bear_call_spread"],
            "dte_min": 20,
            "dte_max": 35,
            "min_score": 65,
            "min_consistency": 3,
        }

        create_response = client.post("/api/v1/scans", json=payload, headers=headers)
        assert create_response.status_code == 200
        created_scan = create_response.json()

        scan_id = created_scan["scan_metadata"]["scan_id"]
        assert scan_id.startswith("scan_")

        latest_response = client.get("/api/v1/scans/latest", headers=headers)
        by_id_response = client.get(f"/api/v1/scans/{scan_id}", headers=headers)

        assert latest_response.status_code == 200
        assert by_id_response.status_code == 200
        assert latest_response.json()["scan_metadata"]["scan_id"] == scan_id
        assert by_id_response.json()["scan_metadata"]["scan_id"] == scan_id
        assert latest_response.json()["summary"] == by_id_response.json()["summary"]

        qualified_response = client.get(
            f"/api/v1/scans/{scan_id}/qualified-trades",
            headers=headers,
        )
        assert qualified_response.status_code == 200
        qualified_rows = qualified_response.json()

        if qualified_rows:
            trade_row = qualified_rows[0]
            assert trade_row["trade_id"].startswith("trade_")

            trade_detail_response = client.get(
                f"/api/v1/scans/{scan_id}/trades/{trade_row['trade_id']}",
                headers=headers,
            )
            assert trade_detail_response.status_code == 200
            trade_detail = trade_detail_response.json()
            assert trade_detail["scan_id"] == scan_id
            assert trade_detail["trade"]["trade_id"] == trade_row["trade_id"]

        alerts_response = client.get(f"/api/v1/scans/{scan_id}/alerts", headers=headers)
        history_response = client.get(f"/api/v1/scans/{scan_id}/history", headers=headers)
        portfolio_response = client.get(f"/api/v1/scans/{scan_id}/portfolio", headers=headers)
        daily_summary_response = client.get(
            f"/api/v1/scans/{scan_id}/daily-summary",
            headers=headers,
        )

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

