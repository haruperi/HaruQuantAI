# ruff: noqa: INP001
"""Progressive 7-stage host bootstrap state machine and lifecycle coordinator.

Description:
    Implements the ordered 7-stage progressive startup state machine and
    automatic reverse-order (LIFO) teardown coordinator for the HaruQuantAI
    Tier 1 Host Platform (CONFIGURING -> PATHS -> LOGGING -> PERSISTENCE ->
    SERVICES -> ROUTES -> READY) via five canonical lifecycle methods.

Purpose:
    FEAT-HOST-BOOT - Progressive 7-stage host bootstrap state machine, service
    coordinator, and reverse-order LIFO teardown lifecycle.

Key Capabilities:
    - FR-HOST-BOOT-STAGE-PROGRESSION: Validate runtime configuration, create and
      inspect workspace directory paths, initialize telemetry, and build FastAPI.
    - FR-HOST-BOOT-PERSISTENCE-STAGE: Initialize SQLite WAL persistence, verify
      all 25 operational database tables, and reload host settings.
    - FR-HOST-BOOT-MODULE-REGISTRATION: Register SessionManager, ResourceMonitor,
      JobManager with orphan recovery, PluginLifecycleManager, and routes.
    - FR-HOST-BOOT-EVENT-BROADCAST: Broadcast events across the EventBus and
      transition the host to READY when publishing system/host.ready.
    - FR-HOST-BOOT-REVERSE-TEARDOWN: Broadcast host.stopping and release all
      acquired resources and stages in strict reverse LIFO order.

Python API Usage:
    from pathlib import Path
    from app.host.bootstrap import AppHost

    host = AppHost(data_dir=Path("data"), headless=True)

CLI Usage:
    uv run python -m app.host.bootstrap --check-only
"""

from __future__ import annotations

import argparse
import asyncio
import concurrent.futures
import inspect
import sys
import tempfile
import threading
import time
import uuid
from collections.abc import Callable, Generator, Mapping
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from functools import partial
from pathlib import Path
from typing import Any, Final

from app.host import discovery as _disc
from app.host import logging as _log
from app.host import resources as _res
from app.host import transport as _tr
from app.host.jobs import JobManager
from app.host.persistence import HostPersistence
from app.host.session import SessionManager
from app.host.settings import settings as host_settings
from app.services.brokers import get_broker
from app.workspace.data_manager import DataManagerWorkspace, create_data_manager_router
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

__all__ = ["AppHost"]

logger = _log.get_logger(__name__)

STAGE_PROGRESSION_FR: Final[str] = "FR-HOST-BOOT-STAGE-PROGRESSION"
PERSISTENCE_STAGE_FR: Final[str] = "FR-HOST-BOOT-PERSISTENCE-STAGE"
MODULE_REGISTRATION_FR: Final[str] = "FR-HOST-BOOT-MODULE-REGISTRATION"
EVENT_BROADCAST_FR: Final[str] = "FR-HOST-BOOT-EVENT-BROADCAST"
REVERSE_TEARDOWN_FR: Final[str] = "FR-HOST-BOOT-REVERSE-TEARDOWN"

_MIN_PORT: Final[int] = 1
_MAX_PORT: Final[int] = 65535
_EXPECTED_TABLE_COUNT: Final[int] = len(HostPersistence.TABLE_PRIMARY_KEYS)
_CLI_ROUTES: Final[str] = "status health resources jobs plugins settings reconcile data"
_UI_ROUTES: Final[str] = (
    "/auth /auth/login /sessions/me /status /readiness /app-loaded /about /settings "
    "/diagnostics /resources /jobs /events /ws /discovery/plugins /discovery/slots "
    "/connections /constants /specs"
)

DEFAULT_SLOTS: Final[tuple[_disc.SlotDefinition, ...]] = (
    _disc.SlotDefinition(
        slot_id="data.provider",
        description="Market data feed provider adapter slot.",
        allow_multiple=True,
    ),
    _disc.SlotDefinition(
        slot_id="validation.crosscheck",
        description="Robustness and cross-check validation plugin slot.",
        allow_multiple=True,
    ),
    _disc.SlotDefinition(
        slot_id="export.platform",
        description="Strategy source code platform exporter slot.",
        allow_multiple=True,
    ),
    _disc.SlotDefinition(
        slot_id="strategy.block",
        description="Strategy building block and indicator plugin slot.",
        allow_multiple=True,
    ),
)


def _dct(**kw: Any) -> dict[str, Any]:
    return kw


def _info(fr_id: str, msg: str, **extra: Any) -> None:
    logger.info("%s: %s", fr_id, msg, extra={"fr_id": fr_id, **extra})


class _LifespanStage(StrEnum):
    """Canonical 7-stage progressive bootstrap sequence."""

    CONFIGURING = "CONFIGURING"
    PATHS = "PATHS"
    LOGGING = "LOGGING"
    PERSISTENCE = "PERSISTENCE"
    SERVICES = "SERVICES"
    ROUTES = "ROUTES"
    READY = "READY"


_ORDERED_BOOT_STAGES: Final[tuple[_LifespanStage, ...]] = tuple(_LifespanStage)

_STAGE_CHECK_KEYS: Final[dict[_LifespanStage, str]] = {
    _LifespanStage.CONFIGURING: "configuration",
    _LifespanStage.PATHS: "paths",
    _LifespanStage.LOGGING: "logging",
    _LifespanStage.PERSISTENCE: "persistence",
    _LifespanStage.SERVICES: "services",
    _LifespanStage.ROUTES: "routes",
    _LifespanStage.READY: "ready",
}


class _ReadinessState(StrEnum):
    """High-level lifecycle states of AppHost."""

    UNINITIALIZED = "UNINITIALIZED"
    STARTING = "STARTING"
    READY = "READY"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class _BootstrapConfig:
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
    log_dir: Path | None = None
    scratch_root: Path | None = None
    plugins_dir: Path | None = None
    max_workers: int | None = None
    use_process_pool: bool = True
    min_available_ram_pct: float = _res.MIN_AVAILABLE_RAM_PCT
    timeout_graceful_shutdown: int = 10

    @property
    def resolved_log_dir(self) -> Path:
        """Return effective log directory path."""
        return Path(self.log_dir) if self.log_dir else Path(self.data_dir) / "logs"

    @property
    def resolved_scratch_root(self) -> Path:
        """Return effective per-job scratch root directory path."""
        return (
            Path(self.scratch_root)
            if self.scratch_root
            else Path(self.data_dir) / "scratch"
        )

    @property
    def resolved_plugins_dir(self) -> Path:
        """Return effective dynamic plugins root directory path."""
        return (
            Path(self.plugins_dir)
            if self.plugins_dir
            else Path(self.data_dir) / "plugins"
        )


@dataclass(frozen=True)
class _ReadinessSnapshot:
    """Immutable point-in-time readiness report of AppHost."""

    state: _ReadinessState
    is_ready: bool
    headless: bool
    host_instance_id: str
    uptime_seconds: float
    timestamp: str
    active_stage: _LifespanStage | None
    completed_stages: list[_LifespanStage]
    checks: dict[str, bool]
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Serialize _ReadinessSnapshot to a plain dictionary."""
        raw = asdict(self)
        raw["state"] = str(self.state)
        raw["active_stage"] = str(self.active_stage) if self.active_stage else None
        raw["completed_stages"] = [str(s) for s in self.completed_stages]
        return raw


@dataclass(frozen=True)
class _AcquiredStage:
    """Internal LIFO stack entry recording an acquired stage and its cleanup."""

    stage: _LifespanStage
    check_key: str
    cleanup: Callable[[], Any] | None = None


async def _eval_awaitable(aw: Any) -> Any:
    return await aw


def _run_sync_or_async(res: Any) -> None:
    if not inspect.isawaitable(res):
        return
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop is not None and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            ex.submit(asyncio.run, _eval_awaitable(res)).result()
    else:
        asyncio.run(_eval_awaitable(res))


class AppHost:
    """Progressive 7-stage host runtime state machine with reverse LIFO teardown."""

    Stage = _LifespanStage
    State = _ReadinessState
    ORDERED_STAGES = _ORDERED_BOOT_STAGES
    Config = _BootstrapConfig
    Snapshot = _ReadinessSnapshot

    def __init__(self, config: _BootstrapConfig | None = None, **kw: Any) -> None:
        """Initialize the AppHost state machine in UNINITIALIZED state."""
        self.config = config or _BootstrapConfig(
            title=kw.get("title", "HaruQuantAI Host Gateway"),
            version=kw.get("version", "1.0.0"),
            host=kw.get("host", "127.0.0.1"),
            port=kw.get("port", 8000),
            debug=bool(kw.get("debug", False)),
            headless=bool(kw.get("headless", False)),
            require_auth=bool(kw.get("require_auth", False)),
            password_hash=kw.get("password_hash"),
            data_dir=kw.get("data_dir") or Path("data"),
            log_dir=kw.get("log_dir"),
            scratch_root=kw.get("scratch_root"),
            plugins_dir=kw.get("plugins_dir"),
            max_workers=kw.get("max_workers"),
            use_process_pool=bool(kw.get("use_process_pool", True)),
            min_available_ram_pct=float(
                kw.get("min_available_ram_pct", _res.MIN_AVAILABLE_RAM_PCT)
            ),
            timeout_graceful_shutdown=int(kw.get("timeout_graceful_shutdown", 10)),
        )
        self.host_instance_id = f"host-{uuid.uuid4().hex[:12]}"
        self._write_lock_obj = threading.RLock()
        self._state = _ReadinessState.UNINITIALIZED
        self._active_stage: _LifespanStage | None = None
        self._completed_stages: list[_LifespanStage] = []
        self._teardown_stages: list[_LifespanStage] = []
        self._acquired_stack: list[_AcquiredStage] = []
        self._start_time: float | None = None
        self._checks: dict[str, bool] = dict.fromkeys(_STAGE_CHECK_KEYS.values(), False)
        self._details: dict[str, Any] = {}
        hooks: Mapping[_LifespanStage, Callable[[AppHost], Any]] | None = kw.get(
            "stage_hooks"
        )
        self._stage_hooks = dict(hooks or {})
        self._extra_routers: list[APIRouter] = list(kw.get("extra_routers") or [])
        self._mounted_routes: list[str] = []
        self.app: FastAPI | None = None
        self.event_bus: _tr.EventBus = kw.get("event_bus") or _tr.get_global_event_bus()
        self.session_manager: SessionManager | None = kw.get("session_mgr")
        self.resource_manager: _res.ResourceMonitor | None = kw.get("resource_mgr")
        self.job_manager: JobManager | None = kw.get("job_mgr")
        self.plugin_manager: _disc.PluginLifecycleManager | None = kw.get("plugin_mgr")
        self.broker_registry: Any | None = kw.get("broker_registry")
        self.gateway_service: _tr.TransportGatewayService | None = None
        self.data_manager: DataManagerWorkspace | None = None

    @property
    def state(self) -> _ReadinessState:
        """Return current readiness state."""
        return self._state

    @property
    def active_stage(self) -> _LifespanStage | None:
        """Return currently active bootstrap stage."""
        return self._active_stage

    @property
    def completed_stages(self) -> list[_LifespanStage]:
        """Return ordered list of completed bootstrap stages."""
        return list(self._completed_stages)

    @property
    def teardown_stages(self) -> list[_LifespanStage]:
        """Return ordered list of stages released during the most recent teardown."""
        return list(self._teardown_stages)

    @property
    def mounted_routes(self) -> list[str]:
        """Return list of route paths or CLI commands registered in Stage 6."""
        return list(self._mounted_routes)

    def _fail_boot(self, fr_id: str, msg: str) -> None:
        logger.error("%s: %s", fr_id, msg, extra={"fr_id": fr_id})
        self._rollback_stages()
        self._state = _ReadinessState.FAILED
        _log.shutdown_logging()

    def startup(self) -> FastAPI:
        """Bootstrap host runtime, directory paths, telemetry, and FastAPI app."""
        if self._state == _ReadinessState.READY:
            _info(STAGE_PROGRESSION_FR, "Host is already in READY state.")
            if self.app is None:
                self.app = self._create_app()
            return self.app
        s1_3 = (
            _LifespanStage.CONFIGURING,
            _LifespanStage.PATHS,
            _LifespanStage.LOGGING,
        )
        if all(s in self._completed_stages for s in s1_3) and self.app is not None:
            return self.app
        self._state = _ReadinessState.STARTING
        if self._start_time is None:
            self._start_time = time.monotonic()
        _info(
            STAGE_PROGRESSION_FR,
            f"Starting bootstrap (instance={self.host_instance_id} "
            f"headless={self.config.headless}).",
        )
        try:
            self._boot_stage_configuring()
            self._boot_stage_paths()
            self._boot_stage_logging()
            if self.app is None:
                self.app = self._create_app()
            return self.app
        except Exception:
            self._fail_boot(
                STAGE_PROGRESSION_FR,
                f"Startup failed during stage {self._active_stage}.",
            )
            raise

    def initialize_db(self) -> bool:
        """Initialize SQLite WAL persistence, schema verification, and write locks."""
        if _LifespanStage.PERSISTENCE in self._completed_stages:
            return True
        s1_3 = (
            _LifespanStage.CONFIGURING,
            _LifespanStage.PATHS,
            _LifespanStage.LOGGING,
        )
        if not all(s in self._completed_stages for s in s1_3):
            self.startup()
        try:
            self._boot_stage_persistence()
        except Exception:
            self._fail_boot(
                PERSISTENCE_STAGE_FR,
                "Persistence initialization failed. Initiating rollback.",
            )
            raise
        return True

    def register_modules(self, app: FastAPI | None = None) -> None:
        """Register and initialize all domain services, recovery, and routing."""
        if (
            _LifespanStage.SERVICES in self._completed_stages
            and _LifespanStage.ROUTES in self._completed_stages
        ):
            return
        if _LifespanStage.PERSISTENCE not in self._completed_stages:
            self.initialize_db()
        try:
            self._boot_stage_services()
            self._boot_stage_routes(app or self.app)
        except Exception:
            self._fail_boot(
                MODULE_REGISTRATION_FR,
                f"Module registration failed during stage {self._active_stage}.",
            )
            raise

    def broadcast_event(
        self,
        channel: str,
        event_type: str = "update",
        payload: dict[str, Any] | None = None,
    ) -> _tr.HostEvent:
        """Broadcast an event across the event bus and advance state on host.ready."""
        ev = self.event_bus.publish(
            channel=channel, event_type=event_type, payload=payload or {}
        )
        logger.debug(
            "%s: Broadcast event (channel=%s, event_type=%s).",
            EVENT_BROADCAST_FR,
            channel,
            event_type,
            extra=_dct(
                fr_id=EVENT_BROADCAST_FR, channel=channel, event_type=event_type
            ),
        )
        if channel == "system" and event_type == "host.ready":
            try:
                self._boot_stage_ready()
                self._state = _ReadinessState.READY
                _info(
                    EVENT_BROADCAST_FR,
                    f"[7/7] Stage READY — Host bootstrap complete "
                    f"(instance={self.host_instance_id}).",
                    stage="READY",
                )
            except Exception:
                self._fail_boot(
                    EVENT_BROADCAST_FR,
                    "Ready stage transition failed. Initiating rollback.",
                )
                raise
        return ev

    def shutdown(self) -> None:
        """Manage graceful application shutdown and reverse-order LIFO cleanup."""
        if self._state in (_ReadinessState.STOPPED, _ReadinessState.UNINITIALIZED):
            self._state = _ReadinessState.STOPPED
            return
        self._state = _ReadinessState.STOPPING
        try:
            self.broadcast_event(
                "system",
                "host.stopping",
                {"host_instance_id": self.host_instance_id},
            )
        except Exception:
            logger.exception(
                "%s: Failed broadcasting host.stopping event.", REVERSE_TEARDOWN_FR
            )
        self._rollback_stages()
        self._state = _ReadinessState.STOPPED
        _info(
            REVERSE_TEARDOWN_FR,
            f"AppHost stopped cleanly (instance={self.host_instance_id}).",
        )
        _log.shutdown_logging()

    def _is_ready(self) -> bool:
        return (
            self._state == _ReadinessState.READY
            and self._active_stage == _LifespanStage.READY
            and all(self._checks.values())
        )

    def _get_readiness(self) -> _ReadinessSnapshot:
        ready = self._is_ready()
        now_iso = datetime.now(UTC).isoformat()
        uptime = (
            max(0.0, time.monotonic() - self._start_time)
            if self._start_time is not None
            else 0.0
        )
        if ready:
            logger.debug(
                "%s: Host READY (instance=%s uptime=%.3fs).",
                STAGE_PROGRESSION_FR,
                self.host_instance_id,
                uptime,
                extra={"fr_id": STAGE_PROGRESSION_FR},
            )
        else:
            logger.warning(
                "%s: Host not ready (state=%s stage=%s).",
                STAGE_PROGRESSION_FR,
                self._state,
                self._active_stage,
                extra={"fr_id": STAGE_PROGRESSION_FR},
            )
        return _ReadinessSnapshot(
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

    @contextmanager
    def _write_lock(self) -> Generator[None]:
        with self._write_lock_obj:
            yield

    @staticmethod
    def _reconcile_database() -> dict[str, Any]:
        host_settings.reload()
        tc = len(HostPersistence.PERSISTENCE_TABLES)
        jm = JobManager(use_process_pool=False, reconcile_on_startup=False)
        try:
            reconciled = jm.reconcile_orphan_jobs()
        finally:
            jm.shutdown(wait=True)
        _info(
            PERSISTENCE_STAGE_FR,
            f"Reconciled database (tables={tc}, orphan_jobs={len(reconciled)}).",
        )
        return _dct(
            status="reconciled",
            table_count=tc,
            reconciled_orphan_jobs=reconciled,
        )

    def _advance_stage(
        self, stage: _LifespanStage, cleanup: Callable[[], Any] | None = None
    ) -> None:
        check_key = _STAGE_CHECK_KEYS[stage]
        self._active_stage = stage
        entry = _AcquiredStage(stage=stage, check_key=check_key, cleanup=cleanup)
        if not any(item.stage == stage for item in self._acquired_stack):
            self._acquired_stack.append(entry)
        elif cleanup is not None:
            for idx, item in enumerate(self._acquired_stack):
                if item.stage == stage:
                    self._acquired_stack[idx] = entry
        if (hook := self._stage_hooks.get(stage)) is not None:
            _run_sync_or_async(hook(self))
        self._checks[check_key] = True
        if stage not in self._completed_stages:
            self._completed_stages.append(stage)
        n = len(self._completed_stages)
        _info(
            STAGE_PROGRESSION_FR,
            f"Advanced to stage {stage.value} ({n}/7) [{self.host_instance_id}].",
            stage=stage.value,
            instance=self.host_instance_id,
        )

    def _rollback_stages(self) -> None:
        self._teardown_stages.clear()
        _info(
            REVERSE_TEARDOWN_FR,
            f"Starting reverse LIFO teardown of {len(self._acquired_stack)} stages.",
        )
        while self._acquired_stack:
            acq = self._acquired_stack.pop()
            st = acq.stage
            try:
                if acq.cleanup is not None:
                    _run_sync_or_async(acq.cleanup())
                self._teardown_stages.append(st)
                _info(
                    REVERSE_TEARDOWN_FR,
                    f"Released stage {st.value} in reverse order.",
                    stage=st.value,
                )
            except Exception:
                self._teardown_stages.append(st)
                logger.exception(
                    "%s: Exception releasing stage %s.",
                    REVERSE_TEARDOWN_FR,
                    st.value,
                    extra={"fr_id": REVERSE_TEARDOWN_FR, "stage": st.value},
                )
            finally:
                self._checks[acq.check_key] = False
        self._active_stage = None

    def _boot_stage_configuring(self) -> None:
        self._active_stage, c = _LifespanStage.CONFIGURING, self.config
        _info(
            STAGE_PROGRESSION_FR,
            f"[1/7] Stage CONFIGURING (host={c.host} port={c.port}).",
            stage="CONFIGURING",
        )
        if not c.host or not c.host.strip():
            raise ValueError("AppHost host must be a non-empty string.")
        if not (_MIN_PORT <= c.port <= _MAX_PORT):
            raise ValueError(
                f"Invalid host port number: {c.port} ({_MIN_PORT}..{_MAX_PORT})."
            )
        if c.min_available_ram_pct <= 0.0:
            raise ValueError("min_available_ram_pct must be positive.")
        self._details.update(
            mode="headless_cli" if c.headless else "ui_server",
            host=c.host,
            port=c.port,
        )
        self._advance_stage(_LifespanStage.CONFIGURING)

    def _boot_stage_paths(self) -> None:
        base_dir = Path(self.config.data_dir)
        log_dir = self.config.resolved_log_dir
        scratch_dir = self.config.resolved_scratch_root
        plugins_dir = self.config.resolved_plugins_dir
        _info(
            STAGE_PROGRESSION_FR,
            f"[2/7] Stage PATHS (data_dir={base_dir}).",
            stage="PATHS",
        )
        for d in (base_dir, log_dir, scratch_dir, plugins_dir, base_dir / "resources"):
            d.mkdir(parents=True, exist_ok=True)
        rep = _res.inspect_workspace_directories()
        self._details["paths"] = _dct(
            data_dir=str(base_dir),
            log_dir=str(log_dir),
            scratch_root=str(scratch_dir),
            plugins_dir=str(plugins_dir),
            inspected_count=len(rep),
        )
        self._advance_stage(_LifespanStage.PATHS)

    def _boot_stage_logging(self) -> None:
        log_dir = self.config.resolved_log_dir
        lvl_name = "DEBUG" if self.config.debug else "INFO"
        lvl_int = 10 if self.config.debug else 20
        _info(
            STAGE_PROGRESSION_FR,
            f"[3/7] Stage LOGGING (log_dir={log_dir} level={lvl_name}).",
            stage="LOGGING",
        )
        _log.setup_logging(
            log_dir=log_dir, level=lvl_int, publish_log=self._publish_log
        )
        ring = _log.get_ring_buffer()
        self._details["logging"] = _dct(
            level=lvl_name,
            ring_buffer_records=len(ring),
            ring_buffer_capacity=ring.maxlen,
        )
        self._advance_stage(_LifespanStage.LOGGING, cleanup=_log.flush_logs)

    def _publish_log(self, entry: dict[str, Any]) -> None:
        self.event_bus.publish(channel="logs", event_type="log", payload=entry)

    def _boot_stage_persistence(self) -> None:
        _info(
            PERSISTENCE_STAGE_FR,
            "[4/7] Stage PERSISTENCE (initializing WAL schema).",
            stage="PERSISTENCE",
        )
        host_settings.reload()
        tc = len(HostPersistence.PERSISTENCE_TABLES)
        if tc < _EXPECTED_TABLE_COUNT:
            raise RuntimeError(
                f"Schema verification failed: expected >= {_EXPECTED_TABLE_COUNT}, "
                f"found {tc}."
            )
        self._details["persistence"] = _dct(table_count=tc, wal_mode=True)
        _info(
            PERSISTENCE_STAGE_FR,
            f"Verified {tc} operational SQLite WAL tables.",
            table_count=tc,
        )
        self._advance_stage(_LifespanStage.PERSISTENCE)

    def _init_discovery(self) -> _disc.PluginLifecycleManager:
        if self.plugin_manager is not None:
            return self.plugin_manager
        slot_reg = _disc.SlotRegistry()
        for slot_def in DEFAULT_SLOTS:
            slot_reg.register_slot(slot_def)
        plugins_dir = self.config.resolved_plugins_dir
        plugins_dir.mkdir(parents=True, exist_ok=True)
        search_dirs = [plugins_dir]
        brokers_dir = Path(__file__).resolve().parents[1] / "services" / "brokers"
        if brokers_dir.exists():
            search_dirs.append(brokers_dir)
        engine = _disc.PluginDiscovery(search_dirs=search_dirs, slot_registry=slot_reg)
        engine.discover_plugins()

        def _broker_factory(plugin_id: str, record: Any, ctx: Any) -> Any:
            del ctx
            manifest = getattr(record, "manifest", None)
            if getattr(manifest, "slot", None) != "data.provider":
                return None
            mid = getattr(manifest, "id", plugin_id)
            try:
                return get_broker(mid)
            except (
                RuntimeError,
                ValueError,
                TypeError,
                KeyError,
                OSError,
                ImportError,
            ) as err:
                logger.warning(
                    "%s: Could not acquire broker client for %s: %s",
                    MODULE_REGISTRATION_FR,
                    mid,
                    err,
                    extra={"fr_id": MODULE_REGISTRATION_FR},
                )
                return None

        lifecycle = _disc.PluginLifecycleManager(
            discovery_engine=engine,
            data_root=Path(self.config.data_dir) / "plugins_data",
            instance_factory_hook=_broker_factory,
        )
        self.plugin_manager = lifecycle
        lifecycle.load_and_attach_all()
        return lifecycle

    def _cleanup_services(self) -> None:
        cleanups: list[Callable[[], Any]] = []
        if self.job_manager is not None:
            cleanups.append(
                partial(self.job_manager.shutdown, wait=True, cancel_futures=True)
            )
        if self.resource_manager is not None:
            cleanups.append(self.resource_manager.watchdog.stop)
        if self.plugin_manager is not None:
            reg = self.plugin_manager.discovery.registry
            active_states = (_disc.PluginState.ENABLED, _disc.PluginState.ATTACHED)
            cleanups.extend(
                partial(self.plugin_manager.disable_plugin, pid)
                for pid in reversed(list(reg.keys()))
                if (rec := reg.get(pid)) is not None and rec.state in active_states
            )
        if self.broker_registry is not None:
            cleanups.append(self.broker_registry.close_all)
        if self.session_manager is not None:
            cleanups.append(self.session_manager.reset)
        for fn in cleanups:
            try:
                fn()
            except Exception:
                logger.exception("%s: service cleanup failed", REVERSE_TEARDOWN_FR)

    def _boot_stage_services(self) -> None:
        self._active_stage = _LifespanStage.SERVICES
        self._acquired_stack.append(
            _AcquiredStage(
                _LifespanStage.SERVICES,
                _STAGE_CHECK_KEYS[_LifespanStage.SERVICES],
                self._cleanup_services,
            )
        )
        _info(
            MODULE_REGISTRATION_FR,
            "[5/7] Stage SERVICES (starting Resource, Job, Session, Discovery).",
            stage="SERVICES",
        )
        if self.session_manager is None:
            self.session_manager = SessionManager(
                host_instance_id=self.host_instance_id
            )
        if self.resource_manager is None:
            self.resource_manager = _res.ResourceMonitor(
                min_available_ram_pct=self.config.min_available_ram_pct,
                scratch_root=self.config.resolved_scratch_root,
            )
        if self.job_manager is None:
            self.job_manager = JobManager(
                max_workers=self.config.max_workers,
                resource_mgr=self.resource_manager,
                min_available_ram_pct=self.config.min_available_ram_pct,
                use_process_pool=self.config.use_process_pool,
                reconcile_on_startup=False,
            )
        reconciled = self.job_manager.reconcile_orphan_jobs()
        plugin_mgr = self._init_discovery()
        rep = plugin_mgr.build_report()
        if self.gateway_service is None:
            self.gateway_service = _tr.TransportGatewayService(
                event_bus=self.event_bus,
                session_mgr=self.session_manager,
                resource_mgr=self.resource_manager,
                job_mgr=self.job_manager,
                password_hash=self.config.password_hash,
                require_auth=self.config.require_auth,
            )
        if self.data_manager is None:
            self.data_manager = DataManagerWorkspace(
                data_dir=Path(self.config.data_dir),
                event_bus=self.event_bus,
                plugin_mgr=plugin_mgr,
                broker_registry=self.broker_registry,
                job_manager=self.job_manager,
            )
        self.data_manager.initialize_defaults()
        mw = self.job_manager.max_workers
        slots = len(plugin_mgr.discovery.slot_registry.list_slots())
        self._details["services"] = _dct(
            max_workers=mw,
            reconciled_orphan_jobs=reconciled,
            plugins_discovered=rep.total_discovered,
            plugins_enabled=rep.enabled_count,
            slots_registered=slots,
        )
        _info(
            MODULE_REGISTRATION_FR,
            f"Services initialized (workers={mw}, reconciled_jobs={len(reconciled)}, "
            f"plugins={rep.total_discovered}).",
            workers=mw,
            reconciled_jobs=len(reconciled),
        )
        self._advance_stage(_LifespanStage.SERVICES, cleanup=self._cleanup_services)

    def _boot_stage_routes(self, app: FastAPI | None = None) -> None:
        if self.config.headless:
            self._mounted_routes = _CLI_ROUTES.split()
            mode = "headless_cli"
        else:
            target = app or self.app
            self._mounted_routes = (
                self._mount_routers(target)
                if target is not None
                else _UI_ROUTES.split()
            )
            mode = "ui_server"
        cnt = len(self._mounted_routes)
        _info(
            MODULE_REGISTRATION_FR,
            f"[6/7] Stage ROUTES (verified {cnt} routes, mode={mode}).",
            mode=mode,
        )
        self._details["routes"] = _dct(
            mode=mode, registered_count=cnt, routes=list(self._mounted_routes)
        )
        self._advance_stage(_LifespanStage.ROUTES, cleanup=self._mounted_routes.clear)

    def _boot_stage_ready(self) -> None:
        prior = (
            "configuration",
            "paths",
            "logging",
            "persistence",
            "services",
            "routes",
        )
        if missing := [k for k in prior if not self._checks.get(k, False)]:
            raise RuntimeError(
                f"Cannot enter Stage READY; incomplete stage checks: {missing}"
            )
        self._advance_stage(_LifespanStage.READY)

    def _create_app(self) -> FastAPI:
        app = FastAPI(title=self.config.title, version=self.config.version)
        app.state.runtime, app.state.config = self, self.config
        origins = [
            f"http://{h}:{p}" for h in ("127.0.0.1", "localhost") for p in (3000, 5173)
        ] + [f"http://{self.config.host}:{self.config.port}"]
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        app.add_middleware(_tr.TransportMiddleware)
        _tr.register_transport_exception_handlers(app)

        @app.get("/api/v1/system/health")
        def _system_health() -> dict[str, Any]:
            return {"status": "ok", "state": self._state.value}

        @app.get("/api/v1/system/readiness")
        def _system_readiness() -> dict[str, Any]:
            return self._get_readiness().to_dict()

        return app

    def _mount_routers(self, app: FastAPI) -> list[str]:
        gw_kw = _dct(
            host_settings=host_settings,
            event_bus=self.event_bus,
            session_mgr=self.session_manager,
            resource_mgr=self.resource_manager,
            job_mgr=self.job_manager,
            password_hash=self.config.password_hash,
            require_auth=self.config.require_auth,
        )
        self.gateway_service = self.gateway_service or _tr.TransportGatewayService(
            **gw_kw
        )
        disc_router = _disc.create_discovery_router(self._init_discovery())
        self.data_manager = self.data_manager or DataManagerWorkspace(
            data_dir=Path(self.config.data_dir),
            event_bus=self.event_bus,
            plugin_mgr=self.plugin_manager,
        )
        dm_router = create_data_manager_router(
            self.data_manager,
            session_mgr=self.session_manager,
            require_auth=self.config.require_auth,
        )
        for pfx in ("", "/api/v1", "/api/v2"):
            app.include_router(_tr.create_transport_router(prefix=pfx, **gw_kw))
            app.include_router(disc_router, prefix=pfx)
            app.include_router(dm_router, prefix=pfx)
        for extra in self._extra_routers:
            app.include_router(extra)
        return [getattr(r, "path", "") for r in app.routes if getattr(r, "path", "")]


def main(argv: list[str] | None = None) -> int:
    """Run a self-contained 7-stage bootstrap and reverse teardown demonstration."""
    parser = argparse.ArgumentParser(prog="python -m app.host.bootstrap")
    parser.add_argument("--check-only", action="store_true", default=False)
    _ = parser.parse_args(argv)
    with tempfile.TemporaryDirectory(
        prefix="hqai_boot_demo_", ignore_cleanup_errors=True
    ) as tmp_str:
        orig_db = HostPersistence.DEFAULT_DB_PATH
        HostPersistence.DEFAULT_DB_PATH = Path(tmp_str) / "database" / "haruquantai.db"
        try:
            host = AppHost(
                data_dir=Path(tmp_str), headless=True, use_process_pool=False
            )
            host.startup()
            host.initialize_db()
            host.register_modules()
            host.broadcast_event("system", "host.ready")
            up_stages = " -> ".join(s.value for s in host.completed_stages)
            up_state = host.state.value
            host.shutdown()
            down_stages = " -> ".join(s.value for s in host.teardown_stages)
            down_state = host.state.value
            sys.stdout.write(
                f"Bootstrap State After Start: {up_state}\n"
                f"Completed 7 Stages: {up_stages}\n"
                f"Bootstrap State After Stop: {down_state}\n"
                f"Reverse Teardown Order: {down_stages}\n"
            )
        finally:
            HostPersistence.DEFAULT_DB_PATH = orig_db
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
