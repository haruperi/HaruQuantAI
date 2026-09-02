"""FR 8: MetaTrader 5 Trade Execution, Position Closing, and Margin/Profit Calculations."""

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


def place_order(
    request: dict[str, Any],
    client: MetaTraderClient | Any | None = None,
) -> dict[str, Any]:
    """Submit order to MT5 via order_send.

    Args:
        request: Order placement request dictionary matching MT5 MqlTradeRequest structure.
        client: Optional MetaTraderClient instance.

    Returns:
        Order execution result dictionary from MT5 MqlTradeResult.

    Raises:
        RuntimeError: If order_send execution fails.
    """
    client_inst = _resolve_client(client)
    mt5 = getattr(client_inst, "mt5", client_inst)
    if mt5 is None or not getattr(client_inst, "is_available", lambda: True)():
        msg = "MetaTrader5 package is not available."
        raise RuntimeError(msg)

    res = mt5.order_send(request)
    if res is None:
        err = (
            mt5.last_error()
            if hasattr(mt5, "last_error")
            else (-1, "Order execution failed")
        )
        msg = f"Failed to execute order in MetaTrader 5: [{err[0]}] {err[1]}"
        raise RuntimeError(msg)

    return res._asdict()


def modify_order(
    request: dict[str, Any],
    client: MetaTraderClient | Any | None = None,
) -> dict[str, Any]:
    """Modify existing pending order via TRADE_ACTION_MODIFY.

    Args:
        request: Order modification parameters.
        client: Optional MetaTraderClient instance.

    Returns:
        Order execution result dictionary.
    """
    client_inst = _resolve_client(client)
    mt5 = getattr(client_inst, "mt5", client_inst)
    req = dict(request)
    action_val = getattr(mt5, "TRADE_ACTION_MODIFY", 7) if mt5 else 7
    req.setdefault("action", action_val)
    return place_order(req, client=client_inst)


def cancel_order(
    order_id: int | str,
    client_request_id: str | None = None,  # noqa: ARG001
    client: MetaTraderClient | Any | None = None,
) -> dict[str, Any]:
    """Cancel pending order via TRADE_ACTION_REMOVE.

    Args:
        order_id: Ticket ID of order to remove.
        client_request_id: Optional tracking identifier.
        client: Optional MetaTraderClient instance.

    Returns:
        Order cancellation result dictionary.
    """
    client_inst = _resolve_client(client)
    mt5 = getattr(client_inst, "mt5", client_inst)
    oid = int(order_id)
    action = getattr(mt5, "TRADE_ACTION_REMOVE", 8) if mt5 else 8
    return place_order({"action": action, "order": oid}, client=client_inst)


def modify_position(
    request: dict[str, Any],
    client: MetaTraderClient | Any | None = None,
) -> dict[str, Any]:
    """Modify open position Stop Loss and Take Profit via TRADE_ACTION_SLTP.

    Args:
        request: Position modification parameters.
        client: Optional MetaTraderClient instance.

    Returns:
        Position modification result dictionary.
    """
    client_inst = _resolve_client(client)
    mt5 = getattr(client_inst, "mt5", client_inst)
    req = dict(request)
    action_val = getattr(mt5, "TRADE_ACTION_SLTP", 6) if mt5 else 6
    req.setdefault("action", action_val)
    return place_order(req, client=client_inst)


def close_position(
    position_id: int | str,
    volume: float | None = None,
    client: MetaTraderClient | Any | None = None,
) -> dict[str, Any]:
    """Close position via TRADE_ACTION_DEAL.

    Args:
        position_id: Ticket ID of position to close.
        volume: Optional volume to close (defaults to full volume).
        client: Optional MetaTraderClient instance.

    Returns:
        Close execution result dictionary.

    Raises:
        ValueError: If position is not found.
    """
    client_inst = _resolve_client(client)
    from app.services.brokers.metatrader._positions_info import get_position

    pos = get_position(position_id, client=client_inst)
    if pos is None:
        msg = f"Position ticket {position_id} not found."
        raise ValueError(msg)

    mt5 = getattr(client_inst, "mt5", client_inst)
    close_type = (
        getattr(mt5, "ORDER_TYPE_SELL", 1)
        if pos.get("type", 0) == 0
        else getattr(mt5, "ORDER_TYPE_BUY", 0)
    )
    close_req = {
        "action": getattr(mt5, "TRADE_ACTION_DEAL", 1) if mt5 else 1,
        "position": pos["ticket"],
        "symbol": pos["symbol"],
        "volume": volume if volume is not None else pos["volume"],
        "type": close_type,
        "price": pos.get("price_current", 0.0),
        "deviation": 20,
    }
    return place_order(close_req, client=client_inst)


def calculate_margin(
    request: dict[str, Any],
    client: MetaTraderClient | Any | None = None,
) -> float:
    """Calculate required margin for order in deposit currency.

    Args:
        request: Dictionary with symbol, action/type, and volume.
        client: Optional MetaTraderClient instance.

    Returns:
        Margin amount as float.

    Raises:
        RuntimeError: If margin calculation query fails.
    """
    client_inst = _resolve_client(client)
    mt5 = getattr(client_inst, "mt5", client_inst)
    if mt5 is None or not getattr(client_inst, "is_available", lambda: True)():
        msg = "MetaTrader5 package is not available."
        raise RuntimeError(msg)

    sym = request.get("symbol", "EURUSD").upper()
    action = request.get("action", getattr(mt5, "ORDER_TYPE_BUY", 0))
    vol = float(request.get("volume", 1.0))
    price = float(request.get("price", 1.0))

    margin = mt5.order_calc_margin(action, sym, vol, price)
    if margin is None:
        err = (
            mt5.last_error()
            if hasattr(mt5, "last_error")
            else (-1, "Margin calculation failed")
        )
        msg = f"Failed to calculate margin in MetaTrader 5: [{err[0]}] {err[1]}"
        raise RuntimeError(msg)

    return float(margin)


def calculate_profit(
    request: dict[str, Any],
    client: MetaTraderClient | Any | None = None,
) -> float:
    """Calculate projected profit/loss for trade.

    Args:
        request: Dictionary with symbol, action/type, volume, open_price, close_price.
        client: Optional MetaTraderClient instance.

    Returns:
        Profit amount in deposit currency as float.

    Raises:
        RuntimeError: If profit calculation query fails.
    """
    client_inst = _resolve_client(client)
    mt5 = getattr(client_inst, "mt5", client_inst)
    if mt5 is None or not getattr(client_inst, "is_available", lambda: True)():
        msg = "MetaTrader5 package is not available."
        raise RuntimeError(msg)

    sym = request.get("symbol", "EURUSD").upper()
    action = request.get("action", getattr(mt5, "ORDER_TYPE_BUY", 0))
    vol = float(request.get("volume", 1.0))
    p_open = float(request.get("open_price", request.get("price_open", 1.0)))
    p_close = float(request.get("close_price", request.get("price_close", 1.0)))

    profit = mt5.order_calc_profit(action, sym, vol, p_open, p_close)
    if profit is None:
        err = (
            mt5.last_error()
            if hasattr(mt5, "last_error")
            else (-1, "Profit calculation failed")
        )
        msg = f"Failed to calculate profit in MetaTrader 5: [{err[0]}] {err[1]}"
        raise RuntimeError(msg)

    return float(profit)
