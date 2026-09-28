"""Assemble and initialize the host's explicitly owned services.

BootstrapCoordinator connects configuration, persistence, sessions, event delivery,
metadata inventories, and the compute pool. Construction allocates in-memory
state; initialize performs filesystem/database work and invokes injected hooks.
The HTTP lifespan owns initialize/close. Missing research providers are reported
as unavailable and are never inferred from metadata discovery.
"""

import asyncio
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

from app.host.commands import ExchangeFiles
from app.host.composition import Composition
from app.host.config import HostSettings
from app.host.contracts import LifecycleHook
from app.host.customizations import scan_presets
from app.host.events import EventBus
from app.host.jobs import JobManager
from app.host.logging import close_host_logging, configure_host_logging, get_logger
from app.host.packages import PackageInventory, scan_packages
from app.host.removal import InstallationLease
from app.host.resource_store import ResourceStore
from app.host.resources import create_pool, diagnostics
from app.host.sessions import SessionManager
from app.host.settings import SettingsStore
from app.host.startup import Startup
from app.persistence.host import HostPersistenceSchemaError, prepare_boot_database

logger = get_logger(__name__)


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
    ) -> None:
        """Compose unstarted services without creating files or database rows.

        Args:
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
        self.startup = Startup(self.events, hooks)
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
            # Buffering is represented by finite early milestones, flushed here.
            for stage in ("B01", "B02", "B03", "B04"):
                self.startup.mark(stage, "running")
                self.startup.mark(stage)
            for name in ("presets", "plugins", "exchange"):
                (self.config.data_dir / name).mkdir(parents=True, exist_ok=True)
            await self.startup.step("I01", self._database)
            self.startup.mark("I02", "running")
            self.presets = scan_presets(self.config.data_dir / "presets")
            self.startup.mark("I02")
            await self.startup.providers("I03")
            self.startup.mark("B09", "running")
            self.resources = diagnostics()
            self.jobs = JobManager(
                self.config.workers
                or min(61, max(1, int(self.resources["cpu_count"]) - 1)),
                max(1, int(self.resources["memory_available_bytes"]) // 2),
            )
            self.composition = Composition(
                self.installation_root, self.resource_store, self.jobs
            )
            self.startup.mark("B09")
            self.startup.mark("I04", "running")
            self.pool = create_pool(self.config.workers)
            self.startup.mark("I04")
            # I05 activation requires the I06 discovery snapshot.
            self.startup.mark("I05", "running", "awaiting_discovery")
            self.startup.mark("I06", "running")
            self.package_inventory = scan_packages(self.installation_root)
            await self.composition.start(self.package_inventory)
            self.catalog = self.composition.catalog()
            self.startup.mark("I06")
            for stage in ("I05", "I07", "I08", "I09", "I10"):
                await self.startup.providers(stage)
            self.startup.mark("I11", "running")
            self.startup.mark("I11", reason="event_hub_ready")
            await self.startup.providers("I12")
            self.initialized = True
            logger.info(
                "Host initialization completed; provider availability is explicit"
            )
        except BaseException:
            await self.close()
            self.startup.state = "FAILED"
            raise

    async def _database(self) -> None:
        """Prepare schema and session authority for the I01 stage.

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
                "I01 Schema verification failed. For absent auth tables, stop other "
                "hosts and run: uv run python -m app.main --migrate-auth-schema "
                "(use the same --data-dir). Conflicting schemas require review."
            )
            raise
        self.settings.snapshot()
        self.sessions = await asyncio.to_thread(SessionManager, self.config)

    def log_boot_summary(self) -> None:
        """Log all stage outcomes and measured scan totals after server binding.

        Reads existing results and inventories only. Does not scan files again, publish
        progress, or run providers. The server entrypoint calls this after browser
        launch
        has been attempted or explicitly disabled.
        """
        self.startup.log_summary("server_ready", open_browser=self.config.open_browser)
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
        await self.startup.close()
        if self.composition is not None:
            await self.composition.close()
        if self.jobs is not None:
            await self.jobs.close()
        if self.pool is not None:
            self.pool.shutdown(wait=False, cancel_futures=True)
            self.pool = None
            logger.info("Compute pool released")
        close_host_logging()
        self.installation_lease.release()
