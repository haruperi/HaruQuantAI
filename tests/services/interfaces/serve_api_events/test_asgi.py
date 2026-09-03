"""ASGI boundary tests for the serve-api-events mounting surface."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any
from uuid import uuid7

import httpx
import pytest
import pytest_asyncio
from app.contracts.interfaces.capabilities import OBSERVE_MARKET_DATA_CAPABILITY
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.interfaces.observe_market_data.config import ObserveMarketDataConfig
from app.services.interfaces.observe_market_data.gateway import MarketDataGateway
from app.services.interfaces.serve_api_events.asgi import create_api_asgi_app

from tests.services.interfaces.observe_market_data.fakes import (
    QueuedStreamProvider,
    make_event,
)

_EVENT_TIME = datetime(2026, 9, 3, 12, 0, 0, tzinfo=UTC)


class _FixedClock:
    """Deterministic UTC clock for boundary tests."""

    def __init__(self) -> None:
        """Initialize the controlled instant."""
        self.now = _EVENT_TIME

    def __call__(self) -> datetime:
        """Return the controlled instant."""
        return self.now


async def _settle() -> None:
    """Yield control for background task scheduling."""
    for _ in range(10):
        await asyncio.sleep(0)


@pytest_asyncio.fixture
async def live_boundary() -> AsyncIterator[
    tuple[ServiceRegistry, QueuedStreamProvider]
]:
    """Provide a registry with a live observation gateway and provider."""
    provider = QueuedStreamProvider()
    gateway = MarketDataGateway(
        provider,
        ObserveMarketDataConfig(),
        clock=_FixedClock(),
    )
    consumer = asyncio.create_task(gateway.run())
    registry = ServiceRegistry()
    registry.register(
        OBSERVE_MARKET_DATA_CAPABILITY,
        gateway,
        owner_id="FEAT-IFACE-OBSERVE_MARKET_DATA",
        scope=FeatureScope(owner_id="FEAT-IFACE-OBSERVE_MARKET_DATA"),
    )
    await _settle()
    assert not consumer.done()
    yield registry, provider
    gateway.close()
    provider.finish()
    await asyncio.wait_for(consumer, timeout=2.0)


def _client(registry: ServiceRegistry) -> httpx.AsyncClient:
    """Build an ASGI test client for the boundary app."""
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create_api_asgi_app(registry)),
        base_url="http://boundary",
    )


def _parse_sse_frames(body: str) -> list[dict[str, Any]]:
    """Parse SSE frames into their decoded data payloads."""
    frames = []
    for chunk in body.split("\n\n"):
        data_lines = [
            line.removeprefix("data: ").strip()
            for line in chunk.splitlines()
            if line.startswith("data:")
        ]
        if data_lines:
            frames.append(json.loads("\n".join(data_lines)))
    return frames


@pytest.mark.asyncio
async def test_snapshot_route_serves_envelope(
    live_boundary: tuple[ServiceRegistry, QueuedStreamProvider],
) -> None:
    """Verify the canonical JSON snapshot envelope."""
    registry, provider = live_boundary
    provider.publish(make_event(1, "EURUSD", occurred_at=_EVENT_TIME))
    await _settle()

    async with _client(registry) as client:
        response = await client.get(
            "/api/v1/market/ticks",
            headers={"X-Request-Id": "req-fixed-1"},
        )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["metadata"]["request_id"] == "req-fixed-1"
    assert payload["metadata"]["route"] == "/api/v1/market/ticks"
    assert payload["metadata"]["operation"] == "api.market.ticks"
    assert payload["metadata"]["side_effect"] == "read"
    assert payload["data"]["quotes"][0]["symbol"] == "EURUSD"
    assert payload["data"]["source_id"] == "data.stream-market-events@1"
    assert payload["data"]["stale"] is False


@pytest.mark.asyncio
async def test_snapshot_route_filters_symbols(
    live_boundary: tuple[ServiceRegistry, QueuedStreamProvider],
) -> None:
    """Verify the comma-joined symbols query filter."""
    registry, provider = live_boundary
    provider.publish(make_event(1, "EURUSD", occurred_at=_EVENT_TIME))
    provider.publish(make_event(2, "GBPUSD", occurred_at=_EVENT_TIME))
    await _settle()

    async with _client(registry) as client:
        response = await client.get(
            "/api/v1/market/ticks",
            params={"symbols": "GBPUSD"},
        )
    quotes = response.json()["data"]["quotes"]
    assert [quote["symbol"] for quote in quotes] == ["GBPUSD"]


@pytest.mark.asyncio
async def test_snapshot_route_rejects_oversized_filter(
    live_boundary: tuple[ServiceRegistry, QueuedStreamProvider],
) -> None:
    """Verify the 200-symbol bound fails closed."""
    registry, _provider = live_boundary
    symbols = ",".join(f"S{index}" for index in range(201))

    async with _client(registry) as client:
        response = await client.get(
            "/api/v1/market/ticks",
            params={"symbols": symbols},
        )
    assert response.status_code == 400
    payload = response.json()
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_routes_fail_closed_without_capability() -> None:
    """Verify absent gateway capability serves the stable unavailable failure."""
    registry = ServiceRegistry()
    async with _client(registry) as client:
        snapshot = await client.get("/api/v1/market/ticks")
        stream = await client.get("/api/v1/data/snapshot-stream")

    assert snapshot.status_code == 503
    assert snapshot.json()["error"]["code"] == "CAPABILITY_UNAVAILABLE"
    assert stream.status_code == 503
    assert stream.json()["error"]["code"] == "CAPABILITY_UNAVAILABLE"


@pytest.mark.asyncio
async def test_unknown_route_and_method_fail_closed(
    live_boundary: tuple[ServiceRegistry, QueuedStreamProvider],
) -> None:
    """Verify unregistered paths and methods return error envelopes."""
    registry, _provider = live_boundary
    async with _client(registry) as client:
        missing = await client.get("/api/v1/unknown")
        method = await client.post("/api/v1/market/ticks")

    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "NOT_FOUND"
    assert method.status_code == 405
    assert method.json()["error"]["code"] == "NOT_IMPLEMENTED"


async def _run_sse_until(
    registry: ServiceRegistry,
    path: str,
    *,
    query: str,
    headers: list[tuple[bytes, bytes]],
    frame_count: int,
) -> str:
    """Drive one SSE request through raw ASGI and collect body chunks.

    The client disconnects once ``frame_count`` payload frames have been
    received, so the app releases its subscription deterministically.

    Args:
        registry: Registry carrying the observation gateway.
        path: Requested route path.
        query: Raw query string.
        headers: Raw request headers.
        frame_count: Number of body chunks to collect before disconnect.

    Returns:
        Concatenated SSE body text.
    """
    app = create_api_asgi_app(registry)
    body: list[bytes] = []
    disconnect = asyncio.Event()
    receive_calls = 0

    async def receive() -> dict[str, Any]:
        nonlocal receive_calls
        receive_calls += 1
        if receive_calls == 1:
            return {"type": "http.request", "body": b"", "more_body": False}
        await disconnect.wait()
        return {"type": "http.disconnect"}

    async def send(message: dict[str, Any]) -> None:
        if message.get("type") == "http.response.body" and message.get("body"):
            body.append(message["body"])
            if len(body) >= frame_count:
                disconnect.set()

    request = asyncio.create_task(
        app(
            {
                "type": "http",
                "method": "GET",
                "path": path,
                "query_string": query.encode("latin-1"),
                "headers": headers,
            },
            receive,
            send,
        )
    )
    for _ in range(200):
        if request.done():
            break
        await asyncio.sleep(0)
    disconnect.set()
    await asyncio.wait_for(request, timeout=2.0)
    return b"".join(body).decode("utf-8")


@pytest.mark.asyncio
async def test_sse_route_streams_snapshot_frames(
    live_boundary: tuple[ServiceRegistry, QueuedStreamProvider],
) -> None:
    """Verify SSE frames carry the adopted stream contract shape."""
    registry, provider = live_boundary
    provider.publish(make_event(1, "EURUSD", occurred_at=_EVENT_TIME))
    await _settle()
    app = create_api_asgi_app(registry)
    body: list[bytes] = []
    disconnect = asyncio.Event()
    receive_calls = 0

    async def receive() -> dict[str, Any]:
        nonlocal receive_calls
        receive_calls += 1
        if receive_calls == 1:
            return {"type": "http.request", "body": b"", "more_body": False}
        await disconnect.wait()
        return {"type": "http.disconnect"}

    async def send(message: dict[str, Any]) -> None:
        if message.get("type") == "http.response.body" and message.get("body"):
            body.append(message["body"])
            if len(body) >= 2:
                disconnect.set()

    request = asyncio.create_task(
        app(
            {
                "type": "http",
                "method": "GET",
                "path": "/api/v1/data/snapshot-stream",
                "query_string": b"",
                "headers": [],
            },
            receive,
            send,
        )
    )
    for _ in range(200):
        if provider.subscriber_count >= 2:
            break
        await asyncio.sleep(0)
    provider.publish(
        make_event(2, "EURUSD", "1.086", "1.0862", occurred_at=_EVENT_TIME)
    )
    for _ in range(200):
        if request.done():
            break
        await asyncio.sleep(0)
    disconnect.set()
    await asyncio.wait_for(request, timeout=2.0)

    frames = _parse_sse_frames(b"".join(body).decode("utf-8"))
    assert len(frames) == 2
    first, second = frames
    assert first["event_type"] == "payload"
    assert first["route"] == "/api/v1/data/snapshot-stream"
    assert first["payload"]["quotes"][0]["symbol"] == "EURUSD"
    assert first["payload"]["source_id"] == "data.stream-market-events@1"
    assert "gap" in first["payload"]
    assert "stale" in first["payload"]
    assert second["sequence"] == 2
    assert second["cursor"] == "2"
    assert second["payload"]["quotes"][0]["bid"] == "1.086"


@pytest.mark.asyncio
async def test_sse_route_passes_symbols_and_resume(
    live_boundary: tuple[ServiceRegistry, QueuedStreamProvider],
) -> None:
    """Verify subscription filter and resume passthrough."""
    registry, provider = live_boundary
    resume_id = str(uuid7())

    body = await _run_sse_until(
        registry,
        "/api/v1/market/ticks/stream",
        query="symbols=EURUSD",
        headers=[(b"last-event-id", resume_id.encode("ascii"))],
        frame_count=1,
    )

    assert _parse_sse_frames(body)
    subscription = provider.subscriptions[-1]
    assert subscription.resume_event_id == resume_id


@pytest.mark.asyncio
async def test_sse_disconnect_releases_subscription(
    live_boundary: tuple[ServiceRegistry, QueuedStreamProvider],
) -> None:
    """Verify client disconnect cancels delivery and releases the iterator."""
    registry, provider = live_boundary
    app = create_api_asgi_app(registry)
    sent: list[dict[str, Any]] = []
    receive_calls = 0

    async def receive() -> dict[str, Any]:
        nonlocal receive_calls
        receive_calls += 1
        if receive_calls == 1:
            return {"type": "http.request", "body": b"", "more_body": False}
        return {"type": "http.disconnect"}

    async def send(message: dict[str, Any]) -> None:
        sent.append(message)

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/v1/data/snapshot-stream",
        "query_string": b"",
        "headers": [],
    }
    await asyncio.wait_for(app(scope, receive, send), timeout=2.0)
    await _settle()

    assert any(message.get("more_body") for message in sent)
    assert provider.iterator_closed is True


@pytest.mark.asyncio
async def test_lifespan_protocol_is_answered(
    live_boundary: tuple[ServiceRegistry, QueuedStreamProvider],
) -> None:
    """Verify ASGI lifespan startup and shutdown complete."""
    registry, _provider = live_boundary
    app = create_api_asgi_app(registry)
    messages: list[dict[str, Any]] = []

    async def receive() -> dict[str, Any]:
        if not messages:
            return {"type": "lifespan.startup"}
        return {"type": "lifespan.shutdown"}

    async def send(message: dict[str, Any]) -> None:
        messages.append(message)

    await app({"type": "lifespan"}, receive, send)
    assert messages[0] == {"type": "lifespan.startup.complete"}
    assert messages[1] == {"type": "lifespan.shutdown.complete"}
