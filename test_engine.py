from data_provider import get_market_data
from main import process_ticker


def test_iwm_bull_put_unavailable():
    provider_result = get_market_data(["IWM"])
    data = provider_result["market_data"]
    iwm_result = process_ticker("IWM", data["IWM"])

    assert iwm_result["bull_put_available"] is False


def test_msft_tie_break():
    provider_result = get_market_data(["MSFT"])
    data = provider_result["market_data"]
    msft_result = process_ticker("MSFT", data["MSFT"])

    short_put = msft_result["selected_legs"]["short_put"]

    assert short_put is not None
    assert short_put["strike"] == 454


def test_spy_near_miss():
    provider_result = get_market_data(["SPY"])
    data = provider_result["market_data"]
    spy_result = process_ticker("SPY", data["SPY"])

    spread = spy_result["bull_put_spread"]

    assert spread is not None
    assert spread["label"] == "Near Miss"


def test_qqq_high_quality():
    provider_result = get_market_data(["QQQ"])
    data = provider_result["market_data"]
    qqq_result = process_ticker("QQQ", data["QQQ"])

    spread = qqq_result["bull_put_spread"]

    assert spread is not None
    assert spread["label"] == "High Quality"


if __name__ == "__main__":
    test_iwm_bull_put_unavailable()
    test_msft_tie_break()
    test_spy_near_miss()
    test_qqq_high_quality()

    print("All tests passed.")