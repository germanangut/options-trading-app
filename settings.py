"""Centralized runtime settings resolution for the options trading app."""

import os
from copy import deepcopy
from pathlib import Path

from dotenv import load_dotenv

from config_loader import load_config, load_strategy_config
from profiles import PROFILES


DEFAULT_SETTINGS = {
    "profile": "balanced",
    "ticker_group": "tech",
    "pop_weight": 0.6,
    "ror_weight": 0.4,
    "min_score": 65,
    "min_consistency": 3,
    "dte_min": 20,
    "dte_max": 35,
    "history_dir": ".history",
    "cache_dir": ".cache",
    "scan_database_path": None,
    "strategy_config": {},
    "alpaca_api_key": None,
    "alpaca_api_secret": None,
    "alpaca_data_base_url": "https://data.alpaca.markets",
    "alpaca_trading_base_url": "https://paper-api.alpaca.markets",
}

ENV_TO_SETTINGS_MAP = {
    "ALPACA_API_KEY": "alpaca_api_key",
    "ALPACA_API_SECRET": "alpaca_api_secret",
    "ALPACA_DATA_BASE_URL": "alpaca_data_base_url",
    "ALPACA_TRADING_BASE_URL": "alpaca_trading_base_url",
    "HISTORY_DIR": "history_dir",
    "CACHE_DIR": "cache_dir",
    "SCAN_DATABASE_PATH": "scan_database_path",
}

BASE_DIR = Path(__file__).resolve().parent
DOTENV_PATH = BASE_DIR / ".env"


def _load_local_dotenv():
    """Load .env if it exists, without overriding runtime environment variables."""
    if DOTENV_PATH.exists():
        load_dotenv(dotenv_path=DOTENV_PATH, override=False)


def _clean_overrides(overrides):
    """Return only explicit override values."""
    return {
        key: value
        for key, value in (overrides or {}).items()
        if value is not None
    }


def _load_env_overrides():
    """Load supported runtime overrides from environment variables."""
    env_overrides = {}

    for env_name, settings_key in ENV_TO_SETTINGS_MAP.items():
        value = os.environ.get(env_name)
        if value not in (None, ""):
            env_overrides[settings_key] = value
            env_overrides[env_name] = value

    return env_overrides


def get_settings(cli_overrides=None):
    """Resolve runtime settings with priority env > CLI > config.yaml > defaults.

    Profile-based scoring defaults are preserved for backward compatibility and
    are applied after config loading but before explicit CLI overrides.

    Args:
        cli_overrides: Optional dictionary of explicit runtime overrides.

    Returns:
        A merged settings dictionary.
    """
    _load_local_dotenv()
    overrides = _clean_overrides(cli_overrides)

    resolved = deepcopy(DEFAULT_SETTINGS)
    resolved.update(load_config())
    resolved["strategy_config"] = load_strategy_config()

    effective_profile = overrides.get("profile", resolved.get("profile"))
    profile_config = PROFILES.get(effective_profile, {})
    if effective_profile:
        resolved["profile"] = effective_profile
    resolved.update(profile_config)

    resolved.update(overrides)
    resolved.update(_load_env_overrides())
    return resolved
