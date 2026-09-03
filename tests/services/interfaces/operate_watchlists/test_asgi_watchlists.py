"""ASGI CRUD tests for the watchlist boundary routes."""

from __future__ import annotations

from uuid import uuid7

import httpx
import pytest
from app.contracts.workspace.capabilities import MANAGE_WATCHLISTS_CAPABILITY
from app.kernel.registry import ServiceRegistry
from app.services.interfaces.serve_api_events.asgi import create_api_asgi_app

from tests.services.interfaces.workspace_shared import mount_watchlist_stack


@pytest.mark.asyncio
async def test_watchlist_crud_matrix_over_asgi() -> None:
    """Verify list/create/update/delete through the frozen route contract."""
    registry, _store_scope, _gateway_scope = await mount_watchlist_stack()
    transport = httpx.ASGITransport(app=create_api_asgi_app(registry))
    async with httpx.AsyncClient(transport=transport, base_url="http://b") as client:
        listed = await client.get("/api/v1/watchlists")
        assert listed.status_code == 200
        payload = listed.json()
        assert payload["status"] == "success"
        rows = payload["data"]
        assert isinstance(rows, list)
        assert len(rows) == 1
        seeded = rows[0]
        assert seeded["name"] == "Default"
        assert seeded["is_default"] is True
        assert [item["symbol"] for item in seeded["items"]] == [
            "EURUSD",
            "GBPUSD",
            "USDJPY",
            "XAUUSD",
        ]
        for key in (
            "watchlist_id",
            "account_id",
            "name",
            "is_default",
            "sort_order",
            "items",
            "created_at",
            "updated_at",
        ):
            assert key in seeded

        created = await client.post("/api/v1/watchlists", json={"name": "Scalping"})
        assert created.status_code == 200
        new_row = created.json()["data"]
        assert new_row["name"] == "Scalping"
        assert new_row["is_default"] is False
        watchlist_id = new_row["watchlist_id"]

        duplicate = await client.post("/api/v1/watchlists", json={"name": "Scalping"})
        assert duplicate.status_code == 409
        assert duplicate.json()["error"]["code"] == "INTERFACE_VALIDATION_FAILED"

        updated = await client.patch(
            f"/api/v1/watchlists/{watchlist_id}",
            json={"symbols": ["EURUSD", "USDCHF"], "name": "Swing"},
        )
        assert updated.status_code == 200
        row = updated.json()["data"]
        assert row["name"] == "Swing"
        assert [item["symbol"] for item in row["items"]] == ["EURUSD", "USDCHF"]

        promoted = await client.patch(
            f"/api/v1/watchlists/{watchlist_id}", json={"is_default": True}
        )
        assert promoted.status_code == 200
        assert promoted.json()["data"]["is_default"] is True

        blocked = await client.delete(f"/api/v1/watchlists/{watchlist_id}")
        assert blocked.status_code == 409

        deleted = await client.delete(f"/api/v1/watchlists/{seeded['watchlist_id']}")
        assert deleted.status_code == 200
        assert deleted.json()["data"] == {
            "watchlist_id": seeded["watchlist_id"],
            "deleted": True,
        }

        missing = await client.patch(
            f"/api/v1/watchlists/{uuid7()!s}", json={"name": "Ghost"}
        )
        assert missing.status_code == 404

        bad_body = await client.post("/api/v1/watchlists", json={"name": ""})
        assert bad_body.status_code == 400
        assert bad_body.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_watchlist_routes_fail_closed_without_capability() -> None:
    """Verify absent watchlist capability serves the stable failure."""
    registry = ServiceRegistry()
    transport = httpx.ASGITransport(app=create_api_asgi_app(registry))
    async with httpx.AsyncClient(transport=transport, base_url="http://b") as client:
        listed = await client.get("/api/v1/watchlists")
        created = await client.post("/api/v1/watchlists", json={"name": "X"})
    assert listed.status_code == 503
    assert listed.json()["error"]["code"] == "CAPABILITY_UNAVAILABLE"
    assert created.status_code == 503


@pytest.mark.asyncio
async def test_watchlist_removal_withdraws_only_watchlist_capability() -> None:
    """Verify the removal matrix for the watchlist vertical slice."""
    registry, _store_scope, gateway_scope = await mount_watchlist_stack()

    transport = httpx.ASGITransport(app=create_api_asgi_app(registry))
    async with httpx.AsyncClient(transport=transport, base_url="http://b") as client:
        before = await client.get("/api/v1/watchlists")
        assert before.status_code == 200

    await gateway_scope.close()
    transport = httpx.ASGITransport(app=create_api_asgi_app(registry))
    async with httpx.AsyncClient(transport=transport, base_url="http://b") as client:
        after = await client.get("/api/v1/watchlists")
        catalogue = await client.get("/api/v1/data/markets")
    assert after.status_code == 503
    assert after.json()["error"]["code"] == "CAPABILITY_UNAVAILABLE"
    # Unrelated boundary surfaces keep their own availability semantics.
    assert catalogue.status_code == 503
    assert registry.resolve(MANAGE_WATCHLISTS_CAPABILITY) is not None
