from backend.services.screen_builders import (
    build_daily_summary_payload,
    build_portfolio_screen_payload,
)


def _build_trade(trade_id: str, ticker: str, *, stability_level: str = "stable") -> dict:
    return {
        "trade_id": trade_id,
        "ticker": ticker,
        "strategy_type": "bull_put_spread",
        "strategy_label": "Bull Put Spread",
        "adjusted_score": 74.0,
        "score": 71.0,
        "POP": 67.0,
        "ROR": 22.0,
        "label": "High Quality",
        "stability_level": stability_level,
        "stability_count": 3,
        "decision_summary": f"{ticker} cleared the current thresholds.",
        "status_reason": f"{ticker} is actionable.",
    }


def test_build_daily_summary_payload_falls_back_to_canonical_scan_sections():
    top_trade = _build_trade("trade_aapl", "AAPL")
    second_trade = _build_trade("trade_msft", "MSFT", stability_level="new")
    scan_result = {
        "scan_metadata": {
            "scan_id": "scan_sparse",
            "profile": "balanced",
            "ticker_group": "tech",
            "execution_time_seconds": 1.8,
        },
        "summary": {
            "qualified_count": 2,
            "near_miss_count": 1,
            "top_overall": dict(top_trade),
        },
        "alerts": [dict(top_trade), dict(second_trade)],
        "daily_summary": {},
        "diagnostics": {
            "missing_tickers": ["NVDA"],
            "provider_errors": [{"ticker": "NVDA", "error": "timeout"}],
        },
    }

    payload = build_daily_summary_payload(scan_result)

    assert payload["scan_id"] == "scan_sparse"
    assert payload["headline"] == {
        "profile": "balanced",
        "ticker_group": "tech",
        "execution_time_seconds": 1.8,
        "qualified_count": 2,
        "near_miss_count": 1,
        "alerts_count": 2,
    }
    assert payload["top_opportunity"]["trade_id"] == "trade_aapl"
    assert payload["notes"] == [
        "Missing tickers: NVDA",
        "Provider errors were reported in the latest scan.",
    ]


def test_build_portfolio_screen_payload_falls_back_to_summary_count_for_sparse_portfolio():
    scan_result = {
        "scan_metadata": {"scan_id": "scan_portfolio"},
        "summary": {"qualified_count": 3},
        "portfolio_summary": {
            "exposure": {},
            "position_sizing": {},
            "overlap": {},
            "decision": {},
        },
    }

    payload = build_portfolio_screen_payload(scan_result)

    assert payload["scan_id"] == "scan_portfolio"
    assert payload["summary_cards"][0] == {"label": "Qualified Trades", "value": 3}
    assert payload["summary_cards"][3] == {
        "label": "Portfolio Posture",
        "value": "Portfolio View",
    }
    assert payload["positions"] == []
    assert payload["warnings"] == []
    assert payload["exposure_notes"] == []
    assert payload["top_ticker_concentration"] == []
    assert payload["directional_exposure"] == []
    assert payload["interpretation"] == []
    assert payload["key_signals"] == []
    assert payload["cautions"] == []
    assert payload["overlap_warnings"] == []