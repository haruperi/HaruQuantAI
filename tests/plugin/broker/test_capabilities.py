"""Unit tests verifying capability rejection and contract compliance on data-only brokers."""

from __future__ import annotations

import pytest
from app.plugin.broker import (
    OrderAction,
    OrderType,
    TradeRequest,
    calculate_margin,
    check_order,
    disconnect,
    get_history_deal_info,
    get_history_order_info,
    get_num_history_deals,
    get_num_history_orders,
    get_num_orders,
    get_num_positions,
    get_order_info,
    get_position_info,
    is_connected,
    trade,
)

DATA_ONLY_BROKERS = [
    ("yahoo", "Yahoo"),
    ("dukascopy", "Dukascopy"),
    ("darwinex", "Darwinex"),
    ("sq_equity", "SQ_Equity"),
    ("sq_futures", "SQ_Futures"),
]


@pytest.mark.parametrize("broker_alias,expected_name", DATA_ONLY_BROKERS)
def test_data_only_brokers_reject_trade(broker_alias: str, expected_name: str) -> None:
    """Verify that attempting to trade on a data-only broker fails gracefully with standard message."""
    req = TradeRequest(
        action=OrderAction.DEAL,
        symbol="AAPL",
        volume=1.0,
        type=OrderType.BUY,
    )
    res = trade(broker=broker_alias, request=req)
    assert res.is_success is False
    assert f"{expected_name} doesn't have trading capabilities" in res.message


@pytest.mark.parametrize("broker_alias,expected_name", DATA_ONLY_BROKERS)
def test_data_only_brokers_reject_check_order(
    broker_alias: str, expected_name: str
) -> None:
    """Verify check_order rejection on data-only brokers."""
    req = TradeRequest(symbol="EURUSD", volume=0.01)
    res = check_order(broker=broker_alias, request=req)
    assert res.is_success is False
    assert f"{expected_name} doesn't have trading capabilities" in res.message


@pytest.mark.parametrize("broker_alias,expected_name", DATA_ONLY_BROKERS)
def test_data_only_brokers_reject_margin_calc(
    broker_alias: str, expected_name: str
) -> None:
    """Verify calculate_margin rejection on data-only brokers."""
    res = calculate_margin(broker=broker_alias, symbol="EURUSD")
    assert res.is_success is False
    assert (
        f"{expected_name} doesn't have margin calculation capabilities" in res.message
    )


@pytest.mark.parametrize("broker_alias,expected_name", DATA_ONLY_BROKERS)
def test_data_only_brokers_reject_positions_and_orders(
    broker_alias: str, expected_name: str
) -> None:
    """Verify positions and active orders inspection rejections."""
    res_pos = get_position_info(broker=broker_alias)
    assert res_pos.is_success is False
    assert f"{expected_name} doesn't have position capabilities" in res_pos.message

    res_num_pos = get_num_positions(broker=broker_alias)
    assert res_num_pos.is_success is False

    res_orders = get_order_info(broker=broker_alias)
    assert res_orders.is_success is False
    assert f"{expected_name} doesn't have orders capabilities" in res_orders.message

    res_num_ord = get_num_orders(broker=broker_alias)
    assert res_num_ord.is_success is False


@pytest.mark.parametrize("broker_alias,expected_name", DATA_ONLY_BROKERS)
def test_data_only_brokers_reject_history(
    broker_alias: str, expected_name: str
) -> None:
    """Verify historical deals and orders inspection rejections."""
    res_h_ord = get_history_order_info(broker=broker_alias)
    assert res_h_ord.is_success is False
    assert f"{expected_name} doesn't have history capabilities" in res_h_ord.message

    res_h_deals = get_history_deal_info(broker=broker_alias)
    assert res_h_deals.is_success is False
    assert f"{expected_name} doesn't have history capabilities" in res_h_deals.message

    assert get_num_history_orders(broker=broker_alias).is_success is False
    assert get_num_history_deals(broker=broker_alias).is_success is False


@pytest.mark.parametrize("broker_alias,_", DATA_ONLY_BROKERS)
def test_data_only_brokers_connection_status(broker_alias: str, _: str) -> None:
    """Verify is_connected and disconnect work cleanly on all data brokers."""
    res = is_connected(broker=broker_alias)
    assert res.is_success is True

    disc = disconnect(broker=broker_alias)
    assert disc.is_success is True
