"""Centralized runtime settings resolution for the options trading app."""

import os
from copy import deepcopy
from pathlib import Path

from dotenv import load_dotenv

from config_loader import load_config, load_strategy_config
from profiles import PROFILES


DEFAULT_SETTINGS = {
    "app_env": "development",
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
    "auth_session_ttl_hours": 168,
    "log_level": "INFO",
    "log_format": "json",
    "sentry_dsn": None,
    "strategy_config": {},
    "alpaca_api_key": None,
    "alpaca_api_secret": None,
    "alpaca_data_base_url": "https://data.alpaca.markets",
    "alpaca_trading_base_url": "https://paper-api.alpaca.markets",
    "market_data_cache_ttl_seconds": 60,
    "provider_timeout_seconds": 12,
    "provider_total_timeout_seconds": 20,
    "provider_retry_count": 2,
    "provider_retry_backoff_seconds": 0.35,
    "provider_retry_strategy": "exponential",
    "provider_retry_max_backoff_seconds": 1.5,
    "provider_contracts_cache_ttl_seconds": 120,
    "provider_snapshots_cache_ttl_seconds": 45,
    "provider_underlying_cache_ttl_seconds": 15,
}

ENV_TO_SETTINGS_MAP = {
    "APP_ENV": "app_env",
    "ALPACA_API_KEY": "alpaca_api_key",
    "ALPACA_API_SECRET": "alpaca_api_secret",
    "ALPACA_DATA_BASE_URL": "alpaca_data_base_url",
    "ALPACA_TRADING_BASE_URL": "alpaca_trading_base_url",
    "MARKET_DATA_CACHE_TTL_SECONDS": "market_data_cache_ttl_seconds",
    "PROVIDER_TIMEOUT_SECONDS": "provider_timeout_seconds",
    "PROVIDER_TOTAL_TIMEOUT_SECONDS": "provider_total_timeout_seconds",
    "PROVIDER_RETRY_COUNT": "provider_retry_count",
    "PROVIDER_RETRY_BACKOFF_SECONDS": "provider_retry_backoff_seconds",
    "PROVIDER_RETRY_STRATEGY": "provider_retry_strategy",
    "PROVIDER_RETRY_MAX_BACKOFF_SECONDS": "provider_retry_max_backoff_seconds",
    "PROVIDER_CONTRACTS_CACHE_TTL_SECONDS": "provider_contracts_cache_ttl_seconds",
    "PROVIDER_SNAPSHOTS_CACHE_TTL_SECONDS": "provider_snapshots_cache_ttl_seconds",
    "PROVIDER_UNDERLYING_CACHE_TTL_SECONDS": "provider_underlying_cache_ttl_seconds",
    "HISTORY_DIR": "history_dir",
    "CACHE_DIR": "cache_dir",
    "SCAN_DATABASE_PATH": "scan_database_path",
    "AUTH_SESSION_TTL_HOURS": "auth_session_ttl_hours",
    "LOG_LEVEL": "log_level",
    "LOG_FORMAT": "log_format",
    "SENTRY_DSN": "sentry_dsn",
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


def mask_sensitive_value(value):
    if value in (None, ""):
        return None

    text = str(value)
    if len(text) <= 4:
        return "***"
    return f"{text[:2]}***{text[-2:]}"


def get_safe_settings_summary() -> dict[str, object]:
    settings = get_settings()
    return {
        "app_env": settings.get("app_env"),
        "log_level": settings.get("log_level"),
        "history_dir": settings.get("history_dir"),
        "cache_dir": settings.get("cache_dir"),
        "scan_database_path": settings.get("scan_database_path"),
        "auth_session_ttl_hours": settings.get("auth_session_ttl_hours"),
        "alpaca_credentials_configured": bool(
            settings.get("alpaca_api_key") and settings.get("alpaca_api_secret")
        ),
        "alpaca_data_base_url": settings.get("alpaca_data_base_url"),
        "alpaca_trading_base_url": settings.get("alpaca_trading_base_url"),
        "market_data_cache_ttl_seconds": settings.get("market_data_cache_ttl_seconds"),
        "provider_timeout_seconds": settings.get("provider_timeout_seconds"),
        "provider_total_timeout_seconds": settings.get("provider_total_timeout_seconds"),
        "provider_retry_count": settings.get("provider_retry_count"),
        "provider_retry_backoff_seconds": settings.get("provider_retry_backoff_seconds"),
        "provider_retry_strategy": settings.get("provider_retry_strategy"),
        "provider_retry_max_backoff_seconds": settings.get("provider_retry_max_backoff_seconds"),
        "provider_contracts_cache_ttl_seconds": settings.get("provider_contracts_cache_ttl_seconds"),
        "provider_snapshots_cache_ttl_seconds": settings.get("provider_snapshots_cache_ttl_seconds"),
        "provider_underlying_cache_ttl_seconds": settings.get("provider_underlying_cache_ttl_seconds"),
        "sentry_dsn": mask_sensitive_value(settings.get("sentry_dsn")),
    }
