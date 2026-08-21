"""Unit and integration tests for system control plane HTTP endpoints."""

import asyncio
import json
import urllib.request
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import pytest

from app.api.facade import create_api
from app.api.http import SystemHttpServer, handle_system_request
from app.composition.discovery import DiscoveryResult, FeatureDiscoverer
from app.composition.engine import CompositionEngine
from app.contracts.data.historical_bars import (
    HISTORICAL_BARS,
    Bar,
    HistoricalBarsRequest,
)
from app.kernel.feature import FeatureSpec

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext


class TestBarsProvider:
    """Test bars provider."""

    async def retrieve(self, _request: HistoricalBarsRequest) -> list[Bar]:
        return [
            Bar(
                datetime=datetime(2026, 1, 1, 0, 0, tzinfo=UTC),
                open=1.0,
                high=1.1,
                low=0.9,
                close=1.05,
                volume=100.0,
            )
        ]


class TestBarsFeature:
    """Test bars feature."""

    spec = FeatureSpec(
        feature_id="FEAT-DATA-TEST_BARS",
        domain="data",
        provides=frozenset({HISTORICAL_BARS}),
    )

    async def mount(self, context: FeatureContext, _config: object) -> None:
        context.provide(HISTORICAL_BARS, TestBarsProvider())


@pytest.fixture
async def http_api(monkeypatch: pytest.MonkeyPatch) -> AsyncGenerator[Any]:
    """Provide a configured HaruQuantAPI instance for HTTP testing."""
    bars_feat = TestBarsFeature()
    engine = CompositionEngine()
    monkeypatch.setattr(
        FeatureDiscoverer,
        "discover",
        lambda _self: DiscoveryResult(discovered={"FEAT-DATA-TEST_BARS": bars_feat}),
    )
    api = create_api(engine=engine)
    try:
        yield api
    finally:
        await engine.shutdown()


def test_handle_system_liveness(http_api: Any) -> None:
    """Test /system/liveness returns 200 OK with active status."""
    status_code, headers, body = handle_system_request(http_api, "/system/liveness")
    assert status_code == 200
    assert headers["Content-Type"] == "application/json"
    assert body["status"] == "ok"
    assert body["kernel"] == "active"
    assert "timestamp" in body


@pytest.mark.asyncio
async def test_handle_system_readiness_degraded_and_ready(http_api: Any) -> None:
    """Test /system/readiness returns 503 when degraded and 200 when ready."""
    # 1. Unreconciled -> Degraded (503)
    status_code, _headers, body = handle_system_request(http_api, "/system/readiness")
    assert status_code == 503
    assert body["status"] == "degraded"
    assert body["is_ready"] is False

    # 2. Reconcile with live profile (missing many capabilities) -> 503
    config_live = """
    [application]
    profile = "live"
    """
    await http_api.engine.load_and_reconcile_toml(config_live)
    code2, _headers, body2 = handle_system_request(http_api, "/system/readiness")
    assert code2 == 503
    assert body2["is_ready"] is False
    assert len(body2["missing_capabilities"]) > 0

    # 3. Reconcile with research profile with bars enabled -> 200
    config_research = """
    [application]
    profile = "research"
    [features.FEAT-DATA-TEST_BARS]
    enabled = true
    """
    await http_api.engine.load_and_reconcile_toml(config_research)
    code3, _headers, body3 = handle_system_request(http_api, "/system/readiness")
    assert code3 == 200
    assert body3["status"] == "ready"
    assert body3["is_ready"] is True
    assert body3["missing_capabilities"] == []


@pytest.mark.asyncio
async def test_handle_system_capabilities_and_features(http_api: Any) -> None:
    """Test /system/capabilities and /system/features endpoints."""
    config = """
    [application]
    profile = "research"
    [features.FEAT-DATA-TEST_BARS]
    enabled = true
    """
    await http_api.engine.load_and_reconcile_toml(config)

    # Capabilities endpoint
    c_code, _c_headers, c_body = handle_system_request(http_api, "/system/capabilities")
    assert c_code == 200
    assert "capabilities" in c_body
    assert "data.historical-bars@1" in c_body["capabilities"]
    cap_data = c_body["capabilities"]["data.historical-bars@1"]
    assert cap_data["is_available"] is True
    assert cap_data["provider_feature_id"] == "FEAT-DATA-TEST_BARS"
    assert cap_data["generation"] == 1

    # Features endpoint
    f_code, _f_headers, f_body = handle_system_request(http_api, "/system/features")
    assert f_code == 200
    assert "features" in f_body
    assert "FEAT-DATA-TEST_BARS" in f_body["features"]
    feat_data = f_body["features"]["FEAT-DATA-TEST_BARS"]
    assert feat_data["is_active"] is True
    assert feat_data["state"] == "ACTIVE"


def test_handle_system_not_found_and_method_not_allowed(http_api: Any) -> None:
    """Test unknown route returns 404 and invalid method returns 405."""
    code404, _h, body404 = handle_system_request(http_api, "/unknown/path")
    assert code404 == 404
    assert body404["error"] == "Not Found"

    code405, _h, body405 = handle_system_request(
        http_api, "/system/liveness", method="POST"
    )
    assert code405 == 405
    assert body405["error"] == "Method Not Allowed"


@pytest.mark.asyncio
async def test_system_http_server_socket_e2e(http_api: Any) -> None:
    """Test live socket server with real HTTP GET request."""
    server = SystemHttpServer(api=http_api, host="127.0.0.1", port=0)
    await server.start()
    actual_port = server.port
    assert actual_port > 0

    try:
        url = f"http://127.0.0.1:{actual_port}/system/liveness"
        loop = asyncio.get_running_loop()

        def fetch_sync() -> tuple[int, dict[str, Any]]:
            req = urllib.request.urlopen(url, timeout=3.0)
            data = json.loads(req.read().decode("utf-8"))
            return req.status, data

        status_code, data = await loop.run_in_executor(None, fetch_sync)
        assert status_code == 200
        assert data["status"] == "ok"
        assert data["kernel"] == "active"
    finally:
        await server.stop()
