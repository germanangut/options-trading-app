import logging
from pathlib import Path
import shutil
import sqlite3
import uuid

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
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("LOG_LEVEL", "INFO")
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


def test_health_endpoint_returns_request_id_header(monkeypatch):
    workspace_tmp_dir = Path("tmp_test_observability_api") / str(uuid.uuid4())
    workspace_tmp_dir.mkdir(parents=True, exist_ok=True)
    _force_mock_mode(monkeypatch, workspace_tmp_dir)

    try:
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
        assert response.headers["x-request-id"].startswith("req_")
    finally:
        shutil.rmtree(workspace_tmp_dir, ignore_errors=True)


def test_ready_endpoint_reports_dependency_status(monkeypatch):
    workspace_tmp_dir = Path("tmp_test_observability_api") / str(uuid.uuid4())
    workspace_tmp_dir.mkdir(parents=True, exist_ok=True)
    _force_mock_mode(monkeypatch, workspace_tmp_dir)
    clear_scan_store()
    get_auth_repository().clear()

    try:
        client = TestClient(app)
        response = client.get("/ready")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ready"
        assert body["checks"]["persistence"]["status"] == "ok"
        assert body["checks"]["auth"]["status"] == "ok"
        assert body["checks"]["provider"]["mode"] == "mock"
    finally:
        shutil.rmtree(workspace_tmp_dir, ignore_errors=True)


def test_ops_cors_endpoint_reports_effective_configuration(monkeypatch):
    workspace_tmp_dir = Path("tmp_test_observability_api") / str(uuid.uuid4())
    workspace_tmp_dir.mkdir(parents=True, exist_ok=True)
    _force_mock_mode(monkeypatch, workspace_tmp_dir)
    monkeypatch.delenv("CORS_ALLOW_ORIGINS", raising=False)
    monkeypatch.delenv("CORS_ALLOW_ORIGIN_REGEX", raising=False)

    try:
        client = TestClient(app)
        response = client.get("/ops/cors")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert "http://127.0.0.1:5173" in body["cors"]["allow_origins"]
        assert body["cors"]["allow_origin_regex"] == (
            r"^https://options-trading-app(?:-[a-z0-9-]+)?\.vercel\.app$"
        )
        assert body["cors"]["source"] == {
            "origins": "default",
            "origin_regex": "default",
        }
    finally:
        shutil.rmtree(workspace_tmp_dir, ignore_errors=True)


def test_authenticated_scan_request_echoes_supplied_request_id(monkeypatch):
    workspace_tmp_dir = Path("tmp_test_observability_api") / str(uuid.uuid4())
    workspace_tmp_dir.mkdir(parents=True, exist_ok=True)
    _force_mock_mode(monkeypatch, workspace_tmp_dir)
    clear_scan_store()
    get_auth_repository().clear()

    try:
        client = TestClient(app)
        headers = _register_and_get_headers(client, f"request-id-{uuid.uuid4().hex}@example.com")
        request_id = f"req-test-{uuid.uuid4().hex}"
        response = client.post(
            "/scans",
            json={
                "profile": "balanced",
                "ticker_group": "tech",
                "selected_strategy_keys": ["bull_put_spread", "bear_call_spread"],
                "dte_min": 20,
                "dte_max": 35,
                "min_score": 65,
                "min_consistency": 3,
            },
            headers={**headers, "X-Request-ID": request_id},
        )

        assert response.status_code == 200
        assert response.headers["x-request-id"] == request_id
        assert response.json()["scan_metadata"]["scan_id"].startswith("scan_")
    finally:
        shutil.rmtree(workspace_tmp_dir, ignore_errors=True)


def test_unauthorized_responses_use_standard_error_envelope(monkeypatch):
    workspace_tmp_dir = Path("tmp_test_observability_api") / str(uuid.uuid4())
    workspace_tmp_dir.mkdir(parents=True, exist_ok=True)
    _force_mock_mode(monkeypatch, workspace_tmp_dir)

    try:
        client = TestClient(app)
        response = client.get("/scans/latest")
        assert response.status_code == 401
        body = response.json()
        assert body["error"]["code"] == "unauthorized"
        assert body["error"]["message"] == "Authentication required."
        assert body["error"]["request_id"].startswith("req_")
        assert response.headers["x-request-id"] == body["error"]["request_id"]
    finally:
        shutil.rmtree(workspace_tmp_dir, ignore_errors=True)


def test_missing_scan_uses_safe_not_found_envelope(monkeypatch):
    workspace_tmp_dir = Path("tmp_test_observability_api") / str(uuid.uuid4())
    workspace_tmp_dir.mkdir(parents=True, exist_ok=True)
    _force_mock_mode(monkeypatch, workspace_tmp_dir)
    clear_scan_store()
    get_auth_repository().clear()

    try:
        client = TestClient(app)
        headers = _register_and_get_headers(client, f"missing-{uuid.uuid4().hex}@example.com")
        response = client.get("/api/v1/scans/scan_missing", headers=headers)
        assert response.status_code == 404
        body = response.json()
        assert body["error"]["code"] == "not_found"
        assert body["error"]["request_id"].startswith("req_")
    finally:
        shutil.rmtree(workspace_tmp_dir, ignore_errors=True)


def test_malformed_persisted_payload_yields_safe_latest_response(monkeypatch):
    workspace_tmp_dir = Path("tmp_test_observability_api") / str(uuid.uuid4())
    workspace_tmp_dir.mkdir(parents=True, exist_ok=True)
    _force_mock_mode(monkeypatch, workspace_tmp_dir)
    clear_scan_store()
    get_auth_repository().clear()

    try:
        client = TestClient(app)
        headers = _register_and_get_headers(client, f"malformed-{uuid.uuid4().hex}@example.com")
        user_id = client.get("/auth/me", headers=headers).json()["user_id"]
        database_path = workspace_tmp_dir / "history" / "scan_store.sqlite"
        database_path.parent.mkdir(parents=True, exist_ok=True)

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
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "scan_bad",
                    "2026-04-16T09:00:00Z",
                    "2026-04-16T09:00:00Z",
                    1,
                    "sqlite",
                    user_id,
                    "balanced",
                    "tech",
                    "not-json",
                ),
            )

        response = client.get("/scans/latest", headers=headers)
        assert response.status_code == 404
        body = response.json()
        assert body["error"]["code"] == "not_found"
        assert body["error"]["message"] == "No scan result is available yet."
    finally:
        shutil.rmtree(workspace_tmp_dir, ignore_errors=True)


def test_login_failure_is_logged_without_password(monkeypatch, caplog):
    workspace_tmp_dir = Path("tmp_test_observability_api") / str(uuid.uuid4())
    workspace_tmp_dir.mkdir(parents=True, exist_ok=True)
    _force_mock_mode(monkeypatch, workspace_tmp_dir)
    clear_scan_store()
    get_auth_repository().clear()

    try:
        caplog.set_level(logging.INFO)
        client = TestClient(app)
        email = f"logging-{uuid.uuid4().hex}@example.com"
        register_response = client.post(
            "/auth/register",
            json={"email": email, "password": "Password123!"},
        )
        assert register_response.status_code == 200

        bad_password = "TotallyWrongPassword123!"
        login_response = client.post(
            "/auth/login",
            json={"email": email, "password": bad_password},
        )

        assert login_response.status_code == 401
        matching_records = [
            record
            for record in caplog.records
            if getattr(record, "event", None) == "auth_login_failure"
        ]
        assert matching_records
        assert all(bad_password not in record.getMessage() for record in matching_records)
    finally:
        shutil.rmtree(workspace_tmp_dir, ignore_errors=True)
