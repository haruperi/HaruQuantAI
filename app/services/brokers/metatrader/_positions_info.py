"""FR 7: MetaTrader 5 Open Trading Positions."""

from __future__ import annotations

from typing import Any

try:
    import MetaTrader5 as mt5  # noqa: N813

    _MT5_AVAILABLE = True
except ImportError:
    mt5 = None  # type: ignore[assignment]
    _MT5_AVAILABLE = False


def get_positions(symbol: str | None = None) -> list[dict[str, Any]]:
    """Retrieve open positions from MT5.

    Args:
        symbol: Optional symbol filter.

    Returns:
        List of open position dictionaries.

    Raises:
        RuntimeError: If positions query fails.
    """
    if not _MT5_AVAILABLE or mt5 is None:
        msg = "MetaTrader5 package is not available."
        raise RuntimeError(msg)

    pos = mt5.positions_get(symbol=symbol.upper()) if symbol else mt5.positions_get()
    if pos is None:
        err = mt5.last_error()
        msg = f"Failed to retrieve positions from MetaTrader 5: [{err[0]}] {err[1]}"
        raise RuntimeError(msg)

    return [p._asdict() for p in pos]


def get_position(position_id: int | str) -> dict[str, Any] | None:
    """Retrieve individual position by ticket.

    Args:
        position_id: Position ticket ID.

    Returns:
        Position dictionary if found, None otherwise.

    Raises:
        RuntimeError: If position query fails.
    """
    if not _MT5_AVAILABLE or mt5 is None:
        msg = "MetaTrader5 package is not available."
        raise RuntimeError(msg)

    pid = int(position_id) if str(position_id).isdigit() else position_id
    if not isinstance(pid, int):
        return None

    pos = mt5.positions_get(ticket=pid)
    if pos is None:
        err = mt5.last_error()
        msg = f"Failed to retrieve position {position_id} from MetaTrader 5: [{err[0]}] {err[1]}"
        raise RuntimeError(msg)

    return pos[0]._asdict() if len(pos) > 0 else None
