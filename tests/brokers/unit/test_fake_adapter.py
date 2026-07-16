"""Deterministic fake adapter tests."""

import asyncio

from app.services.brokers import (
    BrokerAdapter,
    BrokerCapabilityId,
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerError,
    BrokerErrorCode,
    BrokerId,
)
from app.services.brokers.registry import get_broker_capability_catalogue
from app.services.brokers.testing import FakeBrokerAdapter


def _fake() -> FakeBrokerAdapter:
    config = BrokerConnectionConfig(
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
    capabilities = {
        item.capability: item
        for item in get_broker_capability_catalogue()[BrokerId.YAHOO]
    }
    return FakeBrokerAdapter(
        config,
        capabilities,
        fixtures={BrokerCapabilityId.GET_QUOTE: "fixture"},
    )


def test_fake_adapter_implements_complete_protocol() -> None:
    """The fake structurally exposes every adapter operation."""
    fake = _fake()
    assert isinstance(fake, BrokerAdapter)
    assert all(hasattr(fake, operation.value) for operation in BrokerCapabilityId)


def test_fake_adapter_error_injection() -> None:
    """One injected failure affects only the selected operation."""

    async def exercise() -> None:
        fake = _fake()
        fake.inject_error(
            BrokerCapabilityId.GET_QUOTE,
            BrokerError(code=BrokerErrorCode.BROKER_TIMEOUT, message="timeout"),
        )
        result = await fake.get_quote("A")
        assert result.error is not None
        assert result.error.code == BrokerErrorCode.BROKER_TIMEOUT

    asyncio.run(exercise())
