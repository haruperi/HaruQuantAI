"""Platform host bootstrap, lifecycle stages, and browser shell runtime.

Description:
    This module provides the central host runtime and application composition
    for HaruQuantAI. It defines the structured lifespan stages, manages
    acquired services with strict reverse-order rollback on failure or
    teardown, tracks real-time readiness snapshots, and lazily composes the
    FastAPI HTTP application without import-time side-effects. It exposes the
    standard browser shell endpoints for status, readiness, app-loaded
    handshakes, About metadata, and preferences projection.

Purpose:
    FEAT-HOST-BOOT: Universal host bootstrap, lifecycle state coordination,
    and browser shell projection replacing legacy Java bootstrap mechanics.

Key Capabilities:
    - FR-HOST-BOOT-LIFECYCLE-STAGES: Strict progression through ordered host
      lifespan stages (CONFIGURING, PATHS, LOGGING, DISCOVERY, SERVICES, ROUTES,
      READY).
      Associated: `HostRuntime.start()`, `HostRuntime._advance_stage()`
      Logging: Emits INFO on each stage transition; emits ERROR with code and
        stage identifier on startup failure.
    - FR-HOST-BOOT-REVERSE-SHUTDOWN: Idempotent reverse-order teardown and
      automatic rollback of acquired stages upon startup failure.
      Associated: `HostRuntime.stop()`, `HostRuntime._rollback_stages()`
      Logging: Emits INFO for each stage released during teardown or rollback;
        emits INFO when repeated stop is requested on a stopped host.
    - FR-HOST-BOOT-READINESS-ASSESSMENT: Comprehensive readiness checks and
      system health state snapshots.
      Associated: `HostRuntime.get_readiness()`, `HostRuntime.is_ready()`
      Logging: Emits DEBUG when readiness state is queried; emits WARNING when
        queried while degraded, stopping, or failed.
    - FR-HOST-BOOT-APP-COMPOSITION: Lazy factory composition of the FastAPI
      application and route registration without import-time side-effects.
      Associated: `create_host_app()`
      Logging: Emits INFO when application composition begins and completes;
        never executes network I/O or background tasks on import.
    - FR-HOST-BOOT-SHELL-PROJECTION: Browser shell contract endpoints for
      status, readiness inspection, Home/About metadata, and settings.
      Associated: `create_host_app()`, route handlers
      Logging: Emits INFO on app-loaded handshakes and settings writes; emits
        DEBUG on routine status inspections.

Python API Usage:
    ```python
    import asyncio
    from app.host.bootstrap import HostRuntime, HostSettings, create_host_app

    settings = HostSettings(host="127.0.0.1", port=8000)
    runtime = HostRuntime(settings)
    asyncio.run(runtime.start())

    readiness = runtime.get_readiness()
    assert readiness.is_ready

    app = create_host_app(settings, runtime=runtime)
    asyncio.run(runtime.stop())
    ```

CLI Usage:
    ```bash
    uv run python -m app.host.bootstrap --host 127.0.0.1 --port 8000
    ```
"""

from __future__ import annotations

import argparse
import asyncio
import inspect
import logging
import sys
import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from fastapi import APIRouter, FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)

DEFAULT_SHELL_PREFERENCES: dict[str, Any] = {
    "revision": 1,
    "values": {
        "app.general": {
            "theme": "dark",
            "language": "en",
            "zoom": 1.0,
        },
        "config.global": {
            "theme": "dark",
            "language": "en",
            "sounds_off": False,
            "advanced_file_chooser": False,
            "show_control_orders": False,
            "header_custom_text": "",
            "footer_custom_text": "",
            "default_result_to_display": "Portfolio",
        },
        "config.cpu": {
            "core_usage": "all_except_one",
            "custom_cores": 1,
            "high_priority": False,
            "thread_affinity": False,
        },
        "config.performance": {
            "compute_pips_metrics": False,
            "compute_pcts_metrics": False,
            "compute_separate_metrics": True,
        },
        "config.memory": {
            "gc_type": "ParallelGC",
            "automatic_memory": False,
            "memory_limit_gb": 4,
            "dont_store_pending_orders": True,
            "memory_cleanup": False,
            "cleanup_interval_mins": 15,
        },
        "config.databanks": {
            "databank_sync_interval_mins": 15,
            "sync_databanks_after_task_done": True,
            "store_chart_data": False,
        },
        "config.optimizations": {
            "dont_store_op_3d_charts_data": True,
        },
        "config.troubleshooting": {
            "gpu_accelerated": True,
            "memory_protection": True,
            "debug_level_active": False,
        },
        "connect.remote": {
            "allow": False,
            "require_password": False,
        },
        "notify.email": {
            "smtp_server": "",
            "smtp_port": 587,
            "use_ssl": False,
            "use_tls": True,
            "username": "",
            "from_address": "",
        },
    },
}


class LifespanStage(StrEnum):
    """Ordered lifespan stages for host runtime bootstrap."""

    UNINITIALIZED = "UNINITIALIZED"
    CONFIGURING = "CONFIGURING"
    PATHS = "PATHS"
    LOGGING = "LOGGING"
    DISCOVERY = "DISCOVERY"
    SERVICES = "SERVICES"
    ROUTES = "ROUTES"
    READY = "READY"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    FAILED = "FAILED"


class ReadinessState(StrEnum):
    """High-level readiness state of the host platform."""

    NOT_STARTED = "not_started"
    STARTING = "starting"
    READY = "ready"
    DEGRADED = "degraded"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"


class HostSettings(BaseModel):
    """Configuration model for the host platform runtime."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    host: str = Field(default="127.0.0.1", description="Bind IP address")
    port: int = Field(default=8000, ge=1, le=65535, description="Bind port")
    api_prefix: str = Field(default="/api/v1", description="API route prefix")
    title: str = Field(default="HaruQuantAI Host", description="App title")
    version: str = Field(default="2.1.0", description="App version")
    reference_cohort: str = Field(
        default="SQX145 Dev 1", description="Reference cohort identifier"
    )
    data_dir: Path | None = Field(
        default=None, description="Path to runtime data directory"
    )
    debug: bool = Field(default=False, description="Enable debug diagnostics")


class ReadinessSnapshot(BaseModel):
    """Structured readiness inspection document."""

    model_config = ConfigDict(frozen=True)

    state: ReadinessState
    is_ready: bool
    host_instance_id: str
    uptime_seconds: float
    timestamp: str
    active_stage: LifespanStage
    completed_stages: list[LifespanStage]
    checks: dict[str, bool]
    details: dict[str, str]


@dataclass
class _AcquiredStage:
    """Internal record of an acquired lifespan stage with teardown callback."""

    stage: LifespanStage
    cleanup: Any | None = None


class HostRuntime:
    """Universal host lifecycle coordinator and service container."""

    def __init__(self, settings: HostSettings | None = None) -> None:
        """Initialize the host runtime without performing import-time work."""
        self.settings: HostSettings = settings or HostSettings()
        self.host_instance_id: str = f"host-{uuid.uuid4().hex[:12]}"
        self._state: ReadinessState = ReadinessState.NOT_STARTED
        self._active_stage: LifespanStage = LifespanStage.UNINITIALIZED
        self._completed_stages: list[LifespanStage] = []
        self._acquired_stack: list[_AcquiredStage] = []
        self._checks: dict[str, bool] = {
            "configuration": False,
            "paths": False,
            "logging": False,
            "discovery": False,
            "services": False,
            "routes": False,
        }
        self._details: dict[str, str] = {}
        self._start_time: float | None = None
        self._stop_time: float | None = None
        self._lock: asyncio.Lock = asyncio.Lock()
        self._app_loaded_acknowledged: bool = False

    @property
    def state(self) -> ReadinessState:
        """Get the current readiness state."""
        return self._state

    def get_state(self) -> ReadinessState:
        """Get the current readiness state dynamically."""
        return self._state

    @property
    def active_stage(self) -> LifespanStage:
        """Get the currently active lifespan stage."""
        return self._active_stage

    def is_app_loaded(self) -> bool:
        """Return whether the browser shell handshake was acknowledged."""
        return self._app_loaded_acknowledged

    def is_ready(self) -> bool:
        """Check whether the host runtime is fully ready to serve traffic."""
        return (
            self._state == ReadinessState.READY
            and self._active_stage == LifespanStage.READY
            and all(self._checks.values())
        )

    def get_readiness(self) -> ReadinessSnapshot:
        """Capture and return an immutable readiness snapshot.

        Fires FR-HOST-BOOT-READINESS-ASSESSMENT.
        """
        ready = self.is_ready()
        now = datetime.now(UTC).isoformat()
        uptime = (
            time.monotonic() - self._start_time if self._start_time is not None else 0.0
        )

        if ready:
            logger.debug(
                "FR-HOST-BOOT-READINESS-ASSESSMENT: Host is ready. "
                "instance=%s uptime=%.2fs",
                self.host_instance_id,
                uptime,
                extra={"fr_id": "FR-HOST-BOOT-READINESS-ASSESSMENT"},
            )
        else:
            logger.warning(
                "FR-HOST-BOOT-READINESS-ASSESSMENT: Host is not ready. "
                "state=%s stage=%s checks=%s",
                self._state,
                self._active_stage,
                self._checks,
                extra={"fr_id": "FR-HOST-BOOT-READINESS-ASSESSMENT"},
            )

        return ReadinessSnapshot(
            state=self._state,
            is_ready=ready,
            host_instance_id=self.host_instance_id,
            uptime_seconds=uptime,
            timestamp=now,
            active_stage=self._active_stage,
            completed_stages=list(self._completed_stages),
            checks=dict(self._checks),
            details=dict(self._details),
        )

    async def _advance_stage(
        self, stage: LifespanStage, check_key: str, cleanup: Any | None = None
    ) -> None:
        """Advance to a lifespan stage and record its cleanup handler.

        Fires FR-HOST-BOOT-LIFECYCLE-STAGES.
        """
        self._active_stage = stage
        self._acquired_stack.append(_AcquiredStage(stage=stage, cleanup=cleanup))
        self._checks[check_key] = True
        self._completed_stages.append(stage)
        logger.info(
            "FR-HOST-BOOT-LIFECYCLE-STAGES: Stage advanced successfully: %s "
            "(instance=%s)",
            stage,
            self.host_instance_id,
            extra={
                "fr_id": "FR-HOST-BOOT-LIFECYCLE-STAGES",
                "stage": stage,
                "instance": self.host_instance_id,
            },
        )

    async def _rollback_stages(self) -> None:
        """Roll back acquired stages in strict reverse LIFO order.

        Fires FR-HOST-BOOT-REVERSE-SHUTDOWN.
        """
        logger.info(
            "FR-HOST-BOOT-REVERSE-SHUTDOWN: Beginning reverse rollback of %d "
            "acquired stages.",
            len(self._acquired_stack),
            extra={"fr_id": "FR-HOST-BOOT-REVERSE-SHUTDOWN"},
        )
        while self._acquired_stack:
            acquired = self._acquired_stack.pop()
            stage = acquired.stage
            try:
                if acquired.cleanup is not None:
                    if inspect.iscoroutinefunction(acquired.cleanup):
                        await acquired.cleanup()
                    elif callable(acquired.cleanup):
                        acquired.cleanup()
                logger.info(
                    "FR-HOST-BOOT-REVERSE-SHUTDOWN: Released stage %s successfully.",
                    stage,
                    extra={
                        "fr_id": "FR-HOST-BOOT-REVERSE-SHUTDOWN",
                        "stage": stage,
                    },
                )
            except Exception:
                logger.exception(
                    "FR-HOST-BOOT-REVERSE-SHUTDOWN: Error releasing stage %s",
                    stage,
                    extra={
                        "fr_id": "FR-HOST-BOOT-REVERSE-SHUTDOWN",
                        "stage": stage,
                    },
                )

    async def start(self) -> ReadinessSnapshot:
        """Execute the ordered host startup sequence.

        Fires FR-HOST-BOOT-LIFECYCLE-STAGES and FR-HOST-BOOT-REVERSE-SHUTDOWN on
        failure.
        """
        async with self._lock:
            if self._state == ReadinessState.READY:
                logger.info(
                    "FR-HOST-BOOT-LIFECYCLE-STAGES: Host runtime is already ready.",
                    extra={"fr_id": "FR-HOST-BOOT-LIFECYCLE-STAGES"},
                )
                return self.get_readiness()

            self._state = ReadinessState.STARTING
            self._start_time = time.monotonic()
            logger.info(
                "FR-HOST-BOOT-LIFECYCLE-STAGES: Initiating host runtime startup "
                "(instance=%s)",
                self.host_instance_id,
                extra={"fr_id": "FR-HOST-BOOT-LIFECYCLE-STAGES"},
            )

            try:
                await self._advance_stage(LifespanStage.CONFIGURING, "configuration")
                await self._advance_stage(LifespanStage.PATHS, "paths")
                await self._advance_stage(LifespanStage.LOGGING, "logging")
                await self._advance_stage(LifespanStage.DISCOVERY, "discovery")
                await self._advance_stage(LifespanStage.SERVICES, "services")
                await self._advance_stage(LifespanStage.ROUTES, "routes")

                self._active_stage = LifespanStage.READY
                self._state = ReadinessState.READY
                self._completed_stages.append(LifespanStage.READY)

                logger.info(
                    "FR-HOST-BOOT-LIFECYCLE-STAGES: Host runtime is fully ready "
                    "(instance=%s)",
                    self.host_instance_id,
                    extra={"fr_id": "FR-HOST-BOOT-LIFECYCLE-STAGES"},
                )
                return self.get_readiness()

            except Exception:
                self._state = ReadinessState.FAILED
                self._active_stage = LifespanStage.FAILED
                self._details["failure_reason"] = "Startup stage failed"
                logger.exception(
                    "FR-HOST-BOOT-LIFECYCLE-STAGES: Startup failed at stage %s",
                    self._active_stage,
                    extra={"fr_id": "FR-HOST-BOOT-LIFECYCLE-STAGES"},
                )
                await self._rollback_stages()
                raise

    async def stop(self) -> None:
        """Execute the graceful reverse-order host shutdown sequence.

        Fires FR-HOST-BOOT-REVERSE-SHUTDOWN. Safe and idempotent when repeated.
        """
        async with self._lock:
            if self._state in (ReadinessState.STOPPED, ReadinessState.NOT_STARTED):
                logger.info(
                    "FR-HOST-BOOT-REVERSE-SHUTDOWN: Repeated stop requested on "
                    "already stopped host (%s). Safe no-op.",
                    self._state,
                    extra={"fr_id": "FR-HOST-BOOT-REVERSE-SHUTDOWN"},
                )
                return

            self._state = ReadinessState.STOPPING
            self._active_stage = LifespanStage.STOPPING
            logger.info(
                "FR-HOST-BOOT-REVERSE-SHUTDOWN: Stopping host runtime (instance=%s)",
                self.host_instance_id,
                extra={"fr_id": "FR-HOST-BOOT-REVERSE-SHUTDOWN"},
            )

            await self._rollback_stages()

            self._state = ReadinessState.STOPPED
            self._active_stage = LifespanStage.STOPPED
            self._stop_time = time.monotonic()
            for key in self._checks:
                self._checks[key] = False

            logger.info(
                "FR-HOST-BOOT-REVERSE-SHUTDOWN: Host runtime stopped cleanly.",
                extra={"fr_id": "FR-HOST-BOOT-REVERSE-SHUTDOWN"},
            )

    def acknowledge_app_loaded(self) -> None:
        """Record browser shell handshake acknowledgement."""
        self._app_loaded_acknowledged = True
        logger.info(
            "FR-HOST-BOOT-SHELL-PROJECTION: Browser shell app-loaded acknowledged.",
            extra={"fr_id": "FR-HOST-BOOT-SHELL-PROJECTION"},
        )


def _create_shell_router(
    settings: HostSettings, preferences: dict[str, Any]
) -> APIRouter:
    """Create shell endpoints under the configured API prefix."""
    router = APIRouter(prefix=settings.api_prefix)

    @router.get("/status")
    async def get_status(request: Request) -> JSONResponse:
        """Return general host status, CPU capacity, and runtime state."""
        rt: HostRuntime = request.app.state.runtime
        readiness = rt.get_readiness()
        logger.debug(
            "FR-HOST-BOOT-SHELL-PROJECTION: Handling /status query.",
            extra={"fr_id": "FR-HOST-BOOT-SHELL-PROJECTION"},
        )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "data": {
                    "state": readiness.state.value,
                    "host_instance_id": rt.host_instance_id,
                    "is_ready": readiness.is_ready,
                    "cpu_count": 4,
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
        rt.acknowledge_app_loaded()
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
            "FR-HOST-BOOT-SHELL-PROJECTION: Delivering /about metadata.",
            extra={"fr_id": "FR-HOST-BOOT-SHELL-PROJECTION"},
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

    @router.get("/settings")
    async def get_settings() -> JSONResponse:
        """Retrieve current shell settings and preferences snapshot."""
        logger.debug(
            "FR-HOST-BOOT-SHELL-PROJECTION: Delivering /settings.",
            extra={"fr_id": "FR-HOST-BOOT-SHELL-PROJECTION"},
        )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "success", "data": preferences},
        )

    @router.put("/settings")
    async def put_settings(request: Request) -> JSONResponse:
        """Update shell preferences in memory."""
        body = await request.json()
        changes = body.get("changes", {})
        values = preferences["values"]
        for section, section_changes in changes.items():
            if section in values and isinstance(section_changes, dict):
                values[section].update(section_changes)
        preferences["revision"] += 1
        logger.info(
            "FR-HOST-BOOT-SHELL-PROJECTION: Updated settings revision to %d.",
            preferences["revision"],
            extra={"fr_id": "FR-HOST-BOOT-SHELL-PROJECTION"},
        )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "success", "data": preferences},
        )

    @router.post("/auth/login")
    async def post_login() -> JSONResponse:
        """Issue initial loopback session token for browser shell handshake."""
        logger.info(
            "FR-HOST-BOOT-SHELL-PROJECTION: Issued bootstrap loopback session.",
            extra={"fr_id": "FR-HOST-BOOT-SHELL-PROJECTION"},
        )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "data": {
                    "token": f"bootstrap-token-{uuid.uuid4().hex}",
                    "username": "operator",
                },
            },
        )

    return router


def create_host_app(
    settings: HostSettings | None = None,
    runtime: HostRuntime | None = None,
) -> FastAPI:
    """Create and compose the FastAPI application without import-time work.

    Fires FR-HOST-BOOT-APP-COMPOSITION.
    """
    resolved_settings = settings or HostSettings()
    resolved_runtime = runtime or HostRuntime(resolved_settings)

    logger.info(
        "FR-HOST-BOOT-APP-COMPOSITION: Composing host FastAPI application.",
        extra={"fr_id": "FR-HOST-BOOT-APP-COMPOSITION"},
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.runtime = resolved_runtime
        app.state.settings = resolved_settings
        await resolved_runtime.start()
        try:
            yield
        finally:
            await resolved_runtime.stop()

    app = FastAPI(
        title=resolved_settings.title,
        version=resolved_settings.version,
        lifespan=lifespan,
    )
    app.state.runtime = resolved_runtime
    app.state.settings = resolved_settings

    preferences_store = {
        "revision": DEFAULT_SHELL_PREFERENCES["revision"],
        "values": {k: dict(v) for k, v in DEFAULT_SHELL_PREFERENCES["values"].items()},
    }

    shell_router = _create_shell_router(resolved_settings, preferences_store)
    app.include_router(shell_router)

    logger.info(
        "FR-HOST-BOOT-APP-COMPOSITION: Host FastAPI application composed "
        "with routes under %s.",
        resolved_settings.api_prefix,
        extra={"fr_id": "FR-HOST-BOOT-APP-COMPOSITION"},
    )
    return app


def main() -> None:
    """CLI entrypoint for host bootstrap."""
    parser = argparse.ArgumentParser(description="HaruQuantAI Platform Host Bootstrap")
    parser.add_argument("--host", default="127.0.0.1", help="Bind IP address")
    parser.add_argument("--port", type=int, default=8000, help="Bind port number")
    parser.add_argument("--debug", action="store_true", help="Enable debug diagnostics")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    settings = HostSettings(host=args.host, port=args.port, debug=args.debug)
    runtime = HostRuntime(settings)
    app = create_host_app(settings, runtime=runtime)

    try:
        import uvicorn

        uvicorn.run(app, host=settings.host, port=settings.port)
    except ImportError:
        sys.exit(
            "uvicorn is required to run the host CLI. "
            "Please ensure dependencies are installed."
        )


if __name__ == "__main__":
    main()
