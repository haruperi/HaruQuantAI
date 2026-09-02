"""Unit tests for MetaTrader 5 FR 8: Trade Execution and Calculations."""

from __future__ import annotations

from unittest.mock import MagicMock

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
from app.services.brokers.metatrader.client import MetaTraderClient


def test_trade_success() -> None:
    """Verify order execution, modifications, and calculations via client instance."""
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

    mock_pos = MagicMock()
    mock_pos.ticket = 901
    mock_pos._asdict.return_value = {
        "ticket": 901,
        "symbol": "EURUSD",
        "type": 0,
        "volume": 0.5,
        "price_current": 1.08500,
    }

    mock_mt5 = MagicMock()
    mock_mt5.order_send.return_value = mock_res
    mock_mt5.order_calc_margin.return_value = 1000.0
    mock_mt5.order_calc_profit.return_value = 500.0
    mock_mt5.positions_get.return_value = (mock_pos,)

    client = MetaTraderClient(mt5_module=mock_mt5)

    res = place_order(
        {"symbol": "EURUSD", "volume": 0.1, "type": 0, "price": 1.08500},
        client=client,
    )
    assert res["retcode"] == 10009
    assert res["order"] == 100501

    mod_res = modify_order({"order": 101, "price": 1.08200}, client=client)
    assert mod_res["retcode"] == 10009

    cancel_res = cancel_order(101, client=client)
    assert cancel_res["retcode"] == 10009

    mod_pos = modify_position({"position": 901, "sl": 1.07500}, client=client)
    assert mod_pos["retcode"] == 10009

    close_res = close_position(901, client=client)
    assert close_res["retcode"] == 10009

    margin = calculate_margin({"symbol": "EURUSD", "volume": 1.0}, client=client)
    assert margin == 1000.0

    profit = calculate_profit({"symbol": "EURUSD", "volume": 1.0}, client=client)
    assert profit == 500.0


def test_trade_failure_raises_error() -> None:
    """Verify order execution failure raises RuntimeError."""
    mock_mt5 = MagicMock()
    mock_mt5.order_send.return_value = None
    mock_mt5.last_error.return_value = (-10004, "No IPC connection")

    client = MetaTraderClient(mt5_module=mock_mt5)

    with pytest.raises(RuntimeError, match=r"Failed to execute order in MetaTrader 5"):
        place_order({"symbol": "EURUSD", "volume": 0.1}, client=client)
