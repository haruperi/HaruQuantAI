"""Unit tests for MetaTrader 5 FR 5: Historical Orders."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from app.services.brokers.metatrader._history_order_info import (
    get_history_order,
    list_order_history,
)
from app.services.brokers.metatrader.client import MetaTraderClient


def test_list_and_get_history_orders_success() -> None:
    """Verify historical orders listing and individual lookup via client instance."""
    mock_order = MagicMock()
    mock_order.ticket = 501
    mock_order._asdict.return_value = {
        "ticket": 501,
        "symbol": "EURUSD",
        "type": 0,
        "state": 4,
        "volume_initial": 0.5,
    }

    mock_mt5 = MagicMock()
    mock_mt5.history_orders_get.return_value = (mock_order,)

    client = MetaTraderClient(mt5_module=mock_mt5)

    history = list_order_history(client=client)
    assert len(history) == 1
    assert history[0]["ticket"] == 501

    h_order = get_history_order(501, client=client)
    assert h_order is not None
    assert h_order["ticket"] == 501


def test_list_history_orders_failure_raises_error() -> None:
    """Verify history orders query failure raises RuntimeError."""
    mock_mt5 = MagicMock()
    mock_mt5.history_orders_get.return_value = None
    mock_mt5.last_error.return_value = (-10004, "No IPC connection")

    client = MetaTraderClient(mt5_module=mock_mt5)

    with pytest.raises(
        RuntimeError, match=r"Failed to retrieve historical orders from MetaTrader 5"
    ):
        list_order_history(client=client)
