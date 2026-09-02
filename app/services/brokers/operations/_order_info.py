"""FR 4: Pending and Active Orders and Pre-Trade Checks."""

from __future__ import annotations

import time
from typing import Any

# Active / Pending in-memory orders store
_active_orders: dict[int, dict[str, Any]] = {
    101: {
        "order_id": 101,
        "symbol": "EURUSD",
        "type": "BUY_LIMIT",
        "volume": 0.1,
        "price_open": 1.08000,
        "sl": 1.07500,
        "tp": 1.09000,
        "state": "PLACED",
        "time_setup": time.time() - 3600,
        "comment": "Demo Limit Order",
    },
    102: {
        "order_id": 102,
        "symbol": "GBPUSD",
        "type": "SELL_LIMIT",
        "volume": 0.2,
        "price_open": 1.27000,
        "sl": 1.27500,
        "tp": 1.26000,
        "state": "PLACED",
        "time_setup": time.time() - 1800,
        "comment": "Demo Short Order",
    },
}


def get_orders(symbol: str | None = None) -> list[dict[str, Any]]:
    """Retrieve list of all active/pending orders, optionally filtered by symbol.

    Args:
        symbol: Optional symbol filter.

    Returns:
        List of order dictionaries.
    """
    orders = list(_active_orders.values())
    if symbol:
        sym = symbol.upper()
        return [o for o in orders if o["symbol"] == sym]
    return orders


def get_order(order_id: int | str) -> dict[str, Any] | None:
    """Retrieve details for a specific active order by ID.

    Args:
        order_id: Order identifier.

    Returns:
        Order dictionary if found, None otherwise.
    """
    oid = int(order_id) if str(order_id).isdigit() else order_id
    return _active_orders.get(oid)  # type: ignore[arg-type]


def check_order(request: dict[str, Any]) -> dict[str, Any]:
    """Perform pre-trade validation checks (margin, volume, syntax).

    Args:
        request: Order placement request dictionary.

    Returns:
        Dictionary containing validation result, margin requirement, and error if any.
    """
    symbol = request.get("symbol", "").upper()
    volume = float(request.get("volume", 0.0))

    if not symbol:
        return {"retcode": 10013, "valid": False, "comment": "Invalid symbol"}
    if volume <= 0:
        return {"retcode": 10014, "valid": False, "comment": "Invalid volume"}

    # Estimate required margin
    margin = volume * 1000.0
    return {
        "retcode": 0,
        "valid": True,
        "comment": "Order check passed",
        "margin": margin,
        "margin_free": 10050.0,
        "balance": 10000.0,
        "equity": 10250.0,
    }
