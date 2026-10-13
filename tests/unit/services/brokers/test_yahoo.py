"""Unit tests for Yahoo Finance market data and symbol metadata broker."""

import asyncio
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
import requests
from app.services.brokers._base_data import DataBrokerBackend
from app.services.brokers.contracts import (
    BridgeError,
    MarketBar,
    SymbolSnapshot,
    Timeframe,
)
from app.services.brokers.yahoo import (
    YahooBroker,
    create_adapter,
)


def test_yahoo_adapter_and_protocol() -> None:
    """Verify YahooBroker creates adapter and inherits DataBrokerBackend."""
    broker = create_adapter()
    assert isinstance(broker, YahooBroker)
    assert isinstance(broker, DataBrokerBackend)
    assert broker.name == "Yahoo"


def test_fetch_bars_events_history_parameter() -> None:
    """Verify fetch_bars includes events=history in request parameters."""
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

    start_ts = int(datetime(2026, 4, 1, tzinfo=UTC).timestamp())
    end_ts = int(datetime(2026, 4, 10, tzinfo=UTC).timestamp())

    with patch.object(broker.session, "get", return_value=mock_resp) as mock_get:
        bars = broker.fetch_bars(
            symbol="AAPL",
            timeframe="D1",
            mode="range",
            start=start_ts,
            end=end_ts,
            count=0,
            limit=0,
        )

        assert len(bars) == 1
        bar = bars[0]
        assert bar["open"] == 100.0
        assert bar["high"] == 105.0
        assert bar["low"] == 99.0
        assert bar["close"] == 104.0
        assert bar["tick_volume"] == 1000

        mock_get.assert_called_once()
        _url, kwargs = mock_get.call_args
        assert kwargs["params"]["events"] == "history"
        assert kwargs["params"]["interval"] == "1d"
        assert kwargs["params"]["period1"] == start_ts
        assert kwargs["params"]["period2"] == end_ts


def test_fetch_bars_via_call_contract() -> None:
    """Verify call('MarketData.Bars') returns typed MarketBar instances."""
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
                                "open": [150.0],
                                "high": [155.0],
                                "low": [149.0],
                                "close": [154.0],
                                "volume": [5000],
                            }
                        ]
                    },
                }
            ]
        }
    }

    async def scenario() -> None:
        from app.services.libs.data import get_historical_bars

        with patch.object(broker.session, "get", return_value=mock_resp):
            res = await get_historical_bars(
                broker, "AAPL", Timeframe.PERIOD_D1, count=1
            )
            assert isinstance(res, list)
            assert len(res) == 1
            assert isinstance(res[0], MarketBar)
            assert res[0].close == 154.0

    asyncio.run(scenario())


def test_fetch_bars_error_handling() -> None:
    """Verify fetch_bars raises BridgeError on HTTP errors and empty results."""
    broker = YahooBroker()

    # HTTP 500
    err_resp = MagicMock()
    err_resp.status_code = 500
    with patch.object(broker.session, "get", return_value=err_resp):
        with pytest.raises(BridgeError) as exc_info:
            broker.fetch_bars(
                symbol="AAPL",
                timeframe="D1",
                mode="count",
                start=0,
                end=0,
                count=5,
                limit=5,
            )
        assert exc_info.value.code == "REMOTE_ERROR"

    # Empty result
    empty_resp = MagicMock()
    empty_resp.status_code = 200
    empty_resp.json.return_value = {"chart": {"result": []}}
    with patch.object(broker.session, "get", return_value=empty_resp):
        with pytest.raises(BridgeError) as exc_info:
            broker.fetch_bars(
                symbol="AAPL",
                timeframe="D1",
                mode="count",
                start=0,
                end=0,
                count=5,
                limit=5,
            )
        assert exc_info.value.code in ("NO_DATA", "SYMBOL_NOT_FOUND")

    # Network Exception
    with patch.object(
        broker.session, "get", side_effect=requests.RequestException("Boom")
    ):
        with pytest.raises(BridgeError) as exc_info:
            broker.fetch_bars(
                symbol="AAPL",
                timeframe="D1",
                mode="count",
                start=0,
                end=0,
                count=5,
                limit=5,
            )
        assert exc_info.value.code == "DOWNLOAD_ERROR"


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


def test_symbol_info_success() -> None:
    """Verify symbol_info maps quote response to SymbolSnapshot."""
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
        info = broker.symbol_info("AAPL")
        assert isinstance(info, SymbolSnapshot)
        assert info.name == "AAPL"
        assert info.bid == 230.4
        assert info.ask == 230.6
        assert info.last == 230.5

        mock_get.assert_called_once()
        _url, kwargs = mock_get.call_args
        assert kwargs["params"]["symbols"] == "AAPL"
        assert kwargs["params"]["crumb"] == "cached_crumb"


def test_symbols_get() -> None:
    """Verify symbols_get returns registered default symbols."""
    broker = YahooBroker()
    symbols = broker.symbols_get()
    assert "AAPL" in symbols
    assert "MSFT" in symbols


def test_map_interval_variations() -> None:
    """Verify _map_interval parses string variations."""
    broker = YahooBroker()
    assert broker._map_interval("D1") == "1d"
    assert broker._map_interval("H1") == "60m"
    assert broker._map_interval("M1") == "1m"
    assert broker._map_interval("1d") == "1d"
    assert broker._map_interval("W1") == "1wk"
    assert broker._map_interval("MN1") == "1mo"
    assert broker._map_interval("UNKNOWN_TF") == "1d"
