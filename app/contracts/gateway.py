"""Public contracts, protocols, DTOs, and capabilities for the Gateway domain."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

from app.kernel.capability import Capability

if TYPE_CHECKING:
    from fastapi import FastAPI


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class GatewayError(Exception):
    """Base exception for all gateway domain operations."""


class ServerStartupError(GatewayError):
    """Raised when the HTTP server fails to initialize or bind."""


class AuthenticationError(GatewayError):
    """Raised when request authentication fails."""


class RateLimitError(GatewayError):
    """Raised when request limits or streaming buffers are exceeded."""


class InvalidPayloadError(GatewayError):
    """Raised when a request payload fails transport validation."""


class ProblemDetailsError(GatewayError):
    """Transport error wrapping an RFC 7807 problem details document."""

    def __init__(self, problem: ProblemDetails) -> None:
        """Initialize problem details error with structured document.

        Args:
            problem: RFC 7807 structured problem details.
        """
        super().__init__(f"[{problem.status}] {problem.title}: {problem.detail}")
        self.problem = problem


# ---------------------------------------------------------------------------
# Transport DTOs
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ServerInfo:
    """Snapshot of active HTTP server status."""

    host: str
    port: int
    running: bool
    active_routes: tuple[str, ...]
    loopback_only: bool = True


@dataclass(frozen=True, slots=True)
class AuthContext:
    """Authentication and identity context for an inbound request."""

    client_id: str
    authenticated: bool
    is_loopback: bool
    scopes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ProblemDetails:
    """Standard RFC 7807 Problem Details document."""

    type: str
    title: str
    status: int
    detail: str
    instance: str | None = None
    correlation_id: str = ""
    errors: tuple[dict[str, Any], ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        """Serialize problem details to a JSON-compatible dictionary.

        Returns:
            Dictionary following RFC 7807 application/problem+json schema.
        """
        result: dict[str, Any] = {
            "type": self.type,
            "title": self.title,
            "status": self.status,
            "detail": self.detail,
        }
        if self.instance:
            result["instance"] = self.instance
        if self.correlation_id:
            result["correlation_id"] = self.correlation_id
        if self.errors:
            result["errors"] = list(self.errors)
        return result


@dataclass(frozen=True, slots=True)
class JobReceipt:
    """Immediate HTTP 202 Accepted receipt for long-running workflows."""

    job_id: str
    status: str
    status_url: str
    stream_url: str
    correlation_id: str


@dataclass(frozen=True, slots=True)
class StreamEnvelope:
    """Ordered event envelope for real-time WebSocket and SSE delivery."""

    sequence: int
    timestamp: str
    project: str
    channel: str
    data: dict[str, Any]
    cursor: str | None = None


@dataclass(frozen=True, slots=True)
class CursorPage[T]:
    """Generic cursor-paginated collection wrapper."""

    items: tuple[T, ...]
    cursor: str | None
    next_cursor: str | None
    total_items: int | None = None
    limit: int = 50


@dataclass(frozen=True, slots=True)
class AutomationResult:
    """Outcome receipt from a headless CLI or batch automation command."""

    command: str
    success: bool
    output: str
    error: str | None = None


# ---------------------------------------------------------------------------
# Protocols
# ---------------------------------------------------------------------------


class GatewayApplication(Protocol):
    """Public protocol for the FastAPI ASGI application and lifecycle."""

    def get_server_info(self) -> ServerInfo:
        """Return runtime status information about the HTTP server.

        Returns:
            Current `ServerInfo` snapshot.
        """
        ...

    def get_app(self) -> FastAPI:
        """Return the underlying ASGI FastAPI application.

        Returns:
            The FastAPI application instance.
        """
        ...

    def mount_router(
        self,
        prefix: str,
        router: Any,
        tags: Sequence[str] | None = None,
    ) -> None:
        """Mount a versioned router onto the application.

        Args:
            prefix: URL prefix (e.g. '/api/v1').
            router: APIRouter instance to mount.
            tags: Optional OpenAPI tags for documentation.
        """
        ...

    def mount_static(self, path: str, directory: Path) -> None:
        """Mount a local directory for serving static web assets.

        Args:
            path: URL path mount point (e.g. '/static').
            directory: Local filesystem directory containing static files.
        """
        ...

    async def serve(self) -> None:
        """Execute the ASGI server loop asynchronously."""
        ...

    def stop(self) -> None:
        """Signal the ASGI server to stop gracefully."""
        ...


# Legacy alias
HttpServerService = GatewayApplication


class RestGateway(Protocol):
    """Public protocol for versioned REST and OpenAPI resource exposure."""

    def register_resource(self, resource: Any) -> None:
        """Register a REST resource router with the gateway.

        Args:
            resource: Resource definition or router.
        """
        ...

    def get_openapi_schema(self) -> dict[str, Any]:
        """Return the complete OpenAPI schema for registered REST resources.

        Returns:
            OpenAPI specification dictionary.
        """
        ...

    def create_job_receipt(
        self,
        job_id: str,
        action: str,
        correlation_id: str | None = None,
    ) -> JobReceipt:
        """Create an HTTP 202 Accepted job receipt.

        Args:
            job_id: Unique job identifier.
            action: Action or operation name.
            correlation_id: Optional correlation ID (generated if omitted).

        Returns:
            Formed `JobReceipt`.
        """
        ...

    def paginate(
        self,
        items: Sequence[Any],
        cursor: str | None = None,
        limit: int | None = None,
    ) -> CursorPage[Any]:
        """Wrap a sequence of items in a cursor-paginated response.

        Args:
            items: Ordered collection of items.
            cursor: Optional opaque cursor offset.
            limit: Optional item limit per page.

        Returns:
            Formed `CursorPage[Any]`.
        """
        ...

    def execute_idempotent_mutation(
        self,
        idempotency_key: str | None,
        handler: Any,
    ) -> Any:
        """Execute a state-modifying action with idempotency caching if key is provided.

        Args:
            idempotency_key: Optional unique idempotency key from header.
            handler: Callable returning tuple of (status_code,
                response_body_dict_or_str).

        Returns:
            Tuple of (status_code, response_data).
        """
        ...

    def submit_job(
        self,
        action: str,
        params: dict[str, Any] | None = None,
        correlation_id: str | None = None,
    ) -> JobReceipt:
        """Submit a job to workspace job engine if available, returning 202 receipt.

        Args:
            action: Action or operation name.
            params: Optional job parameters.
            correlation_id: Optional correlation tracking ID.

        Returns:
            Formed `JobReceipt`.
        """
        ...


class EventStreamGateway(Protocol):
    """Public protocol for WebSocket and optional SSE event streaming."""

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
        ...

    def subscribe(self, client_id: str, channel: str) -> None:
        """Register a client subscription for a channel.

        Args:
            client_id: Client identifier.
            channel: Target channel name.
        """
        ...

    def unsubscribe(self, client_id: str, channel: str) -> None:
        """Unregister a client subscription for a channel.

        Args:
            client_id: Client identifier.
            channel: Target channel name.
        """
        ...

    def get_active_connections_count(self) -> int:
        """Return the count of currently active streaming connections.

        Returns:
            Active connection count.
        """
        ...

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
        ...


class GatewayAuthorization(Protocol):
    """Public protocol for transport authentication and network origin policy."""

    def authenticate_request(
        self,
        headers: Mapping[str, str],
        client_host: str,
    ) -> AuthContext:
        """Validate request headers and origin against transport security policy.

        Args:
            headers: HTTP request headers dictionary.
            client_host: Client IP address or hostname.

        Returns:
            Validated `AuthContext`.

        Raises:
            AuthenticationError: If credentials or origin fail validation.
        """
        ...

    def is_remote_access_enabled(self) -> bool:
        """Return whether remote (non-loopback) connections are permitted.

        Returns:
            True if remote access is enabled, False if loopback-only.
        """
        ...

    def set_remote_access(self, enabled: bool) -> None:
        """Toggle remote (non-loopback) access permission.

        Args:
            enabled: Desired remote access status.
        """
        ...

    def issue_token(
        self,
        name: str,
        scopes: Sequence[str] = ("read",),
    ) -> str:
        """Generate, persist, and return a new cryptographically secure token.

        Args:
            name: Human-readable token name or description.
            scopes: Allowed scopes.

        Returns:
            Plaintext token string (to be shown once to the user).
        """
        ...


class ProblemMapper(Protocol):
    """Public protocol for mapping exceptions to RFC 7807 problem details."""

    def to_problem_details(
        self,
        exc: Exception,
        correlation_id: str | None = None,
        path: str | None = None,
    ) -> ProblemDetails:
        """Convert an exception into a sanitized RFC 7807 ProblemDetails document.

        Args:
            exc: Exception to map.
            correlation_id: Optional correlation tracking ID.
            path: Optional request path.

        Returns:
            Sanitized `ProblemDetails`.
        """
        ...

    def register_handlers(self, app: FastAPI) -> None:
        """Register standard exception handlers on a FastAPI application.

        Args:
            app: FastAPI application instance.
        """
        ...


class CommandAutomationService(Protocol):
    """Public protocol for headless CLI and batch script automation."""

    async def execute_command(
        self,
        command_str: str,
    ) -> AutomationResult:
        """Parse and execute a single CLI command string.

        Args:
            command_str: Command string (e.g. '-project action=start name=Builder').

        Returns:
            `AutomationResult` describing execution outcome.
        """
        ...

    async def run_batch_file(
        self,
        file_path: Path,
    ) -> Sequence[AutomationResult]:
        """Execute a batch script file containing one command per line.

        Args:
            file_path: Path to the commands text file.

        Returns:
            Sequence of `AutomationResult` items in execution order.
        """
        ...


class GatewayPersistenceService(Protocol):
    """Public protocol for durable state operations in the Gateway domain."""

    def get_setting(self, key: str) -> str | None:
        """Retrieve a stored setting value.

        Args:
            key: Setting key name.

        Returns:
            Stored value string, or None if not found.
        """
        ...

    def set_setting(self, key: str, value: str) -> None:
        """Persist a setting key-value pair.

        Args:
            key: Setting key name.
            value: Setting value.
        """
        ...

    def store_token(self, token: str, name: str) -> None:
        """Store a hashed API token.

        Args:
            token: Plaintext token to hash and store.
            name: Human-readable token name or description.
        """
        ...

    def verify_token(self, token: str) -> bool:
        """Verify if a token hash exists and is active.

        Args:
            token: Plaintext token to verify.

        Returns:
            True if token is valid and active, False otherwise.
        """
        ...

    def record_idempotency_key(
        self,
        key: str,
        status_code: int,
        response_body: str,
        expire_seconds: int = 86400,
    ) -> bool:
        """Record an idempotency key and its response.

        Args:
            key: Idempotency key.
            status_code: HTTP status code.
            response_body: Serialized response body.
            expire_seconds: Time-to-live in seconds.

        Returns:
            True if newly inserted, False if key already exists.
        """
        ...

    def get_idempotency_response(self, key: str) -> tuple[int, str] | None:
        """Retrieve a cached idempotency response if still valid.

        Args:
            key: Idempotency key.

        Returns:
            Tuple of (status_code, response_body) or None if absent/expired.
        """
        ...

    def purge_expired_idempotency(self, retention_seconds: int = 86400) -> int:
        """Purge expired idempotency keys older than retention threshold.

        Args:
            retention_seconds: Maximum age in seconds.

        Returns:
            Count of deleted rows.
        """
        ...


# ---------------------------------------------------------------------------
# Capability Keys
# ---------------------------------------------------------------------------

GATEWAY_APPLICATION: Capability[GatewayApplication] = Capability(
    "gateway.application@1"
)
GATEWAY_REST: Capability[RestGateway] = Capability("gateway.rest@1")
GATEWAY_STREAMS: Capability[EventStreamGateway] = Capability("gateway.streams@1")
GATEWAY_AUTHORIZATION: Capability[GatewayAuthorization] = Capability(
    "gateway.authorization@1"
)
GATEWAY_ERRORS: Capability[ProblemMapper] = Capability("gateway.errors@1")
GATEWAY_AUTOMATION: Capability[CommandAutomationService] = Capability(
    "gateway.automation@1"
)
GATEWAY_PERSISTENCE: Capability[GatewayPersistenceService] = Capability(
    "gateway.persistence@1"
)

# Backward-compatible capability alias
HTTP_SERVER: Capability[GatewayApplication] = Capability("gateway.http_server@1")

__all__ = [
    "GATEWAY_APPLICATION",
    "GATEWAY_AUTHORIZATION",
    "GATEWAY_AUTOMATION",
    "GATEWAY_ERRORS",
    "GATEWAY_PERSISTENCE",
    "GATEWAY_REST",
    "GATEWAY_STREAMS",
    "HTTP_SERVER",
    "AuthContext",
    "AuthenticationError",
    "AutomationResult",
    "CommandAutomationService",
    "CursorPage",
    "EventStreamGateway",
    "GatewayApplication",
    "GatewayAuthorization",
    "GatewayError",
    "GatewayPersistenceService",
    "HttpServerService",
    "InvalidPayloadError",
    "JobReceipt",
    "ProblemDetails",
    "ProblemDetailsError",
    "ProblemMapper",
    "RateLimitError",
    "RestGateway",
    "ServerInfo",
    "ServerStartupError",
    "StreamEnvelope",
]
