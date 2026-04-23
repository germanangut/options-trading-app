"""API integration tests for the workbench endpoint (PU-15B.4)."""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path

import data_provider
import pytest
from fastapi.testclient import TestClient

from backend.api.main import app
from backend.repositories.factory import get_auth_repository
from backend.services.scan_store import clear_scan_store


TMP_ROOT = Path("tmp_test_workbench_api")


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


# ---------------------------------------------------------------------------
# Auth guards
# ---------------------------------------------------------------------------

class TestWorkbenchApiAuth:
    def test_unauthenticated_returns_401(self) -> None:
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/v1/workbench/scans/s/trades/t")
        assert response.status_code == 401

    def test_missing_scan_returns_404(self) -> None:
        client = TestClient(app, raise_server_exceptions=False)
        email = f"user_{uuid.uuid4().hex[:8]}@test.com"
        headers = _register_and_get_headers(client, email)
        response = client.get("/api/v1/workbench/scans/NOSCAN/trades/NOTRADE", headers=headers)
        assert response.status_code == 404

    def test_missing_trade_returns_404(self) -> None:
        client = TestClient(app, raise_server_exceptions=False)
        email = f"user_{uuid.uuid4().hex[:8]}@test.com"
        headers = _register_and_get_headers(client, email)
        scan_id = _create_scan(client, headers)
        response = client.get(f"/api/v1/workbench/scans/{scan_id}/trades/NOTRADE", headers=headers)
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Parameter validation
# ---------------------------------------------------------------------------

class TestWorkbenchApiValidation:
    def test_invalid_strike_shift_returns_422(self) -> None:
        client = TestClient(app, raise_server_exceptions=False)
        email = f"user_{uuid.uuid4().hex[:8]}@test.com"
        headers = _register_and_get_headers(client, email)
        scan_id, trade_id = _get_first_trade(client, headers)
        response = client.get(
            f"/api/v1/workbench/scans/{scan_id}/trades/{trade_id}",
            params={"strike_shift": "invalid_value"},
            headers=headers,
        )
        assert response.status_code == 422

    def test_invalid_width_adjustment_returns_422(self) -> None:
        client = TestClient(app, raise_server_exceptions=False)
        email = f"user_{uuid.uuid4().hex[:8]}@test.com"
        headers = _register_and_get_headers(client, email)
        scan_id, trade_id = _get_first_trade(client, headers)
        response = client.get(
            f"/api/v1/workbench/scans/{scan_id}/trades/{trade_id}",
            params={"width_adjustment": "quadruple"},
            headers=headers,
        )
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Baseline response shape
# ---------------------------------------------------------------------------

class TestWorkbenchBaselineResponse:
    def test_baseline_params_return_200(self) -> None:
        client = TestClient(app, raise_server_exceptions=False)
        email = f"user_{uuid.uuid4().hex[:8]}@test.com"
        headers = _register_and_get_headers(client, email)
        scan_id, trade_id = _get_first_trade(client, headers)
        response = client.get(
            f"/api/v1/workbench/scans/{scan_id}/trades/{trade_id}",
            params={"strike_shift": "baseline", "width_adjustment": "baseline"},
            headers=headers,
        )
        assert response.status_code == 200

    def test_baseline_has_required_top_level_fields(self) -> None:
        client = TestClient(app, raise_server_exceptions=False)
        email = f"user_{uuid.uuid4().hex[:8]}@test.com"
        headers = _register_and_get_headers(client, email)
        scan_id, trade_id = _get_first_trade(client, headers)
        response = client.get(
            f"/api/v1/workbench/scans/{scan_id}/trades/{trade_id}",
            params={"strike_shift": "baseline", "width_adjustment": "baseline"},
            headers=headers,
        )
        data = response.json()
        for field in ("scan_id", "trade_id", "strategy_key", "baseline", "strike_shift", "width_adjustment"):
            assert field in data, f"Missing field: {field}"

    def test_baseline_scenario_has_required_fields(self) -> None:
        client = TestClient(app, raise_server_exceptions=False)
        email = f"user_{uuid.uuid4().hex[:8]}@test.com"
        headers = _register_and_get_headers(client, email)
        scan_id, trade_id = _get_first_trade(client, headers)
        response = client.get(
            f"/api/v1/workbench/scans/{scan_id}/trades/{trade_id}",
            params={"strike_shift": "baseline", "width_adjustment": "baseline"},
            headers=headers,
        )
        baseline = response.json()["baseline"]
        for field in ("short_strike", "long_strike", "net_credit", "spread_width", "max_profit", "max_loss", "breakeven", "label", "is_credit_estimated"):
            assert field in baseline, f"Missing baseline field: {field}"

    def test_baseline_scenario_is_null_for_baseline_params(self) -> None:
        client = TestClient(app, raise_server_exceptions=False)
        email = f"user_{uuid.uuid4().hex[:8]}@test.com"
        headers = _register_and_get_headers(client, email)
        scan_id, trade_id = _get_first_trade(client, headers)
        response = client.get(
            f"/api/v1/workbench/scans/{scan_id}/trades/{trade_id}",
            params={"strike_shift": "baseline", "width_adjustment": "baseline"},
            headers=headers,
        )
        data = response.json()
        assert data["scenario"] is None
        assert data["comparison"] is None

    def test_baseline_includes_control_options(self) -> None:
        client = TestClient(app, raise_server_exceptions=False)
        email = f"user_{uuid.uuid4().hex[:8]}@test.com"
        headers = _register_and_get_headers(client, email)
        scan_id, trade_id = _get_first_trade(client, headers)
        response = client.get(
            f"/api/v1/workbench/scans/{scan_id}/trades/{trade_id}",
            headers=headers,
        )
        data = response.json()
        assert "strike_shift_options" in data
        assert "width_options" in data
        assert len(data["strike_shift_options"]) == 3
        assert len(data["width_options"]) == 3

    def test_baseline_is_not_credit_estimated(self) -> None:
        client = TestClient(app, raise_server_exceptions=False)
        email = f"user_{uuid.uuid4().hex[:8]}@test.com"
        headers = _register_and_get_headers(client, email)
        scan_id, trade_id = _get_first_trade(client, headers)
        response = client.get(
            f"/api/v1/workbench/scans/{scan_id}/trades/{trade_id}",
            headers=headers,
        )
        data = response.json()
        assert data["baseline"]["is_credit_estimated"] is False


# ---------------------------------------------------------------------------
# What-if scenario response shape
# ---------------------------------------------------------------------------

class TestWorkbenchScenarioResponse:
    def test_further_otm_returns_scenario(self) -> None:
        client = TestClient(app, raise_server_exceptions=False)
        email = f"user_{uuid.uuid4().hex[:8]}@test.com"
        headers = _register_and_get_headers(client, email)
        scan_id, trade_id = _get_first_trade(client, headers)
        response = client.get(
            f"/api/v1/workbench/scans/{scan_id}/trades/{trade_id}",
            params={"strike_shift": "further_otm", "width_adjustment": "baseline"},
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        # Scenario may be available or unavailable — both are valid; just not a 500
        assert "baseline" in data

    def test_scenario_has_payoff_when_available(self) -> None:
        client = TestClient(app, raise_server_exceptions=False)
        email = f"user_{uuid.uuid4().hex[:8]}@test.com"
        headers = _register_and_get_headers(client, email)
        scan_id, trade_id = _get_first_trade(client, headers)
        response = client.get(
            f"/api/v1/workbench/scans/{scan_id}/trades/{trade_id}",
            params={"strike_shift": "further_otm", "width_adjustment": "baseline"},
            headers=headers,
        )
        data = response.json()
        if data.get("scenario") is not None:
            scenario = data["scenario"]
            assert "payoff" in scenario
            if scenario["payoff"] is not None:
                assert "payoff_points" in scenario["payoff"]
                assert len(scenario["payoff"]["payoff_points"]) > 0

    def test_comparison_present_when_scenario_available(self) -> None:
        client = TestClient(app, raise_server_exceptions=False)
        email = f"user_{uuid.uuid4().hex[:8]}@test.com"
        headers = _register_and_get_headers(client, email)
        scan_id, trade_id = _get_first_trade(client, headers)
        response = client.get(
            f"/api/v1/workbench/scans/{scan_id}/trades/{trade_id}",
            params={"strike_shift": "further_otm", "width_adjustment": "baseline"},
            headers=headers,
        )
        data = response.json()
        if data.get("scenario") is not None:
            assert data.get("comparison") is not None
            comparison = data["comparison"]
            for field in ("delta_net_credit", "delta_max_profit", "delta_max_loss", "delta_breakeven", "summary"):
                assert field in comparison, f"Missing comparison field: {field}"

    def test_scenario_credit_is_estimated(self) -> None:
        client = TestClient(app, raise_server_exceptions=False)
        email = f"user_{uuid.uuid4().hex[:8]}@test.com"
        headers = _register_and_get_headers(client, email)
        scan_id, trade_id = _get_first_trade(client, headers)
        response = client.get(
            f"/api/v1/workbench/scans/{scan_id}/trades/{trade_id}",
            params={"strike_shift": "further_otm", "width_adjustment": "baseline"},
            headers=headers,
        )
        data = response.json()
        if data.get("scenario") is not None:
            assert data["scenario"]["is_credit_estimated"] is True

    def test_wider_returns_200(self) -> None:
        client = TestClient(app, raise_server_exceptions=False)
        email = f"user_{uuid.uuid4().hex[:8]}@test.com"
        headers = _register_and_get_headers(client, email)
        scan_id, trade_id = _get_first_trade(client, headers)
        response = client.get(
            f"/api/v1/workbench/scans/{scan_id}/trades/{trade_id}",
            params={"strike_shift": "baseline", "width_adjustment": "wider"},
            headers=headers,
        )
        assert response.status_code == 200

    def test_narrower_returns_200(self) -> None:
        client = TestClient(app, raise_server_exceptions=False)
        email = f"user_{uuid.uuid4().hex[:8]}@test.com"
        headers = _register_and_get_headers(client, email)
        scan_id, trade_id = _get_first_trade(client, headers)
        response = client.get(
            f"/api/v1/workbench/scans/{scan_id}/trades/{trade_id}",
            params={"strike_shift": "baseline", "width_adjustment": "narrower"},
            headers=headers,
        )
        assert response.status_code == 200

    def test_default_params_return_baseline(self) -> None:
        """No query params → default to baseline/baseline."""
        client = TestClient(app, raise_server_exceptions=False)
        email = f"user_{uuid.uuid4().hex[:8]}@test.com"
        headers = _register_and_get_headers(client, email)
        scan_id, trade_id = _get_first_trade(client, headers)
        response = client.get(
            f"/api/v1/workbench/scans/{scan_id}/trades/{trade_id}",
            headers=headers,
        )
        data = response.json()
        assert data["strike_shift"] == "baseline"
        assert data["width_adjustment"] == "baseline"
        assert data["scenario"] is None
