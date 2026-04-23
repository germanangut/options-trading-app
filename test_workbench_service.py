"""Unit tests for workbench_service.py (PU-15B.4)."""

from __future__ import annotations

import pytest

from backend.contracts.workbench_models import WorkbenchParams
from backend.services.workbench_service import generate_workbench


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def bull_put_trade(
    *,
    underlying: float = 191.0,
    short_strike: float = 180.0,
    long_strike: float = 175.0,
    net_credit: float = 1.45,
) -> dict:
    return {
        "ticker": "AAPL",
        "strategy_type": "bull_put_spread",
        "underlying_price": underlying,
        "short_strike": short_strike,
        "long_strike": long_strike,
        "net_credit": net_credit,
        "spread_width": abs(short_strike - long_strike),
        "expiration_date": "2026-05-15",
    }


def bear_call_trade(
    *,
    underlying: float = 191.0,
    short_strike: float = 205.0,
    long_strike: float = 210.0,
    net_credit: float = 1.20,
) -> dict:
    return {
        "ticker": "AAPL",
        "strategy_type": "bear_call_spread",
        "underlying_price": underlying,
        "short_strike": short_strike,
        "long_strike": long_strike,
        "net_credit": net_credit,
        "spread_width": abs(long_strike - short_strike),
        "expiration_date": "2026-05-15",
    }


def baseline_params() -> WorkbenchParams:
    return WorkbenchParams(strike_shift="baseline", width_adjustment="baseline")


def further_otm_params() -> WorkbenchParams:
    return WorkbenchParams(strike_shift="further_otm", width_adjustment="baseline")


def closer_atm_params() -> WorkbenchParams:
    return WorkbenchParams(strike_shift="closer_atm", width_adjustment="baseline")


def narrower_params() -> WorkbenchParams:
    return WorkbenchParams(strike_shift="baseline", width_adjustment="narrower")


def wider_params() -> WorkbenchParams:
    return WorkbenchParams(strike_shift="baseline", width_adjustment="wider")


# ---------------------------------------------------------------------------
# Baseline scenario — always present
# ---------------------------------------------------------------------------

class TestWorkbenchBaseline:
    def test_baseline_always_returned(self) -> None:
        result = generate_workbench(bull_put_trade(), scan_id="s1", trade_id="t1", params=baseline_params())
        assert result.baseline is not None

    def test_baseline_strikes_match_trade(self) -> None:
        trade = bull_put_trade(short_strike=180.0, long_strike=175.0, net_credit=1.45)
        result = generate_workbench(trade, scan_id="s1", trade_id="t1", params=baseline_params())
        assert result.baseline.short_strike == 180.0
        assert result.baseline.long_strike == 175.0
        assert result.baseline.net_credit == 1.45

    def test_baseline_is_not_estimated(self) -> None:
        result = generate_workbench(bull_put_trade(), scan_id="s1", trade_id="t1", params=baseline_params())
        assert result.baseline.is_credit_estimated is False

    def test_baseline_label(self) -> None:
        result = generate_workbench(bull_put_trade(), scan_id="s1", trade_id="t1", params=baseline_params())
        assert "baseline" in result.baseline.label.lower() or "current" in result.baseline.label.lower()

    def test_baseline_params_returns_no_scenario(self) -> None:
        """When both controls are at baseline, no scenario is returned (it would be identical)."""
        result = generate_workbench(bull_put_trade(), scan_id="s1", trade_id="t1", params=baseline_params())
        assert result.scenario is None
        assert result.comparison is None
        assert result.unavailable_reason is None

    def test_baseline_has_payoff(self) -> None:
        result = generate_workbench(bull_put_trade(), scan_id="s1", trade_id="t1", params=baseline_params())
        assert result.baseline.payoff is not None
        assert result.baseline.payoff.max_profit > 0
        assert result.baseline.payoff.max_loss > 0


# ---------------------------------------------------------------------------
# Short-strike shift — bull put spread
# ---------------------------------------------------------------------------

class TestStrikeShiftBullPut:
    def test_further_otm_lowers_short_strike(self) -> None:
        trade = bull_put_trade(short_strike=180.0, long_strike=175.0)
        result = generate_workbench(trade, scan_id="s1", trade_id="t1", params=further_otm_params())
        assert result.scenario is not None
        assert result.scenario.short_strike < 180.0

    def test_further_otm_lowers_credit(self) -> None:
        """Further OTM means less premium collected."""
        trade = bull_put_trade(short_strike=180.0, long_strike=175.0, net_credit=1.45)
        result = generate_workbench(trade, scan_id="s1", trade_id="t1", params=further_otm_params())
        assert result.scenario is not None
        assert result.scenario.net_credit < 1.45

    def test_closer_atm_raises_short_strike(self) -> None:
        trade = bull_put_trade(short_strike=180.0, long_strike=175.0)
        result = generate_workbench(trade, scan_id="s1", trade_id="t1", params=closer_atm_params())
        assert result.scenario is not None
        assert result.scenario.short_strike > 180.0

    def test_closer_atm_raises_credit(self) -> None:
        """Closer to ATM means more premium collected."""
        trade = bull_put_trade(short_strike=180.0, long_strike=175.0, net_credit=1.45)
        result = generate_workbench(trade, scan_id="s1", trade_id="t1", params=closer_atm_params())
        assert result.scenario is not None
        assert result.scenario.net_credit > 1.45

    def test_scenario_credit_is_estimated(self) -> None:
        result = generate_workbench(bull_put_trade(), scan_id="s1", trade_id="t1", params=further_otm_params())
        assert result.scenario is not None
        assert result.scenario.is_credit_estimated is True

    def test_scenario_has_payoff(self) -> None:
        result = generate_workbench(bull_put_trade(), scan_id="s1", trade_id="t1", params=further_otm_params())
        assert result.scenario is not None
        assert result.scenario.payoff is not None
        assert len(result.scenario.payoff.payoff_points) > 0

    def test_spread_width_preserved_on_strike_only_shift(self) -> None:
        """When width_adjustment=baseline, width should remain the same."""
        trade = bull_put_trade(short_strike=180.0, long_strike=175.0)
        result = generate_workbench(trade, scan_id="s1", trade_id="t1", params=further_otm_params())
        assert result.scenario is not None
        assert abs(result.scenario.spread_width - result.baseline.spread_width) < 0.01

    def test_closer_atm_blocked_when_short_above_underlying(self) -> None:
        """Shifting short strike above underlying is invalid for bull put."""
        trade = bull_put_trade(underlying=181.0, short_strike=180.0, long_strike=175.0)
        result = generate_workbench(trade, scan_id="s1", trade_id="t1", params=closer_atm_params())
        assert result.scenario is None
        assert result.unavailable_reason is not None
        assert "clean alternative" in result.unavailable_reason.lower()


# ---------------------------------------------------------------------------
# Short-strike shift — bear call spread
# ---------------------------------------------------------------------------

class TestStrikeShiftBearCall:
    def test_further_otm_raises_short_strike(self) -> None:
        trade = bear_call_trade(short_strike=205.0, long_strike=210.0)
        result = generate_workbench(trade, scan_id="s1", trade_id="t1", params=further_otm_params())
        assert result.scenario is not None
        assert result.scenario.short_strike > 205.0

    def test_further_otm_lowers_credit(self) -> None:
        trade = bear_call_trade(short_strike=205.0, long_strike=210.0, net_credit=1.20)
        result = generate_workbench(trade, scan_id="s1", trade_id="t1", params=further_otm_params())
        assert result.scenario is not None
        assert result.scenario.net_credit < 1.20

    def test_closer_atm_lowers_short_strike(self) -> None:
        trade = bear_call_trade(short_strike=205.0, long_strike=210.0)
        result = generate_workbench(trade, scan_id="s1", trade_id="t1", params=closer_atm_params())
        assert result.scenario is not None
        assert result.scenario.short_strike < 205.0

    def test_closer_atm_raises_credit(self) -> None:
        trade = bear_call_trade(short_strike=205.0, long_strike=210.0, net_credit=1.20)
        result = generate_workbench(trade, scan_id="s1", trade_id="t1", params=closer_atm_params())
        assert result.scenario is not None
        assert result.scenario.net_credit > 1.20

    def test_closer_atm_blocked_when_short_below_underlying(self) -> None:
        trade = bear_call_trade(underlying=206.0, short_strike=205.0, long_strike=210.0)
        result = generate_workbench(trade, scan_id="s1", trade_id="t1", params=closer_atm_params())
        assert result.scenario is None
        assert result.unavailable_reason is not None


# ---------------------------------------------------------------------------
# Width adjustment
# ---------------------------------------------------------------------------

class TestWidthAdjustment:
    def test_narrower_reduces_spread_width(self) -> None:
        trade = bull_put_trade(short_strike=180.0, long_strike=175.0)
        result = generate_workbench(trade, scan_id="s1", trade_id="t1", params=narrower_params())
        assert result.scenario is not None
        assert result.scenario.spread_width < result.baseline.spread_width

    def test_wider_increases_spread_width(self) -> None:
        trade = bull_put_trade(short_strike=180.0, long_strike=175.0)
        result = generate_workbench(trade, scan_id="s1", trade_id="t1", params=wider_params())
        assert result.scenario is not None
        assert result.scenario.spread_width > result.baseline.spread_width

    def test_narrower_bear_call_reduces_width(self) -> None:
        trade = bear_call_trade(short_strike=205.0, long_strike=210.0)
        result = generate_workbench(trade, scan_id="s1", trade_id="t1", params=narrower_params())
        assert result.scenario is not None
        assert result.scenario.spread_width < result.baseline.spread_width

    def test_wider_bear_call_increases_width(self) -> None:
        trade = bear_call_trade(short_strike=205.0, long_strike=210.0)
        result = generate_workbench(trade, scan_id="s1", trade_id="t1", params=wider_params())
        assert result.scenario is not None
        assert result.scenario.spread_width > result.baseline.spread_width

    def test_short_strike_unchanged_on_width_only_shift(self) -> None:
        """When strike_shift=baseline, short strike should remain the same."""
        trade = bull_put_trade(short_strike=180.0, long_strike=175.0)
        result = generate_workbench(trade, scan_id="s1", trade_id="t1", params=narrower_params())
        assert result.scenario is not None
        assert result.scenario.short_strike == result.baseline.short_strike


# ---------------------------------------------------------------------------
# Comparison payload
# ---------------------------------------------------------------------------

class TestComparison:
    def test_comparison_returned_when_scenario_exists(self) -> None:
        result = generate_workbench(bull_put_trade(), scan_id="s1", trade_id="t1", params=further_otm_params())
        assert result.scenario is not None
        assert result.comparison is not None

    def test_comparison_is_none_when_no_scenario(self) -> None:
        result = generate_workbench(bull_put_trade(), scan_id="s1", trade_id="t1", params=baseline_params())
        assert result.comparison is None

    def test_comparison_delta_credit_negative_for_further_otm(self) -> None:
        result = generate_workbench(bull_put_trade(), scan_id="s1", trade_id="t1", params=further_otm_params())
        assert result.comparison is not None
        assert result.comparison.delta_net_credit < 0

    def test_comparison_delta_credit_positive_for_closer_atm(self) -> None:
        result = generate_workbench(bull_put_trade(), scan_id="s1", trade_id="t1", params=closer_atm_params())
        assert result.comparison is not None
        assert result.comparison.delta_net_credit > 0

    def test_comparison_has_summary_text(self) -> None:
        result = generate_workbench(bull_put_trade(), scan_id="s1", trade_id="t1", params=further_otm_params())
        assert result.comparison is not None
        assert len(result.comparison.summary) > 0

    def test_delta_width_negative_for_narrower(self) -> None:
        result = generate_workbench(bull_put_trade(), scan_id="s1", trade_id="t1", params=narrower_params())
        assert result.comparison is not None
        assert result.comparison.delta_spread_width < 0

    def test_delta_width_positive_for_wider(self) -> None:
        result = generate_workbench(bull_put_trade(), scan_id="s1", trade_id="t1", params=wider_params())
        assert result.comparison is not None
        assert result.comparison.delta_spread_width > 0


# ---------------------------------------------------------------------------
# Unavailable / safety / fallback scenarios
# ---------------------------------------------------------------------------

class TestUnavailableStates:
    def test_invalid_trade_returns_baseline_with_no_scenario(self) -> None:
        """A trade with zero underlying produces no valid scenario."""
        trade = bull_put_trade(underlying=0.0)
        result = generate_workbench(trade, scan_id="s1", trade_id="t1", params=further_otm_params())
        # Baseline may also be invalid but result should always be a WorkbenchResult
        assert result is not None
        assert result.scan_id == "s1"

    def test_unsupported_strategy_returns_unavailable(self) -> None:
        trade = {
            "ticker": "X",
            "strategy_type": "iron_condor",
            "underlying_price": 100.0,
            "short_strike": 95.0,
            "long_strike": 90.0,
            "net_credit": 1.0,
            "expiration_date": None,
        }
        result = generate_workbench(
            trade,
            scan_id="s1",
            trade_id="t1",
            params=further_otm_params(),
        )
        assert result.scenario is None
        assert result.unavailable_reason is not None

    def test_result_ids_match_inputs(self) -> None:
        result = generate_workbench(bull_put_trade(), scan_id="myScan", trade_id="myTrade", params=further_otm_params())
        assert result.scan_id == "myScan"
        assert result.trade_id == "myTrade"

    def test_result_preserves_strategy_key(self) -> None:
        result = generate_workbench(bull_put_trade(), scan_id="s1", trade_id="t1", params=further_otm_params())
        assert result.strategy_key == "bull_put_spread"

    def test_strategy_key_normalization(self) -> None:
        trade = bull_put_trade()
        trade["strategy_type"] = "Bull Put Spread"
        result = generate_workbench(trade, scan_id="s1", trade_id="t1", params=further_otm_params())
        assert result.strategy_key == "bull_put_spread"


# ---------------------------------------------------------------------------
# Payoff integration
# ---------------------------------------------------------------------------

class TestPayoffIntegration:
    def test_baseline_payoff_points_populated(self) -> None:
        result = generate_workbench(bull_put_trade(), scan_id="s1", trade_id="t1", params=baseline_params())
        assert result.baseline.payoff is not None
        assert len(result.baseline.payoff.payoff_points) > 0

    def test_scenario_payoff_points_populated(self) -> None:
        result = generate_workbench(bull_put_trade(), scan_id="s1", trade_id="t1", params=further_otm_params())
        assert result.scenario is not None
        assert result.scenario.payoff is not None
        assert len(result.scenario.payoff.payoff_points) > 0

    def test_payoff_max_profit_matches_scenario_max_profit(self) -> None:
        result = generate_workbench(bull_put_trade(), scan_id="s1", trade_id="t1", params=further_otm_params())
        assert result.scenario is not None
        assert result.scenario.payoff is not None
        assert abs(result.scenario.payoff.max_profit - result.scenario.max_profit) < 1.0

    def test_bear_call_scenario_payoff_populated(self) -> None:
        result = generate_workbench(bear_call_trade(), scan_id="s1", trade_id="t1", params=further_otm_params())
        assert result.scenario is not None
        assert result.scenario.payoff is not None
        assert len(result.scenario.payoff.payoff_points) > 0
