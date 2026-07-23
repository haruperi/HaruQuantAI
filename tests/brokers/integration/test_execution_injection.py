"""WF-BRK-009: inject a capability-scoped adapter into execution."""

from app.services.brokers import (
    BrokerAdapter,
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerId,
    TradeExecutionProvider,
    create_broker_adapter,
)


def _config(broker_id: BrokerId) -> BrokerConnectionConfig:
    return BrokerConnectionConfig(
        broker_id=broker_id,
        environment=BrokerEnvironment.SANDBOX,
        provider_enabled=True,
        connect_timeout_sec=1,
        request_timeout_sec=1,
        transport_reconnect_max_attempts=0,
        stream_buffer_size=2,
        circuit_failure_threshold=2,
        circuit_recovery_timeout_sec=1,
        circuit_half_open_max_calls=1,
    )


def test_execution_receives_the_canonical_adapter_protocol_not_concrete_apis() -> None:
    """A caller (Trading) only ever needs the canonical BrokerAdapter surface."""
    created = create_broker_adapter(BrokerId.YAHOO, _config(BrokerId.YAHOO))
    assert created.is_success
    adapter = created.data
    assert isinstance(adapter, BrokerAdapter)
    assert isinstance(adapter, TradeExecutionProvider)


def test_capability_scoped_adapter_never_exposes_a_native_sdk_handle() -> None:
    """Concrete adapters expose only canonical protocol members, no raw SDK."""
    from pydantic import SecretStr

    config = BrokerConnectionConfig(
        broker_id=BrokerId.MT5,
        environment=BrokerEnvironment.DEMO,
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
    created = create_broker_adapter(BrokerId.MT5, config)
    assert created.is_success
    adapter = created.data
    assert adapter is not None
    public_members = {name for name in dir(adapter) if not name.startswith("_")}
    forbidden = {"mt5", "MetaTrader5", "terminal", "sdk"}
    assert not forbidden & public_members
