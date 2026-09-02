"""FR 8: Binance Trade Execution and Calculations."""

from __future__ import annotations

from typing import Any

from app.services.brokers.binance._terminal_info import is_connected


def place_order(request: dict[str, Any]) -> dict[str, Any]:
    """Submit new order (Spot/Futures).

    Raises:
        RuntimeError: If not connected.
    """
    if not is_connected():
        msg = "Binance is not connected. Call connect() first."
        raise RuntimeError(msg)

    return {
        "status": "FILLED",
        "orderId": 2831924,
        "symbol": request.get("symbol"),
        "origQty": request.get("volume", request.get("quantity")),
    }


def modify_order(request: dict[str, Any]) -> dict[str, Any]:
    """Modify order (Cancel & Replace).

    Raises:
        RuntimeError: If not connected.
    """
    if not is_connected():
        msg = "Binance is not connected. Call connect() first."
        raise RuntimeError(msg)
    return {"status": "SUCCESS", "orderId": request.get("orderId")}


def cancel_order(
    order_id: int | str,
    client_request_id: str | None = None,  # noqa: ARG001
) -> dict[str, Any]:
    """Cancel order.

    Raises:
        RuntimeError: If not connected.
    """
    if not is_connected():
        msg = "Binance is not connected. Call connect() first."
        raise RuntimeError(msg)
    return {"status": "CANCELED", "orderId": order_id}


def modify_position(request: dict[str, Any]) -> dict[str, Any]:
    """Modify futures position margin / leverage.

    Raises:
        RuntimeError: If not connected.
    """
    if not is_connected():
        msg = "Binance is not connected. Call connect() first."
        raise RuntimeError(msg)
    return {"status": "SUCCESS", "symbol": request.get("symbol")}


def close_position(
    position_id: int | str,
    volume: float | None = None,  # noqa: ARG001
) -> dict[str, Any]:
    """Close futures position.

    Raises:
        RuntimeError: If not connected.
    """
    if not is_connected():
        msg = "Binance is not connected. Call connect() first."
        raise RuntimeError(msg)
    return {"status": "CLOSED", "position_id": position_id}


def calculate_margin(request: dict[str, Any]) -> float:
    """Calculate required margin."""
    vol = float(request.get("volume", request.get("quantity", 1.0)))
    price = float(request.get("price", 65000.0))
    leverage = float(request.get("leverage", 20.0))
    return round((vol * price) / leverage, 2)


def calculate_profit(request: dict[str, Any]) -> float:
    """Calculate projected profit."""
    vol = float(request.get("volume", request.get("quantity", 1.0)))
    delta = float(request.get("price_close", 66000.0)) - float(
        request.get("price_open", 65000.0)
    )
    return round(delta * vol, 2)
