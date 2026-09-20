"""Unit tests for the 6 external market data feed transport connectors.

Features Tested:
    * FEAT-BROKERS-DUKASCOPY (app.services.brokers.dukascopy)
    * FEAT-BROKERS-EQUITY (app.services.brokers.equity)
    * FEAT-BROKERS-FUTURES (app.services.brokers.futures)
    * FEAT-BROKERS-DARWINEX (app.services.brokers.darwinex)
    * FEAT-BROKERS-CRYPTO (app.services.brokers.crypto)
    * FEAT-BROKERS-YAHOO (app.services.brokers.yahoo)

Coverage & Constraints:
    * Tests verify connect, disconnect, streaming raw chunks, health checks, and connection guards.
    * Verifies FR-BROKERS-TRANSPORT_BOUNDARY: Pure transport boundary yielding
      RawTransportChunk with raw bytes.
    * 100% deterministic, offline execution with zero network requirements.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import pytest
from app.contracts.brokers import (
    BrokerAuthenticationError,
    BrokerConnectionConfig,
    BrokerConnectionError,
    ConnectionState,
    RawTransportChunk,
    UnsupportedCapabilityError,
)
from app.services.brokers.crypto import (
    CryptoFeedConfig,
    CryptoFeedService,
)
from app.services.brokers.darwinex import (
    DarwinexFeedConfig,
    DarwinexFeedService,
)
from app.services.brokers.dukascopy import (
    DukascopyFeedConfig,
    DukascopyFeedService,
)
from app.services.brokers.equity import (
    SQEquityFeedConfig,
    SQEquityFeedService,
)
from app.services.brokers.futures import (
    SQFuturesFeedConfig,
    SQFuturesFeedService,
)
from app.services.brokers.yahoo import (
    YahooFeedConfig,
    YahooFeedService,
)


def test_dukascopy_feed_lifecycle_and_streaming() -> None:
    """Test Dukascopy connector session and hourly bi5 chunk streaming."""

    async def _run() -> None:
        service = DukascopyFeedService(DukascopyFeedConfig(mock_mode=True))
        assert service.provider_name == "dukascopy"
        assert not service.is_connected()

        # Stream before connect raises BrokerConnectionError
        start = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
        end = datetime(2026, 1, 1, 2, 0, tzinfo=UTC)
        with pytest.raises(BrokerConnectionError):
            async for _ in service.stream_raw_data("EURUSD", start, end):
                pass

        # Connect
        conn_cfg = BrokerConnectionConfig(
            connection_id="dukascopy-test",
            broker_id=3,
            provider_name="Dukascopy",
        )
        await service.connect(conn_cfg)
        assert service.is_connected()

        # Health check
        health = await service.get_health()
        assert health.state == ConnectionState.READY
        assert health.provider == "dukascopy"

        # Stream bi5 chunks
        chunks: list[RawTransportChunk] = []
        async for chunk in service.stream_raw_data("EURUSD", start, end):
            chunks.append(chunk)

        assert len(chunks) == 3
        assert chunks[0].sequence_num == 0
        assert chunks[0].provider == "dukascopy"
        assert chunks[0].symbol == "EURUSD"
        assert len(chunks[0].payload_bytes) > 0
        assert not chunks[0].is_eof
        assert chunks[2].is_eof

        await service.disconnect()
        assert not service.is_connected()
        post_health = await service.get_health()
        assert post_health.state == ConnectionState.CLOSED

    asyncio.run(_run())


def test_sq_equity_feed_lifecycle_and_streaming() -> None:
    """Test SQ Equity connector session and REST payload chunk streaming."""

    async def _run() -> None:
        service = SQEquityFeedService(SQEquityFeedConfig(mock_mode=True))
        assert service.provider_name == "sq_equity"
        assert not service.is_connected()

        start = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
        end = datetime(2026, 1, 3, 0, 0, tzinfo=UTC)
        with pytest.raises(BrokerConnectionError):
            async for _ in service.stream_raw_data("AAPL", start, end):
                pass

        conn_cfg = BrokerConnectionConfig(
            connection_id="sq-equity-test",
            broker_id=2,
            provider_name="SQ Equity",
        )
        await service.connect(conn_cfg)
        assert service.is_connected()

        health = await service.get_health()
        assert health.state == ConnectionState.READY

        chunks: list[RawTransportChunk] = []
        async for chunk in service.stream_raw_data("AAPL", start, end):
            chunks.append(chunk)

        assert len(chunks) == 3
        assert chunks[0].provider == "sq_equity"
        assert b'"ticker":"AAPL"' in chunks[0].payload_bytes
        assert chunks[2].is_eof

        await service.disconnect()
        assert not service.is_connected()

    asyncio.run(_run())


def test_sq_futures_feed_lifecycle_and_streaming() -> None:
    """Test SQ Futures connector session and continuous contract payload streaming."""

    async def _run() -> None:
        service = SQFuturesFeedService(SQFuturesFeedConfig(mock_mode=True))
        assert service.provider_name == "sq_futures"
        assert not service.is_connected()

        start = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
        end = datetime(2026, 1, 2, 0, 0, tzinfo=UTC)
        with pytest.raises(BrokerConnectionError):
            async for _ in service.stream_raw_data("ES", start, end):
                pass

        conn_cfg = BrokerConnectionConfig(
            connection_id="sq-futures-test",
            broker_id=3,
            provider_name="SQ Futures",
        )
        await service.connect(conn_cfg)
        assert service.is_connected()

        chunks: list[RawTransportChunk] = []
        async for chunk in service.stream_raw_data("ES", start, end):
            chunks.append(chunk)

        assert len(chunks) == 2
        assert chunks[0].provider == "sq_futures"
        assert b'"contract":"ES"' in chunks[0].payload_bytes
        assert chunks[1].is_eof

        await service.disconnect()
        assert not service.is_connected()

    asyncio.run(_run())


def test_darwinex_feed_lifecycle_and_streaming() -> None:
    """Test Darwinex connector session and tick stream payload streaming."""

    async def _run() -> None:
        service = DarwinexFeedService(DarwinexFeedConfig(mock_mode=True))
        assert service.provider_name == "darwinex"
        assert not service.is_connected()

        start = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
        end = datetime(2026, 1, 1, 1, 0, tzinfo=UTC)
        with pytest.raises(BrokerConnectionError):
            async for _ in service.stream_raw_data("EURUSD", start, end):
                pass

        conn_cfg = BrokerConnectionConfig(
            connection_id="darwinex-feed-test",
            broker_id=4,
            provider_name="Darwinex",
        )
        await service.connect(conn_cfg)
        assert service.is_connected()

        chunks: list[RawTransportChunk] = []
        async for chunk in service.stream_raw_data("EURUSD", start, end):
            chunks.append(chunk)

        assert len(chunks) == 2
        assert chunks[0].provider == "darwinex"
        assert b'"provider":"darwinex"' in chunks[0].payload_bytes
        assert chunks[1].is_eof

        await service.disconnect()
        assert not service.is_connected()

    asyncio.run(_run())


def test_crypto_feed_lifecycle_and_streaming() -> None:
    """Test Crypto exchange connector session and raw kline payload streaming."""

    async def _run() -> None:
        service = CryptoFeedService(
            CryptoFeedConfig(exchange_id="binance", mock_mode=True)
        )
        assert service.provider_name == "crypto"
        assert service.exchange_id == "binance"
        assert not service.is_connected()

        start = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
        end = datetime(2026, 1, 1, 2, 0, tzinfo=UTC)
        with pytest.raises(BrokerConnectionError):
            async for _ in service.stream_raw_data("BTCUSDT", start, end):
                pass

        conn_cfg = BrokerConnectionConfig(
            connection_id="crypto-feed-test",
            broker_id=5,
            provider_name="Binance",
        )
        await service.connect(conn_cfg)
        assert service.is_connected()

        chunks: list[RawTransportChunk] = []
        async for chunk in service.stream_raw_data("BTCUSDT", start, end):
            chunks.append(chunk)

        assert len(chunks) == 3
        assert chunks[0].provider == "crypto"
        assert chunks[0].metadata.get("exchange") == "binance"
        assert chunks[2].is_eof

        await service.disconnect()
        assert not service.is_connected()

    asyncio.run(_run())


def test_yahoo_feed_lifecycle_and_streaming() -> None:
    """Test Yahoo Finance connector session crumb and v8 chart payload streaming."""

    async def _run() -> None:
        service = YahooFeedService(YahooFeedConfig(mock_mode=True))
        assert service.provider_name == "yahoo"
        assert not service.is_connected()

        start = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
        end = datetime(2026, 1, 2, 0, 0, tzinfo=UTC)
        with pytest.raises(BrokerConnectionError):
            async for _ in service.stream_raw_data("SPY", start, end):
                pass

        conn_cfg = BrokerConnectionConfig(
            connection_id="yahoo-feed-test",
            broker_id=6,
            provider_name="Yahoo Finance",
        )
        await service.connect(conn_cfg)
        assert service.is_connected()

        chunks: list[RawTransportChunk] = []
        async for chunk in service.stream_raw_data("SPY", start, end):
            chunks.append(chunk)

        assert len(chunks) == 2
        assert chunks[0].provider == "yahoo"
        assert b'"regularMarketPrice"' in chunks[0].payload_bytes
        assert chunks[0].metadata.get("interval") == "1d"
        assert chunks[1].is_eof

        await service.disconnect()
        assert not service.is_connected()

    asyncio.run(_run())


def test_feeds_span_validation_error() -> None:
    """Verify UnsupportedCapabilityError when start_utc > end_utc."""

    async def _run() -> None:
        start = datetime(2026, 1, 2, 0, 0, tzinfo=UTC)
        end = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
        conn = BrokerConnectionConfig(
            connection_id="c1", broker_id=1, provider_name="test"
        )

        duka = DukascopyFeedService(DukascopyFeedConfig(mock_mode=True))
        await duka.connect(conn)
        with pytest.raises(UnsupportedCapabilityError):
            async for _ in duka.stream_raw_data("EURUSD", start, end):
                pass

        crypto = CryptoFeedService(CryptoFeedConfig(mock_mode=True))
        await crypto.connect(conn)
        with pytest.raises(UnsupportedCapabilityError):
            async for _ in crypto.stream_raw_data("BTCUSDT", start, end):
                pass

        yahoo = YahooFeedService(YahooFeedConfig(mock_mode=True))
        await yahoo.connect(conn)
        with pytest.raises(UnsupportedCapabilityError):
            async for _ in yahoo.stream_raw_data("SPY", start, end):
                pass

    asyncio.run(_run())


def test_feeds_real_mode_credential_required(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify BrokerAuthenticationError when credentials are missing in real mode."""
    monkeypatch.delenv("HARU_BROKER_SQ_LICENSE", raising=False)
    monkeypatch.delenv("HARU_BROKER_DARWINEX_TOKEN", raising=False)

    async def _run() -> None:
        conn = BrokerConnectionConfig(
            connection_id="c1", broker_id=1, provider_name="test"
        )

        sq_eq = SQEquityFeedService(SQEquityFeedConfig(mock_mode=False))
        with pytest.raises(BrokerAuthenticationError):
            await sq_eq.connect(conn)

        sq_fut = SQFuturesFeedService(SQFuturesFeedConfig(mock_mode=False))
        with pytest.raises(BrokerAuthenticationError):
            await sq_fut.connect(conn)

        darw = DarwinexFeedService(DarwinexFeedConfig(mock_mode=False))
        with pytest.raises(BrokerAuthenticationError):
            await darw.connect(conn)

    asyncio.run(_run())


def test_feeds_real_mode_monkeypatched_http(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify real-mode streaming path using monkeypatched transport seam."""
    import app.services.brokers.crypto as crypto_mod
    import app.services.brokers.dukascopy as duka_mod
    import app.services.brokers.yahoo as yahoo_mod

    monkeypatch.setattr(
        duka_mod,
        "_http_get",
        lambda url, **kwargs: (b"real_bi5_binary_data", 200, 4.2),
    )
    monkeypatch.setattr(
        crypto_mod,
        "_http_get",
        lambda url, **kwargs: (b'[{"real_kline": 64200.0}]', 200, 6.5),
    )
    monkeypatch.setattr(
        yahoo_mod,
        "_http_get",
        lambda url, **kwargs: (b'{"chart":{"real": true}}', 200, 11.0),
    )

    async def _run() -> None:
        conn = BrokerConnectionConfig(
            connection_id="c1", broker_id=1, provider_name="test"
        )
        start = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
        end = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)

        duka = DukascopyFeedService(DukascopyFeedConfig(mock_mode=False))
        await duka.connect(conn)
        chunks = [c async for c in duka.stream_raw_data("EURUSD", start, end)]
        assert chunks[0].payload_bytes == b"real_bi5_binary_data"
        assert chunks[0].metadata.get("simulated") is False
        assert (await duka.get_health()).latency_ms == 4.2

        crypto = CryptoFeedService(CryptoFeedConfig(mock_mode=False))
        await crypto.connect(conn)
        chunks = [c async for c in crypto.stream_raw_data("BTCUSDT", start, end)]
        assert chunks[0].payload_bytes == b'[{"real_kline": 64200.0}]'
        assert chunks[0].metadata.get("simulated") is False
        assert (await crypto.get_health()).latency_ms == 6.5

        yahoo = YahooFeedService(YahooFeedConfig(mock_mode=False))
        await yahoo.connect(conn)
        chunks = [c async for c in yahoo.stream_raw_data("SPY", start, end)]
        assert chunks[0].payload_bytes == b'{"chart":{"real": true}}'
        assert chunks[0].metadata.get("simulated") is False
        assert (await yahoo.get_health()).latency_ms == 11.0

    asyncio.run(_run())
