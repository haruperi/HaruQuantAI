"""Command-line interface entry point for HaruQuantAI diagnostic operations.

Description:
    Provides the command-line interface entrypoint for operator diagnostics,
    initial sanity checks, and logging severity demonstrations. Resolves a
    dedicated namespace logger via `get_logger(__name__)` and ensures that all
    emitted diagnostic events across all five log levels are flushed to disk
    and console before process exit.

Purpose:
    FEAT-APP-CLI: Command-line interface and diagnostic test dispatch.

Key Capabilities:
    - FR-APP-CLI-DISPATCH: Emit multi-severity diagnostic records and flush telemetry.
      Associated: `main()`
      Logging: Emits records at DEBUG, INFO, WARNING, ERROR, and CRITICAL severities.

Python API Usage:
    ```python
    from app.cli import main

    main()
    ```

CLI Usage:
    Execute the CLI entrypoint directly:
    ```bash
    uv run python -m app.cli
    ```
"""

from __future__ import annotations

from app.host.logging import flush, get_logger

__all__ = ["main"]

logger = get_logger(__name__)


def main() -> None:
    """Execute the diagnostic CLI routine and flush pending telemetry events."""
    logger.debug("This is a debug")
    logger.info("This is a info")
    logger.warning("This is a warning")
    logger.error("This is a error")
    logger.critical("This is a critical")
    flush(timeout=5.0)


if __name__ == "__main__":
    main()
