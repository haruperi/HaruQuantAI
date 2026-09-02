"""FR 2: MetaTrader 5 Account Properties, Balances, and Permissions."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from app.services.brokers.metatrader._terminal_info import is_connected

if TYPE_CHECKING:
    from app.services.brokers.metatrader.client import MetaTraderClient


def _resolve_client(client: MetaTraderClient | Any | None = None) -> Any:
    """Resolve the provided client instance or fall back to the active default."""
    if client is not None:
        return client
    from app.services.brokers.metatrader.client import get_default_client

    return get_default_client()


def get_account_info(
    client: MetaTraderClient | Any | None = None,
) -> dict[str, Any]:
    """Retrieve live MT5 account properties and configuration.

    Args:
        client: Optional MetaTraderClient instance.

    Returns:
        Dictionary containing real account information from MT5.

    Raises:
        RuntimeError: If MetaTrader 5 is not connected or account query fails.
    """
    client_inst = _resolve_client(client)
    mt5 = getattr(client_inst, "mt5", client_inst)
    if mt5 is None or not getattr(client_inst, "is_available", lambda: True)():
        msg = "MetaTrader5 package is not available."
        raise RuntimeError(msg)

    acc = mt5.account_info()
    if acc is None:
        err = (
            mt5.last_error()
            if hasattr(mt5, "last_error")
            else (-1, "Account query failed")
        )
        msg = f"Failed to retrieve MetaTrader 5 account info: [{err[0]}] {err[1]}"
        raise RuntimeError(msg)

    return acc._asdict()


def get_balances(
    client: MetaTraderClient | Any | None = None,
) -> dict[str, Any]:
    """Retrieve financial balances, margin, and equity.

    Args:
        client: Optional MetaTraderClient instance.

    Returns:
        Dictionary containing account balance metrics.

    Raises:
        RuntimeError: If account query fails.
    """
    acc = get_account_info(client=client)
    return {
        "balance": float(acc.get("balance", 0.0)),
        "equity": float(acc.get("equity", 0.0)),
        "margin": float(acc.get("margin", 0.0)),
        "margin_free": float(acc.get("margin_free", 0.0)),
        "margin_level": float(acc.get("margin_level", 0.0)),
        "profit": float(acc.get("profit", 0.0)),
        "currency": str(acc.get("currency", "USD")),
    }


def get_permissions(
    client: MetaTraderClient | Any | None = None,
) -> list[str]:
    """Retrieve trading permissions and account capability flags.

    Args:
        client: Optional MetaTraderClient instance.

    Returns:
        List of permission string identifiers.
    """
    try:
        acc = get_account_info(client=client)
        perms = ["account:read", "quotes:read"]
        if acc.get("trade_allowed", False):
            perms.append("orders:create")
            perms.append("orders:cancel")
            perms.append("positions:modify")
            perms.append("positions:close")
        if acc.get("trade_expert", False):
            perms.append("algo_trading:allowed")
        return perms
    except Exception:
        return ["account:read", "quotes:read"]


def get_account_snapshot(
    client: MetaTraderClient | Any | None = None,
) -> dict[str, Any]:
    """Retrieve complete account status snapshot.

    Args:
        client: Optional MetaTraderClient instance.

    Returns:
        Consolidated snapshot dictionary.
    """
    client_inst = _resolve_client(client)
    acc = get_account_info(client=client_inst)
    return {
        "login": acc.get("login"),
        "name": acc.get("name"),
        "server": acc.get("server"),
        "currency": acc.get("currency"),
        "balance": acc.get("balance"),
        "equity": acc.get("equity"),
        "margin": acc.get("margin"),
        "margin_free": acc.get("margin_free"),
        "margin_level": acc.get("margin_level"),
        "profit": acc.get("profit"),
        "connected": is_connected(client=client_inst),
        "timestamp": time.time(),
    }
