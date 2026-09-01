"""Integration tests for the provider specification snapshot contract."""

import asyncio
from datetime import UTC, datetime

from app.services.brokers import (
    build_broker_connection_config,
    build_provider_specification_snapshot,
    dump_provider_specification_snapshot,
    verify_provider_specification_snapshot,
)
from pydantic import SecretStr

from tests.brokers.conformance import create_configured_fake_broker_adapter

_SYMBOL_INFO = {
    "name": "EURUSD",
    "digits": 5,
    "point": 0.00001,
    "filling_mode": 3,
    "order_mode": 15,
    "expiration_mode": 5,
    "order_gtc_mode": 0,
    "trade_exemode": 2,
    "trade_mode": 4,
    "trade_calc_mode": 0,
    "swap_mode": 1,
    "swap_rollover3days": 3,
    "trade_stops_level": 10,
    "trade_freeze_level": 5,
    "volume_min": 0.01,
    "volume_max": 500.0,
    "volume_step": 0.01,
    "volume_limit": 300.0,
    "trade_tick_size": 0.00001,
    "trade_tick_value": 1.0,
    "trade_tick_value_profit": 1.0,
    "trade_tick_value_loss": 1.0,
    "trade_contract_size": 100000.0,
    "currency_base": "EUR",
    "currency_profit": "USD",
    "currency_margin": "USD",
    "margin_initial": 0.0,
    "margin_maintenance": 0.0,
    "margin_hedged": 100000.0,
    "margin_hedged_use_leg": False,
    "swap_long": -0.2,
    "swap_short": -1.2,
}

_ACCOUNT_INFO = {
    "login": 12345,
    "server": "Demo-Server",
    "currency": "USD",
    "balance": 1000,
    "equity": 1100,
    "margin": 100,
    "margin_free": 1000,
    "trade_allowed": True,
    "margin_mode": 2,
}


def _config() -> object:
    return build_broker_connection_config(
        broker_id="mt5",
        provider_enabled=True,
        connect_timeout_sec=1,
        request_timeout_sec=1,
        transport_reconnect_max_attempts=0,
        stream_buffer_size=2,
        circuit_failure_threshold=2,
        circuit_recovery_timeout_sec=1,
        circuit_half_open_max_calls=1,
        environment="demo",
        account_reference="12345",
        credentials={
            "login": SecretStr("12345"),
            "password": SecretStr("hunter2"),
            "server": SecretStr("Demo-Server"),
        },
    )


def _snapshot() -> object:
    return build_provider_specification_snapshot(
        symbol_info=_SYMBOL_INFO,
        broker="mt5",
        server="Demo-Server",
        account_id="12345",
        environment="demo",
        terminal_build="4570",
        source_revision="mt5:4570",
        observed_at=datetime(2026, 8, 20, tzinfo=UTC),
        account_info=_ACCOUNT_INFO,
    )


def test_conformance_fake_serves_snapshot_fixture() -> None:
    """The deterministic fake carries the new capability with a snapshot."""
    adapter = create_configured_fake_broker_adapter(
        _config(),
        fixtures={"get_provider_specification": _snapshot()},
    )

    async def exercise() -> None:
        await adapter.connect()
        response = await adapter.get_provider_specification("EURUSD")
        assert response.status == "success"
        assert response.data is not None
        assert verify_provider_specification_snapshot(response.data) is True
        dumped = dump_provider_specification_snapshot(response.data)
        assert dumped["directional_volume_limit"] == "300.0"

    asyncio.run(exercise())


def test_root_boundary_round_trip_is_checksum_stable() -> None:
    """Build, dump, and verify through the package root only."""
    snapshot = _snapshot()
    assert verify_provider_specification_snapshot(snapshot) is True
    dumped = dump_provider_specification_snapshot(snapshot)
    assert dumped["environment"] == "demo"
