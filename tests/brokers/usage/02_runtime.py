"""Demonstrate the adapter-local circuit breaker and bounded subscription."""

import asyncio
import importlib
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.brokers import (
    BrokerCapabilityId,
    BrokerEnvironment,
    BrokerErrorCode,
    BrokerId,
    BrokerSubscriptionInfo,
)
from app.services.brokers.runtime.circuit_breaker import _TransportCircuitBreaker
from app.services.brokers.runtime.subscription import _BrokerSubscription


def example_circuit_breaker_opens_after_qualifying_failures() -> None:
    """Illustrate the circuit opening after consecutive transport failures."""
    print("\n1. Circuit breaker opens after qualifying failures")

    async def exercise() -> str:
        circuit = _TransportCircuitBreaker(
            failure_threshold=2,
            recovery_timeout_sec=0.05,
            half_open_max_calls=1,
        )
        for _ in range(2):
            blocked = await circuit.before_call()
            if blocked is not None:
                raise AssertionError("circuit blocked before threshold was reached")
            await circuit.record_failure(BrokerErrorCode.BROKER_CONNECTION_LOST)
        return circuit.state

    state = asyncio.run(exercise())
    print("Circuit state after 2 qualifying failures:", state)
    if state != "open":
        raise AssertionError("circuit did not open as expected")


def example_bounded_subscription_delivers_fifo_events() -> None:
    """Illustrate one bounded FIFO subscription stream."""
    print("\n2. Bounded subscription delivers events in FIFO order")

    async def exercise() -> list[int]:
        subscription = _BrokerSubscription[int](
            broker=BrokerId.YAHOO,
            environment=BrokerEnvironment.SANDBOX,
            adapter_version="1.0.0",
            info=BrokerSubscriptionInfo(
                subscription_id="usage-sub",
                capability=BrokerCapabilityId.SUBSCRIBE_QUOTES,
                symbols=("EURUSD",),
                created_at=datetime.now(UTC),
                buffer_size=4,
            ),
        )
        await subscription.publish(1)
        await subscription.publish(2)
        await subscription.unsubscribe()
        return [event async for event in subscription.events()]

    events = asyncio.run(exercise())
    print("Delivered events:", events)
    if events != [1, 2]:
        raise AssertionError("events were not delivered in FIFO order")


def example_runtime_package_has_no_public_surface() -> None:
    """Illustrate that the private runtime package exports nothing."""
    print("\n3. The runtime package initializer is private")
    runtime = importlib.import_module("app.services.brokers.runtime")
    print("runtime.__all__:", runtime.__all__)
    if runtime.__all__ != []:
        raise AssertionError("runtime package unexpectedly exports a public symbol")


if __name__ == "__main__":
    example_circuit_breaker_opens_after_qualifying_failures()
    example_bounded_subscription_delivers_fifo_events()
    example_runtime_package_has_no_public_surface()
