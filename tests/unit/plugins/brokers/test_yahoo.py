"""Unit tests for Yahoo Finance market data and symbol metadata broker plugin."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import requests
from app.plugins.brokers.contracts import (
    BrokerCapability,
    TimeFrame,
)
from app.plugins.brokers.yahoo import (
    PLUGIN_MANIFEST,
    YahooBroker,
    create_adapter,
)


def test_yahoo_plugin_manifest_and_capabilities() -> None:
    """Verify plugin manifest metadata and broker capability bitmask."""
    broker = create_adapter()
    assert isinstance(broker, YahooBroker)
    assert broker.has_capability(BrokerCapability.MARKET_DATA)
    assert broker.has_capability(BrokerCapability.SYMBOLS)
    assert not broker.has_capability(BrokerCapability.TRADING)

    assert PLUGIN_MANIFEST["id"] == "data-source-yahoo"
    assert "bars" in PLUGIN_MANIFEST["capabilities"]
    assert "symbols" in PLUGIN_MANIFEST["capabilities"]
    assert PLUGIN_MANIFEST["metadata"]["provider_name"] == "Yahoo"


def test_get_bars_events_history_parameter() -> None:
    """Verify get_bars includes events=history in request parameters."""
    broker = YahooBroker()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "chart": {
            "result": [
                {
                    "timestamp": [1775606400],
                    "indicators": {
                        "quote": [
                            {
                                "open": [100.0],
                                "high": [105.0],
                                "low": [99.0],
                                "close": [104.0],
                                "volume": [1000],
                            }
                        ]
                    },
                }
            ]
        }
    }

    with patch.object(broker.session, "get", return_value=mock_resp) as mock_get:
        resp = broker.get_bars(
            symbol="AAPL",
            timeframe=TimeFrame.D1,
            date_from=datetime(2026, 4, 1, tzinfo=UTC),
            date_to=datetime(2026, 4, 10, tzinfo=UTC),
        )

        assert resp.is_success
        assert resp.data is not None
        assert len(resp.data) == 1
        bar = resp.data[0]
        assert bar.open == 100.0
        assert bar.high == 105.0
        assert bar.low == 99.0
        assert bar.close == 104.0
        assert bar.tick_volume == 1000

        mock_get.assert_called_once()
        _url, kwargs = mock_get.call_args
        assert kwargs["params"]["events"] == "history"
        assert kwargs["params"]["interval"] == "1d"
        assert kwargs["params"]["period1"] == int(
            datetime(2026, 4, 1, tzinfo=UTC).timestamp()
        )
        assert kwargs["params"]["period2"] == int(
            datetime(2026, 4, 10, tzinfo=UTC).timestamp()
        )


def test_get_bars_range_fallbacks() -> None:
    """Verify get_bars interval and range mapping when dates are not specified."""
    broker = YahooBroker()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "chart": {
            "result": [
                {
                    "timestamp": [1775606400],
                    "indicators": {
                        "quote": [
                            {
                                "open": [10.0],
                                "high": [11.0],
                                "low": [9.0],
                                "close": [10.5],
                                "volume": [100],
                            }
                        ]
                    },
                }
            ]
        }
    }

    with patch.object(broker.session, "get", return_value=mock_resp) as mock_get:
        # 1m -> 5d
        broker.get_bars("AAPL", timeframe=TimeFrame.M1)
        assert mock_get.call_args[1]["params"]["range"] == "5d"

        # 15m -> 1mo
        broker.get_bars("AAPL", timeframe=TimeFrame.M15)
        assert mock_get.call_args[1]["params"]["range"] == "1mo"

        # 1d -> 1y
        broker.get_bars("AAPL", timeframe=TimeFrame.D1)
        assert mock_get.call_args[1]["params"]["range"] == "1y"

        # 1mo -> 2y
        broker.get_bars("AAPL", timeframe=TimeFrame.MN1)
        assert mock_get.call_args[1]["params"]["range"] == "2y"


def test_get_bars_error_handling() -> None:
    """Verify get_bars failure responses on HTTP errors and empty results."""
    broker = YahooBroker()

    # HTTP 500
    err_resp = MagicMock()
    err_resp.status_code = 500
    with patch.object(broker.session, "get", return_value=err_resp):
        resp = broker.get_bars("AAPL")
        assert not resp.is_success
        assert resp.error is not None
        assert resp.error.code == "500"

    # Empty result
    empty_resp = MagicMock()
    empty_resp.status_code = 200
    empty_resp.json.return_value = {"chart": {"result": []}}
    with patch.object(broker.session, "get", return_value=empty_resp):
        resp = broker.get_bars("AAPL")
        assert not resp.is_success
        assert resp.error is not None
        assert resp.error.code == "NO_DATA"

    # Empty quotes or timestamps
    empty_quotes = MagicMock()
    empty_quotes.status_code = 200
    empty_quotes.json.return_value = {
        "chart": {
            "result": [
                {
                    "timestamp": [],
                    "indicators": {"quote": []},
                }
            ]
        }
    }
    with patch.object(broker.session, "get", return_value=empty_quotes):
        resp = broker.get_bars("AAPL")
        assert resp.is_success
        assert resp.data == []

    # Network Exception
    with patch.object(
        broker.session, "get", side_effect=requests.RequestException("Boom")
    ):
        resp = broker.get_bars("AAPL")
        assert not resp.is_success
        assert resp.error is not None
        assert resp.error.code == "REQUEST_ERROR"


def test_ensure_crumb_caching_and_negotiation() -> None:
    """Verify _ensure_crumb negotiates cookie and crumb and caches token."""
    broker = YahooBroker()
    initial_crumb = broker.crumb
    assert initial_crumb is None

    cookie_resp = MagicMock()
    cookie_resp.status_code = 404

    crumb_resp = MagicMock()
    crumb_resp.status_code = 200
    crumb_resp.text = "test_crumb_123\n"

    with patch.object(
        broker.session, "get", side_effect=[cookie_resp, crumb_resp]
    ) as mock_get:
        crumb = broker._ensure_crumb()
        assert crumb == "test_crumb_123"
        assert broker.crumb == "test_crumb_123"
        assert mock_get.call_count == 2

    # Second call uses cache
    with patch.object(broker.session, "get") as mock_get_cached:
        crumb2 = broker._ensure_crumb()
        assert crumb2 == "test_crumb_123"
        mock_get_cached.assert_not_called()


def test_ensure_crumb_failures() -> None:
    """Verify _ensure_crumb returns None on HTTP error or exception."""
    broker = YahooBroker()

    # Failed crumb status code
    cookie_resp = MagicMock(status_code=200)
    crumb_resp = MagicMock(status_code=500, text="")
    with patch.object(broker.session, "get", side_effect=[cookie_resp, crumb_resp]):
        assert broker._ensure_crumb() is None

    # Exception during request
    with patch.object(
        broker.session, "get", side_effect=requests.RequestException("Fail")
    ):
        assert broker._ensure_crumb() is None


def test_get_symbol_info_success() -> None:
    """Verify get_symbol_info maps quote response to SymbolInfo."""
    broker = YahooBroker()
    broker.crumb = "cached_crumb"

    quote_resp = MagicMock()
    quote_resp.status_code = 200
    quote_resp.json.return_value = {
        "quoteResponse": {
            "result": [
                {
                    "symbol": "AAPL",
                    "shortName": "Apple Inc.",
                    "exchange": "NMS",
                    "currency": "USD",
                    "regularMarketPrice": 230.5,
                    "bid": 230.4,
                    "ask": 230.6,
                }
            ]
        }
    }

    with patch.object(broker.session, "get", return_value=quote_resp) as mock_get:
        resp = broker.get_symbol_info("AAPL")
        assert resp.is_success
        assert resp.data is not None

        info = resp.data
        assert info.name == "AAPL"
        assert info.description == "Apple Inc. (NMS)"
        assert info.exchange == "NMS"
        assert info.currency_base == "USD"
        assert info.last == 230.5
        assert info.bid == 230.4
        assert info.ask == 230.6

        mock_get.assert_called_once()
        _url, kwargs = mock_get.call_args
        assert kwargs["params"]["symbols"] == "AAPL"
        assert kwargs["params"]["crumb"] == "cached_crumb"


def test_get_symbol_info_401_retry_success() -> None:
    """Verify get_symbol_info retries after 401 when acquiring crumb."""
    broker = YahooBroker()
    broker.crumb = None

    resp_401 = MagicMock(status_code=401)
    resp_200 = MagicMock(
        status_code=200,
        json=lambda: {
            "quoteResponse": {
                "result": [
                    {
                        "symbol": "MSFT",
                        "shortName": "Microsoft",
                        "exchange": "NMS",
                    }
                ]
            }
        },
    )

    with patch.object(
        broker.session,
        "get",
        side_effect=[resp_401, resp_200],
    ):
        with patch.object(broker, "_ensure_crumb", side_effect=[None, "new_crumb_xyz"]):
            resp = broker.get_symbol_info("MSFT")
            assert resp.is_success
            assert resp.data is not None
            assert resp.data.name == "MSFT"


def test_get_symbol_info_not_found_and_errors() -> None:
    """Verify get_symbol_info handles missing symbols and HTTP failures."""
    broker = YahooBroker()
    broker.crumb = "crumb"

    # Symbol not found
    empty_resp = MagicMock()
    empty_resp.status_code = 200
    empty_resp.json.return_value = {"quoteResponse": {"result": []}}
    with patch.object(broker.session, "get", return_value=empty_resp):
        resp = broker.get_symbol_info("NONEXISTENT")
        assert not resp.is_success
        assert resp.error is not None
        assert resp.error.code == "SYMBOL_NOT_FOUND"

    # HTTP 500
    err_resp = MagicMock()
    err_resp.status_code = 500
    with patch.object(broker.session, "get", return_value=err_resp):
        resp = broker.get_symbol_info("AAPL")
        assert not resp.is_success
        assert resp.error is not None
        assert resp.error.code == "500"

    # Request exception
    with patch.object(
        broker.session, "get", side_effect=requests.RequestException("Fail")
    ):
        resp = broker.get_symbol_info("AAPL")
        assert not resp.is_success
        assert resp.error is not None
        assert resp.error.code == "REQUEST_ERROR"


def test_map_interval_variations() -> None:
    """Verify _map_interval parses enum, string, and reverse formats."""
    broker = YahooBroker()
    assert broker._map_interval(TimeFrame.D1) == "1d"
    assert broker._map_interval("H1") == "60m"
    assert broker._map_interval("1h") == "1d" or broker._map_interval("60m") == "60m"
    assert broker._map_interval("1D") == "1d"
    assert broker._map_interval("W1") == "1wk"
    assert broker._map_interval("UNKNOWN_TF") == "1d"
