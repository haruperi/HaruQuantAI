"""Unit tests for order action primitives."""

from __future__ import annotations

from decimal import Decimal

import pytest
from app.services.trading.actions.orders import (
    buy,
    buy_limit,
    buy_stop,
    order_delete,
    order_modify,
    sell,
    sell_limit,
    sell_stop,
    submit_oco_group,
)
from app.services.trading.actions.validation import OrderIntent, OrderSide, OrderType
from app.services.trading.contracts import SideEffectMode, TradingStatus
from app.services.trading.security.error_mapping import TradingMappedError

from tests.trading.unit.actions._fixtures import (
    ROUTE_KWARGS,
    build_context,
    build_deps,
)


def test_buy_and_sell_package_market_orders() -> None:
    """buy/sell package validated market order intents as packaged_only."""
    context = build_context()
    deps = build_deps()
    buy_response = buy(
        symbol="EURUSD",
        volume=Decimal("0.10"),
        sl=Decimal("1.09000"),
        tp=Decimal("1.11000"),
        deviation_points=10,
        request_id="req-buy",
        correlation_id="corr-buy",
        context=context,
        deps=deps,
        **ROUTE_KWARGS,
    )
    sell_response = sell(
        symbol="EURUSD",
        volume=Decimal("0.10"),
        deviation_points=10,
        request_id="req-sell",
        correlation_id="corr-sell",
        context=context,
        deps=deps,
        **ROUTE_KWARGS,
    )
    assert buy_response.status is TradingStatus.ACCEPTED
    assert buy_response.side_effect_mode is SideEffectMode.PACKAGED_ONLY
    assert sell_response.status is TradingStatus.ACCEPTED


def test_pending_orders_package_limit_and_stop_intents() -> None:
    """Pending order helpers package limit/stop intents correctly."""
    context = build_context()
    deps = build_deps()
    limit_response = buy_limit(
        symbol="EURUSD",
        volume=Decimal("0.10"),
        price=Decimal("1.09500"),
        request_id="req-buy-limit",
        correlation_id="corr-buy-limit",
        context=context,
        deps=deps,
        **ROUTE_KWARGS,
    )
    sell_limit_response = sell_limit(
        symbol="EURUSD",
        volume=Decimal("0.10"),
        price=Decimal("1.10500"),
        request_id="req-sell-limit",
        correlation_id="corr-sell-limit",
        context=context,
        deps=deps,
        **ROUTE_KWARGS,
    )
    stop_response = buy_stop(
        symbol="EURUSD",
        volume=Decimal("0.10"),
        price=Decimal("1.10500"),
        request_id="req-buy-stop",
        correlation_id="corr-buy-stop",
        context=context,
        deps=deps,
        **ROUTE_KWARGS,
    )
    sell_stop_response = sell_stop(
        symbol="EURUSD",
        volume=Decimal("0.10"),
        price=Decimal("1.09500"),
        request_id="req-sell-stop",
        correlation_id="corr-sell-stop",
        context=context,
        deps=deps,
        **ROUTE_KWARGS,
    )
    for response in (
        limit_response,
        sell_limit_response,
        stop_response,
        sell_stop_response,
    ):
        assert response.status is TradingStatus.ACCEPTED


def test_buy_stop_promotes_to_stop_limit_when_stop_limit_price_given() -> None:
    """buy_stop packages a stop_limit order type when a resting price is given."""
    context = build_context()
    deps = build_deps()
    response = buy_stop(
        symbol="EURUSD",
        volume=Decimal("0.10"),
        price=Decimal("1.10500"),
        stop_limit_price=Decimal("1.10520"),
        request_id="req-stop-limit",
        correlation_id="corr-stop-limit",
        context=context,
        deps=deps,
        **ROUTE_KWARGS,
    )
    assert response.status is TradingStatus.ACCEPTED


def test_order_modify_and_delete_require_ticket() -> None:
    """order_modify/order_delete reject a blank ticket and package otherwise."""
    deps = build_deps()
    with pytest.raises(TradingMappedError):
        order_modify(
            ticket=" ",
            symbol="EURUSD",
            request_id="req-1",
            correlation_id="corr-1",
            deps=deps,
            **ROUTE_KWARGS,
        )
    with pytest.raises(TradingMappedError):
        order_delete(
            ticket="",
            symbol="EURUSD",
            request_id="req-2",
            correlation_id="corr-2",
            deps=deps,
            **ROUTE_KWARGS,
        )
    modify_response = order_modify(
        ticket="123",
        price=Decimal("1.10600"),
        expected_state_version=3,
        symbol="EURUSD",
        request_id="req-3",
        correlation_id="corr-3",
        deps=deps,
        **ROUTE_KWARGS,
    )
    delete_response = order_delete(
        ticket="123",
        symbol="EURUSD",
        request_id="req-4",
        correlation_id="corr-4",
        deps=deps,
        **ROUTE_KWARGS,
    )
    assert modify_response.status is TradingStatus.ACCEPTED
    assert delete_response.status is TradingStatus.ACCEPTED


def test_submit_oco_group_validates_group_shape() -> None:
    """submit_oco_group enforces group id, leg count, and symbol consistency."""
    context = build_context()
    deps = build_deps()
    entry = OrderIntent(
        symbol="EURUSD",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        volume=Decimal("0.10"),
        max_slippage_points=10,
    )
    with pytest.raises(TradingMappedError):
        submit_oco_group(
            (entry,),
            contexts=(context,),
            oco_group_id="",
            request_id="req-1",
            correlation_id="corr-1",
            deps=deps,
            **ROUTE_KWARGS,
        )
    with pytest.raises(TradingMappedError):
        submit_oco_group(
            (entry,),
            contexts=(context,),
            oco_group_id="grp-1",
            request_id="req-2",
            correlation_id="corr-2",
            deps=deps,
            **ROUTE_KWARGS,
        )
    with pytest.raises(TradingMappedError):
        submit_oco_group(
            (entry, entry),
            contexts=(context,),
            oco_group_id="grp-1",
            request_id="req-3",
            correlation_id="corr-3",
            deps=deps,
            **ROUTE_KWARGS,
        )
    other_symbol = OrderIntent(
        symbol="GBPUSD",
        side=OrderSide.SELL,
        order_type=OrderType.MARKET,
        volume=Decimal("0.10"),
        max_slippage_points=10,
    )
    with pytest.raises(TradingMappedError):
        submit_oco_group(
            (entry, other_symbol),
            contexts=(context, context),
            oco_group_id="grp-1",
            request_id="req-4",
            correlation_id="corr-4",
            deps=deps,
            **ROUTE_KWARGS,
        )


def test_submit_oco_group_packages_valid_group() -> None:
    """A valid two-leg OCO group is validated and packaged together."""
    wide_collar_context = build_context()
    wide_collar_context = wide_collar_context.model_copy(
        update={
            "constraints": wide_collar_context.constraints.model_copy(
                update={"price_collar_bps": Decimal(2000)}
            )
        }
    )
    deps = build_deps()
    entry = OrderIntent(
        symbol="EURUSD",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        volume=Decimal("0.10"),
        max_slippage_points=10,
    )
    stop_leg = OrderIntent(
        symbol="EURUSD",
        side=OrderSide.SELL,
        order_type=OrderType.STOP,
        volume=Decimal("0.10"),
        price=Decimal("1.09000"),
    )
    response = submit_oco_group(
        (entry, stop_leg),
        contexts=(wide_collar_context, wide_collar_context),
        oco_group_id="grp-1",
        request_id="req-5",
        correlation_id="corr-5",
        deps=deps,
        **ROUTE_KWARGS,
    )
    assert response.status is TradingStatus.ACCEPTED
