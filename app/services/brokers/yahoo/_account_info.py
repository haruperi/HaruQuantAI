"""FR 2: Yahoo Finance Account Properties (Capability Unavailable)."""

from __future__ import annotations

from typing import Any


def get_account_info() -> dict[str, Any]:
    """Retrieve account properties.

    Raises:
        NotImplementedError: Because Yahoo Finance is a market data provider only.
    """
    msg = "Broker capability 'account:read' is unavailable for Yahoo Finance provider."
    raise NotImplementedError(msg)


def get_balances() -> dict[str, Any]:
    """Retrieve balances.

    Raises:
        NotImplementedError: Because Yahoo Finance is a market data provider only.
    """
    msg = "Broker capability 'account:balances' is unavailable for Yahoo Finance provider."
    raise NotImplementedError(msg)


def get_permissions() -> list[str]:
    """Retrieve permissions."""
    return ["quotes:read", "historical_bars:read"]


def get_account_snapshot() -> dict[str, Any]:
    """Retrieve account snapshot.

    Raises:
        NotImplementedError: Because Yahoo Finance is a market data provider only.
    """
    msg = "Broker capability 'account:snapshot' is unavailable for Yahoo Finance provider."
    raise NotImplementedError(msg)
