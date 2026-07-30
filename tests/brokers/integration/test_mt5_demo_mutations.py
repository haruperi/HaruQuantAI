"""Credential-gated MT5 demo mutation, cleanup, and reconciliation evidence."""

from __future__ import annotations

import asyncio
from decimal import ROUND_DOWN, Decimal

import pytest
from app.services.brokers import (
    build_broker_connection_config,
    build_broker_order_filter,
    build_broker_order_request,
    build_broker_position_close_request,
    build_broker_position_filter,
    cancel_broker_order,
    check_broker_order,
    close_broker_position,
    connect_broker,
    create_broker_adapter,
    disconnect_broker,
    get_broker_id,
    get_broker_orders,
    get_broker_permissions,
    get_broker_position,
    get_broker_positions,
    get_broker_quote,
    get_broker_symbol_info,
    get_broker_value_field,
    place_broker_order,
)
from app.utils import (
    generate_id,
    get_logger,
    load_broker_provider_settings,
    load_settings,
)

logger = get_logger("tests.brokers.integration.test_mt5_demo_mutations")

_SYMBOL = "EURUSD"
_STATE_LIMIT = 1_000


def _connection_config(settings: object) -> object:
    """Build the exact credential-backed MT5 demo connection."""
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
    return build_broker_connection_config(
        "mt5",
        "demo",
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


async def _authority_state(adapter: object) -> tuple[set[str], set[str]]:
    """Read bounded active order and position identities."""
    orders_result = await get_broker_orders(adapter, build_broker_order_filter())
    positions_result = await get_broker_positions(
        adapter, build_broker_position_filter()
    )
    assert get_broker_value_field(orders_result, "status") == "success"
    assert get_broker_value_field(positions_result, "status") == "success"
    orders_data = get_broker_value_field(orders_result, "data")
    positions_data = get_broker_value_field(positions_result, "data")
    assert orders_data is not None
    assert positions_data is not None
    return (
        {
            get_broker_value_field(item, "order_id")
            for item in get_broker_value_field(orders_data, "items")
        },
        {
            get_broker_value_field(item, "position_id")
            for item in get_broker_value_field(positions_data, "items")
        },
    )


async def _cleanup_created_state(
    adapter: object,
    *,
    original_orders: set[str],
    original_positions: set[str],
) -> None:
    """Remove only authority state created by this validation run."""
    current_orders, current_positions = await _authority_state(adapter)
    for order_id in sorted(current_orders - original_orders):
        cancelled = await cancel_broker_order(adapter, order_id)
        if get_broker_value_field(cancelled, "status") != "success":
            try:
                import MetaTrader5

                MetaTrader5.order_send(
                    {"action": MetaTrader5.TRADE_ACTION_REMOVE, "order": int(order_id)}
                )
            except RuntimeError, OSError, AttributeError:
                logger.warning("Could not cancel order %s via native SDK", order_id)
    for position_id in sorted(current_positions - original_positions):
        position = await get_broker_position(adapter, position_id)
        assert get_broker_value_field(position, "status") == "success"
        pos_data = get_broker_value_field(position, "data")
        assert pos_data is not None
        closed = await close_broker_position(
            adapter,
            build_broker_position_close_request(
                position_id=position_id,
                quantity=get_broker_value_field(pos_data, "quantity"),
                quantity_unit=get_broker_value_field(pos_data, "quantity_unit"),
                client_request_id=generate_id("req"),
            ),
        )
        assert get_broker_value_field(closed, "status") == "success"
    reconciled_orders, reconciled_positions = await _authority_state(adapter)
    assert reconciled_orders == original_orders
    assert reconciled_positions == original_positions


def _require_demo_settings() -> object:
    """Load complete dev/demo settings or skip without provider access."""
    settings = load_broker_provider_settings()
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


async def _verify_demo_session(adapter: object) -> None:
    """Require provider-reported demo classification and write permission."""
    import MetaTrader5

    account = MetaTrader5.account_info()
    assert account is not None
    assert account.trade_mode == MetaTrader5.ACCOUNT_TRADE_MODE_DEMO
    permissions = await get_broker_permissions(adapter)
    assert get_broker_value_field(permissions, "status") == "success"
    perm_data = get_broker_value_field(permissions, "data")
    assert perm_data is not None
    assert get_broker_value_field(perm_data, "trade_write") is True


async def _minimum_pending_order(
    adapter: object,
    settings: object,
) -> object:
    """Build a far-from-market minimum-size order from provider evidence."""
    positions = await get_broker_positions(adapter)
    assert get_broker_value_field(positions, "status") == "success"
    pos_data = get_broker_value_field(positions, "data")
    assert pos_data is not None
    pos_items = get_broker_value_field(pos_data, "items")
    assert pos_items is not None
    symbol = await get_broker_symbol_info(adapter, _SYMBOL)
    quote = await get_broker_quote(adapter, _SYMBOL)
    assert get_broker_value_field(symbol, "status") == "success"
    assert get_broker_value_field(quote, "status") == "success"
    sym_data = get_broker_value_field(symbol, "data")
    q_data = get_broker_value_field(quote, "data")
    assert sym_data is not None
    assert q_data is not None
    min_qty = get_broker_value_field(sym_data, "min_quantity")
    prec = get_broker_value_field(sym_data, "price_precision")
    bid = get_broker_value_field(q_data, "bid")
    step = get_broker_value_field(sym_data, "price_step") or Decimal(1).scaleb(-prec)
    limit_price = (bid * Decimal("0.80")).quantize(step, rounding=ROUND_DOWN)
    run_id = generate_id("cor")
    assert settings.mt5_login is not None
    return build_broker_order_request(
        symbol=_SYMBOL,
        side="BUY",
        order_type="LIMIT",
        quantity=min_qty,
        quantity_unit=get_broker_value_field(sym_data, "quantity_unit"),
        environment="demo",
        account_reference=settings.mt5_login.get_secret_value(),
        limit_price=limit_price,
        time_in_force="GTC",
        client_order_id=run_id,
    )


async def _exercise_demo_mutation(
    adapter: object,
    settings: object,
) -> None:
    """Execute one provider-classified demo mutation and exact cleanup."""
    connected = await connect_broker(adapter)
    assert get_broker_value_field(connected, "status") == "success"
    original_orders: set[str] | None = None
    original_positions: set[str] | None = None
    try:
        await _verify_demo_session(adapter)
        original_orders, original_positions = await _authority_state(adapter)
        request = await _minimum_pending_order(adapter, settings)
        checked = await check_broker_order(adapter, request)
        assert get_broker_value_field(checked, "status") == "success"
        chk_data = get_broker_value_field(checked, "data")
        assert chk_data is not None
        assert get_broker_value_field(chk_data, "accepted_for_submission")
        logger.info(
            "Submitting one minimum-size MT5 demo validation order | "
            "environment=dev provider_environment=demo "
            "provider_account_classification=demo operation=place_order"
        )
        placed = await place_broker_order(adapter, request)
        assert get_broker_value_field(placed, "status") == "success"
        pl_data = get_broker_value_field(placed, "data")
        assert pl_data is not None
        assert get_broker_value_field(pl_data, "outcome") == "ACCEPTED"
        assert get_broker_value_field(pl_data, "order_id") is not None
    finally:
        if original_orders is not None and original_positions is not None:
            await _cleanup_created_state(
                adapter,
                original_orders=original_orders,
                original_positions=original_positions,
            )
        await disconnect_broker(adapter)


def test_mt5_demo_minimum_order_is_cancelled_and_reconciled() -> None:
    """Place one minimum-size demo order, clean it up, and reconcile exactly."""
    settings = _require_demo_settings()
    created = create_broker_adapter(get_broker_id("mt5"), _connection_config(settings))
    assert get_broker_value_field(created, "status") == "success"
    adapter = get_broker_value_field(created, "data")
    assert adapter is not None

    asyncio.run(_exercise_demo_mutation(adapter, settings))
