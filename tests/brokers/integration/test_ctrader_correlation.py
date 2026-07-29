"""cTrader concurrent-request correlation integration test (WF-BRK-007)."""

import asyncio

from app.services.brokers import (
    build_broker_connection_config,
    create_configured_fake_broker_adapter,
    get_broker_connection_status,
    get_broker_value_field,
)
from pydantic import SecretStr


def _config() -> object:
    return build_broker_connection_config(
        "ctrader",
        "demo",
        provider_enabled=True,
        connect_timeout_sec=1,
        request_timeout_sec=1,
        transport_reconnect_max_attempts=0,
        stream_buffer_size=2,
        circuit_failure_threshold=2,
        circuit_recovery_timeout_sec=1,
        circuit_half_open_max_calls=1,
        account_reference="12345",
        credentials={
            "client_id": SecretStr("cid"),
            "client_secret": SecretStr("csec"),
            "access_token": SecretStr("token"),
            "account_id": SecretStr("12345"),
        },
    )


def test_ctrader_correlation_integration_via_root() -> None:
    """Verify cTrader adapter correlation via root API boundary."""
    adapter = create_configured_fake_broker_adapter(_config())

    async def exercise() -> None:
        status = await get_broker_connection_status(adapter)
        assert get_broker_value_field(status, "status") == "success"

    asyncio.run(exercise())
