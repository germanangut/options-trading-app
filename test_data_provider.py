from data_provider import (
    get_market_data,
    get_mock_market_data,
    has_alpaca_credentials,
    normalize_contract,
    validate_normalized_contract,
)


def test_mock_provider_metadata():
    result = get_mock_market_data(["SPY"])

    assert result["provider"] == "alpaca-mock-fallback"


def test_get_market_data_uses_fallback_when_no_credentials():
    if has_alpaca_credentials():
        print("Skipping fallback test because Alpaca credentials are present.")
        return

    result = get_market_data(["SPY"])

    assert result["provider"] == "alpaca-mock-fallback"
    assert "SPY" in result["market_data"]


def test_missing_ticker_reporting():
    result = get_mock_market_data(["SPY", "FAKE"])

    assert "SPY" in result["market_data"]
    assert "FAKE" in result["missing_tickers"]


def test_normalize_contract_shape():
    raw_contract = {
        "details": {
            "strike_price": 500,
            "type": "PUT",
        },
        "greeks": {
            "delta": -0.30,
        },
        "latestQuote": {
            "bp": 2.20,
            "ap": 2.40,
        },
        "open_interest": 1200,
    }

    normalized = normalize_contract(raw_contract)

    assert normalized == {
        "strike": 500,
        "type": "put",
        "delta": -0.30,
        "bid": 2.20,
        "ask": 2.40,
        "open_interest": 1200,
    }


def test_validate_normalized_contract_accepts_valid_contract():
    contract = {
        "strike": 500,
        "type": "put",
        "delta": -0.30,
        "bid": 2.20,
        "ask": 2.40,
        "open_interest": 1200,
    }

    assert validate_normalized_contract(contract) is True


def test_validate_normalized_contract_rejects_missing_delta():
    contract = {
        "strike": 500,
        "type": "put",
        "delta": None,
        "bid": 2.20,
        "ask": 2.40,
        "open_interest": 1200,
    }

    assert validate_normalized_contract(contract) is False


if __name__ == "__main__":
    test_mock_provider_metadata()
    test_get_market_data_uses_fallback_when_no_credentials()
    test_missing_ticker_reporting()
    test_normalize_contract_shape()
    test_validate_normalized_contract_accepts_valid_contract()
    test_validate_normalized_contract_rejects_missing_delta()

    print("All provider tests passed.")