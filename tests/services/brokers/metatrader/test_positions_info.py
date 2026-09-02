"""Unit tests for MetaTrader 5 FR 7: Open Positions."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from app.services.brokers.metatrader._positions_info import (
    get_position,
    get_positions,
)
from app.services.brokers.metatrader.client import MetaTraderClient


def test_positions_success() -> None:
    """Verify open positions retrieval and ticket lookup via client instance."""
    mock_pos = MagicMock()
    mock_pos.ticket = 901
    mock_pos._asdict.return_value = {
        "ticket": 901,
        "symbol": "EURUSD",
        "type": 0,
        "volume": 0.5,
        "profit": 150.0,
    }

    mock_mt5 = MagicMock()
    mock_mt5.positions_get.return_value = (mock_pos,)

    client = MetaTraderClient(mt5_module=mock_mt5)

    positions = get_positions(client=client)
    assert len(positions) == 1
    assert positions[0]["ticket"] == 901

    pos = get_position(901, client=client)
    assert pos is not None
    assert pos["ticket"] == 901


def test_positions_failure_raises_error() -> None:
    """Verify positions query failure raises RuntimeError."""
    mock_mt5 = MagicMock()
    mock_mt5.positions_get.return_value = None
    mock_mt5.last_error.return_value = (-10004, "No IPC connection")

    client = MetaTraderClient(mt5_module=mock_mt5)

    with pytest.raises(
        RuntimeError, match=r"Failed to retrieve positions from MetaTrader 5"
    ):
        get_positions(client=client)
