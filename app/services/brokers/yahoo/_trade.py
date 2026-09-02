"""FR 8: Yahoo Finance Trade Execution (Capability Unavailable)."""

from __future__ import annotations

from typing import Any


def place_order(request: dict[str, Any]) -> dict[str, Any]:
    """Place order.

    Raises:
        NotImplementedError: Because Yahoo Finance is a market data provider only.
    """
    msg = "Broker capability 'orders:place' is unavailable for Yahoo Finance provider."
    raise NotImplementedError(msg)


def modify_order(request: dict[str, Any]) -> dict[str, Any]:
    """Modify order.

    Raises:
        NotImplementedError: Because Yahoo Finance is a market data provider only.
    """
    msg = "Broker capability 'orders:modify' is unavailable for Yahoo Finance provider."
    raise NotImplementedError(msg)


def cancel_order(
    order_id: int | str,
    client_request_id: str | None = None,
) -> dict[str, Any]:
    """Cancel order.

    Raises:
        NotImplementedError: Because Yahoo Finance is a market data provider only.
    """
    msg = "Broker capability 'orders:cancel' is unavailable for Yahoo Finance provider."
    raise NotImplementedError(msg)


def modify_position(request: dict[str, Any]) -> dict[str, Any]:
    """Modify position.

    Raises:
        NotImplementedError: Because Yahoo Finance is a market data provider only.
    """
    msg = "Broker capability 'positions:modify' is unavailable for Yahoo Finance provider."
    raise NotImplementedError(msg)


def close_position(
    position_id: int | str,
    volume: float | None = None,
) -> dict[str, Any]:
    """Close position.

    Raises:
        NotImplementedError: Because Yahoo Finance is a market data provider only.
    """
    msg = (
        "Broker capability 'positions:close' is unavailable for Yahoo Finance provider."
    )
    raise NotImplementedError(msg)


def calculate_margin(request: dict[str, Any]) -> float:
    """Calculate margin.

    Raises:
        NotImplementedError: Because Yahoo Finance is a market data provider only.
    """
    msg = "Broker capability 'margin:calculate' is unavailable for Yahoo Finance provider."
    raise NotImplementedError(msg)


def calculate_profit(request: dict[str, Any]) -> float:
    """Calculate profit.

    Raises:
        NotImplementedError: Because Yahoo Finance is a market data provider only.
    """
    msg = "Broker capability 'profit:calculate' is unavailable for Yahoo Finance provider."
    raise NotImplementedError(msg)
