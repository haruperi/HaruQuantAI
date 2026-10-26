"""Read-only MT5 bridge setup shared by Data Manager and headless ingestion."""

from __future__ import annotations

from typing import Any

from app.workspace.brokers.base import get_broker


async def bridge_action(action: str, application: Any) -> dict[str, Any]:
    """Start the local EA listener without arming trading or submitting orders."""
    client = get_broker("metatrader")
    if action == "connect" and not client.bridge.listening:
        await client.start()
        application.state.data_mt5 = client
    result: dict[str, Any] = {
        "connected": client.bridge.connected,
        "listening": client.bridge.listening,
        "host": client.bridge.host,
        "port": client.bridge.port,
    }
    if action == "connect":
        result["auth_token"] = client.bridge.auth_token
    if client.bridge.connected:
        payload = await client.symbol.SymbolsGet()
        result["symbols"] = payload
    return result
