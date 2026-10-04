"""Command-line interface entry point for HaruQuantAI diagnostic operations.

Description:
    Provides the command-line interface entrypoint for operator diagnostics,
    initial sanity checks, logging severity demonstrations, and host configuration
    settings inspection. Resolves a dedicated namespace logger via
    `get_logger(__name__)`, queries persisted configuration settings via the
    `settings` singleton, and ensures all emitted records across all log
    severities are flushed cleanly to disk and console before process exit.

Purpose:
    FEAT-APP-CLI: Command-line interface and diagnostic test dispatch.

Key Capabilities:
    - FR-APP-CLI-DISPATCH: Emit multi-severity diagnostic records and flush telemetry.
      Associated: `main()`
      Logging: Emits records at DEBUG, INFO, WARNING, ERROR, and CRITICAL severities.
    - FR-APP-CLI-SETTINGS: Query and display host database settings via telemetry.
      Associated: `show_settings()`, `main()`
      Logging: Emits INFO events for each loaded setting key and value.

Python API Usage:
    ```python
    from app.cli import main, show_settings

    # Display settings directly
    records = show_settings(limit=5)

    # Execute full diagnostic routine
    main()
    ```

CLI Usage:
    Execute the CLI entrypoint directly:
    ```bash
    uv run python -m app.cli
    ```
"""

from __future__ import annotations

from typing import Any

from app.host.logging import flush, get_logger
from app.host.settings import settings

__all__ = ["main", "show_settings"]

logger = get_logger(__name__)


def show_settings(limit: int = 5) -> dict[str, Any]:
    """Query and display scoped settings records via the settings singleton.

    Args:
        limit: Maximum number of settings to query and display.

    Returns:
        Dictionary of loaded settings.
    """
    items = settings.items()
    if not items:
        logger.info(
            "No settings loaded from host database",
            extra={"requirement": "FR-APP-CLI-SETTINGS"},
        )
        return {}

    displayed: dict[str, Any] = {}
    for key, val in items[:limit]:
        raw_val = val.as_dict() if hasattr(val, "as_dict") else val
        displayed[key] = raw_val
        logger.info(
            "Loaded setting %s = %s",
            key,
            raw_val,
            extra={"key": key, "requirement": "FR-APP-CLI-SETTINGS"},
        )

    return displayed


def main() -> None:
    """Execute the diagnostic CLI routine and flush pending telemetry events."""
    logger.debug("This is a debug")
    logger.info("This is a info")
    logger.warning("This is a warning")
    logger.error("This is a error")
    logger.critical("This is a critical")

    show_settings()

    flush(timeout=5.0)


if __name__ == "__main__":
    main()
