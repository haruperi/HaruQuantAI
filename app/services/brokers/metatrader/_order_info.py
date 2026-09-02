"""FR 4: MetaTrader 5 Pending and Active Orders and Pre-Trade Checks."""

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


def get_orders(
    symbol: str | None = None,
    client: MetaTraderClient | Any | None = None,
) -> list[dict[str, Any]]:
    """Retrieve active and pending orders from MT5.

    Args:
        symbol: Optional symbol filter.
        client: Optional MetaTraderClient instance.

    Returns:
        List of active order dictionaries.

    Raises:
        RuntimeError: If orders query fails.
    """
    client_inst = _resolve_client(client)
    mt5 = getattr(client_inst, "mt5", client_inst)
    if mt5 is None or not getattr(client_inst, "is_available", lambda: True)():
        msg = "MetaTrader5 package is not available."
        raise RuntimeError(msg)

    orders = mt5.orders_get(symbol=symbol.upper()) if symbol else mt5.orders_get()
    if orders is None:
        err = (
            mt5.last_error()
            if hasattr(mt5, "last_error")
            else (-1, "Orders query failed")
        )
        msg = f"Failed to retrieve orders from MetaTrader 5: [{err[0]}] {err[1]}"
        raise RuntimeError(msg)

    return [o._asdict() for o in orders]


def get_order(
    order_id: int | str,
    client: MetaTraderClient | Any | None = None,
) -> dict[str, Any] | None:
    """Retrieve individual active order by ticket number.

    Args:
        order_id: Order ticket ID.
        client: Optional MetaTraderClient instance.

    Returns:
        Order dictionary if found, None otherwise.

    Raises:
        RuntimeError: If order query fails.
    """
    client_inst = _resolve_client(client)
    mt5 = getattr(client_inst, "mt5", client_inst)
    if mt5 is None or not getattr(client_inst, "is_available", lambda: True)():
        msg = "MetaTrader5 package is not available."
        raise RuntimeError(msg)

    oid = int(order_id) if str(order_id).isdigit() else order_id
    if not isinstance(oid, int):
        return None

    orders = mt5.orders_get(ticket=oid)
    if orders is None:
        err = (
            mt5.last_error()
            if hasattr(mt5, "last_error")
            else (-1, "Order query failed")
        )
        msg = f"Failed to retrieve order {order_id} from MetaTrader 5: [{err[0]}] {err[1]}"
        raise RuntimeError(msg)

    return orders[0]._asdict() if len(orders) > 0 else None


def check_order(
    request: dict[str, Any],
    client: MetaTraderClient | Any | None = None,
) -> dict[str, Any]:
    """Perform pre-trade check via MT5 order_check.

    Args:
        request: Order placement request dictionary.
        client: Optional MetaTraderClient instance.

    Returns:
        Dictionary containing validation result.

    Raises:
        RuntimeError: If order_check query fails.
    """
    client_inst = _resolve_client(client)
    mt5 = getattr(client_inst, "mt5", client_inst)
    if mt5 is None or not getattr(client_inst, "is_available", lambda: True)():
        msg = "MetaTrader5 package is not available."
        raise RuntimeError(msg)

    res = mt5.order_check(request)
    if res is None:
        err = (
            mt5.last_error()
            if hasattr(mt5, "last_error")
            else (-1, "Order check failed")
        )
        msg = f"Failed to check order in MetaTrader 5: [{err[0]}] {err[1]}"
        raise RuntimeError(msg)

    return res._asdict()
