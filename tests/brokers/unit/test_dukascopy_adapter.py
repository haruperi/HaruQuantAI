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
from app.services.brokers.dukascopy.adapter import DukascopyBrokerAdapter

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
        DukascopyBrokerAdapter(bad, _capabilities())


def test_adapter_connect_verifies_via_bounded_probe() -> None:
    """A successful bounded EURUSD probe verifies the session."""
    adapter = DukascopyBrokerAdapter(
        _config(), _capabilities(), transport=_FakeTransport()
    )

    async def exercise() -> None:
        result = await adapter.connect()
        assert result.is_success

    asyncio.run(exercise())


def test_adapter_connect_fails_closed_on_transport_error() -> None:
    """A transport failure never reports a successful connection."""
    adapter = DukascopyBrokerAdapter(
        _config(), _capabilities(), transport=_FakeTransport(fails=True)
    )

    async def exercise() -> None:
        result = await adapter.connect()
        assert not result.is_success

    asyncio.run(exercise())


def test_adapter_get_symbols_filters_by_query() -> None:
    """Only fixture-declared symbols matching the query are returned."""
    adapter = DukascopyBrokerAdapter(
        _config(), _capabilities(), transport=_FakeTransport()
    )

    async def exercise() -> None:
        result = await adapter.get_symbols(query="EUR")
        assert result.data is not None
        assert [item.provider_symbol for item in result.data.items] == ["EURUSD"]
        empty = await adapter.get_symbols(query="ZZZ")
        assert empty.data is not None
        assert empty.data.items == ()

    asyncio.run(exercise())


def test_adapter_get_symbol_info_rejects_undeclared_symbol() -> None:
    """An undeclared symbol raises rather than returning fabricated metadata."""
    adapter = DukascopyBrokerAdapter(
        _config(), _capabilities(), transport=_FakeTransport()
    )

    async def exercise() -> None:
        result = await adapter.get_symbol_info("GBPUSD")
        assert result.error is not None
        assert result.error.code == BrokerErrorCode.BROKER_REQUEST_INVALID

    asyncio.run(exercise())


def test_adapter_get_ticks_requires_start_and_positive_limit() -> None:
    """Missing start or non-positive limit is rejected before any transport call."""
    adapter = DukascopyBrokerAdapter(
        _config(), _capabilities(), transport=_FakeTransport()
    )

    async def exercise() -> None:
        result = await adapter.get_ticks("EURUSD", limit=1)
        assert result.error is not None
        assert result.error.code == BrokerErrorCode.BROKER_REQUEST_INVALID

    asyncio.run(exercise())


def test_adapter_get_ticks_maps_bounded_genuine_ticks() -> None:
    """A bounded genuine tick page is mapped from the provider hour file."""
    adapter = DukascopyBrokerAdapter(
        _config(), _capabilities(), transport=_FakeTransport()
    )

    async def exercise() -> None:
        result = await adapter.get_ticks(
            "EURUSD", start=datetime(2026, 1, 1, tzinfo=UTC), limit=1
        )
        assert result.data is not None
        assert len(result.data.items) == 1
        assert str(result.data.items[0].bid) == "1.0999"

    asyncio.run(exercise())


def test_adapter_aggregates_bounded_midpoint_bars_locally() -> None:
    """DEC-BRK-002(a): Dukascopy mapping owns deterministic tick aggregation."""

    class _BarTransport(_FakeTransport):
        async def get_hour(self, symbol: str, hour: object) -> bytes:
            del symbol, hour
            return b"".join(
                (
                    _RECORD.pack(0, 110_010, 109_990, 1.0, 1.0),
                    _RECORD.pack(30_000, 110_030, 110_010, 1.0, 1.0),
                    _RECORD.pack(60_000, 110_020, 110_000, 1.0, 1.0),
                )
            )

    adapter = DukascopyBrokerAdapter(
        _config(), _capabilities(), transport=_BarTransport()
    )

    async def exercise() -> None:
        result = await adapter.get_historical_bars(
            "EURUSD",
            "M1",
            start=datetime(2026, 1, 1, tzinfo=UTC),
            end=datetime(2026, 1, 1, 0, 2, tzinfo=UTC),
            limit=2,
        )
        assert result.data is not None
        assert len(result.data.items) == 2
        assert result.data.items[0].open == Decimal("1.1000")
        assert result.data.items[0].close == Decimal("1.1002")
        assert result.data.provider_metadata["derivation"] == (
            "quote_midpoint_tick_aggregation"
        )

    asyncio.run(exercise())
