"""Unit tests for YahooBroker plugin with mocked HTTP session."""

from __future__ import annotations

from unittest.mock import MagicMock

from app.plugin.broker import (
    TimeFrame,
    YahooBroker,
)


def test_yahoo_connect_success() -> None:
    """Verify YahooBroker connect when HTTP 200."""
    broker = YahooBroker()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    broker.session.get = MagicMock(return_value=mock_resp)

    res = broker.connect()
    assert res.is_success is True
    assert broker.is_connected().data is True


def test_yahoo_connect_failure() -> None:
    """Verify YahooBroker connect when HTTP error."""
    broker = YahooBroker()
    mock_resp = MagicMock()
    mock_resp.status_code = 500
    broker.session.get = MagicMock(return_value=mock_resp)

    res = broker.connect()
    assert res.is_success is False


def test_yahoo_disconnect() -> None:
    """Verify YahooBroker disconnect sets connected state to False."""
    broker = YahooBroker()
    assert broker.disconnect().is_success is True
    assert broker.is_connected().data is False


def test_yahoo_get_symbol_info() -> None:
    """Verify YahooBroker get_symbol_info parsing."""
    broker = YahooBroker()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "chart": {
            "result": [
                {
                    "meta": {
                        "regularMarketPrice": 150.25,
                        "currency": "USD",
                        "priceHint": 2,
                    }
                }
            ]
        }
    }
    broker.session.get = MagicMock(return_value=mock_resp)

    res = broker.get_symbol_info("AAPL")
    assert res.is_success is True
    assert res.data.name == "AAPL"
    assert res.data.bid == 150.25
    assert res.data.currency_base == "USD"


def test_yahoo_get_symbols_search() -> None:
    """Verify YahooBroker get_symbols query search."""
    broker = YahooBroker()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "quotes": [
            {"symbol": "MSFT", "currency": "USD"},
            {"symbol": "GOOGL", "currency": "USD"},
        ]
    }
    broker.session.get = MagicMock(return_value=mock_resp)

    res = broker.get_symbols(group="TECH")
    assert res.is_success is True
    assert len(res.data) == 2
    assert res.data[0].name == "MSFT"


def test_yahoo_get_symbol_tick() -> None:
    """Verify YahooBroker get_symbol_tick returns quote price."""
    broker = YahooBroker()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "chart": {
            "result": [
                {
                    "meta": {
                        "regularMarketPrice": 180.50,
                    }
                }
            ]
        }
    }
    broker.session.get = MagicMock(return_value=mock_resp)

    res = broker.get_symbol_tick("AAPL")
    assert res.is_success is True
    assert res.data.bid == 180.50


def test_yahoo_get_bars() -> None:
    """Verify YahooBroker get_bars parses candles and timestamps."""
    broker = YahooBroker()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "chart": {
            "result": [
                {
                    "timestamp": [1700000000, 1700003600],
                    "indicators": {
                        "quote": [
                            {
                                "open": [100.0, 101.0],
                                "high": [102.0, 103.0],
                                "low": [99.0, 100.5],
                                "close": [101.0, 102.5],
                                "volume": [1000, 1500],
                            }
                        ]
                    },
                }
            ]
        }
    }
    broker.session.get = MagicMock(return_value=mock_resp)

    res = broker.get_bars("AAPL", timeframe=TimeFrame.H1, count=2)
    assert res.is_success is True
    assert len(res.data) == 2
    assert res.data[0].open == 100.0
    assert res.data[1].close == 102.5
