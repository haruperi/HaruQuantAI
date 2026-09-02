"""FR 7: Dukascopy Open Positions."""

from __future__ import annotations

from typing import Any

from app.services.brokers.dukascopy._terminal_info import is_connected


def get_positions(symbol: str | None = None) -> list[dict[str, Any]]:  # noqa: ARG001
    """Retrieve open positions.

    Raises:
        RuntimeError: If not connected.
    """
    if not is_connected():
        msg = "Dukascopy is not connected. Call connect() first."
        raise RuntimeError(msg)
    return []


def get_position(position_id: int | str) -> dict[str, Any] | None:  # noqa: ARG001
    """Retrieve individual position."""
    if not is_connected():
        msg = "Dukascopy is not connected. Call connect() first."
        raise RuntimeError(msg)
    return None
