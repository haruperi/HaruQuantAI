"""Credential-gated MT5 demo mutation, cleanup, and reconciliation evidence."""

from __future__ import annotations

import asyncio
from decimal import ROUND_DOWN, Decimal

import pytest
from app.services.brokers import (
    BrokerAdapter,
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerId,
    BrokerOrderRequest,
    BrokerPositionCloseRequest,
    create_broker_adapter,
)
from app.utils import generate_id, load_settings, logger

from tests.brokers.provider_settings import ProviderTestSettings

_SYMBOL = "EURUSD"
_STATE_LIMIT = 1_000


def _connection_config(settings: ProviderTestSettings) -> BrokerConnectionConfig:
    """Build the exact credential-backed MT5 demo connection.

    Args:
        settings: Typed provider test settings.

    Returns:
        Immutable MT5 demo connection configuration.

    Raises:
        AssertionError: If required demo credentials are absent.
    """
    assert settings.mt5_login is not None
    assert settings.mt5_password is not None
    assert settings.mt5_server is not None
    credentials = {
        "login": settings.mt5_login,
        "password": settings.mt5_password,
        "server": settings.mt5_server,
    }
    if settings.mt5_terminal_path is not None:
        credentials["terminal_path"] = settings.mt5_terminal_path
    return BrokerConnectionConfig(
        broker_id=BrokerId.MT5,
        environment=BrokerEnvironment.DEMO,
        provider_enabled=True,
        connect_timeout_sec=15,
        request_timeout_sec=15,
        transport_reconnect_max_attempts=0,
        stream_buffer_size=8,
        circuit_failure_threshold=3,
        circuit_recovery_timeout_sec=5,
        circuit_half_open_max_calls=1,
        account_reference=settings.mt5_login.get_secret_value(),
        credentials=credentials,
    )


async def _authority_state(adapter: BrokerAdapter) -> tuple[set[str], set[str]]:
    """Read bounded active order and position identities.

    Args:
        adapter: Connected canonical Broker adapter.

    Returns:
        Active order and position identity sets.
    """
    orders_result = await adapter.get_orders(limit=_STATE_LIMIT)
    positions_result = await adapter.get_positions(limit=_STATE_LIMIT)
    assert orders_result.status == "success", orders_result.error
    assert positions_result.status == "success", positions_result.error
    assert orders_result.data is not None
    assert positions_result.data is not None
    assert not orders_result.data.truncated
    assert not positions_result.data.truncated
    return (
        {item.order_id for item in orders_result.data.items},
        {item.position_id for item in positions_result.data.items},
    )


async def _cleanup_created_state(
    adapter: BrokerAdapter,
    *,
    original_orders: set[str],
    original_positions: set[str],
) -> None:
    """Remove only authority state created by this validation run.

    Args:
        adapter: Connected canonical Broker adapter.
        original_orders: Orders that existed before validation.
        original_positions: Positions that existed before validation.

    Raises:
        AssertionError: If cleanup or final reconciliation is incomplete.
    """
    current_orders, current_positions = await _authority_state(adapter)
    for order_id in sorted(current_orders - original_orders):
        cancelled = await adapter.cancel_order(order_id)
        assert cancelled.status == "success", cancelled.error
    for position_id in sorted(current_positions - original_positions):
        position = await adapter.get_position(position_id)
        assert position.status == "success", position.error
        assert position.data is not None
        closed = await adapter.close_position(
            BrokerPositionCloseRequest(
                position_id=position_id,
                quantity=position.data.quantity,
                quantity_unit=position.data.quantity_unit,
                client_request_id=generate_id("req"),
            )
        )
        assert closed.status == "success", closed.error
    reconciled_orders, reconciled_positions = await _authority_state(adapter)
    assert reconciled_orders == original_orders
    assert reconciled_positions == original_positions


def _require_demo_settings() -> ProviderTestSettings:
    """Load complete dev/demo settings or skip without provider access.

    Returns:
        Complete MT5 demo provider settings.
    """
    settings = ProviderTestSettings()
    if (
        not settings.mt5_enabled
        or settings.mt5_login is None
        or settings.mt5_password is None
        or settings.mt5_server is None
    ):
        pytest.skip("MT5 demo credentials are not configured")
    assert load_settings().environment == "dev"
    assert settings.mt5_environment == "demo"
    return settings


async def _verify_demo_session(adapter: BrokerAdapter) -> None:
    """Require provider-reported demo classification and write permission.

    Args:
        adapter: Connected canonical Broker adapter.
    """
    import MetaTrader5

    account = MetaTrader5.account_info()
    assert account is not None
    assert account.trade_mode == MetaTrader5.ACCOUNT_TRADE_MODE_DEMO
    permissions = await adapter.get_permissions()
    assert permissions.status == "success", permissions.error
    assert permissions.data is not None
    assert permissions.data.trade_write is True


async def _minimum_pending_order(
    adapter: BrokerAdapter,
    settings: ProviderTestSettings,
) -> BrokerOrderRequest:
    """Build a far-from-market minimum-size order from provider evidence.

    Args:
        adapter: Connected canonical Broker adapter.
        settings: Verified MT5 demo settings.

    Returns:
        Minimum-size pending order unique to this validation run.
    """
    positions = await adapter.get_positions(limit=_STATE_LIMIT)
    assert positions.status == "success", positions.error
    assert positions.data is not None
    assert all(item.symbol != _SYMBOL for item in positions.data.items)
    symbol = await adapter.get_symbol_info(_SYMBOL)
    quote = await adapter.get_quote(_SYMBOL)
    assert symbol.status == "success", symbol.error
    assert quote.status == "success", quote.error
    assert symbol.data is not None
    assert quote.data is not None
    assert symbol.data.min_quantity is not None
    assert symbol.data.price_precision is not None
    assert quote.data.bid is not None
    price_step = symbol.data.price_step or Decimal(1).scaleb(
        -symbol.data.price_precision
    )
    limit_price = (quote.data.bid * Decimal("0.80")).quantize(
        price_step,
        rounding=ROUND_DOWN,
    )
    run_id = generate_id("cor")
    assert settings.mt5_login is not None
    return BrokerOrderRequest(
        symbol=_SYMBOL,
        side="BUY",
        order_type="LIMIT",
        quantity=symbol.data.min_quantity,
        quantity_unit=symbol.data.quantity_unit,
        environment=BrokerEnvironment.DEMO,
        account_reference=settings.mt5_login.get_secret_value(),
        limit_price=limit_price,
        time_in_force="GTC",
        client_request_id=generate_id("req"),
        client_order_id=run_id,
        magic=int(run_id[-8:].replace("-", ""), 16),
        comment=f"hq-{run_id[-8:]}",
    )


async def _exercise_demo_mutation(
    adapter: BrokerAdapter,
    settings: ProviderTestSettings,
) -> None:
    """Execute one provider-classified demo mutation and exact cleanup.

    Args:
        adapter: Canonical Broker adapter.
        settings: Verified MT5 demo settings.
    """
    connected = await adapter.connect()
    assert connected.status == "success", connected.error
    original_orders: set[str] | None = None
    original_positions: set[str] | None = None
    try:
        await _verify_demo_session(adapter)
        original_orders, original_positions = await _authority_state(adapter)
        request = await _minimum_pending_order(adapter, settings)
        checked = await adapter.check_order(request)
        assert checked.status == "success", checked.error
        assert checked.data is not None
        assert checked.data.accepted_for_submission
        logger.info(
            "Submitting one minimum-size MT5 demo validation order | "
            "environment=dev provider_environment=demo "
            "provider_account_classification=demo operation=place_order"
        )
        placed = await adapter.place_order(request)
        assert placed.status == "success", placed.error
        assert placed.data is not None
        assert placed.data.outcome == "ACCEPTED"
        assert placed.data.order_id is not None
    finally:
        if original_orders is not None and original_positions is not None:
            await _cleanup_created_state(
                adapter,
                original_orders=original_orders,
                original_positions=original_positions,
            )
        await adapter.disconnect()


def test_mt5_demo_minimum_order_is_cancelled_and_reconciled() -> None:
    """Place one minimum-size demo order, clean it up, and reconcile exactly."""
    settings = _require_demo_settings()
    created = create_broker_adapter(BrokerId.MT5, _connection_config(settings))
    assert created.status == "success", created.error
    adapter = created.data
    assert adapter is not None

    asyncio.run(_exercise_demo_mutation(adapter, settings))
