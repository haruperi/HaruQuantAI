"""Unit tests for FR 8: Trade Execution and Margin/Profit Calculations."""

from __future__ import annotations

import pytest
from app.services.brokers.operations._trade import (
    calculate_margin,
    calculate_profit,
    cancel_order,
    close_position,
    modify_order,
    modify_position,
    place_order,
)


def test_place_modify_cancel_pending_order() -> None:
    """Verify pending order placement, parameter modification, and cancellation."""
    res = place_order(
        {
            "symbol": "EURUSD",
            "type": "BUY_LIMIT",
            "volume": 0.5,
            "price": 1.07500,
            "sl": 1.07000,
            "tp": 1.08500,
        }
    )
    assert res["status"] == "PLACED"
    order_id = res["order_id"]

    mod_res = modify_order({"order_id": order_id, "price": 1.07600, "sl": 1.07100})
    assert mod_res["status"] == "MODIFIED"
    assert mod_res["price"] == 1.07600

    cancel_res = cancel_order(order_id)
    assert cancel_res["status"] == "CANCELLED"

    with pytest.raises(ValueError, match="not found"):
        cancel_order(order_id)


def test_place_market_order_and_close_position() -> None:
    """Verify market order opens position, modify position, and close position."""
    res = place_order(
        {
            "symbol": "GBPUSD",
            "type": "BUY",
            "volume": 0.3,
            "price": 1.26500,
        }
    )
    assert res["status"] == "FILLED"
    pos_id = res["position_id"]

    mod_pos = modify_position({"position_id": pos_id, "sl": 1.25800, "tp": 1.27500})
    assert mod_pos["status"] == "MODIFIED"
    assert mod_pos["sl"] == 1.25800

    part_close = close_position(pos_id, volume=0.1)
    assert part_close["status"] == "PARTIALLY_CLOSED"
    assert part_close["remaining_volume"] == 0.2

    full_close = close_position(pos_id)
    assert full_close["status"] == "CLOSED"

    with pytest.raises(ValueError, match="not found"):
        close_position(pos_id)


def test_margin_and_profit_calculations() -> None:
    """Verify standard leverage margin and profit calculations."""
    margin = calculate_margin({"volume": 1.0, "leverage": 100.0})
    assert margin == 1000.0

    profit_buy = calculate_profit(
        {
            "volume": 1.0,
            "open_price": 1.08000,
            "close_price": 1.08500,
            "order_type": "BUY",
        }
    )
    assert profit_buy == 500.0

    profit_sell = calculate_profit(
        {
            "volume": 1.0,
            "open_price": 1.08500,
            "close_price": 1.08000,
            "order_type": "SELL",
        }
    )
    assert profit_sell == 500.0
