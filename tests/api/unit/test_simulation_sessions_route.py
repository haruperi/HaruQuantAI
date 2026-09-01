"""Tests for completed-run Simulation playback HTTP routes."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from app.kernel.identity import generate_id
from app.services.api.identity import build_auth_context
from app.services.api.widgets.event_delivery import StreamLimitError
from app.services.api.widgets.simulation import (
    session_routes as simulation_sessions,
)
from app.services.api.widgets.simulation.session_routes import (
    _create_session,
    _stream_frames,
)
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict
from starlette.requests import Request


class _JournalEvent(BaseModel):
    """Minimal validated journal event fixture consumed by the route."""

    model_config = ConfigDict(frozen=True)

    run_id: str = "run-playback"
    sequence: int
    occurred_at: datetime = datetime(2026, 8, 4, tzinfo=UTC)
    event_type: str = "order_accepted"
    payload: dict[str, object] = {"order_id": "order-1"}
    previous_hash: str = "a" * 64
    event_hash: str = "b" * 64


class _Manager:
    """Record playback connection quota lifecycle calls."""

    def __init__(self, *, reject: bool = False) -> None:
        """Initialize empty lifecycle evidence."""
        self.reject = reject
        self.opened = 0
        self.closed = 0

    async def open(self, **_values: object) -> None:
        """Open or reject one connection."""
        if self.reject:
            raise StreamLimitError("limit")
        self.opened += 1

    async def close(self, _connection_id: str) -> None:
        """Record one released connection."""
        self.closed += 1


def _context() -> object:
    """Return an authenticated Simulation reader."""
    return build_auth_context(
        principal={
            "principal_id": "user-playback",
            "principal_type": "USER",
            "roles": ("researcher",),
            "permissions": ("simulation:read",),
            "scopes": (),
            "tenant_or_environment": "development",
            "runtime_profile": "simulation",
        },
        trace={
            "issued_at": datetime.now(UTC),
            "request_id": generate_id("req"),
            "workflow_id": generate_id("wf"),
            "correlation_id": generate_id("cor"),
        },
    )


def _request(manager: _Manager) -> Request:
    """Build one request carrying the shared stream manager."""
    application = FastAPI()
    application.state.api_stream_connection_manager = manager
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/api/v1/simulation/sessions/id-test/frames",
            "headers": (),
            "app": application,
        }
    )


def test_create_session_is_durably_idempotent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The POST reserves and finalizes one scoped idempotency key."""
    finalized: list[str] = []
    monkeypatch.setattr(
        simulation_sessions,
        "reserve_idempotency_key",
        lambda **_values: SimpleNamespace(state="reserved", response_json=None),
    )
    monkeypatch.setattr(
        simulation_sessions,
        "finalize_idempotency_key",
        lambda **values: finalized.append(str(values["response_json"])),
    )

    def source(operation: str, run_id: str, **_values: object) -> object:
        assert operation == "create"
        return {"session_id": "id-session", "run_id": run_id, "cursor": -1}

    result = _create_session(
        simulation_sessions.SimulationSessionCreateRequest(run_id="run-playback"),
        _context(),
        source,
        "idem-playback",
    )
    assert result == {
        "session_id": "id-session",
        "run_id": "run-playback",
        "cursor": -1,
    }
    assert len(finalized) == 1


def test_stream_frames_resumes_and_releases_quota() -> None:
    """The SSE route translates frames after the client cursor and cleans up."""

    def source(
        operation: str, _session_id: str, **values: object
    ) -> AsyncGenerator[_JournalEvent]:
        assert operation == "frames"
        assert values["resume_after"] == 4

        async def events() -> AsyncGenerator[_JournalEvent]:
            yield _JournalEvent(sequence=5)

        return events()

    async def scenario() -> tuple[list[dict[str, object]], _Manager]:
        manager = _Manager()
        response = await _stream_frames(
            "id-session",
            _request(manager),
            _context(),
            source,
            "4",
        )
        body = b"".join([chunk async for chunk in response.body_iterator])
        documents = [
            json.loads(line.removeprefix("data: "))
            for line in body.decode().splitlines()
            if line.startswith("data: ")
        ]
        return documents, manager

    documents, manager = asyncio.run(scenario())
    assert documents[0]["sequence"] == 5
    assert documents[0]["cursor"] == "5"
    assert documents[0]["payload"]["kind"] == "order_accepted"
    assert manager.opened == 1
    assert manager.closed == 1


def test_stream_frames_rejects_connection_over_quota() -> None:
    """Quota rejection occurs before the frame producer is invoked."""

    async def scenario() -> None:
        manager = _Manager(reject=True)
        with pytest.raises(HTTPException, match="STREAM_CONNECTION_LIMIT"):
            await _stream_frames(
                "id-session",
                _request(manager),
                _context(),
                lambda *_args, **_kwargs: None,
                None,
            )

    asyncio.run(scenario())


def test_stream_disconnect_releases_connection_quota() -> None:
    """Closing the response iterator releases its admitted connection."""

    def source(
        _operation: str, _session_id: str, **_values: object
    ) -> AsyncGenerator[_JournalEvent]:
        async def events() -> AsyncGenerator[_JournalEvent]:
            yield _JournalEvent(sequence=0)
            yield _JournalEvent(sequence=1)

        return events()

    async def scenario() -> _Manager:
        manager = _Manager()
        response = await _stream_frames(
            "id-session",
            _request(manager),
            _context(),
            source,
            None,
        )
        iterator = response.body_iterator
        await anext(iterator)
        await iterator.aclose()
        return manager

    manager = asyncio.run(scenario())
    assert manager.opened == 1
    assert manager.closed == 1
