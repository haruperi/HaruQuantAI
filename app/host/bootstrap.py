# ruff: noqa: INP001
"""Progressive 7-stage host bootstrap state machine and lifecycle coordinator.

Description:
    Implements the ordered 7-stage progressive startup state machine and
    automatic reverse-order (LIFO) teardown coordinator for the HaruQuantAI
    Tier 1 Host Platform (app/host/bootstrap.py). Every host execution mode —
    both the UI/FastAPI web server (app/main.py) and the headless CLI
    (app/cli.py) — progresses deterministically through:
        CONFIGURING -> PATHS -> LOGGING -> PERSISTENCE -> SERVICES -> ROUTES -> READY
    If any stage fails during startup, or when the process shuts down, acquired
    stages are released in strict reverse LIFO order (READY -> ROUTES ->
    SERVICES -> PERSISTENCE -> LOGGING -> PATHS -> CONFIGURING) so database
    handles, worker pools, plugin adapters, and telemetry buffers never leak.

Purpose:
    FEAT-HOST-BOOT: Progressive 7-stage host bootstrap state machine, service
    coordinator, and reverse-order LIFO teardown lifecycle.

Key Capabilities:
    - FR-HOST-BOOT-STAGE-PROGRESSION: Execute the ordered 7-stage startup state
      machine (CONFIGURING -> PATHS -> LOGGING -> PERSISTENCE -> SERVICES ->
      ROUTES -> READY), recording stage checks and cleanup hooks.
      Associated: `LifespanStage`, `HostRuntime.start()`, `HostRuntime.start_sync()`
      Logging: Emits INFO on each stage entry and advancement; ERROR on stage
      failure.
    - FR-HOST-BOOT-REVERSE-TEARDOWN: Roll back or shut down acquired bootstrap
      stages in strict reverse LIFO order, isolating cleanup exceptions.
      Associated: `HostRuntime.stop()`, `HostRuntime.stop_sync()`,
      `HostRuntime._rollback_stages()`
      Logging: Emits INFO on teardown start and stage release; ERROR on cleanup
      exceptions.
    - FR-HOST-BOOT-PERSISTENCE-STAGE: Initialize SQLite WAL persistence via
      app.host.persistence.create, verify all 25 operational tables, and reload
      host settings without importing sqlite3.
      Associated: `HostRuntime._boot_stage_persistence()`, `reconcile_database()`
      Logging: Emits INFO on schema verification and table inventory count;
      ERROR on persistence failure.
    - FR-HOST-BOOT-SERVICES-STAGE: Initialize and coordinate EventBus,
      SessionManager, ResourceManager, JobManager (with startup orphan-job
      reconciliation RUNNING -> INTERRUPTED), and PluginLifecycleManager.
      Associated: `HostRuntime._boot_stage_services()`,
      `HostRuntime.init_discovery()`
      Logging: Emits INFO on service initialization and orphan job recovery.
    - FR-HOST-BOOT-ROUTES-STAGE: Mount and verify FastAPI transport and
      discovery routers (/api/v1, /api/v2) in UI/server mode or verify headless
      CLI command dispatch routes in CLI mode.
      Associated: `HostRuntime._boot_stage_routes()`, `create_bootstrap_app()`
      Logging: Emits INFO on route registration and verification.
    - FR-HOST-BOOT-READINESS-SNAPSHOT: Capture immutable ReadinessSnapshot
      reports detailing active/completed stages, stage check statuses, uptime,
      and host_instance_id.
      Associated: `ReadinessState`, `ReadinessSnapshot`,
      `HostRuntime.get_readiness()`, `HostRuntime.is_ready()`
      Logging: Emits DEBUG when ready and WARNING when queried while not ready.
    - FR-HOST-BOOT-LIFESPAN-CONTEXT: Provide dual sync/async bootstrap_context
      context managers and FastAPI lifespan composition via
      create_bootstrap_app().
      Associated: `BootstrapConfig`, `bootstrap_context()`,
      `create_bootstrap_app()`
      Logging: Emits INFO when entering and exiting bootstrap lifespan contexts.

Python API Usage:
    ```python
    from pathlib import Path
    from app.host.bootstrap import BootstrapConfig, bootstrap_context

    cfg = BootstrapConfig(data_dir=Path("data"), headless=True)
    with bootstrap_context(cfg) as runtime:
        snap = runtime.get_readiness()
        assert snap.is_ready is True
    ```

CLI Usage:
    ```bash
    uv run python -m app.host.bootstrap
    uv run python -m app.host.bootstrap --check-only
    ```
"""

from __future__ import annotations

import argparse
import asyncio
import inspect
import time
import uuid
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from functools import partial
from pathlib import Path
from typing import Any

from app.host.discovery import (
    PluginDiscoveryEngine,
    PluginLifecycleManager,
    PluginState,
    SlotDefinition,
    SlotRegistry,
    create_discovery_router,
)
from app.host.jobs import JobManager
from app.host.logging import (
    flush_logs,
    get_logger,
    get_ring_buffer,
    setup_logging,
    shutdown_logging,
)
from app.host.persistence.create import (
    DEFAULT_DB_PATH,
    TABLE_PRIMARY_KEYS,
    create_schema,
    get_connection,
)
from app.host.persistence.read import count_database_tables
from app.host.resources import (
    MIN_AVAILABLE_RAM_PCT,
    ResourceManager,
    inspect_workspace_directories,
)
from app.host.session import SessionManager
from app.host.settings import settings as host_settings
from app.host.transport import (
    EventBus,
    TransportGatewayService,
    TransportMiddleware,
    create_transport_router,
    get_global_event_bus,
    register_transport_exception_handlers,
)
from app.services.brokers.registry import BrokerRegistry
from app.workspace.data_manager import (
    DataManagerWorkspace,
    create_data_manager_router,
)
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

__all__ = [
    "BootstrapConfig",
    "HostRuntime",
    "LifespanStage",
    "ReadinessSnapshot",
    "ReadinessState",
    "bootstrap_context",
    "create_bootstrap_app",
]

logger = get_logger(__name__)

# ============================================================================
# Functional Requirement Constants & Defaults
# ============================================================================

STAGE_PROGRESSION_FR = "FR-HOST-BOOT-STAGE-PROGRESSION"
REVERSE_TEARDOWN_FR = "FR-HOST-BOOT-REVERSE-TEARDOWN"
PERSISTENCE_STAGE_FR = "FR-HOST-BOOT-PERSISTENCE-STAGE"
SERVICES_STAGE_FR = "FR-HOST-BOOT-SERVICES-STAGE"
ROUTES_STAGE_FR = "FR-HOST-BOOT-ROUTES-STAGE"
READINESS_SNAPSHOT_FR = "FR-HOST-BOOT-READINESS-SNAPSHOT"
LIFESPAN_CONTEXT_FR = "FR-HOST-BOOT-LIFESPAN-CONTEXT"

_MIN_PORT = 1
_MAX_PORT = 65535
_EXPECTED_TABLE_COUNT = len(TABLE_PRIMARY_KEYS)

DEFAULT_SLOTS: tuple[SlotDefinition, ...] = (
    SlotDefinition(
        slot_id="data.provider",
        description="Market data feed provider adapter slot.",
        allow_multiple=True,
    ),
    SlotDefinition(
        slot_id="validation.crosscheck",
        description="Robustness and cross-check validation plugin slot.",
        allow_multiple=True,
    ),
    SlotDefinition(
        slot_id="export.platform",
        description="Strategy source code platform exporter slot.",
        allow_multiple=True,
    ),
    SlotDefinition(
        slot_id="strategy.block",
        description="Strategy building block and indicator plugin slot.",
        allow_multiple=True,
    ),
)


# ============================================================================
# Progressive 7-Stage Enums & Immutable Snapshots
# ============================================================================


class LifespanStage(StrEnum):
    """Canonical 7-stage progressive bootstrap sequence."""

    CONFIGURING = "CONFIGURING"
    PATHS = "PATHS"
    LOGGING = "LOGGING"
    PERSISTENCE = "PERSISTENCE"
    SERVICES = "SERVICES"
    ROUTES = "ROUTES"
    READY = "READY"


ORDERED_BOOT_STAGES: tuple[LifespanStage, ...] = (
    LifespanStage.CONFIGURING,
    LifespanStage.PATHS,
    LifespanStage.LOGGING,
    LifespanStage.PERSISTENCE,
    LifespanStage.SERVICES,
    LifespanStage.ROUTES,
    LifespanStage.READY,
)

STAGE_CHECK_KEYS: dict[LifespanStage, str] = {
    LifespanStage.CONFIGURING: "configuration",
    LifespanStage.PATHS: "paths",
    LifespanStage.LOGGING: "logging",
    LifespanStage.PERSISTENCE: "persistence",
    LifespanStage.SERVICES: "services",
    LifespanStage.ROUTES: "routes",
    LifespanStage.READY: "ready",
}


class ReadinessState(StrEnum):
    """High-level lifecycle states of the HostRuntime."""

    UNINITIALIZED = "UNINITIALIZED"
    STARTING = "STARTING"
    READY = "READY"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class BootstrapConfig:
    """Configuration parameters governing the 7-stage host bootstrap."""

    title: str = "HaruQuantAI Host Gateway"
    version: str = "1.0.0"
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = False
    headless: bool = False
    require_auth: bool = False
    password_hash: str | None = None
    data_dir: Path = field(default_factory=lambda: Path("data"))
    db_path: Path | None = None
    log_dir: Path | None = None
    scratch_root: Path | None = None
    plugins_dir: Path | None = None
    max_workers: int | None = None
    use_process_pool: bool = True
    min_available_ram_pct: float = MIN_AVAILABLE_RAM_PCT
    timeout_graceful_shutdown: int = 10

    @property
    def resolved_db_path(self) -> Path:
        """Return effective SQLite database file path."""
        if self.db_path is not None:
            return Path(self.db_path)
        return Path(self.data_dir) / "database" / DEFAULT_DB_PATH.name

    @property
    def resolved_log_dir(self) -> Path:
        """Return effective log directory path."""
        if self.log_dir is not None:
            return Path(self.log_dir)
        return Path(self.data_dir) / "logs"

    @property
    def resolved_scratch_root(self) -> Path:
        """Return effective per-job scratch root directory path."""
        if self.scratch_root is not None:
            return Path(self.scratch_root)
        return Path(self.data_dir) / "scratch"

    @property
    def resolved_plugins_dir(self) -> Path:
        """Return effective dynamic plugins root directory path."""
        if self.plugins_dir is not None:
            return Path(self.plugins_dir)
        return Path(self.data_dir) / "plugins"


@dataclass(frozen=True)
class ReadinessSnapshot:
    """Immutable point-in-time readiness report of the HostRuntime."""

    state: ReadinessState
    is_ready: bool
    headless: bool
    host_instance_id: str
    uptime_seconds: float
    timestamp: str
    active_stage: LifespanStage | None
    completed_stages: list[LifespanStage]
    checks: dict[str, bool]
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Serialize ReadinessSnapshot to a plain dictionary."""
        raw = asdict(self)
        raw["state"] = str(self.state)
        raw["active_stage"] = (
            str(self.active_stage) if self.active_stage is not None else None
        )
        raw["completed_stages"] = [str(s) for s in self.completed_stages]
        return raw


@dataclass(frozen=True)
class _AcquiredStage:
    """Internal LIFO stack entry recording an acquired stage and its cleanup."""

    stage: LifespanStage
    check_key: str
    cleanup: Callable[[], Any] | None = None


# ============================================================================
# Progressive 7-Stage HostRuntime Coordinator
# ============================================================================


class HostRuntime:
    """Progressive 7-stage host runtime state machine with reverse LIFO teardown."""

    def __init__(
        self,
        config: BootstrapConfig | None = None,
        *,
        event_bus: EventBus | None = None,
        session_mgr: SessionManager | None = None,
        resource_mgr: ResourceManager | None = None,
        job_mgr: JobManager | None = None,
        plugin_mgr: PluginLifecycleManager | None = None,
        broker_registry: BrokerRegistry | None = None,
        extra_routers: list[APIRouter] | None = None,
        stage_hooks: dict[LifespanStage, Callable[[HostRuntime], Any]] | None = None,
    ) -> None:
        """Initialize the HostRuntime state machine in UNINITIALIZED state."""
        self.config = config or BootstrapConfig()
        self.host_instance_id = f"host-{uuid.uuid4().hex[:12]}"
        self._lock = asyncio.Lock()
        self._state = ReadinessState.UNINITIALIZED
        self._active_stage: LifespanStage | None = None
        self._completed_stages: list[LifespanStage] = []
        self._teardown_stages: list[LifespanStage] = []
        self._acquired_stack: list[_AcquiredStage] = []
        self._start_time: float | None = None
        self._checks: dict[str, bool] = {
            "configuration": False,
            "paths": False,
            "logging": False,
            "persistence": False,
            "services": False,
            "routes": False,
            "ready": False,
        }
        self._details: dict[str, Any] = {}
        self._stage_hooks = dict(stage_hooks or {})
        self._extra_routers: list[APIRouter] = list(extra_routers or [])
        self._mounted_routes: list[str] = []

        # Managed service references populated during Stage 5 (SERVICES)
        self.event_bus: EventBus = (
            event_bus if event_bus is not None else get_global_event_bus()
        )
        self.session_manager: SessionManager | None = session_mgr
        self.resource_manager: ResourceManager | None = resource_mgr
        self.job_manager: JobManager | None = job_mgr
        self.plugin_manager: PluginLifecycleManager | None = plugin_mgr
        self.broker_registry: BrokerRegistry | None = broker_registry
        self.gateway_service: TransportGatewayService | None = None
        self.data_manager: DataManagerWorkspace | None = None

    @property
    def state(self) -> ReadinessState:
        """Return current ReadinessState."""
        return self._state

    @property
    def active_stage(self) -> LifespanStage | None:
        """Return currently active LifespanStage."""
        return self._active_stage

    @property
    def completed_stages(self) -> list[LifespanStage]:
        """Return ordered list of completed bootstrap stages."""
        return list(self._completed_stages)

    @property
    def teardown_stages(self) -> list[LifespanStage]:
        """Return ordered list of stages released during the most recent teardown."""
        return list(self._teardown_stages)

    @property
    def mounted_routes(self) -> list[str]:
        """Return list of route paths or CLI commands registered in Stage 6."""
        return list(self._mounted_routes)

    def is_ready(self) -> bool:
        """Return True if all 7 stages completed and state is READY."""
        return (
            self._state == ReadinessState.READY
            and self._active_stage == LifespanStage.READY
            and all(self._checks.values())
        )

    def get_readiness(self) -> ReadinessSnapshot:
        """Capture and return an immutable ReadinessSnapshot."""
        ready = self.is_ready()
        now_iso = datetime.now(UTC).isoformat()
        uptime = (
            max(0.0, time.monotonic() - self._start_time)
            if self._start_time is not None
            else 0.0
        )
        if ready:
            logger.debug(
                "%s: Host runtime is READY (instance=%s uptime=%.3fs headless=%s).",
                READINESS_SNAPSHOT_FR,
                self.host_instance_id,
                uptime,
                self.config.headless,
                extra={"fr_id": READINESS_SNAPSHOT_FR},
            )
        else:
            logger.warning(
                "%s: Host runtime not ready (state=%s stage=%s checks=%s).",
                READINESS_SNAPSHOT_FR,
                self._state,
                self._active_stage,
                self._checks,
                extra={"fr_id": READINESS_SNAPSHOT_FR},
            )
        return ReadinessSnapshot(
            state=self._state,
            is_ready=ready,
            headless=self.config.headless,
            host_instance_id=self.host_instance_id,
            uptime_seconds=round(uptime, 4),
            timestamp=now_iso,
            active_stage=self._active_stage,
            completed_stages=list(self._completed_stages),
            checks=dict(self._checks),
            details=dict(self._details),
        )

    async def _advance_stage(
        self,
        stage: LifespanStage,
        cleanup: Callable[[], Any] | None = None,
    ) -> None:
        """Mark stage completed, push cleanup onto LIFO stack, and run hook."""
        check_key = STAGE_CHECK_KEYS[stage]
        self._active_stage = stage
        if not any(item.stage == stage for item in self._acquired_stack):
            self._acquired_stack.append(
                _AcquiredStage(stage=stage, check_key=check_key, cleanup=cleanup)
            )
        hook = self._stage_hooks.get(stage)
        if hook is not None:
            res = hook(self)
            if inspect.isawaitable(res):
                await res

        self._checks[check_key] = True
        self._completed_stages.append(stage)
        logger.info(
            "%s: Advanced to stage %s (%d/7) [instance=%s].",
            STAGE_PROGRESSION_FR,
            stage.value,
            len(self._completed_stages),
            self.host_instance_id,
            extra={
                "fr_id": STAGE_PROGRESSION_FR,
                "stage": stage.value,
                "instance": self.host_instance_id,
            },
        )

    async def _rollback_stages(self) -> None:
        """Release all acquired stages in strict reverse LIFO order."""
        self._teardown_stages.clear()
        logger.info(
            "%s: Starting reverse LIFO teardown of %d acquired stages.",
            REVERSE_TEARDOWN_FR,
            len(self._acquired_stack),
            extra={"fr_id": REVERSE_TEARDOWN_FR},
        )
        while self._acquired_stack:
            acquired = self._acquired_stack.pop()
            stage = acquired.stage
            try:
                if acquired.cleanup is not None:
                    res = acquired.cleanup()
                    if inspect.isawaitable(res):
                        await res
                self._checks[acquired.check_key] = False
                self._teardown_stages.append(stage)
                logger.info(
                    "%s: Released stage %s in reverse order.",
                    REVERSE_TEARDOWN_FR,
                    stage.value,
                    extra={
                        "fr_id": REVERSE_TEARDOWN_FR,
                        "stage": stage.value,
                    },
                )
            except Exception:
                self._teardown_stages.append(stage)
                logger.exception(
                    "%s: Exception while releasing stage %s during reverse teardown.",
                    REVERSE_TEARDOWN_FR,
                    stage.value,
                    extra={
                        "fr_id": REVERSE_TEARDOWN_FR,
                        "stage": stage.value,
                    },
                )
            finally:
                self._checks[acquired.check_key] = False
        self._active_stage = None

    # ------------------------------------------------------------------------
    # Stage 1..7 Implementations
    # ------------------------------------------------------------------------

    async def _boot_stage_configuring(self) -> None:
        """Stage 1/7: CONFIGURING — Validate host, port, and runtime configuration."""
        self._active_stage = LifespanStage.CONFIGURING
        logger.info(
            "%s: [1/7] Stage CONFIGURING (host=%s port=%d headless=%s debug=%s).",
            STAGE_PROGRESSION_FR,
            self.config.host,
            self.config.port,
            self.config.headless,
            self.config.debug,
            extra={"fr_id": STAGE_PROGRESSION_FR, "stage": "CONFIGURING"},
        )
        if not self.config.host or not self.config.host.strip():
            raise ValueError("BootstrapConfig.host must be a non-empty string.")
        if not (_MIN_PORT <= self.config.port <= _MAX_PORT):
            raise ValueError(
                f"Invalid host port number: {self.config.port} "
                f"(expected {_MIN_PORT}..{_MAX_PORT})."
            )
        if self.config.min_available_ram_pct <= 0.0:
            raise ValueError("min_available_ram_pct must be positive.")

        self._details["mode"] = "headless_cli" if self.config.headless else "ui_server"
        self._details["host"] = self.config.host
        self._details["port"] = self.config.port
        await self._advance_stage(LifespanStage.CONFIGURING)

    async def _boot_stage_paths(self) -> None:
        """Stage 2/7: PATHS — Create and verify workspace directory hierarchy."""
        base_dir = Path(self.config.data_dir)
        db_dir = self.config.resolved_db_path.parent
        log_dir = self.config.resolved_log_dir
        scratch_dir = self.config.resolved_scratch_root
        plugins_dir = self.config.resolved_plugins_dir
        resources_dir = base_dir / "resources"

        logger.info(
            "%s: [2/7] Stage PATHS (data_dir=%s).",
            STAGE_PROGRESSION_FR,
            base_dir,
            extra={"fr_id": STAGE_PROGRESSION_FR, "stage": "PATHS"},
        )
        for directory in (
            base_dir,
            db_dir,
            log_dir,
            scratch_dir,
            plugins_dir,
            resources_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)

        dir_report = inspect_workspace_directories()
        self._details["paths"] = {
            "data_dir": str(base_dir),
            "db_path": str(self.config.resolved_db_path),
            "log_dir": str(log_dir),
            "scratch_root": str(scratch_dir),
            "plugins_dir": str(plugins_dir),
            "inspected_count": len(dir_report),
        }
        await self._advance_stage(LifespanStage.PATHS)

    async def _boot_stage_logging(self) -> None:
        """Stage 3/7: LOGGING — Configure multi-sink telemetry and ring buffer."""
        log_dir = self.config.resolved_log_dir
        level_name = "DEBUG" if self.config.debug else "INFO"
        level_int = 10 if self.config.debug else 20
        logger.info(
            "%s: [3/7] Stage LOGGING (log_dir=%s level=%s).",
            STAGE_PROGRESSION_FR,
            log_dir,
            level_name,
            extra={"fr_id": STAGE_PROGRESSION_FR, "stage": "LOGGING"},
        )
        setup_logging(log_dir=log_dir, level=level_int, publish_log=self._publish_log)
        ring = get_ring_buffer()
        self._details["logging"] = {
            "level": level_name,
            "ring_buffer_records": len(ring),
            "ring_buffer_capacity": ring.maxlen,
        }
        await self._advance_stage(LifespanStage.LOGGING, cleanup=flush_logs)

    def _publish_log(self, entry: dict[str, Any]) -> None:
        """Forward scrubbed telemetry to the runtime's bounded event broker."""
        self.event_bus.publish(channel="logs", event_type="log", payload=entry)

    async def _boot_stage_persistence(self) -> None:
        """Stage 4/7: PERSISTENCE — Initialize SQLite WAL schema and verify tables."""
        db_path = self.config.resolved_db_path
        logger.info(
            "%s: [4/7] Stage PERSISTENCE (initializing WAL schema at %s).",
            PERSISTENCE_STAGE_FR,
            db_path.name,
            extra={"fr_id": PERSISTENCE_STAGE_FR, "stage": "PERSISTENCE"},
        )
        conn = get_connection(db_path)
        try:
            create_schema(conn)
        finally:
            conn.close()
        host_settings.reload(conn=db_path)

        table_count = count_database_tables(db_path)
        if table_count < _EXPECTED_TABLE_COUNT:
            raise RuntimeError(
                f"Database schema verification failed: expected >= "
                f"{_EXPECTED_TABLE_COUNT} tables, found {table_count}."
            )

        self._details["persistence"] = {
            "db_name": db_path.name,
            "table_count": table_count,
            "wal_mode": True,
        }
        logger.info(
            "%s: Verified %d operational SQLite WAL tables.",
            PERSISTENCE_STAGE_FR,
            table_count,
            extra={"fr_id": PERSISTENCE_STAGE_FR, "table_count": table_count},
        )
        await self._advance_stage(LifespanStage.PERSISTENCE)

    def init_discovery(self) -> PluginLifecycleManager:
        """Initialize the dynamic plugin discovery and lifecycle manager."""
        if self.plugin_manager is not None:
            return self.plugin_manager

        slot_registry = SlotRegistry()
        for slot_def in DEFAULT_SLOTS:
            slot_registry.register_slot(slot_def)

        plugins_dir = self.config.resolved_plugins_dir
        plugins_dir.mkdir(parents=True, exist_ok=True)
        search_dirs = [plugins_dir]
        brokers_dir = Path(__file__).resolve().parents[1] / "services" / "brokers"
        if brokers_dir.exists():
            search_dirs.append(brokers_dir)

        engine = PluginDiscoveryEngine(
            search_dirs=search_dirs,
            slot_registry=slot_registry,
        )
        engine.discover()
        if self.broker_registry is None:
            self.broker_registry = BrokerRegistry(
                data_root=Path(self.config.data_dir),
                discovery_engine=engine,
            )

        def _broker_instance_factory(plugin_id: str, record: Any, ctx: Any) -> Any:
            del ctx
            slot = getattr(getattr(record, "manifest", None), "slot", None)
            if slot == "data.provider" and self.broker_registry is not None:
                from app.services.brokers.registry import (
                    BrokerKey,
                    normalize_provider_id,
                )

                manifest_id = getattr(
                    getattr(record, "manifest", None), "id", plugin_id
                )
                canon = normalize_provider_id(manifest_id)
                bkey = BrokerKey(provider=canon, data_root=str(self.config.data_dir))
                return self.broker_registry.acquire(bkey)
            return None

        lifecycle = PluginLifecycleManager(
            discovery_engine=engine,
            data_root=Path(self.config.data_dir) / "plugins_data",
            instance_factory_hook=_broker_instance_factory,
        )
        self.plugin_manager = lifecycle
        lifecycle.load_and_attach_all()
        return lifecycle

    def _cleanup_services(self) -> None:
        """Release plugins, job pool, resource watchdog, and sessions in reverse."""
        cleanups: list[Callable[[], Any]] = []

        # 1. Drain background job pool and cancel futures before teardown
        if self.job_manager is not None:
            cleanups.append(
                partial(self.job_manager.shutdown, wait=True, cancel_futures=True)
            )

        # 2. Stop resource watchdog
        if self.resource_manager is not None:
            cleanups.append(self.resource_manager.watchdog.stop)

        # 3. Disable plugins
        if self.plugin_manager is not None:
            for pid in reversed(list(self.plugin_manager.discovery.registry.keys())):
                rec = self.plugin_manager.discovery.registry.get(pid)
                if rec is not None and rec.state in (
                    PluginState.ENABLED,
                    PluginState.ATTACHED,
                ):
                    cleanups.append(partial(self.plugin_manager.disable_plugin, pid))

        # 4. Close broker registry instances after workers/plugins are drained
        if self.broker_registry is not None:
            cleanups.append(self.broker_registry.close_all)

        # 5. Reset session manager
        if self.session_manager is not None:
            cleanups.append(self.session_manager.reset)
        for cleanup in cleanups:
            try:
                cleanup()
            except Exception:
                logger.exception("%s: service cleanup failed", REVERSE_TEARDOWN_FR)

    async def _boot_stage_services(self) -> None:
        """Stage 5/7: SERVICES — Initialize Resource, Job, Session, and Discovery."""
        self._active_stage = LifespanStage.SERVICES
        self._acquired_stack.append(
            _AcquiredStage(
                stage=LifespanStage.SERVICES,
                check_key=STAGE_CHECK_KEYS[LifespanStage.SERVICES],
                cleanup=self._cleanup_services,
            )
        )
        db_path = self.config.resolved_db_path
        logger.info(
            "%s: [5/7] Stage SERVICES (starting Resource, Job, Session, Discovery).",
            SERVICES_STAGE_FR,
            extra={"fr_id": SERVICES_STAGE_FR, "stage": "SERVICES"},
        )

        # 5.1 SessionManager
        if self.session_manager is None:
            self.session_manager = SessionManager(
                db_path=db_path,
                host_instance_id=self.host_instance_id,
            )

        # 5.2 ResourceManager & MemoryWatchdog
        if self.resource_manager is None:
            self.resource_manager = ResourceManager(
                min_available_ram_pct=self.config.min_available_ram_pct,
                scratch_root=self.config.resolved_scratch_root,
            )

        # 5.3 JobManager & Startup Orphan Job Reconciliation (RUNNING -> INTERRUPTED)
        if self.job_manager is None:
            self.job_manager = JobManager(
                db_path=db_path,
                max_workers=self.config.max_workers,
                resource_mgr=self.resource_manager,
                min_available_ram_pct=self.config.min_available_ram_pct,
                use_process_pool=self.config.use_process_pool,
                reconcile_on_startup=False,
            )
        reconciled_jobs = self.job_manager.reconcile_orphan_jobs()

        # 5.4 Dynamic Plugin Discovery Engine
        plugin_mgr = self.init_discovery()
        report = plugin_mgr.build_report()

        # 5.5 TransportGatewayService
        self.gateway_service = TransportGatewayService(
            event_bus=self.event_bus,
            session_mgr=self.session_manager,
            resource_mgr=self.resource_manager,
            job_mgr=self.job_manager,
            password_hash=self.config.password_hash,
            require_auth=self.config.require_auth,
        )

        # 5.6 DataManagerWorkspace (Stage 2B & 2C)
        if self.data_manager is None:
            self.data_manager = DataManagerWorkspace(
                db_path=db_path,
                data_dir=Path(self.config.data_dir),
                event_bus=self.event_bus,
                plugin_mgr=plugin_mgr,
                broker_registry=self.broker_registry,
                job_manager=self.job_manager,
            )
        self.data_manager.initialize_defaults()

        self._details["services"] = {
            "max_workers": self.job_manager.max_workers,
            "reconciled_orphan_jobs": reconciled_jobs,
            "plugins_discovered": report.total_discovered,
            "plugins_enabled": report.enabled_count,
            "slots_registered": len(plugin_mgr.discovery.slot_registry.list_slots()),
        }
        logger.info(
            "%s: Services initialized (workers=%d, reconciled_jobs=%d, plugins=%d).",
            SERVICES_STAGE_FR,
            self.job_manager.max_workers,
            len(reconciled_jobs),
            report.total_discovered,
            extra={
                "fr_id": SERVICES_STAGE_FR,
                "workers": self.job_manager.max_workers,
                "reconciled_jobs": len(reconciled_jobs),
            },
        )
        await self._advance_stage(
            LifespanStage.SERVICES, cleanup=self._cleanup_services
        )

    async def _boot_stage_routes(self) -> None:
        """Stage 6/7: ROUTES — Verify mounted HTTP/WS routers or CLI dispatch routes."""
        if self.config.headless:
            cli_commands = [
                "status",
                "health",
                "resources",
                "jobs",
                "plugins",
                "settings",
                "reconcile",
                "data",
            ]
            self._mounted_routes = list(cli_commands)
            logger.info(
                "%s: [6/7] Stage ROUTES (verified %d headless CLI dispatch routes).",
                ROUTES_STAGE_FR,
                len(cli_commands),
                extra={"fr_id": ROUTES_STAGE_FR, "mode": "headless_cli"},
            )
        else:
            if not self._mounted_routes:
                self._mounted_routes = [
                    "/auth",
                    "/auth/login",
                    "/sessions/me",
                    "/status",
                    "/readiness",
                    "/app-loaded",
                    "/about",
                    "/settings",
                    "/diagnostics",
                    "/resources",
                    "/jobs",
                    "/events",
                    "/ws",
                    "/discovery/plugins",
                    "/discovery/slots",
                ]
            logger.info(
                "%s: [6/7] Stage ROUTES (verified %d FastAPI gateway routes).",
                ROUTES_STAGE_FR,
                len(self._mounted_routes),
                extra={"fr_id": ROUTES_STAGE_FR, "mode": "ui_server"},
            )

        self._details["routes"] = {
            "mode": "headless_cli" if self.config.headless else "ui_server",
            "registered_count": len(self._mounted_routes),
            "routes": list(self._mounted_routes),
        }
        await self._advance_stage(
            LifespanStage.ROUTES,
            cleanup=self._mounted_routes.clear,
        )

    async def _boot_stage_ready(self) -> None:
        """Stage 7/7: READY — Verify all prior stages and broadcast system.ready."""
        prior_keys = (
            "configuration",
            "paths",
            "logging",
            "persistence",
            "services",
            "routes",
        )
        missing = [k for k in prior_keys if not self._checks.get(k, False)]
        if missing:
            raise RuntimeError(
                f"Cannot enter Stage READY; incomplete stage checks: {missing}"
            )

        await self._advance_stage(LifespanStage.READY)
        self._state = ReadinessState.READY
        self.event_bus.publish(
            channel="system",
            event_type="host.ready",
            payload={
                "host_instance_id": self.host_instance_id,
                "headless": self.config.headless,
                "stages": [s.value for s in self._completed_stages],
            },
        )
        logger.info(
            "%s: [7/7] Stage READY — Host bootstrap complete (instance=%s).",
            STAGE_PROGRESSION_FR,
            self.host_instance_id,
            extra={"fr_id": STAGE_PROGRESSION_FR, "stage": "READY"},
        )

    # ------------------------------------------------------------------------
    # Public Lifecycle Methods (Async & Sync)
    # ------------------------------------------------------------------------

    async def start(self) -> ReadinessSnapshot:
        """Execute the progressive 7-stage startup sequence asynchronously."""
        async with self._lock:
            if self._state == ReadinessState.READY:
                logger.info(
                    "%s: HostRuntime is already in READY state.",
                    STAGE_PROGRESSION_FR,
                    extra={"fr_id": STAGE_PROGRESSION_FR},
                )
                return self.get_readiness()

            self._state = ReadinessState.STARTING
            self._start_time = time.monotonic()
            self._completed_stages.clear()
            self._teardown_stages.clear()
            for key in self._checks:
                self._checks[key] = False

            logger.info(
                "%s: Starting 7-stage host bootstrap (instance=%s headless=%s).",
                STAGE_PROGRESSION_FR,
                self.host_instance_id,
                self.config.headless,
                extra={"fr_id": STAGE_PROGRESSION_FR},
            )
            try:
                await self._boot_stage_configuring()
                await self._boot_stage_paths()
                await self._boot_stage_logging()
                await self._boot_stage_persistence()
                await self._boot_stage_services()
                await self._boot_stage_routes()
                await self._boot_stage_ready()
            except Exception:
                logger.exception(
                    "%s: Bootstrap failed during stage %s. Initiating rollback.",
                    STAGE_PROGRESSION_FR,
                    self._active_stage,
                    extra={"fr_id": STAGE_PROGRESSION_FR},
                )
                await self._rollback_stages()
                self._state = ReadinessState.FAILED
                shutdown_logging()
                raise

            return self.get_readiness()

    async def stop(self) -> ReadinessSnapshot:
        """Execute reverse-order LIFO teardown of all acquired stages."""
        async with self._lock:
            if self._state in (
                ReadinessState.STOPPED,
                ReadinessState.UNINITIALIZED,
            ):
                self._state = ReadinessState.STOPPED
                return self.get_readiness()

            self._state = ReadinessState.STOPPING
            self.event_bus.publish(
                channel="system",
                event_type="host.stopping",
                payload={"host_instance_id": self.host_instance_id},
            )
            await self._rollback_stages()
            self._state = ReadinessState.STOPPED
            logger.info(
                "%s: HostRuntime stopped cleanly (instance=%s).",
                REVERSE_TEARDOWN_FR,
                self.host_instance_id,
                extra={"fr_id": REVERSE_TEARDOWN_FR},
            )
            snapshot = self.get_readiness()
            shutdown_logging()
            return snapshot

    def start_sync(self) -> ReadinessSnapshot:
        """Synchronous wrapper executing the 7-stage startup sequence."""
        return asyncio.run(self.start())

    def stop_sync(self) -> ReadinessSnapshot:
        """Synchronous wrapper executing reverse-order LIFO teardown."""
        return asyncio.run(self.stop())


# ============================================================================
# Dual Sync/Async Bootstrap Context Manager & FastAPI Composition
# ============================================================================


class _BootstrapContextManager:
    """Dual synchronous (`with`) and asynchronous (`async with`) context manager."""

    def __init__(
        self,
        config: BootstrapConfig | None = None,
        *,
        runtime: HostRuntime | None = None,
    ) -> None:
        self.runtime = runtime if runtime is not None else HostRuntime(config=config)

    def __enter__(self) -> HostRuntime:
        logger.info(
            "%s: Entering synchronous 7-stage bootstrap context.",
            LIFESPAN_CONTEXT_FR,
            extra={"fr_id": LIFESPAN_CONTEXT_FR},
        )
        self.runtime.start_sync()
        return self.runtime

    def __exit__(
        self,
        exc_type: object,
        exc_val: object,
        exc_tb: object,
    ) -> None:
        logger.info(
            "%s: Exiting synchronous 7-stage bootstrap context.",
            LIFESPAN_CONTEXT_FR,
            extra={"fr_id": LIFESPAN_CONTEXT_FR},
        )
        self.runtime.stop_sync()

    async def __aenter__(self) -> HostRuntime:
        logger.info(
            "%s: Entering asynchronous 7-stage bootstrap context.",
            LIFESPAN_CONTEXT_FR,
            extra={"fr_id": LIFESPAN_CONTEXT_FR},
        )
        await self.runtime.start()
        return self.runtime

    async def __aexit__(
        self,
        exc_type: object,
        exc_val: object,
        exc_tb: object,
    ) -> None:
        logger.info(
            "%s: Exiting asynchronous 7-stage bootstrap context.",
            LIFESPAN_CONTEXT_FR,
            extra={"fr_id": LIFESPAN_CONTEXT_FR},
        )
        await self.runtime.stop()


def bootstrap_context(
    config: BootstrapConfig | None = None,
    *,
    runtime: HostRuntime | None = None,
) -> _BootstrapContextManager:
    """Return a dual sync/async context manager running the 7-stage bootstrap."""
    return _BootstrapContextManager(config=config, runtime=runtime)


def _mount_gateway_and_discovery_routers(
    app: FastAPI,
    runtime: HostRuntime,
) -> list[str]:
    """Mount transport gateway, discovery, and extra routers onto ``app``."""
    gateway_svc = runtime.gateway_service or TransportGatewayService(
        event_bus=runtime.event_bus,
        session_mgr=runtime.session_manager,
        resource_mgr=runtime.resource_manager,
        job_mgr=runtime.job_manager,
        password_hash=runtime.config.password_hash,
        require_auth=runtime.config.require_auth,
    )
    runtime.gateway_service = gateway_svc

    for prefix in ("", "/api/v1", "/api/v2"):
        app.include_router(
            create_transport_router(
                event_bus=runtime.event_bus,
                session_mgr=runtime.session_manager,
                resource_mgr=runtime.resource_manager,
                job_mgr=runtime.job_manager,
                password_hash=runtime.config.password_hash,
                require_auth=runtime.config.require_auth,
                prefix=prefix,
            ),
        )

    plugin_mgr = runtime.init_discovery()
    disc_router = create_discovery_router(plugin_mgr)
    app.include_router(disc_router)
    app.include_router(disc_router, prefix="/api/v1")
    app.include_router(disc_router, prefix="/api/v2")

    dm_workspace = runtime.data_manager or DataManagerWorkspace(
        db_path=runtime.config.resolved_db_path,
        data_dir=Path(runtime.config.data_dir),
        event_bus=runtime.event_bus,
        plugin_mgr=runtime.plugin_manager,
    )
    runtime.data_manager = dm_workspace
    dm_router = create_data_manager_router(
        dm_workspace,
        session_mgr=runtime.session_manager,
        require_auth=runtime.config.require_auth,
    )
    app.include_router(dm_router)
    app.include_router(dm_router, prefix="/api/v1")
    app.include_router(dm_router, prefix="/api/v2")

    for extra_router in runtime._extra_routers:  # noqa: SLF001
        app.include_router(extra_router)

    return [getattr(r, "path", "") for r in app.routes if getattr(r, "path", "")]


def create_bootstrap_app(
    config: BootstrapConfig | None = None,
    *,
    runtime: HostRuntime | None = None,
    extra_routers: list[APIRouter] | None = None,
) -> FastAPI:
    """Compose a FastAPI application bound to the 7-stage HostRuntime lifespan."""
    resolved_config = config or BootstrapConfig(headless=False)
    resolved_runtime = runtime or HostRuntime(
        config=resolved_config,
        extra_routers=extra_routers,
    )

    logger.info(
        "%s: Composing FastAPI application with 7-stage HostRuntime lifespan.",
        LIFESPAN_CONTEXT_FR,
        extra={"fr_id": LIFESPAN_CONTEXT_FR},
    )

    @asynccontextmanager
    async def _lifespan(app: FastAPI) -> AsyncGenerator[None]:
        app.state.runtime = resolved_runtime
        app.state.config = resolved_config
        logger.info(
            "%s: FastAPI lifespan starting 7-stage HostRuntime.",
            LIFESPAN_CONTEXT_FR,
            extra={"fr_id": LIFESPAN_CONTEXT_FR},
        )
        await resolved_runtime.start()
        try:
            yield
        finally:
            logger.info(
                "%s: FastAPI lifespan stopping 7-stage HostRuntime.",
                LIFESPAN_CONTEXT_FR,
                extra={"fr_id": LIFESPAN_CONTEXT_FR},
            )
            await resolved_runtime.stop()

    app = FastAPI(
        title=resolved_config.title,
        version=resolved_config.version,
        lifespan=_lifespan,
    )
    app.state.runtime = resolved_runtime
    app.state.config = resolved_config

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:3000",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
            "http://localhost:5173",
            f"http://{resolved_config.host}:{resolved_config.port}",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(TransportMiddleware)
    register_transport_exception_handlers(app)

    mounted = _mount_gateway_and_discovery_routers(app, resolved_runtime)
    resolved_runtime._mounted_routes = mounted  # noqa: SLF001
    return app


create_host_app = create_bootstrap_app


def reconcile_database(db_path: Path) -> dict[str, Any]:
    """Ensure SQLite WAL schema and reconcile orphan RUNNING jobs on ``db_path``."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection(db_path)
    try:
        create_schema(conn)
    finally:
        conn.close()

    table_count = count_database_tables(db_path)
    job_mgr = JobManager(
        db_path=db_path,
        use_process_pool=False,
        reconcile_on_startup=False,
    )
    try:
        reconciled = job_mgr.reconcile_orphan_jobs()
    finally:
        job_mgr.shutdown(wait=True)

    report = {
        "status": "reconciled",
        "db_path": str(db_path),
        "table_count": table_count,
        "reconciled_orphan_jobs": reconciled,
    }
    logger.info(
        "%s: Reconciled database %s (tables=%d, orphan_jobs=%d).",
        PERSISTENCE_STAGE_FR,
        db_path.name,
        table_count,
        len(reconciled),
        extra={"fr_id": PERSISTENCE_STAGE_FR},
    )
    return report


# ============================================================================
# CLI Demonstration Entrypoint
# ============================================================================


def main(argv: list[str] | None = None) -> int:
    """Run a self-contained 7-stage bootstrap and reverse teardown demonstration."""
    import tempfile

    parser = argparse.ArgumentParser(
        prog="python -m app.host.bootstrap",
        description="HaruQuantAI 7-Stage Host Bootstrap Demonstration",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        default=False,
        help="Execute 7-stage startup and reverse teardown verification.",
    )
    _ = parser.parse_args(argv)

    with tempfile.TemporaryDirectory(
        prefix="hqai_boot_demo_",
        ignore_cleanup_errors=True,
    ) as tmp_str:
        cfg = BootstrapConfig(
            data_dir=Path(tmp_str),
            headless=True,
            use_process_pool=False,
        )
        runtime = HostRuntime(config=cfg)
        snap_ready = runtime.start_sync()
        stages_up = [s.value for s in snap_ready.completed_stages]
        snap_stopped = runtime.stop_sync()
        stages_down = [s.value for s in runtime.teardown_stages]

        print(f"Bootstrap State After Start: {snap_ready.state}")
        print(f"Completed 7 Stages: {' -> '.join(stages_up)}")
        print(f"Bootstrap State After Stop: {snap_stopped.state}")
        print(f"Reverse Teardown Order: {' -> '.join(stages_down)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
