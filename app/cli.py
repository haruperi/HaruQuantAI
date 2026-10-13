"""Command-Line Interface (CLI) runner package for HaruQuantAI.

Description:
    Provides the central headless command-line interface for HaruQuantAI,
    entrypoint via cli when run with python -m app.cli.
    Enables full verification, data ingestion, instrument
    configuration, and diagnostic inspection directly from the terminal without
    requiring a browser, UI shell, or ASGI HTTP server.

Purpose:
    FEAT-HOST-CLI-RUNNER: Universal headless host CLI runner and dispatcher.

Key Capabilities:
    - FR-HOST-CLI-BOOTSTRAP: Initialize and coordinate headless HostRuntime
      contexts without ASGI web server overhead.
      Logging: Emits INFO on CLI invocation and graceful teardown.
    - FR-HOST-CLI-DISPATCHER: Parse command-line subcommands and route requests
      directly to workspace managers and host services.

CLI Usage:
    ```bash
    python -m app.cli --help
    python -m app.cli host diagnostics
    python -m app.cli data symbols list
    ```
"""

from __future__ import annotations

from app.host.logging import get_logger
from app.host.settings import settings

logger = get_logger(__name__)


def main() -> None:
    """Execute central command-line interface."""
    logger.info("FR-HOST-CLI-BOOTSTRAP: initializing CLI runner")
    _ = settings


if __name__ == "__main__":
    main()
