"""Unit tests for FR 4: Pending and Active Orders and Pre-Trade Checks."""

from __future__ import annotations

from app.services.brokers.operations._order_info import (
    check_order,
    get_order,
    get_orders,
)


def test_get_orders_and_filtering() -> None:
    """Verify listing active orders and symbol filtering."""
    orders = get_orders()
    assert len(orders) >= 2

    eur_orders = get_orders(symbol="EURUSD")
    assert all(o["symbol"] == "EURUSD" for o in eur_orders)

    order = get_order(101)
    assert order is not None
    assert order["symbol"] == "EURUSD"

    assert get_order(999999) is None


def test_check_order_validation() -> None:
    """Verify pre-trade order validation checks."""
    valid_res = check_order({"symbol": "EURUSD", "volume": 0.5, "type": "BUY"})
    assert valid_res["valid"] is True
    assert valid_res["margin"] > 0

    invalid_sym = check_order({"symbol": "", "volume": 0.5})
    assert invalid_sym["valid"] is False

    invalid_vol = check_order({"symbol": "EURUSD", "volume": 0.0})
    assert invalid_vol["valid"] is False
