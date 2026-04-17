import os
from datetime import date, datetime, timedelta
import logging
import sys
import time
import json
import hashlib
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

from backend.observability.logging import get_logger, log_event
from mock_data import MOCK_OPTIONS_DATA
from settings import get_settings

DEBUG_MODE = "--debug" in sys.argv
logger = get_logger(__name__)



def debug_print(*args, **kwargs):
    if DEBUG_MODE:
        print(*args, **kwargs)

load_dotenv()

ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_API_SECRET = os.getenv("ALPACA_API_SECRET")
ALPACA_DATA_BASE_URL = os.getenv("ALPACA_DATA_BASE_URL", "https://data.alpaca.markets")
ALPACA_TRADING_BASE_URL = os.getenv("ALPACA_TRADING_BASE_URL", "https://paper-api.alpaca.markets")

OPTION_CONTRACTS_URL = f"{ALPACA_TRADING_BASE_URL}/v2/options/contracts"
OPTION_SNAPSHOTS_URL = f"{ALPACA_DATA_BASE_URL}/v1beta1/options/snapshots"
#STOCK_LATEST_QUOTES_URL = f"{ALPACA_DATA_BASE_URL}/v2/stocks/quotes/latest"
STOCK_LATEST_TRADES_URL = f"{ALPACA_DATA_BASE_URL}/v2/stocks/trades/latest"

RETRIABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504}


class ProviderRequestError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        category: str,
        transient: bool,
        status_code: int | None = None,
    ):
        super().__init__(message)
        self.category = category
        self.transient = transient
        self.status_code = status_code


def _provider_runtime_settings() -> dict[str, float | int]:
    settings = get_settings()
    return {
        "market_data_cache_ttl_seconds": int(
            settings.get("market_data_cache_ttl_seconds", 60)
        ),
        "provider_timeout_seconds": float(settings.get("provider_timeout_seconds", 12)),
        "provider_retry_count": int(settings.get("provider_retry_count", 2)),
        "provider_retry_backoff_seconds": float(
            settings.get("provider_retry_backoff_seconds", 0.35)
        ),
        "provider_contracts_cache_ttl_seconds": int(
            settings.get("provider_contracts_cache_ttl_seconds", 120)
        ),
        "provider_snapshots_cache_ttl_seconds": int(
            settings.get("provider_snapshots_cache_ttl_seconds", 45)
        ),
        "provider_underlying_cache_ttl_seconds": int(
            settings.get("provider_underlying_cache_ttl_seconds", 15)
        ),
    }


def _safe_float(value):
    if value in (None, ""):
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_int(value):
    if value in (None, ""):
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _build_cache_key(namespace, payload):
    raw_key = json.dumps({"namespace": namespace, **payload}, sort_keys=True)
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def _get_namespaced_cache_file_path(namespace, cache_key):
    return get_cache_dir() / f"{namespace}_{cache_key}.json"


def _read_cached_json(namespace, cache_key, ttl_seconds):
    if ttl_seconds <= 0:
        return None

    cache_file = _get_namespaced_cache_file_path(namespace, cache_key)
    if not cache_file.exists():
        return None

    try:
        with cache_file.open("r", encoding="utf-8") as file_handle:
            entry = json.load(file_handle)
    except (json.JSONDecodeError, OSError):
        return None

    timestamp = entry.get("timestamp")
    value = entry.get("value")
    if timestamp is None or value is None:
        return None

    age = time.time() - timestamp
    if age > ttl_seconds:
        try:
            cache_file.unlink()
        except OSError:
            pass
        return None

    return value


def _write_cached_json(namespace, cache_key, value):
    cache_file = _get_namespaced_cache_file_path(namespace, cache_key)
    entry = {
        "timestamp": time.time(),
        "value": value,
    }

    try:
        with cache_file.open("w", encoding="utf-8") as file_handle:
            json.dump(entry, file_handle)
    except OSError:
        pass


def _backoff_seconds(attempt_index, base_delay):
    return round(base_delay * max(attempt_index, 1), 3)


def _request_provider_json(
    url,
    *,
    headers,
    params,
    operation,
    ticker=None,
    cache_namespace=None,
    cache_ttl_seconds=0,
):
    runtime = _provider_runtime_settings()
    max_attempts = max(1, int(runtime["provider_retry_count"]) + 1)
    timeout_seconds = float(runtime["provider_timeout_seconds"])
    backoff_seconds = float(runtime["provider_retry_backoff_seconds"])
    cache_key = None

    if cache_namespace:
        cache_key = _build_cache_key(
            cache_namespace,
            {
                "url": url,
                "params": params,
            },
        )
        cached_payload = _read_cached_json(cache_namespace, cache_key, cache_ttl_seconds)
        if cached_payload is not None:
            return cached_payload, {
                "cache_hit": True,
                "attempt_count": 0,
                "status_code": 200,
                "timeout_seconds": timeout_seconds,
            }

    last_error = None
    for attempt in range(1, max_attempts + 1):
        request_started_at = time.perf_counter()
        try:
            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=timeout_seconds,
            )
        except requests.exceptions.Timeout as exc:
            last_error = ProviderRequestError(
                "Provider request timed out.",
                category="timeout",
                transient=True,
            )
        except requests.exceptions.ConnectionError as exc:
            last_error = ProviderRequestError(
                "Provider network connection failed.",
                category="network",
                transient=True,
            )
        except requests.exceptions.RequestException as exc:
            last_error = ProviderRequestError(
                str(exc) or "Provider request failed.",
                category="network",
                transient=False,
            )
        else:
            if response.status_code >= 400:
                category = "http"
                transient = response.status_code in RETRIABLE_STATUS_CODES
                if response.status_code in {401, 403}:
                    category = "auth"
                    transient = False
                elif 400 <= response.status_code < 500 and response.status_code not in RETRIABLE_STATUS_CODES:
                    category = "validation"
                    transient = False

                last_error = ProviderRequestError(
                    f"Provider returned HTTP {response.status_code}.",
                    category=category,
                    transient=transient,
                    status_code=response.status_code,
                )
            else:
                try:
                    payload = response.json()
                except ValueError as exc:
                    last_error = ProviderRequestError(
                        "Provider returned malformed JSON.",
                        category="payload",
                        transient=False,
                        status_code=response.status_code,
                    )
                else:
                    if not isinstance(payload, dict):
                        last_error = ProviderRequestError(
                            "Provider returned an unexpected payload shape.",
                            category="payload",
                            transient=False,
                            status_code=response.status_code,
                        )
                    else:
                        if cache_namespace and cache_key:
                            _write_cached_json(cache_namespace, cache_key, payload)
                        return payload, {
                            "cache_hit": False,
                            "attempt_count": attempt,
                            "status_code": response.status_code,
                            "timeout_seconds": timeout_seconds,
                            "duration_ms": round(
                                (time.perf_counter() - request_started_at) * 1000, 2
                            ),
                        }

        duration_ms = round((time.perf_counter() - request_started_at) * 1000, 2)
        if last_error is not None and last_error.transient and attempt < max_attempts:
            retry_delay = _backoff_seconds(attempt, backoff_seconds)
            log_event(
                logger,
                "provider_retry_scheduled",
                level=logging.WARNING,
                provider="alpaca",
                operation=operation,
                ticker=ticker,
                attempt=attempt,
                max_attempts=max_attempts,
                duration_ms=duration_ms,
                error_type=type(last_error).__name__,
                error_category=last_error.category,
                status_code=last_error.status_code,
                retry_delay_seconds=retry_delay,
            )
            time.sleep(retry_delay)
            continue

        break

    if last_error is None:
        last_error = ProviderRequestError(
            "Provider request failed.",
            category="unknown",
            transient=False,
        )

    raise last_error


def get_cache_dir():
    cache_dir = Path(get_settings().get("cache_dir", ".cache"))
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def build_market_data_cache_key(tickers, dte_min, dte_max):
    payload = {
        "tickers": sorted(tickers),
        "dte_min": dte_min,
        "dte_max": dte_max,
        "provider_mode": "alpaca" if has_alpaca_credentials() else "mock",
    }
    raw_key = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def get_cache_file_path(cache_key):
    return get_cache_dir() / f"market_data_{cache_key}.json"


def get_cached_market_data(cache_key):
    runtime = _provider_runtime_settings()
    return _read_cached_json(
        "market_data",
        cache_key,
        int(runtime["market_data_cache_ttl_seconds"]),
    )


def set_cached_market_data(cache_key, value):
    _write_cached_json("market_data", cache_key, value)
    
    

def get_market_data(tickers, dte_min=30, dte_max=45):
    provider = "alpaca" if has_alpaca_credentials() else "alpaca-mock-fallback"
    started_at = time.perf_counter()
    log_event(
        logger,
        "provider_request_started",
        provider=provider,
        ticker_count=len(tickers or []),
    )
    cache_key = build_market_data_cache_key(tickers, dte_min, dte_max)
    cached_value = get_cached_market_data(cache_key)

    if cached_value is not None:
        cached_value.setdefault("cache", {})
        cached_value["cache"]["market_data"] = {
            "hit": True,
            "ttl_seconds": int(_provider_runtime_settings()["market_data_cache_ttl_seconds"]),
        }
        cached_value.setdefault("performance", {})
        cached_value["performance"]["provider_duration_ms"] = round(
            (time.perf_counter() - started_at) * 1000, 2
        )
        log_event(
            logger,
            "provider_request_completed",
            provider=provider,
            duration_ms=round((time.perf_counter() - started_at) * 1000, 2),
            cache_hit=True,
            missing_ticker_count=len(cached_value.get("missing_tickers", [])),
        )
        return cached_value

    if has_alpaca_credentials():
        result = get_alpaca_market_data(tickers, dte_min=dte_min, dte_max=dte_max)
    else:
        result = get_mock_market_data(tickers)

    result.setdefault("cache", {})
    result["cache"]["market_data"] = {
        "hit": False,
        "ttl_seconds": int(_provider_runtime_settings()["market_data_cache_ttl_seconds"]),
    }
    result.setdefault("performance", {})
    result["performance"]["provider_duration_ms"] = round(
        (time.perf_counter() - started_at) * 1000, 2
    )
    if not result.get("provider_errors"):
        set_cached_market_data(cache_key, result)
    log_event(
        logger,
        "provider_request_completed",
        provider=result.get("provider", provider),
        duration_ms=round((time.perf_counter() - started_at) * 1000, 2),
        cache_hit=False,
        missing_ticker_count=len(result.get("missing_tickers", [])),
        provider_error_count=len(result.get("provider_errors", [])),
    )
    return result


def has_alpaca_credentials():
    return bool(ALPACA_API_KEY and ALPACA_API_SECRET)


def alpaca_headers():
    return {
        "APCA-API-KEY-ID": ALPACA_API_KEY,
        "APCA-API-SECRET-KEY": ALPACA_API_SECRET,
    }


def get_mock_market_data(tickers):
    started_at = time.perf_counter()
    log_event(
        logger,
        "provider_request_started",
        provider="alpaca-mock-fallback",
        ticker_count=len(tickers or []),
        fallback_mode=True,
    )
    market_data = {}
    missing_tickers = []

    for ticker in tickers:
        if ticker in MOCK_OPTIONS_DATA:
            market_data[ticker] = MOCK_OPTIONS_DATA[ticker]
        else:
            missing_tickers.append(ticker)

    result = {
        "market_data": market_data,
        "missing_tickers": missing_tickers,
        "provider": "alpaca-mock-fallback",
        "provider_errors": [],
        "ticker_diagnostics": [
            {
                "ticker": ticker,
                "provider_status": "ok" if ticker in market_data else "missing",
                "provider": "alpaca-mock-fallback",
                "cache_hit": False,
                "provider_diagnostics": {
                    "ticker": ticker,
                    "fallback_mode": True,
                    "valid_contract_count": len((market_data.get(ticker) or {}).get("contracts", [])),
                    "underlying_price_found": bool((market_data.get(ticker) or {}).get("underlying_price") is not None),
                },
            }
            for ticker in tickers
        ],
        "cache": {
            "market_data": {"hit": False},
            "contracts": {"hits": 0, "misses": 0},
            "snapshots": {"hits": 0, "misses": 0},
            "underlying": {"hits": 0, "misses": 0},
        },
        "performance": {},
    }
    log_event(
        logger,
        "provider_request_completed",
        provider="alpaca-mock-fallback",
        duration_ms=round((time.perf_counter() - started_at) * 1000, 2),
        missing_ticker_count=len(missing_tickers),
        fallback_mode=True,
    )
    return result


def get_alpaca_market_data(tickers, dte_min=30, dte_max=45):
    market_data = {}
    missing_tickers = []
    provider_errors = []
    ticker_diagnostics = []
    cache_summary = {
        "contracts": {"hits": 0, "misses": 0},
        "snapshots": {"hits": 0, "misses": 0},
        "underlying": {"hits": 0, "misses": 0},
    }

    for ticker in tickers:
        ticker_started_at = time.perf_counter()
        log_event(
            logger,
            "provider_request_started",
            provider="alpaca",
            ticker=ticker,
        )
        try:
            discovered = discover_option_contracts_for_window(
                ticker=ticker,
                dte_min=dte_min,
                dte_max=dte_max,
            )
            cache_summary["contracts"]["hits" if discovered["request_metadata"].get("cache_hit") else "misses"] += 1

            if not discovered["contracts"]:
                missing_tickers.append(ticker)
                ticker_diagnostics.append(
                    {
                        "ticker": ticker,
                        "provider_status": "missing",
                        "provider": "alpaca",
                        "cache_hit": bool(discovered["request_metadata"].get("cache_hit")),
                        "provider_diagnostics": {
                            "ticker": ticker,
                            "chosen_expiration": discovered.get("chosen_expiration"),
                            "chosen_dte": discovered.get("chosen_dte"),
                            "discovered_contract_count": 0,
                            "reason": "empty_option_chain",
                            "request_attempts": discovered["request_metadata"].get("attempt_count", 0),
                        },
                        "duration_ms": round((time.perf_counter() - ticker_started_at) * 1000, 2),
                    }
                )
                log_event(
                    logger,
                    "provider_request_completed",
                    provider="alpaca",
                    ticker=ticker,
                    duration_ms=round((time.perf_counter() - ticker_started_at) * 1000, 2),
                    missing_data=True,
                    contract_count=0,
                )
                continue

            option_symbols = [contract["symbol"] for contract in discovered["contracts"]]
            option_snapshots = fetch_option_snapshots_for_symbols(option_symbols)
            cache_summary["snapshots"]["hits"] += option_snapshots["request_metadata"].get("cache_hits", 0)
            cache_summary["snapshots"]["misses"] += option_snapshots["request_metadata"].get("cache_misses", 0)
            underlying_trade = fetch_underlying_stock_trade(ticker)
            cache_summary["underlying"]["hits" if underlying_trade["request_metadata"].get("cache_hit") else "misses"] += 1

            normalized = normalize_discovered_contracts(
                        ticker=ticker,
                        discovered_contracts=discovered["contracts"],
                        option_snapshots=option_snapshots["snapshots"],
                        underlying_trade=underlying_trade["trade"],
                        chosen_expiration=discovered["chosen_expiration"],
                        chosen_dte=discovered["chosen_dte"],
                    )

            normalized["provider_diagnostics"].update(
                {
                    "contracts_request": discovered["request_metadata"],
                    "snapshots_request": option_snapshots["request_metadata"],
                    "underlying_request": underlying_trade["request_metadata"],
                }
            )

            if normalized is None or normalized.get("underlying_price") is None:
                missing_tickers.append(ticker)
                reason = "underlying_price_missing" if normalized else "normalization_failed"
                provider_errors.append(
                    {
                        "ticker": ticker,
                        "error": reason,
                        "category": "payload",
                    }
                )
                ticker_diagnostics.append(
                    {
                        "ticker": ticker,
                        "provider_status": "missing",
                        "provider": "alpaca",
                        "cache_hit": bool(discovered["request_metadata"].get("cache_hit")),
                        "provider_diagnostics": (normalized or {}).get("provider_diagnostics", {}),
                        "duration_ms": round((time.perf_counter() - ticker_started_at) * 1000, 2),
                    }
                )
                log_event(
                    logger,
                    "provider_request_completed",
                    provider="alpaca",
                    ticker=ticker,
                    duration_ms=round((time.perf_counter() - ticker_started_at) * 1000, 2),
                    missing_data=True,
                    contract_count=0,
                )
                continue

            market_data[ticker] = normalized

            if not normalized["contracts"]:
                missing_tickers.append(ticker)

            ticker_diagnostics.append(
                {
                    "ticker": ticker,
                    "provider_status": "ok" if normalized["contracts"] else "missing",
                    "provider": "alpaca",
                    "cache_hit": bool(
                        discovered["request_metadata"].get("cache_hit")
                        and underlying_trade["request_metadata"].get("cache_hit")
                    ),
                    "provider_diagnostics": normalized["provider_diagnostics"],
                    "duration_ms": round((time.perf_counter() - ticker_started_at) * 1000, 2),
                }
            )

            log_event(
                logger,
                "provider_request_completed",
                provider="alpaca",
                ticker=ticker,
                duration_ms=round((time.perf_counter() - ticker_started_at) * 1000, 2),
                missing_data=not bool(normalized["contracts"]),
                contract_count=len(normalized["contracts"]),
                partial_data=normalized["provider_diagnostics"].get("matching_symbol_count", 0)
                != normalized["provider_diagnostics"].get("discovered_symbol_count", 0),
            )

        except Exception as exc:
            if ticker not in missing_tickers:
                missing_tickers.append(ticker)
            provider_errors.append(
                {
                    "ticker": ticker,
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                    "category": getattr(exc, "category", "provider"),
                    "status_code": getattr(exc, "status_code", None),
                }
            )
            ticker_diagnostics.append(
                {
                    "ticker": ticker,
                    "provider_status": "error",
                    "provider": "alpaca",
                    "cache_hit": False,
                    "provider_diagnostics": {
                        "ticker": ticker,
                        "reason": str(exc),
                    },
                    "duration_ms": round((time.perf_counter() - ticker_started_at) * 1000, 2),
                }
            )
            log_event(
                logger,
                "provider_request_failed",
                level=logging.ERROR,
                provider="alpaca",
                ticker=ticker,
                duration_ms=round((time.perf_counter() - ticker_started_at) * 1000, 2),
                error_type=type(exc).__name__,
            )

    return {
        "market_data": market_data,
        "missing_tickers": missing_tickers,
        "provider": "alpaca-contracts-plus-symbol-snapshots",
        "provider_errors": provider_errors,
        "ticker_diagnostics": ticker_diagnostics,
        "cache": cache_summary,
        "performance": {},
    }


def discover_option_contracts_for_window(ticker, dte_min=30, dte_max=45, limit=1000):
    today = date.today()
    expiration_gte = (today + timedelta(days=dte_min)).strftime("%Y-%m-%d")
    expiration_lte = (today + timedelta(days=dte_max)).strftime("%Y-%m-%d")

    params = {
        "underlying_symbols": ticker,
        "expiration_date_gte": expiration_gte,
        "expiration_date_lte": expiration_lte,
        "status": "active",
        "limit": limit,
    }

    raw, request_metadata = _request_provider_json(
        OPTION_CONTRACTS_URL,
        headers=alpaca_headers(),
        params=params,
        operation="discover_contracts",
        ticker=ticker,
        cache_namespace="provider_contracts",
        cache_ttl_seconds=int(_provider_runtime_settings()["provider_contracts_cache_ttl_seconds"]),
    )

    raw_contracts = extract_contract_list(raw)
    grouped = group_discovered_contracts_by_expiration(raw_contracts)
    chosen_expiration = choose_best_discovered_expiration(grouped)

    expiration_date = None
    chosen_contracts = []
    chosen_dte = None

    if chosen_expiration is not None:
        expiration_date = chosen_expiration["expiration_date"]
        chosen_contracts = chosen_expiration["contracts"]
        chosen_dte = chosen_expiration["DTE"]

    debug_print(f"\n=== CONTRACT DISCOVERY DEBUG: {ticker} ===")
    debug_print("raw_contract_count:", len(raw_contracts))

    if raw_contracts:
        debug_print("sample_discovered_contract_keys:", list(raw_contracts[0].keys()))
        debug_print("sample_discovered_contract:", raw_contracts[0])

    debug_print("grouped_expiration_count:", len(grouped))
    debug_print("chosen_expiration:", expiration_date)
    debug_print("chosen_dte:", chosen_dte)
    debug_print("chosen_contract_count:", len(chosen_contracts))

    if not chosen_contracts:
        return {
            "contracts": [],
            "chosen_expiration": None,
            "chosen_dte": None,
            "request_metadata": request_metadata,
        }

    return {
        "contracts": chosen_contracts,
        "chosen_expiration": expiration_date,
        "chosen_dte": chosen_dte,
        "request_metadata": request_metadata,
    }


def extract_contract_list(raw_response):
    if not isinstance(raw_response, dict):
        return []

    for key in ["option_contracts", "contracts", "data"]:
        value = raw_response.get(key)
        if isinstance(value, list):
            return value

    return []


def group_discovered_contracts_by_expiration(raw_contracts):
    grouped = {}

    for contract in raw_contracts:
        expiration_date = contract.get("expiration_date")
        if not expiration_date:
            continue

        grouped.setdefault(expiration_date, []).append(contract)

    return grouped


def choose_best_discovered_expiration(grouped_contracts):
    today = date.today()
    candidates = []

    for expiration_str, contracts in grouped_contracts.items():
        try:
            expiration_dt = datetime.strptime(expiration_str, "%Y-%m-%d").date()
        except ValueError:
            continue

        dte = (expiration_dt - today).days
        candidates.append(
            {
                "expiration_date": expiration_str,
                "contracts": contracts,
                "DTE": dte,
                "distance_from_target": abs(dte - 37),
            }
        )

    if not candidates:
        return None

    candidates.sort(key=lambda item: item["distance_from_target"])
    return candidates[0]


def chunk_list(items, chunk_size):
    for i in range(0, len(items), chunk_size):
        yield items[i:i + chunk_size]


def fetch_option_snapshots_for_symbols(option_symbols, chunk_size=50):
    """
    Fetch symbol-specific option snapshots in batches.

    Returns a dict keyed by option symbol.
    """
    if not option_symbols:
        return {
            "snapshots": {},
            "request_metadata": {
                "cache_hits": 0,
                "cache_misses": 0,
                "chunk_count": 0,
                "attempt_count": 0,
                "errors": [],
            },
        }

    all_snapshots = {}
    cache_hits = 0
    cache_misses = 0
    total_attempts = 0
    errors = []

    for symbol_chunk in chunk_list(option_symbols, chunk_size):
        params = {
            "symbols": ",".join(symbol_chunk),
        }

        try:
            raw, request_metadata = _request_provider_json(
                OPTION_SNAPSHOTS_URL,
                headers=alpaca_headers(),
                params=params,
                operation="fetch_option_snapshots",
                cache_namespace="provider_snapshots",
                cache_ttl_seconds=int(_provider_runtime_settings()["provider_snapshots_cache_ttl_seconds"]),
            )
        except ProviderRequestError as exc:
            errors.append(
                {
                    "message": str(exc),
                    "category": exc.category,
                    "status_code": exc.status_code,
                }
            )
            continue

        cache_hits += 1 if request_metadata.get("cache_hit") else 0
        cache_misses += 0 if request_metadata.get("cache_hit") else 1
        total_attempts += int(request_metadata.get("attempt_count", 0))

        chunk_snapshots = {}
        for key in ["snapshots", "data"]:
            value = raw.get(key)
            if isinstance(value, dict):
                chunk_snapshots = value
                break

        all_snapshots.update(chunk_snapshots)

    return {
        "snapshots": all_snapshots,
        "request_metadata": {
            "cache_hits": cache_hits,
            "cache_misses": cache_misses,
            "chunk_count": len(list(chunk_list(option_symbols, chunk_size))),
            "attempt_count": total_attempts,
            "errors": errors,
        },
    }


def fetch_underlying_stock_trade(ticker):
    params = {
        "symbols": ticker,
    }

    raw, request_metadata = _request_provider_json(
        STOCK_LATEST_TRADES_URL,
        headers=alpaca_headers(),
        params=params,
        operation="fetch_underlying_trade",
        ticker=ticker,
        cache_namespace="provider_underlying",
        cache_ttl_seconds=int(_provider_runtime_settings()["provider_underlying_cache_ttl_seconds"]),
    )

    for key in ["trades", "data"]:
        value = raw.get(key)
        if isinstance(value, dict):
            return {
                "trade": value.get(ticker),
                "request_metadata": request_metadata,
            }

    return {
        "trade": None,
        "request_metadata": request_metadata,
    }


def normalize_discovered_contracts(
    ticker,
    discovered_contracts,
    option_snapshots,
    underlying_trade,
    chosen_expiration,
    chosen_dte,
):
    normalized_contracts = []
    all_normalized_contracts = []

    snapshot_symbols = set(option_snapshots.keys())
    discovered_symbols = {contract.get("symbol") for contract in discovered_contracts}
    matching_symbols = discovered_symbols & snapshot_symbols

    debug_print(f"\n=== SYMBOL SNAPSHOT MATCH DEBUG: {ticker} ===")
    debug_print("discovered_symbol_count:", len(discovered_symbols))
    debug_print("snapshot_symbol_count:", len(snapshot_symbols))
    debug_print("matching_symbol_count:", len(matching_symbols))

    if discovered_contracts:
        first_symbol = discovered_contracts[0].get("symbol")
        debug_print("first_discovered_symbol:", first_symbol)
        debug_print("first_symbol_in_snapshots:", first_symbol in snapshot_symbols)

    for raw_contract in discovered_contracts:
        normalized = normalize_discovered_contract(raw_contract, option_snapshots)
        all_normalized_contracts.append(normalized)

        if validate_normalized_contract(normalized):
            normalized_contracts.append(normalized)

    underlying_price = normalize_underlying_price(underlying_trade)

    debug_print(f"\n=== NORMALIZED CONTRACT DEBUG: {ticker} ===")
    debug_print("discovered_contract_count:", len(discovered_contracts))
    debug_print("all_normalized_contract_count:", len(all_normalized_contracts))
    debug_print("valid_normalized_contract_count:", len(normalized_contracts))
    debug_print("underlying_price:", underlying_price)

    if all_normalized_contracts:
        debug_print("sample_normalized_contract:", all_normalized_contracts[0])

    return {
        "underlying_price": underlying_price,
        "expiration_date": chosen_expiration,
        "DTE": chosen_dte,
        "contracts": normalized_contracts,
        "provider_diagnostics": {
            "ticker": ticker,
            "chosen_expiration": chosen_expiration,
            "chosen_dte": chosen_dte,
            "discovered_contract_count": len(discovered_contracts),
            "valid_contract_count": len(normalized_contracts),
            "missing_delta_contracts": sum(
                1 for c in all_normalized_contracts if c.get("delta") is None
            ),
            "underlying_price_found": underlying_price is not None,
            "discovered_symbol_count": len(discovered_symbols),
            "snapshot_symbol_count": len(snapshot_symbols),
            "matching_symbol_count": len(matching_symbols),
            "degraded": bool(len(normalized_contracts) != len(discovered_contracts) or underlying_price is None),
        },
    }


def normalize_contract(raw_contract):
    """Normalize a single contract shape for legacy callers and tests."""
    if not isinstance(raw_contract, dict):
        return {
            "strike": None,
            "type": None,
            "delta": None,
            "bid": None,
            "ask": None,
            "open_interest": None,
        }

    details = raw_contract.get("details") if isinstance(raw_contract.get("details"), dict) else {}
    greeks = raw_contract.get("greeks") if isinstance(raw_contract.get("greeks"), dict) else {}
    latest_quote = raw_contract.get("latestQuote") if isinstance(raw_contract.get("latestQuote"), dict) else {}

    strike_raw = raw_contract.get("strike_price", details.get("strike_price"))
    option_type = raw_contract.get("type", details.get("type"))
    if option_type:
        option_type = option_type.lower()

    open_interest_raw = raw_contract.get("open_interest")

    strike = _safe_float(strike_raw)
    open_interest = _safe_int(open_interest_raw)

    return {
        "strike": strike,
        "type": option_type,
        "delta": greeks.get("delta"),
        "bid": latest_quote.get("bp"),
        "ask": latest_quote.get("ap"),
        "open_interest": open_interest,
    }


def normalize_discovered_contract(raw_contract, option_snapshots):
    contract_symbol = raw_contract.get("symbol")
    option_type = raw_contract.get("type")
    if option_type:
        option_type = option_type.lower()

    strike_raw = raw_contract.get("strike_price")
    open_interest_raw = raw_contract.get("open_interest")

    snapshot = option_snapshots.get(contract_symbol, {})
    if not isinstance(snapshot, dict):
        snapshot = {}

    latest_quote = snapshot.get("latestQuote", {})
    if not isinstance(latest_quote, dict):
        latest_quote = {}

    greeks = snapshot.get("greeks", {})

    if greeks is None:
        greeks = {}
    if not isinstance(greeks, dict):
        greeks = {}

    strike = _safe_float(strike_raw)
    open_interest = _safe_int(open_interest_raw)

    return {
        "strike": strike,
        "type": option_type,
        "delta": greeks.get("delta"),
        "bid": latest_quote.get("bp"),
        "ask": latest_quote.get("ap"),
        "open_interest": open_interest,
        "expiration_date": raw_contract.get("expiration_date"),  
        "symbol": contract_symbol,
    }


def normalize_underlying_price(underlying_trade):
    if not isinstance(underlying_trade, dict):
        return None

    price = _safe_float(underlying_trade.get("p"))

    if price is not None:
        return round(float(price), 4)

    return None

def validate_normalized_contract(contract):
    required_fields = ["strike", "type", "delta", "bid", "ask"]
    return all(field in contract and contract[field] is not None for field in required_fields) 

def is_cached_market_data_available(tickers, dte_min=30, dte_max=45):
    cache_key = build_market_data_cache_key(tickers, dte_min, dte_max)
    return get_cached_market_data(cache_key) is not None