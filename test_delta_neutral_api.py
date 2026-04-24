"""API integration tests for delta-neutral exploration endpoint (PU-15B.5)."""

from __future__ import annotations

import uuid
from pathlib import Path

import data_provider
import pytest
from fastapi.testclient import TestClient

from backend.api.main import app
from backend.repositories.factory import get_auth_repository
from backend.services.scan_store import clear_scan_store


def _force_mock_mode(monkeypatch: pytest.MonkeyPatch, workspace_tmp_dir: Path) -> None:
    monkeypatch.setattr(data_provider, "ALPACA_API_KEY", None)
    monkeypatch.setattr(data_provider, "ALPACA_API_SECRET", None)
    monkeypatch.setenv("HISTORY_DIR", str(workspace_tmp_dir / "history"))
    monkeypatch.setenv("CACHE_DIR", str(workspace_tmp_dir / "cache"))
    monkeypatch.setenv(
        "SCAN_DATABASE_PATH",
        str(workspace_tmp_dir / "history" / "scan_store.sqlite"),
    )


def _register_and_get_headers(client: TestClient, email: str) -> dict[str, str]:
    response = client.post("/auth/register", json={"email": email, "password": "Password123!"})
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _create_scan(client: TestClient, headers: dict[str, str]) -> str:
    payload = {
        "profile": "balanced",
        "ticker_group": "tech",
        "selected_strategy_keys": ["bull_put_spread", "bear_call_spread"],
        "dte_min": 20,
        "dte_max": 35,
        "min_score": 65,
        "min_consistency": 3,
    }
    response = client.post("/api/v1/scans", headers=headers, json=payload)
    assert response.status_code == 200
    return response.json()["scan_metadata"]["scan_id"]


def _get_first_trade(client: TestClient, headers: dict[str, str]) -> tuple[str, str]:
    scan_id = _create_scan(client, headers)
    qualified_response = client.get(f"/api/v1/scans/{scan_id}/qualified-trades", headers=headers)
    assert qualified_response.status_code == 200
    rows = qualified_response.json()
    assert rows, "Expected at least one qualified trade"
    return scan_id, rows[0]["trade_id"]


@pytest.fixture()
def workspace_tmp_dir(tmp_path: Path) -> Path:
    run_dir = tmp_path / uuid.uuid4().hex
    run_dir.mkdir(parents=True)
    (run_dir / "history").mkdir()
    (run_dir / "cache").mkdir()
    return run_dir


@pytest.fixture(autouse=True)
def _clear_state(workspace_tmp_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _force_mock_mode(monkeypatch, workspace_tmp_dir)
    get_auth_repository().clear()
    clear_scan_store()
    yield
    get_auth_repository().clear()
    clear_scan_store()


class TestDeltaNeutralApiAuth:
    def test_unauthenticated_returns_401(self) -> None:
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/v1/delta-neutral/scans/s/trades/t")
        assert response.status_code == 401

    def test_missing_scan_returns_404(self) -> None:
        client = TestClient(app, raise_server_exceptions=False)
        headers = _register_and_get_headers(client, f"user_{uuid.uuid4().hex[:8]}@test.com")
        response = client.get("/api/v1/delta-neutral/scans/NOSCAN/trades/NOTRADE", headers=headers)
        assert response.status_code == 404

    def test_missing_trade_returns_404(self) -> None:
        client = TestClient(app, raise_server_exceptions=False)
        headers = _register_and_get_headers(client, f"user_{uuid.uuid4().hex[:8]}@test.com")
        scan_id = _create_scan(client, headers)
        response = client.get(f"/api/v1/delta-neutral/scans/{scan_id}/trades/NOTRADE", headers=headers)
        assert response.status_code == 404


class TestDeltaNeutralApiPayload:
    def test_returns_expected_fields(self) -> None:
        client = TestClient(app, raise_server_exceptions=False)
        headers = _register_and_get_headers(client, f"user_{uuid.uuid4().hex[:8]}@test.com")
        scan_id, trade_id = _get_first_trade(client, headers)

        response = client.get(
            f"/api/v1/delta-neutral/scans/{scan_id}/trades/{trade_id}",
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()

        for field in (
            "scan_id",
            "trade_id",
            "strategy_key",
            "baseline",
            "neutral_candidate_available",
            "rationale",
        ):
            assert field in data

        baseline = data["baseline"]
        for field in (
            "short_strike",
            "long_strike",
            "net_credit",
            "max_profit",
            "max_loss",
            "breakeven",
            "net_delta",
        ):
            assert field in baseline

    def test_candidate_and_comparison_shape_when_available(self) -> None:
        client = TestClient(app, raise_server_exceptions=False)
        headers = _register_and_get_headers(client, f"user_{uuid.uuid4().hex[:8]}@test.com")
        scan_id, trade_id = _get_first_trade(client, headers)

        response = client.get(
            f"/api/v1/delta-neutral/scans/{scan_id}/trades/{trade_id}",
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()

        if data["neutral_candidate_available"]:
            assert data["neutral_candidate"] is not None
            assert data["comparison"] is not None
            assert "delta_reduction" in data["comparison"]
            assert "delta_reduction_pct" in data["comparison"]
            assert "summary" in data["comparison"]
        else:
            assert data["neutral_candidate"] is None
            assert data["unavailable_reason"] is not None
