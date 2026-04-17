from pathlib import Path
import shutil
import uuid

import pytest
import requests

import data_provider
from data_provider import discover_option_contracts_for_window, fetch_underlying_stock_trade
from engine import run_scan_engine
from mock_data import MOCK_OPTIONS_DATA


class _FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


def _workspace_tmp_dir() -> Path:
    workspace_tmp_dir = Path("tmp_test_performance_reliability") / str(uuid.uuid4())
    workspace_tmp_dir.mkdir(parents=True, exist_ok=True)
    return workspace_tmp_dir


def test_run_scan_engine_keeps_successful_tickers_when_one_provider_result_fails(monkeypatch):
    provider_result = {
        "market_data": {"QQQ": MOCK_OPTIONS_DATA["QQQ"]},
        "missing_tickers": ["BROKEN"],
        "provider": "alpaca-contracts-plus-symbol-snapshots",
        "provider_errors": [
            {
                "ticker": "BROKEN",
                "error": "Provider request timed out.",
                "category": "timeout",
            }
        ],
        "ticker_diagnostics": [
            {
                "ticker": "QQQ",
                "provider_status": "ok",
                "provider": "alpaca",
                "cache_hit": False,
                "duration_ms": 75.5,
                "provider_diagnostics": {"ticker": "QQQ", "valid_contract_count": 8},
            },
            {
                "ticker": "BROKEN",
                "provider_status": "error",
                "provider": "alpaca",
                "cache_hit": False,
                "duration_ms": 120.0,
                "provider_diagnostics": {"ticker": "BROKEN", "reason": "Provider request timed out."},
            },
        ],
        "cache": {
            "market_data": {"hit": False},
            "contracts": {"hits": 0, "misses": 1},
            "snapshots": {"hits": 0, "misses": 1},
            "underlying": {"hits": 0, "misses": 1},
        },
        "performance": {"provider_duration_ms": 180.0},
    }

    monkeypatch.setattr("engine.get_market_data", lambda *args, **kwargs: provider_result)

    result = run_scan_engine(
        profile_name="balanced",
        group_name="tech",
        tickers=["QQQ", "BROKEN"],
        persist_history=False,
    )

    assert result["partial_result"] is True
    assert result["provider_errors"] == provider_result["provider_errors"]
    assert any(trade["ticker"] == "QQQ" for trade in result["qualified"])
    assert len(result["ticker_diagnostics"]) == 2
    broken = next(item for item in result["ticker_diagnostics"] if item["ticker"] == "BROKEN")
    assert broken["provider_status"] == "error"
    assert broken["provider_diagnostics"]["reason"] == "Provider request timed out."


def test_discover_contracts_retries_after_timeout(monkeypatch):
    workspace_tmp_dir = _workspace_tmp_dir()
    call_count = {"value": 0}

    def fake_get(*args, **kwargs):
        call_count["value"] += 1
        if call_count["value"] == 1:
            raise requests.exceptions.Timeout("timed out")

        return _FakeResponse(
            200,
            {
                "option_contracts": [
                    {
                        "symbol": "SPY250117P00450000",
                        "expiration_date": "2030-01-17",
                    }
                ]
            },
        )

    monkeypatch.setenv("CACHE_DIR", str(workspace_tmp_dir / "cache"))
    monkeypatch.setattr(data_provider.requests, "get", fake_get)

    try:
        result = discover_option_contracts_for_window("SPY", dte_min=1, dte_max=4000)
        assert call_count["value"] == 2
        assert result["contracts"]
        assert result["request_metadata"]["attempt_count"] == 2
        assert result["request_metadata"]["cache_hit"] is False
    finally:
        shutil.rmtree(workspace_tmp_dir, ignore_errors=True)


def test_fetch_underlying_trade_uses_cache_on_repeat_call(monkeypatch):
    workspace_tmp_dir = _workspace_tmp_dir()
    call_count = {"value": 0}

    def fake_get(*args, **kwargs):
        call_count["value"] += 1
        return _FakeResponse(
            200,
            {
                "trades": {
                    "SPY": {
                        "p": 502.13,
                    }
                }
            },
        )

    monkeypatch.setenv("CACHE_DIR", str(workspace_tmp_dir / "cache"))
    monkeypatch.setenv("PROVIDER_UNDERLYING_CACHE_TTL_SECONDS", "60")
    monkeypatch.setattr(data_provider.requests, "get", fake_get)

    try:
        first = fetch_underlying_stock_trade("SPY")
        second = fetch_underlying_stock_trade("SPY")

        assert call_count["value"] == 1
        assert first["trade"]["p"] == 502.13
        assert second["trade"]["p"] == 502.13
        assert first["request_metadata"]["cache_hit"] is False
        assert second["request_metadata"]["cache_hit"] is True
    finally:
        shutil.rmtree(workspace_tmp_dir, ignore_errors=True)