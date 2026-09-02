"""FR 7: MetaTrader 5 Open Trading Positions."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.services.brokers.metatrader.client import MetaTraderClient


def _resolve_client(client: MetaTraderClient | Any | None = None) -> Any:
    """Resolve the provided client instance or fall back to the active default."""
    if client is not None:
        return client
    from app.services.brokers.metatrader.client import get_default_client

    return get_default_client()


def get_positions(
    symbol: str | None = None,
    client: MetaTraderClient | Any | None = None,
) -> list[dict[str, Any]]:
    """Retrieve open positions from MT5.

    Args:
        symbol: Optional symbol filter.
        client: Optional MetaTraderClient instance.

    Returns:
        List of open position dictionaries.

    Raises:
        RuntimeError: If positions query fails.
    """
    client_inst = _resolve_client(client)
    mt5 = getattr(client_inst, "mt5", client_inst)
    if mt5 is None or not getattr(client_inst, "is_available", lambda: True)():
        msg = "MetaTrader5 package is not available."
        raise RuntimeError(msg)

    pos = mt5.positions_get(symbol=symbol.upper()) if symbol else mt5.positions_get()
    if pos is None:
        err = (
            mt5.last_error()
            if hasattr(mt5, "last_error")
            else (-1, "Positions query failed")
        )
        msg = f"Failed to retrieve positions from MetaTrader 5: [{err[0]}] {err[1]}"
        raise RuntimeError(msg)

    return [p._asdict() for p in pos]


def get_position(
    position_id: int | str,
    client: MetaTraderClient | Any | None = None,
) -> dict[str, Any] | None:
    """Retrieve individual position by ticket.

    Args:
        position_id: Position ticket ID.
        client: Optional MetaTraderClient instance.

    Returns:
        Position dictionary if found, None otherwise.

    Raises:
        RuntimeError: If position query fails.
    """
    client_inst = _resolve_client(client)
    mt5 = getattr(client_inst, "mt5", client_inst)
    if mt5 is None or not getattr(client_inst, "is_available", lambda: True)():
        msg = "MetaTrader5 package is not available."
        raise RuntimeError(msg)

    pid = int(position_id) if str(position_id).isdigit() else position_id
    if not isinstance(pid, int):
        return None

    pos = mt5.positions_get(ticket=pid)
    if pos is None:
        err = (
            mt5.last_error()
            if hasattr(mt5, "last_error")
            else (-1, "Position query failed")
        )
        msg = f"Failed to retrieve position {position_id} from MetaTrader 5: [{err[0]}] {err[1]}"
        raise RuntimeError(msg)

    return pos[0]._asdict() if len(pos) > 0 else None
