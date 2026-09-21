"""WebSocket and SSE event streaming delivery feature.

Feature:
    FEAT-GATEWAY-STREAMS

Purpose:
    Provides real-time event distribution over WebSocket (`/websocket/updates`)
    and Server-Sent Events (`/api/v1/stream`), matching the SQX donor protocol
    with setup handshakes, project/channel multiplexing, sequence numbering,
    heartbeats, and bounded slow-consumer eviction under capability
    `gateway.streams@1`.

Key capabilities:
    * Multiplexed WebSocket streaming matching SQWebSocketService.js.
    * Client subscription management by project and channel.
    * Bounded queues preventing slow-consumer memory exhaustion.
    * One-way Server-Sent Events (SSE) fallback.

Python API usage:
    streams = ctx.require(GATEWAY_STREAMS)
    await streams.broadcast_update("Builder", "progress", {"pct": 50})

CLI usage:
    uv run python -m tests.examples.05_gateway
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import uuid
from collections import deque
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, override

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse

from app.contracts.gateway import (
    GATEWAY_APPLICATION,
    GATEWAY_AUTHORIZATION,
    GATEWAY_STREAMS,
    AuthenticationError,
    GatewayApplication,
    GatewayAuthorization,
    StreamEnvelope,
)
from app.contracts.gateway import (
    EventStreamGateway as IEventStreamGateway,
)
from app.kernel.feature import FeatureSpec
from app.kernel.logging import get_logger

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class StreamsConfig:
    """Runtime configuration for event stream gateway."""

    max_connections: int = 100
    client_buffer_size: int = 256
    heartbeat_interval_s: float = 15.0
    websocket_path: str = "/websocket/updates"
    sse_path: str = "/api/v1/stream"

    def __post_init__(self) -> None:
        """Validate configuration limits."""
        if self.max_connections <= 0:
            msg = f"max_connections must be > 0; got {self.max_connections}"
            raise ValueError(msg)
        if self.client_buffer_size <= 0:
            msg = f"client_buffer_size must be > 0; got {self.client_buffer_size}"
            raise ValueError(msg)
        if self.heartbeat_interval_s <= 0:
            msg = f"heartbeat_interval_s must be > 0; got {self.heartbeat_interval_s}"
            raise ValueError(msg)


# ---------------------------------------------------------------------------
# Service Implementation
# ---------------------------------------------------------------------------


class EventStreamService(IEventStreamGateway):
    """Implement real-time WebSocket and SSE event streaming."""

    def __init__(
        self,
        app_service: GatewayApplication,
        config: StreamsConfig | None = None,
        auth: GatewayAuthorization | None = None,
    ) -> None:
        """Initialize the event stream service.

        Args:
            app_service: Underlying GatewayApplication supervisor.
            config: Optional runtime streaming configuration.
            auth: Optional transport authorization service.
        """
        self._app_service = app_service
        self._config = config or StreamsConfig()
        self._auth = auth
        self._sequence = 0
        self._subscriptions: dict[str, set[str]] = {}  # channel -> set[client_id]
        self._queues: dict[str, asyncio.Queue[StreamEnvelope | None]] = {}
        self._event_buffer: dict[str, deque[StreamEnvelope]] = {}
        self._setup_routes()

    def _setup_routes(self) -> None:
        """Mount WebSocket and SSE endpoints onto the application."""
        app = self._app_service.get_app()

        @app.websocket(self._config.websocket_path)
        async def websocket_endpoint(websocket: WebSocket) -> None:
            await self._handle_websocket_connection(websocket)

        @app.get(self._config.sse_path)
        async def sse_endpoint() -> StreamingResponse:
            return StreamingResponse(
                self._sse_event_generator(),
                media_type="text/event-stream",
            )

    async def _handle_websocket_connection(self, websocket: WebSocket) -> None:
        """Manage connection lifecycle, setup handshake, and frame delivery."""
        if len(self._queues) >= self._config.max_connections:
            logger.warning("websocket_max_connections_exceeded")
            await websocket.close(code=1008, reason="Max connections exceeded")
            return

        # Authenticate inbound websocket connection if auth is configured
        if self._auth is not None:
            headers: dict[str, str] = {
                k.decode("latin-1").lower(): v.decode("latin-1")
                for k, v in websocket.scope.get("headers", [])
            }
            client = websocket.scope.get("client")
            client_host = client[0] if client else "127.0.0.1"
            try:
                self._auth.authenticate_request(
                    headers=headers, client_host=client_host
                )
            except AuthenticationError:
                logger.warning("websocket_auth_failed", client_host=client_host)
                await websocket.close(code=4401, reason="Unauthorized")
                return

        await websocket.accept()
        client_id = f"client-{uuid.uuid4().hex[:8]}"
        queue: asyncio.Queue[StreamEnvelope | None] = asyncio.Queue(
            maxsize=self._config.client_buffer_size
        )
        self._queues[client_id] = queue
        logger.info("websocket_client_connected", client_id=client_id)

        try:
            async with asyncio.TaskGroup() as tg:
                tg.create_task(self._websocket_send_loop(websocket, queue))
                tg.create_task(
                    self._websocket_receive_loop(websocket, client_id, queue)
                )
        except* WebSocketDisconnect, asyncio.CancelledError:
            pass
        finally:
            self._disconnect_client(client_id)
            with contextlib.suppress(Exception):
                await websocket.close()
            logger.info("websocket_client_disconnected", client_id=client_id)

    async def _websocket_send_loop(
        self,
        websocket: WebSocket,
        queue: asyncio.Queue[StreamEnvelope | None],
    ) -> None:
        """Drain client queue and emit frames over WebSocket."""
        while True:
            envelope = await queue.get()
            if envelope is None:
                break
            payload = {
                "sequence": envelope.sequence,
                "timestamp": envelope.timestamp,
                "projectData": {
                    "name": envelope.project,
                    "channels": [
                        {
                            "name": envelope.channel,
                            "data": envelope.data,
                        }
                    ],
                },
            }
            await websocket.send_text(json.dumps(payload))

    async def _websocket_receive_loop(
        self,
        websocket: WebSocket,
        client_id: str,
        queue: asyncio.Queue[StreamEnvelope | None],
    ) -> None:
        """Receive commands from client (setup handshake, subscribe)."""
        try:
            while True:
                text = await websocket.receive_text()
                try:
                    data = json.loads(text)
                except json.JSONDecodeError:
                    continue

                action = data.get("action")
                if action == "setup":
                    logger.info("websocket_setup_received", client_id=client_id)
                    cursor = data.get("cursor")
                    channel = data.get("channel")
                    ack_payload: dict[str, Any] = {
                        "action": "setup_ack",
                        "client_id": client_id,
                    }
                    if cursor and channel:
                        missed = self.get_events_after(channel, str(cursor))
                        ack_payload["replayed"] = len(missed)
                        await websocket.send_text(json.dumps(ack_payload))
                        for env in missed:
                            await queue.put(env)
                    else:
                        await websocket.send_text(json.dumps(ack_payload))
                elif action == "subscribe":
                    channel = str(data.get("channel", "*"))
                    self.subscribe(client_id, channel)
                    logger.info(
                        "websocket_subscribed",
                        client_id=client_id,
                        channel=channel,
                    )
        finally:
            with contextlib.suppress(Exception):
                queue.put_nowait(None)

    async def _sse_event_generator(self) -> AsyncGenerator[str]:
        """Yield formatted SSE event frames."""
        client_id = f"sse-{uuid.uuid4().hex[:8]}"
        queue: asyncio.Queue[StreamEnvelope | None] = asyncio.Queue(
            maxsize=self._config.client_buffer_size
        )
        self._queues[client_id] = queue
        self.subscribe(client_id, "*")

        try:
            yield ": connected\n\n"
            while True:
                envelope = await queue.get()
                if envelope is None:
                    break
                payload = json.dumps(
                    {
                        "sequence": envelope.sequence,
                        "project": envelope.project,
                        "channel": envelope.channel,
                        "data": envelope.data,
                    }
                )
                yield f"data: {payload}\n\n"
        finally:
            self._disconnect_client(client_id)

    def _disconnect_client(self, client_id: str) -> None:
        """Unregister client and cleanup all its subscriptions."""
        self._queues.pop(client_id, None)
        for channel, subscribers in list(self._subscriptions.items()):
            subscribers.discard(client_id)
            if not subscribers:
                self._subscriptions.pop(channel, None)

    @override
    async def broadcast_update(
        self,
        project_name: str,
        channel_name: str,
        payload: dict[str, Any],
    ) -> None:
        """Broadcast an update to all subscribers of a project and channel.

        Args:
            project_name: Target project or subsystem name.
            channel_name: Target channel name.
            payload: Structured event data.
        """
        self._sequence += 1
        now = datetime.now(UTC).isoformat()
        cursor = f"{channel_name}:{self._sequence}:{now}"
        envelope = StreamEnvelope(
            sequence=self._sequence,
            timestamp=now,
            project=project_name,
            channel=channel_name,
            data=payload,
            cursor=cursor,
        )

        if channel_name not in self._event_buffer:
            self._event_buffer[channel_name] = deque(maxlen=100)
        self._event_buffer[channel_name].append(envelope)

        target_clients = set(self._subscriptions.get(channel_name, ())) | set(
            self._subscriptions.get("*", ())
        )

        for client_id in target_clients:
            q = self._queues.get(client_id)
            if q is not None:
                try:
                    q.put_nowait(envelope)
                except asyncio.QueueFull:
                    logger.warning(
                        "stream_slow_consumer_dropped",
                        client_id=client_id,
                    )
                    # Disconnect slow consumer cleanly
                    self._disconnect_client(client_id)

    @override
    def subscribe(self, client_id: str, channel: str) -> None:
        """Register a client subscription for a channel.

        Args:
            client_id: Client identifier.
            channel: Target channel name.
        """
        self._subscriptions.setdefault(channel, set()).add(client_id)

    @override
    def unsubscribe(self, client_id: str, channel: str) -> None:
        """Unregister a client subscription for a channel.

        Args:
            client_id: Client identifier.
            channel: Target channel name.
        """
        if channel in self._subscriptions:
            self._subscriptions[channel].discard(client_id)

    @override
    def get_active_connections_count(self) -> int:
        """Return the count of currently active streaming connections.

        Returns:
            Active connection count.
        """
        return len(self._queues)

    @override
    def get_events_after(
        self,
        channel: str,
        cursor: str,
    ) -> tuple[StreamEnvelope, ...]:
        """Retrieve missed events after a given cursor from the in-memory buffer.

        Args:
            channel: Target channel name.
            cursor: Cursor offset from previous envelope.

        Returns:
            Tuple of `StreamEnvelope` events occurring after the specified cursor.
        """
        buf = self._event_buffer.get(channel)
        if not buf:
            return ()
        if not cursor:
            return tuple(buf)
        found = False
        missed: list[StreamEnvelope] = []
        for env in buf:
            if found:
                missed.append(env)
            elif env.cursor == cursor:
                found = True
        return tuple(missed) if found else ()

    async def run_heartbeat(self) -> None:
        """Periodic background heartbeat task broadcasting ping envelopes."""
        try:
            while True:
                await asyncio.sleep(self._config.heartbeat_interval_s)
                await self.broadcast_update(
                    project_name="system",
                    channel_name="heartbeat",
                    payload={"type": "ping", "active_clients": len(self._queues)},
                )
        except asyncio.CancelledError:
            logger.debug("streams_heartbeat_cancelled")


# ---------------------------------------------------------------------------
# Feature Specification and Wiring
# ---------------------------------------------------------------------------

SPEC = FeatureSpec(
    name="gateway.streams",
    provides=frozenset({GATEWAY_STREAMS}),
    requires=frozenset({GATEWAY_APPLICATION}),
    optional=frozenset({GATEWAY_AUTHORIZATION}),
    description="WebSocket and SSE event streaming and channel subscriptions.",
)


class StreamsFeature:
    """Composition feature wiring for event stream gateway."""

    def __init__(self, config: StreamsConfig | None = None) -> None:
        """Initialize the feature with optional configuration.

        Args:
            config: Optional runtime configuration.
        """
        self._config = config or StreamsConfig()

    @property
    def spec(self) -> FeatureSpec:
        """Return the immutable feature specification."""
        return SPEC

    async def start(self, context: FeatureContext) -> None:
        """Start the streams feature and publish capability.

        Args:
            context: Feature composition context.
        """
        app_service = context.require(GATEWAY_APPLICATION)
        auth = context.optional(GATEWAY_AUTHORIZATION)
        service = EventStreamService(app_service, self._config, auth=auth)
        context.provide(GATEWAY_STREAMS, service)
        context.spawn(service.run_heartbeat())

    async def stop(self) -> None:
        """Stop feature and clean up resources."""


def feature() -> StreamsFeature:
    """Factory creating the default StreamsFeature.

    Returns:
        Configured feature instance.
    """
    return StreamsFeature()
