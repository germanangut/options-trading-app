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
from backend.repositories.factory import get_auth_repository, get_lifecycle_repository


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


def test_lifecycle_api_default_upsert_and_list(monkeypatch):
    workspace_tmp_dir = Path("tmp_test_lifecycle_api") / str(uuid.uuid4())
    workspace_tmp_dir.mkdir(parents=True, exist_ok=True)
    _force_mock_mode(monkeypatch, workspace_tmp_dir)
    get_lifecycle_repository().clear()
    get_auth_repository().clear()

    try:
        client = TestClient(app)
        headers = _register_and_get_headers(client, f"lifecycle-{uuid.uuid4().hex}@example.com")

        default_response = client.get("/api/v1/lifecycle/trade_demo", headers=headers)
        assert default_response.status_code == 200
        default_body = default_response.json()
        assert default_body["trade_id"] == "trade_demo"
        assert default_body["lifecycle_state"] == "new"
        assert default_body["is_default"] is True

        upsert_response = client.patch(
            "/api/v1/lifecycle/trade_demo",
            headers=headers,
            json={
                "lifecycle_state": "watching",
                "note": "Keep tracking before execution.",
                "tags": ["tech", "swing"],
                "source_scan_id": "scan_demo",
            },
        )
        assert upsert_response.status_code == 200
        upserted = upsert_response.json()
        assert upserted["lifecycle_state"] == "watching"
        assert upserted["note"] == "Keep tracking before execution."
        assert upserted["tags"] == ["tech", "swing"]
        assert upserted["source_scan_id"] == "scan_demo"
        assert upserted["is_default"] is False

        single_response = client.get("/api/v1/lifecycle/trade_demo", headers=headers)
        assert single_response.status_code == 200
        assert single_response.json()["lifecycle_state"] == "watching"

        list_response = client.get("/api/v1/lifecycle", headers=headers)
        assert list_response.status_code == 200
        listed = list_response.json()["items"]
        assert len(listed) == 1
        assert listed[0]["trade_id"] == "trade_demo"


        invalid_transition_response = client.patch(
            "/api/v1/lifecycle/trade_demo",
            headers=headers,
            json={"lifecycle_state": "new"},
        )
        assert invalid_transition_response.status_code == 400
        error_payload = invalid_transition_response.json()
        message = (
            (error_payload.get("error") or {}).get("message")
            or error_payload.get("detail")
            or ""
        )
        assert "Invalid lifecycle transition" in message
    finally:
        shutil.rmtree(workspace_tmp_dir, ignore_errors=True)
