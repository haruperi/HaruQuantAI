"""FR 2: MetaTrader 5 Account Properties, Balances, and Permissions."""

from __future__ import annotations

import time
from typing import Any

try:
    import MetaTrader5 as mt5  # noqa: N813

    _MT5_AVAILABLE = True
except ImportError:
    mt5 = None  # type: ignore[assignment]
    _MT5_AVAILABLE = False

from app.services.brokers.metatrader._terminal_info import is_connected


def get_account_info() -> dict[str, Any]:
    """Retrieve live MT5 account properties and configuration.

    Returns:
        Dictionary containing real account information from MT5.

    Raises:
        RuntimeError: If MetaTrader 5 is not connected or account query fails.
    """
    if not _MT5_AVAILABLE or mt5 is None:
        msg = "MetaTrader5 package is not available."
        raise RuntimeError(msg)

    acc = mt5.account_info()
    if acc is None:
        err = mt5.last_error()
        msg = f"Failed to retrieve MetaTrader 5 account info: [{err[0]}] {err[1]}"
        raise RuntimeError(msg)

    return acc._asdict()


def get_balances() -> dict[str, Any]:
    """Retrieve financial balances, margin, and equity.

    Returns:
        Dictionary containing account balance metrics.

    Raises:
        RuntimeError: If account query fails.
    """
    acc = get_account_info()
    return {
        "balance": float(acc.get("balance", 0.0)),
        "equity": float(acc.get("equity", 0.0)),
        "margin": float(acc.get("margin", 0.0)),
        "margin_free": float(acc.get("margin_free", 0.0)),
        "margin_level": float(acc.get("margin_level", 0.0)),
        "profit": float(acc.get("profit", 0.0)),
        "currency": str(acc.get("currency", "USD")),
    }


def get_permissions() -> list[str]:
    """Retrieve active trading permissions.

    Returns:
        List of permission strings based on actual MT5 account properties.

    Raises:
        RuntimeError: If account query fails.
    """
    acc = get_account_info()
    perms = ["account:read", "quotes:read"]
    if acc.get("trade_allowed"):
        perms.append("orders:create")
        perms.append("orders:modify")
        perms.append("orders:cancel")
        perms.append("positions:close")
    if acc.get("trade_expert"):
        perms.append("algo_trading:allowed")
    return perms


def get_account_snapshot() -> dict[str, Any]:
    """Retrieve instantaneous equity and margin snapshot.

    Returns:
        Dictionary containing snapshot state.

    Raises:
        RuntimeError: If account query fails.
    """
    acc = get_account_info()
    return {
        "login": acc.get("login"),
        "timestamp": time.time(),
        "balance": acc.get("balance"),
        "equity": acc.get("equity"),
        "margin_free": acc.get("margin_free"),
        "connected": is_connected(),
    }
