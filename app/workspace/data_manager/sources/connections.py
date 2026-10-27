"""Read-only provider access checks for the existing host connection service."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from http import HTTPStatus
from typing import Any

import httpx

from ._base import _fetch_frame
from ._helpers import PROVIDERS, capabilities, make_client, resolve_result


async def test_provider_access(metadata: dict[str, Any]) -> dict[str, Any]:
    """Separate endpoint authentication from an actual provider-history read."""
    provider = metadata["provider"]
    credentials = metadata.get("credentials") or {}
    auth = (
        (credentials["username"], credentials["password"])
        if credentials.get("username") and credentials.get("password")
        else None
    )
    headers = (
        {"Authorization": f"Bearer {credentials['token']}"}
        if credentials.get("token")
        else {}
    )
    if provider != "mt5":
        async with httpx.AsyncClient(timeout=4, follow_redirects=False) as http:
            response = await http.get(metadata["endpoint"], auth=auth, headers=headers)
        if response.status_code == HTTPStatus.UNAUTHORIZED:
            return {
                "authenticated": False,
                "authentication": "invalid_credentials",
                "entitlement": "unknown",
                "status": "invalid_credentials",
            }
        if response.status_code == HTTPStatus.FORBIDDEN:
            return {
                "authenticated": None,
                "authentication": "unknown",
                "entitlement": "denied",
                "status": "access_denied",
            }
        if response.status_code >= HTTPStatus.INTERNAL_SERVER_ERROR:
            return {
                "authenticated": None,
                "authentication": "unknown",
                "entitlement": "unknown",
                "status": "provider_unavailable",
            }

    def read() -> int:
        client = make_client(provider, metadata)
        try:
            symbols = (
                resolve_result(client.symbol.SymbolsGet(), client)
                if provider == "mt5"
                else client.get_symbols()
            )
            if not symbols:
                return 0
            end = datetime.now(UTC)
            frame = _fetch_frame(
                client,
                {
                    "underlying": symbols[0],
                    "timeframe": capabilities(provider)["default_timeframe"],
                },
                end - timedelta(days=7),
                end,
            )
            return len(frame)
        finally:
            if provider != "mt5":
                client.disconnect()

    count = await asyncio.to_thread(read)
    return {
        "authenticated": None if credentials else provider == "mt5",
        "authentication": "unknown"
        if credentials
        else "terminal_bridge"
        if provider == "mt5"
        else "not_required",
        "entitlement": "history_read_verified" if count else "unknown",
        "rows_read": count,
        "status": "ok" if count else "no_history_returned",
    }


def build_provider_testers() -> dict[str, Any]:
    """Register supported adapters without asserting paid subscription access."""
    return dict.fromkeys(PROVIDERS, test_provider_access)
