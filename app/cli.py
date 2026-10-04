"""Command-line interface entry point for HaruQuantAI operations.

Description:
    Serves as the main process bootstrap and lifecycle coordinator for the
    HaruQuantAI platform when using CLI. Initializes or arms host telemetry,
    emits application lifecycle events, executes initial runtime sanity checks,
    and guarantees orderly shutdown with complete queue draining in a finally boundary.

Purpose:
    FEAT-APP-CLI: CLI application lifecycle entry point and process coordinator.

Key Capabilities:
    - FR-APP-CLI-BOOTSTRAP: Coordinate host telemetry and start application runtime.
      Associated: `main()`
      Logging: Emits INFO event upon process initialization.
    - FR-APP-CLI-SESSION: Initialize host session authority and record operator session.
      Associated: `main()`
      Logging: Emits INFO event upon session initialization and operator recording.
    - FR-APP-CLI-JOBS: Initialize hardware diagnostics and job admission manager.
      Associated: `main()`
      Logging: Emits INFO event upon jobs system initialization.
    - FR-APP-CLI-LIFECYCLE: Coordinate graceful process shutdown and telemetry sync.
      Associated: `main()`
      Logging: Emits INFO event before exit and drains queued telemetry via shutdown.

Python API Usage:
    Not applicable

CLI Usage:
    Launch the main application entry point:
    ```bash
    uv run python -m app.cli
    ```
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.host.jobs import JobManager, create_pool, diagnostics
from app.host.logging import (
    TelemetryEngine,
    configure_host_logging,
    get_logger,
    shutdown,
)
from app.host.session import SessionAuthority
from app.host.settings import settings

if TYPE_CHECKING:
    from app.host.logging import LoggingConfig

logger = get_logger(__name__)


def main(config: LoggingConfig | None = None) -> None:
    """Bootstrap application runtime, execute tasks, and coordinate clean shutdown.

    Args:
        config: Optional telemetry configuration override. If None, default host
            logging configuration is utilized.
    """
    logger.info("HaruQuantAI Application is booting up using CLI...")

    logger.info("Configuring Runtime Environment...")
    logger.info("Resolving Settings...")
    if settings:
        logger.info("Settings loaded...")
    else:
        logger.error("Failed to load settings...")
        return

    logger.info("Configuring Logging...")
    is_root_caller = not TelemetryEngine.is_configured()

    if config is not None:
        configure_host_logging(
            log_dir=config.log_dir,
            level=config.level,
            max_bytes=config.max_bytes,
            retention_days=config.retention_days,
            include_console=config.include_console,
            use_color=config.use_color,
        )
    elif is_root_caller:
        target_level = (
            "DEBUG" if settings.config_troubleshooting.debug_level_active else "INFO"
        )
        configure_host_logging(level=target_level)

    if not settings.validate_workspace_paths():
        return

    logger.info("Security checks...")
    if bool(settings.user_access.get("locked", False)):
        logger.error("Application is locked. Please contact support.")
        return

    logger.info("Initializing Sessions...")
    logger.info("Logging in user: %s ...", settings.user_access.username)
    session_authority = SessionAuthority(db_path=settings.db_path)
    session_authority.initialize()
    timeout_mins = int(settings.user_access.get("session_timeout_mins", 1440))
    username = str(settings.user_access.get("username", "haruquantai"))
    session_authority.create_session(
        username=username,
        peer_id="cli-local",
        ttl_seconds=timeout_mins * 60,
    )

    logger.info("Jobs System setting up...")
    diag = diagnostics()

    logger.info("Gathering system resources...")
    logger.info("Number of Cores: %s", diag.cpu_count_logical)
    logger.info("Memory: %s GB", diag.total_ram_gb)
    logger.info(
        "Number of Cores to be used: %s Active",
        settings.config_cpu.custom_cores,
    )
    logger.info("Memory: %s GB", settings.config_memory.memory_limit_gb)

    max_cores = int(settings.config_cpu.get("custom_cores", diag.cpu_count_logical))
    max_ram_gb = float(settings.config_memory.get("memory_limit_gb", 8.0))
    max_ram_bytes = int(max_ram_gb * (1024**3))
    job_pool = create_pool(max_workers=max_cores)
    job_manager = JobManager(
        pool=job_pool,
        max_workers=max_cores,
        max_memory_bytes=max_ram_bytes,
    )

    try:
        logger.info("Application started successfully")

    finally:
        job_manager.close(timeout=5.0)
        logger.info("Application shutdown... Routine finished")
        if is_root_caller or config is not None:
            shutdown(timeout=5.0)


if __name__ == "__main__":
    main()
