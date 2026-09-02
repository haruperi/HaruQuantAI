"""FR 5: MetaTrader 5 Historical Orders."""

from __future__ import annotations

import time
from typing import Any

try:
    import MetaTrader5 as mt5  # noqa: N813

    _MT5_AVAILABLE = True
except ImportError:
    mt5 = None  # type: ignore[assignment]
    _MT5_AVAILABLE = False


def list_order_history(
    symbol: str | None = None,
    start: Any = None,
    end: Any = None,
) -> list[dict[str, Any]]:
    """Retrieve historical orders from MT5.

    Args:
        symbol: Optional symbol filter.
        start: Optional start timestamp.
        end: Optional end timestamp.

    Returns:
        List of historical order dictionaries.

    Raises:
        RuntimeError: If history orders query fails.
    """
    if not _MT5_AVAILABLE or mt5 is None:
        msg = "MetaTrader5 package is not available."
        raise RuntimeError(msg)

    start_ts = int(start) if start else 0
    end_ts = int(end) if end else int(time.time())

    orders = (
        mt5.history_orders_get(start_ts, end_ts, symbol=symbol.upper())
        if symbol
        else mt5.history_orders_get(start_ts, end_ts)
    )
    if orders is None:
        err = mt5.last_error()
        msg = f"Failed to retrieve historical orders from MetaTrader 5: [{err[0]}] {err[1]}"
        raise RuntimeError(msg)

    return [o._asdict() for o in orders]


def get_history_order(order_id: int | str) -> dict[str, Any] | None:
    """Retrieve single historical order by ticket.

    Args:
        order_id: Order ticket ID.

    Returns:
        Historical order dictionary if found, None otherwise.

    Raises:
        RuntimeError: If history order query fails.
    """
    if not _MT5_AVAILABLE or mt5 is None:
        msg = "MetaTrader5 package is not available."
        raise RuntimeError(msg)

    oid = int(order_id) if str(order_id).isdigit() else order_id
    if not isinstance(oid, int):
        return None

    orders = mt5.history_orders_get(ticket=oid)
    if orders is None:
        err = mt5.last_error()
        msg = f"Failed to retrieve historical order {order_id} from MetaTrader 5: [{err[0]}] {err[1]}"
        raise RuntimeError(msg)

    return orders[0]._asdict() if len(orders) > 0 else None
