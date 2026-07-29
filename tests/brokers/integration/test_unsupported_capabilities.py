"""WF-BRK-008: handle an unsupported operation without a provider call."""

import asyncio

from app.services.brokers import create_broker_adapter
from app.services.brokers.contracts import (
    BrokerCapabilityId,
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerErrorCode,
    BrokerId,
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
    assert created.status == "success"
    adapter = created.data
    assert adapter is not None

    async def exercise() -> None:
        result = await adapter.cancel_order("not-a-ticket")
        assert result.status != "success"
        assert result.error is not None
        assert result.error.code == BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED.value
        assert (
            result.error.details["capability"] == BrokerCapabilityId.CANCEL_ORDER.value
        )

    asyncio.run(exercise())


def test_unsupported_result_identifies_broker_and_environment() -> None:
    """The unsupported result carries broker/environment identity."""
    created = create_broker_adapter(BrokerId.DUKASCOPY, _config())
    assert created.status == "success"
    adapter = created.data
    assert adapter is not None

    async def exercise() -> None:
        result = await adapter.cancel_order("not-a-ticket")
        assert result.metadata.extensions["broker"] == BrokerId.DUKASCOPY.value
        assert (
            result.metadata.extensions["environment"] == BrokerEnvironment.SANDBOX.value
        )

    asyncio.run(exercise())
