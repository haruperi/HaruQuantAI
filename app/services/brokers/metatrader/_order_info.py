"""FR 4: MetaTrader 5 Pending and Active Orders and Pre-Trade Checks."""

from __future__ import annotations

from typing import Any

try:
    import MetaTrader5 as mt5  # noqa: N813

    _MT5_AVAILABLE = True
except ImportError:
    mt5 = None  # type: ignore[assignment]
    _MT5_AVAILABLE = False


def get_orders(symbol: str | None = None) -> list[dict[str, Any]]:
    """Retrieve active and pending orders from MT5.

    Args:
        symbol: Optional symbol filter.

    Returns:
        List of active order dictionaries.

    Raises:
        RuntimeError: If orders query fails.
    """
    if not _MT5_AVAILABLE or mt5 is None:
        msg = "MetaTrader5 package is not available."
        raise RuntimeError(msg)

    orders = mt5.orders_get(symbol=symbol.upper()) if symbol else mt5.orders_get()
    if orders is None:
        err = mt5.last_error()
        msg = f"Failed to retrieve orders from MetaTrader 5: [{err[0]}] {err[1]}"
        raise RuntimeError(msg)

    return [o._asdict() for o in orders]


def get_order(order_id: int | str) -> dict[str, Any] | None:
    """Retrieve individual active order by ticket number.

    Args:
        order_id: Order ticket ID.

    Returns:
        Order dictionary if found, None otherwise.

    Raises:
        RuntimeError: If order query fails.
    """
    if not _MT5_AVAILABLE or mt5 is None:
        msg = "MetaTrader5 package is not available."
        raise RuntimeError(msg)

    oid = int(order_id) if str(order_id).isdigit() else order_id
    if not isinstance(oid, int):
        return None

    orders = mt5.orders_get(ticket=oid)
    if orders is None:
        err = mt5.last_error()
        msg = f"Failed to retrieve order {order_id} from MetaTrader 5: [{err[0]}] {err[1]}"
        raise RuntimeError(msg)

    return orders[0]._asdict() if len(orders) > 0 else None


def check_order(request: dict[str, Any]) -> dict[str, Any]:
    """Perform pre-trade check via MT5 order_check.

    Args:
        request: Order placement request dictionary.

    Returns:
        Dictionary containing validation result.

    Raises:
        RuntimeError: If order_check query fails.
    """
    if not _MT5_AVAILABLE or mt5 is None:
        msg = "MetaTrader5 package is not available."
        raise RuntimeError(msg)

    res = mt5.order_check(request)
    if res is None:
        err = mt5.last_error()
        msg = f"Failed to check order in MetaTrader 5: [{err[0]}] {err[1]}"
        raise RuntimeError(msg)

    return res._asdict()
