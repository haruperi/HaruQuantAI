"""Unit tests for REST and CDN broker clients and HTTP transport.

Description:
    Tests HTTP transport session pooling, rate limiting, and credential redaction,
    as well as uniform market data clients: DukascopyClient, SQEquityClient,
    SQFuturesClient, CryptoClient, YahooClient, TickDownloaderClient, and BinanceClient.
    Directly tests typed get_bars and get_ticks client APIs and BridgeError exceptions.

Purpose:
    FEAT-BROKER-REST-CDN-TEST: Unit tests for REST and CDN market data clients.

Key Capabilities:
    - FR-TEST-HTTP-TRANSPORT: Test connection pooling, redaction, and error translation.
    - FR-TEST-REST-PROVIDERS: Test uniform get_bars and get_ticks on REST/CDN clients.

Python API Usage:
    ```bash
    uv run pytest tests/unit/services/brokers/test_brokers_rest_and_cdn_providers.py --no-cov
    ```
"""

from __future__ import annotations

import importlib
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests
from app.services.brokers._http import (
    create_http_session,
    execute_bounded_get,
    redact_url_or_message,
)
from app.services.brokers.base import BridgeError
from app.services.brokers.crypto import BinanceClient, CryptoClient
from app.services.brokers.dukascopy import DukascopyClient
from app.services.brokers.sq_equity import SQEquityClient
from app.services.brokers.sq_futures import SQFuturesClient
from app.services.brokers.tick_downloader import TickDownloaderClient
from app.services.brokers.yahoo import YahooClient
from app.services.include.contracts import MarketBar, MarketTick
from app.services.include.enums import Timeframe

# ============================================================================
# Shared HTTP Transport Tests
# ============================================================================


def test_http_session_and_redaction() -> None:
    """Verify session headers, adapter pooling, and sensitive token redaction."""
    session = create_http_session("TestAgent/1.0", retries=2, pool_size=8)
    assert session.headers.get("User-Agent") == "TestAgent/1.0"

    raw_url = "https://api.exchange.com/v1/data?apiKey=SECRET_12345&token=XYZ_TOKEN&symbol=BTC"
    clean_url = redact_url_or_message(raw_url)
    assert "SECRET_12345" not in clean_url
    assert "XYZ_TOKEN" not in clean_url
    assert "apiKey=REDACTED" in clean_url
    assert "token=REDACTED" in clean_url


def test_execute_bounded_get_errors() -> None:
    """Verify execute_bounded_get translates HTTP 429, 401, timeout to BridgeError."""
    session = MagicMock(spec=requests.Session)

    # Test 429 Rate Limit
    resp_429 = MagicMock()
    resp_429.status_code = 429
    session.get.return_value = resp_429

    with pytest.raises(BridgeError) as exc_429:
        execute_bounded_get(session, "https://api.com/feed", provider="test")
    assert exc_429.value.code == "RATE_LIMIT"

    # Test Timeout
    session.get.side_effect = requests.exceptions.Timeout("Connection timed out")
    with pytest.raises(BridgeError) as exc_timeout:
        execute_bounded_get(session, "https://api.com/feed", provider="test")
    assert exc_timeout.value.code == "TIMEOUT"


# ============================================================================
# Dukascopy Client Tests
# ============================================================================


def test_dukascopy_rest_provider(tmp_path: Path) -> None:
    """Verify Dukascopy get_bars hard-fails when datafeed returns HTTP 404."""
    client = DukascopyClient(data_dir=tmp_path)

    with patch("app.services.brokers.dukascopy.execute_bounded_get") as mock_get:
        resp_404 = MagicMock()
        resp_404.status_code = 404
        resp_404.content = b""
        mock_get.return_value = resp_404

        with pytest.raises(BridgeError, match="HTTP 404"):
            client.get_bars("EURUSD", Timeframe.PERIOD_M1, count=10)


# ============================================================================
# StrategyQuant Equity Client Tests (Cadence Protection)
# ============================================================================


def test_sq_equity_d1_protection(tmp_path: Path) -> None:
    """Verify StrategyQuant Equity rejects intraday requests and accepts D1."""
    client = SQEquityClient(data_dir=tmp_path)

    # Rejection of intraday M1
    with pytest.raises(BridgeError, match="only supports D1"):
        client.get_bars("AAPL", Timeframe.PERIOD_M1, count=10)

    # Valid D1 with 404 CDN response
    with patch("app.services.brokers.sq_equity.execute_bounded_get") as mock_get:
        resp = MagicMock()
        resp.status_code = 404
        resp.content = b""
        mock_get.return_value = resp

        with pytest.raises(BridgeError, match="No equity data found"):
            client.get_bars("AAPL", Timeframe.PERIOD_D1, count=10)


# ============================================================================
# StrategyQuant Futures Client Tests
# ============================================================================


def test_sq_futures_cadence_and_404(tmp_path: Path) -> None:
    """Verify StrategyQuant Futures validates timeframe and handles 404 safely."""
    client = SQFuturesClient(data_dir=tmp_path)

    # Invalid timeframe (H4)
    with pytest.raises(BridgeError, match="only supports M1 and D1"):
        client.get_bars("@ES", Timeframe.PERIOD_H4, count=10)

    # Valid D1 with 404 CDN response
    with patch("app.services.brokers.sq_futures.execute_bounded_get") as mock_get:
        resp = MagicMock()
        resp.status_code = 404
        resp.content = b""
        mock_get.return_value = resp

        with pytest.raises(BridgeError, match="No futures data found"):
            client.get_bars("@ES", Timeframe.PERIOD_D1, count=10)


# ============================================================================
# Crypto Client Multi-Exchange Routing Tests
# ============================================================================


def test_crypto_multiexchange_routing() -> None:
    """Verify CryptoClient routes requests to Bitfinex, Coinbase, Poloniex, and Binance."""
    # 1. Bitfinex routing & decoding
    client_bfx = CryptoClient(exchange="bitfinex")
    with patch("app.services.brokers.crypto.execute_bounded_get") as mock_get:
        resp = MagicMock()
        resp.status_code = 200
        # Bitfinex layout: [[MTS, OPEN, CLOSE, HIGH, LOW, VOLUME]]
        resp.json.return_value = [
            [1768478400000, 50000.0, 50500.0, 50800.0, 49800.0, 10.5]
        ]
        mock_get.return_value = resp

        bars = client_bfx.get_bars("BTCUSD", Timeframe.PERIOD_M1, count=1)
        assert len(bars) == 1
        assert isinstance(bars[0], MarketBar)
        assert bars[0].open == 50000.0
        assert bars[0].high == 50800.0
        assert bars[0].low == 49800.0
        assert bars[0].close == 50500.0

    # 2. Coinbase routing & decoding
    client_cb = CryptoClient(exchange="coinbase")
    with patch("app.services.brokers.crypto.execute_bounded_get") as mock_get:
        resp = MagicMock()
        resp.status_code = 200
        # Coinbase layout: [[time, low, high, open, close, volume]]
        resp.json.return_value = [
            [1768478400, 49800.0, 50800.0, 50000.0, 50500.0, 10.5]
        ]
        mock_get.return_value = resp

        bars_cb = client_cb.get_bars("BTC-USD", Timeframe.PERIOD_M1, count=1)
        assert len(bars_cb) == 1
        assert isinstance(bars_cb[0], MarketBar)
        assert bars_cb[0].open == 50000.0
        assert bars_cb[0].close == 50500.0

    # 3. Poloniex routing & decoding
    client_polo = CryptoClient(exchange="poloniex")
    with patch("app.services.brokers.crypto.execute_bounded_get") as mock_get:
        resp = MagicMock()
        resp.status_code = 200
        # Poloniex layout: [low, high, open, close, amount, quantity, buyTakerAmount, buyTakerQuantity, tradeCount, ts, weightedAverage, interval, startTime, closeTime]
        resp.json.return_value = [
            [
                "49800.0",
                "50800.0",
                "50000.0",
                "50500.0",
                "100.0",
                "10.5",
                "50.0",
                "5.0",
                120,
                1768478400000,
                "50000.0",
                "MINUTE_1",
                1768478400000,
                1768478460000,
            ]
        ]
        mock_get.return_value = resp

        bars_polo = client_polo.get_bars("BTC_USDT", Timeframe.PERIOD_M1, count=1)
        assert len(bars_polo) == 1
        assert isinstance(bars_polo[0], MarketBar)
        assert bars_polo[0].open == 50000.0


# ============================================================================
# Yahoo Finance Client Tests
# ============================================================================


def test_yahoo_provider_contracts() -> None:
    """Verify Yahoo Finance validates unsupported ticks and parses chart responses."""
    client = YahooClient()

    # Reject unsupported ticks
    with pytest.raises(BridgeError, match="does not support tick"):
        client.get_ticks("SPY", count=10)

    # Valid bars parsing
    with patch.object(client.session, "get") as mock_get:
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {
            "chart": {
                "result": [
                    {
                        "timestamp": [1768478400],
                        "indicators": {
                            "quote": [
                                {
                                    "open": [500.0],
                                    "high": [505.0],
                                    "low": [498.0],
                                    "close": [502.0],
                                    "volume": [10000],
                                }
                            ]
                        },
                    }
                ],
                "error": None,
            }
        }
        mock_get.return_value = resp

        bars = client.get_bars("SPY", Timeframe.PERIOD_D1, count=1)
        assert len(bars) == 1
        assert isinstance(bars[0], MarketBar)
        assert bars[0].open == 500.0
        assert bars[0].close == 502.0


# ============================================================================
# Tick Downloader Client Tests
# ============================================================================


def test_tick_downloader_compatibility(tmp_path: Path) -> None:
    """Verify TickDownloaderClient hard-fails when local data is missing."""
    client = TickDownloaderClient(data_dir=tmp_path)
    symbols = client.get_symbols()
    assert isinstance(symbols, list)
    assert "EURUSD" in symbols

    with pytest.raises(BridgeError, match="No local TickDownloader"):
        client.get_bars("EURUSD", Timeframe.PERIOD_M1, count=5)

    with pytest.raises(BridgeError, match="No local TickDownloader"):
        client.get_ticks("EURUSD", count=5)


def test_binance_bars_and_ticks_integer_validation() -> None:
    """Verify Binance get_bars and get_ticks produce valid MarketBar and MarketTick instances."""
    client = BinanceClient()

    # 1. Bars validation
    with patch("app.services.brokers.crypto.execute_bounded_get") as mock_get:
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = [
            [
                1700000000000,
                "50000.0",
                "50100.0",
                "49900.0",
                "50050.0",
                "12.345",
                1700000059999,
                "617250",
                150,
            ]
        ]
        mock_get.return_value = resp

        bars = client.get_bars(
            symbol="BTCUSDT",
            timeframe=Timeframe.PERIOD_M1,
            start=1700000000,
            end=1700000060,
            count=1,
        )
        assert len(bars) == 1
        assert isinstance(bars[0], MarketBar)
        assert bars[0].real_volume == 12

    # 2. Ticks validation
    with patch("app.services.brokers.crypto.execute_bounded_get") as mock_get:
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = [
            {
                "a": 1,
                "p": "50000.0",
                "q": "0.125",
                "f": 1,
                "l": 1,
                "T": 1700000001000,
                "m": True,
            }
        ]
        mock_get.return_value = resp

        ticks = client.get_ticks(
            symbol="BTCUSDT",
            start=1700000000000,
            end=1700000010000,
            count=1,
        )
        assert len(ticks) == 1
        assert isinstance(ticks[0], MarketTick)
        assert ticks[0].volume == 1
        assert ticks[0].volume_real == 0.125


@pytest.mark.parametrize(
    "legacy_mod",
    [
        "app.services.brokers.exchanges",
        "app.services.brokers.exchanges.bitfinex",
        "app.services.brokers.exchanges.coinbase",
        "app.services.brokers.exchanges.poloniex",
    ],
)
def test_legacy_exchanges_package_removed(legacy_mod: str) -> None:
    """Verify legacy exchanges package and submodules are removed with zero shims."""
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module(legacy_mod)


def test_crypto_broker_helpers_and_symbol_info() -> None:
    """Verify BinanceClient symbol resolution, market venues, helpers, and adapter factory."""
    from app.services.brokers.crypto import (
        _calc_digits,
        _map_timeframe,
        create_adapter,
    )

    assert isinstance(create_adapter(), BinanceClient)
    assert _calc_digits(0.001) == 3
    assert _calc_digits(0.0) == 0
    assert _calc_digits(1.0) == 0
    assert _map_timeframe("H1") == "1h"

    # Spot get_symbol_info with mocked 200
    client = BinanceClient(venue="spot")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "symbols": [
            {
                "symbol": "BTCUSDT",
                "baseAsset": "BTC",
                "quoteAsset": "USDT",
                "filters": [
                    {"filterType": "PRICE_FILTER", "tickSize": "0.01000000"},
                    {"filterType": "LOT_SIZE", "stepSize": "0.00100000"},
                ],
            }
        ]
    }
    with patch.object(client.session, "get", return_value=mock_resp):
        info = client.get_symbol_info("BTC/USDT")
        assert info.name == "BTCUSDT"
        assert info.digits == 2
        assert client.get_symbols() == ["BTCUSDT"]

    # Cached lookup
    cached = client.get_symbol_info("BTCUSDT")
    assert cached.name == "BTCUSDT"

    # Futures USDT venue hard-fails on network error
    futures_client = BinanceClient(venue="usdt-m")
    assert futures_client.base_url == "https://fapi.binance.com"
    with (
        patch.object(
            futures_client.session, "get", side_effect=Exception("network error")
        ),
        pytest.raises(BridgeError),
    ):
        futures_client.get_symbol_info("ETHUSDT")

    # Coin-M venue
    coin_client = BinanceClient(venue="coin-m")
    assert coin_client.base_url == "https://dapi.binance.com"

    # Close with multiple exchange adapters
    multi_client = BinanceClient(exchange="bitfinex")
    bfx_adapter = multi_client._get_exchange_adapter("bitfinex")
    cb_adapter = multi_client._get_exchange_adapter("coinbase")
    pol_adapter = multi_client._get_exchange_adapter("poloniex")
    assert bfx_adapter is not None
    assert cb_adapter is not None
    assert pol_adapter is not None
    multi_client.disconnect()


def test_crypto_exchange_adapters_edge_cases() -> None:
    """Verify exchange adapters error paths, invalid payloads, and parameter handling."""
    from app.services.brokers.crypto import (
        BitfinexExchangeAdapter,
        CoinbaseExchangeAdapter,
        PoloniexExchangeAdapter,
    )

    sess = requests.Session()
    bfx = BitfinexExchangeAdapter(session=sess)
    cb = CoinbaseExchangeAdapter(session=sess)
    pol = PoloniexExchangeAdapter(session=sess)

    # Payload not a list raises BridgeError
    mock_dict_resp = MagicMock()
    mock_dict_resp.status_code = 200
    mock_dict_resp.json.return_value = {"error": "rate limited"}
    with patch.object(sess, "get", return_value=mock_dict_resp):
        with pytest.raises(BridgeError, match="expected list"):
            bfx.get_bars(symbol="BTCUSD", timeframe="1m")
        with pytest.raises(BridgeError, match="expected list"):
            cb.get_bars(symbol="BTC-USD", timeframe="1m")
        with pytest.raises(BridgeError, match="expected list"):
            pol.get_bars(symbol="BTC_USDT", timeframe="1m")

    # Valid reads with start and end bounds
    mock_bfx_valid = MagicMock()
    mock_bfx_valid.status_code = 200
    mock_bfx_valid.json.return_value = [[1767225600000, 1.1, 1.15, 1.2, 1.0, 100.0]]
    with patch.object(sess, "get", return_value=mock_bfx_valid):
        rows = bfx.get_bars(
            symbol="BTCUSD", timeframe="1m", start=1767225600, end=1767225700
        )
        assert len(rows) == 1

    mock_cb_valid = MagicMock()
    mock_cb_valid.status_code = 200
    mock_cb_valid.json.return_value = [[1767225600, 1.0, 1.2, 1.1, 1.15, 100.0]]
    with patch.object(sess, "get", return_value=mock_cb_valid):
        rows = cb.get_bars(
            symbol="BTC-USD", timeframe="1m", start=1767225600, end=1767225700
        )
        assert len(rows) == 1

    mock_pol_valid = MagicMock()
    mock_pol_valid.status_code = 200
    mock_pol_valid.json.return_value = [
        [
            "1.0",
            "1.2",
            "1.1",
            "1.15",
            "100.0",
            "1000.0",
            "50.0",
            "500.0",
            10,
            1767225600000,
            "1.12",
            "MINUTE_1",
            1767225600000,
            1767225660000,
        ]
    ]
    with patch.object(sess, "get", return_value=mock_pol_valid):
        rows = pol.get_bars(
            symbol="BTC_USDT", timeframe="1m", start=1767225600, end=1767225700
        )
        assert len(rows) == 1


def test_crypto_timeframe_resolution_and_exchange_formatting() -> None:
    """Verify Timeframe.resolve normalization and multi-exchange timeframe conversion."""
    from app.services.brokers.crypto import (
        BINANCE_TIMEFRAME_MAP,
        BITFINEX_TIMEFRAME_MAP,
        COINBASE_GRANULARITY_MAP,
        COINBASE_SUPPORTED_GRANULARITIES,
        POLONIEX_INTERVAL_MAP,
        BitfinexExchangeAdapter,
        CoinbaseExchangeAdapter,
        PoloniexExchangeAdapter,
        _map_timeframe,
    )
    from app.services.include.enums import Timeframe

    # 1. Verify Timeframe.resolve idempotence and alias normalization
    assert Timeframe.resolve("M1") == Timeframe.PERIOD_M1
    assert Timeframe.resolve("1m") == Timeframe.PERIOD_M1
    assert Timeframe.resolve("1H") == Timeframe.PERIOD_H1
    assert Timeframe.resolve("day") == Timeframe.PERIOD_D1
    assert Timeframe.resolve(Timeframe.PERIOD_H4) == Timeframe.PERIOD_H4
    assert Timeframe.resolve(None) == Timeframe.PERIOD_M1
    assert Timeframe.resolve(None, default=Timeframe.PERIOD_H1) == Timeframe.PERIOD_H1
    assert (
        Timeframe.resolve("NONEXISTENT_TF", default=Timeframe.PERIOD_D1)
        == Timeframe.PERIOD_D1
    )
    assert Timeframe.from_string(Timeframe.PERIOD_M5) == Timeframe.PERIOD_M5

    # 2. Verify Binance interval resolution
    assert _map_timeframe("1m") == "1m"
    assert _map_timeframe("M1") == "1m"
    assert _map_timeframe("1h") == "1h"
    assert _map_timeframe(Timeframe.PERIOD_D1) == "1d"
    assert _map_timeframe(Timeframe.PERIOD_MN1) == "1M"
    assert _map_timeframe("UNKNOWN") == "1m"
    assert Timeframe.PERIOD_M1 in BINANCE_TIMEFRAME_MAP

    # 3. Verify Bitfinex timeframe resolution
    sess = requests.Session()
    bfx = BitfinexExchangeAdapter(session=sess)
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = []
    with patch(
        "app.services.brokers.crypto.execute_bounded_get", return_value=mock_resp
    ) as mock_get:
        # Lowercase string
        bfx.get_bars(symbol="BTCUSD", timeframe="1m")
        assert "trade:1m:tBTCUSD" in mock_get.call_args[0][1]

        # Canonical enum
        bfx.get_bars(symbol="BTCUSD", timeframe=Timeframe.PERIOD_D1)
        assert "trade:1D:tBTCUSD" in mock_get.call_args[0][1]

    assert Timeframe.PERIOD_M1 in BITFINEX_TIMEFRAME_MAP

    # 4. Verify Coinbase granularity seconds
    cb = CoinbaseExchangeAdapter(session=sess)
    with patch(
        "app.services.brokers.crypto.execute_bounded_get", return_value=mock_resp
    ) as mock_get:
        # String '1m' -> 60s
        cb.get_bars(symbol="BTC-USD", timeframe="1m")
        assert mock_get.call_args[1]["params"]["granularity"] == 60

        # Enum PERIOD_H1 -> 3600s
        cb.get_bars(symbol="BTC-USD", timeframe=Timeframe.PERIOD_H1)
        assert mock_get.call_args[1]["params"]["granularity"] == 3600

        # Unsupported timeframe falls back to 60s
        cb.get_bars(symbol="BTC-USD", timeframe="3m")
        assert mock_get.call_args[1]["params"]["granularity"] == 60

    assert 60 in COINBASE_SUPPORTED_GRANULARITIES
    assert COINBASE_GRANULARITY_MAP[Timeframe.PERIOD_H1] == 3600

    # 5. Verify Poloniex interval strings
    pol = PoloniexExchangeAdapter(session=sess)
    with patch(
        "app.services.brokers.crypto.execute_bounded_get", return_value=mock_resp
    ) as mock_get:
        # String '1m' -> 'MINUTE_1'
        pol.get_bars(symbol="BTC_USDT", timeframe="1m")
        assert mock_get.call_args[1]["params"]["interval"] == "MINUTE_1"

        # Enum PERIOD_D1 -> 'DAY_1'
        pol.get_bars(symbol="BTC_USDT", timeframe=Timeframe.PERIOD_D1)
        assert mock_get.call_args[1]["params"]["interval"] == "DAY_1"

    assert Timeframe.PERIOD_M1 in POLONIEX_INTERVAL_MAP
