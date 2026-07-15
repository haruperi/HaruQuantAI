"""Every registered provider adapter satisfies the canonical BrokerAdapter contract."""

from app.services.brokers import (
    BrokerAdapter,
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerId,
    create_broker_adapter,
    get_registered_brokers,
)
from pydantic import SecretStr


def _config(broker_id: BrokerId) -> BrokerConnectionConfig:
    common: dict[str, object] = {
        "broker_id": broker_id,
        "provider_enabled": True,
        "connect_timeout_sec": 1,
        "request_timeout_sec": 1,
        "transport_reconnect_max_attempts": 0,
        "stream_buffer_size": 2,
        "circuit_failure_threshold": 2,
        "circuit_recovery_timeout_sec": 1,
        "circuit_half_open_max_calls": 1,
    }
    if broker_id == BrokerId.MT5:
        return BrokerConnectionConfig(
            **common,
            environment=BrokerEnvironment.DEMO,
            account_reference="1",
            credentials={
                "login": SecretStr("1"),
                "password": SecretStr("p"),
                "server": SecretStr("s"),
            },
        )
    if broker_id == BrokerId.CTRADER:
        return BrokerConnectionConfig(
            **common,
            environment=BrokerEnvironment.DEMO,
            account_reference="1",
            credentials={
                "client_id": SecretStr("c"),
                "client_secret": SecretStr("s"),
                "access_token": SecretStr("a"),
                "account_id": SecretStr("1"),
            },
        )
    if broker_id in {
        BrokerId.BINANCE_SPOT,
        BrokerId.BINANCE_USD_M_FUTURES,
        BrokerId.BINANCE_COIN_M_FUTURES,
    }:
        return BrokerConnectionConfig(**common, environment=BrokerEnvironment.TESTNET)
    return BrokerConnectionConfig(**common, environment=BrokerEnvironment.SANDBOX)


def test_every_registered_broker_resolves_a_canonical_adapter() -> None:
    """Every registered broker profile constructs a protocol-conformant adapter."""
    for broker_id in get_registered_brokers():
        result = create_broker_adapter(broker_id, _config(broker_id))
        assert result.is_success, (broker_id, result.error)
        assert isinstance(result.data, BrokerAdapter)
