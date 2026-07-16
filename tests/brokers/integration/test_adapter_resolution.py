"""Explicit adapter resolution workflow test."""

from app.services.brokers import (
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerId,
    create_broker_adapter,
)


def test_adapter_resolution_is_explicit_and_isolated() -> None:
    """The registry returns independent exact-profile adapter instances."""
    config = BrokerConnectionConfig(
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
    first = create_broker_adapter(BrokerId.YAHOO, config)
    second = create_broker_adapter(BrokerId.YAHOO, config)
    assert first.is_success
    assert second.is_success
    assert first.data is not second.data
