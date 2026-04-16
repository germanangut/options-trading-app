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
