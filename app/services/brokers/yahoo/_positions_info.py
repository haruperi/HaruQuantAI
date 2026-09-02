"""FR 7: Yahoo Finance Open Positions (Capability Unavailable)."""

from __future__ import annotations

from typing import Any


def get_positions(symbol: str | None = None) -> list[dict[str, Any]]:
    """Retrieve open positions.

    Raises:
        NotImplementedError: Because Yahoo Finance is a market data provider only.
    """
    msg = "Broker capability 'positions:get' is unavailable for Yahoo Finance provider."
    raise NotImplementedError(msg)


def get_position(position_id: int | str) -> dict[str, Any] | None:
    """Retrieve position.

    Raises:
        NotImplementedError: Because Yahoo Finance is a market data provider only.
    """
    msg = "Broker capability 'positions:get' is unavailable for Yahoo Finance provider."
    raise NotImplementedError(msg)
