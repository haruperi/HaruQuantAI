"""WF-BRK-003: Data receives direct provider truth via read capabilities."""

import asyncio

from app.services.brokers import (
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerErrorCode,
    BrokerId,
    create_broker_adapter,
)

_SYMBOL = "AAPL"


def _config() -> BrokerConnectionConfig:
    return BrokerConnectionConfig(
        broker_id=BrokerId.YAHOO,
        environment=BrokerEnvironment.SANDBOX,
        provider_enabled=True,
        connect_timeout_sec=1,
        request_timeout_sec=1,
        transport_reconnect_max_attempts=0,
        stream_buffer_size=8,
        circuit_failure_threshold=2,
        circuit_recovery_timeout_sec=1,
        circuit_half_open_max_calls=1,
        probe_symbol=_SYMBOL,
    )


def test_data_boundary_via_root() -> None:
    """Verify data boundary via root API and session gating."""
    created = create_broker_adapter(BrokerId.YAHOO, _config())
    assert created.is_success
    adapter = created.data
    assert adapter is not None

    async def exercise() -> None:
        # Disconnected call returns BROKER_NOT_CONNECTED
        result = await adapter.get_historical_bars(_SYMBOL, "1d", limit=1)
        assert not result.is_success
        assert result.error is not None
        assert result.error.code == BrokerErrorCode.BROKER_NOT_CONNECTED

    asyncio.run(exercise())
