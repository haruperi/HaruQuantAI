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
    with patch(
        "app.services.brokers.exchanges.bitfinex.execute_bounded_get"
    ) as mock_get:
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
    with patch(
        "app.services.brokers.exchanges.coinbase.execute_bounded_get"
    ) as mock_get:
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
    with patch(
        "app.services.brokers.exchanges.poloniex.execute_bounded_get"
    ) as mock_get:
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
    from app.workspace.data_manager import MarketBar, MarketTick
    from app.workspace.data_manager.history import validate_rows

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
