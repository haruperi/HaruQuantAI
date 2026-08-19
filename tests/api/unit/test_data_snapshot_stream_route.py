"""Tests for the authenticated multi-symbol snapshot SSE bridge."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

import pytest
from app.services.api.identity import build_auth_context
from app.services.api.widgets.data import stream_routes
from app.services.api.widgets.data.stream_routes import _stream_market_snapshots
from app.utils import generate_id
from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict
from starlette.requests import Request


class _SnapshotEvent(BaseModel):
    """Minimal Data snapshot event fixture."""

    model_config = ConfigDict(frozen=True)
    sequence: int = 8
    occurred_at: datetime = datetime(2026, 8, 13, 20, tzinfo=UTC)
    quotes: tuple[dict[str, object], ...] = (
        {
            "symbol": "EURUSD",
            "time": "2026-08-13T20:00:00Z",
            "bid": "1.1000",
            "ask": "1.1002",
            "last": None,
            "spread": "0.0002",
        },
    )
    stale: bool = False
    gap: int = 0
    request_id: str = "req-snapshot-test"
    source_id: str = "pepperstone-demo"


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
            "principal_id": "user-snapshot-test",
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


def test_snapshot_route_preserves_atomic_quotes_and_releases_quota(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """One Data snapshot becomes one SSE payload for all requested symbols."""

    async def source(_request: object) -> AsyncGenerator[_SnapshotEvent]:
        yield _SnapshotEvent()

    async def scenario() -> None:
        monkeypatch.setattr(stream_routes, "stream_market_snapshots", source)
        application = FastAPI()
        manager = _Manager()
        application.state.api_stream_connection_manager = manager
        request = Request(
            {
                "type": "http",
                "method": "GET",
                "path": "/api/v1/data/snapshot-stream",
                "headers": (),
                "app": application,
            }
        )
        response = await _stream_market_snapshots(
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
        assert document["sequence"] == 8
        assert document["payload"]["kind"] == "snapshot"
        assert document["payload"]["source_id"] == "pepperstone-demo"
        assert document["payload"]["quotes"][0]["symbol"] == "EURUSD"
        assert manager.opened == manager.closed == 1

    asyncio.run(scenario())
