"""Bounded-work and latency-separation tests (NFR-BRK-010).

No numeric latency target is asserted; only that local adapter work stays
bounded and that provider/adapter latency are represented as separate fields.
"""

import asyncio
import time
from datetime import UTC, datetime

from app.services.brokers import (
    BrokerCapabilityId,
    BrokerEnvironment,
    BrokerErrorCode,
    BrokerId,
    BrokerResult,
)
from app.services.brokers.runtime.circuit_breaker import _TransportCircuitBreaker

REQUEST_ID = "req-b4b8aa60-ba17-4561-884b-138c6074c5fb"


def test_broker_result_separates_provider_and_adapter_latency() -> None:
    """Provider network latency and local adapter overhead are distinct fields."""
    result: BrokerResult[None] = BrokerResult(
        status="success",
        broker=BrokerId.YAHOO,
        operation=BrokerCapabilityId.GET_HISTORICAL_BARS,
        request_id=REQUEST_ID,
        timestamp=datetime.now(UTC),
        environment=BrokerEnvironment.SANDBOX,
        adapter_version="1.0.0",
        latency_ms=12.5,
        provider_latency_ms=10.0,
        adapter_overhead_ms=2.5,
    )
    assert result.latency_ms == 12.5
    assert result.provider_latency_ms == 10.0
    assert result.adapter_overhead_ms == 2.5


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
