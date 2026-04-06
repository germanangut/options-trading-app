"""Lightweight strategy definitions for currently supported spread types.

This module keeps strategy metadata centralized and easy to extend without
changing the existing engine flow or trading logic.
"""

STRATEGY_DEFINITIONS = {
    "bull_put_spread": {
        "key": "bull_put_spread",
        "display_label": "bull put spread",
        "family": "credit_spread",
        "directional_bias": "bullish",
        "is_active": True,
        "is_supported": True,
    },
    "bear_call_spread": {
        "key": "bear_call_spread",
        "display_label": "bear call spread",
        "family": "credit_spread",
        "directional_bias": "bearish",
        "is_active": True,
        "is_supported": True,
    },
}

BULL_PUT_SPREAD = STRATEGY_DEFINITIONS["bull_put_spread"]
BEAR_CALL_SPREAD = STRATEGY_DEFINITIONS["bear_call_spread"]


def get_strategy_definition(strategy_key):
    strategy = STRATEGY_DEFINITIONS.get(strategy_key)
    return dict(strategy) if strategy else None


def get_active_strategies():
    return [
        dict(strategy)
        for strategy in STRATEGY_DEFINITIONS.values()
        if strategy.get("is_active") and strategy.get("is_supported")
    ]


def apply_strategy_metadata(spread, strategy_key):
    if spread is None:
        return None

    strategy = STRATEGY_DEFINITIONS.get(strategy_key)
    if strategy is None:
        return spread

    spread.setdefault("strategy_key", strategy["key"])
    spread.setdefault("strategy_label", strategy["display_label"])
    spread.setdefault("strategy_family", strategy["family"])
    spread.setdefault("directional_bias", strategy["directional_bias"])
    spread.setdefault("strategy_active", strategy["is_active"])
    spread.setdefault("strategy_supported", strategy["is_supported"])
    return spread
