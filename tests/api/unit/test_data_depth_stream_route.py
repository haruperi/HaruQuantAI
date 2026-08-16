"""Tests for the authenticated multi-symbol Depth-of-Market SSE bridge."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

import pytest
from app.services.api.identity import build_auth_context
from app.services.api.workstation.data import stream_routes
from app.services.api.workstation.data.stream_routes import _stream_market_depth
from app.services.data.contracts import DataError
from app.utils import generate_id
from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict
from starlette.requests import Request


class _DepthEvent(BaseModel):
    """Minimal Data depth event fixture."""

    model_config = ConfigDict(frozen=True)
    sequence: int = 5
    occurred_at: datetime = datetime(2026, 8, 13, 20, tzinfo=UTC)
    books: tuple[dict[str, object], ...] = (
        {
            "symbol": "EURUSD",
            "book_depth": 10,
            "bids": ({"price": "1.1000", "volume": "2.5"},),
            "asks": ({"price": "1.1002", "volume": "1.0"},),
        },
    )
    stale: bool = False
    gap: int = 0
    request_id: str = "req-depth-test"
    source_id: str = "pepperstone-demo"
    errors: tuple[dict[str, object], ...] = ()


class _Manager:
    """Record stream quota lifecycle."""

    def __init__(self) -> None:
        """Initialize counters."""
        self.opened = 0
        self.closed = 0

    async def open(self, **_values: object) -> None:
        """Record admission."""
        self.opened += 1

    async def close(self, _connection_id: str) -> None:
        """Record cleanup."""
        self.closed += 1


def _context() -> object:
    """Build one authenticated Data reader."""
    return build_auth_context(
        principal={
            "principal_id": "user-depth-test",
            "principal_type": "USER",
            "roles": ("user",),
            "permissions": ("data:read",),
            "scopes": (),
            "tenant_or_environment": "development",
            "runtime_profile": "research",
        },
        trace={
            "issued_at": datetime.now(UTC),
            "request_id": generate_id("req"),
            "workflow_id": generate_id("wf"),
            "correlation_id": generate_id("cor"),
        },
    )


def test_depth_route_preserves_atomic_books_and_releases_quota(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """One Data depth read becomes one SSE payload for all requested symbols."""

    async def source(_request: object) -> AsyncGenerator[_DepthEvent]:
        yield _DepthEvent()

    async def scenario() -> None:
        monkeypatch.setattr(stream_routes, "stream_market_depth", source)
        application = FastAPI()
        manager = _Manager()
        application.state.api_stream_connection_manager = manager
        request = Request(
            {
                "type": "http",
                "method": "GET",
                "path": "/api/v1/data/depth-stream",
                "headers": (),
                "app": application,
            }
        )
        response = await _stream_market_depth(
            request=request,
            context=_context(),
            symbols="EURUSD,GBPUSD",
            last_event_id=None,
        )
        body = b"".join([chunk async for chunk in response.body_iterator])
        document = next(
            json.loads(line.removeprefix("data: "))
            for line in body.decode().splitlines()
            if line.startswith("data: ")
        )
        assert document["sequence"] == 5
        assert document["payload"]["kind"] == "depth"
        assert document["payload"]["source_id"] == "pepperstone-demo"
        assert document["payload"]["books"][0]["symbol"] == "EURUSD"
        assert manager.opened == manager.closed == 1

    asyncio.run(scenario())


def test_depth_route_surfaces_a_bounded_source_failure_and_releases_quota(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An upstream depth stream that never delivers fails the route, not hangs it."""

    async def source(_request: object) -> AsyncGenerator[_DepthEvent]:
        raise DataError(
            "SOURCE_UNAVAILABLE",
            safe_details={"operation": "mt5_depth_first_read"},
        )
        yield _DepthEvent()  # pragma: no cover - unreachable generator marker

    async def scenario() -> None:
        monkeypatch.setattr(stream_routes, "stream_market_depth", source)
        application = FastAPI()
        manager = _Manager()
        application.state.api_stream_connection_manager = manager
        request = Request(
            {
                "type": "http",
                "method": "GET",
                "path": "/api/v1/data/depth-stream",
                "headers": (),
                "app": application,
            }
        )
        response = await _stream_market_depth(
            request=request,
            context=_context(),
            symbols="EURUSD",
            last_event_id=None,
        )

        with pytest.raises(DataError) as failure:
            await asyncio.wait_for(
                anext(response.body_iterator),
                timeout=5.0,
            )

        assert failure.value.code == "SOURCE_UNAVAILABLE"
        assert manager.opened == manager.closed == 1

    asyncio.run(scenario())
