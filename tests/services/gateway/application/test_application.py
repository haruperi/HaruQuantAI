"""Functional tests for gateway application service."""

from __future__ import annotations

import asyncio
from pathlib import Path

import httpx
from app.services.gateway.application import (
    ApplicationConfig,
    ApplicationService,
)
from fastapi import APIRouter


def test_application_service_health_and_status(tmp_path: Path) -> None:
    """Test standard health check and readiness status endpoints."""
    # Create static test directory
    ui_dir = tmp_path / "ui"
    ui_dir.mkdir()
    (ui_dir / "index.html").write_text("<h1>HaruQuant UI</h1>", encoding="utf-8")

    config = ApplicationConfig(static_ui_dir=ui_dir)
    service = ApplicationService(config)

    # Mount custom test router
    test_router = APIRouter()

    @test_router.get("/custom")
    def custom_endpoint() -> dict[str, str]:
        return {"hello": "world"}

    service.mount_router("/api/v1/test", test_router)

    info = service.get_server_info()
    assert info.host == "127.0.0.1"
    assert info.port == 8000
    assert info.loopback_only is True
    assert "/health" in info.active_routes
    assert "/healthz" in info.active_routes
    assert "/readyz" in info.active_routes
    assert "/api/v1/test/custom" in info.active_routes

    async def _test() -> None:
        transport = httpx.ASGITransport(app=service.get_app())
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            # /health
            resp_health = await client.get("/health")
            assert resp_health.status_code == 200
            assert resp_health.json()["status"] == "ok"

            # /healthz
            resp_healthz = await client.get("/healthz")
            assert resp_healthz.status_code == 200

            # /readyz
            resp_readyz = await client.get("/readyz")
            assert resp_readyz.status_code == 200
            assert resp_readyz.json()["status"] == "ready"

            # /api/v1/status
            resp_status = await client.get("/api/v1/status")
            assert resp_status.status_code == 200
            assert resp_status.json()["port"] == 8000

            # Mounted router endpoint
            resp_custom = await client.get("/api/v1/test/custom")
            assert resp_custom.status_code == 200
            assert resp_custom.json() == {"hello": "world"}

            # Static mounted file
            resp_ui = await client.get("/ui/index.html")
            assert resp_ui.status_code == 200
            assert "HaruQuant UI" in resp_ui.text

    asyncio.run(_test())


def test_application_gzip_decompression() -> None:
    """Verify inbound gzip request payload decompression."""
    import gzip
    import json

    service = ApplicationService(ApplicationConfig())
    router = APIRouter()

    @router.post("/echo")
    async def echo_endpoint(payload: dict[str, str]) -> dict[str, str]:
        return payload

    service.mount_router("/api/v1", router)

    async def _test() -> None:
        transport = httpx.ASGITransport(app=service.get_app())
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            raw_data = json.dumps({"message": "compressed payload"}).encode("utf-8")
            compressed_data = gzip.compress(raw_data)

            # Valid gzip payload
            resp = await client.post(
                "/api/v1/echo",
                content=compressed_data,
                headers={
                    "Content-Encoding": "gzip",
                    "Content-Type": "application/json",
                },
            )
            assert resp.status_code == 200
            assert resp.json() == {"message": "compressed payload"}

            # Malformed gzip payload returns 400 Problem Details
            resp_bad = await client.post(
                "/api/v1/echo",
                content=b"not-gzip-data",
                headers={
                    "Content-Encoding": "gzip",
                    "Content-Type": "application/json",
                },
            )
            assert resp_bad.status_code == 400
            assert resp_bad.headers["content-type"] == "application/problem+json"
            assert "Invalid gzip" in resp_bad.json()["detail"]

    asyncio.run(_test())


def test_application_auth_middleware() -> None:
    """Verify GatewayAuthMiddleware enforces authentication on non-exempt routes."""
    from app.services.gateway.authorization import (
        AuthorizationConfig,
        AuthorizationService,
    )

    auth_config = AuthorizationConfig(
        token_auth_enabled=True,
        static_tokens=("test-secret-token",),
    )
    auth_service = AuthorizationService(auth_config)

    app_config = ApplicationConfig()
    service = ApplicationService(app_config, auth=auth_service)

    router = APIRouter()

    @router.get("/protected")
    async def protected_endpoint() -> dict[str, str]:
        return {"access": "granted"}

    service.mount_router("/api/v1", router)

    async def _test() -> None:
        transport = httpx.ASGITransport(app=service.get_app())
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            # System probe is exempt from auth
            resp_health = await client.get("/healthz")
            assert resp_health.status_code == 200

            # Protected endpoint without credentials fails with 401
            resp_unauth = await client.get("/api/v1/protected")
            assert resp_unauth.status_code == 401
            assert resp_unauth.headers["content-type"] == "application/problem+json"
            assert resp_unauth.json()["title"] == "Unauthorized"

            # Protected endpoint with valid credentials succeeds
            resp_auth = await client.get(
                "/api/v1/protected",
                headers={"X-API-Key": "test-secret-token"},
            )
            assert resp_auth.status_code == 200
            assert resp_auth.json() == {"access": "granted"}

    asyncio.run(_test())


def test_application_cors_configuration() -> None:
    """Verify CORS headers for configured allowed origins."""
    service = ApplicationService(ApplicationConfig())

    async def _test() -> None:
        transport = httpx.ASGITransport(app=service.get_app())
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            resp = await client.options(
                "/health",
                headers={
                    "Origin": "http://127.0.0.1:3000",
                    "Access-Control-Request-Method": "GET",
                },
            )
            assert (
                resp.headers.get("access-control-allow-origin")
                == "http://127.0.0.1:3000"
            )
            assert resp.headers.get("access-control-allow-credentials") == "true"

    asyncio.run(_test())
