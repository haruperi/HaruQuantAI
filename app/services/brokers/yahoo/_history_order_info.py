"""FR 5: Yahoo Finance Historical Orders (Capability Unavailable)."""

from __future__ import annotations

from typing import Any


def list_order_history(
    symbol: str | None = None,
    start: Any = None,
    end: Any = None,
) -> list[dict[str, Any]]:
    """Retrieve historical orders.

    Raises:
        NotImplementedError: Because Yahoo Finance is a market data provider only.
    """
    msg = (
        "Broker capability 'orders:history' is unavailable for Yahoo Finance provider."
    )
    raise NotImplementedError(msg)


def get_history_order(order_id: int | str) -> dict[str, Any] | None:
    """Retrieve historical order.

    Raises:
        NotImplementedError: Because Yahoo Finance is a market data provider only.
    """
    msg = (
        "Broker capability 'orders:history' is unavailable for Yahoo Finance provider."
    )
    raise NotImplementedError(msg)
