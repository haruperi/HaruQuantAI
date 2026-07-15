"""WF-BRK-008: handle an unsupported operation without a provider call."""

import asyncio

from app.services.brokers import (
    BrokerCapabilityId,
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerErrorCode,
    BrokerId,
)
from app.services.brokers.testing import FakeBrokerAdapter


def _config() -> BrokerConnectionConfig:
    return BrokerConnectionConfig(
        broker_id=BrokerId.DUKASCOPY,
        environment=BrokerEnvironment.SANDBOX,
        provider_enabled=True,
        connect_timeout_sec=1,
        request_timeout_sec=1,
        transport_reconnect_max_attempts=0,
        stream_buffer_size=8,
        circuit_failure_threshold=2,
        circuit_recovery_timeout_sec=1,
        circuit_half_open_max_calls=1,
    )


def test_unsupported_operation_never_calls_provider() -> None:
    """An operation with no registered fixture returns a deterministic error."""
    adapter = FakeBrokerAdapter(_config(), {})

    async def exercise() -> None:
        result = await adapter.place_order(object())
        assert not result.is_success
        assert result.error is not None
        assert result.error.code == BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED
        assert result.error.capability == BrokerCapabilityId.PLACE_ORDER

    asyncio.run(exercise())


def test_unsupported_result_identifies_broker_and_environment() -> None:
    """The unsupported result still carries broker/environment identity."""
    adapter = FakeBrokerAdapter(_config(), {})

    async def exercise() -> None:
        result = await adapter.get_order_book("EURUSD")
        assert result.broker == BrokerId.DUKASCOPY
        assert result.environment == BrokerEnvironment.SANDBOX

    asyncio.run(exercise())
