"""WF-BRK-006: stream provider and connection events."""

import asyncio

from app.services.brokers import (
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerErrorCode,
    BrokerId,
    create_broker_adapter,
)
from pydantic import SecretStr

_BUFFER_SIZE = 2
_SYMBOL = "BTCUSDT"


def _config() -> BrokerConnectionConfig:
    return BrokerConnectionConfig(
        broker_id=BrokerId.BINANCE_SPOT,
        environment=BrokerEnvironment.TESTNET,
        provider_enabled=True,
        connect_timeout_sec=1,
        request_timeout_sec=1,
        transport_reconnect_max_attempts=0,
        stream_buffer_size=_BUFFER_SIZE,
        circuit_failure_threshold=2,
        circuit_recovery_timeout_sec=1,
        circuit_half_open_max_calls=1,
        credentials={
            "api_key": SecretStr("offline-key"),
            "api_secret": SecretStr("offline-secret"),
        },
    )


def test_streaming_boundary_via_root() -> None:
    """Verify streaming boundary behavior via domain root API."""
    created = create_broker_adapter(BrokerId.BINANCE_SPOT, _config())
    assert created.is_success
    adapter = created.data
    assert adapter is not None

    async def exercise() -> None:
        # Unreleased subscribe_quotes returns BROKER_CAPABILITY_UNSUPPORTED
        result = await adapter.subscribe_quotes((_SYMBOL,))
        assert not result.is_success
        assert result.error is not None
        assert result.error.code == BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED

    asyncio.run(exercise())
