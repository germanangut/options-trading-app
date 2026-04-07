"""Lightweight strategy definitions and registry for supported spread types.

This module keeps strategy metadata centralized and easy to extend without
changing the existing engine flow or trading logic.
"""

from copy import deepcopy

from config_loader import load_strategy_config


DEFAULT_STRATEGY_DEFINITIONS = {
    "bull_put_spread": {
        "key": "bull_put_spread",
        "display_label": "bull put spread",
        "family": "credit_spread",
        "directional_bias": "bullish",
        "is_active": True,
        "is_supported": True,
        "target_deltas": {
            "short": -0.30,
            "long": -0.20,
        },
        "default_dte": {
            "min": 20,
            "max": 35,
        },
    },
    "bear_call_spread": {
        "key": "bear_call_spread",
        "display_label": "bear call spread",
        "family": "credit_spread",
        "directional_bias": "bearish",
        "is_active": True,
        "is_supported": True,
        "target_deltas": {
            "short": 0.30,
            "long": 0.20,
        },
        "default_dte": {
            "min": 20,
            "max": 35,
        },
    },
}

STRATEGY_CONFIG = load_strategy_config()


def _build_strategy_definitions():
    strategy_definitions = deepcopy(DEFAULT_STRATEGY_DEFINITIONS)

    for strategy_key, config in STRATEGY_CONFIG.items():
        if strategy_key not in strategy_definitions or not isinstance(config, dict):
            continue

        strategy = strategy_definitions[strategy_key]
        strategy["key"] = strategy_key

        if "enabled" in config:
            strategy["is_active"] = bool(config["enabled"])
        if config.get("display_label"):
            strategy["display_label"] = config["display_label"]
        if config.get("family"):
            strategy["family"] = config["family"]
        if config.get("direction"):
            strategy["directional_bias"] = config["direction"]
        if "is_supported" in config:
            strategy["is_supported"] = bool(config["is_supported"])
        if isinstance(config.get("target_deltas"), dict):
            strategy["target_deltas"] = dict(config["target_deltas"])
        if isinstance(config.get("default_dte"), dict):
            strategy["default_dte"] = dict(config["default_dte"])

    return strategy_definitions


STRATEGY_DEFINITIONS = _build_strategy_definitions()


def _normalize_strategy_key(strategy_key):
    if strategy_key is None:
        return None

    return (
        str(strategy_key)
        .strip()
        .lower()
        .replace("-", "_")
        .replace(" ", "_")
    )


def _build_strategy_registry():
    registry = {}

    for strategy in STRATEGY_DEFINITIONS.values():
        aliases = {
            strategy["key"],
            _normalize_strategy_key(strategy["key"]),
            _normalize_strategy_key(strategy.get("display_label")),
        }

        for alias in aliases:
            if alias:
                registry[alias] = strategy

    return registry


STRATEGY_REGISTRY = _build_strategy_registry()

BULL_PUT_SPREAD = STRATEGY_DEFINITIONS["bull_put_spread"]
BEAR_CALL_SPREAD = STRATEGY_DEFINITIONS["bear_call_spread"]


def get_strategy(strategy_key):
    strategy = STRATEGY_REGISTRY.get(_normalize_strategy_key(strategy_key))
    return dict(strategy) if strategy else None


def get_strategy_definition(strategy_key):
    return get_strategy(strategy_key)


def get_strategy_config(strategy_key):
    return get_strategy(strategy_key)


def get_active_strategies():
    return [
        dict(strategy)
        for strategy in STRATEGY_DEFINITIONS.values()
        if strategy.get("is_active") and strategy.get("is_supported")
    ]


def get_strategy_label(strategy_key, default=None):
    strategy = get_strategy(strategy_key)
    if strategy is None:
        return default

    return strategy["display_label"]


def apply_strategy_metadata(spread, strategy_key):
    if spread is None:
        return None

    strategy = get_strategy(strategy_key)
    if strategy is None:
        return spread

    spread.setdefault("strategy_key", strategy["key"])
    spread.setdefault("strategy_label", strategy["display_label"])
    spread.setdefault("strategy_type", strategy["display_label"])
    spread.setdefault("strategy_family", strategy["family"])
    spread.setdefault("directional_bias", strategy["directional_bias"])
    spread.setdefault("strategy_active", strategy["is_active"])
    spread.setdefault("strategy_supported", strategy["is_supported"])
    return spread
