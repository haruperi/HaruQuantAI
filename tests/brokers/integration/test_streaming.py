"""WF-BRK-006: stream provider and connection events."""

import asyncio

from app.services.brokers import (
    build_broker_connection_config,
    create_broker_adapter,
    get_broker_id,
    get_broker_value_field,
    subscribe_broker_quotes,
)
from pydantic import SecretStr

_BUFFER_SIZE = 2
_SYMBOL = "BTCUSDT"


def _config() -> object:
    return build_broker_connection_config(
        get_broker_id("binance_spot"),
        "testnet",
        provider_enabled=True,
        connect_timeout_sec=1,
        request_timeout_sec=1,
        transport_reconnect_max_attempts=0,
        stream_buffer_size=_BUFFER_SIZE,
        circuit_failure_threshold=2,
        circuit_recovery_timeout_sec=1,
        circuit_half_open_max_calls=1,
        credentials={
            "api_key": SecretStr("offline-key"),
            "api_secret": SecretStr("offline-secret"),
        },
    )


def test_streaming_boundary_via_root() -> None:
    """Verify streaming boundary behavior via domain root API."""
    created = create_broker_adapter(get_broker_id("binance_spot"), _config())
    assert get_broker_value_field(created, "status") == "success"
    adapter = get_broker_value_field(created, "data")
    assert adapter is not None

    async def exercise() -> None:
        # Unreleased subscribe_quotes returns BROKER_CAPABILITY_UNSUPPORTED
        result = await subscribe_broker_quotes(adapter, (_SYMBOL,))
        assert get_broker_value_field(result, "status") != "success"
        error = get_broker_value_field(result, "error")
        assert error is not None
        assert get_broker_value_field(error, "code") == "BROKER_CAPABILITY_UNSUPPORTED"

    asyncio.run(exercise())
