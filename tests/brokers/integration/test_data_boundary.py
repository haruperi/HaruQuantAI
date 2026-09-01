"""WF-BRK-003: Data receives direct provider truth via read capabilities."""

import asyncio

from app.services.brokers import (
    build_broker_connection_config,
    get_broker_historical_bars,
    get_broker_value_field,
)

from tests.brokers.conformance import create_configured_fake_broker_adapter

_SYMBOL = "AAPL"


def _config() -> object:
    return build_broker_connection_config(
        "yahoo",
        "sandbox",
        provider_enabled=True,
        connect_timeout_sec=1,
        request_timeout_sec=1,
        transport_reconnect_max_attempts=0,
        stream_buffer_size=8,
        circuit_failure_threshold=2,
        circuit_recovery_timeout_sec=1,
        circuit_half_open_max_calls=1,
        probe_symbol=_SYMBOL,
    )


def test_data_boundary_via_root() -> None:
    """Verify data boundary via root API and session gating."""
    adapter = create_configured_fake_broker_adapter(_config())

    async def exercise() -> None:
        # Disconnected call returns BROKER_NOT_CONNECTED
        result = await get_broker_historical_bars(adapter, _SYMBOL, "1d", limit=1)
        assert get_broker_value_field(result, "status") != "success"
        error = get_broker_value_field(result, "error")
        assert error is not None
        assert get_broker_value_field(error, "code") == "BROKER_NOT_CONNECTED"

    asyncio.run(exercise())
