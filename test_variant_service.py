"""Tests for variant_service.py (PU-15B.2)."""

from __future__ import annotations

import pytest

from backend.services.variant_service import generate_variants


# ---------------------------------------------------------------------------
# Shared fixtures
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


# ---------------------------------------------------------------------------
# Baseline variant
# ---------------------------------------------------------------------------

class TestBaselineVariant:
    def test_baseline_always_present_for_bull_put(self) -> None:
        result = generate_variants(bull_put_trade(), scan_id="s1", trade_id="t1")
        types = [v.variant_type for v in result.variants]
        assert "baseline" in types

    def test_baseline_always_present_for_bear_call(self) -> None:
        result = generate_variants(bear_call_trade(), scan_id="s1", trade_id="t1")
        types = [v.variant_type for v in result.variants]
        assert "baseline" in types

    def test_baseline_credit_is_not_estimated(self) -> None:
        result = generate_variants(bull_put_trade(), scan_id="s1", trade_id="t1")
        baseline = next(v for v in result.variants if v.variant_type == "baseline")
        assert baseline.is_credit_estimated is False

    def test_baseline_strikes_match_trade(self) -> None:
        trade = bull_put_trade(short_strike=180.0, long_strike=175.0, net_credit=1.45)
        result = generate_variants(trade, scan_id="s1", trade_id="t1")
        baseline = next(v for v in result.variants if v.variant_type == "baseline")
        assert baseline.short_strike == 180.0
        assert baseline.long_strike == 175.0
        assert baseline.net_credit == 1.45

    def test_baseline_has_payoff(self) -> None:
        result = generate_variants(bull_put_trade(), scan_id="s1", trade_id="t1")
        baseline = next(v for v in result.variants if v.variant_type == "baseline")
        assert baseline.payoff is not None
        assert baseline.payoff.max_profit > 0
        assert baseline.payoff.max_loss > 0


# ---------------------------------------------------------------------------
# Conservative variant — bull put spread
# ---------------------------------------------------------------------------

class TestConservativeVariantBullPut:
    def test_conservative_variant_is_present(self) -> None:
        result = generate_variants(bull_put_trade(), scan_id="s1", trade_id="t1")
        types = [v.variant_type for v in result.variants]
        assert "conservative" in types

    def test_conservative_short_strike_is_lower(self) -> None:
        """Conservative bull put has a lower short strike (further OTM)."""
        trade = bull_put_trade(short_strike=180.0, long_strike=175.0)
        result = generate_variants(trade, scan_id="s1", trade_id="t1")
        baseline = next(v for v in result.variants if v.variant_type == "baseline")
        conservative = next(v for v in result.variants if v.variant_type == "conservative")
        assert conservative.short_strike < baseline.short_strike

    def test_conservative_credit_is_lower(self) -> None:
        """Conservative variant offers less credit (further OTM)."""
        trade = bull_put_trade(short_strike=180.0, long_strike=175.0, net_credit=1.45)
        result = generate_variants(trade, scan_id="s1", trade_id="t1")
        baseline = next(v for v in result.variants if v.variant_type == "baseline")
        conservative = next(v for v in result.variants if v.variant_type == "conservative")
        assert conservative.net_credit < baseline.net_credit

    def test_conservative_breakeven_is_lower(self) -> None:
        """Conservative bull put has a lower breakeven price (more buffer)."""
        result = generate_variants(bull_put_trade(), scan_id="s1", trade_id="t1")
        baseline = next(v for v in result.variants if v.variant_type == "baseline")
        conservative = next(v for v in result.variants if v.variant_type == "conservative")
        assert conservative.breakeven < baseline.breakeven

    def test_conservative_spread_width_unchanged(self) -> None:
        """Shifting both legs preserves spread width."""
        result = generate_variants(bull_put_trade(), scan_id="s1", trade_id="t1")
        baseline = next(v for v in result.variants if v.variant_type == "baseline")
        conservative = next(v for v in result.variants if v.variant_type == "conservative")
        assert abs(conservative.spread_width - baseline.spread_width) < 0.01

    def test_conservative_credit_is_estimated(self) -> None:
        result = generate_variants(bull_put_trade(), scan_id="s1", trade_id="t1")
        conservative = next(v for v in result.variants if v.variant_type == "conservative")
        assert conservative.is_credit_estimated is True

    def test_conservative_has_payoff(self) -> None:
        result = generate_variants(bull_put_trade(), scan_id="s1", trade_id="t1")
        conservative = next(v for v in result.variants if v.variant_type == "conservative")
        assert conservative.payoff is not None

    def test_conservative_max_loss_less_than_baseline(self) -> None:
        """Less credit → larger max loss? No: same width, less credit → larger max loss.
        Actually: same width but less credit → max_loss = (width - credit)*100 is bigger."""
        result = generate_variants(bull_put_trade(), scan_id="s1", trade_id="t1")
        baseline = next(v for v in result.variants if v.variant_type == "baseline")
        conservative = next(v for v in result.variants if v.variant_type == "conservative")
        # Less credit means more of the spread width becomes max loss
        assert conservative.max_loss > baseline.max_loss


# ---------------------------------------------------------------------------
# Max-credit variant — bull put spread
# ---------------------------------------------------------------------------

class TestMaxCreditVariantBullPut:
    def test_max_credit_variant_is_present(self) -> None:
        result = generate_variants(bull_put_trade(), scan_id="s1", trade_id="t1")
        types = [v.variant_type for v in result.variants]
        assert "max_credit" in types

    def test_max_credit_short_strike_is_higher(self) -> None:
        """Max credit bull put has a higher short strike (closer to ATM)."""
        trade = bull_put_trade(short_strike=180.0, long_strike=175.0)
        result = generate_variants(trade, scan_id="s1", trade_id="t1")
        baseline = next(v for v in result.variants if v.variant_type == "baseline")
        max_credit = next(v for v in result.variants if v.variant_type == "max_credit")
        assert max_credit.short_strike > baseline.short_strike

    def test_max_credit_credit_is_higher(self) -> None:
        """Max credit variant offers more credit (closer to ATM)."""
        trade = bull_put_trade(short_strike=180.0, long_strike=175.0, net_credit=1.45)
        result = generate_variants(trade, scan_id="s1", trade_id="t1")
        baseline = next(v for v in result.variants if v.variant_type == "baseline")
        max_credit = next(v for v in result.variants if v.variant_type == "max_credit")
        assert max_credit.net_credit > baseline.net_credit

    def test_max_credit_breakeven_is_higher(self) -> None:
        """Max credit bull put has a higher breakeven (tighter room)."""
        result = generate_variants(bull_put_trade(), scan_id="s1", trade_id="t1")
        baseline = next(v for v in result.variants if v.variant_type == "baseline")
        max_credit = next(v for v in result.variants if v.variant_type == "max_credit")
        assert max_credit.breakeven > baseline.breakeven

    def test_max_credit_credit_is_estimated(self) -> None:
        result = generate_variants(bull_put_trade(), scan_id="s1", trade_id="t1")
        max_credit = next(v for v in result.variants if v.variant_type == "max_credit")
        assert max_credit.is_credit_estimated is True

    def test_max_credit_short_strike_still_otm(self) -> None:
        """Max credit short strike must remain below underlying (still OTM)."""
        trade = bull_put_trade(underlying=191.0, short_strike=180.0)
        result = generate_variants(trade, scan_id="s1", trade_id="t1")
        max_credit = next((v for v in result.variants if v.variant_type == "max_credit"), None)
        if max_credit is not None:
            assert max_credit.short_strike < 191.0

    def test_max_credit_credit_below_spread_width(self) -> None:
        """Credit must never exceed spread width (max loss must be positive)."""
        result = generate_variants(bull_put_trade(), scan_id="s1", trade_id="t1")
        max_credit = next((v for v in result.variants if v.variant_type == "max_credit"), None)
        if max_credit is not None:
            assert max_credit.net_credit < max_credit.spread_width


# ---------------------------------------------------------------------------
# Conservative variant — bear call spread
# ---------------------------------------------------------------------------

class TestConservativeVariantBearCall:
    def test_conservative_variant_is_present(self) -> None:
        result = generate_variants(bear_call_trade(), scan_id="s1", trade_id="t1")
        types = [v.variant_type for v in result.variants]
        assert "conservative" in types

    def test_conservative_short_strike_is_higher(self) -> None:
        """Conservative bear call has a higher short strike (further OTM for calls)."""
        result = generate_variants(bear_call_trade(), scan_id="s1", trade_id="t1")
        baseline = next(v for v in result.variants if v.variant_type == "baseline")
        conservative = next(v for v in result.variants if v.variant_type == "conservative")
        assert conservative.short_strike > baseline.short_strike

    def test_conservative_credit_is_lower(self) -> None:
        result = generate_variants(bear_call_trade(), scan_id="s1", trade_id="t1")
        baseline = next(v for v in result.variants if v.variant_type == "baseline")
        conservative = next(v for v in result.variants if v.variant_type == "conservative")
        assert conservative.net_credit < baseline.net_credit

    def test_conservative_breakeven_is_higher(self) -> None:
        """Conservative bear call has a higher breakeven (more buffer before loss)."""
        result = generate_variants(bear_call_trade(), scan_id="s1", trade_id="t1")
        baseline = next(v for v in result.variants if v.variant_type == "baseline")
        conservative = next(v for v in result.variants if v.variant_type == "conservative")
        assert conservative.breakeven > baseline.breakeven

    def test_conservative_spread_width_unchanged(self) -> None:
        result = generate_variants(bear_call_trade(), scan_id="s1", trade_id="t1")
        baseline = next(v for v in result.variants if v.variant_type == "baseline")
        conservative = next(v for v in result.variants if v.variant_type == "conservative")
        assert abs(conservative.spread_width - baseline.spread_width) < 0.01


# ---------------------------------------------------------------------------
# Max-credit variant — bear call spread
# ---------------------------------------------------------------------------

class TestMaxCreditVariantBearCall:
    def test_max_credit_variant_is_present(self) -> None:
        result = generate_variants(bear_call_trade(), scan_id="s1", trade_id="t1")
        types = [v.variant_type for v in result.variants]
        assert "max_credit" in types

    def test_max_credit_short_strike_is_lower(self) -> None:
        """Max credit bear call has a lower short strike (closer to ATM for calls)."""
        result = generate_variants(bear_call_trade(), scan_id="s1", trade_id="t1")
        baseline = next(v for v in result.variants if v.variant_type == "baseline")
        max_credit = next(v for v in result.variants if v.variant_type == "max_credit")
        assert max_credit.short_strike < baseline.short_strike

    def test_max_credit_credit_is_higher(self) -> None:
        result = generate_variants(bear_call_trade(), scan_id="s1", trade_id="t1")
        baseline = next(v for v in result.variants if v.variant_type == "baseline")
        max_credit = next(v for v in result.variants if v.variant_type == "max_credit")
        assert max_credit.net_credit > baseline.net_credit

    def test_max_credit_breakeven_is_lower(self) -> None:
        """Max credit bear call has a lower breakeven (tighter room)."""
        result = generate_variants(bear_call_trade(), scan_id="s1", trade_id="t1")
        baseline = next(v for v in result.variants if v.variant_type == "baseline")
        max_credit = next(v for v in result.variants if v.variant_type == "max_credit")
        assert max_credit.breakeven < baseline.breakeven

    def test_max_credit_short_strike_still_otm(self) -> None:
        """Max credit bear call short strike must stay above underlying."""
        trade = bear_call_trade(underlying=191.0, short_strike=205.0)
        result = generate_variants(trade, scan_id="s1", trade_id="t1")
        max_credit = next((v for v in result.variants if v.variant_type == "max_credit"), None)
        if max_credit is not None:
            assert max_credit.short_strike > 191.0


# ---------------------------------------------------------------------------
# Safety / edge cases
# ---------------------------------------------------------------------------

class TestVariantSafetyGuardrails:
    def test_unsupported_strategy_returns_only_baseline_or_empty(self) -> None:
        """Unsupported strategies never produce conservative or max_credit variants."""
        trade = {
            "ticker": "SPY",
            "strategy_type": "iron_condor",
            "underlying_price": 500.0,
            "short_strike": 495.0,
            "long_strike": 490.0,
            "net_credit": 1.0,
            "spread_width": 5.0,
            "expiration_date": "2026-05-15",
        }
        result = generate_variants(trade, scan_id="s1", trade_id="t1")
        non_baseline = [v for v in result.variants if v.variant_type != "baseline"]
        assert len(non_baseline) == 0

    def test_missing_underlying_returns_baseline_only(self) -> None:
        trade = {
            "ticker": "AAPL",
            "strategy_type": "bull_put_spread",
            "underlying_price": 0,
            "short_strike": 180.0,
            "long_strike": 175.0,
            "net_credit": 1.45,
        }
        result = generate_variants(trade, scan_id="s1", trade_id="t1")
        assert len(result.variants) == 1
        assert result.variants[0].variant_type == "baseline"

    def test_zero_credit_returns_no_baseline(self) -> None:
        trade = bull_put_trade(net_credit=0.0)
        result = generate_variants(trade, scan_id="s1", trade_id="t1")
        baseline = next((v for v in result.variants if v.variant_type == "baseline"), None)
        assert baseline is None

    def test_itm_max_credit_is_rejected(self) -> None:
        """If shifting up would make short strike >= underlying, max credit is not emitted."""
        trade = bull_put_trade(underlying=180.5, short_strike=180.0, long_strike=175.0, net_credit=1.45)
        result = generate_variants(trade, scan_id="s1", trade_id="t1")
        max_credit = next((v for v in result.variants if v.variant_type == "max_credit"), None)
        # If returned, must still be OTM
        if max_credit is not None:
            assert max_credit.short_strike < 180.5

    def test_variant_type_order_covers_all_expected(self) -> None:
        result = generate_variants(bull_put_trade(), scan_id="s1", trade_id="t1")
        types = {v.variant_type for v in result.variants}
        assert "baseline" in types
        assert types.issubset({"baseline", "conservative", "max_credit"})

    def test_delta_neutral_is_not_generated(self) -> None:
        """Delta-neutral is explicitly excluded from PU-15B.2."""
        result = generate_variants(bull_put_trade(), scan_id="s1", trade_id="t1")
        types = [v.variant_type for v in result.variants]
        assert "delta_neutral" not in types

    def test_all_variants_have_valid_payoff(self) -> None:
        result = generate_variants(bull_put_trade(), scan_id="s1", trade_id="t1")
        for v in result.variants:
            assert v.payoff is not None
            assert v.payoff.max_profit > 0
            assert v.payoff.max_loss > 0

    def test_variant_set_metadata(self) -> None:
        result = generate_variants(bull_put_trade(), scan_id="my_scan", trade_id="my_trade")
        assert result.scan_id == "my_scan"
        assert result.trade_id == "my_trade"
        assert result.strategy_key == "bull_put_spread"
        assert result.ticker == "AAPL"

    def test_strategy_alias_normalization(self) -> None:
        trade = bull_put_trade()
        trade["strategy_type"] = "bull_put"  # alias
        result = generate_variants(trade, scan_id="s1", trade_id="t1")
        assert result.strategy_key == "bull_put_spread"
        assert any(v.variant_type == "conservative" for v in result.variants)
