import os
from datetime import date, datetime, timedelta
import sys
import time
import json
import hashlib
from pathlib import Path

import requests
from dotenv import load_dotenv

from mock_data import MOCK_OPTIONS_DATA

DEBUG_MODE = "--debug" in sys.argv



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

CACHE_TTL_SECONDS = 60
CACHE_DIR = Path(".cache")
CACHE_DIR.mkdir(exist_ok=True)


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
    return CACHE_DIR / f"market_data_{cache_key}.json"


def get_cached_market_data(cache_key):
    cache_file = get_cache_file_path(cache_key)

    if not cache_file.exists():
        return None

    try:
        with cache_file.open("r", encoding="utf-8") as f:
            entry = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None

    timestamp = entry.get("timestamp")
    value = entry.get("value")

    if timestamp is None or value is None:
        return None

    age = time.time() - timestamp
    if age > CACHE_TTL_SECONDS:
        try:
            cache_file.unlink()
        except OSError:
            pass
        return None

    return value


def set_cached_market_data(cache_key, value):
    cache_file = get_cache_file_path(cache_key)

    entry = {
        "timestamp": time.time(),
        "value": value,
    }

    try:
        with cache_file.open("w", encoding="utf-8") as f:
            json.dump(entry, f)
    except OSError:
        pass
    
    

def get_market_data(tickers, dte_min=30, dte_max=45):
    cache_key = build_market_data_cache_key(tickers, dte_min, dte_max)
    cached_value = get_cached_market_data(cache_key)

    if cached_value is not None:
        return cached_value

    if has_alpaca_credentials():
        result = get_alpaca_market_data(tickers, dte_min=dte_min, dte_max=dte_max)
    else:
        result = get_mock_market_data(tickers)

    set_cached_market_data(cache_key, result)
    return result


def has_alpaca_credentials():
    return bool(ALPACA_API_KEY and ALPACA_API_SECRET)


def alpaca_headers():
    return {
        "APCA-API-KEY-ID": ALPACA_API_KEY,
        "APCA-API-SECRET-KEY": ALPACA_API_SECRET,
    }


def get_mock_market_data(tickers):
    market_data = {}
    missing_tickers = []

    for ticker in tickers:
        if ticker in MOCK_OPTIONS_DATA:
            market_data[ticker] = MOCK_OPTIONS_DATA[ticker]
        else:
            missing_tickers.append(ticker)

    return {
        "market_data": market_data,
        "missing_tickers": missing_tickers,
        "provider": "alpaca-mock-fallback",
        "provider_errors": [],
    }


def get_alpaca_market_data(tickers, dte_min=30, dte_max=45):
    market_data = {}
    missing_tickers = []
    provider_errors = []

    for ticker in tickers:
        try:
            discovered = discover_option_contracts_for_window(
                ticker=ticker,
                dte_min=dte_min,
                dte_max=dte_max,
            )

            if not discovered["contracts"]:
                missing_tickers.append(ticker)
                continue

            option_symbols = [contract["symbol"] for contract in discovered["contracts"]]
            option_snapshots = fetch_option_snapshots_for_symbols(option_symbols)
            underlying_trade = fetch_underlying_stock_trade(ticker)

            normalized = normalize_discovered_contracts(
                        ticker=ticker,
                        discovered_contracts=discovered["contracts"],
                        option_snapshots=option_snapshots,
                        underlying_trade=underlying_trade,
                        chosen_expiration=discovered["chosen_expiration"],
                        chosen_dte=discovered["chosen_dte"],
                    )

            if normalized is None:
                missing_tickers.append(ticker)
                continue

            market_data[ticker] = normalized

            if not normalized["contracts"]:
                missing_tickers.append(ticker)

        except Exception as exc:
            provider_errors.append(
                {
                    "ticker": ticker,
                    "error": str(exc),
                }
            )

    return {
        "market_data": market_data,
        "missing_tickers": missing_tickers,
        "provider": "alpaca-contracts-plus-symbol-snapshots",
        "provider_errors": provider_errors,
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

    response = requests.get(
        OPTION_CONTRACTS_URL,
        headers=alpaca_headers(),
        params=params,
        timeout=20,
    )
    response.raise_for_status()

    raw = response.json()

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
        }

    return {
        "contracts": chosen_contracts,
        "chosen_expiration": expiration_date,
        "chosen_dte": chosen_dte,
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
        return {}

    all_snapshots = {}

    for symbol_chunk in chunk_list(option_symbols, chunk_size):
        params = {
            "symbols": ",".join(symbol_chunk),
        }

        response = requests.get(
            OPTION_SNAPSHOTS_URL,
            headers=alpaca_headers(),
            params=params,
            timeout=20,
        )
        response.raise_for_status()

        raw = response.json()

        chunk_snapshots = {}
        for key in ["snapshots", "data"]:
            value = raw.get(key)
            if isinstance(value, dict):
                chunk_snapshots = value
                break

        all_snapshots.update(chunk_snapshots)

    return all_snapshots


def fetch_underlying_stock_trade(ticker):
    params = {
        "symbols": ticker,
    }

    response = requests.get(
        STOCK_LATEST_TRADES_URL,
        headers=alpaca_headers(),
        params=params,
        timeout=20,
    )
    response.raise_for_status()

    raw = response.json()

    for key in ["trades", "data"]:
        value = raw.get(key)
        if isinstance(value, dict):
            return value.get(ticker)

    return None


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
        },
    }


def normalize_discovered_contract(raw_contract, option_snapshots):
    contract_symbol = raw_contract.get("symbol")
    option_type = raw_contract.get("type")
    if option_type:
        option_type = option_type.lower()

    strike_raw = raw_contract.get("strike_price")
    open_interest_raw = raw_contract.get("open_interest")

    snapshot = option_snapshots.get(contract_symbol, {})
    latest_quote = snapshot.get("latestQuote", {})
    greeks = snapshot.get("greeks", {})

    if greeks is None:
        greeks = {}

    strike = float(strike_raw) if strike_raw is not None else None
    open_interest = int(open_interest_raw) if open_interest_raw is not None else None

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

    price = underlying_trade.get("p")

    if price is not None:
        return round(float(price), 4)

    return None

def validate_normalized_contract(contract):
    required_fields = ["strike", "type", "delta", "bid", "ask"]
    return all(field in contract and contract[field] is not None for field in required_fields) 

def is_cached_market_data_available(tickers, dte_min=30, dte_max=45):
    cache_key = build_market_data_cache_key(tickers, dte_min, dte_max)
    return get_cached_market_data(cache_key) is not None