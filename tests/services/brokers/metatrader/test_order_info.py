"""Unit tests for MetaTrader 5 FR 4: Active Orders and Pre-Trade Checks."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from app.services.brokers.metatrader._order_info import (
    check_order,
    get_order,
    get_orders,
)
from app.services.brokers.metatrader.client import MetaTraderClient


def test_get_orders_and_check_success() -> None:
    """Verify active orders retrieval and pre-trade checks via client instance."""
    mock_order = MagicMock()
    mock_order.ticket = 101
    mock_order._asdict.return_value = {
        "ticket": 101,
        "symbol": "EURUSD",
        "type": 2,
        "volume_initial": 0.1,
        "price_open": 1.08000,
    }

    mock_check = MagicMock()
    mock_check._asdict.return_value = {
        "retcode": 0,
        "margin": 100.0,
        "margin_free": 53375.40,
    }

    mock_mt5 = MagicMock()
    mock_mt5.orders_get.return_value = (mock_order,)
    mock_mt5.order_check.return_value = mock_check

    client = MetaTraderClient(mt5_module=mock_mt5)

    orders = get_orders(client=client)
    assert len(orders) == 1
    assert orders[0]["ticket"] == 101

    order = get_order(101, client=client)
    assert order is not None
    assert order["ticket"] == 101

    chk = check_order({"symbol": "EURUSD", "volume": 0.1, "type": 0}, client=client)
    assert chk["retcode"] == 0
    assert chk["margin"] == 100.0


def test_get_orders_failure_raises_error() -> None:
    """Verify orders query failure raises RuntimeError."""
    mock_mt5 = MagicMock()
    mock_mt5.orders_get.return_value = None
    mock_mt5.last_error.return_value = (-10004, "No IPC connection")

    client = MetaTraderClient(mt5_module=mock_mt5)

    with pytest.raises(
        RuntimeError, match=r"Failed to retrieve orders from MetaTrader 5"
    ):
        get_orders(client=client)
