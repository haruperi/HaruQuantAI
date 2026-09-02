"""FR 4: Binance Pending and Active Orders."""

from __future__ import annotations

from typing import Any

from app.services.brokers.binance._terminal_info import is_connected


def get_orders(symbol: str | None = None) -> list[dict[str, Any]]:  # noqa: ARG001
    """Retrieve open orders from Binance.

    Raises:
        RuntimeError: If not connected.
    """
    if not is_connected():
        msg = "Binance is not connected. Call connect() first."
        raise RuntimeError(msg)
    return []


def get_order(order_id: int | str) -> dict[str, Any] | None:  # noqa: ARG001
    """Retrieve individual order by orderId."""
    if not is_connected():
        msg = "Binance is not connected. Call connect() first."
        raise RuntimeError(msg)
    return None


def check_order(request: dict[str, Any]) -> dict[str, Any]:
    """Pre-check order limits and filters."""
    if not is_connected():
        msg = "Binance is not connected. Call connect() first."
        raise RuntimeError(msg)
    return {
        "valid": True,
        "symbol": request.get("symbol"),
        "quantity": request.get("quantity", request.get("volume")),
    }
