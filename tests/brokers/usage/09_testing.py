"""Demonstrate FakeBrokerAdapter, the domain's own deterministic test double.

Unlike the other usage scripts in this directory, using ``FakeBrokerAdapter``
here is not a stand-in for a real provider connection — it *is* the real
subject being demonstrated: the documented, in-memory test double that
calling domains (Data, Trading) use in their own tests.
"""

import asyncio
import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.brokers import (
    BrokerCapability,
    BrokerCapabilityId,
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerError,
    BrokerErrorCode,
    BrokerId,
    BrokerQuote,
)
from app.services.brokers.testing import FakeBrokerAdapter


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
            execution_model="FAKE",
        )
        for operation in BrokerCapabilityId
    }


def example_fake_adapter_returns_injected_fixtures() -> None:
    """Illustrate a calling domain injecting a deterministic quote fixture."""
    print("\n1. Injecting a deterministic quote fixture")
    quote = BrokerQuote(
        symbol="EURUSD",
        price_unit="quote_currency",
        quantity_unit="lots",
        retrieved_at=datetime.now(UTC),
        bid=None,
        ask=None,
        last_price=Decimal("1.1000"),
    )
    adapter = FakeBrokerAdapter(
        _config(),
        _capabilities(),
        fixtures={BrokerCapabilityId.GET_QUOTE: quote},
    )

    async def exercise() -> None:
        await adapter.connect()
        result = await adapter.get_quote("EURUSD")
        print("Returned fixture is the same object:", result.data is quote)
        if result.data is not quote:
            raise AssertionError("fake adapter did not return the injected fixture")

    asyncio.run(exercise())


def example_fake_adapter_injects_and_clears_errors() -> None:
    """Illustrate a calling domain injecting, then clearing, a canonical error."""
    print("\n2. Injecting and then clearing a canonical error")
    adapter = FakeBrokerAdapter(_config(), _capabilities())
    error = BrokerError(
        code=BrokerErrorCode.BROKER_SYMBOL_NOT_FOUND, message="not found"
    )

    async def exercise() -> None:
        await adapter.connect()
        adapter.inject_error(BrokerCapabilityId.GET_QUOTE, error)
        first = await adapter.get_quote("EURUSD")
        print("With error injected:", first.status, first.error)
        adapter.inject_error(BrokerCapabilityId.GET_QUOTE, None)
        second = await adapter.get_quote("EURUSD")
        print("After clearing (no fixture registered either):", second.status)

    asyncio.run(exercise())


if __name__ == "__main__":
    example_fake_adapter_returns_injected_fixtures()
    example_fake_adapter_injects_and_clears_errors()
