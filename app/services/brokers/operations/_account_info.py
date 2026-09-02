"""FR 2: Account Properties, Balances, Permissions, and Equity Snapshots."""

from __future__ import annotations

import time
from typing import Any

from app.services.brokers.operations._terminal_info import is_connected

_account_data: dict[str, Any] = {
    "account_id": 10001,
    "name": "Demo Account",
    "currency": "USD",
    "leverage": 100,
    "balance": 10000.0,
    "equity": 10250.0,
    "margin": 200.0,
    "margin_free": 10050.0,
    "margin_level": 5125.0,
    "profit": 250.0,
    "trade_mode": "demo",
    "limit_orders": 200,
    "permissions": [
        "account:read",
        "quotes:read",
        "orders:create",
        "orders:cancel",
        "orders:modify",
        "positions:close",
    ],
}


def get_account_info() -> dict[str, Any]:
    """Retrieve full account configuration and metadata.

    Returns:
        Dictionary containing account details.
    """
    return {
        "account_id": _account_data["account_id"],
        "name": _account_data["name"],
        "currency": _account_data["currency"],
        "leverage": _account_data["leverage"],
        "trade_mode": _account_data["trade_mode"],
        "connected": is_connected(),
    }


def get_balances() -> dict[str, Any]:
    """Retrieve financial balances, margin, and equity.

    Returns:
        Dictionary containing balance, equity, margin, free margin, and profit.
    """
    return {
        "balance": _account_data["balance"],
        "equity": _account_data["equity"],
        "margin": _account_data["margin"],
        "margin_free": _account_data["margin_free"],
        "margin_level": _account_data["margin_level"],
        "profit": _account_data["profit"],
        "currency": _account_data["currency"],
    }


def get_permissions() -> list[str]:
    """Retrieve granted operational permissions on the active broker account.

    Returns:
        List of permission key strings.
    """
    return list(_account_data["permissions"])


def get_account_snapshot() -> dict[str, Any]:
    """Retrieve an instantaneous snapshot of account equity, balances, and timestamp.

    Returns:
        Dictionary containing account state snapshot.
    """
    return {
        "account_id": _account_data["account_id"],
        "timestamp": time.time(),
        "balance": _account_data["balance"],
        "equity": _account_data["equity"],
        "margin_free": _account_data["margin_free"],
        "unrealized_pnl": _account_data["profit"],
        "connected": is_connected(),
    }
