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
from backend.api.routes import scans


def _force_mock_mode(monkeypatch, workspace_tmp_dir):
    monkeypatch.setattr(data_provider, "ALPACA_API_KEY", None)
    monkeypatch.setattr(data_provider, "ALPACA_API_SECRET", None)
    monkeypatch.setenv("HISTORY_DIR", str(workspace_tmp_dir / "history"))
    monkeypatch.setenv("CACHE_DIR", str(workspace_tmp_dir / "cache"))


def test_post_scan_and_get_latest(monkeypatch):
    workspace_tmp_dir = Path("tmp_test_api_scans") / str(uuid.uuid4())
    workspace_tmp_dir.mkdir(parents=True, exist_ok=True)
    _force_mock_mode(monkeypatch, workspace_tmp_dir)
    scans._LATEST_SCAN_RESULT = None

    try:
        client = TestClient(app)
        payload = {
            "profile": "balanced",
            "ticker_group": "tech",
            "selected_strategy_keys": ["bull_put_spread", "bear_call_spread"],
            "dte_min": 20,
            "dte_max": 35,
            "min_score": 65,
            "min_consistency": 3,
        }

        post_response = client.post("/scans", json=payload)
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

        latest_response = client.get("/scans/latest")
        assert latest_response.status_code == 200
        latest_body = latest_response.json()

        assert latest_body["summary"] == body["summary"]
        assert latest_body["diagnostics"] == body["diagnostics"]
    finally:
        shutil.rmtree(workspace_tmp_dir, ignore_errors=True)
