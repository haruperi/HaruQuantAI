"""Explicit adapter resolution workflow test."""

from app.services.brokers import (
    build_broker_connection_config,
    create_broker_adapter,
    get_broker_id,
    get_broker_value_field,
)
from pydantic import SecretStr

_LOGIN = "12345"
_SERVER = "Demo-Server"


def test_adapter_resolution_is_explicit_and_isolated() -> None:
    """The registry returns independent exact-profile adapter instances."""
    broker_id = get_broker_id("mt5")
    config = build_broker_connection_config(
        broker_id,
        "demo",
        provider_enabled=True,
        connect_timeout_sec=1,
        request_timeout_sec=1,
        transport_reconnect_max_attempts=0,
        stream_buffer_size=2,
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
    first = create_broker_adapter(broker_id, config)
    second = create_broker_adapter(broker_id, config)
    assert get_broker_value_field(first, "status") == "success"
    assert get_broker_value_field(second, "status") == "success"
    assert get_broker_value_field(first, "data") is not get_broker_value_field(
        second, "data"
    )
