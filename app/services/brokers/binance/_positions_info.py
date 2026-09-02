"""FR 7: Binance Futures Positions."""

from __future__ import annotations

from typing import Any

from app.services.brokers.binance._terminal_info import is_connected


def get_positions(symbol: str | None = None) -> list[dict[str, Any]]:  # noqa: ARG001
    """Retrieve open futures positions.

    Raises:
        RuntimeError: If not connected.
    """
    if not is_connected():
        msg = "Binance is not connected. Call connect() first."
        raise RuntimeError(msg)
    return []


def get_position(position_id: int | str) -> dict[str, Any] | None:  # noqa: ARG001
    """Retrieve position by symbol/ID."""
    if not is_connected():
        msg = "Binance is not connected. Call connect() first."
        raise RuntimeError(msg)
    return None
