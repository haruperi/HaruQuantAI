"""Consolidated offline usage example for the Gateway domain.

Run with:
    `uv run python -m tests.examples.gateway_usage`
"""

import asyncio
from unittest.mock import AsyncMock

import httpx
import uvicorn
from app.contracts.gateway import HTTP_SERVER
from app.kernel.bootstrapper import Runtime
from app.services.gateway.api_server import feature as gateway_feature


async def example_gateway_api_server() -> None:
    """Demonstrate gateway API server initialization and ASGI querying."""
    # Mock network loop for safe, offline, instantaneous execution

    async def _mock_serve(self: uvicorn.Server) -> None:
        await asyncio.Event().wait()

    uvicorn.Server.serve = AsyncMock(side_effect=_mock_serve)  # type: ignore[method-assign]

    async with Runtime((gateway_feature,)) as runtime:
        gateway = runtime.require(HTTP_SERVER)
        info = gateway.get_server_info()
        print(f"Gateway server initialized on {info.host}:{info.port}")
        print(f"Active routes: {', '.join(info.active_routes)}")

        # Perform in-memory ASGI request against the FastAPI app
        transport = httpx.ASGITransport(app=gateway.get_app())
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            response = await client.get("/health")
            print(f"GET /health status: {response.status_code}")
            print(f"Payload: {response.json()}")

            status_resp = await client.get("/api/v1/status")
            print(f"GET /api/v1/status status: {status_resp.status_code}")
            print(f"Payload: {status_resp.json()}")


def main() -> None:
    """Execute the gateway usage demonstration."""
    asyncio.run(example_gateway_api_server())


if __name__ == "__main__":
    main()
