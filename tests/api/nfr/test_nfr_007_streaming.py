"""NFR-API-007: Disconnect stops delivery, releases resources, preserves owner state.

Verifies the StreamConnectionManager lifecycle: after a connection is closed,
no further events are delivered, resources are released (the connection is
removed from the registry), and a terminal error stops delivery cleanly.
"""

import asyncio

import pytest
from app.services.api.widgets.event_delivery import (
    build_stream_event,
    create_stream_connection_manager,
)
from app.services.api.widgets.event_delivery.orchestration import StreamLimitError


def _manager() -> object:
    """Build a stream connection manager with small bounded limits."""
    return create_stream_connection_manager(
        max_connections_per_actor=2,
        max_connections_process=4,
        resume_window=8,
    )


def _event(sequence: int, event_type: str = "payload") -> object:
    """Build one minimal validated stream event."""
    return build_stream_event(
        {
            "sequence": sequence,
            "event_type": event_type,
            "timestamp": "2026-08-03T12:00:00Z",
            "payload": {"seq": sequence} if event_type == "payload" else None,
            "error": "terminal" if event_type == "error" else None,
            "cursor": str(sequence),
            "kind": "tick",
        },
        {
            "request_id": "req_nfr",
            "trace_id": "trc_nfr",
            "route": "/api/v1/data/stream",
        },
    )


class TestNfrApi007Streaming:
    """NFR-API-007: stream disconnect lifecycle."""

    @staticmethod
    def test_close_releases_connection_resources() -> None:
        """After close, the connection is removed from the registry."""

        async def _run() -> None:
            manager = _manager()
            await manager.open(connection_id="conn-1", actor_id="actor-1")
            await manager.close("conn-1")
            with pytest.raises(StreamLimitError):
                async for _ in manager.events("conn-1"):
                    pass

        asyncio.run(_run())

    @staticmethod
    def test_close_is_idempotent() -> None:
        """Closing an already-closed connection is a no-op."""

        async def _run() -> None:
            manager = _manager()
            await manager.open(connection_id="conn-3", actor_id="actor-3")
            await manager.close("conn-3")
            await manager.close("conn-3")  # must not raise

        asyncio.run(_run())

    @staticmethod
    def test_terminal_error_stops_delivery_and_cleans_up() -> None:
        """A terminal error event stops delivery; event after it is not delivered."""

        async def _run() -> None:
            manager = _manager()
            await manager.open(connection_id="conn-4", actor_id="actor-4")
            await manager.publish(_event(1))
            await manager.publish(_event(2, "error"))
            await manager.publish(_event(3))
            sequences: list[int] = []
            async for event in manager.events("conn-4"):
                if hasattr(event, "sequence"):
                    sequences.append(event.sequence)
            # Event 3 (published after the terminal error) must not be delivered.
            assert 3 not in sequences
            # After the consumer loop ends, the connection is cleaned up.
            with pytest.raises(StreamLimitError):
                async for _ in manager.events("conn-4"):
                    pass

        asyncio.run(_run())
