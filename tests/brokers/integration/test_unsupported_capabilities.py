"""WF-BRK-008: handle an unsupported operation without a provider call."""

import asyncio

from app.services.brokers import (
    build_broker_connection_config,
    cancel_broker_order,
    create_configured_fake_broker_adapter,
    get_broker_value_field,
)


def _config() -> object:
    return build_broker_connection_config(
        "dukascopy",
        "sandbox",
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
    adapter = create_configured_fake_broker_adapter(_config())

    async def exercise() -> None:
        result = await cancel_broker_order(adapter, "not-a-ticket")
        assert get_broker_value_field(result, "status") != "success"
        error = get_broker_value_field(result, "error")
        assert error is not None
        assert get_broker_value_field(error, "code") == "BROKER_CAPABILITY_UNSUPPORTED"
        details = get_broker_value_field(error, "details")
        assert isinstance(details, dict)
        assert details.get("capability") == "cancel_order"

    asyncio.run(exercise())


def test_unsupported_result_identifies_broker_and_environment() -> None:
    """The unsupported result carries broker/environment identity."""
    adapter = create_configured_fake_broker_adapter(_config())

    async def exercise() -> None:
        result = await cancel_broker_order(adapter, "not-a-ticket")
        metadata = get_broker_value_field(result, "metadata")
        assert metadata is not None
        extensions = get_broker_value_field(metadata, "extensions")
        assert extensions is not None
        assert extensions.get("broker") == "dukascopy"
        assert extensions.get("environment") == "sandbox"

    asyncio.run(exercise())
