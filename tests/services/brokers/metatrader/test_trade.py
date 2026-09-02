"""Unit tests for MetaTrader 5 FR 8: Trade Execution and Calculations."""

from __future__ import annotations

from unittest.mock import MagicMock

import app.services.brokers.metatrader._trade as trade_mod
import pytest
from app.services.brokers.metatrader._trade import (
    calculate_margin,
    calculate_profit,
    cancel_order,
    close_position,
    modify_order,
    modify_position,
    place_order,
)


def test_trade_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify order execution, modifications, and calculations."""
    mock_res = MagicMock()
    mock_res.retcode = 10009  # TRADE_RETCODE_DONE
    mock_res.order = 100501
    mock_res._asdict.return_value = {
        "retcode": 10009,
        "order": 100501,
        "volume": 0.1,
        "price": 1.08500,
        "comment": "Done",
    }

    monkeypatch.setattr(trade_mod.mt5, "order_send", lambda req: mock_res)
    monkeypatch.setattr(trade_mod.mt5, "order_calc_margin", lambda *a: 1000.0)
    monkeypatch.setattr(trade_mod.mt5, "order_calc_profit", lambda *a: 500.0)

    res = place_order({"symbol": "EURUSD", "volume": 0.1, "type": 0, "price": 1.08500})
    assert res["retcode"] == 10009
    assert res["order"] == 100501

    mod_res = modify_order({"order": 101, "price": 1.08200})
    assert mod_res["retcode"] == 10009

    cancel_res = cancel_order(101)
    assert cancel_res["retcode"] == 10009

    mod_pos = modify_position({"position": 901, "sl": 1.07500})
    assert mod_pos["retcode"] == 10009

    close_res = close_position(901)
    assert close_res["retcode"] == 10009

    margin = calculate_margin({"symbol": "EURUSD", "volume": 1.0})
    assert margin == 1000.0

    profit = calculate_profit({"symbol": "EURUSD", "volume": 1.0})
    assert profit == 500.0


def test_trade_failure_raises_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify order execution failure raises RuntimeError."""
    monkeypatch.setattr(trade_mod.mt5, "order_send", lambda req: None)
    monkeypatch.setattr(
        trade_mod.mt5, "last_error", lambda: (-10004, "No IPC connection")
    )

    with pytest.raises(RuntimeError, match=r"Failed to execute order in MetaTrader 5"):
        place_order({"symbol": "EURUSD", "volume": 0.1})
