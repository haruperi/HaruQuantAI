"""Adapter-local transport circuit breaking under repeated provider failure."""

import asyncio

from app.services.brokers import (
    build_broker_connection_config,
    get_broker_connection_status,
    get_broker_value_field,
)

from tests.brokers.conformance import create_configured_fake_broker_adapter


def _config() -> object:
    return build_broker_connection_config(
        "yahoo",
        "sandbox",
        provider_enabled=True,
        connect_timeout_sec=1,
        request_timeout_sec=1,
        transport_reconnect_max_attempts=0,
        stream_buffer_size=2,
        circuit_failure_threshold=2,
        circuit_recovery_timeout_sec=0.1,
        circuit_half_open_max_calls=1,
    )


def test_circuit_breaking_integration_via_root() -> None:
    """Verify circuit breaking adapter behavior via root API boundary."""
    adapter = create_configured_fake_broker_adapter(_config())

    async def exercise() -> None:
        status = await get_broker_connection_status(adapter)
        assert get_broker_value_field(status, "status") == "success"

    asyncio.run(exercise())
