"""Runnable broker public API usage examples."""

from app.services.brokers import (
    BrokerCapabilityId,
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerId,
    YahooBrokerAdapter,
    create_broker_adapter,
)


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


def test_usage_public_api_and_lazy_adapter_type() -> None:
    """Resolve a type lazily and obtain instances through the registry."""
    result = create_broker_adapter(BrokerId.YAHOO, _config())
    assert isinstance(result.data, YahooBrokerAdapter)


def test_usage_enums_capability_id() -> None:
    """Use stable operation identifiers for capability checks."""
    assert BrokerCapabilityId.GET_HISTORICAL_BARS.value == "get_historical_bars"
