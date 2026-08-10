"""Dukascopy adapter tests using an injected fake transport."""

import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.services.brokers.canonical_contracts import (
    BrokerCapability,
    BrokerCapabilityId,
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerErrorCode,
    BrokerId,
)
from app.services.brokers.dukascopy.adapter import DukascopyBrokerAdapter
from app.services.brokers.dukascopy.candle_transport import _CandleBatch


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

    async def get_ticks(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
        limit: int,
    ) -> tuple[tuple[object, ...], ...]:
        del symbol, end
        if self._fails:
            raise OSError("network unreachable")
        return ((int(start.timestamp() * 1000), 1.0999, 1.1, 1_000_000, 1_000_000),)[
            :limit
        ]


class _FakeCandleTransport:
    """Return bounded recorded Dukascopy web-chart rows."""

    def __init__(self, *, truncated: bool = False, empty: bool = False) -> None:
        self.truncated = truncated
        self.empty = empty
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
        rows = (
            ()
            if self.empty
            else ((int(start.timestamp() * 1000), 1.1, 1.2, 1.0, 1.15, 10.0),)
        )
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
    """A genuine bounded EUR/USD candle verifies the session."""
    candle_transport = _FakeCandleTransport()
    adapter = DukascopyBrokerAdapter(
        _config(),
        transport=_FakeTransport(),
        candle_transport=candle_transport,
    )

    async def exercise() -> None:
        result = await adapter.connect()
        assert result.status == "success"
        symbol, timeframe, start, end, limit = candle_transport.requests[0]
        assert (symbol, timeframe, limit) == ("EURUSD", "H1", 1)
        assert end - start == timedelta(days=7)

    asyncio.run(exercise())


def test_adapter_connect_fails_closed_on_transport_error() -> None:
    """An empty provider response never reports a successful connection."""
    adapter = DukascopyBrokerAdapter(
        _config(),
        transport=_FakeTransport(),
        candle_transport=_FakeCandleTransport(empty=True),
    )

    async def exercise() -> None:
        result = await adapter.connect()
        assert result.status != "success"

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
        assert result.error.code == BrokerErrorCode.BROKER_REQUEST_INVALID.value

    asyncio.run(exercise())


def test_adapter_get_ticks_requires_start_and_positive_limit() -> None:
    """Missing start or non-positive limit is rejected before any transport call."""
    adapter = DukascopyBrokerAdapter(_config(), transport=_FakeTransport())

    async def exercise() -> None:
        await adapter.connect()
        result = await adapter.get_ticks("EURUSD", limit=1)
        assert result.error is not None
        assert result.error.code == BrokerErrorCode.BROKER_REQUEST_INVALID.value

    asyncio.run(exercise())


def test_adapter_bars_reject_invalid_bounds_cursor_and_limit() -> None:
    """Every caller-controlled bar bound fails before provider access."""
    adapter = DukascopyBrokerAdapter(
        _config(),
        transport=_FakeTransport(),
        candle_transport=_FakeCandleTransport(),
    )

    async def exercise() -> None:
        await adapter.connect()
        start = datetime(2026, 1, 1, tzinfo=UTC)
        end = datetime(2026, 1, 1, 1, tzinfo=UTC)
        assert (
            await adapter.get_historical_bars("EURUSD", "H1", limit=1)
        ).error is not None
        assert (
            await adapter.get_historical_bars(
                "EURUSD", "H1", start, end, cursor="cursor", limit=1
            )
        ).error is not None
        assert (
            await adapter.get_historical_bars("EURUSD", "H1", start, end, limit=0)
        ).error is not None

    asyncio.run(exercise())


def test_adapter_get_ticks_maps_bounded_genuine_ticks() -> None:
    """A bounded genuine tick page is mapped from the provider hour file."""
    adapter = DukascopyBrokerAdapter(_config(), transport=_FakeTransport())

    async def exercise() -> None:
        await adapter.connect()
        result = await adapter.get_ticks(
            "EURUSD",
            start=datetime(2026, 1, 1, tzinfo=UTC),
            end=datetime(2026, 1, 1, 1, tzinfo=UTC),
            limit=1,
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
