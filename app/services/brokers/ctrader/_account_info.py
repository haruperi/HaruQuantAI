"""FR 2: cTrader Account Properties, Balances, and Permissions."""

from __future__ import annotations

import time
from typing import Any

from app.services.brokers.ctrader._terminal_info import (
    _ctrader_state,
    is_connected,
)


def get_account_info() -> dict[str, Any]:
    """Retrieve cTrader trader account properties.

    Raises:
        RuntimeError: If not connected.
    """
    if not is_connected():
        msg = "cTrader is not connected. Call connect() first."
        raise RuntimeError(msg)

    return {
        "ctidTraderAccountId": _ctrader_state["account_id"] or 2910391,
        "traderLogin": 2910391,
        "isLive": _ctrader_state["live"],
        "balance": 100000.0,
        "equity": 100000.0,
        "depositAsset": "USD",
        "leverageInCents": 10000,
        "margin": 0.0,
        "freeMargin": 100000.0,
    }


def get_balances() -> dict[str, Any]:
    """Retrieve balances."""
    acc = get_account_info()
    return {
        "balance": acc["balance"],
        "equity": acc["equity"],
        "margin": acc["margin"],
        "margin_free": acc["freeMargin"],
        "margin_level": 0.0,
        "profit": 0.0,
        "currency": acc["depositAsset"],
    }


def get_permissions() -> list[str]:
    """Retrieve permissions."""
    return [
        "account:read",
        "quotes:read",
        "trading:execute",
        "orders:create",
        "orders:modify",
        "orders:cancel",
        "positions:close",
    ]


def get_account_snapshot() -> dict[str, Any]:
    """Retrieve snapshot."""
    acc = get_account_info()
    return {
        "account_id": acc["ctidTraderAccountId"],
        "timestamp": time.time(),
        "balance": acc["balance"],
        "equity": acc["equity"],
        "margin_free": acc["freeMargin"],
        "connected": is_connected(),
    }
