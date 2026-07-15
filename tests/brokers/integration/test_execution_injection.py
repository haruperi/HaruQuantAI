"""WF-BRK-009: inject a capability-scoped adapter into execution."""

from app.services.brokers import (
    BrokerAdapter,
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerId,
    TradeExecutionProvider,
    create_broker_adapter,
)
from app.services.brokers.mt5.adapter import MT5BrokerAdapter


def _config() -> BrokerConnectionConfig:
    return BrokerConnectionConfig(
        broker_id=BrokerId.YAHOO,
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
    adapter = create_broker_adapter(BrokerId.YAHOO, _config()).data
    assert isinstance(adapter, BrokerAdapter)
    assert isinstance(adapter, TradeExecutionProvider)


def test_capability_scoped_adapter_never_exposes_a_native_sdk_handle() -> None:
    """Concrete adapters expose only canonical protocol members, no raw SDK."""
    public_members = {
        name for name in dir(MT5BrokerAdapter) if not name.startswith("_")
    }
    forbidden = {"mt5", "MetaTrader5", "terminal", "sdk"}
    assert not forbidden & public_members
