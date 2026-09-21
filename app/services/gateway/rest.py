"""Versioned REST API and OpenAPI resource exposure feature.

Feature:
    FEAT-GATEWAY-REST

Purpose:
    Provides versioned REST/OpenAPI resource routing, cursor pagination helpers,
    bounded DTO serialization, and asynchronous job receipt generation (HTTP 202)
    under capability `gateway.rest@1`.

Key capabilities:
    * Central `/api/v1` router assembly and OpenAPI schema generation.
    * 202 Accepted job receipt generation (`JobReceipt`).
    * Deterministic cursor-based pagination helper (`CursorPage`).

Python API usage:
    rest_gw = ctx.require(GATEWAY_REST)
    receipt = rest_gw.create_job_receipt(job_id="job-1", action="backtest")

CLI usage:
    uv run python -m tests.examples.05_gateway
"""

from __future__ import annotations

import base64
import json
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, TypeVar, override

from fastapi import APIRouter, Request

from app.contracts.gateway import (
    GATEWAY_APPLICATION,
    GATEWAY_PERSISTENCE,
    GATEWAY_REST,
    CursorPage,
    GatewayApplication,
    GatewayPersistenceService,
    JobReceipt,
)
from app.contracts.gateway import (
    RestGateway as IRestGateway,
)
from app.contracts.workspace import (
    WORKSPACE_JOBS,
    JobDefinition,
    JobService,
    WorkspaceError,
)
from app.kernel.feature import FeatureSpec
from app.kernel.logging import get_logger

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext

logger = get_logger(__name__)

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class RestConfig:
    """Runtime configuration for versioned REST gateway."""

    api_prefix: str = "/api/v1"
    default_page_limit: int = 50
    max_page_limit: int = 500

    def __post_init__(self) -> None:
        """Validate configuration limits."""
        if not self.api_prefix.startswith("/"):
            msg = f"api_prefix must start with '/'; got {self.api_prefix}"
            raise ValueError(msg)
        if self.default_page_limit <= 0:
            msg = f"default_page_limit must be > 0; got {self.default_page_limit}"
            raise ValueError(msg)
        if self.max_page_limit < self.default_page_limit:
            msg = (
                f"max_page_limit ({self.max_page_limit}) cannot be less than "
                f"default_page_limit ({self.default_page_limit})"
            )
            raise ValueError(msg)


# ---------------------------------------------------------------------------
# Service Implementation
# ---------------------------------------------------------------------------


class RestGatewayService(IRestGateway):
    """Implement the public RestGateway capability."""

    def __init__(
        self,
        app_service: GatewayApplication,
        config: RestConfig | None = None,
        persistence: GatewayPersistenceService | None = None,
        jobs: JobService | None = None,
    ) -> None:
        """Initialize the REST gateway service.

        Args:
            app_service: Underlying GatewayApplication supervisor.
            config: Optional runtime REST configuration.
            persistence: Optional persistence service for idempotency caching.
            jobs: Optional workspace jobs capability for job dispatch.
        """
        self._app_service = app_service
        self._config = config or RestConfig()
        self._persistence = persistence
        self._jobs = jobs
        self._router = APIRouter()
        self._setup_core_routes()

        # Mount the core router onto the FastAPI application
        self._app_service.mount_router(self._config.api_prefix, self._router)

    def _setup_core_routes(self) -> None:
        """Register built-in REST resource discovery and job endpoints."""

        @self._router.get("/openapi-schema", tags=["Schema"])
        async def get_schema() -> dict[str, Any]:
            """Return the active OpenAPI specification document."""
            return self.get_openapi_schema()

        @self._router.post("/jobs", status_code=202, tags=["Jobs"])
        async def submit_job_endpoint(
            payload: dict[str, Any],
            request: Request,
        ) -> dict[str, Any]:
            """Submit a background job with optional idempotency key."""
            action = str(payload.get("action", "unknown"))
            params = dict(payload.get("params", {}))
            idempotency_key = request.headers.get("idempotency-key")
            correlation_id = request.headers.get("x-correlation-id")

            def handler() -> tuple[int, dict[str, Any]]:
                receipt = self.submit_job(action, params, correlation_id)
                return 202, {
                    "job_id": receipt.job_id,
                    "status": receipt.status,
                    "status_url": receipt.status_url,
                    "stream_url": receipt.stream_url,
                    "correlation_id": receipt.correlation_id,
                }

            _status_code, result = self.execute_idempotent_mutation(
                idempotency_key, handler
            )
            return dict(result)

    @override
    def register_resource(self, resource: Any) -> None:
        """Register a REST resource router with the gateway.

        Args:
            resource: Sub-router or APIRouter instance to register.

        Raises:
            TypeError: If resource is not an APIRouter instance.
        """
        if not isinstance(resource, APIRouter):
            msg = (
                f"Resource must be an APIRouter instance; got {type(resource).__name__}"
            )
            raise TypeError(msg)
        self._router.include_router(resource)
        logger.info("rest_resource_registered", routes_count=len(resource.routes))

    @override
    def get_openapi_schema(self) -> dict[str, Any]:
        """Return the complete OpenAPI schema for registered REST resources.

        Returns:
            OpenAPI specification dictionary.
        """
        app = self._app_service.get_app()
        return app.openapi()

    @override
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
        cid = correlation_id or f"corr-{uuid.uuid4().hex[:12]}"
        prefix = self._config.api_prefix.rstrip("/")
        return JobReceipt(
            job_id=job_id,
            status="accepted",
            status_url=f"{prefix}/jobs/{job_id}",
            stream_url="/websocket/updates",
            correlation_id=cid,
        )

    @override
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
        cid = correlation_id or f"corr-{uuid.uuid4().hex[:12]}"
        job_id = f"job-{uuid.uuid4().hex[:8]}"

        if self._jobs is not None:
            try:
                definition = JobDefinition(
                    job_id=job_id,
                    group_id=str((params or {}).get("group_id", "default")),
                    operation=action,
                    priority=int((params or {}).get("priority", 0)),
                    resource_class=str((params or {}).get("resource_class", "default")),
                    config_hash=str((params or {}).get("config_hash", "none")),
                    payload=dict(params or {}),
                    created_at_utc=datetime.now(UTC),
                )
                self._jobs.create_job(definition)
                logger.info("job_dispatched_to_workspace", job_id=job_id, action=action)
            except (WorkspaceError, ValueError, RuntimeError) as exc:
                logger.warning("job_dispatch_failed", action=action, error=str(exc))

        return self.create_job_receipt(
            job_id=job_id,
            action=action,
            correlation_id=cid,
        )

    @override
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
        if not idempotency_key or self._persistence is None:
            return handler()

        cached = self._persistence.get_idempotency_response(idempotency_key)
        if cached is not None:
            status_code, body_str = cached
            try:
                parsed = json.loads(body_str)
            except json.JSONDecodeError, ValueError:
                parsed = body_str
            logger.info("idempotency_cache_hit", key=idempotency_key)
            return status_code, parsed

        status_code, response_data = handler()
        body_str = (
            json.dumps(response_data)
            if isinstance(response_data, (dict, list))
            else str(response_data)
        )
        self._persistence.record_idempotency_key(
            key=idempotency_key,
            status_code=status_code,
            response_body=body_str,
        )
        logger.info("idempotency_key_recorded", key=idempotency_key)
        return status_code, response_data

    @override
    def paginate(
        self,
        items: Sequence[T],
        cursor: str | None = None,
        limit: int | None = None,
    ) -> CursorPage[T]:
        """Wrap a sequence of items in a cursor-paginated response.

        Args:
            items: Ordered collection of items.
            cursor: Optional opaque cursor offset.
            limit: Optional item limit per page.

        Returns:
            Formed `CursorPage[T]`.
        """
        eff_limit = min(
            limit or self._config.default_page_limit,
            self._config.max_page_limit,
        )
        if eff_limit <= 0:
            eff_limit = self._config.default_page_limit

        start_idx = 0
        if cursor:
            try:
                decoded = base64.b64decode(cursor.encode("utf-8")).decode("utf-8")
                start_idx = max(0, int(decoded))
            except ValueError, UnicodeDecodeError:
                start_idx = 0

        total = len(items)
        end_idx = min(start_idx + eff_limit, total)
        page_items = tuple(items[start_idx:end_idx])

        next_cursor = None
        if end_idx < total:
            next_cursor = base64.b64encode(str(end_idx).encode("utf-8")).decode("utf-8")

        return CursorPage(
            items=page_items,
            cursor=cursor,
            next_cursor=next_cursor,
            total_items=total,
            limit=eff_limit,
        )


# ---------------------------------------------------------------------------
# Feature Specification and Wiring
# ---------------------------------------------------------------------------

SPEC = FeatureSpec(
    name="gateway.rest",
    provides=frozenset({GATEWAY_REST}),
    requires=frozenset({GATEWAY_APPLICATION}),
    optional=frozenset({GATEWAY_PERSISTENCE, WORKSPACE_JOBS}),
    description="Versioned REST/OpenAPI resources and cursor pagination.",
)


class RestFeature:
    """Composition feature wiring for REST gateway."""

    def __init__(self, config: RestConfig | None = None) -> None:
        """Initialize the feature with optional configuration.

        Args:
            config: Optional runtime configuration.
        """
        self._config = config or RestConfig()

    @property
    def spec(self) -> FeatureSpec:
        """Return the immutable feature specification."""
        return SPEC

    async def start(self, context: FeatureContext) -> None:
        """Start the REST feature and publish capability.

        Args:
            context: Feature composition context.
        """
        app_service = context.require(GATEWAY_APPLICATION)
        persistence = context.optional(GATEWAY_PERSISTENCE)
        jobs = context.optional(WORKSPACE_JOBS)
        service = RestGatewayService(
            app_service=app_service,
            config=self._config,
            persistence=persistence,
            jobs=jobs,
        )
        context.provide(GATEWAY_REST, service)

    async def stop(self) -> None:
        """Stop feature and clean up resources."""


def feature() -> RestFeature:
    """Factory creating the default RestFeature.

    Returns:
        Configured feature instance.
    """
    return RestFeature()
