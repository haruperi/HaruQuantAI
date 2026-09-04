"""Boundary tests for the Data reference and settings surfaces.

These tests run against the hydrated boundary database
(data/database/haruquantai.db) exactly like the sibling ASGI tests: the
reference tables are part of the composed runtime state, and startup
hydration is the production seeding path.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx
import pytest
import pytest_asyncio
from app.kernel.registry import ServiceRegistry
from app.services.interfaces.serve_api_events.asgi import create_api_asgi_app

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


@pytest_asyncio.fixture
async def client() -> AsyncIterator[httpx.AsyncClient]:
    """Build an ASGI test client over a bare service registry."""
    transport = httpx.ASGITransport(app=create_api_asgi_app(ServiceRegistry()))
    async with httpx.AsyncClient(
        transport=transport, base_url="http://boundary"
    ) as test_client:
        yield test_client


@pytest.mark.asyncio
async def test_settings_boundary_matches_workstation_contract(
    client: httpx.AsyncClient,
) -> None:
    """Verify manifest, legacy-keyed system settings, and credentials."""
    manifest_res = await client.get("/api/v1/settings/manifest")
    assert manifest_res.status_code == 200
    manifest = manifest_res.json()["data"]
    assert len(manifest) == 49
    by_key = {definition["key"]: definition for definition in manifest}
    account_mode = by_key["ACCOUNT_MODE"]
    assert account_mode["value_kind"] == "string"
    assert account_mode["allowed_values"] == ["sim", "demo", "live"]
    assert account_mode["activation"] == "hot"
    snapshot_port = by_key["MT5_SNAPSHOT_PORT"]
    assert snapshot_port["value_kind"] == "integer"
    assert snapshot_port["minimum"] == 1
    assert snapshot_port["maximum"] == 65535

    settings_res = await client.get("/api/v1/settings?scope=system")
    assert settings_res.status_code == 200
    settings = settings_res.json()["data"]
    assert settings["scope"] == "system"
    assert settings["user_id"] is None
    stored = settings["settings"]
    # The widgets read legacy uppercase keys; a missing MT5 snapshot symbol
    # set is exactly what breaks the market-ticks widget.
    assert stored["MT5_SNAPSHOT_SYMBOLS"] == "EURUSD,GBPUSD,USDJPY,XAUUSD"
    assert stored["ACCOUNT_MODE"] in {"sim", "demo", "live"}
    assert stored["RUNTIME_BROKER"] in {
        "binance",
        "ctrader",
        "dukascopy",
        "mt5",
        "yahoo",
    }
    assert set(stored) == set(by_key)

    credentials_res = await client.get("/api/v1/settings/credentials")
    assert credentials_res.status_code == 200
    credentials = credentials_res.json()["data"]
    assert len(credentials) == 6
    assert "mt5_snapshot_bridge" in {slot["slot"] for slot in credentials}
    assert all(slot["activation"] == "restart_required" for slot in credentials)


@pytest.mark.asyncio
async def test_data_reference_catalogue_routes(
    client: httpx.AsyncClient,
) -> None:
    """Verify capability surface and reference catalogue projections."""
    capabilities_res = await client.get("/api/v1/data/capabilities")
    assert capabilities_res.status_code == 200
    capabilities = capabilities_res.json()["data"]["capabilities"]
    assert len(capabilities) == 14
    assert all(item["availability"] == "available" for item in capabilities)

    series_res = await client.get("/api/v1/data/series?limit=200")
    assert series_res.status_code == 200
    series = series_res.json()["data"]["series"]
    assert len(series) == 60
    assert series[0]["bar_type"] == "start_of_bar"
    assert all("total_days" in row for row in series)

    instruments_res = await client.get("/api/v1/data/instruments?limit=200")
    assert instruments_res.status_code == 200
    instruments = instruments_res.json()["data"]["instruments"]
    assert len(instruments) == 29
    assert instruments[0]["instrument"]

    brokers_res = await client.get("/api/v1/data/brokers?limit=200")
    assert brokers_res.status_code == 200
    brokers = brokers_res.json()["data"]["brokers"]
    assert len(brokers) == 9
    assert all("customized_instruments" in row for row in brokers)

    # Symbol discovery pages with an opaque cursor; the watchlist widget
    # walks every page until next_cursor is null.
    page_one = await client.get("/api/v1/data/symbols?limit=10")
    assert page_one.status_code == 200
    page_one_data = page_one.json()["data"]
    assert len(page_one_data["items"]) == 10
    assert page_one_data["next_cursor"] is not None
    page_two = await client.get(
        f"/api/v1/data/symbols?limit=200&cursor={page_one_data['next_cursor']}"
    )
    page_two_data = page_two.json()["data"]
    assert page_two_data["next_cursor"] is None
    assert len(page_one_data["items"]) + len(page_two_data["items"]) == 29

    quotes_res = await client.get("/api/v1/data/quotes?symbols=EURUSD,GBPUSD")
    assert quotes_res.status_code == 200
    quotes = quotes_res.json()["data"]
    assert [row["symbol"] for row in quotes["rows"]] == ["EURUSD", "GBPUSD"]
    # Reference projections never fabricate live prices.
    assert all(row["bid"] is None for row in quotes["rows"])


@pytest.mark.asyncio
async def test_data_bars_route_serves_stored_history_only(
    client: httpx.AsyncClient,
) -> None:
    """Verify bar history reads and their honest failure modes."""
    bars_res = await client.get("/api/v1/data/bars?symbol=EURUSD&timeframe=H1")
    assert bars_res.status_code == 200
    payload = bars_res.json()["data"]
    assert payload["symbol"] == "EURUSD"
    assert payload["timeframe"] == "H1"
    assert payload["count"] == len(payload["bars"])
    assert payload["count"] > 0
    assert payload["count"] <= 500
    assert payload["cache_status"] == "hit"
    first_bar = payload["bars"][0]
    assert set(first_bar) == {"time", "open", "high", "low", "close", "volume"}
    assert payload["start"] == first_bar["time"]
    assert payload["end"] == payload["bars"][-1]["time"]

    limited = await client.get("/api/v1/data/bars?symbol=EURUSD&timeframe=M1&limit=10")
    assert limited.status_code == 200
    assert limited.json()["data"]["count"] == 10

    # A symbol with no stored history fails closed instead of rendering a
    # generated series the chart would present as real broker history.
    missing = await client.get("/api/v1/data/bars?symbol=NOSUCH&timeframe=H1")
    assert missing.status_code == 503
    assert missing.json()["error"]["code"] == "UPSTREAM_UNAVAILABLE"

    bad_timeframe = await client.get("/api/v1/data/bars?symbol=EURUSD&timeframe=H2")
    assert bad_timeframe.status_code == 422
    assert bad_timeframe.json()["error"]["code"] == "VALIDATION_FAILED"

    inverted = await client.get(
        "/api/v1/data/bars?symbol=EURUSD&timeframe=H1"
        "&start=2026-08-10T00:00:00Z&end=2026-08-01T00:00:00Z"
    )
    assert inverted.status_code == 422
    assert inverted.json()["error"]["code"] == "BAR_WINDOW_INVALID"

    no_symbol = await client.get("/api/v1/data/bars")
    assert no_symbol.status_code == 422


@pytest.mark.asyncio
async def test_data_reference_sync_and_item_routes(
    client: httpx.AsyncClient,
) -> None:
    """Verify reference sync reporting and governed item reads/edits."""
    sync_res = await client.post("/api/v1/data/reference/sync")
    assert sync_res.status_code == 200
    summary = sync_res.json()["data"]
    assert summary["series_synced"] == 60
    assert summary["brokers_synced"] == 9
    assert summary["instruments_synced"] == 29
    # No live terminal participates; the report says so honestly.
    assert summary["mt5_available"] is False
    assert summary["instruments_failed"] == []

    spec_res = await client.get("/api/v1/data/instruments/EURUSD")
    assert spec_res.status_code == 200
    spec = spec_res.json()["data"]
    assert spec["instrument"] == "EURUSD"
    assert "swap" in spec

    # Governed edit round-trip restores the mutated column so repeated test
    # runs stay faithful to the hydrated reference values.
    original = spec["default_spread"] or 0.0
    patched = await client.patch(
        "/api/v1/data/instruments/EURUSD",
        json={"default_spread": original + 3.25},
    )
    assert patched.status_code == 200
    assert patched.json()["data"]["default_spread"] == original + 3.25
    restored = await client.patch(
        "/api/v1/data/instruments/EURUSD",
        json={"default_spread": original},
    )
    assert restored.status_code == 200

    series_res = await client.patch(
        "/api/v1/data/series/1",
        json={"symbol": "AUDUSD", "instrument": "AUDUSD", "show": 1},
    )
    assert series_res.status_code == 200
    assert series_res.json()["data"] == {
        "series_id": 1,
        "symbol": "AUDUSD",
        "instrument": "AUDUSD",
        "bar_type": "start_of_bar",
    }

    missing_series = await client.patch(
        "/api/v1/data/series/99999",
        json={"symbol": "X", "instrument": "X"},
    )
    assert missing_series.status_code == 404
    assert missing_series.json()["error"]["code"] == "SERIES_NOT_FOUND"

    missing_spec = await client.get("/api/v1/data/instruments/NOSUCH")
    assert missing_spec.status_code == 404
    assert missing_spec.json()["error"]["code"] == "INSTRUMENT_NOT_FOUND"

    unknown = await client.get("/api/v1/data/not-a-route")
    assert unknown.status_code == 404
