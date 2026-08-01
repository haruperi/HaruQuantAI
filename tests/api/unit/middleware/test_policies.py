"""Tests for API rate-limit and deadline middleware."""

import asyncio

from app.services.api import build_api_settings, create_api_app
from app.services.api.middleware.deadlines import DeadlineMiddleware
from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_registered_rate_class_is_enforced() -> None:
    """A route exceeding its configured class returns the stable error envelope."""
    limits = {
        "authentication": (5, 60.0),
        "compute": (10, 60.0),
        "governed_write": (10, 60.0),
        "read": (1, 60.0),
        "stream": (10, 60.0),
    }
    app = create_api_app(build_api_settings(rate_limits_by_class=limits))
    client = TestClient(app)
    try:
        assert client.get("/api/v1/health/liveness").status_code == 200
        limited = client.get("/api/v1/health/liveness")
    finally:
        client.close()
    assert limited.status_code == 429
    assert limited.json()["error"]["code"] == "RATE_LIMITED"


def test_deadline_returns_gateway_timeout() -> None:
    """A slow asynchronous handler is cancelled at the configured deadline."""
    app = FastAPI()
    app.add_middleware(DeadlineMiddleware, timeout_seconds=0.001)

    @app.get("/slow")
    async def slow() -> dict[str, bool]:
        """Return only after the middleware deadline."""
        await asyncio.sleep(0.05)
        return {"completed": True}

    with TestClient(app) as client:
        response = client.get("/slow")
    assert response.status_code == 504
    assert response.json() == {"detail": "UPSTREAM_TIMEOUT"}
