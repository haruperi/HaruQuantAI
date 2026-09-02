"""FR 8: MetaTrader 5 Trade Execution, Position Closing, and Margin/Profit Calculations."""

from __future__ import annotations

from typing import Any

try:
    import MetaTrader5 as mt5  # noqa: N813

    _MT5_AVAILABLE = True
except ImportError:
    mt5 = None  # type: ignore[assignment]
    _MT5_AVAILABLE = False


def place_order(request: dict[str, Any]) -> dict[str, Any]:
    """Submit order to MT5 via order_send.

    Args:
        request: Order placement request dictionary matching MT5 MqlTradeRequest structure.

    Returns:
        Order execution result dictionary from MT5 MqlTradeResult.

    Raises:
        RuntimeError: If order_send execution fails.
    """
    if not _MT5_AVAILABLE or mt5 is None:
        msg = "MetaTrader5 package is not available."
        raise RuntimeError(msg)

    res = mt5.order_send(request)
    if res is None:
        err = mt5.last_error()
        msg = f"Failed to execute order in MetaTrader 5: [{err[0]}] {err[1]}"
        raise RuntimeError(msg)

    return res._asdict()


def modify_order(request: dict[str, Any]) -> dict[str, Any]:
    """Modify existing pending order via TRADE_ACTION_MODIFY.

    Args:
        request: Order modification parameters.

    Returns:
        Order execution result dictionary.
    """
    req = dict(request)
    if _MT5_AVAILABLE and mt5 is not None:
        req.setdefault("action", getattr(mt5, "TRADE_ACTION_MODIFY", 7))
    return place_order(req)


def cancel_order(
    order_id: int | str,
    client_request_id: str | None = None,  # noqa: ARG001
) -> dict[str, Any]:
    """Cancel pending order via TRADE_ACTION_REMOVE.

    Args:
        order_id: Ticket ID of order to remove.
        client_request_id: Optional tracking identifier.

    Returns:
        Order cancellation result dictionary.
    """
    oid = int(order_id)
    action = (
        getattr(mt5, "TRADE_ACTION_REMOVE", 8)
        if (_MT5_AVAILABLE and mt5 is not None)
        else 8
    )
    return place_order({"action": action, "order": oid})


def modify_position(request: dict[str, Any]) -> dict[str, Any]:
    """Modify open position Stop Loss and Take Profit via TRADE_ACTION_SLTP.

    Args:
        request: Position modification parameters.

    Returns:
        Position modification result dictionary.
    """
    req = dict(request)
    if _MT5_AVAILABLE and mt5 is not None:
        req.setdefault("action", getattr(mt5, "TRADE_ACTION_SLTP", 6))
    return place_order(req)


def close_position(
    position_id: int | str,
    volume: float | None = None,
) -> dict[str, Any]:
    """Close position via TRADE_ACTION_DEAL.

    Args:
        position_id: Ticket ID of position to close.
        volume: Optional volume to close.

    Returns:
        Position closing result dictionary.
    """
    pid = int(position_id)
    action = (
        getattr(mt5, "TRADE_ACTION_DEAL", 1)
        if (_MT5_AVAILABLE and mt5 is not None)
        else 1
    )
    req: dict[str, Any] = {"action": action, "position": pid}
    if volume is not None:
        req["volume"] = float(volume)
    return place_order(req)


def calculate_margin(request: dict[str, Any]) -> float:
    """Calculate required margin for an MT5 order.

    Args:
        request: Dictionary with action, symbol, volume, price.

    Returns:
        Required margin amount in account currency.

    Raises:
        RuntimeError: If calculation fails.
    """
    if not _MT5_AVAILABLE or mt5 is None:
        msg = "MetaTrader5 package is not available."
        raise RuntimeError(msg)

    action = request.get("action", getattr(mt5, "ORDER_TYPE_BUY", 0))
    symbol = str(request.get("symbol", "EURUSD")).upper()
    volume = float(request.get("volume", 1.0))
    price = float(request.get("price", 1.08500))

    margin = mt5.order_calc_margin(action, symbol, volume, price)
    if margin is None:
        err = mt5.last_error()
        msg = f"Failed to calculate margin in MetaTrader 5 for '{symbol}': [{err[0]}] {err[1]}"
        raise RuntimeError(msg)

    return float(margin)


def calculate_profit(request: dict[str, Any]) -> float:
    """Calculate projected profit for an MT5 trade.

    Args:
        request: Dictionary with action, symbol, volume, price_open, price_close.

    Returns:
        Projected profit in account currency.

    Raises:
        RuntimeError: If calculation fails.
    """
    if not _MT5_AVAILABLE or mt5 is None:
        msg = "MetaTrader5 package is not available."
        raise RuntimeError(msg)

    action = request.get("action", getattr(mt5, "ORDER_TYPE_BUY", 0))
    symbol = str(request.get("symbol", "EURUSD")).upper()
    volume = float(request.get("volume", 1.0))
    price_open = float(request.get("price_open", 1.08000))
    price_close = float(request.get("price_close", 1.08500))

    profit = mt5.order_calc_profit(action, symbol, volume, price_open, price_close)
    if profit is None:
        err = mt5.last_error()
        msg = f"Failed to calculate profit in MetaTrader 5 for '{symbol}': [{err[0]}] {err[1]}"
        raise RuntimeError(msg)

    return float(profit)
