"""Host shell status, readiness, about, and recovery REST API endpoints.

Description:
    Exposes FastAPI routes for host readiness probes, shell status inspection,
    frontend application-loaded acknowledgement, platform provenance/version
    metadata, and persistence recovery reconciliation.

Purpose:
    FEAT-API-SHELL: Dedicated REST API routing for shell lifecycle and recovery.

Key Capabilities:
    - FR-API-SHELL-STATUS: HTTP routes for readiness, status, about, and app-loaded.
      Associated: `create_shell_router()`
      Logging: Emits DEBUG on /status, /readiness queries; INFO on /app-loaded, /about.
    - FR-API-SHELL-RECOVERY: HTTP route for persistence restart reconciliation.
      Associated: `create_recovery_router()`
      Logging: Emits DEBUG when recovery router initialized; INFO on reconciliation.

Python API Usage:
    ```python
    from app.api.shell import create_recovery_router, create_shell_router
    from app.host.settings import HostSettings

    shell_router = create_shell_router(HostSettings())
    recovery_router = create_recovery_router(lambda: {"recovered": True})
    ```

CLI Usage:
    Shell REST endpoints are mounted by the host bootstrap runtime:
    ```bash
    uv run python -m app.main
    ```
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from app.api.sessions import extract_bearer_token
from app.host.logging import get_logger
from app.host.response import StandardResponse

if TYPE_CHECKING:
    from collections.abc import Callable

    from app.host.bootstrap import HostRuntime
    from app.host.settings import HostSettings

__all__ = [
    "create_recovery_router",
    "create_shell_router",
]

logger = get_logger(__name__)


def create_shell_router(settings: HostSettings) -> APIRouter:
    """Create shell endpoints under the configured API prefix."""
    raw_prefix = settings.api_prefix.strip()
    prefix = "" if raw_prefix in ("", "/") else raw_prefix.rstrip("/")
    router = APIRouter(prefix=prefix)

    @router.get("/status")
    async def get_status(request: Request) -> JSONResponse:
        """Return general host status, CPU capacity, and runtime state."""
        rt: HostRuntime = request.app.state.runtime
        readiness = rt.get_readiness()
        logger.debug(
            "FR-API-SHELL-STATUS: Handling /status query.",
            extra={"fr_id": "FR-API-SHELL-STATUS"},
        )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "data": {
                    "state": readiness.state.value,
                    "host_instance_id": rt.host_instance_id,
                    "is_ready": readiness.is_ready,
                    "cpu_count": max(1, os.cpu_count() or 1),
                    "uptime_seconds": readiness.uptime_seconds,
                    "version": settings.version,
                    "reference_cohort": settings.reference_cohort,
                },
            },
        )

    @router.get("/readiness")
    async def get_readiness_endpoint(request: Request) -> JSONResponse:
        """Return the host readiness assessment snapshot."""
        rt: HostRuntime = request.app.state.runtime
        readiness = rt.get_readiness()
        logger.debug(
            "FR-API-SHELL-STATUS: Readiness endpoint evaluated: is_ready=%s",
            readiness.is_ready,
            extra={"fr_id": "FR-API-SHELL-STATUS"},
        )
        http_status = (
            status.HTTP_200_OK
            if readiness.is_ready
            else status.HTTP_503_SERVICE_UNAVAILABLE
        )
        return JSONResponse(
            status_code=http_status,
            content={
                "status": "success" if readiness.is_ready else "error",
                "data": readiness.model_dump(),
            },
        )

    @router.post("/app-loaded")
    async def post_app_loaded(request: Request) -> JSONResponse:
        """Acknowledge the browser shell frontend completion of load."""
        rt: HostRuntime = request.app.state.runtime
        token = extract_bearer_token(request.headers.get("authorization"))
        request.app.state.authentication.verify_session(token)
        rt.acknowledge_app_loaded()
        logger.info(
            "FR-API-SHELL-STATUS: Browser shell app-loaded received for host=%s",
            rt.host_instance_id,
            extra={"fr_id": "FR-API-SHELL-STATUS"},
        )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "data": {
                    "acknowledged": True,
                    "host_instance_id": rt.host_instance_id,
                },
            },
        )

    @router.get("/about")
    async def get_about(request: Request) -> JSONResponse:
        """Provide application identity, version, and clean-room provenance."""
        rt: HostRuntime = request.app.state.runtime
        logger.info(
            "FR-API-SHELL-STATUS: Delivering /about metadata.",
            extra={"fr_id": "FR-API-SHELL-STATUS"},
        )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "data": {
                    "application": "HaruQuantAI",
                    "title": settings.title,
                    "version": settings.version,
                    "reference_cohort": settings.reference_cohort,
                    "runtime": "CPython 3.14 (FastAPI)",
                    "disposition": "Clean-room Python host replacing JVM mechanics",
                    "host_instance_id": rt.host_instance_id,
                },
            },
        )

    return router


def create_recovery_router(reconcile: Callable[[], dict[str, Any]]) -> APIRouter:
    """Expose bootstrap recovery using the supplied lifecycle workflow."""
    router = APIRouter(prefix="/persistence/recovery", tags=["persistence"])

    @router.post("/reconcile", summary="Trigger restart recovery reconciliation")
    def reconcile_endpoint(request: Request) -> JSONResponse:
        """Run the bootstrap-owned recovery sequence."""
        response = StandardResponse.success(
            data=reconcile(),
            message="Recovery reconciliation completed.",
            request_id=request.headers.get("x-request-id"),
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=response.to_dict())

    logger.debug(
        "Recovery REST router initialized",
        extra={"fr_id": "FR-API-SHELL-RECOVERY"},
    )
    return router
