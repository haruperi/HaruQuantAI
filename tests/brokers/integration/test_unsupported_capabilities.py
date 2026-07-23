"""WF-BRK-008: handle an unsupported operation without a provider call."""

import asyncio

from app.services.brokers import (
    BrokerCapabilityId,
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerErrorCode,
    BrokerId,
    create_broker_adapter,
)


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
    """An unreleased mutation returns a deterministic error from root API."""
    created = create_broker_adapter(BrokerId.DUKASCOPY, _config())
    assert created.is_success
    adapter = created.data
    assert adapter is not None

    async def exercise() -> None:
        result = await adapter.cancel_order("not-a-ticket")
        assert not result.is_success
        assert result.error is not None
        assert result.error.code == BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED
        assert result.error.capability == BrokerCapabilityId.CANCEL_ORDER

    asyncio.run(exercise())


def test_unsupported_result_identifies_broker_and_environment() -> None:
    """The unsupported result carries broker/environment identity."""
    created = create_broker_adapter(BrokerId.DUKASCOPY, _config())
    assert created.is_success
    adapter = created.data
    assert adapter is not None

    async def exercise() -> None:
        result = await adapter.cancel_order("not-a-ticket")
        assert result.broker == BrokerId.DUKASCOPY
        assert result.environment == BrokerEnvironment.SANDBOX

    asyncio.run(exercise())
