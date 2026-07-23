"""WF-BRK-005: read account and execution state."""

import asyncio

from app.services.brokers import (
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerErrorCode,
    BrokerId,
    BrokerPositionFilter,
    create_broker_adapter,
)
from pydantic import SecretStr

_LOGIN = "12345"
_SERVER = "Demo-Server"


def _config() -> BrokerConnectionConfig:
    return BrokerConnectionConfig(
        broker_id=BrokerId.MT5,
        environment=BrokerEnvironment.DEMO,
        provider_enabled=True,
        connect_timeout_sec=1,
        request_timeout_sec=1,
        transport_reconnect_max_attempts=0,
        stream_buffer_size=8,
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


def test_account_and_execution_state_boundary_from_root() -> None:
    """Root-created adapter handles session gating and account reads safely."""
    created = create_broker_adapter(BrokerId.MT5, _config())
    assert created.is_success
    adapter = created.data
    assert adapter is not None

    async def exercise() -> None:
        # Disconnected operations return BROKER_NOT_CONNECTED
        res_acc = await adapter.get_account_info()
        assert not res_acc.is_success
        assert res_acc.error is not None
        assert res_acc.error.code == BrokerErrorCode.BROKER_NOT_CONNECTED

        res_pos = await adapter.get_positions(BrokerPositionFilter(), limit=10)
        assert not res_pos.is_success
        assert res_pos.error is not None
        assert res_pos.error.code == BrokerErrorCode.BROKER_NOT_CONNECTED

    asyncio.run(exercise())
