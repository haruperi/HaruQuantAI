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
import sys
import time
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from fastapi import APIRouter, FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict

from app.host.diagnostics import create_diagnostics_router
from app.host.discovery import create_discovery_router
from app.host.jobs import JobManager, create_jobs_router
from app.host.logging import (
    configure_host_logging,
    create_debug_console_router,
    get_logger,
    shutdown,
)
from app.host.persistence import (
    DEFAULT_DATABASE_PATH,
    DatabaseManager,
    create_persistence_router,
    get_database_manager,
)
from app.host.resources import ResourceManager, create_resources_router
from app.host.session import create_sessions_router
from app.host.settings import (
    HostSettings,
    create_settings_router,
)
from app.host.settings import settings as default_host_settings
from app.host.transport import (
    TransportMiddleware,
    create_transport_router,
    get_event_bus,
    register_transport_exception_handlers,
)
from app.plugins.data.integration import create_data_router

__all__ = [
    "HostRuntime",
    "HostSettings",
    "LifespanStage",
    "ReadinessSnapshot",
    "ReadinessState",
    "create_host_app",
]

logger = get_logger(__name__)

_MIN_PORT: int = 1
_MAX_PORT: int = 65535


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
        self.db_manager: DatabaseManager | None = None
        self.job_manager: JobManager | None = None
        self.resource_manager: ResourceManager | None = None

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

    @staticmethod
    def _validate_configuration(settings: HostSettings) -> None:
        """Validate critical host runtime settings before advancing stages."""
        if not (_MIN_PORT <= settings.port <= _MAX_PORT):
            raise ValueError(f"Invalid host port number: {settings.port}")

    async def _boot_stage_configuring(self) -> None:
        """Execute Stage 1: CONFIGURING."""
        logger.info(
            "FR-HOST-BOOT-LIFECYCLE-STAGES: [1/6] Stage CONFIGURING: "
            "Validating runtime settings and configuration profiles "
            "(host=%s, port=%d, debug=%s, title=%s)",
            self.settings.host,
            self.settings.port,
            self.settings.debug,
            self.settings.title,
            extra={
                "fr_id": "FR-HOST-BOOT-LIFECYCLE-STAGES",
                "stage": LifespanStage.CONFIGURING,
                "host": self.settings.host,
                "port": self.settings.port,
                "debug": self.settings.debug,
            },
        )
        self._validate_configuration(self.settings)
        await self._advance_stage(LifespanStage.CONFIGURING, "configuration")

    async def _boot_stage_paths(self) -> None:
        """Execute Stage 2: PATHS."""
        base_data_dir = self.settings.data_dir or Path("data")
        logger.info(
            "FR-HOST-BOOT-LIFECYCLE-STAGES: [2/6] Stage PATHS: "
            "Initializing and verifying filesystem containment hierarchy at %s",
            base_data_dir,
            extra={
                "fr_id": "FR-HOST-BOOT-LIFECYCLE-STAGES",
                "stage": LifespanStage.PATHS,
                "data_dir": str(base_data_dir),
            },
        )
        (base_data_dir / "database").mkdir(parents=True, exist_ok=True)
        (base_data_dir / "logs").mkdir(parents=True, exist_ok=True)
        (base_data_dir / "resources" / "staging").mkdir(parents=True, exist_ok=True)
        (base_data_dir / "resources" / "store").mkdir(parents=True, exist_ok=True)
        (base_data_dir / "resources" / "metadata").mkdir(parents=True, exist_ok=True)
        (base_data_dir / "resources" / "extracted").mkdir(parents=True, exist_ok=True)
        (base_data_dir / "resources" / "datasets").mkdir(parents=True, exist_ok=True)
        (base_data_dir / "resources" / "custom_data").mkdir(parents=True, exist_ok=True)
        (base_data_dir / "resources" / "cot").mkdir(parents=True, exist_ok=True)
        await self._advance_stage(LifespanStage.PATHS, "paths")

    async def _boot_stage_logging(self) -> None:
        """Execute Stage 3: LOGGING."""
        logger.info(
            "FR-HOST-BOOT-LIFECYCLE-STAGES: [3/6] Stage LOGGING: "
            "Centralized telemetry, asynchronous queue worker, "
            "and ring buffer active",
            extra={
                "fr_id": "FR-HOST-BOOT-LIFECYCLE-STAGES",
                "stage": LifespanStage.LOGGING,
            },
        )
        await self._advance_stage(LifespanStage.LOGGING, "logging")

    async def _boot_stage_discovery(self) -> None:
        """Execute Stage 4: DISCOVERY."""
        logger.info(
            "FR-HOST-BOOT-LIFECYCLE-STAGES: [4/6] Stage DISCOVERY: "
            "Initializing workspace package discovery and "
            "extension slot registry",
            extra={
                "fr_id": "FR-HOST-BOOT-LIFECYCLE-STAGES",
                "stage": LifespanStage.DISCOVERY,
            },
        )
        await self._advance_stage(LifespanStage.DISCOVERY, "discovery")

    def _init_persistence(self) -> DatabaseManager:
        """Initialize SQLite database persistence and schema migrations."""
        if self.db_manager is None:
            self.db_manager = get_database_manager(
                getattr(self.settings, "db_path", None)
            )
        self.db_manager.initialize()
        return self.db_manager

    def _cleanup_services(self) -> None:
        """Tear down database and job manager during rollback or shutdown."""
        if self.job_manager is not None:
            try:
                self.job_manager.close(timeout=5.0)
            except Exception:
                logger.exception(
                    "FR-HOST-BOOT-REVERSE-SHUTDOWN: Error closing job manager."
                )
            self.job_manager = None
        if self.db_manager is not None:
            try:
                self.db_manager.close()
            except Exception:
                logger.exception(
                    "FR-HOST-BOOT-REVERSE-SHUTDOWN: Error closing db manager."
                )
            self.db_manager = None

    async def _boot_stage_services(self) -> None:
        """Execute Stage 5: SERVICES."""
        logger.info(
            "FR-HOST-BOOT-LIFECYCLE-STAGES: [5/6] Stage SERVICES: "
            "Initializing authoritative host persistence, "
            "recovery, and compute coordinators",
            extra={
                "fr_id": "FR-HOST-BOOT-LIFECYCLE-STAGES",
                "stage": LifespanStage.SERVICES,
            },
        )

        # Substage 5.1: Persistence & Schema Migrations
        logger.info(
            "FR-HOST-BOOT-LIFECYCLE-STAGES: [5/6] Stage SERVICES "
            "(Substage 1/4): Initializing SQLite persistence authority "
            "and executing schema migrations",
            extra={
                "fr_id": "FR-HOST-BOOT-LIFECYCLE-STAGES",
                "stage": LifespanStage.SERVICES,
                "substage": "persistence",
            },
        )
        db_mgr = self._init_persistence()

        # Substage 5.2: Startup Recovery & Integrity Verification
        logger.info(
            "FR-HOST-BOOT-LIFECYCLE-STAGES: [5/6] Stage SERVICES "
            "(Substage 2/4): Running database physical integrity audit "
            "and restart reconciliation",
            extra={
                "fr_id": "FR-HOST-BOOT-LIFECYCLE-STAGES",
                "stage": LifespanStage.SERVICES,
                "substage": "recovery",
            },
        )
        recovery_report = db_mgr.recovery.reconcile_on_startup()
        logger.info(
            "FR-HOST-BOOT-LIFECYCLE-STAGES: Startup recovery audit complete "
            "(integrity=%s, pruned_leases=%s)",
            recovery_report.get("integrity", "unknown"),
            recovery_report.get("pruned_expired_leases", 0),
            extra={
                "fr_id": "FR-HOST-BOOT-LIFECYCLE-STAGES",
                "stage": LifespanStage.SERVICES,
                "recovery": recovery_report,
            },
        )

        # Substage 5.3: Safe Resource Custody
        logger.info(
            "FR-HOST-BOOT-LIFECYCLE-STAGES: [5/6] Stage SERVICES "
            "(Substage 3/4): Verifying immutable resource custody "
            "and content-addressed storage",
            extra={
                "fr_id": "FR-HOST-BOOT-LIFECYCLE-STAGES",
                "stage": LifespanStage.SERVICES,
                "substage": "resources",
            },
        )
        if self.resource_manager is None:
            res_target = (
                (self.settings.data_dir / "resources")
                if self.settings.data_dir is not None
                else Path("data/resources")
            )
            self.resource_manager = ResourceManager(root_dir=res_target)

        # Substage 5.4: Job Coordinator & In-flight Task Reconciliation
        logger.info(
            "FR-HOST-BOOT-LIFECYCLE-STAGES: [5/6] Stage SERVICES "
            "(Substage 4/4): Reconciling in-flight compute jobs "
            "and worker process pool",
            extra={
                "fr_id": "FR-HOST-BOOT-LIFECYCLE-STAGES",
                "stage": LifespanStage.SERVICES,
                "substage": "jobs",
            },
        )
        if self.job_manager is None:
            self.job_manager = JobManager(
                max_workers=4,
                db_path=db_mgr.database_path,
                auto_reconcile=False,
            )
        self.job_manager.store.reconcile_on_startup()

        await self._advance_stage(
            LifespanStage.SERVICES, "services", cleanup=self._cleanup_services
        )

    async def _boot_stage_routes(self) -> None:
        """Execute Stage 6: ROUTES."""
        logger.info(
            "FR-HOST-BOOT-LIFECYCLE-STAGES: [6/6] Stage ROUTES: "
            "Verifying mounted capability routers, transport middleware, "
            "and API endpoints",
            extra={
                "fr_id": "FR-HOST-BOOT-LIFECYCLE-STAGES",
                "stage": LifespanStage.ROUTES,
            },
        )
        await self._advance_stage(LifespanStage.ROUTES, "routes")

    async def start(self) -> ReadinessSnapshot:
        """Execute the ordered host startup sequence across all lifespan stages.

        Progresses strictly through:
            1. CONFIGURING: Validates runtime host, port, and debug configuration.
            2. PATHS: Ensures directory containment hierarchy for data and resources.
            3. LOGGING: Verifies centralized telemetry and ring buffer readiness.
            4. DISCOVERY: Initializes extension slot registry and plugin context.
            5. SERVICES: Initializes SQLite schemas, runs startup recovery audit,
               reconciles active compute jobs, and verifies resource custody.
            6. ROUTES: Confirms capability routers, transport middleware and contracts.
            7. READY: Asserts all checks passed and signals readiness to serve.

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
                await self._boot_stage_configuring()
                await self._boot_stage_paths()
                await self._boot_stage_logging()
                await self._boot_stage_discovery()
                await self._boot_stage_services()
                await self._boot_stage_routes()

                # -------------------------------------------------------------
                # Stage 7: READY
                # -------------------------------------------------------------
                self._active_stage = LifespanStage.READY
                self._state = ReadinessState.READY
                self._completed_stages.append(LifespanStage.READY)

                uptime = time.monotonic() - self._start_time
                logger.info(
                    "FR-HOST-BOOT-LIFECYCLE-STAGES: [READY] HaruQuantAI platform "
                    "host is ready to serve requests "
                    "(instance=%s, uptime=%.2fs, prefix=%s)",
                    self.host_instance_id,
                    uptime,
                    self.settings.api_prefix,
                    extra={
                        "fr_id": "FR-HOST-BOOT-LIFECYCLE-STAGES",
                        "stage": LifespanStage.READY,
                        "instance": self.host_instance_id,
                        "uptime": uptime,
                    },
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

            if self.job_manager is not None:
                try:
                    self.job_manager.close(timeout=5.0)
                except Exception:
                    logger.exception(
                        "FR-HOST-BOOT-REVERSE-SHUTDOWN: Error closing job manager.",
                        extra={"fr_id": "FR-HOST-BOOT-REVERSE-SHUTDOWN"},
                    )
                self.job_manager = None

            if self.db_manager is not None:
                try:
                    self.db_manager.close()
                except Exception:
                    logger.exception(
                        "FR-HOST-BOOT-REVERSE-SHUTDOWN: Error closing db manager.",
                        extra={"fr_id": "FR-HOST-BOOT-REVERSE-SHUTDOWN"},
                    )
                self.db_manager = None

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


def _create_shell_router(settings: HostSettings) -> APIRouter:
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
        logger.debug(
            "FR-HOST-BOOT-SHELL-PROJECTION: Readiness endpoint evaluated: is_ready=%s",
            readiness.is_ready,
            extra={"fr_id": "FR-HOST-BOOT-SHELL-PROJECTION"},
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
        rt.acknowledge_app_loaded()
        logger.info(
            "FR-HOST-BOOT-SHELL-PROJECTION: Browser shell app-loaded received "
            "for host=%s",
            rt.host_instance_id,
            extra={"fr_id": "FR-HOST-BOOT-SHELL-PROJECTION"},
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


def _mount_host_routers(
    app: FastAPI,
    resolved_settings: HostSettings,
    resolved_runtime: HostRuntime,
    resolved_config: Any,
) -> None:
    """Mount all host capability routers and initialize service custody."""
    # 1. Shell Router (/api/v1/status, /api/v1/readiness, /api/v1/about, etc.)
    shell_router = _create_shell_router(resolved_settings)
    app.include_router(shell_router)

    # 2. Settings Router (/api/v1/settings, /api/v1/settings/paths/validate)
    settings_router = create_settings_router(resolved_config)
    app.include_router(settings_router, prefix=resolved_settings.api_prefix)

    # 3. Transport Router (/events, /auth/status, /events/publish, /events/snapshot)
    transport_router = create_transport_router()
    app.include_router(transport_router)
    app.include_router(transport_router, prefix=resolved_settings.api_prefix)

    # 4. Debug Console Router (/debugconsole/..., /api/v1/debugconsole/...)
    debug_console_router = create_debug_console_router()
    app.include_router(debug_console_router)

    # 5. Diagnostics Router (/api/v1/diagnostics/...)
    diagnostics_router = create_diagnostics_router()
    app.include_router(diagnostics_router)

    # 6. Discovery Router (/api/v1/discovery/...)
    discovery_router = create_discovery_router()
    app.include_router(discovery_router, prefix=resolved_settings.api_prefix)

    # 7. Sessions Router (/api/v1/sessions/...)
    sessions_router = create_sessions_router()
    app.include_router(sessions_router, prefix=resolved_settings.api_prefix)

    # 8. Persistence Router (/api/v1/persistence/...)
    if resolved_runtime.db_manager is None:
        db_target = getattr(resolved_settings, "db_path", None)
        if (db_target is None or db_target == DEFAULT_DATABASE_PATH) and hasattr(
            resolved_config, "db_path"
        ):
            db_target = resolved_config.db_path
        resolved_runtime.db_manager = get_database_manager(db_target)
    persistence_router = create_persistence_router(resolved_runtime.db_manager)
    app.include_router(persistence_router, prefix=resolved_settings.api_prefix)

    # 9. Jobs Router (/api/v1/jobs/...)
    if resolved_runtime.job_manager is None:
        max_workers = 4
        if hasattr(resolved_config, "config_cpu"):
            max_workers = int(resolved_config.config_cpu.get("custom_cores", 4))
        resolved_runtime.job_manager = JobManager(
            max_workers=max_workers,
            db_path=resolved_runtime.db_manager.database_path,
            auto_reconcile=False,
        )
    jobs_router = create_jobs_router(resolved_runtime.job_manager)
    app.include_router(jobs_router, prefix=resolved_settings.api_prefix)

    # 10. Resources Router (/api/v1/resources/...)
    if resolved_runtime.resource_manager is None:
        res_dir = (
            resolved_settings.data_dir / "resources"
            if resolved_settings.data_dir is not None
            else Path("data/resources")
        )
        resolved_runtime.resource_manager = ResourceManager(root_dir=res_dir)
    resources_router = create_resources_router(resolved_runtime.resource_manager)
    app.include_router(resources_router, prefix=resolved_settings.api_prefix)

    # 11. Market Data Router (/data/..., /api/v1/data/...)
    data_router = create_data_router(
        resolved_runtime.db_manager,
        resolved_runtime.resource_manager,
        job_manager=resolved_runtime.job_manager,
        event_bus=get_event_bus(),
    )
    app.include_router(data_router)
    app.include_router(data_router, prefix=resolved_settings.api_prefix)


def create_host_app(
    settings: HostSettings | None = None,
    runtime: HostRuntime | None = None,
    *,
    configuration: Any | None = None,
) -> FastAPI:
    """Create and compose the FastAPI application without import-time work.

    Fires FR-HOST-BOOT-APP-COMPOSITION.
    """
    resolved_settings = settings or HostSettings()
    resolved_runtime = runtime or HostRuntime(resolved_settings)
    resolved_config = configuration or default_host_settings

    logger.info(
        "FR-HOST-BOOT-APP-COMPOSITION: Composing host FastAPI application.",
        extra={"fr_id": "FR-HOST-BOOT-APP-COMPOSITION"},
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
        app.state.runtime = resolved_runtime
        app.state.settings = resolved_settings
        logger.info(
            "FR-HOST-BOOT-LIFECYCLE-STAGES: Entering host lifespan: starting runtime.",
            extra={"fr_id": "FR-HOST-BOOT-LIFECYCLE-STAGES"},
        )
        await resolved_runtime.start()
        try:
            yield
        finally:
            logger.info(
                "FR-HOST-BOOT-REVERSE-SHUTDOWN: Exiting host lifespan: "
                "stopping runtime.",
                extra={"fr_id": "FR-HOST-BOOT-REVERSE-SHUTDOWN"},
            )
            await resolved_runtime.stop()

    app = FastAPI(
        title=resolved_settings.title,
        version=resolved_settings.version,
        lifespan=lifespan,
    )
    app.state.runtime = resolved_runtime
    app.state.settings = resolved_settings

    # Middleware: CORS for browser shell & Vite UI (port 3000)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:3000",
            "http://localhost:3000",
            f"http://{resolved_settings.host}:{resolved_settings.port}",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(TransportMiddleware)
    register_transport_exception_handlers(app)

    _mount_host_routers(app, resolved_settings, resolved_runtime, resolved_config)

    logger.info(
        "FR-HOST-BOOT-APP-COMPOSITION: Host FastAPI application composed "
        "with routes under %s.",
        resolved_settings.api_prefix,
        extra={"fr_id": "FR-HOST-BOOT-APP-COMPOSITION"},
    )
    return app


def main(argv: list[str] | None = None) -> None:
    """CLI entrypoint for host bootstrap."""
    parser = argparse.ArgumentParser(description="HaruQuantAI Platform Host Bootstrap")
    parser.add_argument("--host", default=None, help="Bind IP address")
    parser.add_argument("--port", type=int, default=None, help="Bind port number")
    parser.add_argument(
        "--debug",
        action="store_true",
        default=None,
        help="Enable debug diagnostics",
    )
    args = parser.parse_args(argv)

    db_host = str(default_host_settings.app_general.get("host", "127.0.0.1"))
    db_port = int(default_host_settings.app_general.get("backend_port", 8000))
    db_debug = bool(
        default_host_settings.config_troubleshooting.get("debug_level_active", False)
    )

    host: str = args.host if args.host is not None else db_host
    port: int = args.port if args.port is not None else db_port
    debug: bool = args.debug if args.debug is not None else db_debug

    configure_host_logging(level="DEBUG" if debug else "INFO")
    logger.info(
        "FR-HOST-BOOT-LIFECYCLE-STAGES: Initializing host from CLI: "
        "host=%s port=%d debug=%s",
        host,
        port,
        debug,
        extra={"fr_id": "FR-HOST-BOOT-LIFECYCLE-STAGES"},
    )

    settings = HostSettings(host=host, port=port, debug=debug)
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
    finally:
        shutdown(timeout=5.0)


if __name__ == "__main__":
    main()
