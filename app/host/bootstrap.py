"""Host Lifecycle Orchestration, Phase Supervision, and Service Initialization.

Description:
    This module provides the central lifecycle engine and composition root for
    the HaruQuantAI host process. It exists to guarantee deterministic, observable
    boot progression and orderly, reverse-order resource disposal. Externally, it
    participates in three critical workflows: (1) The application entrypoint
    (`app.main`) instantiates `BootstrapCoordinator` and hands it to the ASGI
    transport layer (`app.host.transport`); (2) The ASGI HTTP/WebSocket lifespan
    drives the asynchronous `initialize()` and `close()` lifecycle stages; and (3)
    Connected UI and WebSocket clients query startup snapshots and subscribe to the
    `boot.progress` event stream (`app.host.events`) while tracking connection
    readiness before accessing workspace resources. Internally, `Startup` models an
    in-memory finite state machine that advances through 5 discrete stages
    (`runtime`, `services`, `packages`, `transport`, `serving`), records monotonic
    phase durations, invokes injected `LifecycleHook` providers, and manages client
    handshake deadlines. `BootstrapCoordinator` sits above `Startup`, orchestrating
    the physical subsystem allocations: acquiring the installation filesystem lease,
    configuring rotating JSON telemetry, initializing SQLite persistence and
    operator sessions, discovering presets, measuring hardware capabilities,
    allocating worker pools, composing package catalogs, and ensuring fail-safe
    teardown if any critical component faults.

Purpose:
    FEAT-HOST-BOOT: Host Lifecycle Orchestration and Boot Engine.
    Provides deterministic 5-phase startup coordination, runtime dependency
    injection, fault-tolerant provider hook supervision, client handshake
    validation, and graceful reverse-order teardown for all host-owned services.

Key Capabilities:
    - FR-HOST-BOOT-STAGE-PROGRESSION: Deterministic 5-Stage Monotonic Boot
      Progression
      Associated: `Startup.mark()`, `Startup.step()`
      Logging: Emits debug log on stage start and info log on terminal outcome
      (`succeeded`, `failed`, `cancelled`) with elapsed milliseconds to the
      logger and publishes a `boot.progress` event on the `EventBus`.
    - FR-HOST-BOOT-LIFECYCLE-HOOKS: Injected Provider Hook Supervision and
      Periodic Execution
      Associated: `Startup.providers()`, `Startup._periodic()`
      Logging: Emits info log when each hook starts/completes, logs warning on hook
      failure or periodic failure, and marks stage failure or DEGRADED status.
    - FR-HOST-BOOT-SOCKET-READINESS: Server Socket Readiness and Wire Snapshot
      Generation
      Associated: `Startup.listening()`, `Startup.snapshot()`,
      `Startup.log_summary()`
      Logging: Emits info log on host milestone reach with state and total elapsed
      milliseconds, and logs debug wire snapshot payload.
    - FR-HOST-BOOT-CLIENT-HANDSHAKE: Client Session Readiness and Handshake
      Tracking
      Associated: `Startup.connected()`, `Startup.acknowledge()`
      Logging: Emits info log when client connects its update channel and info log
      when client successfully acknowledges initialization within the 30-second
      window.
    - FR-HOST-BOOT-SERVICE-COMPOSITION: Host Service Composition and Dependency
      Initialization
      Associated: `BootstrapCoordinator.initialize()`,
      `BootstrapCoordinator._services()`, `BootstrapCoordinator._packages()`,
      `BootstrapCoordinator._database()`
      Logging: Emits info log when initialization completes, logs error on
      SQLite schema verification failure, and logs warning/error on abortive
      teardown.
    - FR-HOST-BOOT-INVENTORY-TELEMETRY: Post-Boot Inventory Telemetry Reporting
      Associated: `BootstrapCoordinator.log_boot_summary()`
      Logging: Emits info log detailing total discovered presets, catalog
      descriptors, and catalog issues after network socket bind.
    - FR-HOST-BOOT-RESOURCE-TEARDOWN: Graceful Reverse-Order Teardown and
      Resource Disposal
      Associated: `BootstrapCoordinator.close()`, `Startup.close()`
      Logging: Emits info logs as compute pools and lifecycle providers are
      released, logs error if provider cleanup fails, and emits final host
      shutdown completed log.

Python API Usage:
    ```python
    from pathlib import Path
    from app.host.bootstrap import BootstrapCoordinator
    from app.host.settings import HostSettings

    # 1. Instantiate coordinator with immutable configuration
    settings = HostSettings(
        host="127.0.0.1",
        port=8000,
        data_dir=Path("./data"),
        database_path=Path("./data/haruquant.db"),
    )
    coordinator = BootstrapCoordinator(settings)

    # 2. Asynchronously initialize services, persistence, and packages
    await coordinator.initialize()

    # 3. Retrieve initialized subsystem authorities
    session_mgr = coordinator.session_manager()
    coordinator.log_boot_summary()

    # 4. Gracefully dispose resources during application shutdown
    await coordinator.close()
    ```

CLI Usage:
    The bootstrap process is launched externally via the command line through
    the application entrypoint:
    ```bash
    # Standard server launch
    uv run python -m app.main --host 127.0.0.1 --port 8000 --data-dir ./data

    # Headless server with specific worker pool configuration
    uv run python -m app.main --no-browser --workers 4

    # Run persistence schema migration prior to boot
    uv run python -m app.main --migrate-auth-schema --data-dir ./data
    ```
"""

from __future__ import annotations

import asyncio
import re
import time
from collections.abc import Awaitable, Callable
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

from app.host.contracts import BootSnapshot, LifecycleHook, Outcome, StageResult, State
from app.host.discovery import scan_presets
from app.host.events import EventBus
from app.host.jobs import JobManager, create_pool, diagnostics
from app.host.logging import close_host_logging, configure_host_logging, get_logger
from app.host.packages import (
    Composition,
    InstallationLease,
    PackageInventory,
    scan_packages,
)
from app.host.sessions import SessionManager
from app.host.settings import HostSettings, SettingsStore
from app.host.transport import ExchangeFiles
from app.persistence.host import HostPersistenceSchemaError, prepare_boot_database
from app.persistence.resources import ResourceStore

logger = get_logger(__name__)

MAX_CLIENTS = 256
READINESS_SECONDS = 30

STAGES: tuple[tuple[str, str], ...] = (
    ("runtime", "Configure runtime"),
    ("services", "Initialize host services"),
    ("packages", "Discover and compose packages"),
    ("transport", "Prepare transport"),
    ("serving", "Start serving"),
)
PROVIDER_STAGES = frozenset(("services", "packages"))


class Startup:
    """Maintain host progress independently of any one client's authentication.

    results contains the latest StageResult for every stage. clients holds bounded
    session readiness state, while hooks are explicit trusted implementations.
    No provider is discovered or imported by this class. Callers supply validated
    stage IDs and serialize lifecycle operations on the host loop.
    """

    def __init__(
        self,
        events: EventBus,
        hooks: tuple[LifecycleHook, ...] = (),
        *,
        runtime_started_at: float | None = None,
    ) -> None:
        """Validate hooks and create pending stage records without running work.

        Args:
            runtime_started_at: Monotonic entrypoint start, or this construction time.
            events: Event bus owned by the same host/event loop.
            hooks: Unique named hooks for allowed provider stages; empty means
                normal.

        Raises:
            ValueError: Hook IDs, stage slots, timeout, or repeat intervals are invalid.
        """
        ids = [hook.id for hook in hooks]
        if len(ids) != len(set(ids)) or any(
            not re.fullmatch(r"[a-z][a-z0-9_.-]{0,99}", h.id)
            or h.stage not in PROVIDER_STAGES
            or h.timeout <= 0
            or (h.interval is not None and h.interval < 1)
            for h in hooks
        ):
            raise ValueError("Invalid lifecycle hooks")
        self.started_at = (
            time.monotonic() if runtime_started_at is None else runtime_started_at
        )
        self.events = events
        self.hooks = hooks
        self.state: State = "OFFLINE"
        self.results = {
            key: StageResult(stage=key, label=label) for key, label in STAGES
        }
        self._began: dict[str, float] = {"runtime": self.started_at}
        self._opened: list[LifecycleHook] = []
        self._tasks: set[asyncio.Task[None]] = set()
        self.clients: dict[str, tuple[float, bool]] = {}

    def mark(
        self, stage: str, outcome: Outcome = "succeeded", reason: str = ""
    ) -> None:
        """Replace one stage result, log it, and publish a progress event.

        Only actual transitions are emitted. Running starts the
        monotonic timer; elapsed_ms records milliseconds since that start. This method
        is a transition operation, not a read-only reporting call.

        Args:
            stage: Known STAGES identifier.
            outcome: New outcome; defaults to succeeded.
            reason: Safe machine-readable explanation without secrets.

        Raises:
            KeyError: stage is not registered.
        """
        now = time.monotonic()
        if outcome == "running":
            self._began[stage] = now
        result = self.results[stage].model_copy(
            update={
                "outcome": outcome,
                "reason": reason,
                "elapsed_ms": round((now - self._began.get(stage, now)) * 1000, 3),
            }
        )
        self.results[stage] = result
        log = logger.debug if outcome == "running" else logger.info
        log(
            "%s %s: %s",
            stage,
            result.label,
            outcome,
            extra={
                "fields": {
                    "stage": stage,
                    "outcome": outcome,
                    "reason": reason,
                    "elapsed_ms": result.elapsed_ms,
                }
            },
        )
        self.events.publish("boot.progress", result.model_dump())

    def log_summary(self, milestone: str) -> None:
        """Report one concise summary without mutating progress."""
        logger.info(
            "Host %s: state=%s; elapsed_ms=%.3f",
            milestone,
            self.state,
            (time.monotonic() - self.started_at) * 1000,
        )
        logger.info("Boot snapshot: %s", self.snapshot().model_dump())

    def listening(self) -> None:
        """Publish readiness after the server confirms its listening socket."""
        self.state = (
            "DEGRADED"
            if any(r.outcome == "failed" for r in self.results.values())
            else "SERVER_READY"
        )
        self.mark("serving", reason="listening")

    def snapshot(self) -> BootSnapshot:
        """Build an immutable wire snapshot of current lifecycle state.

        Returns:
            BootSnapshot containing process state, current event sequence, and all stage
            results.
        """
        return BootSnapshot(
            schema_version=2,
            state=self.state,
            sequence=self.events.sequence,
            stages=tuple(self.results.values()),
        )

    async def step(self, stage: str, action: Callable[[], Awaitable[Any]]) -> Any:
        """Await one operation with observable start and terminal outcomes.

        Cancellation marks cancelled and propagates. Other exceptions mark failed, set
        process state FAILED, and propagate. Resource cleanup belongs to the enclosing
        coordinator, not this helper.

        Args:
            stage: Known stage whose timing and outcome will be recorded.
            action: Async callable invoked exactly once by this call.

        Returns:
            The action result, unchanged.
        """
        self.mark(stage, "running")
        try:
            result = await action()
        except asyncio.CancelledError:
            self.mark(stage, "cancelled", "cancelled")
            raise
        except Exception:
            if self.results[stage].outcome != "failed":
                self.mark(stage, "failed", "operation_failed")
            self.state = "FAILED"
            raise
        if self.results[stage].outcome == "running":
            self.mark(stage)
        return result

    async def providers(self, stage: str) -> None:
        """Execute matching hooks sequentially within their individual time budgets.

        Optional failures mark the stage failed but allow remaining hooks to run.
        Successful interval hooks get supervised repeat tasks. Hooks are tracked before
        execution so partial acquisition can be cleaned up. Cancellation propagates.
        The coordinator invokes each slot once during initialization.

        Args:
            stage: Host phase whose injected hooks should run.

        Raises:
            RuntimeError: A required provider fails or times out; its raw error text is
                suppressed.
        """
        selected = [hook for hook in self.hooks if hook.stage == stage]
        failed = False
        for hook in selected:
            self._opened.append(hook)
            logger.info("%s Provider %s starting", stage, hook.id)
            try:
                async with asyncio.timeout(hook.timeout):
                    await hook.run()
            except asyncio.CancelledError:
                self.mark(stage, "cancelled", "cancelled")
                raise
            except Exception:  # noqa: BLE001 -- isolate failures at the provider boundary.
                failed = True
                logger.warning("%s Provider %s failed", stage, hook.id)
                if hook.required:
                    self.mark(stage, "failed", "required_provider_failed")
                    self.state = "FAILED"
                    raise RuntimeError(
                        "Required provider initialization failed"
                    ) from None
            else:
                logger.info("%s Provider %s completed", stage, hook.id)
                if hook.interval is not None:
                    task = asyncio.create_task(self._periodic(hook))
                    self._tasks.add(task)
                    task.add_done_callback(self._tasks.discard)
        if failed:
            self.mark(stage, "failed", "optional_provider_failed")

    async def _periodic(self, hook: LifecycleHook) -> None:
        """Repeat a successful hook until cancellation or its first failure.

        Waits before each invocation. A repeat failure logs safely, marks its stage
        failed, and sets process state DEGRADED. Cancellation is propagated to shutdown.

        Args:
            hook: Injected provider with a repeat interval and per-call timeout in
                seconds.
        """
        while True:
            await asyncio.sleep(hook.interval or 1)
            try:
                async with asyncio.timeout(hook.timeout):
                    await hook.run()
            except asyncio.CancelledError:
                raise
            except Exception:  # noqa: BLE001 -- optional task failure is observable, never silent.
                if self.state in ("SERVER_READY", "DEGRADED"):
                    self.state = "DEGRADED"
                logger.warning("%s Periodic provider %s failed", hook.stage, hook.id)
                self.mark(hook.stage, "failed", "periodic_provider_failed")
                return

    def connected(self, key: str) -> None:
        """Track an authenticated session and mark its update channel connected.

        Starts a readiness deadline for new clients; an expired unready entry can
        reconnect. Does not change process readiness.

        Args:
            key: Internal session key, not the plaintext bearer credential.

        Raises:
            ValueError: The bounded client collection is full after stale entries are
                pruned.
        """
        if (
            key in self.clients
            and not self.clients[key][1]
            and time.monotonic() - self.clients[key][0] > READINESS_SECONDS
        ):
            del self.clients[key]
        if key not in self.clients:
            if len(self.clients) >= MAX_CLIENTS:
                stale = [
                    k
                    for k, (started, _) in self.clients.items()
                    if time.monotonic() - started > READINESS_SECONDS
                ]
                for old in stale:
                    del self.clients[old]
                if len(self.clients) >= MAX_CLIENTS:
                    raise ValueError("Client capacity exceeded")
            self.clients[key] = (time.monotonic(), False)
            logger.info("Client update channel connected")

    def acknowledge(self, key: str) -> None:
        """Record client initialization without changing process readiness."""
        if key not in self.clients:
            raise ValueError("Client must connect before acknowledgment")
        started, ready = self.clients[key]
        if ready:
            return
        if time.monotonic() - started > READINESS_SECONDS:
            raise ValueError("Client readiness deadline expired; reconnect")
        self.clients[key] = (started, True)
        logger.info("Client initialized after %.3f seconds", time.monotonic() - started)

    async def close(self) -> None:
        """Cancel supervised work and close acquired providers in reverse order.

        Awaits cancelled tasks, invokes bounded close callbacks, and logs cleanup
        failures while continuing to other providers. Clears acquired hooks and sets
        STOPPED. Does not close the shared event loop or persistence store.
        """
        tasks = list(self._tasks)
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        for hook in reversed(self._opened):
            if hook.close is not None:
                try:
                    async with asyncio.timeout(hook.timeout):
                        await hook.close()
                    logger.info("Provider %s released", hook.id)
                except Exception:  # noqa: BLE001 -- continue releasing independent resources.
                    logger.error("Provider cleanup failed")  # noqa: TRY400 -- provider exception text may contain secrets.
        self._opened.clear()
        self.state = "STOPPED"
        logger.info("Host shutdown completed")


class BootstrapCoordinator:
    """Own one host instance and its startup/shutdown resources.

    Dependencies are retained on the instance rather than retrieved from globals.
    The coordinator is intended for one event-loop lifecycle; initialize is not a
    concurrent initialization barrier. Closing releases tasks, pool, and host logging.
    """

    def __init__(
        self,
        settings: HostSettings,
        hooks: tuple[LifecycleHook, ...] = (),
        *,
        installation_root: Path | None = None,
        runtime_started_at: float | None = None,
    ) -> None:
        """Compose unstarted services without creating files or database rows.

        Args:
            runtime_started_at: Monotonic entrypoint start, when supplied.
            settings: Immutable runtime configuration shared with owned services.
            hooks: Trusted, preconstructed lifecycle providers with explicit
                dependencies.
            installation_root: Explicit code installation boundary; defaults to the
                installation containing this host. Tests supply isolated directories.

        Raises:
            ValueError: Startup rejects duplicate or invalid hook declarations.
        """
        self.config = settings
        self.events = EventBus()
        self.startup = Startup(
            self.events, hooks, runtime_started_at=runtime_started_at
        )
        self.settings = SettingsStore(settings.database_path)
        self.sessions: SessionManager | None = None
        self.pool: ProcessPoolExecutor | None = None
        self.exchange = ExchangeFiles(settings.data_dir / "exchange")
        self.catalog: dict[str, Any] = {"domains": [], "issues": []}
        self.presets: dict[str, Any] = {"entries": [], "issues": []}
        self.resources: dict[str, Any] = {}
        self.shutdown_event = asyncio.Event()
        self.initialized = False
        self.installation_root = (
            installation_root
            or settings.installation_root
            or Path(__file__).resolve().parents[2]
        )
        self.installation_lease = InstallationLease(self.installation_root)
        self.package_inventory = PackageInventory(
            packages=(), issues=(), fingerprint=""
        )
        self.resource_store = ResourceStore(settings.data_dir / "resources")
        self.jobs: JobManager | None = None
        self.composition: Composition | None = None

    async def initialize(self) -> None:
        """Initialize core host services and inspect optional contributions.

        Configures logging and directories, verifies or creates storage, initializes
        sessions, scans presets/catalog, and allocates the pool. A completed second call
        is a no-op. On any failure, including cancellation, cleanup runs and state
        becomes
        FAILED before the exception propagates. Existing incompatible stores are never
        automatically migrated.
        """
        if self.initialized:
            return
        self.startup.state = "INITIALIZING"
        try:
            self.installation_lease.acquire()
            configure_host_logging(self.config.log_dir)
            self.startup.mark("runtime")
            await self.startup.step("services", self._services)
            await self.startup.step("packages", self._packages)
            self.initialized = True
            logger.info(
                "Host initialization completed; provider availability is explicit"
            )
        except BaseException:
            await self.close()
            self.startup.state = "FAILED"
            raise

    async def _services(self) -> None:
        """Prepare shared host services before package activation."""
        for name in ("presets", "plugins", "exchange"):
            (self.config.data_dir / name).mkdir(parents=True, exist_ok=True)
        await self._database()
        self.presets = scan_presets(self.config.data_dir / "presets")
        self.resources = diagnostics()
        self.jobs = JobManager(
            self.config.workers
            or min(61, max(1, int(self.resources["cpu_count"]) - 1)),
            max(1, int(self.resources["memory_available_bytes"]) // 2),
        )
        self.composition = Composition(
            self.installation_root,
            self.resource_store,
            self.jobs,
            settings=self.settings,
            source_credentials=self.config.source_credentials,
        )
        self.pool = create_pool(self.config.workers)
        await self.startup.providers("services")

    async def _packages(self) -> None:
        """Prepare accepted packages and publish their actual availability."""
        self.package_inventory = scan_packages(self.installation_root)
        if self.composition is None:
            raise RuntimeError("Host services are not initialized")
        await self.composition.start(self.package_inventory)
        self.catalog = self.composition.catalog()
        await self.startup.providers("packages")

    async def _database(self) -> None:
        """Prepare schema and session authority for host services.

        Schema work and session construction run in worker threads. The public settings
        snapshot is validated before assigning session authority. Other storage errors
        propagate to initialize for cleanup.

        Raises:
            HostPersistenceSchemaError: Existing storage is incompatible; an actionable
                diagnostic is logged.
            SessionError: Stored operator authority conflicts with runtime settings.
        """
        try:
            await asyncio.to_thread(prepare_boot_database, self.config.database_path)
        except HostPersistenceSchemaError:
            logger.error(  # noqa: TRY400 -- schema diagnostics must not expose values.
                "Schema verification failed. For absent auth tables, stop other "
                "hosts and run: uv run python -m app.main --migrate-auth-schema "
                "(use the same --data-dir). Conflicting schemas require review."
            )
            raise
        self.settings.snapshot()
        self.sessions = await asyncio.to_thread(SessionManager, self.config)

    def log_boot_summary(self) -> None:
        """Log concise readiness and actual inventory totals after server binding.

        Reads existing results and inventories only. Does not scan files again,
        publish progress, or run providers. The server calls this immediately after
        listening readiness, before optional browser launch.
        """
        self.startup.log_summary("ready")
        logger.info(
            "Boot scan totals: presets=%d; catalog descriptors=%d; catalog issues=%d",
            len(self.presets["entries"]),
            len(self.catalog["domains"]),
            len(self.catalog["issues"]),
        )

    def session_manager(self) -> SessionManager:
        """Return the initialized authentication authority.

        Returns:
            The coordinator-owned SessionManager.

        Raises:
            RuntimeError: Initialization has not assigned a session manager.
        """
        if self.sessions is None:
            raise RuntimeError("Host is not initialized")
        return self.sessions

    async def close(self) -> None:
        """Release lifecycle resources in dependency order.

        Cancels and awaits supervised startup tasks, closes providers, requests pool
        shutdown without waiting for running jobs, and releases owned logging handlers.
        Cancels queued pool futures; does not remove files or alter persisted sessions.
        """
        if not self.initialized and not self.installation_lease.held:
            return
        self.initialized = False
        await self.startup.close()
        if self.composition is not None:
            await self.composition.close()
            self.composition = None
        if self.jobs is not None:
            await self.jobs.close()
            self.jobs = None
        if self.pool is not None:
            self.pool.shutdown(wait=False, cancel_futures=True)
            self.pool = None
            logger.info("Compute pool released")
        close_host_logging()
        self.installation_lease.release()
