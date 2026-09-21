"""Functional tests for WebSocket and SSE event streaming."""

from __future__ import annotations

import asyncio
import contextlib
import json
from unittest.mock import AsyncMock, MagicMock

from app.contracts.gateway import StreamEnvelope
from app.services.gateway.application import (
    ApplicationConfig,
    ApplicationService,
)
from app.services.gateway.streams import (
    EventStreamService,
    StreamsConfig,
)
from starlette.websockets import WebSocketDisconnect


def test_streams_subscription_and_broadcast() -> None:
    """Test subscription tracking and update broadcasting."""
    app_service = ApplicationService(ApplicationConfig())
    service = EventStreamService(app_service, StreamsConfig())

    assert service.get_active_connections_count() == 0

    # Test subscribe & unsubscribe
    service.subscribe("client-1", "progress")
    service.subscribe("client-2", "progress")
    service.subscribe("client-2", "logs")

    async def _test() -> None:
        await service.broadcast_update(
            project_name="Builder",
            channel_name="progress",
            payload={"percent": 25, "strategies": 10},
        )
        service.unsubscribe("client-1", "progress")

    asyncio.run(_test())


def test_sse_event_streaming() -> None:
    """Test Server-Sent Events generator connects, yields initial ping, and streams data."""
    app_service = ApplicationService(ApplicationConfig())
    service = EventStreamService(app_service, StreamsConfig())

    async def _test() -> None:
        gen = service._sse_event_generator()
        first_frame = await anext(gen)
        assert first_frame == ": connected\n\n"
        assert service.get_active_connections_count() == 1

        # Broadcast event
        await service.broadcast_update(
            project_name="Builder",
            channel_name="progress",
            payload={"percent": 50},
        )

        second_frame = await anext(gen)
        assert second_frame.startswith("data: ")
        data = json.loads(second_frame[6:].strip())
        assert data["project"] == "Builder"
        assert data["channel"] == "progress"
        assert data["data"]["percent"] == 50

        # Close generator cleanly
        await gen.aclose()
        assert service.get_active_connections_count() == 0

    asyncio.run(_test())


def test_websocket_lifecycle_and_protocol() -> None:
    """Test WebSocket connection lifecycle, setup handshake, and frame sending."""
    app_service = ApplicationService(ApplicationConfig())
    service = EventStreamService(app_service, StreamsConfig())

    mock_ws = MagicMock()
    mock_ws.accept = AsyncMock()
    mock_ws.close = AsyncMock()
    mock_ws.send_text = AsyncMock()

    # Client sends setup message, then disconnects
    messages = [
        json.dumps({"action": "setup"}),
        json.dumps({"action": "subscribe", "channel": "progress"}),
    ]

    disconnect_event = asyncio.Event()

    async def _mock_receive_text() -> str:
        if messages:
            return messages.pop(0)
        await disconnect_event.wait()
        raise WebSocketDisconnect(1000)

    mock_ws.receive_text = _mock_receive_text

    async def _test() -> None:
        handler_task = asyncio.create_task(
            service._handle_websocket_connection(mock_ws)
        )
        # Give handler moment to establish and read setup/subscribe
        await asyncio.sleep(0.05)
        assert service.get_active_connections_count() == 1

        # Broadcast message to progress channel
        await service.broadcast_update(
            project_name="Retester",
            channel_name="progress",
            payload={"processed": 42},
        )
        await asyncio.sleep(0.05)

        # Signal disconnect and let handler complete
        disconnect_event.set()
        await handler_task

        assert mock_ws.accept.await_count == 1
        assert service.get_active_connections_count() == 0
        # Verify sent messages: setup_ack and broadcast
        sent_calls = [c.args[0] for c in mock_ws.send_text.await_args_list]
        assert any("setup_ack" in msg for msg in sent_calls)
        assert any("Retester" in msg for msg in sent_calls)

    asyncio.run(_test())


def test_streams_max_connections_rejection() -> None:
    """Verify exceeding max connections drops subsequent requests."""
    app_service = ApplicationService(ApplicationConfig())
    service = EventStreamService(app_service, StreamsConfig(max_connections=1))

    # Manually register one fake client queue
    service._queues["fake-client"] = asyncio.Queue()

    mock_ws = MagicMock()
    mock_ws.close = AsyncMock()

    async def _test() -> None:
        await service._handle_websocket_connection(mock_ws)
        mock_ws.close.assert_awaited_once_with(
            code=1008, reason="Max connections exceeded"
        )

    asyncio.run(_test())


def test_streams_slow_consumer_dropped() -> None:
    """Verify slow consumer whose buffer is full is disconnected."""
    app_service = ApplicationService(ApplicationConfig())
    service = EventStreamService(app_service, StreamsConfig(client_buffer_size=1))

    queue: asyncio.Queue[StreamEnvelope | None] = asyncio.Queue(maxsize=1)
    service._queues["slow-client"] = queue
    service.subscribe("slow-client", "progress")

    async def _test() -> None:
        # Fill the queue
        await service.broadcast_update("Proj", "progress", {"msg": 1})
        assert "slow-client" in service._queues

        # Second broadcast should overflow buffer and drop client
        await service.broadcast_update("Proj", "progress", {"msg": 2})
        assert "slow-client" not in service._queues

    asyncio.run(_test())


def test_streams_cursor_and_replay() -> None:
    """Verify monotonic cursor generation and buffered event replay."""
    app_service = ApplicationService(ApplicationConfig())
    service = EventStreamService(app_service, StreamsConfig())

    async def _test() -> None:
        # Broadcast three sequential updates
        await service.broadcast_update("Proj", "metrics", {"val": 1})
        await service.broadcast_update("Proj", "metrics", {"val": 2})
        await service.broadcast_update("Proj", "metrics", {"val": 3})

        buf = service._event_buffer["metrics"]
        assert len(buf) == 3
        cursor1 = buf[0].cursor
        cursor2 = buf[1].cursor
        cursor3 = buf[2].cursor
        assert cursor1 is not None and cursor2 is not None and cursor3 is not None
        assert cursor1.startswith("metrics:1:")
        assert cursor2.startswith("metrics:2:")
        assert cursor3.startswith("metrics:3:")

        # Replay after cursor1 should return items 2 and 3
        replayed = service.get_events_after("metrics", cursor1)
        assert len(replayed) == 2
        assert replayed[0].data["val"] == 2
        assert replayed[1].data["val"] == 3

        # Replay after cursor3 should return empty tuple
        assert service.get_events_after("metrics", cursor3) == ()

        # Replay with unknown cursor returns empty tuple
        assert service.get_events_after("metrics", "unknown-cursor") == ()

    asyncio.run(_test())


def test_streams_heartbeat() -> None:
    """Verify background heartbeat broadcasting ping frames."""
    app_service = ApplicationService(ApplicationConfig())
    service = EventStreamService(app_service, StreamsConfig(heartbeat_interval_s=0.01))

    q: asyncio.Queue[StreamEnvelope | None] = asyncio.Queue()
    service._queues["hb-client"] = q
    service.subscribe("hb-client", "heartbeat")

    async def _test() -> None:
        hb_task = asyncio.create_task(service.run_heartbeat())
        try:
            envelope = await asyncio.wait_for(q.get(), timeout=1.0)
            assert envelope is not None
            assert envelope.channel == "heartbeat"
            assert envelope.project == "system"
            assert envelope.data["type"] == "ping"
        finally:
            hb_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await hb_task

    asyncio.run(_test())


def test_websocket_auth_gate() -> None:
    """Verify WebSocket connection rejects unauthenticated client with code 4401."""
    from app.services.gateway.authorization import (
        AuthorizationConfig,
        AuthorizationService,
    )

    auth = AuthorizationService(
        AuthorizationConfig(
            token_auth_enabled=True,
            static_tokens=("valid-token",),
        )
    )

    app_service = ApplicationService(ApplicationConfig())
    service = EventStreamService(app_service, StreamsConfig(), auth=auth)

    mock_ws = MagicMock()
    mock_ws.scope = {
        "headers": [(b"host", b"localhost")],
        "client": ("127.0.0.1", 50000),
    }
    mock_ws.close = AsyncMock()

    async def _test() -> None:
        await service._handle_websocket_connection(mock_ws)
        mock_ws.close.assert_awaited_once_with(code=4401, reason="Unauthorized")

    asyncio.run(_test())
