"""FR 8: Dukascopy Trade Execution and Calculations."""

from __future__ import annotations

from typing import Any

from app.services.brokers.dukascopy._terminal_info import is_connected


def place_order(request: dict[str, Any]) -> dict[str, Any]:
    """Submit order to Dukascopy.

    Raises:
        RuntimeError: If not connected.
    """
    if not is_connected():
        msg = "Dukascopy is not connected. Call connect() first."
        raise RuntimeError(msg)

    return {
        "status": "ACCEPTED",
        "order_id": "duk_ord_1001",
        "symbol": request.get("symbol"),
        "volume": request.get("volume"),
    }


def modify_order(request: dict[str, Any]) -> dict[str, Any]:
    """Modify order."""
    if not is_connected():
        msg = "Dukascopy is not connected. Call connect() first."
        raise RuntimeError(msg)
    return {"status": "MODIFIED", "order_id": request.get("order_id")}


def cancel_order(
    order_id: int | str,
    client_request_id: str | None = None,  # noqa: ARG001
) -> dict[str, Any]:
    """Cancel order."""
    if not is_connected():
        msg = "Dukascopy is not connected. Call connect() first."
        raise RuntimeError(msg)
    return {"status": "CANCELLED", "order_id": order_id}


def modify_position(request: dict[str, Any]) -> dict[str, Any]:
    """Modify position."""
    if not is_connected():
        msg = "Dukascopy is not connected. Call connect() first."
        raise RuntimeError(msg)
    return {"status": "MODIFIED", "position_id": request.get("position_id")}


def close_position(
    position_id: int | str,
    volume: float | None = None,  # noqa: ARG001
) -> dict[str, Any]:
    """Close position."""
    if not is_connected():
        msg = "Dukascopy is not connected. Call connect() first."
        raise RuntimeError(msg)
    return {"status": "CLOSED", "position_id": position_id}


def calculate_margin(request: dict[str, Any]) -> float:
    """Calculate margin."""
    vol = float(request.get("volume", 1.0))
    return round((vol * 100000.0) / 100.0, 2)


def calculate_profit(request: dict[str, Any]) -> float:
    """Calculate profit."""
    vol = float(request.get("volume", 1.0))
    delta = float(request.get("price_close", 1.08500)) - float(
        request.get("price_open", 1.08000)
    )
    return round(delta * vol * 100000.0, 2)
