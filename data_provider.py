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


def fetch_alpaca_option_chain(ticker):
    url = f"{ALPACA_DATA_BASE_URL}/v1beta1/options/snapshots/{ticker}"
    headers = {
        "APCA-API-KEY-ID": ALPACA_API_KEY,
        "APCA-API-SECRET-KEY": ALPACA_API_SECRET,
    }

    response = requests.get(url, headers=headers, timeout=20)
    response.raise_for_status()

    return response.json()


def normalize_alpaca_chain(raw_chain, ticker):
    snapshots = extract_contract_snapshots(raw_chain)

    if not snapshots:
        return None

    grouped = group_contracts_by_expiration(snapshots)
    expiration_choice = choose_target_expiration(grouped)

    if expiration_choice is None:
        return None

    expiration_date = expiration_choice["expiration_date"]
    dte = expiration_choice["DTE"]
    contracts_for_expiration = expiration_choice["contracts"]

    normalized_contracts = []
    for raw_contract in contracts_for_expiration:
        normalized_contract = normalize_contract(raw_contract)
        if validate_normalized_contract(normalized_contract):
            normalized_contracts.append(normalized_contract)

    if not normalized_contracts:
        return None

    underlying_price = extract_underlying_price(raw_chain, contracts_for_expiration)

    if underlying_price is None:
        return None

    return {
        "underlying_price": underlying_price,
        "expiration_date": expiration_date,
        "DTE": dte,
        "contracts": normalized_contracts,
    }


def extract_contract_snapshots(raw_chain):
    if not isinstance(raw_chain, dict):
        return []

    # Alpaca snapshot responses are keyed by contract symbol.
    # We normalize them into a list of contract payloads.
    snapshots = []

    for contract_symbol, payload in raw_chain.items():
        if not isinstance(payload, dict):
            continue

        snapshot = dict(payload)
        snapshot["contract_symbol"] = contract_symbol
        snapshots.append(snapshot)

    return snapshots


def group_contracts_by_expiration(contract_snapshots):
    grouped = {}

    for contract in contract_snapshots:
        details = contract.get("details", {})
        expiration_date = details.get("expiration_date")

        if not expiration_date:
            continue

        grouped.setdefault(expiration_date, []).append(contract)

    return grouped


def choose_target_expiration(grouped_contracts):
    today = date.today()
    candidates = []

    for expiration_str, contracts in grouped_contracts.items():
        try:
            expiration_dt = datetime.strptime(expiration_str, "%Y-%m-%d").date()
        except ValueError:
            continue

        dte = (expiration_dt - today).days

        if 30 <= dte <= 45:
            distance_from_target = abs(dte - 37)
            candidates.append(
                {
                    "expiration_date": expiration_str,
                    "DTE": dte,
                    "contracts": contracts,
                    "distance_from_target": distance_from_target,
                }
            )

    if not candidates:
        return None

    candidates.sort(key=lambda item: item["distance_from_target"])
    return candidates[0]


def normalize_contract(raw_contract):
    details = raw_contract.get("details", {})
    latest_quote = raw_contract.get("latestQuote", {})
    greeks = raw_contract.get("greeks", {})

    option_type = details.get("type")
    if option_type:
        option_type = option_type.lower()

    return {
        "strike": details.get("strike_price"),
        "type": option_type,
        "delta": greeks.get("delta"),
        "bid": latest_quote.get("bp"),
        "ask": latest_quote.get("ap"),
        "open_interest": raw_contract.get("open_interest"),
    }


def validate_normalized_contract(contract):
    required_fields = ["strike", "type", "delta", "bid", "ask"]
    return all(field in contract and contract[field] is not None for field in required_fields)


def extract_underlying_price(raw_chain, contracts_for_expiration):
    # Try to pull underlying price from one of the contract snapshots.
    # Exact field location may vary, so we look in common places.
    for contract in contracts_for_expiration:
        if "underlying_price" in contract and contract["underlying_price"] is not None:
            return contract["underlying_price"]

        underlying_asset = contract.get("underlying_asset", {})
        if isinstance(underlying_asset, dict):
            price = underlying_asset.get("price")
            if price is not None:
                return price

    return None