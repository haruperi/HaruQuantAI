"""Tests for ordered stream validation, resume, limits, and cleanup."""

import asyncio

import pytest
from app.services.api import create_stream_manager, normalize_stream_event
from app.services.api.streams import StreamGapError, StreamLimitError


def _event(sequence: int) -> object:
    """Build one public ordered event."""
    return normalize_stream_event(
        {"sequence": sequence, "event_type": "payload", "value": sequence},
        {
            "request_id": "req-stream-0001",
            "trace_id": "trace-stream-0001",
            "route": "/api/v1/events",
        },
    )


def test_stream_resume_limits_and_cleanup() -> None:
    """Retain bounded events, enforce quotas, and cleanly disconnect."""

    async def scenario() -> None:
        manager = create_stream_manager(
            max_connections_per_actor=1,
            max_connections_process=2,
            resume_window=2,
            queue_size=2,
        )
        await manager.publish(_event(1))
        await manager.publish(_event(2))
        await manager.open(
            connection_id="connection-1",
            actor_id="actor-1",
            resume_after=1,
        )
        with pytest.raises(StreamLimitError):
            await manager.open(connection_id="connection-2", actor_id="actor-1")
        stream = manager.events("connection-1")
        assert (await anext(stream)).sequence == 2
        await stream.aclose()
        assert manager.connection_count == 0
        await manager.publish(_event(3))
        with pytest.raises(StreamGapError):
            await manager.open(
                connection_id="connection-gap",
                actor_id="actor-2",
                resume_after=0,
            )

    asyncio.run(scenario())


def test_stream_overflow_emits_terminal_error() -> None:
    """Backpressure produces a terminal error before resource cleanup."""

    async def scenario() -> None:
        manager = create_stream_manager(
            max_connections_per_actor=1,
            max_connections_process=1,
            resume_window=3,
            queue_size=1,
        )
        await manager.open(connection_id="slow", actor_id="actor")
        await manager.publish(_event(1))
        await manager.publish(_event(2))
        stream = manager.events("slow")
        terminal = await anext(stream)
        assert terminal.event_type == "error"
        assert terminal.error == "STREAM_BACKPRESSURE_LIMIT"
        with pytest.raises(StopAsyncIteration):
            await anext(stream)
        assert manager.connection_count == 0

    asyncio.run(scenario())


def test_stream_rejects_sensitive_payload() -> None:
    """Secret-bearing owner events never cross the stream boundary."""
    with pytest.raises(ValueError, match="forbidden key"):
        normalize_stream_event(
            {  # pragma: allowlist secret
                "sequence": 1,
                "api_key": "not-published",  # pragma: allowlist secret
            },
            {"request_id": "req-stream-0001", "route": "/api/v1/events"},
        )
