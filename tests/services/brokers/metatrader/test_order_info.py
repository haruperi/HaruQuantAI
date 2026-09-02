"""Unit tests for MetaTrader 5 FR 4: Active Orders and Pre-Trade Checks."""

from __future__ import annotations

from unittest.mock import MagicMock

import app.services.brokers.metatrader._order_info as order_mod
import pytest
from app.services.brokers.metatrader._order_info import (
    check_order,
    get_order,
    get_orders,
)


def test_get_orders_and_check_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify active orders retrieval and pre-trade checks."""
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

    monkeypatch.setattr(order_mod.mt5, "orders_get", lambda **kw: (mock_order,))
    monkeypatch.setattr(order_mod.mt5, "order_check", lambda req: mock_check)

    orders = get_orders()
    assert len(orders) == 1
    assert orders[0]["ticket"] == 101

    order = get_order(101)
    assert order is not None
    assert order["ticket"] == 101

    chk = check_order({"symbol": "EURUSD", "volume": 0.1, "type": 0})
    assert chk["retcode"] == 0
    assert chk["margin"] == 100.0


def test_get_orders_failure_raises_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify orders query failure raises RuntimeError."""
    monkeypatch.setattr(order_mod.mt5, "orders_get", lambda **kw: None)
    monkeypatch.setattr(
        order_mod.mt5, "last_error", lambda: (-10004, "No IPC connection")
    )

    with pytest.raises(
        RuntimeError, match=r"Failed to retrieve orders from MetaTrader 5"
    ):
        get_orders()
