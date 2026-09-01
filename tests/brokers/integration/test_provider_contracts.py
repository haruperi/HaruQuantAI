"""Every registered provider adapter satisfies the canonical BrokerAdapter contract."""

from app.services.brokers import (
    build_broker_connection_config,
    get_broker_value_field,
    get_registered_brokers,
)
from pydantic import SecretStr

from tests.brokers.conformance import create_configured_fake_broker_adapter


def _config(broker_id: str | object) -> object:
    raw_id = (
        get_broker_value_field(broker_id, "value")
        if not isinstance(broker_id, str)
        else broker_id
    )
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
    if raw_id == "mt5":
        return build_broker_connection_config(
            **common,
            environment="demo",
            account_reference="1",
            credentials={
                "login": SecretStr("1"),
                "password": SecretStr("p"),
                "server": SecretStr("s"),
            },
        )
    if raw_id == "ctrader":
        return build_broker_connection_config(
            **common,
            environment="demo",
            account_reference="1",
            credentials={
                "client_id": SecretStr("c"),
                "client_secret": SecretStr("s"),
                "access_token": SecretStr("a"),
                "account_id": SecretStr("1"),
            },
        )
    if raw_id in {
        "binance_spot",
        "binance_usd_m_futures",
        "binance_coin_m_futures",
    }:
        return build_broker_connection_config(**common, environment="testnet")
    return build_broker_connection_config(**common, environment="sandbox")


def test_every_registered_broker_resolves_a_canonical_adapter() -> None:
    """Every registered broker profile constructs a protocol-conformant adapter."""
    registered = get_registered_brokers()
    assert get_broker_value_field(registered, "status") == "success"
    data = get_broker_value_field(registered, "data")
    assert data is not None
    for broker_id in data:
        cfg = _config(broker_id)
        adapter = create_configured_fake_broker_adapter(cfg)
        assert adapter is not None
