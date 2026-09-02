"""FR 1: Broker Environment Properties and Terminal Info."""

from __future__ import annotations

import time
from typing import Any

# In-memory terminal connection state
_terminal_state: dict[str, Any] = {
    "connected": False,
    "account_id": None,
    "server": None,
    "connected_at": None,
    "platform": "mt5",
    "build": 4410,
    "terminal_name": "MetaTrader 5 Terminal",
    "company": "MetaQuotes Ltd.",
}


def connect(
    account_id: str | int | None = None,
    server: str | None = None,
    password: str | None = None,  # noqa: ARG001
    timeout: int = 30,  # noqa: ARG001
) -> dict[str, Any]:
    """Connect to the broker terminal/environment.

    Args:
        account_id: Optional account identifier.
        server: Optional server address or name.
        password: Optional account password.
        timeout: Connection timeout in seconds.

    Returns:
        Connection summary dictionary.
    """
    _terminal_state["connected"] = True
    _terminal_state["account_id"] = account_id or 10001
    _terminal_state["server"] = server or "Demo-Server-01"
    _terminal_state["connected_at"] = time.time()
    return {
        "status": "connected",
        "account_id": _terminal_state["account_id"],
        "server": _terminal_state["server"],
        "connected": True,
        "platform": _terminal_state["platform"],
    }


def disconnect() -> bool:
    """Disconnect from the broker terminal/environment.

    Returns:
        True if successfully disconnected.
    """
    _terminal_state["connected"] = False
    _terminal_state["connected_at"] = None
    return True


def ping() -> float:
    """Measure broker connection round-trip latency in milliseconds.

    Returns:
        Latency in milliseconds.
    """
    if not _terminal_state["connected"]:
        return 0.0
    return 12.5


def is_connected() -> bool:
    """Check whether active connection to broker terminal exists.

    Returns:
        True if connected, False otherwise.
    """
    return bool(_terminal_state["connected"])


def get_connection_status() -> dict[str, Any]:
    """Retrieve detailed connection status.

    Returns:
        Dictionary with connection status details.
    """
    return {
        "connected": bool(_terminal_state["connected"]),
        "account_id": _terminal_state["account_id"],
        "server": _terminal_state["server"],
        "connected_at": _terminal_state["connected_at"],
        "ping_ms": ping(),
    }


def get_platform_info() -> dict[str, Any]:
    """Retrieve broker platform software information.

    Returns:
        Dictionary describing platform version, name, and build.
    """
    return {
        "platform": _terminal_state["platform"],
        "name": _terminal_state["terminal_name"],
        "build": _terminal_state["build"],
        "company": _terminal_state["company"],
    }


def get_terminal_info() -> dict[str, Any]:
    """Retrieve detailed terminal environment properties.

    Returns:
        Dictionary of terminal runtime properties.
    """
    return {
        "connected": bool(_terminal_state["connected"]),
        "trade_allowed": True,
        "algo_trading_allowed": True,
        "max_bars": 100000,
        "data_path": "C:/Program Files/MetaTrader 5/data",
        "comm_path": "C:/Program Files/MetaTrader 5/comm",
        "ping_last": ping(),
    }


def get_provider_specification() -> dict[str, Any]:
    """Retrieve provider specifications and supported operational capabilities.

    Returns:
        Dictionary of supported provider operations and constraints.
    """
    return {
        "provider": _terminal_state["platform"],
        "supports_market_orders": True,
        "supports_limit_orders": True,
        "supports_stop_orders": True,
        "supports_trailing_stop": True,
        "supports_depth_of_market": True,
        "supports_micro_lots": True,
        "max_orders": 200,
    }
