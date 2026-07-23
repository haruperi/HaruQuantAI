"""WF-BRK-004: submit one broker mutation (Trading-only capability)."""

import asyncio
from decimal import Decimal

import pytest
from app.services.brokers import (
    BrokerCapabilityId,
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerErrorCode,
    BrokerId,
    BrokerOrderRequest,
    create_broker_adapter,
)
from pydantic import SecretStr


def _config() -> BrokerConnectionConfig:
    from tests.brokers.provider_settings import ProviderTestSettings

    settings = ProviderTestSettings()
    if (
        settings.mt5_login is not None
        and settings.mt5_password is not None
        and settings.mt5_server is not None
    ):
        account_ref = settings.mt5_login.get_secret_value()
        creds = {
            "login": settings.mt5_login,
            "password": settings.mt5_password,
            "server": settings.mt5_server,
        }
        if settings.mt5_terminal_path is not None:
            creds["terminal_path"] = settings.mt5_terminal_path
    else:
        account_ref = "100001"
        creds = {
            "login": SecretStr("100001"),
            "password": SecretStr("offline-placeholder"),
            "server": SecretStr("Offline-Demo"),
        }
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
        account_reference=account_ref,
        credentials=creds,
    )


def _order_request() -> BrokerOrderRequest:
    """Build one complete, structurally valid V1 order request."""
    return BrokerOrderRequest(
        symbol="EURUSD",
        side="BUY",
        order_type="MARKET",
        quantity=Decimal("0.01"),
        quantity_unit="lots",
        environment=BrokerEnvironment.DEMO,
        client_request_id="req-2f1d5a6c-8b3e-4c17-9f52-70a1c8d94e33",
    )


def test_structurally_invalid_request_is_rejected_before_transmission() -> None:
    """An incomplete request never reaches the provider (WF-BRK-004 step 1)."""
    with pytest.raises(ValueError, match="quantity must be positive"):
        BrokerOrderRequest(
            symbol="EURUSD",
            side="BUY",
            order_type="MARKET",
            quantity=Decimal(0),
            quantity_unit="lots",
            environment=BrokerEnvironment.DEMO,
        )


def test_registry_created_real_adapter_blocks_every_unreleased_write() -> None:
    """The genuine registry/MT5 boundary blocks writes before provider access."""
    created = create_broker_adapter(BrokerId.MT5, _config())
    assert created.data is not None
    adapter = created.data
    request = _order_request()

    async def exercise() -> None:
        result = await adapter.place_order(request)
        assert result.error is not None
        assert result.error.code is BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED
        assert result.error.capability is BrokerCapabilityId.PLACE_ORDER

    asyncio.run(exercise())


def _broker_config(broker_id: BrokerId) -> BrokerConnectionConfig:
    creds: dict[str, SecretStr] = {}
    if broker_id == BrokerId.MT5:
        creds = {
            "login": SecretStr("100001"),
            "password": SecretStr("pwd"),
            "server": SecretStr("srv"),
        }
    elif broker_id == BrokerId.CTRADER:
        creds = {
            "client_id": SecretStr("cid"),
            "client_secret": SecretStr("csec"),
            "access_token": SecretStr("token"),
            "account_id": SecretStr("100001"),
        }
    elif broker_id == BrokerId.BINANCE_SPOT:
        creds = {
            "api_key": SecretStr("key"),
            "api_secret": SecretStr("sec"),
        }
    return BrokerConnectionConfig(
        broker_id=broker_id,
        environment=BrokerEnvironment.DEMO
        if broker_id != BrokerId.BINANCE_SPOT
        else BrokerEnvironment.TESTNET,
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


def test_all_mutation_operations_fail_closed_at_public_root_boundary() -> None:
    """Every mutation method returns BROKER_CAPABILITY_UNSUPPORTED for root adapters."""
    for broker_id in (BrokerId.MT5, BrokerId.CTRADER, BrokerId.BINANCE_SPOT):
        config = _broker_config(broker_id)
        created = create_broker_adapter(broker_id, config)
        assert created.data is not None
        adapter = created.data

        async def exercise(target_adapter: object = adapter) -> None:
            res_place = await target_adapter.place_order(_order_request())  # type: ignore[attr-defined]
            assert res_place.error is not None
            assert res_place.error.code is BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED

            res_cancel = await target_adapter.cancel_order("ticket-1")  # type: ignore[attr-defined]
            assert res_cancel.error is not None
            assert (
                res_cancel.error.code is BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED
            )

        asyncio.run(exercise())
