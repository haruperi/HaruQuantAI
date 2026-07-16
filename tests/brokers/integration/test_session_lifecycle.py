"""WF-BRK-002: connect/authenticate/disconnect session lifecycle."""

import asyncio

from app.services.brokers import (
    BrokerCapability,
    BrokerCapabilityId,
    BrokerConnectionConfig,
    BrokerConnectionState,
    BrokerEnvironment,
    BrokerId,
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
        stream_buffer_size=8,
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


def test_session_lifecycle_verifies_and_cleans_up() -> None:
    """Connect verifies a session; disconnect deterministically releases it."""
    adapter = FakeBrokerAdapter(_config(), _capabilities())

    async def exercise() -> None:
        connected = await adapter.connect()
        assert connected.is_success
        status = await adapter.get_connection_status()
        assert status.data is not None
        assert status.data.state == BrokerConnectionState.READY

        disconnected = await adapter.disconnect()
        assert disconnected.is_success
        final_status = await adapter.get_connection_status()
        assert final_status.data is not None
        assert final_status.data.state == BrokerConnectionState.DISCONNECTED

        # Idempotent disconnect never errors.
        again = await adapter.disconnect()
        assert again.is_success

    asyncio.run(exercise())


def test_session_lifecycle_supports_async_context_manager() -> None:
    """The adapter's async context manager connects and always disconnects."""

    async def exercise() -> BrokerConnectionState:
        adapter = FakeBrokerAdapter(_config(), _capabilities())
        async with adapter:
            status = await adapter.get_connection_status()
            assert status.data is not None
            assert status.data.state == BrokerConnectionState.READY
        final_status = await adapter.get_connection_status()
        assert final_status.data is not None
        return final_status.data.state

    assert asyncio.run(exercise()) == BrokerConnectionState.DISCONNECTED
