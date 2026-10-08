"""Unit tests for Binance cryptocurrency market data and symbol catalog plugin."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock, patch

import requests
from app.plugins.brokers.contracts import (
    BrokerCapability,
    TimeFrame,
    TradeRequest,
)
from app.plugins.brokers.crypto import (
    BINANCE_FUTURES_COIN_BASE_URL,
    BINANCE_FUTURES_USDT_BASE_URL,
    BINANCE_SPOT_BASE_URL,
    PLUGIN_MANIFEST,
    BinanceBroker,
    _calc_digits,
    _map_timeframe,
    create_adapter,
)


def test_crypto_plugin_manifest_and_capabilities() -> None:
    """Verify plugin manifest metadata and broker capability flags."""
    broker = create_adapter()
    assert isinstance(broker, BinanceBroker)
    assert broker.has_capability(BrokerCapability.MARKET_DATA)
    assert broker.has_capability(BrokerCapability.SYMBOLS)
    assert not broker.has_capability(BrokerCapability.TRADING)
    assert not broker.has_capability(BrokerCapability.ORDERS)

    assert PLUGIN_MANIFEST["id"] == "broker-binance"
    assert PLUGIN_MANIFEST["name"] == "Binance Crypto Connector"
    assert "bars" in PLUGIN_MANIFEST["capabilities"]
    assert "ticks" in PLUGIN_MANIFEST["capabilities"]
    assert "symbols" in PLUGIN_MANIFEST["capabilities"]
    assert PLUGIN_MANIFEST["metadata"]["provider_name"] == "Binance"


def test_map_timeframe_mappings() -> None:
    """Verify mapping of TimeFrame enum, strings, and integers to Binance intervals."""
    assert _map_timeframe(TimeFrame.M1) == "1m"
    assert _map_timeframe(TimeFrame.M5) == "5m"
    assert _map_timeframe(TimeFrame.H1) == "1h"
    assert _map_timeframe(TimeFrame.D1) == "1d"
    assert _map_timeframe("M15") == "15m"
    assert _map_timeframe("1h") == "1h"
    assert _map_timeframe("60") == "1h"
    assert _map_timeframe(240) == "4h"
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
    assert spot._normalize_symbol("BTCUSD") == "BTCUSDT"  # Normalized to USDT on spot

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
        resp1 = broker.get_symbol_info("BTC/USDT")
        assert resp1.is_success
        assert resp1.data is not None
        assert resp1.data.name == "BTCUSDT"
        assert resp1.data.digits == 2
        assert resp1.data.point == 0.01
        assert resp1.data.currency_base == "BTC"
        assert resp1.data.currency_profit == "USDT"
        assert resp1.data.trade_contract_size == 0.00001
        assert mock_get.call_count == 1

        # Second call: served from memory cache
        resp2 = broker.get_symbol_info("BTCUSDT")
        assert resp2.is_success
        assert resp2.data is not None
        assert resp2.data.name == "BTCUSDT"
        assert mock_get.call_count == 1  # Not called again


def test_get_symbol_info_not_found_and_request_error() -> None:
    """Verify get_symbol_info returns structured failure for 404 or network errors."""
    broker = BinanceBroker(venue="spot")

    # 1. 400 / Not Found
    mock_not_found = MagicMock()
    mock_not_found.status_code = 400
    mock_not_found.text = '{"code":-1121,"msg":"Invalid symbol."}'
    with patch.object(broker.session, "get", return_value=mock_not_found):
        resp = broker.get_symbol_info("INVALID_COIN")
        assert not resp.is_success
        assert resp.error is not None
        assert resp.error.code == "SYMBOL_NOT_FOUND"

    # 2. Network exception
    with patch.object(
        broker.session, "get", side_effect=requests.RequestException("DNS failure")
    ):
        resp_err = broker.get_symbol_info("ETHUSDT")
        assert not resp_err.is_success
        assert resp_err.error is not None
        assert resp_err.error.code == "REQUEST_ERROR"


def test_get_symbols_and_count() -> None:
    """Verify loading full catalog, catalog count, and group filtering."""
    broker = BinanceBroker(venue="spot")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = MOCK_EXCHANGE_INFO_ALL

    with patch.object(broker.session, "get", return_value=mock_resp):
        # 1. Num of symbols
        count_resp = broker.get_num_of_symbols()
        assert count_resp.is_success
        assert count_resp.data == 3

        # 2. All symbols
        all_syms = broker.get_symbols()
        assert all_syms.is_success
        assert all_syms.data is not None
        assert len(all_syms.data) == 3

        # 3. Filter by quote currency / group 'USDT'
        usdt_syms = broker.get_symbols(group="USDT")
        assert usdt_syms.is_success
        assert usdt_syms.data is not None
        assert len(usdt_syms.data) == 2
        assert {s.name for s in usdt_syms.data} == {"BTCUSDT", "ETHUSDT"}

        # 4. Filter by quote currency / group 'BTC'
        btc_syms = broker.get_symbols(group="BTC")
        assert btc_syms.is_success
        assert btc_syms.data is not None
        assert len(btc_syms.data) == 1
        assert btc_syms.data[0].name == "ETHBTC"


def test_ensure_exchange_info_error_handling() -> None:
    """Verify _ensure_exchange_info handles HTTP errors and exceptions gracefully."""
    broker = BinanceBroker(venue="spot")

    # Status error
    mock_err = MagicMock()
    mock_err.status_code = 500
    mock_err.text = "Internal Server Error"
    with patch.object(broker.session, "get", return_value=mock_err):
        broker._ensure_exchange_info()
        assert not broker._exchange_info_loaded

    # Exception
    with patch.object(
        broker.session, "get", side_effect=requests.RequestException("Timeout")
    ):
        broker._ensure_exchange_info()
        assert not broker._exchange_info_loaded


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


def test_get_bars_success_and_time_filtering() -> None:
    """Verify parsing klines into canonical Bar records with timestamp filters."""
    broker = BinanceBroker(venue="spot")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = MOCK_RAW_KLINES

    d_from = datetime(2023, 10, 1, 0, 0, tzinfo=UTC)
    d_to = datetime(2023, 10, 1, 0, 5, tzinfo=UTC)

    with patch.object(broker.session, "get", return_value=mock_resp) as mock_get:
        resp = broker.get_bars(
            symbol="BTCUSDT",
            timeframe=TimeFrame.M1,
            count=10,
            date_from=d_from,
            date_to=d_to,
        )
        assert resp.is_success
        assert resp.data is not None
        assert len(resp.data) == 2

        bar0 = resp.data[0]
        assert bar0.open == 27000.00
        assert bar0.high == 27100.50
        assert bar0.low == 26950.00
        assert bar0.close == 27050.25
        assert bar0.tick_volume == 123
        assert bar0.time == datetime.fromtimestamp(1696118400, tz=UTC)

        # Verify query params passed to API
        _, kwargs = mock_get.call_args
        params = kwargs.get("params", {})
        assert params["symbol"] == "BTCUSDT"
        assert params["interval"] == "1m"
        assert params["limit"] == 10
        assert params["startTime"] == int(d_from.timestamp() * 1000)
        assert params["endTime"] == int(d_to.timestamp() * 1000)


def test_get_bars_errors() -> None:
    """Verify get_bars handles HTTP status failure and connection errors."""
    broker = BinanceBroker(venue="spot")

    # 1. HTTP 400
    mock_err = MagicMock()
    mock_err.status_code = 400
    mock_err.text = "Bad Request"
    with patch.object(broker.session, "get", return_value=mock_err):
        resp = broker.get_bars("BTCUSDT")
        assert not resp.is_success
        assert resp.error is not None
        assert resp.error.code == "400"

    # 2. Exception
    with patch.object(
        broker.session, "get", side_effect=requests.RequestException("Connection error")
    ):
        resp_exc = broker.get_bars("BTCUSDT")
        assert not resp_exc.is_success
        assert resp_exc.error is not None
        assert resp_exc.error.code == "KLINE_ERROR"


MOCK_RAW_TRADES: list[dict[str, Any]] = [
    {
        "id": 1001,
        "price": "27055.50",
        "qty": "0.15000000",
        "quoteQty": "4058.325",
        "time": 1696118430000,
        "isBuyerMaker": True,
        "isBestMatch": True,
    },
    {
        "id": 1002,
        "price": "27056.00",
        "qty": "0.25000000",
        "quoteQty": "6764.000",
        "time": 1696118435000,
        "isBuyerMaker": False,
        "isBestMatch": True,
    },
]


def test_get_ticks_success() -> None:
    """Verify parsing trades into canonical Tick records."""
    broker = BinanceBroker(venue="spot")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = MOCK_RAW_TRADES

    with patch.object(broker.session, "get", return_value=mock_resp):
        resp = broker.get_ticks(symbol="BTC/USDT", count=2)
        assert resp.is_success
        assert resp.data is not None
        assert len(resp.data) == 2

        t0 = resp.data[0]
        assert t0.bid == 27055.50
        assert t0.ask == 27055.50
        assert t0.last == 27055.50
        assert t0.volume == 0.15
        assert t0.time == datetime.fromtimestamp(1696118430, tz=UTC)


def test_get_ticks_errors() -> None:
    """Verify get_ticks handles HTTP status failure and connection errors."""
    broker = BinanceBroker(venue="spot")

    # 1. HTTP 500
    mock_err = MagicMock()
    mock_err.status_code = 500
    mock_err.text = "Internal Server Error"
    with patch.object(broker.session, "get", return_value=mock_err):
        resp = broker.get_ticks("BTCUSDT")
        assert not resp.is_success
        assert resp.error is not None
        assert resp.error.code == "500"

    # 2. Exception
    with patch.object(
        broker.session, "get", side_effect=requests.RequestException("Network down")
    ):
        resp_exc = broker.get_ticks("BTCUSDT")
        assert not resp_exc.is_success
        assert resp_exc.error is not None
        assert resp_exc.error.code == "TRADES_ERROR"


def test_unsupported_broker_capabilities() -> None:
    """Verify non-market-data methods cleanly fail with CAPABILITY_NOT_SUPPORTED."""
    broker = create_adapter()

    # Trading
    trade_resp = broker.trade(TradeRequest(symbol="BTCUSDT", volume=1.0))
    assert not trade_resp.is_success
    assert trade_resp.error is not None
    assert trade_resp.error.code == "CAPABILITY_NOT_SUPPORTED"
    assert "trading capabilities" in trade_resp.message

    # Order check
    order_resp = broker.check_order(TradeRequest(symbol="BTCUSDT", volume=1.0))
    assert not order_resp.is_success
    assert order_resp.error is not None
    assert order_resp.error.code == "CAPABILITY_NOT_SUPPORTED"

    # Connection lifecycle
    assert not broker.is_connected()
    conn_resp = broker.connect()
    assert not conn_resp.is_success
    assert conn_resp.error is not None
    assert conn_resp.error.code == "CAPABILITY_NOT_SUPPORTED"

    disc_resp = broker.disconnect()
    assert not disc_resp.is_success
    assert disc_resp.error is not None
    assert disc_resp.error.code == "CAPABILITY_NOT_SUPPORTED"
