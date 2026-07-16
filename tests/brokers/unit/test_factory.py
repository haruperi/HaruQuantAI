"""Explicit registry factory tests."""

import asyncio
import sys

from app.services.brokers import (
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerErrorCode,
    BrokerId,
)
from app.services.brokers.registry import (
    create_broker_adapter,
    get_registered_brokers,
)


def _config(enabled: bool = True) -> BrokerConnectionConfig:
    return BrokerConnectionConfig(
        broker_id=BrokerId.YAHOO,
        environment=BrokerEnvironment.SANDBOX,
        provider_enabled=enabled,
        connect_timeout_sec=1,
        request_timeout_sec=1,
        transport_reconnect_max_attempts=0,
        stream_buffer_size=2,
        circuit_failure_threshold=2,
        circuit_recovery_timeout_sec=1,
        circuit_half_open_max_calls=1,
    )


def test_listing_does_not_import_optional_sdks() -> None:
    """Listing profiles is static and SDK-free."""
    before = set(sys.modules)
    assert set(get_registered_brokers()) == set(BrokerId)
    assert not ({"MetaTrader5", "binance", "yfinance"} - before) & set(sys.modules)


def test_create_adapter_never_falls_back() -> None:
    """Disabled or mismatched profiles fail before provider import."""
    result = create_broker_adapter(BrokerId.YAHOO, _config(enabled=False))
    assert result.error is not None
    assert result.error.code == BrokerErrorCode.BROKER_CONFIGURATION_INVALID


def test_create_adapter_is_explicit_and_independent() -> None:
    """Each exact factory call creates a new disconnected adapter."""
    first = create_broker_adapter(BrokerId.YAHOO, _config())
    second = create_broker_adapter(BrokerId.YAHOO, _config())
    assert first.is_success
    assert second.is_success
    assert first.data is not second.data


def test_registry_created_adapter_can_connect_and_report_state() -> None:
    """CONNECT and IS_CONNECTED remain attemptable on a fresh registry adapter."""

    async def exercise() -> None:
        adapter = create_broker_adapter(BrokerId.YAHOO, _config()).data
        assert adapter is not None
        connected = await adapter.connect()
        assert connected.is_success
        status = await adapter.is_connected()
        assert status.is_success
        assert status.data is True
        await adapter.disconnect()

    asyncio.run(exercise())


def test_unavailable_provider_call_never_imports_sdk() -> None:
    """The catalogue release gate is enforced before provider transport."""

    async def exercise() -> None:
        result = create_broker_adapter(BrokerId.YAHOO, _config())
        assert result.data is not None
        bars = await result.data.get_historical_bars("AAPL", "1d", limit=1)
        assert bars.error is not None
        assert bars.error.code == BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED
        assert "yfinance" not in sys.modules

    asyncio.run(exercise())


def test_create_adapter_invalid_broker_type() -> None:
    """create_broker_adapter returns BROKER_UNKNOWN when broker_id is not a BrokerId."""
    from typing import Any, cast

    result = create_broker_adapter(cast("Any", "NOT_AN_ID"), _config())
    assert result.error is not None
    assert result.error.code == BrokerErrorCode.BROKER_UNKNOWN


def test_create_adapter_missing_dependency() -> None:
    """create_broker_adapter returns BROKER_DEPENDENCY_MISSING when import fails."""
    from unittest.mock import patch

    fake_factories = {
        BrokerId.YAHOO: (
            "app.services.brokers.nonexistent",
            "YahooBrokerAdapter",
            "nonexistent-pkg",
        )
    }
    with patch("app.services.brokers.registry.factory._FACTORIES", fake_factories):
        result = create_broker_adapter(BrokerId.YAHOO, _config())
        assert result.error is not None
        assert result.error.code == BrokerErrorCode.BROKER_DEPENDENCY_MISSING
        assert result.provider_metadata["package"] == "nonexistent-pkg"
        assert result.provider_metadata["required_version"] is None


def test_create_adapter_dukascopy_missing_dependency() -> None:
    """create_broker_adapter handles package version checks when package is None."""
    from unittest.mock import patch

    fake_factories = {
        BrokerId.DUKASCOPY: (
            "app.services.brokers.nonexistent_dukascopy",
            "DukascopyBrokerAdapter",
            None,
        )
    }
    with patch("app.services.brokers.registry.factory._FACTORIES", fake_factories):
        config = _config()
        config = BrokerConnectionConfig(
            broker_id=BrokerId.DUKASCOPY,
            environment=config.environment,
            provider_enabled=config.provider_enabled,
            connect_timeout_sec=config.connect_timeout_sec,
            request_timeout_sec=config.request_timeout_sec,
            transport_reconnect_max_attempts=config.transport_reconnect_max_attempts,
            stream_buffer_size=config.stream_buffer_size,
            circuit_failure_threshold=config.circuit_failure_threshold,
            circuit_recovery_timeout_sec=config.circuit_recovery_timeout_sec,
            circuit_half_open_max_calls=config.circuit_half_open_max_calls,
        )
        result = create_broker_adapter(BrokerId.DUKASCOPY, config)
        assert result.error is not None
        assert result.error.code == BrokerErrorCode.BROKER_DEPENDENCY_MISSING
        expected_pkg = "app.services.brokers.nonexistent_dukascopy"
        assert result.provider_metadata["package"] == expected_pkg
        assert result.provider_metadata["required_version"] is None


def test_create_adapter_value_error() -> None:
    """create_broker_adapter handles ValueError during adapter instantiation."""
    from typing import Any
    from unittest.mock import patch

    fake_factories = {
        BrokerId.YAHOO: ("app.services.brokers.yahoo", "InvalidClass", "yfinance")
    }

    class MockAdapter:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            del args, kwargs
            raise ValueError("Invalid config")

    with (
        patch("app.services.brokers.registry.factory._FACTORIES", fake_factories),
        patch("app.services.brokers.yahoo.InvalidClass", MockAdapter, create=True),
    ):
        result = create_broker_adapter(BrokerId.YAHOO, _config())
        assert result.error is not None
        assert result.error.code == BrokerErrorCode.BROKER_CONFIGURATION_INVALID
