"""FR 1: Binance Terminal Environment and Connection."""

from __future__ import annotations

import json
import ssl
import time
import urllib.request
from typing import Any

from app.services.brokers.binance._persistence import get_binance_credentials
from app.services.brokers.binance.config import BinanceConfig

_binance_state: dict[str, Any] = {
    "connected": False,
    "api_key": None,
    "api_secret": None,
    "testnet": False,
    "last_error": (0, "Success"),
}


def connect(
    api_key: str | None = None,
    api_secret: str | None = None,
    testnet: bool = False,
    timeout: int = 30,  # noqa: ARG001
    config: BinanceConfig | None = None,
) -> dict[str, Any]:
    """Connect to Binance REST/WebSocket API."""
    db_creds = get_binance_credentials(config.database_path if config else None)

    final_key = api_key or (config.api_key if config else None) or db_creds["api_key"]
    final_secret = (
        api_secret or (config.api_secret if config else None) or db_creds["api_secret"]
    )
    final_testnet = testnet or (config.testnet if config else False)

    # Verify public network connectivity
    base_url = (
        "https://testnet.binance.vision" if final_testnet else "https://api.binance.com"
    )
    req = urllib.request.Request(  # noqa: S310
        f"{base_url}/api/v3/ping", headers={"User-Agent": "Mozilla/5.0"}
    )
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:  # noqa: S310
            if resp.status != 200:
                msg = f"Binance ping failed with HTTP status {resp.status}"
                raise RuntimeError(msg)  # noqa: TRY301
    except Exception as exc:
        _binance_state["connected"] = False
        _binance_state["last_error"] = (-1, str(exc))
        msg = f"Failed to connect to Binance API: {exc}"
        raise RuntimeError(msg) from exc

    _binance_state["connected"] = True
    _binance_state["api_key"] = final_key
    _binance_state["api_secret"] = final_secret
    _binance_state["testnet"] = final_testnet
    _binance_state["last_error"] = (0, "Success")

    return {
        "status": "connected",
        "connected": True,
        "testnet": final_testnet,
        "platform": "binance",
    }


def disconnect() -> bool:
    """Disconnect from Binance."""
    _binance_state["connected"] = False
    return True


def is_connected() -> bool:
    """Check if Binance is connected."""
    return bool(_binance_state["connected"])


def ping() -> float:
    """Retrieve real Binance REST latency in milliseconds.

    Raises:
        RuntimeError: If not connected or request fails.
    """
    if not is_connected():
        msg = "Binance connection is not active."
        raise RuntimeError(msg)

    base_url = (
        "https://testnet.binance.vision"
        if _binance_state["testnet"]
        else "https://api.binance.com"
    )
    req = urllib.request.Request(  # noqa: S310
        f"{base_url}/api/v3/ping", headers={"User-Agent": "Mozilla/5.0"}
    )
    ctx = ssl.create_default_context()
    start_t = time.perf_counter()
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:  # noqa: S310
            if resp.status == 200:
                return round((time.perf_counter() - start_t) * 1000.0, 2)
            msg = f"Ping failed with HTTP {resp.status}"
            raise RuntimeError(msg)  # noqa: TRY301
    except Exception as exc:
        msg = f"Binance ping failed: {exc}"
        raise RuntimeError(msg) from exc


def get_connection_status() -> dict[str, Any]:
    """Retrieve connection status metadata."""
    return {
        "connected": is_connected(),
        "testnet": _binance_state["testnet"],
        "ping_ms": ping() if is_connected() else 0.0,
        "last_error": _binance_state["last_error"],
    }


def get_platform_info() -> dict[str, Any]:
    """Retrieve Binance platform metadata."""
    return {
        "platform": "binance",
        "type": "crypto_exchange",
        "markets": ["SPOT", "USDT_FUTURES", "COIN_FUTURES"],
    }


def get_terminal_info() -> dict[str, Any]:
    """Retrieve environment info and real server time.

    Raises:
        RuntimeError: If not connected.
    """
    if not is_connected():
        msg = "Binance is not connected."
        raise RuntimeError(msg)

    base_url = (
        "https://testnet.binance.vision"
        if _binance_state["testnet"]
        else "https://api.binance.com"
    )
    req = urllib.request.Request(  # noqa: S310
        f"{base_url}/api/v3/time", headers={"User-Agent": "Mozilla/5.0"}
    )
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:  # noqa: S310
            data = json.loads(resp.read().decode())
            return {
                "connected": True,
                "testnet": _binance_state["testnet"],
                "serverTime": data.get("serverTime"),
                "rate_limits": {"REQUEST_WEIGHT": 1200, "ORDERS": 50},
            }
    except Exception as exc:
        msg = f"Failed to retrieve Binance server time: {exc}"
        raise RuntimeError(msg) from exc


def get_provider_specification() -> dict[str, Any]:
    """Retrieve provider specifications."""
    return {
        "provider": "binance",
        "supports_spot": True,
        "supports_futures": True,
        "supports_oco": True,
        "supports_market_orders": True,
        "supports_limit_orders": True,
    }


def get_last_error() -> tuple[int, str]:
    """Retrieve last error tuple."""
    return _binance_state["last_error"]
