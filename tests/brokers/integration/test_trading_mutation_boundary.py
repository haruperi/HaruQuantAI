"""WF-BRK-004: submit one broker mutation (Trading-only capability)."""

import asyncio
from decimal import Decimal

import pytest
from app.services.brokers import (
    build_broker_connection_config,
    build_broker_order_request,
    cancel_broker_order,
    create_broker_adapter,
    get_broker_id,
    get_broker_value_field,
    place_broker_order,
)
from pydantic import SecretStr


def _config() -> object:
    return build_broker_connection_config(
        get_broker_id("mt5"),
        "demo",
        provider_enabled=True,
        connect_timeout_sec=1,
        request_timeout_sec=1,
        transport_reconnect_max_attempts=0,
        stream_buffer_size=8,
        circuit_failure_threshold=2,
        circuit_recovery_timeout_sec=1,
        circuit_half_open_max_calls=1,
        account_reference="100001",
        credentials={
            "login": SecretStr("100001"),
            "password": SecretStr("offline-placeholder"),
            "server": SecretStr("Offline-Demo"),
        },
    )


def _order_request() -> object:
    """Build one complete, structurally valid V1 order request."""
    return build_broker_order_request(
        symbol="EURUSD",
        side="BUY",
        order_type="MARKET",
        quantity=Decimal("0.01"),
        quantity_unit="lots",
        environment="demo",
        client_order_id="req-2f1d5a6c-8b3e-4c17-9f52-70a1c8d94e33",
    )


def test_structurally_invalid_request_is_rejected_before_transmission() -> None:
    """An incomplete request never reaches the provider (WF-BRK-004 step 1)."""
    with pytest.raises(ValueError, match="quantity must be positive"):
        build_broker_order_request(
            symbol="EURUSD",
            side="BUY",
            order_type="MARKET",
            quantity=Decimal(0),
            quantity_unit="lots",
            environment="demo",
        )


def test_registry_created_real_adapter_requires_connection_for_released_write() -> None:
    """The genuine registry/MT5 boundary requires a ready connection."""
    created = create_broker_adapter(get_broker_id("mt5"), _config())
    assert get_broker_value_field(created, "status") == "success"
    adapter = get_broker_value_field(created, "data")
    assert adapter is not None
    request = _order_request()

    async def exercise() -> None:
        result = await place_broker_order(adapter, request)
        error = get_broker_value_field(result, "error")
        assert error is not None
        assert get_broker_value_field(error, "code") == "BROKER_NOT_CONNECTED"

    asyncio.run(exercise())


def test_all_mutation_operations_fail_closed_at_public_root_boundary() -> None:
    """Every disconnected mutation fails closed under its capability policy."""
    for broker_id_str in ("mt5", "ctrader", "binance_spot"):
        broker_id = get_broker_id(broker_id_str)
        creds: dict[str, SecretStr] = {}
        if broker_id_str == "mt5":
            creds = {
                "login": SecretStr("100001"),
                "password": SecretStr("pwd"),
                "server": SecretStr("srv"),
            }
        elif broker_id_str == "ctrader":
            creds = {
                "client_id": SecretStr("cid"),
                "client_secret": SecretStr("csec"),
                "access_token": SecretStr("token"),
                "account_id": SecretStr("100001"),
            }
        elif broker_id_str == "binance_spot":
            creds = {
                "api_key": SecretStr("key"),
                "api_secret": SecretStr("sec"),
            }
        cfg = build_broker_connection_config(
            broker_id,
            "demo" if broker_id_str != "binance_spot" else "testnet",
            provider_enabled=True,
            connect_timeout_sec=1,
            request_timeout_sec=1,
            transport_reconnect_max_attempts=0,
            stream_buffer_size=2,
            circuit_failure_threshold=2,
            circuit_recovery_timeout_sec=1,
            circuit_half_open_max_calls=1,
            account_reference="100001",
            credentials=creds,
        )
        created = create_broker_adapter(broker_id, cfg)
        assert get_broker_value_field(created, "status") == "success"
        adapter = get_broker_value_field(created, "data")
        assert adapter is not None

        async def exercise(target_adapter: object = adapter) -> None:
            res_place = await place_broker_order(target_adapter, _order_request())
            err_place = get_broker_value_field(res_place, "error")
            assert err_place is not None
            assert get_broker_value_field(err_place, "code") in (
                "BROKER_NOT_CONNECTED",
                "BROKER_CAPABILITY_UNSUPPORTED",
            )

            res_cancel = await cancel_broker_order(target_adapter, "ticket-1")
            err_cancel = get_broker_value_field(res_cancel, "error")
            assert err_cancel is not None
            assert get_broker_value_field(err_cancel, "code") in (
                "BROKER_NOT_CONNECTED",
                "BROKER_CAPABILITY_UNSUPPORTED",
            )

        asyncio.run(exercise())
