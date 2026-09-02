"""FR 5: Dukascopy Historical Orders."""

from __future__ import annotations

from typing import Any

from app.services.brokers.dukascopy._terminal_info import is_connected


def list_order_history(
    symbol: str | None = None,  # noqa: ARG001
    start: Any = None,  # noqa: ARG001
    end: Any = None,  # noqa: ARG001
) -> list[dict[str, Any]]:
    """Retrieve historical orders.

    Raises:
        RuntimeError: If not connected.
    """
    if not is_connected():
        msg = "Dukascopy is not connected. Call connect() first."
        raise RuntimeError(msg)
    return []


def get_history_order(order_id: int | str) -> dict[str, Any] | None:  # noqa: ARG001
    """Retrieve single historical order."""
    if not is_connected():
        msg = "Dukascopy is not connected. Call connect() first."
        raise RuntimeError(msg)
    return None
