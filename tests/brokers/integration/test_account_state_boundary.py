"""WF-BRK-005: read account and execution state."""

import asyncio

from app.services.brokers import (
    build_broker_connection_config,
    build_broker_position_filter,
    get_broker_account_info,
    get_broker_positions,
    get_broker_value_field,
)
from pydantic import SecretStr

from tests.brokers.conformance import create_configured_fake_broker_adapter

_LOGIN = "12345"
_SERVER = "Demo-Server"


def _config() -> object:
    return build_broker_connection_config(
        "mt5",
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


def test_account_and_execution_state_boundary_from_root() -> None:
    """Root-created adapter handles session gating and account reads safely."""
    adapter = create_configured_fake_broker_adapter(_config())

    async def exercise() -> None:
        # Disconnected operations return BROKER_NOT_CONNECTED
        res_acc = await get_broker_account_info(adapter)
        assert get_broker_value_field(res_acc, "status") != "success"
        error_acc = get_broker_value_field(res_acc, "error")
        assert error_acc is not None
        assert get_broker_value_field(error_acc, "code") == "BROKER_NOT_CONNECTED"

        res_pos = await get_broker_positions(adapter, build_broker_position_filter())
        assert get_broker_value_field(res_pos, "status") != "success"
        error_pos = get_broker_value_field(res_pos, "error")
        assert error_pos is not None
        assert get_broker_value_field(error_pos, "code") == "BROKER_NOT_CONNECTED"

    asyncio.run(exercise())
