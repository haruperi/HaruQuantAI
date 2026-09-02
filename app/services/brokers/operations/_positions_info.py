"""FR 7: Open Trading Positions."""

from __future__ import annotations

import time
from typing import Any

_open_positions: dict[int, dict[str, Any]] = {
    901: {
        "position_id": 901,
        "symbol": "EURUSD",
        "type": "POSITION_TYPE_BUY",
        "volume": 0.5,
        "price_open": 1.08200,
        "price_current": 1.08500,
        "sl": 1.07800,
        "tp": 1.09200,
        "profit": 150.0,
        "swap": -1.20,
        "time": time.time() - 7200,
        "comment": "Long EURUSD",
    },
    902: {
        "position_id": 902,
        "symbol": "GBPUSD",
        "type": "POSITION_TYPE_BUY",
        "volume": 0.2,
        "price_open": 1.26000,
        "price_current": 1.26400,
        "sl": 1.25500,
        "tp": 1.27000,
        "profit": 80.0,
        "swap": -0.50,
        "time": time.time() - 3600,
        "comment": "Long GBPUSD",
    },
}


def get_positions(symbol: str | None = None) -> list[dict[str, Any]]:
    """Retrieve all open trading positions, optionally filtered by symbol.

    Args:
        symbol: Optional symbol filter.

    Returns:
        List of open position dictionaries.
    """
    positions = list(_open_positions.values())
    if symbol:
        sym = symbol.upper()
        return [p for p in positions if p["symbol"] == sym]
    return positions


def get_position(position_id: int | str) -> dict[str, Any] | None:
    """Retrieve an individual open position by ID.

    Args:
        position_id: Position identifier.

    Returns:
        Position dictionary if found, None otherwise.
    """
    pid = int(position_id) if str(position_id).isdigit() else position_id
    return _open_positions.get(pid)  # type: ignore[arg-type]
