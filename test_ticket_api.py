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


def _ticket_payload() -> dict[str, object]:
    return {
        "trade_id": "trade_demo_1",
        "source_scan_id": "scan_demo_1",
        "ticker": "aapl",
        "strategy_key": "bull_put_spread",
        "strategy_label": "Bull Put Spread",
        "directional_bias": "bullish",
        "expiration_date": "2026-05-15",
        "short_strike": 180,
        "long_strike": 175,
        "underlying_price_at_creation": 191.2,
        "net_credit_estimate": 1.45,
        "max_risk_estimate": 355,
        "adjusted_score_at_creation": 74,
        "quantity": 1,
        "order_intent": "open_credit",
        "note": "Initial review complete.",
    }


def test_ticket_api_create_get_list_patch(monkeypatch):
    workspace_tmp_dir = Path("tmp_test_ticket_api") / str(uuid.uuid4())
    workspace_tmp_dir.mkdir(parents=True, exist_ok=True)
    _force_mock_mode(monkeypatch, workspace_tmp_dir)
    clear_scan_store()
    get_auth_repository().clear()

    try:
        client = TestClient(app)
        headers = _register_and_get_headers(client, f"ticket-user-{uuid.uuid4().hex}@example.com")

        create_response = client.post("/api/v1/tickets", json=_ticket_payload(), headers=headers)
        assert create_response.status_code == 201
        created = create_response.json()

        assert created["ticket_id"].startswith("ticket_")
        assert created["trade_id"] == "trade_demo_1"
        assert created["ticker"] == "AAPL"
        assert created["execution_status"] == "draft"
        assert created["quantity"] == 1

        ticket_id = created["ticket_id"]

        get_response = client.get(f"/api/v1/tickets/{ticket_id}", headers=headers)
        assert get_response.status_code == 200
        assert get_response.json()["ticket_id"] == ticket_id

        list_response = client.get("/api/v1/tickets", headers=headers)
        assert list_response.status_code == 200
        list_items = list_response.json()["items"]
        assert any(item["ticket_id"] == ticket_id for item in list_items)

        by_trade_response = client.get("/api/v1/tickets/by-trade/trade_demo_1", headers=headers)
        assert by_trade_response.status_code == 200
        by_trade_items = by_trade_response.json()["items"]
        assert len(by_trade_items) >= 1
        assert by_trade_items[0]["trade_id"] == "trade_demo_1"

        patch_quantity_response = client.patch(
            f"/api/v1/tickets/{ticket_id}",
            json={"quantity": 3},
            headers=headers,
        )
        assert patch_quantity_response.status_code == 200
        assert patch_quantity_response.json()["quantity"] == 3

        patch_note_response = client.patch(
            f"/api/v1/tickets/{ticket_id}",
            json={"note": "Adjusted size after review."},
            headers=headers,
        )
        assert patch_note_response.status_code == 200
        assert patch_note_response.json()["note"] == "Adjusted size after review."

        patch_ready_response = client.patch(
            f"/api/v1/tickets/{ticket_id}",
            json={"execution_status": "ready"},
            headers=headers,
        )
        assert patch_ready_response.status_code == 200
        assert patch_ready_response.json()["execution_status"] == "ready"

        patch_invalid_status_response = client.patch(
            f"/api/v1/tickets/{ticket_id}",
            json={"execution_status": "submitted"},
            headers=headers,
        )
        assert patch_invalid_status_response.status_code == 422
    finally:
        shutil.rmtree(workspace_tmp_dir, ignore_errors=True)


def test_ticket_api_unauthenticated_create_rejected(monkeypatch):
    workspace_tmp_dir = Path("tmp_test_ticket_api") / str(uuid.uuid4())
    workspace_tmp_dir.mkdir(parents=True, exist_ok=True)
    _force_mock_mode(monkeypatch, workspace_tmp_dir)
    clear_scan_store()
    get_auth_repository().clear()

    try:
        client = TestClient(app)
        response = client.post("/api/v1/tickets", json=_ticket_payload())
        assert response.status_code == 401
    finally:
        shutil.rmtree(workspace_tmp_dir, ignore_errors=True)
