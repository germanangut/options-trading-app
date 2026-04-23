"""API integration tests for the variants endpoint (PU-15B.2)."""

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


TMP_ROOT = Path("tmp_test_variant_api")


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


class TestVariantApiAuth:
    def test_unauthenticated_returns_401(self) -> None:
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/v1/variants/scans/s/trades/t")
        assert response.status_code == 401

    def test_missing_scan_returns_404(self) -> None:
        client = TestClient(app, raise_server_exceptions=False)
        email = f"user_{uuid.uuid4().hex[:8]}@test.com"
        headers = _register_and_get_headers(client, email)
        response = client.get("/api/v1/variants/scans/NOSCAN/trades/NOTRADE", headers=headers)
        assert response.status_code == 404

    def test_missing_trade_returns_404(self) -> None:
        client = TestClient(app, raise_server_exceptions=False)
        email = f"user_{uuid.uuid4().hex[:8]}@test.com"
        headers = _register_and_get_headers(client, email)
        scan_id = _create_scan(client, headers)
        response = client.get(f"/api/v1/variants/scans/{scan_id}/trades/NOTRADE", headers=headers)
        assert response.status_code == 404


class TestVariantApiResponse:
    def test_variants_endpoint_returns_200(self) -> None:
        client = TestClient(app, raise_server_exceptions=False)
        email = f"user_{uuid.uuid4().hex[:8]}@test.com"
        headers = _register_and_get_headers(client, email)
        scan_id, trade_id = _get_first_trade(client, headers)
        response = client.get(
            f"/api/v1/variants/scans/{scan_id}/trades/{trade_id}",
            headers=headers,
        )
        assert response.status_code == 200

    def test_variants_envelope_has_required_fields(self) -> None:
        client = TestClient(app, raise_server_exceptions=False)
        email = f"user_{uuid.uuid4().hex[:8]}@test.com"
        headers = _register_and_get_headers(client, email)
        scan_id, trade_id = _get_first_trade(client, headers)
        data = client.get(
            f"/api/v1/variants/scans/{scan_id}/trades/{trade_id}",
            headers=headers,
        ).json()
        assert "scan_id" in data
        assert "trade_id" in data
        assert "strategy_key" in data
        assert "variants" in data
        assert isinstance(data["variants"], list)

    def test_variants_contains_baseline(self) -> None:
        client = TestClient(app, raise_server_exceptions=False)
        email = f"user_{uuid.uuid4().hex[:8]}@test.com"
        headers = _register_and_get_headers(client, email)
        scan_id, trade_id = _get_first_trade(client, headers)
        data = client.get(
            f"/api/v1/variants/scans/{scan_id}/trades/{trade_id}",
            headers=headers,
        ).json()
        types = [v["variant_type"] for v in data["variants"]]
        assert "baseline" in types

    def test_variant_objects_have_required_fields(self) -> None:
        client = TestClient(app, raise_server_exceptions=False)
        email = f"user_{uuid.uuid4().hex[:8]}@test.com"
        headers = _register_and_get_headers(client, email)
        scan_id, trade_id = _get_first_trade(client, headers)
        data = client.get(
            f"/api/v1/variants/scans/{scan_id}/trades/{trade_id}",
            headers=headers,
        ).json()
        required = {
            "variant_type", "strategy_key", "short_strike", "long_strike",
            "net_credit", "spread_width", "max_profit", "max_loss", "breakeven",
            "label", "rationale", "is_credit_estimated", "comparison",
        }
        for variant in data["variants"]:
            for field in required:
                assert field in variant, f"Missing field '{field}' in variant"

    def test_comparison_payload_has_expected_deltas(self) -> None:
        client = TestClient(app, raise_server_exceptions=False)
        email = f"user_{uuid.uuid4().hex[:8]}@test.com"
        headers = _register_and_get_headers(client, email)
        scan_id, trade_id = _get_first_trade(client, headers)
        data = client.get(
            f"/api/v1/variants/scans/{scan_id}/trades/{trade_id}",
            headers=headers,
        ).json()

        baseline = next(v for v in data["variants"] if v["variant_type"] == "baseline")
        assert baseline["comparison"] is not None
        assert baseline["comparison"]["is_baseline"] is True
        assert baseline["comparison"]["delta_net_credit"] == 0.0

        for variant in data["variants"]:
            comparison = variant.get("comparison")
            assert comparison is not None
            assert "summary" in comparison
            assert "delta_max_loss" in comparison

    def test_baseline_has_payoff(self) -> None:
        client = TestClient(app, raise_server_exceptions=False)
        email = f"user_{uuid.uuid4().hex[:8]}@test.com"
        headers = _register_and_get_headers(client, email)
        scan_id, trade_id = _get_first_trade(client, headers)
        data = client.get(
            f"/api/v1/variants/scans/{scan_id}/trades/{trade_id}",
            headers=headers,
        ).json()
        baseline = next(v for v in data["variants"] if v["variant_type"] == "baseline")
        assert baseline["payoff"] is not None
        payoff = baseline["payoff"]
        assert payoff["max_profit"] > 0
        assert payoff["max_loss"] > 0
        assert "payoff_points" in payoff
        assert len(payoff["payoff_points"]) > 0

    def test_baseline_is_not_credit_estimated(self) -> None:
        client = TestClient(app, raise_server_exceptions=False)
        email = f"user_{uuid.uuid4().hex[:8]}@test.com"
        headers = _register_and_get_headers(client, email)
        scan_id, trade_id = _get_first_trade(client, headers)
        data = client.get(
            f"/api/v1/variants/scans/{scan_id}/trades/{trade_id}",
            headers=headers,
        ).json()
        baseline = next(v for v in data["variants"] if v["variant_type"] == "baseline")
        assert baseline["is_credit_estimated"] is False

    def test_non_baseline_variants_are_credit_estimated(self) -> None:
        client = TestClient(app, raise_server_exceptions=False)
        email = f"user_{uuid.uuid4().hex[:8]}@test.com"
        headers = _register_and_get_headers(client, email)
        scan_id, trade_id = _get_first_trade(client, headers)
        data = client.get(
            f"/api/v1/variants/scans/{scan_id}/trades/{trade_id}",
            headers=headers,
        ).json()
        for variant in data["variants"]:
            if variant["variant_type"] != "baseline":
                assert variant["is_credit_estimated"] is True

    def test_variant_labels_are_user_facing(self) -> None:
        """Labels should match the defined user-facing text."""
        client = TestClient(app, raise_server_exceptions=False)
        email = f"user_{uuid.uuid4().hex[:8]}@test.com"
        headers = _register_and_get_headers(client, email)
        scan_id, trade_id = _get_first_trade(client, headers)
        data = client.get(
            f"/api/v1/variants/scans/{scan_id}/trades/{trade_id}",
            headers=headers,
        ).json()
        label_map = {v["variant_type"]: v["label"] for v in data["variants"]}
        if "baseline" in label_map:
            assert "scanned" in label_map["baseline"].lower() or "current" in label_map["baseline"].lower()
        if "conservative" in label_map:
            assert "lower credit" in label_map["conservative"].lower() or "conservative" in label_map["conservative"].lower()
        if "max_credit" in label_map:
            assert "higher" in label_map["max_credit"].lower() or "premium" in label_map["max_credit"].lower()

    def test_delta_neutral_never_appears(self) -> None:
        """PU-15B.2 explicitly excludes delta-neutral."""
        client = TestClient(app, raise_server_exceptions=False)
        email = f"user_{uuid.uuid4().hex[:8]}@test.com"
        headers = _register_and_get_headers(client, email)
        scan_id, trade_id = _get_first_trade(client, headers)
        data = client.get(
            f"/api/v1/variants/scans/{scan_id}/trades/{trade_id}",
            headers=headers,
        ).json()
        types = [v["variant_type"] for v in data["variants"]]
        assert "delta_neutral" not in types
