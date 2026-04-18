import data_provider
import pytest
from pathlib import Path
import shutil
import uuid


fastapi = pytest.importorskip("fastapi")
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


def _scan_payload() -> dict[str, object]:
    return {
        "profile": "balanced",
        "ticker_group": "tech",
        "selected_strategy_keys": ["bull_put_spread", "bear_call_spread"],
        "dte_min": 20,
        "dte_max": 35,
        "min_score": 65,
        "min_consistency": 3,
    }


def test_post_scan_and_get_latest(monkeypatch):
    workspace_tmp_dir = Path("tmp_test_api_scans") / str(uuid.uuid4())
    workspace_tmp_dir.mkdir(parents=True, exist_ok=True)
    _force_mock_mode(monkeypatch, workspace_tmp_dir)
    clear_scan_store()
    get_auth_repository().clear()

    try:
        client = TestClient(app)
        headers = _register_and_get_headers(client, f"alice-{uuid.uuid4().hex}@example.com")
        payload = {
            "profile": "balanced",
            "ticker_group": "tech",
            "selected_strategy_keys": ["bull_put_spread", "bear_call_spread"],
            "dte_min": 20,
            "dte_max": 35,
            "min_score": 65,
            "min_consistency": 3,
        }

        post_response = client.post("/scans", json=payload, headers=headers)
        assert post_response.status_code == 200

        body = post_response.json()
        assert set(body.keys()) == {
            "scan_metadata",
            "summary",
            "qualified_trades",
            "alerts",
            "near_miss_trades",
            "ticker_diagnostics",
            "portfolio_summary",
            "history_context",
            "daily_summary",
            "diagnostics",
        }
        assert body["scan_metadata"]["scan_id"].startswith("scan_")

        latest_response = client.get("/scans/latest", headers=headers)
        assert latest_response.status_code == 200
        latest_body = latest_response.json()

        assert latest_body["summary"] == body["summary"]
        assert latest_body["diagnostics"] == body["diagnostics"]
    finally:
        shutil.rmtree(workspace_tmp_dir, ignore_errors=True)


def test_get_latest_returns_404_before_first_scan(monkeypatch):
    workspace_tmp_dir = Path("tmp_test_api_scans") / str(uuid.uuid4())
    workspace_tmp_dir.mkdir(parents=True, exist_ok=True)
    _force_mock_mode(monkeypatch, workspace_tmp_dir)
    clear_scan_store()
    get_auth_repository().clear()

    try:
        client = TestClient(app)
        headers = _register_and_get_headers(client, f"empty-{uuid.uuid4().hex}@example.com")

        response = client.get("/scans/latest", headers=headers)

        assert response.status_code == 404
        assert response.json()["error"]["message"] == "No scan result is available yet."
    finally:
        shutil.rmtree(workspace_tmp_dir, ignore_errors=True)


def test_scan_lifecycle_routes_and_refresh_behavior(monkeypatch):
    workspace_tmp_dir = Path("tmp_test_api_scans") / str(uuid.uuid4())
    workspace_tmp_dir.mkdir(parents=True, exist_ok=True)
    _force_mock_mode(monkeypatch, workspace_tmp_dir)
    clear_scan_store()
    get_auth_repository().clear()

    try:
        client = TestClient(app)
        headers = _register_and_get_headers(client, f"flow-{uuid.uuid4().hex}@example.com")
        payload = _scan_payload()

        first_scan = client.post("/scans", json=payload, headers=headers)
        assert first_scan.status_code == 200
        first_body = first_scan.json()
        first_scan_id = first_body["scan_metadata"]["scan_id"]

        latest_first = client.get("/scans/latest", headers=headers)
        assert latest_first.status_code == 200
        assert latest_first.json()["scan_metadata"]["scan_id"] == first_scan_id

        by_id = client.get(f"/api/v1/scans/{first_scan_id}", headers=headers)
        overview = client.get(f"/api/v1/scans/{first_scan_id}/overview", headers=headers)
        qualified = client.get(f"/api/v1/scans/{first_scan_id}/qualified-trades", headers=headers)
        history = client.get(f"/api/v1/scans/{first_scan_id}/history", headers=headers)
        alerts = client.get(f"/api/v1/scans/{first_scan_id}/alerts", headers=headers)
        portfolio = client.get(f"/api/v1/scans/{first_scan_id}/portfolio", headers=headers)
        daily_summary = client.get(f"/api/v1/scans/{first_scan_id}/daily-summary", headers=headers)

        assert by_id.status_code == 200
        assert overview.status_code == 200
        assert qualified.status_code == 200
        assert history.status_code == 200
        assert alerts.status_code == 200
        assert portfolio.status_code == 200
        assert daily_summary.status_code == 200
        assert by_id.json()["diagnostics"]["performance"]["history_duration_ms"] >= 0
        assert overview.json()["scan_id"] == first_scan_id
        assert history.json()["scan_id"] == first_scan_id
        assert isinstance(alerts.json(), list)
        assert isinstance(qualified.json(), list)

        trade_id = None
        if first_body["qualified_trades"]:
            trade_id = first_body["qualified_trades"][0]["trade_id"]
        elif first_body["alerts"]:
            trade_id = first_body["alerts"][0]["trade_id"]

        assert trade_id is not None
        trade_detail = client.get(
            f"/api/v1/scans/{first_scan_id}/trades/{trade_id}",
            headers=headers,
        )

        assert trade_detail.status_code == 200
        assert trade_detail.json()["scan_id"] == first_scan_id
        assert trade_detail.json()["trade"]["trade_id"] == trade_id

        second_scan = client.post("/scans", json=payload, headers=headers)
        third_scan = client.post("/scans", json=payload, headers=headers)

        assert second_scan.status_code == 200
        assert third_scan.status_code == 200
        assert second_scan.json()["scan_metadata"]["scan_id"] != first_scan_id
        assert third_scan.json()["scan_metadata"]["scan_id"] not in {
            first_scan_id,
            second_scan.json()["scan_metadata"]["scan_id"],
        }

        latest_third = client.get("/scans/latest", headers=headers)
        refreshed_history = client.get(
            f"/api/v1/scans/{third_scan.json()['scan_metadata']['scan_id']}/history",
            headers=headers,
        )

        assert latest_third.status_code == 200
        assert latest_third.json()["scan_metadata"]["scan_id"] == third_scan.json()["scan_metadata"]["scan_id"]
        assert latest_third.json()["diagnostics"]["top_overall_identity"] == third_scan.json()["diagnostics"]["top_overall_identity"]
        assert refreshed_history.status_code == 200
        assert refreshed_history.json()["summary_cards"][0]["value"] >= 3
    finally:
        shutil.rmtree(workspace_tmp_dir, ignore_errors=True)


def test_scan_routes_accept_cors_preflight():
    client = TestClient(app)

    response = client.options(
        "/scans/latest",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"


def test_scan_routes_accept_vercel_preflight_origin():
    client = TestClient(app)

    response = client.options(
        "/auth/login",
        headers={
            "Origin": "https://options-trading-app-nu.vercel.app",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert (
        response.headers["access-control-allow-origin"]
        == "https://options-trading-app-nu.vercel.app"
    )
