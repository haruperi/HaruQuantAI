"""Tests for the thin authenticated Data stream transport route."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

import pytest
from app.services.api.identity import build_auth_context
from app.services.api.routes import data_stream
from app.services.api.routes.data_stream import _resume_sequence, _stream_market_data
from app.utils import generate_id
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict
from starlette.requests import Request


class _DataEvent(BaseModel):
    """Minimal structural Data-event fixture consumed by the bridge."""

    model_config = ConfigDict(frozen=True)

    feed_id: str = "feed-test"
    sequence: int
    event_type: str = "tick"
    mode: str = "ticks"
    source_id: str = "mt5"
    symbol: str = "EURUSD"
    timeframe: str = "M1"
    occurred_at: datetime = datetime(2026, 8, 3, 12, tzinfo=UTC)
    payload: object | None = None
    cursor: str
    error: str | None = None
    terminal: bool = False
    request_id: str = "req-data-test"


class _Manager:
    """Record API connection quota lifecycle calls."""

    def __init__(self) -> None:
        """Initialize empty lifecycle evidence."""
        self.opened = 0
        self.closed = 0

    async def open(self, **_values: object) -> None:
        """Record one opened connection."""
        self.opened += 1

    async def close(self, _connection_id: str) -> None:
        """Record one released connection."""
        self.closed += 1


def _context() -> object:
    """Return a validated caller with Data read permission."""
    request_id = generate_id("req")
    return build_auth_context(
        principal={
            "principal_id": "user-stream-test",
            "principal_type": "USER",
            "roles": ("user",),
            "permissions": ("data:read",),
            "scopes": (),
            "tenant_or_environment": "development",
            "runtime_profile": "research",
        },
        trace={
            "issued_at": datetime.now(UTC),
            "request_id": request_id,
            "workflow_id": generate_id("wf"),
            "correlation_id": generate_id("cor"),
        },
    )


def test_stream_route_bridges_every_data_tick_and_releases_quota(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The API preserves ordered tick cadence without owning acquisition."""

    async def fake_stream(_request: object) -> AsyncGenerator[_DataEvent]:
        for sequence in range(2):
            yield _DataEvent(
                sequence=sequence,
                cursor=str(sequence),
                payload={"bid": f"1.100{sequence}"},
            )

    async def scenario() -> None:
        monkeypatch.setattr(data_stream, "stream_market_data", fake_stream)
        application = FastAPI()
        manager = _Manager()
        application.state.api_stream_connection_manager = manager
        request = Request(
            {
                "type": "http",
                "method": "GET",
                "path": "/api/v1/data/stream",
                "headers": (),
                "app": application,
            }
        )
        response = await _stream_market_data(
            request=request,
            context=_context(),
            symbol="EURUSD",
            mode="ticks",
            timeframe="M1",
            source_id="mt5",
            last_event_id=None,
        )
        body = b"".join([chunk async for chunk in response.body_iterator])
        documents = [
            json.loads(line.removeprefix("data: "))
            for line in body.decode().splitlines()
            if line.startswith("data: ")
        ]
        assert [item["sequence"] for item in documents] == [0, 1]
        assert [item["payload"]["kind"] for item in documents] == ["tick", "tick"]
        assert manager.opened == 1
        assert manager.closed == 1

    asyncio.run(scenario())


def test_resume_header_requires_a_non_negative_integer() -> None:
    """Malformed transport cursors fail before Data subscription."""
    assert _resume_sequence(None) is None
    assert _resume_sequence("12") == 12
    with pytest.raises(HTTPException, match="STREAM_CURSOR_INVALID"):
        _resume_sequence("invalid")
    with pytest.raises(HTTPException, match="STREAM_CURSOR_INVALID"):
        _resume_sequence("-1")
