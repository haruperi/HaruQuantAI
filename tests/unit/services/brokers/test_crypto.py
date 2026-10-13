"""Unit tests for Binance cryptocurrency market data and symbol catalog broker."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from app.services.brokers._base_data import DataBrokerBackend
from app.services.brokers.contracts import (
    BridgeError,
    MarketBar,
    MarketTick,
    SymbolSnapshot,
    Timeframe,
)
from app.services.brokers.crypto import (
    BINANCE_FUTURES_COIN_BASE_URL,
    BINANCE_FUTURES_USDT_BASE_URL,
    BINANCE_SPOT_BASE_URL,
    BinanceBroker,
    _calc_digits,
    _map_timeframe,
    create_adapter,
)
from app.services.libs.data import get_historical_bars, get_ticks


def test_crypto_adapter_and_protocol() -> None:
    """Verify BinanceBroker creates adapter and inherits DataBrokerBackend."""
    broker = create_adapter()
    assert isinstance(broker, BinanceBroker)
    assert isinstance(broker, DataBrokerBackend)
    assert broker.name == "Binance"


def test_map_timeframe_mappings() -> None:
    """Verify mapping of timeframe strings to Binance intervals."""
    assert _map_timeframe("M1") == "1m"
    assert _map_timeframe("M5") == "5m"
    assert _map_timeframe("H1") == "1h"
    assert _map_timeframe("D1") == "1d"
    assert _map_timeframe("M15") == "15m"
    assert _map_timeframe("1h") == "1h"
    assert _map_timeframe("UNKNOWN_TF") == "1m"


def test_calc_digits() -> None:
    """Verify calculation of decimal digits precision from tick size."""
    assert _calc_digits(0.01) == 2
    assert _calc_digits(0.0001) == 4
    assert _calc_digits(0.00000001) == 8
    assert _calc_digits(0.5) == 1
    assert _calc_digits(1.0) == 0
    assert _calc_digits(5.0) == 0
    assert _calc_digits(0.0) == 0
    assert _calc_digits(-0.01) == 0


def test_venue_routing_and_symbol_normalization() -> None:
    """Verify base URL and API prefix selection across Spot, USDT-M, and Coin-M venues."""
    # Spot
    spot = BinanceBroker(venue="spot", api_key="test_key")
    assert spot.base_url == BINANCE_SPOT_BASE_URL
    assert spot.api_prefix == "/api/v3"
    assert spot.session.headers.get("X-MBX-APIKEY") == "test_key"
    assert spot._normalize_symbol("BTC/USDT") == "BTCUSDT"
    assert spot._normalize_symbol("eth_usdt") == "ETHUSDT"
    assert spot._normalize_symbol("BTCUSD") == "BTCUSD"

    # USDT-M Futures
    usdt_m = BinanceBroker(venue="usdt-m")
    assert usdt_m.base_url == BINANCE_FUTURES_USDT_BASE_URL
    assert usdt_m.api_prefix == "/fapi/v1"

    # Coin-M Futures
    coin_m = BinanceBroker(venue="coin-m")
    assert coin_m.base_url == BINANCE_FUTURES_COIN_BASE_URL
    assert coin_m.api_prefix == "/dapi/v1"
    assert coin_m._normalize_symbol("BTCUSD_PERP") == "BTCUSDPERP"


MOCK_EXCHANGE_INFO_BTC: dict[str, Any] = {
    "symbols": [
        {
            "symbol": "BTCUSDT",
            "status": "TRADING",
            "baseAsset": "BTC",
            "quoteAsset": "USDT",
            "filters": [
                {"filterType": "PRICE_FILTER", "tickSize": "0.01000000"},
                {"filterType": "LOT_SIZE", "stepSize": "0.00001000"},
            ],
        }
    ]
}

MOCK_EXCHANGE_INFO_ALL: dict[str, Any] = {
    "symbols": [
        {
            "symbol": "BTCUSDT",
            "status": "TRADING",
            "baseAsset": "BTC",
            "quoteAsset": "USDT",
            "filters": [
                {"filterType": "PRICE_FILTER", "tickSize": "0.01000000"},
                {"filterType": "LOT_SIZE", "stepSize": "0.00001000"},
            ],
        },
        {
            "symbol": "ETHUSDT",
            "status": "TRADING",
            "baseAsset": "ETH",
            "quoteAsset": "USDT",
            "filters": [
                {"filterType": "PRICE_FILTER", "tickSize": "0.01000000"},
                {"filterType": "LOT_SIZE", "stepSize": "0.00010000"},
            ],
        },
        {
            "symbol": "ETHBTC",
            "status": "TRADING",
            "baseAsset": "ETH",
            "quoteAsset": "BTC",
            "filters": [
                {"filterType": "PRICE_FILTER", "tickSize": "0.00000100"},
                {"filterType": "LOT_SIZE", "stepSize": "0.00100000"},
            ],
        },
    ]
}


def test_get_symbol_info_success_and_caching() -> None:
    """Verify symbol_info resolution from single-symbol exchangeInfo query and in-memory cache."""
    broker = BinanceBroker(venue="spot")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = MOCK_EXCHANGE_INFO_BTC

    with patch.object(broker.session, "get", return_value=mock_resp) as mock_get:
        # First call: fetched via API
        snap1 = broker.symbol_info("BTC/USDT")
        assert isinstance(snap1, SymbolSnapshot)
        assert snap1.name == "BTCUSDT"
        assert snap1.digits == 2
        assert snap1.point == 0.01
        assert snap1.currency_base == "BTC"
        assert snap1.currency_profit == "USDT"
        assert snap1.trade_contract_size == 0.00001
        assert mock_get.call_count == 1

        # Second call: served from memory cache
        snap2 = broker.symbol_info("BTCUSDT")
        assert isinstance(snap2, SymbolSnapshot)
        assert snap2.name == "BTCUSDT"
        assert mock_get.call_count == 1


def test_symbol_info_fallback_on_error() -> None:
    """Verify symbol_info returns default snapshot when request fails."""
    broker = BinanceBroker(venue="spot")

    mock_err = MagicMock(status_code=500)
    with patch.object(broker.session, "get", return_value=mock_err):
        snap = broker.symbol_info("UNKNOWN_SYM")
        assert isinstance(snap, SymbolSnapshot)
        assert snap.name == "UNKNOWNSYM"


def test_symbols_get() -> None:
    """Verify symbols_get returns registered symbols."""
    broker = BinanceBroker(venue="spot")
    symbols = broker.symbols_get()
    assert "BTCUSDT" in symbols
    assert "ETHUSDT" in symbols


MOCK_RAW_KLINES: list[list[Any]] = [
    [
        1696118400000,  # openTime (2023-10-01 00:00:00 UTC)
        "27000.00",  # open
        "27100.50",  # high
        "26950.00",  # low
        "27050.25",  # close
        "123.456",  # volume
        1696118459999,  # closeTime
        "3335000.00",  # quoteAssetVolume
        1500,  # numberOfTrades
        "60.00",  # takerBuyBaseAssetVolume
        "1620000.00",  # takerBuyQuoteAssetVolume
        "0",  # ignore
    ],
    [
        1696118460000,  # openTime (2023-10-01 00:01:00 UTC)
        "27050.25",
        "27150.00",
        "27020.00",
        "27120.00",
        "98.765",
        1696118519999,
        "2670000.00",
        1200,
        "45.00",
        "1220000.00",
        "0",
    ],
]


def test_fetch_bars_success() -> None:
    """Verify parsing klines into bar dicts."""
    broker = BinanceBroker(venue="spot")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = MOCK_RAW_KLINES

    d_from = int(datetime(2023, 10, 1, 0, 0, tzinfo=UTC).timestamp())
    d_to = int(datetime(2023, 10, 1, 0, 5, tzinfo=UTC).timestamp())

    with patch.object(broker.session, "get", return_value=mock_resp) as mock_get:
        bars = broker.fetch_bars(
            symbol="BTCUSDT",
            timeframe="M1",
            mode="range",
            start=d_from,
            end=d_to,
            count=10,
            limit=10,
        )

        assert len(bars) == 2
        assert bars[0]["open"] == 27000.00
        assert bars[0]["high"] == 27100.50
        assert bars[0]["low"] == 26950.00
        assert bars[0]["close"] == 27050.25
        assert bars[0]["time"] == 1696118400

        mock_get.assert_called_once()
        params = mock_get.call_args[1]["params"]
        assert params["symbol"] == "BTCUSDT"
        assert params["interval"] == "1m"
        assert params["startTime"] == d_from * 1000
        assert params["endTime"] == d_to * 1000


def test_fetch_bars_via_data_lib() -> None:
    """Verify get_historical_bars works with BinanceBroker."""
    broker = BinanceBroker(venue="spot")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = MOCK_RAW_KLINES

    async def scenario() -> None:
        with patch.object(broker.session, "get", return_value=mock_resp):
            bars = await get_historical_bars(
                broker, "BTCUSDT", Timeframe.PERIOD_M1, count=2
            )
            assert len(bars) == 2
            assert isinstance(bars[0], MarketBar)
            assert bars[0].close == 27050.25

    asyncio.run(scenario())


MOCK_RAW_TRADES: list[dict[str, Any]] = [
    {
        "id": 28457,
        "price": "27000.50",
        "qty": "1.234",
        "quoteQty": "33318.617",
        "time": 1696118400123,
        "isBuyerMaker": True,
        "isBestMatch": True,
    },
    {
        "id": 28458,
        "price": "27001.00",
        "qty": "0.500",
        "quoteQty": "13500.50",
        "time": 1696118400456,
        "isBuyerMaker": False,
        "isBestMatch": True,
    },
]


def test_fetch_ticks_success() -> None:
    """Verify fetch_ticks returns correctly formatted tick records."""
    broker = BinanceBroker(venue="spot")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = MOCK_RAW_TRADES

    with patch.object(broker.session, "get", return_value=mock_resp):
        ticks = broker.fetch_ticks(
            symbol="BTCUSDT",
            count=2,
            limit=2,
        )

        assert len(ticks) == 2
        assert ticks[0]["bid"] == 27000.50
        assert ticks[0]["ask"] == 27000.50
        assert ticks[0]["time_msc"] == 1696118400123
        assert ticks[0]["volume_real"] == 1.234


def test_fetch_ticks_via_data_lib() -> None:
    """Verify get_ticks works with BinanceBroker."""
    broker = BinanceBroker(venue="spot")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = MOCK_RAW_TRADES

    async def scenario() -> None:
        with patch.object(broker.session, "get", return_value=mock_resp):
            ticks = await get_ticks(broker, "BTCUSDT", count=2)
            assert len(ticks) == 2
            assert isinstance(ticks[0], MarketTick)
            assert ticks[0].bid == 27000.50

    asyncio.run(scenario())


def test_error_handling_raises_bridge_error() -> None:
    """Verify HTTP errors raise BridgeError with REMOTE_ERROR code."""
    broker = BinanceBroker(venue="spot")

    err_resp = MagicMock(status_code=500, text="Internal Server Error")
    with patch.object(broker.session, "get", return_value=err_resp):
        with pytest.raises(BridgeError) as exc_info:
            broker.fetch_bars(
                symbol="BTCUSDT",
                timeframe="M1",
                mode="count",
                start=0,
                end=0,
                count=5,
                limit=5,
            )
        assert exc_info.value.code == "REMOTE_ERROR"
