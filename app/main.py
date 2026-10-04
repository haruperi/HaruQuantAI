"""Primary application entry point and runtime lifecycle coordinator for HaruQuantAI.

Description:
    Serves as the main process bootstrap and lifecycle coordinator for the
    HaruQuantAI platform. Initializes or arms host telemetry, emits application
    lifecycle events, executes initial runtime sanity checks, and guarantees
    orderly shutdown with complete queue draining in a finally boundary.

Purpose:
    FEAT-APP-MAIN: Main application lifecycle entry point and process coordinator.

Key Capabilities:
    - FR-APP-MAIN-BOOTSTRAP: Coordinate host telemetry and start application runtime.
      Associated: `main()`
      Logging: Emits INFO event upon process initialization.
    - FR-APP-MAIN-LIFECYCLE: Coordinate graceful process shutdown and telemetry sync.
      Associated: `main()`
      Logging: Emits INFO event before exit and drains queued telemetry via shutdown.

Python API Usage:
    ```python
    from app.main import main

    main()
    ```

CLI Usage:
    Launch the main application entry point:
    ```bash
    uv run python -m app.main
    ```
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.cli import main as cli_main
from app.host.logging import configure_host_logging, get_logger, shutdown

if TYPE_CHECKING:
    from app.host.logging import LoggingConfig

__all__ = ["main"]

logger = get_logger(__name__)


def main(config: LoggingConfig | None = None) -> None:
    """Bootstrap application runtime, execute tasks, and coordinate clean shutdown.

    Args:
        config: Optional telemetry configuration override. If None, default host
            logging configuration is utilized.
    """
    if config is not None:
        configure_host_logging(
            log_dir=config.log_dir,
            level=config.level,
            max_bytes=config.max_bytes,
            retention_days=config.retention_days,
            include_console=config.include_console,
            use_color=config.use_color,
        )

    try:
        logger.info("Starting HaruQuantAI application...")
        cli_main()
        logger.info("HaruQuantAI application shutdown routine finished")
    finally:
        shutdown(timeout=5.0)


if __name__ == "__main__":
    main()
