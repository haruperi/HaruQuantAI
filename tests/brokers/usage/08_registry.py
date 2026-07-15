"""Demonstrate the explicit broker registry: listing and adapter creation."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.brokers import (
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerErrorCode,
    BrokerId,
    create_broker_adapter,
    get_registered_brokers,
)


def _config(broker_id: BrokerId, *, enabled: bool = True) -> BrokerConnectionConfig:
    return BrokerConnectionConfig(
        broker_id=broker_id,
        environment=BrokerEnvironment.SANDBOX,
        provider_enabled=enabled,
        connect_timeout_sec=5,
        request_timeout_sec=5,
        transport_reconnect_max_attempts=0,
        stream_buffer_size=4,
        circuit_failure_threshold=2,
        circuit_recovery_timeout_sec=1,
        circuit_half_open_max_calls=1,
    )


def example_list_registered_brokers_without_importing_sdks() -> None:
    """Illustrate listing every registered profile without importing an SDK."""
    print("\n1. Listing registered broker profiles")
    import sys as _sys

    before = set(_sys.modules)
    brokers = get_registered_brokers()
    print("Registered brokers:", [broker.value for broker in brokers])
    imported = {"MetaTrader5", "yfinance", "binance"} & (set(_sys.modules) - before)
    if imported:
        raise AssertionError(f"listing unexpectedly imported: {imported}")


def example_disabled_provider_fails_before_import() -> None:
    """Illustrate a disabled provider failing closed before any import."""
    print("\n2. A disabled provider is rejected before import")
    disabled_config = _config(BrokerId.YAHOO, enabled=False)
    result = create_broker_adapter(BrokerId.YAHOO, disabled_config)
    print("Result:", result.status, result.error.code if result.error else None)
    expected = BrokerErrorCode.BROKER_CONFIGURATION_INVALID
    if result.error is None or result.error.code != expected:
        raise AssertionError("disabled provider was not rejected as expected")


def example_each_factory_call_returns_an_independent_adapter() -> None:
    """Illustrate that each factory call returns a new, independent adapter."""
    print("\n3. Every factory call returns an independent adapter")
    first = create_broker_adapter(BrokerId.YAHOO, _config(BrokerId.YAHOO))
    second = create_broker_adapter(BrokerId.YAHOO, _config(BrokerId.YAHOO))
    print("Same instance?", first.data is second.data)
    if first.data is second.data:
        raise AssertionError("factory returned the same adapter instance twice")


if __name__ == "__main__":
    example_list_registered_brokers_without_importing_sdks()
    example_disabled_provider_fails_before_import()
    example_each_factory_call_returns_an_independent_adapter()
