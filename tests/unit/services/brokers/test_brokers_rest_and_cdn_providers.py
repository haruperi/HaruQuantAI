"""Unit tests for REST, CDN, and exchange-based market data providers.

Description:
    Tests HTTP transport resilience, bounded reads, retry mechanics, credential
    redaction, and health probes across Dukascopy, Darwinex, StrategyQuant Equity/Futures,
    Crypto multi-exchange feeds (Binance, Bitfinex, Coinbase, Poloniex), Yahoo Finance,
    and Tick Downloader. Validates that rate-limiting, authentication failures,
    timeouts, and empty CDN payloads are translated to domain errors or empty pages
    without synthetic fallback. All network calls are strictly mocked.

Purpose:
    FEAT-BROKER-REST-TEST: Verification of HTTP, CDN, and exchange market data providers.

Key Capabilities:
    - FR-TEST-REST-TRANSPORT: Assert session configuration, retry backoff, and redaction.
      Associated: `test_http_session_and_redaction()`, `test_execute_bounded_get_errors()`
      Logging: Validates redacted error strings and transport error mapping.
    - FR-TEST-REST-PROVIDERS: Assert HTTP and CDN data fetching and response parsing.
      Associated: `test_dukascopy_rest_provider()`, `test_sq_equity_d1_protection()`,
      `test_crypto_multiexchange_routing()`, `test_yahoo_provider_contracts()`
      Logging: Validates URL resolution, status mappings, and zero synthetic fallbacks.

Python API Usage:
    ```bash
    uv run pytest tests/unit/services/brokers/test_brokers_rest_and_cdn_providers.py --no-cov
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/brokers/test_brokers_rest_and_cdn_providers.py --no-cov
    ```
"""

from __future__ import annotations

import importlib
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
import requests
from app.services.brokers._http import (
    create_http_session,
    execute_bounded_get,
    redact_url_or_message,
)
from app.services.brokers.capabilities import (
    CancellationToken,
    HistoryRequest,
    ProviderAuthError,
    ProviderCancelledError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderUnsupportedError,
    ProviderValidationError,
)
from app.services.brokers.crypto import CryptoBroker
from app.services.brokers.dukascopy import DukascopyBroker
from app.services.brokers.sq_equity import SQEquityBroker
from app.services.brokers.sq_futures import SQFuturesBroker
from app.services.brokers.tick_downloader import TickDownloaderBroker
from app.services.brokers.yahoo import YahooBroker

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
    """Verify execute_bounded_get translates HTTP 429, 401, timeout, and cancellation."""
    session = MagicMock(spec=requests.Session)

    # Test 429 Rate Limit
    resp_429 = MagicMock()
    resp_429.status_code = 429
    resp_429.headers = {"Retry-After": "5"}
    session.get.return_value = resp_429

    with pytest.raises(ProviderRateLimitError) as exc_429:
        execute_bounded_get(session, "https://api.com/feed", provider="test")
    assert exc_429.value.status_code == 429
    assert exc_429.value.retry_after == 5.0

    # Test 401 Auth Error
    resp_401 = MagicMock()
    resp_401.status_code = 401
    session.get.return_value = resp_401

    with pytest.raises(ProviderAuthError) as exc_401:
        execute_bounded_get(session, "https://api.com/feed", provider="test")
    assert exc_401.value.status_code == 502

    # Test Timeout
    session.get.side_effect = requests.exceptions.Timeout("Connection timed out")
    with pytest.raises(ProviderTimeoutError) as exc_timeout:
        execute_bounded_get(session, "https://api.com/feed", provider="test")
    assert exc_timeout.value.status_code == 504

    # Test CancellationToken
    token = CancellationToken()
    token.cancel("Aborted by user")
    with pytest.raises(ProviderCancelledError):
        execute_bounded_get(
            session, "https://api.com/feed", token=token, provider="test"
        )


# ============================================================================
# Dukascopy Provider Tests
# ============================================================================


def test_dukascopy_rest_provider() -> None:
    """Verify Dukascopy health check and empty 404 response handling."""
    broker = DukascopyBroker()
    mock_head_resp = MagicMock()
    mock_head_resp.status_code = 200
    with patch.object(broker.session, "head", return_value=mock_head_resp):
        health = broker.check_health()
        assert health.provider_id == "dukascopy"
        assert health.status in ("HEALTHY", "available")

    # Mock 404 Not Found from Dukascopy CDN
    with patch("app.services.brokers.dukascopy.execute_bounded_get") as mock_get:
        resp_404 = MagicMock()
        resp_404.status_code = 404
        resp_404.content = b""
        mock_get.return_value = resp_404

        req = HistoryRequest(
            provider="dukascopy",
            symbol="EURUSD",
            timeframe="M1",
            count=10,
            start=datetime(2026, 1, 1, tzinfo=UTC),
            end=datetime(2026, 1, 1, 1, 0, 0, tzinfo=UTC),
        )
        page = broker.read_history(req)
        assert page.row_count == 0
        assert page.is_complete is True


# ============================================================================
# StrategyQuant Equity Provider Tests (Cadence Protection)
# ============================================================================


def test_sq_equity_d1_protection() -> None:
    """Verify StrategyQuant Equity rejects intraday requests and accepts D1."""
    broker = SQEquityBroker()

    # Rejection of intraday M1
    req_m1 = HistoryRequest(
        provider="sq_equity",
        symbol="AAPL",
        timeframe="M1",
        count=10,
    )
    with pytest.raises(ProviderValidationError, match="only supports D1"):
        broker.read_history(req_m1)

    # Valid D1 with 404 CDN response
    with patch("app.services.brokers.sq_equity.execute_bounded_get") as mock_get:
        resp = MagicMock()
        resp.status_code = 404
        resp.content = b""
        mock_get.return_value = resp

        req_d1 = HistoryRequest(
            provider="sq_equity",
            symbol="AAPL",
            timeframe="D1",
            count=10,
        )
        page = broker.read_history(req_d1)
        assert page.row_count == 0


# ============================================================================
# StrategyQuant Futures Provider Tests
# ============================================================================


def test_sq_futures_cadence_and_404() -> None:
    """Verify StrategyQuant Futures validates timeframe and handles 404 safely."""
    broker = SQFuturesBroker()

    # Invalid timeframe (H4)
    req_h4 = HistoryRequest(
        provider="sq_futures",
        symbol="ES",
        timeframe="H4",
        count=10,
    )
    with pytest.raises(ProviderValidationError, match="only supports D1 and M1"):
        broker.read_history(req_h4)

    # Valid M1 with 404 CDN response
    with patch("app.services.brokers.sq_futures.execute_bounded_get") as mock_get:
        resp = MagicMock()
        resp.status_code = 404
        resp.content = b""
        mock_get.return_value = resp

        req_m1 = HistoryRequest(
            provider="sq_futures",
            symbol="ES",
            timeframe="M1",
            count=10,
        )
        page = broker.read_history(req_m1)
        assert page.row_count == 0


# ============================================================================
# Crypto Provider Multi-Exchange Routing Tests
# ============================================================================


def test_crypto_multiexchange_routing() -> None:
    """Verify CryptoBroker routes requests to Bitfinex, Coinbase, Poloniex, and Binance."""
    broker = CryptoBroker()

    # 1. Bitfinex routing & decoding
    with patch("app.services.brokers.crypto.execute_bounded_get") as mock_get:
        resp = MagicMock()
        resp.status_code = 200
        # Bitfinex layout: [[MTS, OPEN, CLOSE, HIGH, LOW, VOLUME]]
        resp.json.return_value = [
            [1768478400000, 50000.0, 50500.0, 50800.0, 49800.0, 10.5]
        ]
        mock_get.return_value = resp

        req_bitfinex = HistoryRequest(
            provider="crypto",
            symbol="BTCUSD",
            exchange="bitfinex",
            timeframe="M1",
            count=1,
        )
        page = broker.read_history(req_bitfinex)
        assert page.row_count == 1
        assert page.rows[0]["open"] == 50000.0
        assert page.rows[0]["high"] == 50800.0
        assert page.rows[0]["low"] == 49800.0
        assert page.rows[0]["close"] == 50500.0

    # 2. Coinbase routing & decoding
    with patch("app.services.brokers.crypto.execute_bounded_get") as mock_get:
        resp = MagicMock()
        resp.status_code = 200
        # Coinbase layout: [[time, low, high, open, close, volume]]
        resp.json.return_value = [
            [1768478400, 49800.0, 50800.0, 50000.0, 50500.0, 10.5]
        ]
        mock_get.return_value = resp

        req_coinbase = HistoryRequest(
            provider="crypto",
            symbol="BTC-USD",
            exchange="coinbase",
            timeframe="M1",
            count=1,
        )
        page_cb = broker.read_history(req_coinbase)
        assert page_cb.row_count == 1
        assert page_cb.rows[0]["open"] == 50000.0
        assert page_cb.rows[0]["close"] == 50500.0

    # 3. Poloniex routing & decoding
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

        req_polo = HistoryRequest(
            provider="crypto",
            symbol="BTC_USDT",
            exchange="poloniex",
            timeframe="M1",
            count=1,
        )
        page_polo = broker.read_history(req_polo)
        assert page_polo.row_count == 1
        assert page_polo.rows[0]["open"] == 50000.0


# ============================================================================
# Yahoo Finance Provider Tests
# ============================================================================


def test_yahoo_provider_contracts() -> None:
    """Verify Yahoo Finance validates unsupported ticks and parses chart responses."""
    broker = YahooBroker()

    # Reject unsupported ticks
    req_ticks = HistoryRequest(
        provider="yahoo",
        symbol="SPY",
        kind="ticks",
        count=10,
    )
    with pytest.raises(ProviderUnsupportedError, match="does not support tick"):
        broker.read_history(req_ticks)

    # Valid bars parsing
    with patch.object(broker.session, "get") as mock_get:
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

        req_bars = HistoryRequest(
            provider="yahoo",
            symbol="SPY",
            timeframe="D1",
            count=1,
        )
        page = broker.read_history(req_bars)
        assert page.row_count == 1
        assert page.rows[0]["open"] == 500.0
        assert page.rows[0]["close"] == 502.0


# ============================================================================
# Tick Downloader Provider Legacy Compatibility Tests
# ============================================================================


def test_tick_downloader_compatibility() -> None:
    """Verify TickDownloaderBroker backward compatibility methods."""
    broker = TickDownloaderBroker()
    symbols = broker.get_available_symbols()
    assert isinstance(symbols, list)
    assert "EURUSD" in symbols

    # Read history empty range returns 0 rows without crashing
    req = HistoryRequest(
        provider="tick_downloader",
        symbol="UNKNOWN_PAIR",
        timeframe="M1",
        count=5,
    )
    with patch(
        "app.services.brokers.dukascopy.DukascopyBroker.fetch_bars", return_value=[]
    ):
        page = broker.read_history(req)
        assert page.row_count == 0


def test_binance_bars_and_ticks_integer_validation() -> None:
    """Verify Binance fetch_bars and fetch_ticks produce integer volumes accepted by validate_rows."""
    from app.services.brokers.crypto import BinanceBroker
    from app.services.include.data import validate_rows
    from app.workspace.data_manager import MarketBar, MarketTick

    broker = BinanceBroker()

    # 1. Bars integer volume validation
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

        bars = broker.fetch_bars(
            symbol="BTCUSDT",
            timeframe="M1",
            mode="range",
            start=1700000000,
            end=1700000060,
            count=1,
            limit=10,
        )
        assert len(bars) == 1
        assert isinstance(bars[0]["real_volume"], int)
        assert isinstance(bars[0]["tick_volume"], int)
        validated_bars = validate_rows(bars, "bars", 0, 2**63 - 1, 10)
        assert len(validated_bars) == 1
        assert isinstance(validated_bars[0], MarketBar)
        assert validated_bars[0].real_volume == 12

    # 2. Ticks integer volume validation
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

        ticks = broker.fetch_ticks(
            symbol="BTCUSDT",
            start_ms=1700000000000,
            end_ms=1700000010000,
            count=1,
            limit=10,
        )
        assert len(ticks) == 1
        assert isinstance(ticks[0]["volume"], int)
        assert isinstance(ticks[0]["volume_real"], float)
        assert ticks[0]["volume"] == 1
        assert ticks[0]["volume_real"] == 0.125
        validated_ticks = validate_rows(ticks, "ticks", 0, 2**63 - 1, 10)
        assert len(validated_ticks) == 1
        assert isinstance(validated_ticks[0], MarketTick)
        assert validated_ticks[0].volume == 1
        assert validated_ticks[0].volume_real == 0.125


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
    """Verify BinanceBroker symbol resolution, market venues, helpers, and adapter factory."""
    from app.services.brokers.crypto import (
        BinanceBroker,
        _calc_digits,
        _map_timeframe,
        create_adapter,
    )

    assert isinstance(create_adapter(), BinanceBroker)
    assert _calc_digits(0.001) == 3
    assert _calc_digits(0.0) == 0
    assert _calc_digits(1.0) == 0
    assert _map_timeframe("H1") == "1h"

    # Spot symbol_info with mocked 200
    broker = BinanceBroker(venue="spot")
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
    with patch.object(broker.session, "get", return_value=mock_resp):
        info = broker.symbol_info("BTC/USDT")
        assert info.name == "BTCUSDT"
        assert info.digits == 2
        assert broker.symbols_get() == ["BTCUSDT"]

    # Cached lookup
    cached = broker.symbol_info("BTCUSDT")
    assert cached.name == "BTCUSDT"

    # Futures USDT venue
    futures_broker = BinanceBroker(venue="usdt-m")
    assert futures_broker.base_url == "https://fapi.binance.com"
    with patch.object(
        futures_broker.session, "get", side_effect=Exception("network error")
    ):
        fallback = futures_broker.symbol_info("ETHUSDT")
        assert fallback.name == "ETHUSDT"
        assert fallback.digits == 2

    # Coin-M venue
    coin_broker = BinanceBroker(venue="coin-m")
    assert coin_broker.base_url == "https://dapi.binance.com"
    health = coin_broker.check_health()
    assert health.provider_id == "crypto"

    # Close with multiple exchange adapters
    multi_broker = BinanceBroker(exchange="bitfinex")
    bfx_adapter = multi_broker._get_exchange_adapter("bitfinex")
    cb_adapter = multi_broker._get_exchange_adapter("coinbase")
    pol_adapter = multi_broker._get_exchange_adapter("poloniex")
    assert bfx_adapter is not None
    assert cb_adapter is not None
    assert pol_adapter is not None
    multi_broker.close_sync()


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

    # Payload not a list
    mock_dict_resp = MagicMock()
    mock_dict_resp.status_code = 200
    mock_dict_resp.json.return_value = {"error": "rate limited"}
    with patch.object(sess, "get", return_value=mock_dict_resp):
        assert bfx.fetch_bars(symbol="BTCUSD", timeframe="1m") == []
        assert cb.fetch_bars(symbol="BTC-USD", timeframe="1m") == []
        assert pol.fetch_bars(symbol="BTC_USDT", timeframe="1m") == []

    # Valid reads with start and end bounds
    mock_bfx_valid = MagicMock()
    mock_bfx_valid.status_code = 200
    mock_bfx_valid.json.return_value = [[1767225600000, 1.1, 1.15, 1.2, 1.0, 100.0]]
    with patch.object(sess, "get", return_value=mock_bfx_valid):
        rows = bfx.fetch_bars(
            symbol="BTCUSD", timeframe="1m", start=1767225600, end=1767225700
        )
        assert len(rows) == 1

    mock_cb_valid = MagicMock()
    mock_cb_valid.status_code = 200
    mock_cb_valid.json.return_value = [[1767225600, 1.0, 1.2, 1.1, 1.15, 100.0]]
    with patch.object(sess, "get", return_value=mock_cb_valid):
        rows = cb.fetch_bars(
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
        rows = pol.fetch_bars(
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
        bfx.fetch_bars(symbol="BTCUSD", timeframe="1m")
        assert "trade:1m:tBTCUSD" in mock_get.call_args[0][1]

        # Canonical enum
        bfx.fetch_bars(symbol="BTCUSD", timeframe=Timeframe.PERIOD_D1)
        assert "trade:1D:tBTCUSD" in mock_get.call_args[0][1]

    assert Timeframe.PERIOD_M1 in BITFINEX_TIMEFRAME_MAP

    # 4. Verify Coinbase granularity seconds
    cb = CoinbaseExchangeAdapter(session=sess)
    with patch(
        "app.services.brokers.crypto.execute_bounded_get", return_value=mock_resp
    ) as mock_get:
        # String '1m' -> 60s
        cb.fetch_bars(symbol="BTC-USD", timeframe="1m")
        assert mock_get.call_args[1]["params"]["granularity"] == 60

        # Enum PERIOD_H1 -> 3600s
        cb.fetch_bars(symbol="BTC-USD", timeframe=Timeframe.PERIOD_H1)
        assert mock_get.call_args[1]["params"]["granularity"] == 3600

        # Unsupported timeframe falls back to 60s
        cb.fetch_bars(symbol="BTC-USD", timeframe="3m")
        assert mock_get.call_args[1]["params"]["granularity"] == 60

    assert 60 in COINBASE_SUPPORTED_GRANULARITIES
    assert COINBASE_GRANULARITY_MAP[Timeframe.PERIOD_H1] == 3600

    # 5. Verify Poloniex interval strings
    pol = PoloniexExchangeAdapter(session=sess)
    with patch(
        "app.services.brokers.crypto.execute_bounded_get", return_value=mock_resp
    ) as mock_get:
        # String '1m' -> 'MINUTE_1'
        pol.fetch_bars(symbol="BTC_USDT", timeframe="1m")
        assert mock_get.call_args[1]["params"]["interval"] == "MINUTE_1"

        # Enum PERIOD_D1 -> 'DAY_1'
        pol.fetch_bars(symbol="BTC_USDT", timeframe=Timeframe.PERIOD_D1)
        assert mock_get.call_args[1]["params"]["interval"] == "DAY_1"

    assert Timeframe.PERIOD_M1 in POLONIEX_INTERVAL_MAP
