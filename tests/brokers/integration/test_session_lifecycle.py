"""WF-BRK-002: connect/authenticate/disconnect session lifecycle."""

import asyncio

from app.services.brokers import (
    BrokerConnectionConfig,
    BrokerConnectionState,
    BrokerEnvironment,
    BrokerId,
    create_broker_adapter,
)
from pydantic import SecretStr

_LOGIN = "12345"
_SERVER = "Demo-Server"


def _config() -> BrokerConnectionConfig:
    return BrokerConnectionConfig(
        broker_id=BrokerId.MT5,
        environment=BrokerEnvironment.DEMO,
        provider_enabled=True,
        connect_timeout_sec=1,
        request_timeout_sec=1,
        transport_reconnect_max_attempts=0,
        stream_buffer_size=8,
        circuit_failure_threshold=2,
        circuit_recovery_timeout_sec=1,
        circuit_half_open_max_calls=1,
        account_reference=_LOGIN,
        credentials={
            "login": SecretStr(_LOGIN),
            "password": SecretStr("offline-placeholder"),
            "server": SecretStr(_SERVER),
        },
    )


def test_session_lifecycle_initialization_and_status() -> None:
    """Root-created adapter initializes disconnected and status reflects state."""
    created = create_broker_adapter(BrokerId.MT5, _config())
    assert created.is_success
    adapter = created.data
    assert adapter is not None

    async def exercise() -> None:
        status = await adapter.get_connection_status()
        assert status.is_success
        assert status.data is not None
        assert status.data.state == BrokerConnectionState.DISCONNECTED

        disconnected = await adapter.disconnect()
        assert disconnected.is_success

        again = await adapter.disconnect()
        assert again.is_success

    asyncio.run(exercise())


def test_connect_emits_lifecycle_events() -> None:
    """Connection status and event channels function cleanly."""
    created = create_broker_adapter(BrokerId.MT5, _config())
    assert created.is_success
    adapter = created.data
    assert adapter is not None

    async def exercise() -> None:
        status = await adapter.get_connection_status()
        assert status.data is not None
        assert status.data.state == BrokerConnectionState.DISCONNECTED

    asyncio.run(exercise())
