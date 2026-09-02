"""FR 4: Yahoo Finance Orders (Capability Unavailable)."""

from __future__ import annotations

from typing import Any


def get_orders(symbol: str | None = None) -> list[dict[str, Any]]:
    """Retrieve orders.

    Raises:
        NotImplementedError: Because Yahoo Finance is a market data provider only.
    """
    msg = "Broker capability 'orders:get' is unavailable for Yahoo Finance provider."
    raise NotImplementedError(msg)


def get_order(order_id: int | str) -> dict[str, Any] | None:
    """Retrieve order.

    Raises:
        NotImplementedError: Because Yahoo Finance is a market data provider only.
    """
    msg = "Broker capability 'orders:get' is unavailable for Yahoo Finance provider."
    raise NotImplementedError(msg)


def check_order(request: dict[str, Any]) -> dict[str, Any]:
    """Check order.

    Raises:
        NotImplementedError: Because Yahoo Finance is a market data provider only.
    """
    msg = "Broker capability 'orders:check' is unavailable for Yahoo Finance provider."
    raise NotImplementedError(msg)
