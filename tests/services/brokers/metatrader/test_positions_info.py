"""Unit tests for MetaTrader 5 FR 7: Open Positions."""

from __future__ import annotations

from unittest.mock import MagicMock

import app.services.brokers.metatrader._positions_info as pos_mod
import pytest
from app.services.brokers.metatrader._positions_info import (
    get_position,
    get_positions,
)


def test_positions_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify open positions retrieval and ticket lookup."""
    mock_pos = MagicMock()
    mock_pos.ticket = 901
    mock_pos._asdict.return_value = {
        "ticket": 901,
        "symbol": "EURUSD",
        "type": 0,
        "volume": 0.5,
        "profit": 150.0,
    }

    monkeypatch.setattr(pos_mod.mt5, "positions_get", lambda **kw: (mock_pos,))

    positions = get_positions()
    assert len(positions) == 1
    assert positions[0]["ticket"] == 901

    pos = get_position(901)
    assert pos is not None
    assert pos["ticket"] == 901


def test_positions_failure_raises_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify positions query failure raises RuntimeError."""
    monkeypatch.setattr(pos_mod.mt5, "positions_get", lambda **kw: None)
    monkeypatch.setattr(
        pos_mod.mt5, "last_error", lambda: (-10004, "No IPC connection")
    )

    with pytest.raises(
        RuntimeError, match=r"Failed to retrieve positions from MetaTrader 5"
    ):
        get_positions()
