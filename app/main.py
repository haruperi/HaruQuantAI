"""Primary application entry point and runtime lifecycle coordinator for HaruQuantAI.

Description:
    Serves as the main process bootstrap and lifecycle coordinator for the
    HaruQuantAI clean-room Python host (replacing legacy JVM mechanics).
    Resolves host, port, and debug configuration from the authoritative database
    settings with CLI overrides, initializes host telemetry, launches the ASGI
    web server with factory composition, and triggers the structured LifespanStage
    state machine:
        1. CONFIGURING: Validates runtime settings and configuration profiles.
        2. PATHS: Ensures directory containment hierarchy for data and resources.
        3. LOGGING: Verifies centralized telemetry and ring buffer readiness.
        4. DISCOVERY: Initializes extension slot registry and plugin context.
        5. SERVICES: Initializes SQLite schemas, runs startup recovery audit,
           reconciles active compute jobs, and verifies resource custody.
        6. ROUTES: Confirms capability routers, transport middleware and contracts.
        7. READY: Asserts all checks passed and signals readiness to serve.

    Guarantees orderly shutdown with reverse-order stage rollback and complete
    queue draining in a finally boundary.

Purpose:
    FEAT-APP-MAIN: Main application lifecycle entry point and process coordinator.

Key Capabilities:
    - FR-APP-MAIN-BOOTSTRAP: Coordinate host telemetry, resolve configuration from
      database settings or CLI flags, and start application runtime.
      Associated: `main()`, `create_app()`
      Logging: Emits INFO event upon process initialization and configuration
        resolution.
    - FR-APP-MAIN-LIFECYCLE: Coordinate graceful process shutdown and telemetry sync.
      Associated: `main()`
      Logging: Emits INFO event before exit and drains queued telemetry via shutdown.

Python API Usage:
    ```python
    from app.main import create_app

    app = create_app()
    ```

CLI Usage:
    Launch the main application entry point:
    ```bash
    uv run python -m app.main
    uv run python -m app.main --host 127.0.0.1 --port 8000 --debug
    uv run python -m app.main --reload
    ```
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI

from app.host.bootstrap import HostRuntime, create_host_app
from app.host.logging import configure_host_logging, get_logger, shutdown
from app.host.settings import (
    HostSettings,
)
from app.host.settings import settings as default_host_settings

logger = get_logger(__name__)


def create_app(
    settings: HostSettings | None = None,
    runtime: HostRuntime | None = None,
    *,
    configuration: Any | None = None,
) -> FastAPI:
    """Factory function creating the composed host FastAPI application.

    Fires FR-APP-MAIN-BOOTSTRAP.

    Args:
        settings: Optional HostSettings override. If None, default settings are used.
        runtime: Optional HostRuntime instance. If None, a new runtime is created.
        configuration: Optional HostSettingsManager configuration override.

    Returns:
        Configured FastAPI application instance.
    """
    resolved_config = configuration or default_host_settings
    if settings is None:
        host_str = str(resolved_config.app_general.get("host", "127.0.0.1"))
        port_int = int(resolved_config.app_general.get("backend_port", 8000))
        debug_bool = bool(
            resolved_config.config_troubleshooting.get("debug_level_active", False)
        )
        resolved_settings = HostSettings(
            host=host_str,
            port=port_int,
            debug=debug_bool,
        )
    else:
        resolved_settings = settings

    return create_host_app(
        settings=resolved_settings,
        runtime=runtime,
        configuration=resolved_config,
    )


def _build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser for HaruQuantAI main application."""
    parser = argparse.ArgumentParser(
        prog="haruquantai",
        description="HaruQuantAI Platform Main Application",
    )
    parser.add_argument(
        "--host",
        type=str,
        default=None,
        help="Bind IP address (defaults to database app_general.host or 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Bind port number (defaults to database app_general.backend_port or 8000)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        default=None,
        help=(
            "Enable debug diagnostics "
            "(defaults to config_troubleshooting.debug_level_active)"
        ),
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        default=False,
        help="Enable automatic reload on code changes (development mode)",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="Optional path to runtime data directory",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    """Bootstrap application runtime, resolve settings, run server, and clean up.

    Args:
        argv: Optional command-line argument list. If None, sys.argv[1:] is parsed.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    # 1. Resolve host, port, and debug from database settings when not provided via CLI
    db_host = str(default_host_settings.app_general.get("host", "127.0.0.1"))
    db_port = int(default_host_settings.app_general.get("backend_port", 8000))
    db_debug = bool(
        default_host_settings.config_troubleshooting.get("debug_level_active", False)
    )

    host: str = args.host if args.host is not None else db_host
    port: int = args.port if args.port is not None else db_port
    debug: bool = args.debug if args.debug is not None else db_debug

    # 2. Configure logging and emit bootstrap event
    configure_host_logging(level="DEBUG" if debug else "INFO")
    logger.info(
        "FR-APP-MAIN-BOOTSTRAP: Initializing HaruQuantAI main application "
        "(host=%s, port=%d, debug=%s, reload=%s)",
        host,
        port,
        debug,
        args.reload,
        extra={
            "fr_id": "FR-APP-MAIN-BOOTSTRAP",
            "host": host,
            "port": port,
            "debug": debug,
            "reload": args.reload,
        },
    )

    host_settings = HostSettings(
        host=host,
        port=port,
        debug=debug,
        data_dir=args.data_dir,
    )

    # 3. Launch ASGI web server and trigger HostRuntime lifespan state machine
    try:
        import uvicorn

        if args.reload:
            # Development reload mode: factory string allows hot reloading
            uvicorn.run(
                "app.main:create_app",
                host=host,
                port=port,
                factory=True,
                reload=True,
            )
        else:
            # Production mode: pre-composed application instance with bound runtime
            app = create_app(settings=host_settings)
            uvicorn.run(app, host=host, port=port)

        logger.info(
            "FR-APP-MAIN-LIFECYCLE: HaruQuantAI application server stopped cleanly.",
            extra={"fr_id": "FR-APP-MAIN-LIFECYCLE"},
        )
    except ImportError:
        sys.exit(
            "uvicorn is required to run the HaruQuantAI server. "
            "Please ensure dependencies are installed."
        )
    finally:
        # 4. Process teardown boundary: drain all queued telemetry sinks
        logger.info(
            "FR-APP-MAIN-LIFECYCLE: Draining queued telemetry and shutting down.",
            extra={"fr_id": "FR-APP-MAIN-LIFECYCLE"},
        )
        shutdown(timeout=5.0)


if __name__ == "__main__":
    main()
