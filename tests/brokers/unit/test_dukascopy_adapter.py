"""Dukascopy adapter tests using an injected fake transport."""

import asyncio
import struct
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from app.services.brokers import (
    BrokerCapability,
    BrokerCapabilityId,
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerErrorCode,
    BrokerId,
)
from app.services.brokers.dukascopy_ticks.adapter import DukascopyBrokerAdapter
from app.services.brokers.dukascopy_ticks.candle_transport import _CandleBatch

_RECORD = struct.Struct(">3I2f")


def _config() -> BrokerConnectionConfig:
    return BrokerConnectionConfig(
        broker_id=BrokerId.DUKASCOPY,
        environment=BrokerEnvironment.SANDBOX,
        provider_enabled=True,
        connect_timeout_sec=1,
        request_timeout_sec=1,
        transport_reconnect_max_attempts=0,
        stream_buffer_size=2,
        circuit_failure_threshold=2,
        circuit_recovery_timeout_sec=1,
        circuit_half_open_max_calls=1,
    )


def _capabilities() -> dict[BrokerCapabilityId, BrokerCapability]:
    return {
        operation: BrokerCapability(
            capability=operation,
            implementation_status="IMPLEMENTED",
            availability="AVAILABLE",
            access_mode="READ",
            requirement="NONE",
            verification_status="NOT_TESTED",
            execution_model="TEST_DOUBLE",
        )
        for operation in BrokerCapabilityId
    }


class _FakeTransport:
    def __init__(self, *, fails: bool = False) -> None:
        self._fails = fails

    async def get_hour(self, symbol: str, hour: object) -> bytes:
        del symbol, hour
        if self._fails:
            raise OSError("network unreachable")
        return _RECORD.pack(0, 110_000, 109_990, 1.0, 1.0)


class _FakeCandleTransport:
    """Return bounded recorded Dukascopy web-chart rows."""

    def __init__(self, *, truncated: bool = False) -> None:
        self.truncated = truncated
        self.requests: list[tuple[str, str, datetime, datetime, int]] = []

    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
        limit: int,
    ) -> _CandleBatch:
        """Return one recorded candle batch."""
        self.requests.append((symbol, timeframe, start, end, limit))
        rows = ((int(start.timestamp() * 1000), 1.1, 1.2, 1.0, 1.15, 10.0),)
        return _CandleBatch(
            rows=rows[:limit],
            provider_symbol="EUR/USD",
            provider_interval="1HOUR" if timeframe == "H1" else "1MIN",
            page_count=1,
            truncated=self.truncated,
        )


def test_adapter_rejects_non_sandbox_environment() -> None:
    """Dukascopy accepts only the SANDBOX environment."""
    bad = BrokerConnectionConfig(
        broker_id=BrokerId.DUKASCOPY,
        environment=BrokerEnvironment.DEMO,
        provider_enabled=True,
        connect_timeout_sec=1,
        request_timeout_sec=1,
        transport_reconnect_max_attempts=0,
        stream_buffer_size=2,
        circuit_failure_threshold=2,
        circuit_recovery_timeout_sec=1,
        circuit_half_open_max_calls=1,
    )
    with pytest.raises(ValueError, match="sandbox-only"):
        DukascopyBrokerAdapter(bad)


def test_adapter_connect_verifies_via_bounded_probe() -> None:
    """A successful bounded EURUSD probe verifies the session."""
    adapter = DukascopyBrokerAdapter(_config(), transport=_FakeTransport())

    async def exercise() -> None:
        result = await adapter.connect()
        assert result.is_success

    asyncio.run(exercise())


def test_adapter_connect_fails_closed_on_transport_error() -> None:
    """A transport failure never reports a successful connection."""
    adapter = DukascopyBrokerAdapter(_config(), transport=_FakeTransport(fails=True))

    async def exercise() -> None:
        result = await adapter.connect()
        assert not result.is_success

    asyncio.run(exercise())


def test_adapter_get_symbols_filters_by_query() -> None:
    """Only fixture-declared symbols matching the query are returned."""
    adapter = DukascopyBrokerAdapter(_config(), transport=_FakeTransport())

    async def exercise() -> None:
        await adapter.connect()
        result = await adapter.get_symbols(query="EUR")
        assert result.data is not None
        assert [item.provider_symbol for item in result.data.items] == ["EURUSD"]
        empty = await adapter.get_symbols(query="ZZZ")
        assert empty.data is not None
        assert empty.data.items == ()

    asyncio.run(exercise())


def test_adapter_get_symbol_info_rejects_undeclared_symbol() -> None:
    """An undeclared symbol raises rather than returning fabricated metadata."""
    adapter = DukascopyBrokerAdapter(_config(), transport=_FakeTransport())

    async def exercise() -> None:
        await adapter.connect()
        result = await adapter.get_symbol_info("GBPUSD")
        assert result.error is not None
        assert result.error.code == BrokerErrorCode.BROKER_REQUEST_INVALID

    asyncio.run(exercise())


def test_adapter_get_ticks_requires_start_and_positive_limit() -> None:
    """Missing start or non-positive limit is rejected before any transport call."""
    adapter = DukascopyBrokerAdapter(_config(), transport=_FakeTransport())

    async def exercise() -> None:
        await adapter.connect()
        result = await adapter.get_ticks("EURUSD", limit=1)
        assert result.error is not None
        assert result.error.code == BrokerErrorCode.BROKER_REQUEST_INVALID

    asyncio.run(exercise())


def test_adapter_get_ticks_maps_bounded_genuine_ticks() -> None:
    """A bounded genuine tick page is mapped from the provider hour file."""
    adapter = DukascopyBrokerAdapter(_config(), transport=_FakeTransport())

    async def exercise() -> None:
        await adapter.connect()
        result = await adapter.get_ticks(
            "EURUSD", start=datetime(2026, 1, 1, tzinfo=UTC), limit=1
        )
        assert result.data is not None
        assert len(result.data.items) == 1
        assert str(result.data.items[0].bid) == "1.0999"

    asyncio.run(exercise())


def test_adapter_maps_bounded_provider_bid_bars() -> None:
    """Dukascopy web-chart BID rows map without invented spread evidence."""
    candle_transport = _FakeCandleTransport()
    adapter = DukascopyBrokerAdapter(
        _config(),
        transport=_FakeTransport(),
        candle_transport=candle_transport,
    )

    async def exercise() -> None:
        await adapter.connect()
        result = await adapter.get_historical_bars(
            "EURUSD",
            "H1",
            start=datetime(2026, 1, 1, tzinfo=UTC),
            end=datetime(2026, 1, 1, 2, tzinfo=UTC),
            limit=1,
        )
        assert result.data is not None
        assert len(result.data.items) == 1
        assert result.data.items[0].open == Decimal("1.1")
        assert result.data.items[0].spread is None
        assert result.data.provider_metadata["offer_side"] == "BID"
        assert result.data.provider_metadata["provider_symbol"] == "EUR/USD"

    asyncio.run(exercise())


def test_adapter_passes_output_limit_to_candle_pagination() -> None:
    """The bar limit bounds web-chart pagination rather than BI5 hour fan-out."""
    candle_transport = _FakeCandleTransport(truncated=True)
    adapter = DukascopyBrokerAdapter(
        _config(),
        transport=_FakeTransport(),
        candle_transport=candle_transport,
    )

    async def exercise() -> None:
        await adapter.connect()
        result = await adapter.get_historical_bars(
            "EURUSD",
            "H1",
            start=datetime(2026, 1, 1, tzinfo=UTC),
            end=datetime(2026, 1, 1, 3, tzinfo=UTC),
            limit=1,
        )
        assert result.data is not None
        assert len(result.data.items) == 1
        assert result.data.truncated
        assert candle_transport.requests[0][-1] == 1

    asyncio.run(exercise())
