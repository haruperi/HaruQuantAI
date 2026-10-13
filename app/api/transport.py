"""Host event streaming and transport REST API endpoints.

Description:
    Exposes FastAPI routes for streaming server-sent events (SSE), querying
    event channel snapshots, publishing real-time platform telemetry events,
    and mounting legacy session authentication endpoints.

Purpose:
    FEAT-API-TRANSPORT: Dedicated REST API routing for SSE event streams and
    real-time event bus integration.

Key Capabilities:
    - FR-API-TRANSPORT-STREAM: Server-sent events streaming for authorized subscribers.
      Associated: `create_transport_router()`, `TransportService.handle_events_stream()`
      Logging: Emits DEBUG when event stream starts; disconnect telemetry on completion.
    - FR-API-TRANSPORT-PUBLISH: Event publication and snapshot inspection.
      Associated: `handle_publish()`, `handle_snapshot()`
      Logging: Emits DEBUG on event published and snapshots retrieved.

Python API Usage:
    ```python
    from app.api.transport import create_transport_router
    from app.host.transport import EventBus

    bus = EventBus()
    router = create_transport_router(event_bus=bus)
    ```

CLI Usage:
    Transport REST endpoints are mounted by the host bootstrap runtime:
    ```bash
    uv run python -m app.main
    ```
"""

from __future__ import annotations

from fastapi import APIRouter, Query, Request, Response, status
from fastapi.responses import JSONResponse, StreamingResponse

from app.api.sessions import create_auth_router
from app.host.logging import get_logger
from app.host.response import StandardError, StandardResponse
from app.host.session import HostAuthentication, SessionTokenManager
from app.host.settings import HostSettings
from app.host.transport import (
    EventBus,
    PublishEventRequest,
    get_global_event_bus,
    get_global_token_manager,
    sse_event_generator,
)

__all__ = [
    "TransportService",
    "create_transport_router",
]

logger = get_logger(__name__)


class TransportService:
    """Coordinates authentication and event routing for HTTP transport."""

    def __init__(self, bus: EventBus, tokens: SessionTokenManager) -> None:
        self.bus = bus
        self.tokens = tokens

    def resolve_token(self, request: Request, token_query: str | None) -> str | None:
        """Extract token from Authorization Bearer header or query parameter."""
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.lower().startswith("bearer "):
            return auth_header[7:].strip()
        if token_query and token_query.strip():
            return token_query.strip()
        return None

    async def handle_events_stream(
        self,
        request: Request,
        channels: str = Query(
            default="*", description="Comma-separated channel filter"
        ),
        since_cursor: int | None = Query(
            default=None, description="Replay starting after this cursor"
        ),
        token: str | None = Query(
            default=None, description="Optional bearer token in query"
        ),
        limit: int | None = Query(
            default=None, description="Optional maximum number of events to receive"
        ),
    ) -> Response:
        """Stream real-time server-sent events for authorized subscribers."""
        req_id = request.headers.get("x-request-id")
        resolved = self.resolve_token(request, token)
        if not resolved or not self.tokens.is_valid(resolved):
            err = StandardError(
                code="UNAUTHORIZED",
                message="Host session required or expired.",
            )
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=StandardResponse.failure(
                    message="Unauthorized.",
                    error=err,
                    request_id=req_id,
                ).to_dict(),
            )

        last_id = request.headers.get("last-event-id")
        effective_cursor = since_cursor
        if effective_cursor is None and last_id and last_id.isdigit():
            effective_cursor = int(last_id)

        parsed_channels = [c.strip() for c in channels.split(",") if c.strip()]
        if not parsed_channels:
            parsed_channels = ["*"]

        return StreamingResponse(
            sse_event_generator(
                event_bus=self.bus,
                channels=parsed_channels,
                since_cursor=effective_cursor,
                request=request,
                limit=limit,
                session_valid=lambda: self.tokens.is_valid(resolved),
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    async def handle_publish(
        self, event_in: PublishEventRequest, request: Request
    ) -> JSONResponse:
        """Publish an event to the host event bus."""
        req_id = request.headers.get("x-request-id")
        event = self.bus.publish(
            channel=event_in.channel,
            event_type=event_in.event_type,
            payload=event_in.payload,
        )
        resp = StandardResponse.success(
            data=event.model_dump(),
            message="Event published successfully.",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    async def handle_snapshot(
        self,
        request: Request,
        channel: str = Query(default="*", description="Target channel name"),
        since_cursor: int | None = Query(
            default=None, description="Cursor lower bound"
        ),
        limit: int = Query(default=100, ge=1, le=1000),
    ) -> JSONResponse:
        """Query channel snapshot and retained history."""
        req_id = request.headers.get("x-request-id")
        snapshot = self.bus.get_snapshot(
            channel=channel, since_cursor=since_cursor, limit=limit
        )
        resp = StandardResponse.success(
            data=snapshot.model_dump(),
            message="Snapshot retrieved successfully.",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())


def create_transport_router(
    event_bus: EventBus | None = None,
    token_manager: SessionTokenManager | None = None,
) -> APIRouter:
    """Create FastAPI router exposing auth and event transport endpoints."""
    bus = event_bus if event_bus is not None else get_global_event_bus()
    tokens = token_manager if token_manager is not None else get_global_token_manager()
    service = TransportService(bus, tokens)
    router = APIRouter(tags=["transport"])

    authentication = tokens.authentication or HostAuthentication(
        HostSettings(), tokens.manager
    )
    router.include_router(create_auth_router(authentication))
    router.add_api_route("/events", service.handle_events_stream, methods=["GET"])
    router.add_api_route("/events/publish", service.handle_publish, methods=["POST"])
    router.add_api_route("/events/snapshot", service.handle_snapshot, methods=["GET"])

    logger.debug(
        "create_transport_router composed",
        extra={
            "requirement": "FR-HOST-TRANSPORT-REST-PROJECTION",
            "fr_id": "FR-HOST-TRANSPORT-REST-PROJECTION",
        },
    )
    return router
