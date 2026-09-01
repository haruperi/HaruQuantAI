"""WF-BRK-009: inject a capability-scoped adapter into execution."""

from app.services.brokers import (
    build_broker_connection_config,
)
from pydantic import SecretStr

from tests.brokers.conformance import create_configured_fake_broker_adapter


def _config(broker_id: str) -> object:
    return build_broker_connection_config(
        broker_id,
        "sandbox" if broker_id == "yahoo" else "demo",
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
            "login": SecretStr("12345"),
            "password": SecretStr("hunter2"),
            "server": SecretStr("Demo-Server"),
        },
    )


def test_execution_receives_the_canonical_adapter_protocol_not_concrete_apis() -> None:
    """A caller (Trading) only ever needs the canonical BrokerAdapter surface."""
    adapter = create_configured_fake_broker_adapter(_config("yahoo"))
    assert adapter is not None
    public_members = {name for name in dir(adapter) if not name.startswith("_")}
    mutation_primitives = {
        "place_order",
        "cancel_order",
        "modify_order",
        "close_position",
    }
    assert mutation_primitives <= public_members


def test_capability_scoped_adapter_never_exposes_a_native_sdk_handle() -> None:
    """Concrete adapters expose only canonical protocol members, no raw SDK."""
    adapter = create_configured_fake_broker_adapter(_config("mt5"))
    assert adapter is not None
    public_members = {name for name in dir(adapter) if not name.startswith("_")}
    forbidden = {"mt5", "MetaTrader5", "terminal", "sdk"}
    assert not forbidden & public_members
