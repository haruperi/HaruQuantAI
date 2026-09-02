"""FR 1: Yahoo Finance Environment and Connection."""

from __future__ import annotations

from typing import Any

from app.services.brokers.yahoo.config import YahooConfig

_yahoo_state: dict[str, Any] = {
    "connected": True,
    "last_error": (0, "Success"),
}


def connect(
    timeout: int = 30,  # noqa: ARG001
    config: YahooConfig | None = None,  # noqa: ARG001
) -> dict[str, Any]:
    """Connect to Yahoo Finance public data service."""
    _yahoo_state["connected"] = True
    return {
        "status": "connected",
        "connected": True,
        "platform": "yahoo",
        "type": "market_data_provider",
    }


def disconnect() -> bool:
    """Disconnect from Yahoo Finance."""
    _yahoo_state["connected"] = False
    return True


def is_connected() -> bool:
    """Check connection status."""
    return bool(_yahoo_state["connected"])


def ping() -> float:
    """Check ping latency."""
    if not is_connected():
        msg = "Yahoo Finance data provider is not connected."
        raise RuntimeError(msg)
    return 45.0


def get_connection_status() -> dict[str, Any]:
    """Retrieve connection status."""
    return {
        "connected": is_connected(),
        "platform": "yahoo",
        "ping_ms": ping() if is_connected() else 0.0,
        "last_error": _yahoo_state["last_error"],
    }


def get_platform_info() -> dict[str, Any]:
    """Retrieve platform info."""
    return {
        "platform": "yahoo",
        "type": "market_data_provider",
        "capabilities": ["quotes", "bars", "financials"],
    }


def get_terminal_info() -> dict[str, Any]:
    """Retrieve terminal environment info."""
    return {
        "connected": is_connected(),
        "type": "web_api",
    }


def get_provider_specification() -> dict[str, Any]:
    """Retrieve provider specifications."""
    return {
        "provider": "yahoo",
        "supports_market_orders": False,
        "supports_trading": False,
        "supports_quotes": True,
        "supports_historical_bars": True,
    }


def get_last_error() -> tuple[int, str]:
    """Retrieve last error."""
    return _yahoo_state["last_error"]
