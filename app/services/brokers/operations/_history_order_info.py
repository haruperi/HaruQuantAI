"""FR 5: Historical Orders and Audit Listings."""

from __future__ import annotations

import time
from typing import Any

_history_orders: dict[int, dict[str, Any]] = {
    501: {
        "order_id": 501,
        "symbol": "EURUSD",
        "type": "BUY",
        "volume_initial": 0.5,
        "volume_current": 0.0,
        "price_open": 1.08200,
        "price_current": 1.08500,
        "state": "FILLED",
        "time_setup": time.time() - 86400,
        "time_done": time.time() - 86390,
        "comment": "Historical Fill",
    },
    502: {
        "order_id": 502,
        "symbol": "USDJPY",
        "type": "SELL",
        "volume_initial": 1.0,
        "volume_current": 0.0,
        "price_open": 154.500,
        "price_current": 154.200,
        "state": "FILLED",
        "time_setup": time.time() - 43200,
        "time_done": time.time() - 43190,
        "comment": "Historical Short Fill",
    },
}


def list_order_history(
    symbol: str | None = None,
    start: Any = None,
    end: Any = None,
) -> list[dict[str, Any]]:
    """Retrieve historical closed/cancelled orders, optionally filtered by symbol and dates.

    Args:
        symbol: Optional symbol filter.
        start: Optional start timestamp.
        end: Optional end timestamp.

    Returns:
        List of historical order dictionaries.
    """
    orders = list(_history_orders.values())
    if symbol:
        sym = symbol.upper()
        orders = [o for o in orders if o["symbol"] == sym]
    if start is not None:
        orders = [o for o in orders if o["time_done"] >= float(start)]
    if end is not None:
        orders = [o for o in orders if o["time_done"] <= float(end)]
    return orders


def get_history_order(order_id: int | str) -> dict[str, Any] | None:
    """Retrieve an individual historical order record by ID.

    Args:
        order_id: Historical order identifier.

    Returns:
        Order dictionary if found, None otherwise.
    """
    oid = int(order_id) if str(order_id).isdigit() else order_id
    return _history_orders.get(oid)  # type: ignore[arg-type]
