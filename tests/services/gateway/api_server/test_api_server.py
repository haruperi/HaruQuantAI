"""Unit tests for Gateway API server service and endpoints."""

import asyncio

import httpx
from app.services.gateway.api_server import ApiServerConfig, ApiServerService


def test_service_initialization_and_info() -> None:
    """Verify service creates app and returns valid server info."""
    config = ApiServerConfig(host="127.0.0.1", port=8000)
    service = ApiServerService(config)

    app = service.get_app()
    assert app.title == "HaruQuant Gateway"

    info = service.get_server_info()
    assert info.host == "127.0.0.1"
    assert info.port == 8000
    assert info.running is False
    assert "/health" in info.active_routes
    assert "/api/v1/status" in info.active_routes


def test_health_endpoint() -> None:
    """Verify GET /health returns standard health check status."""
    service = ApiServerService(ApiServerConfig())

    async def _test() -> None:
        transport = httpx.ASGITransport(app=service.get_app())
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            response = await client.get("/health")
            assert response.status_code == 200
            payload = response.json()
            assert payload["status"] == "ok"
            assert payload["version"] == "0.1.0"
            assert "timestamp" in payload

    asyncio.run(_test())


def test_status_endpoint() -> None:
    """Verify GET /api/v1/status returns diagnostic metadata."""
    service = ApiServerService(ApiServerConfig(host="127.0.0.1", port=8888))

    async def _test() -> None:
        transport = httpx.ASGITransport(app=service.get_app())
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/status")
            assert response.status_code == 200
            payload = response.json()
            assert payload["status"] == "ready"
            assert payload["host"] == "127.0.0.1"
            assert payload["port"] == 8888

    asyncio.run(_test())


def test_docs_enabled_and_disabled() -> None:
    """Verify Swagger docs availability respects enable_docs setting."""
    enabled_service = ApiServerService(ApiServerConfig(enable_docs=True))
    disabled_service = ApiServerService(ApiServerConfig(enable_docs=False))

    async def _test() -> None:
        # Docs enabled
        transport_on = httpx.ASGITransport(app=enabled_service.get_app())
        async with httpx.AsyncClient(
            transport=transport_on, base_url="http://test"
        ) as client:
            resp = await client.get("/docs")
            assert resp.status_code == 200

        # Docs disabled
        transport_off = httpx.ASGITransport(app=disabled_service.get_app())
        async with httpx.AsyncClient(
            transport=transport_off, base_url="http://test"
        ) as client:
            resp = await client.get("/docs")
            assert resp.status_code == 404

    asyncio.run(_test())
