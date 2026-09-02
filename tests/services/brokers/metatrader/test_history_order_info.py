"""Unit tests for MetaTrader 5 FR 5: Historical Orders."""

from __future__ import annotations

from unittest.mock import MagicMock

import app.services.brokers.metatrader._history_order_info as hist_mod
import pytest
from app.services.brokers.metatrader._history_order_info import (
    get_history_order,
    list_order_history,
)


def test_list_and_get_history_orders_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify historical orders listing and individual lookup."""
    mock_order = MagicMock()
    mock_order.ticket = 501
    mock_order._asdict.return_value = {
        "ticket": 501,
        "symbol": "EURUSD",
        "type": 0,
        "state": 4,
        "volume_initial": 0.5,
    }

    monkeypatch.setattr(
        hist_mod.mt5, "history_orders_get", lambda *a, **kw: (mock_order,)
    )

    history = list_order_history()
    assert len(history) == 1
    assert history[0]["ticket"] == 501

    h_order = get_history_order(501)
    assert h_order is not None
    assert h_order["ticket"] == 501


def test_list_history_orders_failure_raises_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify history orders query failure raises RuntimeError."""
    monkeypatch.setattr(hist_mod.mt5, "history_orders_get", lambda *a, **kw: None)
    monkeypatch.setattr(
        hist_mod.mt5, "last_error", lambda: (-10004, "No IPC connection")
    )

    with pytest.raises(
        RuntimeError, match=r"Failed to retrieve historical orders from MetaTrader 5"
    ):
        list_order_history()
