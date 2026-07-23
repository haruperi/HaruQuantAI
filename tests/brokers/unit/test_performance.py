"""Bounded-work and latency-separation tests (NFR-BRK-010).

No numeric latency target is asserted; only that local adapter work stays
bounded and that provider/adapter latency are represented as separate fields.
"""

import asyncio
import time
from datetime import UTC, datetime

import pytest
from app.services.brokers import (
    BrokerCapability,
    BrokerCapabilityId,
    BrokerConnectionConfig,
    BrokerConnectionState,
    BrokerEnvironment,
    BrokerErrorCode,
    BrokerId,
    BrokerResult,
)
from app.services.brokers.adapter_runtime.circuit_breaker import (
    _TransportCircuitBreaker,
)
from app.services.brokers.yahoo_history.adapter import YahooBrokerAdapter


def _config() -> BrokerConnectionConfig:
    return BrokerConnectionConfig(
        broker_id=BrokerId.YAHOO,
        environment=BrokerEnvironment.SANDBOX,
        provider_enabled=True,
        connect_timeout_sec=1,
        request_timeout_sec=1,
        transport_reconnect_max_attempts=0,
        stream_buffer_size=2,
        circuit_failure_threshold=2,
        circuit_recovery_timeout_sec=1,
        circuit_half_open_max_calls=1,
        probe_symbol="AAPL",
    )


def _capabilities() -> dict[BrokerCapabilityId, BrokerCapability]:
    mutations = {
        BrokerCapabilityId.CHECK_ORDER,
        BrokerCapabilityId.PLACE_ORDER,
        BrokerCapabilityId.MODIFY_ORDER,
        BrokerCapabilityId.CANCEL_ORDER,
        BrokerCapabilityId.MODIFY_POSITION,
        BrokerCapabilityId.CLOSE_POSITION,
        BrokerCapabilityId.REPLACE_ORDER,
    }
    return {
        operation: BrokerCapability(
            capability=operation,
            implementation_status="IMPLEMENTED",
            availability="UNAVAILABLE" if operation in mutations else "AVAILABLE",
            access_mode="WRITE" if operation in mutations else "READ",
            requirement="NONE",
            verification_status="NOT_TESTED",
            execution_model="TEST_DOUBLE",
            reason="test release gate" if operation in mutations else None,
        )
        for operation in BrokerCapabilityId
    }


class _Table:
    def __init__(self) -> None:
        self._rows = [
            (
                datetime(2026, 1, 1, tzinfo=UTC),
                {"Open": 1, "High": 2, "Low": 0.5, "Close": 1.5, "Volume": 3},
            )
        ]

    def iterrows(self) -> object:
        return iter(self._rows)


class _SlowTransport:
    """Spend a measurable, bounded interval inside the provider call.

    When a latency sink is supplied the stub reports its provider-call time the
    same way every real transport does, so the adapter's separation of provider
    latency from local overhead is exercised end to end.
    """

    PROVIDER_DELAY_SEC = 0.02

    def __init__(self, latency_sink: object | None = None) -> None:
        self._latency_sink = latency_sink

    async def history(
        self, *, symbol: str, timeframe: str, start: object, end: object
    ) -> object:
        del symbol, timeframe, start, end
        started = time.perf_counter()
        await asyncio.sleep(self.PROVIDER_DELAY_SEC)
        if self._latency_sink is not None:
            self._latency_sink((time.perf_counter() - started) * 1000.0)  # type: ignore[operator]
        return _Table()


def test_adapter_populates_measured_latency() -> None:
    """The adapter measures real elapsed time instead of reporting zero."""

    async def exercise() -> BrokerResult[object]:
        adapter = YahooBrokerAdapter(_config(), transport=_SlowTransport())
        adapter._state = BrokerConnectionState.READY
        return await adapter.get_historical_bars("AAPL", "1d", limit=1)

    result = asyncio.run(exercise())
    assert result.is_success, result.error
    assert result.latency_ms > 0.0
    assert result.adapter_overhead_ms > 0.0


def test_adapter_separates_provider_latency_from_local_overhead() -> None:
    """Provider network time is reported separately from adapter overhead."""

    async def exercise() -> BrokerResult[object]:
        adapter = YahooBrokerAdapter(_config())
        adapter._transport = _SlowTransport(adapter._record_provider_latency)  # type: ignore[assignment]
        adapter._state = BrokerConnectionState.READY
        return await adapter.get_historical_bars("AAPL", "1d", limit=1)

    result = asyncio.run(exercise())
    assert result.provider_latency_ms is not None
    # The provider call dominates, but the two components stay distinct and sum
    # to the measured total.
    assert result.provider_latency_ms > 0.0
    assert result.provider_latency_ms <= result.latency_ms
    assert result.adapter_overhead_ms == pytest.approx(
        result.latency_ms - result.provider_latency_ms, abs=1e-6
    )


def test_unsupported_operation_does_not_inherit_a_previous_measurement() -> None:
    """A fail-closed gate reports no borrowed latency from an earlier call."""
    capabilities = _capabilities()
    capabilities[BrokerCapabilityId.GET_ORDER_BOOK] = BrokerCapability(
        capability=BrokerCapabilityId.GET_ORDER_BOOK,
        implementation_status="NOT_IMPLEMENTED",
        availability="UNAVAILABLE",
        access_mode="READ",
        requirement="NONE",
        verification_status="NOT_TESTED",
        execution_model="PROVIDER_CALL",
    )

    async def exercise() -> BrokerResult[object]:
        adapter = YahooBrokerAdapter(_config(), transport=_SlowTransport())
        adapter._capabilities = capabilities
        adapter._state = BrokerConnectionState.READY
        await adapter.get_historical_bars("AAPL", "1d", limit=1)
        return await adapter.get_order_book("AAPL")

    result = asyncio.run(exercise())
    assert not result.is_success
    assert result.latency_ms == 0.0
    assert result.provider_latency_ms is None


def test_circuit_breaker_before_call_is_bounded_under_repeated_use() -> None:
    """Repeated admission checks complete without unbounded growth in work."""

    async def exercise() -> float:
        circuit = _TransportCircuitBreaker(
            failure_threshold=1_000_000,
            recovery_timeout_sec=1,
            half_open_max_calls=1,
        )
        started = time.monotonic()
        for _ in range(1_000):
            assert await circuit.before_call() is None
            await circuit.record_success()
        return time.monotonic() - started

    elapsed = asyncio.run(exercise())
    assert elapsed < 5.0


def test_non_qualifying_failure_code_is_excluded_from_transport_accounting() -> None:
    """Structural error codes never contribute to circuit-breaker bookkeeping."""

    async def exercise() -> None:
        circuit = _TransportCircuitBreaker(
            failure_threshold=1,
            recovery_timeout_sec=1,
            half_open_max_calls=1,
        )
        for _ in range(100):
            await circuit.record_failure(BrokerErrorCode.BROKER_REQUEST_INVALID)
        assert circuit.state == "closed"

    asyncio.run(exercise())
