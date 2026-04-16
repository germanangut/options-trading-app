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


def _force_mock_mode(monkeypatch, workspace_tmp_dir: Path):
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


def test_unauthenticated_requests_are_rejected(monkeypatch):
    workspace_tmp_dir = Path("tmp_test_auth_api") / str(uuid.uuid4())
    workspace_tmp_dir.mkdir(parents=True, exist_ok=True)
    _force_mock_mode(monkeypatch, workspace_tmp_dir)
    clear_scan_store()
    get_auth_repository().clear()

    try:
        client = TestClient(app)
        assert client.get("/scans/latest").status_code == 401
        assert client.post("/scans", json=_scan_payload()).status_code == 401
        assert client.get("/api/v1/scans/scan_missing").status_code == 401
    finally:
        shutil.rmtree(workspace_tmp_dir, ignore_errors=True)


def test_auth_register_login_logout_and_current_user(monkeypatch):
    workspace_tmp_dir = Path("tmp_test_auth_api") / str(uuid.uuid4())
    workspace_tmp_dir.mkdir(parents=True, exist_ok=True)
    _force_mock_mode(monkeypatch, workspace_tmp_dir)
    clear_scan_store()
    get_auth_repository().clear()

    try:
        client = TestClient(app)
        email = f"user-{uuid.uuid4().hex}@example.com"

        register_response = client.post(
            "/auth/register",
            json={"email": email, "password": "Password123!"},
        )
        assert register_response.status_code == 200
        register_body = register_response.json()
        token = register_body["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        me_response = client.get("/auth/me", headers=headers)
        assert me_response.status_code == 200
        assert me_response.json()["email"] == email

        logout_response = client.post("/auth/logout", headers=headers)
        assert logout_response.status_code == 200
        assert logout_response.json()["success"] is True

        assert client.get("/auth/me", headers=headers).status_code == 401

        login_response = client.post(
            "/auth/login",
            json={"email": email, "password": "Password123!"},
        )
        assert login_response.status_code == 200
        assert login_response.json()["user"]["email"] == email
    finally:
        shutil.rmtree(workspace_tmp_dir, ignore_errors=True)


def test_user_scoped_latest_scan_and_history_are_isolated(monkeypatch):
    workspace_tmp_dir = Path("tmp_test_auth_api") / str(uuid.uuid4())
    workspace_tmp_dir.mkdir(parents=True, exist_ok=True)
    _force_mock_mode(monkeypatch, workspace_tmp_dir)
    clear_scan_store()
    get_auth_repository().clear()

    try:
        client = TestClient(app)
        alice_headers = _register_and_get_headers(client, f"alice-{uuid.uuid4().hex}@example.com")
        bob_headers = _register_and_get_headers(client, f"bob-{uuid.uuid4().hex}@example.com")

        alice_first = client.post("/scans", json=_scan_payload(), headers=alice_headers)
        alice_second = client.post("/scans", json=_scan_payload(), headers=alice_headers)
        bob_scan = client.post("/scans", json=_scan_payload(), headers=bob_headers)

        assert alice_first.status_code == 200
        assert alice_second.status_code == 200
        assert bob_scan.status_code == 200

        alice_latest = client.get("/scans/latest", headers=alice_headers)
        bob_latest = client.get("/scans/latest", headers=bob_headers)

        assert alice_latest.status_code == 200
        assert bob_latest.status_code == 200
        assert alice_latest.json()["scan_metadata"]["scan_id"] == alice_second.json()["scan_metadata"]["scan_id"]
        assert bob_latest.json()["scan_metadata"]["scan_id"] == bob_scan.json()["scan_metadata"]["scan_id"]

        alice_history = client.get(
            f"/api/v1/scans/{alice_second.json()['scan_metadata']['scan_id']}/history",
            headers=alice_headers,
        )
        bob_history = client.get(
            f"/api/v1/scans/{bob_scan.json()['scan_metadata']['scan_id']}/history",
            headers=bob_headers,
        )

        assert alice_history.status_code == 200
        assert bob_history.status_code == 200
        assert alice_history.json()["summary_cards"][0]["value"] == 2
        assert bob_history.json()["summary_cards"][0]["value"] == 1
    finally:
        shutil.rmtree(workspace_tmp_dir, ignore_errors=True)


def test_trade_detail_enforces_user_ownership(monkeypatch):
    workspace_tmp_dir = Path("tmp_test_auth_api") / str(uuid.uuid4())
    workspace_tmp_dir.mkdir(parents=True, exist_ok=True)
    _force_mock_mode(monkeypatch, workspace_tmp_dir)
    clear_scan_store()
    get_auth_repository().clear()

    try:
        client = TestClient(app)
        alice_headers = _register_and_get_headers(client, f"alice-{uuid.uuid4().hex}@example.com")
        bob_headers = _register_and_get_headers(client, f"bob-{uuid.uuid4().hex}@example.com")

        alice_scan = client.post("/api/v1/scans", json=_scan_payload(), headers=alice_headers)
        assert alice_scan.status_code == 200
        alice_body = alice_scan.json()

        trade_id = None
        if alice_body["qualified_trades"]:
            trade_id = alice_body["qualified_trades"][0]["trade_id"]
        elif alice_body["alerts"]:
            trade_id = alice_body["alerts"][0]["trade_id"]

        assert trade_id is not None

        alice_detail = client.get(
            f"/api/v1/scans/{alice_body['scan_metadata']['scan_id']}/trades/{trade_id}",
            headers=alice_headers,
        )
        bob_detail = client.get(
            f"/api/v1/scans/{alice_body['scan_metadata']['scan_id']}/trades/{trade_id}",
            headers=bob_headers,
        )

        assert alice_detail.status_code == 200
        assert bob_detail.status_code == 404
    finally:
        shutil.rmtree(workspace_tmp_dir, ignore_errors=True)