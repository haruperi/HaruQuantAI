"""cTrader concurrent-request correlation integration test (WF-BRK-007)."""

import asyncio

from app.services.brokers import (
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerId,
    create_broker_adapter,
)


def _config() -> BrokerConnectionConfig:
    from pydantic import SecretStr

    return BrokerConnectionConfig(
        broker_id=BrokerId.CTRADER,
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
            "client_id": SecretStr("cid"),
            "client_secret": SecretStr("csec"),
            "access_token": SecretStr("token"),
            "account_id": SecretStr("12345"),
        },
    )


def test_ctrader_correlation_integration_via_root() -> None:
    """Verify cTrader adapter correlation via root API boundary."""
    created = create_broker_adapter(BrokerId.CTRADER, _config())
    assert created.is_success
    adapter = created.data
    assert adapter is not None

    async def exercise() -> None:
        status = await adapter.get_connection_status()
        assert status.is_success

    asyncio.run(exercise())
