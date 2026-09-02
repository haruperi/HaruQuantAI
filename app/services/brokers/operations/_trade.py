"""FR 8: Trade Execution, Order/Position Modifications, and Margin/Profit Calculations."""

from __future__ import annotations

import time
import uuid
from typing import Any

from app.services.brokers.operations._order_info import _active_orders
from app.services.brokers.operations._positions_info import _open_positions


def place_order(request: dict[str, Any]) -> dict[str, Any]:
    """Submit a new trade order to the broker.

    Args:
        request: Order placement dictionary with symbol, volume, type, price, sl, tp, comment.

    Returns:
        Execution result dictionary with order_id, status, and executed price.
    """
    symbol = request.get("symbol", "EURUSD").upper()
    volume = float(request.get("volume", 0.1))
    order_type = str(request.get("type", "BUY")).upper()
    price = float(request.get("price", 1.08500))
    sl = float(request.get("sl", 0.0))
    tp = float(request.get("tp", 0.0))
    comment = str(request.get("comment", "API Execution"))

    order_id = int(str(uuid.uuid4().int)[:6])

    if "LIMIT" in order_type or "STOP" in order_type:
        # Place as pending order
        _active_orders[order_id] = {
            "order_id": order_id,
            "symbol": symbol,
            "type": order_type,
            "volume": volume,
            "price_open": price,
            "sl": sl,
            "tp": tp,
            "state": "PLACED",
            "time_setup": time.time(),
            "comment": comment,
        }
        return {
            "retcode": 0,
            "order_id": order_id,
            "status": "PLACED",
            "symbol": symbol,
            "volume": volume,
            "price": price,
            "comment": comment,
        }

    # Market order immediately opens a position
    pos_id = int(str(uuid.uuid4().int)[:6])
    _open_positions[pos_id] = {
        "position_id": pos_id,
        "symbol": symbol,
        "type": "POSITION_TYPE_BUY" if "BUY" in order_type else "POSITION_TYPE_SELL",
        "volume": volume,
        "price_open": price,
        "price_current": price,
        "sl": sl,
        "tp": tp,
        "profit": 0.0,
        "swap": 0.0,
        "time": time.time(),
        "comment": comment,
    }
    return {
        "retcode": 0,
        "order_id": order_id,
        "position_id": pos_id,
        "status": "FILLED",
        "symbol": symbol,
        "volume": volume,
        "price": price,
        "comment": comment,
    }


def modify_order(request: dict[str, Any]) -> dict[str, Any]:
    """Modify parameters of an existing pending order (price, SL, TP).

    Args:
        request: Order modification dictionary with order_id, price, sl, tp.

    Returns:
        Modification result dictionary.

    Raises:
        ValueError: If order is not found.
    """
    order_id = int(request["order_id"])
    if order_id not in _active_orders:
        msg = f"Order {order_id} not found."
        raise ValueError(msg)

    order = _active_orders[order_id]
    if "price" in request and request["price"] is not None:
        order["price_open"] = float(request["price"])
    if "sl" in request and request["sl"] is not None:
        order["sl"] = float(request["sl"])
    if "tp" in request and request["tp"] is not None:
        order["tp"] = float(request["tp"])

    return {
        "retcode": 0,
        "order_id": order_id,
        "status": "MODIFIED",
        "price": order["price_open"],
        "sl": order["sl"],
        "tp": order["tp"],
    }


def cancel_order(
    order_id: int | str,
    client_request_id: str | None = None,  # noqa: ARG001
) -> dict[str, Any]:
    """Cancel an active pending order.

    Args:
        order_id: Order identifier to cancel.
        client_request_id: Optional client tracking ID.

    Returns:
        Cancellation confirmation dictionary.

    Raises:
        ValueError: If order is not found.
    """
    oid = int(order_id)
    if oid not in _active_orders:
        msg = f"Order {order_id} not found."
        raise ValueError(msg)

    del _active_orders[oid]
    return {"retcode": 0, "order_id": oid, "status": "CANCELLED"}


def modify_position(request: dict[str, Any]) -> dict[str, Any]:
    """Modify Stop Loss and Take Profit levels for an open position.

    Args:
        request: Position modification dictionary with position_id, sl, tp.

    Returns:
        Modification result dictionary.

    Raises:
        ValueError: If position is not found.
    """
    position_id = int(request["position_id"])
    if position_id not in _open_positions:
        msg = f"Position {position_id} not found."
        raise ValueError(msg)

    pos = _open_positions[position_id]
    if "sl" in request and request["sl"] is not None:
        pos["sl"] = float(request["sl"])
    if "tp" in request and request["tp"] is not None:
        pos["tp"] = float(request["tp"])

    return {
        "retcode": 0,
        "position_id": position_id,
        "status": "MODIFIED",
        "sl": pos["sl"],
        "tp": pos["tp"],
    }


def close_position(
    position_id: int | str,
    volume: float | None = None,
) -> dict[str, Any]:
    """Close an open position fully or partially.

    Args:
        position_id: Position identifier.
        volume: Optional volume to close (defaults to full position volume).

    Returns:
        Closing result dictionary.

    Raises:
        ValueError: If position is not found or volume is invalid.
    """
    pid = int(position_id)
    if pid not in _open_positions:
        msg = f"Position {position_id} not found."
        raise ValueError(msg)

    pos = _open_positions[pid]
    current_vol = float(pos["volume"])
    close_vol = float(volume) if volume is not None else current_vol

    if close_vol <= 0 or close_vol > current_vol:
        msg = f"Invalid close volume {close_vol} for position {pid} (current: {current_vol})."
        raise ValueError(msg)

    if close_vol >= current_vol:
        del _open_positions[pid]
        return {
            "retcode": 0,
            "position_id": pid,
            "status": "CLOSED",
            "volume_closed": close_vol,
            "profit": pos["profit"],
        }

    pos["volume"] = round(current_vol - close_vol, 2)
    return {
        "retcode": 0,
        "position_id": pid,
        "status": "PARTIALLY_CLOSED",
        "volume_closed": close_vol,
        "remaining_volume": pos["volume"],
    }


def calculate_margin(request: dict[str, Any]) -> float:
    """Calculate margin required for an order.

    Args:
        request: Dictionary with symbol, volume, leverage.

    Returns:
        Required margin amount in account currency.
    """
    volume = float(request.get("volume", 1.0))
    leverage = float(request.get("leverage", 100.0))
    contract_size = 100000.0
    return round((volume * contract_size) / leverage, 2)


def calculate_profit(request: dict[str, Any]) -> float:
    """Calculate projected profit/loss for a trade.

    Args:
        request: Dictionary with volume, open_price, close_price, order_type.

    Returns:
        Projected profit/loss in account currency.
    """
    volume = float(request.get("volume", 1.0))
    open_price = float(request.get("open_price", 1.08000))
    close_price = float(request.get("close_price", 1.08500))
    order_type = str(request.get("order_type", "BUY")).upper()
    contract_size = 100000.0

    delta = (
        (close_price - open_price)
        if "BUY" in order_type
        else (open_price - close_price)
    )
    return round(delta * volume * contract_size, 2)
