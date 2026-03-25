import os
from datetime import datetime, date
from typing import Any

import requests
from dotenv import load_dotenv

from mock_data import MOCK_OPTIONS_DATA


load_dotenv()

ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_API_SECRET = os.getenv("ALPACA_API_SECRET")
ALPACA_DATA_BASE_URL = os.getenv("ALPACA_DATA_BASE_URL", "https://data.alpaca.markets")


def get_market_data(tickers):
    if has_alpaca_credentials():
        return get_alpaca_market_data(tickers)

    return get_mock_market_data(tickers)


def has_alpaca_credentials():
    return bool(ALPACA_API_KEY and ALPACA_API_SECRET)


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
    }


def get_alpaca_market_data(tickers):
    market_data = {}
    missing_tickers = []
    provider_errors = []

    for ticker in tickers:
        try:
            raw_chain = fetch_alpaca_option_chain(ticker)

            if not raw_chain:
                missing_tickers.append(ticker)
                continue

            normalized = normalize_alpaca_chain(raw_chain, ticker)

            if normalized is None:
                missing_tickers.append(ticker)
                continue

            market_data[ticker] = normalized

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
        "provider": "alpaca",
        "provider_errors": provider_errors,
    }


def fetch_alpaca_option_chain(ticker, max_pages=5):
    headers = {
        "APCA-API-KEY-ID": ALPACA_API_KEY,
        "APCA-API-SECRET-KEY": ALPACA_API_SECRET,
    }

    base_url = f"{ALPACA_DATA_BASE_URL}/v1beta1/options/snapshots/{ticker}"

    all_snapshots = {}
    next_page_token = None
    pages_fetched = 0

    while pages_fetched < max_pages:
        params = {}

        if next_page_token:
            params["page_token"] = next_page_token

        response = requests.get(base_url, headers=headers, params=params, timeout=20)
        response.raise_for_status()

        data = response.json()
        pages_fetched += 1

        page_snapshots = data.get("snapshots", {})
        if not isinstance(page_snapshots, dict):
            page_snapshots = {}

        all_snapshots = merge_snapshot_maps(all_snapshots, page_snapshots)

        print(f"\n=== RAW RESPONSE PAGE {pages_fetched} FOR {ticker} ===")
        print("Top-level keys:", list(data.keys()))
        print("page_snapshot_count:", len(page_snapshots))
        print("total_snapshot_count:", len(all_snapshots))

        if page_snapshots:
            first_symbol = next(iter(page_snapshots))
            print("Sample contract symbol:", repr(first_symbol))
            print("Sample contract keys:", list(page_snapshots[first_symbol].keys()))
            print("Sample latestQuote:", page_snapshots[first_symbol].get("latestQuote"))
            print("Sample greeks:", page_snapshots[first_symbol].get("greeks"))

        next_page_token = data.get("next_page_token")
        print("next_page_token:", next_page_token)

        # Stop early if we already found expirations in the target DTE range
        if response_contains_target_dte(all_snapshots):
            print("Target DTE range found. Stopping pagination early.")
            break

        if not next_page_token:
            break

    return {
        "snapshots": all_snapshots,
        "next_page_token": next_page_token,
        "pages_fetched": pages_fetched,
    }


def normalize_alpaca_chain(raw_chain, ticker):
    snapshots = extract_contract_snapshots(raw_chain)

    print(f"\n=== NORMALIZE DEBUG: {ticker} ===")
    print("snapshot_count:", len(snapshots))

    if snapshots:
        first = snapshots[0]
        print("first_snapshot_symbol:", first.get("contract_symbol"))

    grouped = group_contracts_by_expiration(snapshots)
    print("grouped_expirations:", list(grouped.keys())[:10])
    print("grouped_expiration_count:", len(grouped))

    expiration_choice = choose_target_expiration(grouped)
    print("expiration_choice:", expiration_choice["expiration_date"] if expiration_choice else None)

    if expiration_choice is None:
        return {
            "underlying_price": None,
            "expiration_date": None,
            "DTE": None,
            "contracts": [],
            "provider_diagnostics": {
                "ticker": ticker,
                "snapshot_count": len(snapshots),
                "grouped_expiration_count": len(grouped),
                "reason": "no_usable_expiration_found",
            },
        }

    expiration_date = expiration_choice["expiration_date"]
    dte = expiration_choice["DTE"]
    contracts_for_expiration = expiration_choice["contracts"]

    print("contracts_for_expiration_count:", len(contracts_for_expiration))

    normalized_contracts = []
    all_normalized_contracts = []

    for raw_contract in contracts_for_expiration:
        normalized_contract = normalize_contract(raw_contract)
        all_normalized_contracts.append(normalized_contract)

        if validate_normalized_contract(normalized_contract):
            normalized_contracts.append(normalized_contract)

    print("normalized_contract_count:", len(all_normalized_contracts))
    print("valid_contract_count:", len(normalized_contracts))

    underlying_price = extract_underlying_price(raw_chain, contracts_for_expiration)
    print("underlying_price:", underlying_price)

    return {
        "underlying_price": underlying_price,
        "expiration_date": expiration_date,
        "DTE": dte,
        "contracts": normalized_contracts,
        "provider_diagnostics": {
            "ticker": ticker,
            "snapshot_count": len(snapshots),
            "grouped_expiration_count": len(grouped),
            "chosen_expiration": expiration_date,
            "chosen_dte": dte,
            "used_fallback_expiration": expiration_choice.get("used_fallback_expiration", False),
            "contracts_for_expiration_count": len(contracts_for_expiration),
            "normalized_contract_count": len(all_normalized_contracts),
            "valid_contract_count": len(normalized_contracts),
            "missing_delta_contracts": sum(
                1 for c in all_normalized_contracts if c.get("delta") is None
            ),
            "underlying_price_found": underlying_price is not None,
        },
    }


def extract_contract_snapshots(raw_chain):
    if not isinstance(raw_chain, dict):
        return []

    snapshots_container = raw_chain.get("snapshots", {})
    if not isinstance(snapshots_container, dict):
        return []

    snapshots = []

    for contract_symbol, payload in snapshots_container.items():
        if not isinstance(payload, dict):
            continue

        snapshot = dict(payload)
        snapshot["contract_symbol"] = contract_symbol
        snapshots.append(snapshot)

    return snapshots


def group_contracts_by_expiration(contract_snapshots):
    grouped = {}

    for contract in contract_snapshots:
        contract_symbol = contract.get("contract_symbol")
        symbol_info = parse_option_symbol(contract_symbol)

        if symbol_info is None:
            continue

        expiration_date = symbol_info["expiration_date"]
        grouped.setdefault(expiration_date, []).append(contract)

    return grouped

from datetime import datetime, date


def choose_target_expiration(grouped_contracts):
    today = date.today()
    candidates_in_range = []
    all_candidates = []

    for expiration_str, contracts in grouped_contracts.items():
        try:
            expiration_dt = datetime.strptime(expiration_str, "%Y-%m-%d").date()
        except ValueError:
            continue

        dte = (expiration_dt - today).days

        candidate = {
            "expiration_date": expiration_str,
            "DTE": dte,
            "contracts": contracts,
            "distance_from_target": abs(dte - 37),
            "used_fallback_expiration": False,
        }

        all_candidates.append(candidate)

        if 30 <= dte <= 45:
            candidates_in_range.append(candidate)

    if candidates_in_range:
        candidates_in_range.sort(key=lambda item: item["distance_from_target"])
        return candidates_in_range[0]

    non_expired = [c for c in all_candidates if c["DTE"] >= 0]
    if non_expired:
        non_expired.sort(key=lambda item: item["distance_from_target"])
        chosen = non_expired[0]
        chosen["used_fallback_expiration"] = True
        return chosen

    return None

def normalize_contract(raw_contract):
    contract_symbol = raw_contract.get("contract_symbol")
    symbol_info = parse_option_symbol(contract_symbol)

    if symbol_info is None:
        return {
            "strike": None,
            "type": None,
            "delta": None,
            "bid": None,
            "ask": None,
            "open_interest": None,
            "expiration_date": None,
        }

    latest_quote = raw_contract.get("latestQuote", {})
    greeks = raw_contract.get("greeks", {})

    if greeks is None:
        greeks = {}

    return {
        "strike": symbol_info["strike"],
        "type": symbol_info["type"],
        "delta": greeks.get("delta"),
        "bid": latest_quote.get("bp"),
        "ask": latest_quote.get("ap"),
        "open_interest": raw_contract.get("open_interest"),
        "expiration_date": symbol_info["expiration_date"],
    }

def validate_normalized_contract(contract):
    required_fields = ["strike", "type", "delta", "bid", "ask"]
    return all(field in contract and contract[field] is not None for field in required_fields)

from datetime import datetime


def parse_option_symbol(contract_symbol):
    """
    Parse an OCC-style option symbol like:
    QQQ260324C00547000

    Returns:
    {
        "underlying": "QQQ",
        "expiration_date": "2026-03-24",
        "type": "call",
        "strike": 547.0,
    }
    """
    if not contract_symbol or len(contract_symbol) < 15:
        return None

    underlying = contract_symbol[:-15]
    date_part = contract_symbol[-15:-9]
    option_type_code = contract_symbol[-9]
    strike_part = contract_symbol[-8:]

    try:
        expiration_date = datetime.strptime(date_part, "%y%m%d").strftime("%Y-%m-%d")
        strike = int(strike_part) / 1000
    except ValueError:
        return None

    option_type = "call" if option_type_code == "C" else "put" if option_type_code == "P" else None

    if option_type is None:
        return None

    return {
        "underlying": underlying,
        "expiration_date": expiration_date,
        "type": option_type,
        "strike": strike,
    }

def extract_underlying_price(raw_chain, contracts_for_expiration):
    
    # Only use real underlying fields if present.
    for contract in contracts_for_expiration:
        if "underlying_price" in contract and contract["underlying_price"] is not None:
            return contract["underlying_price"]

        underlying_asset = contract.get("underlying_asset", {})
        if isinstance(underlying_asset, dict):
            price = underlying_asset.get("price")
            if price is not None:
                return price

    # Do NOT use option latestTrade price as stock price.
    return None

def merge_snapshot_maps(existing_snapshots, new_snapshots):
    merged = dict(existing_snapshots)

    for contract_symbol, payload in new_snapshots.items():
        merged[contract_symbol] = payload

    return merged

def response_contains_target_dte(snapshot_map):
    if not isinstance(snapshot_map, dict) or not snapshot_map:
        return False

    grouped = group_contracts_by_expiration(
        [
            {**payload, "contract_symbol": contract_symbol}
            for contract_symbol, payload in snapshot_map.items()
            if isinstance(payload, dict)
        ]
    )

    today = date.today()

    for expiration_str in grouped.keys():
        try:
            expiration_dt = datetime.strptime(expiration_str, "%Y-%m-%d").date()
        except ValueError:
            continue

        dte = (expiration_dt - today).days
        if 30 <= dte <= 45:
            return True

    return False

