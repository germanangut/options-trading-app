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


def _get_first_trade_id(client: TestClient, headers: dict[str, str]) -> tuple[str, str]:
    scan_id = _create_scan(client, headers)
    qualified_response = client.get(f"/api/v1/scans/{scan_id}/qualified-trades", headers=headers)
    assert qualified_response.status_code == 200
    qualified_rows = qualified_response.json()
    assert qualified_rows, "Expected at least one qualified trade candidate"
    trade_id = qualified_rows[0]["trade_id"]
    return scan_id, trade_id


def _create_ticket_from_trade(client: TestClient, headers: dict[str, str], scan_id: str, trade_id: str) -> str:
    detail_response = client.get(f"/api/v1/scans/{scan_id}/trades/{trade_id}", headers=headers)
    assert detail_response.status_code == 200
    trade = detail_response.json()["trade"]

    create_response = client.post(
        "/api/v1/tickets",
        headers=headers,
        json={
            "trade_id": trade_id,
            "source_scan_id": scan_id,
            "ticker": trade["ticker"],
            "strategy_key": trade["strategy_type"],
            "strategy_label": trade.get("strategy_label") or trade["strategy_type"],
            "directional_bias": trade.get("directional_bias"),
            "expiration_date": trade.get("expiration_date"),
            "short_strike": trade.get("short_strike"),
            "long_strike": trade.get("long_strike"),
            "underlying_price_at_creation": trade.get("underlying_price"),
            "net_credit_estimate": trade.get("net_credit"),
            "max_risk_estimate": trade.get("max_risk"),
            "adjusted_score_at_creation": trade.get("adjusted_score"),
        },
    )
    assert create_response.status_code == 201
    return create_response.json()["ticket_id"]


def test_get_trade_payoff_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    workspace_tmp_dir = Path("tmp_test_payoff_api") / str(uuid.uuid4())
    workspace_tmp_dir.mkdir(parents=True, exist_ok=True)
    _force_mock_mode(monkeypatch, workspace_tmp_dir)
    clear_scan_store()
    get_auth_repository().clear()

    client = TestClient(app)
    headers = _register_and_get_headers(client, f"payoff-{uuid.uuid4().hex}@example.com")
    scan_id, trade_id = _get_first_trade_id(client, headers)

    response = client.get(
        f"/api/v1/payoff/scans/{scan_id}/trades/{trade_id}",
        headers=headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["source_type"] == "qualified_trade"
    assert payload["source_id"] == trade_id

    payoff = payload["payoff"]
    assert payoff["strategy_key"] in {"bull_put_spread", "bear_call_spread"}
    assert payoff["max_profit"] >= 0
    assert payoff["max_loss"] >= 0
    assert len(payoff["payoff_points"]) == len(payoff["price_grid"])

    shutil.rmtree(workspace_tmp_dir, ignore_errors=True)


def test_get_ticket_payoff_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    workspace_tmp_dir = Path("tmp_test_payoff_api") / str(uuid.uuid4())
    workspace_tmp_dir.mkdir(parents=True, exist_ok=True)
    _force_mock_mode(monkeypatch, workspace_tmp_dir)
    clear_scan_store()
    get_auth_repository().clear()

    client = TestClient(app)
    headers = _register_and_get_headers(client, f"payoff-ticket-{uuid.uuid4().hex}@example.com")
    scan_id, trade_id = _get_first_trade_id(client, headers)
    ticket_id = _create_ticket_from_trade(client, headers, scan_id, trade_id)

    response = client.get(f"/api/v1/payoff/tickets/{ticket_id}", headers=headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["source_type"] == "execution_ticket"
    assert payload["source_id"] == ticket_id

    payoff = payload["payoff"]
    assert payoff["quantity"] >= 1
    assert payoff["breakeven_low"] is not None or payoff["breakeven_high"] is not None
    assert payoff["expiration_summary"]

    shutil.rmtree(workspace_tmp_dir, ignore_errors=True)
