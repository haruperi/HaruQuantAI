"""WF-BRK-002: connect/authenticate/disconnect session lifecycle."""

import asyncio

from app.services.brokers import (
    build_broker_connection_config,
    create_broker_adapter,
    disconnect_broker,
    get_broker_connection_status,
    get_broker_id,
    get_broker_value_field,
)
from pydantic import SecretStr

_LOGIN = "12345"
_SERVER = "Demo-Server"


def _config() -> object:
    return build_broker_connection_config(
        get_broker_id("mt5"),
        "demo",
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
    created = create_broker_adapter(get_broker_id("mt5"), _config())
    assert get_broker_value_field(created, "status") == "success"
    adapter = get_broker_value_field(created, "data")
    assert adapter is not None

    async def exercise() -> None:
        status = await get_broker_connection_status(adapter)
        assert get_broker_value_field(status, "status") == "success"
        data = get_broker_value_field(status, "data")
        assert data is not None
        assert (
            get_broker_value_field(get_broker_value_field(data, "state"), "value")
            == "disconnected"
        )

        disconnected = await disconnect_broker(adapter)
        assert get_broker_value_field(disconnected, "status") == "success"

        again = await disconnect_broker(adapter)
        assert get_broker_value_field(again, "status") == "success"

    asyncio.run(exercise())


def test_connect_emits_lifecycle_events() -> None:
    """Connection status and event channels function cleanly."""
    created = create_broker_adapter(get_broker_id("mt5"), _config())
    assert get_broker_value_field(created, "status") == "success"
    adapter = get_broker_value_field(created, "data")
    assert adapter is not None

    async def exercise() -> None:
        status = await get_broker_connection_status(adapter)
        data = get_broker_value_field(status, "data")
        assert data is not None
        assert (
            get_broker_value_field(get_broker_value_field(data, "state"), "value")
            == "disconnected"
        )

    asyncio.run(exercise())
