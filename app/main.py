"""Main UI and FastAPI/Uvicorn web server entrypoint with 7-stage bootstrap.

Description:
    Serves as the primary UI and web-server starting point for HaruQuantAI
    (invoked via `uv run python -m app.main` or the `haruquantai` script).
    Resolves host bind address, port, debug flags, and workspace directories
    from CLI arguments and database settings, composes the FastAPI gateway
    application bound to the progressive 7-stage AppHost state machine
    (CONFIGURING -> PATHS -> LOGGING -> PERSISTENCE -> SERVICES -> ROUTES ->
    READY), and launches the Uvicorn ASGI server. On server exit or failure,
    executes reverse-order (LIFO) stage teardown and drains queued telemetry
    sinks via shutdown_logging().

Purpose:
    FEAT-HOST-MAIN: Main UI and FastAPI/Uvicorn web server entrypoint
    coordinating the 7-stage host bootstrap and ASGI server lifecycle.

Key Capabilities:
    - FR-HOST-MAIN-CONFIG-RESOLUTION: Resolve host bind address, port, debug
      mode, and workspace paths from CLI arguments and database settings into
      an immutable AppHost.Config(headless=False).
      Associated: `resolve_main_config()`, `_build_parser()`
      Logging: Emits INFO detailing resolved host, port, debug, and data_dir.
    - FR-HOST-MAIN-APP-FACTORY: Compose the FastAPI application (create_app)
      bound to AppHost so entering the ASGI lifespan executes all 7
      bootstrap stages and mounts UI/API routers.
      Associated: `create_app()`
      Logging: Emits INFO when composing the FastAPI application and binding
      the 7-stage runtime.
    - FR-HOST-MAIN-UVICORN-LIFECYCLE: Launch the Uvicorn ASGI server
      (uvicorn.run) or run --check-only 7-stage verification, ensuring
      reverse-order stage teardown and telemetry queue draining on exit.
      Associated: `run_server()`, `main()`
      Logging: Emits INFO on Uvicorn server startup, clean stop, and telemetry
      drain completion.

Python API Usage:
    ```python
    from app.main import create_app, resolve_main_config

    cfg, _ = resolve_main_config(["--port", "8080", "--data-dir", "data"])
    app = create_app(config=cfg)
    ```

CLI Usage:
    ```bash
    uv run python -m app.main --check-only
    uv run python -m app.main --host 127.0.0.1 --port 8000
    uv run python -m app.main --reload
    ```
"""

from __future__ import annotations

import argparse
from collections.abc import AsyncGenerator, Sequence
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import uvicorn
from app.host.bootstrap import AppHost
from app.host.logging import get_logger, setup_logging, shutdown_logging
from app.host.settings import settings as default_host_settings
from fastapi import FastAPI

__all__ = [
    "create_app",
    "resolve_main_config",
    "run_server",
]

logger = get_logger(__name__)

CONFIG_RESOLUTION_FR = "FR-HOST-MAIN-CONFIG-RESOLUTION"
APP_FACTORY_FR = "FR-HOST-MAIN-APP-FACTORY"
UVICORN_LIFECYCLE_FR = "FR-HOST-MAIN-UVICORN-LIFECYCLE"


def _build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser for the UI/FastAPI server entrypoint."""
    parser = argparse.ArgumentParser(
        prog="haruquantai",
        description="HaruQuantAI UI & FastAPI/Uvicorn Host Server",
    )
    parser.add_argument(
        "--host",
        type=str,
        default=None,
        help="Bind IP address (defaults to settings app_general.host or 127.0.0.1).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Bind port (defaults to settings app_general.backend_port or 8000).",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        default=None,
        help="Enable debug logging and diagnostics.",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        default=False,
        help="Enable Uvicorn hot-reload mode for development.",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="Root directory for database, logs, scratch, and plugins.",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=None,
        help="Explicit SQLite database file path override.",
    )
    parser.add_argument(
        "--plugins-dir",
        type=Path,
        default=None,
        help="Explicit dynamic plugins directory override.",
    )
    parser.add_argument(
        "--require-auth",
        action="store_true",
        default=False,
        help="Require bearer session authentication on protected routes.",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        default=False,
        help="Execute all 7 bootstrap stages + FastAPI route check and exit cleanly.",
    )
    return parser


def resolve_main_config(
    argv: Sequence[str] | None = None,
    *,
    settings_source: Any | None = None,
) -> tuple[Any, argparse.Namespace]:
    """Resolve CLI arguments and database settings into an ``AppHost.Config``."""
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else [])
    cfg_src = settings_source if settings_source is not None else default_host_settings

    db_host = str(cfg_src.get("app_general", "host", "127.0.0.1") or "127.0.0.1")
    raw_port = cfg_src.get("app_general", "backend_port", 8000)
    db_port = int(raw_port) if isinstance(raw_port, (int, str)) else 8000
    db_debug = bool(cfg_src.get("config_troubleshooting", "debug_level_active", False))

    host = str(args.host) if args.host is not None else db_host
    port = int(args.port) if args.port is not None else db_port
    debug = bool(args.debug) if args.debug is not None else db_debug
    data_dir = Path(args.data_dir) if args.data_dir is not None else Path("data")

    config = AppHost.Config(
        host=host,
        port=port,
        debug=debug,
        headless=False,
        require_auth=bool(args.require_auth),
        data_dir=data_dir,
        db_path=args.db_path,
        plugins_dir=args.plugins_dir,
    )
    logger.info(
        "%s: Resolved UI server config (host=%s port=%d debug=%s data_dir=%s).",
        CONFIG_RESOLUTION_FR,
        config.host,
        config.port,
        config.debug,
        config.data_dir,
        extra={
            "fr_id": CONFIG_RESOLUTION_FR,
            "host": config.host,
            "port": config.port,
            "debug": config.debug,
        },
    )
    return config, args


def create_app(
    config: Any | None = None,
    *,
    runtime: AppHost | None = None,
) -> FastAPI:
    """Create the FastAPI application orchestrated by the 5-method AppHost lifecycle."""
    if config is None:
        resolved_config, _ = resolve_main_config([])
    else:
        resolved_config = config

    logger.info(
        "%s: Creating FastAPI UI/gateway application (host=%s port=%d).",
        APP_FACTORY_FR,
        resolved_config.host,
        resolved_config.port,
        extra={"fr_id": APP_FACTORY_FR},
    )
    host = runtime or AppHost(config=resolved_config)
    app = host.startup()

    @asynccontextmanager
    async def _lifespan(target_app: FastAPI) -> AsyncGenerator[None]:
        runtime_host: AppHost = target_app.state.runtime
        logger.info(
            "%s: FastAPI lifespan orchestrating AppHost lifecycle.",
            UVICORN_LIFECYCLE_FR,
            extra={"fr_id": UVICORN_LIFECYCLE_FR},
        )
        runtime_host.startup()
        runtime_host.initialize_db()
        runtime_host.register_modules(target_app)
        runtime_host.broadcast_event(
            channel="system",
            event_type="host.ready",
            payload={
                "host_instance_id": runtime_host.host_instance_id,
                "state": runtime_host.state.value,
            },
        )
        try:
            yield
        finally:
            logger.info(
                "%s: FastAPI lifespan shutting down AppHost.",
                UVICORN_LIFECYCLE_FR,
                extra={"fr_id": UVICORN_LIFECYCLE_FR},
            )
            runtime_host.shutdown()

    app.router.lifespan_context = _lifespan
    app.state.runtime = host
    app.state.config = host.config
    return app


def run_server(
    argv: Sequence[str] | None = None,
    *,
    uvicorn_runner: Any | None = None,
) -> int:
    """Execute the 7-stage bootstrap and start the FastAPI/Uvicorn server."""
    config, args = resolve_main_config(argv)
    setup_logging(
        log_dir=config.resolved_log_dir,
        level=10 if config.debug else 20,
    )
    runner = uvicorn_runner if uvicorn_runner is not None else uvicorn.run

    logger.info(
        "%s: Starting HaruQuantAI UI/API server lifecycle (check_only=%s reload=%s).",
        UVICORN_LIFECYCLE_FR,
        args.check_only,
        args.reload,
        extra={"fr_id": UVICORN_LIFECYCLE_FR},
    )
    try:
        if args.check_only:
            host = AppHost(config=config)
            app = host.startup()
            try:
                host.initialize_db()
                host.register_modules(app)
                host.broadcast_event(
                    channel="system",
                    event_type="host.ready",
                    payload={
                        "host_instance_id": host.host_instance_id,
                        "state": host.state.value,
                    },
                )
                logger.info(
                    "%s: Check-only verified %d stages and %d FastAPI routes.",
                    UVICORN_LIFECYCLE_FR,
                    len(host.completed_stages),
                    len(app.routes),
                    extra={"fr_id": UVICORN_LIFECYCLE_FR},
                )
            finally:
                host.shutdown()
            return 0

        if args.reload:
            runner(
                "app.main:create_app",
                host=config.host,
                port=config.port,
                factory=True,
                reload=True,
                timeout_graceful_shutdown=config.timeout_graceful_shutdown,
            )
        else:
            app = create_app(config=config)
            runner(
                app,
                host=config.host,
                port=config.port,
                timeout_graceful_shutdown=config.timeout_graceful_shutdown,
            )

        logger.info(
            "%s: HaruQuantAI Uvicorn server stopped cleanly.",
            UVICORN_LIFECYCLE_FR,
            extra={"fr_id": UVICORN_LIFECYCLE_FR},
        )
        return 0
    finally:
        logger.info(
            "%s: Draining telemetry queue and completing server shutdown.",
            UVICORN_LIFECYCLE_FR,
            extra={"fr_id": UVICORN_LIFECYCLE_FR},
        )
        shutdown_logging()


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint for `uv run python -m app.main`."""
    import tempfile

    effective_argv = list(argv) if argv is not None else None
    if effective_argv is None:
        import sys

        effective_argv = sys.argv[1:]

    if "--check-only" in effective_argv and "--data-dir" not in effective_argv:
        with tempfile.TemporaryDirectory(
            prefix="hqai_main_check_",
            ignore_cleanup_errors=True,
        ) as tmp_dir:
            code = run_server([*effective_argv, "--data-dir", tmp_dir])
            print(
                "HaruQuantAI UI Server (--check-only): 7-stage bootstrap + FastAPI OK"
            )
            return code

    return run_server(effective_argv)


if __name__ == "__main__":
    raise SystemExit(main())
