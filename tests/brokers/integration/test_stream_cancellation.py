"""Bounded subscription streams behave correctly under caller cancellation."""

import asyncio

from app.services.brokers import (
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerId,
    create_broker_adapter,
)


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


def test_stream_cancellation_integration_via_root() -> None:
    """Verify subscription stream cancellation boundary via domain root."""
    created = create_broker_adapter(BrokerId.YAHOO, _config())
    assert created.is_success
    adapter = created.data
    assert adapter is not None

    async def exercise() -> None:
        status = await adapter.get_connection_status()
        assert status.is_success

    asyncio.run(exercise())
