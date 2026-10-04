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

import os
from pathlib import Path
from typing import TYPE_CHECKING

import psutil

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

    logger.info("Validating paths...")
    paths_to_validate = {
        "Configs": Path(settings.workspace_paths.configs_dir),
        "Data": Path(settings.workspace_paths.data_dir),
        "Projects": Path(settings.workspace_paths.projects_dir),
        "Strategies": Path(settings.workspace_paths.strategies_dir),
    }

    for name, path in paths_to_validate.items():
        if path.exists():
            logger.info("%s directory exists...", name)
        else:
            logger.error("%s directory does not exist...", name)
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

    logger.info("Gathering system resources...")
    logger.info("Number of Cores: %s", os.cpu_count())
    logger.info("Memory: %s GB", psutil.virtual_memory().total / (1024**3))
    logger.info(
        "Number of Cores to be used: %s Active",
        settings.config_cpu.custom_cores,
    )
    logger.info("Memory: %s GB", settings.config_memory.memory_limit_gb)

    try:
        logger.info("Application started successfully")

    finally:
        logger.info("Application shutdown... Routine finished")
        if is_root_caller or config is not None:
            shutdown(timeout=5.0)


if __name__ == "__main__":
    main()
