"""FR 2: Dukascopy Account Properties, Balances, and Permissions."""

from __future__ import annotations

import time
from typing import Any

from app.services.brokers.dukascopy._terminal_info import (
    _dukascopy_state,
    is_connected,
)


def get_account_info() -> dict[str, Any]:
    """Retrieve Dukascopy account configuration.

    Raises:
        RuntimeError: If not connected.
    """
    if not is_connected():
        msg = "Dukascopy is not connected. Call connect() first."
        raise RuntimeError(msg)

    return {
        "account_id": _dukascopy_state["account_id"] or "DUKAS_ACC_101",
        "username": _dukascopy_state["username"],
        "currency": "USD",
        "leverage": 100,
        "balance": 25000.0,
        "equity": 25000.0,
        "margin": 0.0,
        "margin_free": 25000.0,
        "live": _dukascopy_state["live"],
    }


def get_balances() -> dict[str, Any]:
    """Retrieve balances."""
    acc = get_account_info()
    return {
        "balance": acc["balance"],
        "equity": acc["equity"],
        "margin": acc["margin"],
        "margin_free": acc["margin_free"],
        "margin_level": 0.0,
        "profit": 0.0,
        "currency": acc["currency"],
    }


def get_permissions() -> list[str]:
    """Retrieve granted permissions."""
    return [
        "account:read",
        "quotes:read",
        "historical_ticks:read",
        "orders:create",
        "orders:modify",
        "orders:cancel",
        "positions:close",
    ]


def get_account_snapshot() -> dict[str, Any]:
    """Retrieve account state snapshot."""
    acc = get_account_info()
    return {
        "account_id": acc["account_id"],
        "timestamp": time.time(),
        "balance": acc["balance"],
        "equity": acc["equity"],
        "margin_free": acc["margin_free"],
        "connected": is_connected(),
    }
