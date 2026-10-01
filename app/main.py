"""HaruQuantAI Host Server Process Entrypoint, Port Reservation, and Lifecycle.

Description:
    Provides the primary process entrypoint and service launcher for the
    HaruQuantAI universal backend host server.

    External relations and workflows:
    - Host bootstrap: Instantiates `BootstrapCoordinator` (`app.host.bootstrap`)
      to manage phase supervision, directory creation, and lifecycle state.
    - ASGI transport: Initializes the ASGI web application through
      `app.host.transport.create_app` and hosts it using an embedded Uvicorn
      server.
    - Persistence: Invokes `load_settings` (`app.host.settings`) and handles
      authorized offline database migrations (`migrate_auth_schema`) via
      `app.persistence.host`.
    - Browser integration: Detects port binding and optionally launches the
      platform web browser to connect to the active host server URL.

    Internal coordination:
    - arguments: Extracts command-line options (`--host`, `--port`, `--data-dir`,
      `--open-browser`, `--migrate-auth-schema`).
    - bind_socket: Reserves a non-blocking TCP socket across fallback port ranges
      before database write initialization to eliminate port collision races.
    - HostServer: Custom Uvicorn adapter that commits the selected port to
      `host_settings`, notifies the coordinator of listening readiness, and
      launches the browser.
    - run_host: Asynchronous server supervisor monitoring the coordinator's
      shutdown event and closing sockets cleanly upon exit.
    - main: Top-level entrypoint configuring boot logging, handling errors
      closed without credential leakage, and cleaning up log handlers.

Purpose:
    FEAT-MAIN-ENTRYPOINT: Top-level application server entrypoint, socket
    reservation, ASGI server initialization, and lifecycle termination.

Key Capabilities:
    - FR-MAIN-ENTRYPOINT-SOCKET: Reserves non-blocking TCP listening sockets
      across port fallback ranges without port collision races via bind_socket().
      * Verified via: logger.info("Port reserved: %s")
    - FR-MAIN-ENTRYPOINT-SERVE: Hosts the ASGI application via Uvicorn adapter,
      commits bound port to persistent settings, and reports listening readiness
      via HostServer.startup() and run_host().
      * Verified via: logger.info("Port reserved: %s") and BootstrapCoordinator
    - FR-MAIN-ENTRYPOINT-BROWSER: Automatically launches system default browser
      pointing to the active host URL via launch().
      * Verified via: logger.info("Browser launch outcome: %s")
    - FR-MAIN-ENTRYPOINT-MAINTENANCE: Executes authorized database auth
      migrations and exits without launching network listeners via main().
      * Verified via: logger.info("HaruQuantAI entrypoint starting in %s mode")

Python API Usage:
    ```python
    from app.host.settings import load_settings
    from app.main import run_host

    settings = load_settings({"port": 8000})
    await run_host(settings)
    ```

CLI Usage:
    ```bash
    uv run python -m app.main --host 127.0.0.1 --port 8000
    ```
"""

import argparse
import asyncio
import errno
import json
import socket
import sqlite3
import sys
import time
import webbrowser
from pathlib import Path
from typing import Any, override

if __name__ == "__main__" and not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import uvicorn

from app.host.bootstrap import BootstrapCoordinator
from app.host.logging import close_host_logging, configure_boot_logging, get_logger
from app.host.settings import HostSettings, load_settings
from app.host.transport import create_app
from app.persistence.host import (
    HostPersistenceError,
    HostSettingRecord,
    HostStore,
    migrate_auth_schema,
    utc_now_iso,
)

logger = get_logger(__name__)
WINDOWS_ADDRESS_IN_USE = 10048


def launch(url: str) -> bool:
    """Ask the system browser to open the supplied host URL.

    Logs the launch outcome without logging the URL. A False result does not stop
    the backend; unrelated exceptions propagate to the caller.

    Args:
        url: Host address assembled by the caller after successful binding.

    Returns:
        The browser API acceptance flag, or False on webbrowser.Error.
    """
    try:
        opened = webbrowser.open(url)
    except webbrowser.Error:
        logger.warning("Browser launch failed")
        return False
    logger.info("Browser launch outcome: %s", opened)
    return opened


def bind_socket(settings: HostSettings) -> socket.socket:
    """Reserve the configured port or the next available fallback.

    Tries at most eleven ports without exceeding 65535. Retaining the socket avoids
    a check-then-bind race and prevents initialization writes when no port is usable.

    Args:
        settings: Validated bind address and starting port.

    Returns:
        Nonblocking bound socket; the caller must close it.

    Raises:
        OSError: Binding fails for a reason other than address-in-use, or all fallback
            ports are occupied.
    """
    for port in range(settings.port, min(65536, settings.port + 11)):
        bound = socket.socket(
            socket.AF_INET6 if ":" in settings.host else socket.AF_INET,
            socket.SOCK_STREAM,
        )
        try:
            bound.bind((settings.host, port))
            bound.setblocking(False)
            logger.info("Port reserved: %s", port)
            return bound
        except OSError as error:
            bound.close()
            if (
                error.errno != errno.EADDRINUSE
                and getattr(error, "winerror", None) != WINDOWS_ADDRESS_IN_USE
            ):
                raise
            logger.warning("Port occupied: %s", port)
    raise OSError("No available port in configured fallback range")


class HostServer(uvicorn.Server):
    """Uvicorn adapter that records readiness only after transports are listening.

    Owns no separate startup loop. The injected coordinator owns application state;
    run_host retains the reserved socket and the shutdown watcher.
    """

    def __init__(self, config: uvicorn.Config, host: BootstrapCoordinator) -> None:
        """Associate the server configuration with one host coordinator.

        Args:
            config: Uvicorn configuration with explicit logging and transport policy.
            host: Coordinator whose state and settings receive listening readiness.
        """
        super().__init__(config)
        self.host = host

    @override
    async def startup(self, sockets: list[socket.socket] | None = None) -> None:
        """Start transports, record the selected port, and report server readiness.

        After successful Uvicorn startup, persists host/bound_port and completes
        the serving phase. Optionally launches the browser and reports readiness.
        If startup did not complete
        or no sockets were provided, host readiness is not marked here.

        Args:
            sockets: Reserved listening sockets supplied by run_host; None delegates to
                Uvicorn.
        """
        await super().startup(sockets=sockets)
        if not self.started or not sockets:
            return
        port = sockets[0].getsockname()[1]
        store = HostStore(self.host.config.database_path)
        store.upsert_setting(
            HostSettingRecord(
                "host", "bound_port", json.dumps({"port": port}), 1, utc_now_iso()
            )
        )
        self.host.startup.listening()
        self.host.log_boot_summary()
        if self.host.config.open_browser:
            scheme = "https" if self.host.config.certificate else "http"
            address = self.host.config.host
            if ":" in address:
                address = f"[{address}]"
            launch(f"{scheme}://{address}:{port}/")


async def run_host(
    settings: HostSettings, *, runtime_started_at: float | None = None
) -> None:
    """Serve the configured host and release its reserved socket on exit.

    The HTTP lifespan owns coordinator initialization and cleanup. A watcher turns
    the authorized shutdown event into Uvicorn shutdown. The watcher is cancelled
    and awaited and the socket closed in finally; server exceptions propagate.

    Args:
        runtime_started_at: Monotonic entrypoint start for accurate boot timing.
        settings: Validated runtime configuration with TLS, UI, and persistence
            locations.

    Raises:
        RuntimeError: Uvicorn returns without starting the server.
        OSError: No socket can be reserved or transport setup fails.
    """
    host = BootstrapCoordinator(settings, runtime_started_at=runtime_started_at)
    app = create_app(host)
    # Reserve before initialization so a bind failure cannot mutate settings.
    bound = bind_socket(settings)
    config = uvicorn.Config(
        app,
        log_config=None,
        access_log=False,
        proxy_headers=False,
        ssl_certfile=str(settings.certificate) if settings.certificate else None,
        ssl_keyfile=str(settings.private_key) if settings.private_key else None,
        ws_max_size=65536,
        timeout_graceful_shutdown=5,
    )
    server = HostServer(config, host)

    async def watch_shutdown() -> None:
        """Translate the coordinator shutdown event into Uvicorn exit intent.

        Waits without polling; run_host cancels this watcher if the server exits first.
        """
        await host.shutdown_event.wait()
        server.should_exit = True

    watcher = asyncio.create_task(watch_shutdown())
    try:
        await server.serve(sockets=[bound])
        if not server.started:
            raise RuntimeError("Host startup failed")
    finally:
        watcher.cancel()
        await asyncio.gather(watcher, return_exceptions=True)
        bound.close()
        if host.initialized or host.installation_lease.held:
            await host.close()


def arguments(argv: list[str] | None = None) -> dict[str, Any]:
    """Parse explicitly supplied CLI overrides and the maintenance switch.

    Args:
        argv: Argument sequence without executable name; None uses process arguments.

    Returns:
        Only supplied options, preserving database/environment precedence for omitted
        fields.

    Raises:
        SystemExit: Argparse handles help or rejects invalid command syntax.
    """
    parser = argparse.ArgumentParser(description="HaruQuantAI universal backend host")
    parser.add_argument("--host", default=argparse.SUPPRESS)
    parser.add_argument("--port", type=int, default=argparse.SUPPRESS)
    parser.add_argument("--data-dir", type=Path, default=argparse.SUPPRESS)
    parser.add_argument(
        "--open-browser", action="store_true", default=argparse.SUPPRESS
    )
    parser.add_argument(
        "--migrate-auth-schema",
        action="store_true",
        default=argparse.SUPPRESS,
        help="Back up and add absent auth tables, then exit without serving",
    )
    return vars(parser.parse_args(argv))


def main(argv: list[str] | None = None) -> int:
    """Run server or maintenance mode with safe diagnostics and exit status.

    Configures early logging, removes the maintenance switch from settings fields,
    and closes owned logging in finally. Migration requires caller authorization.
    Argparse exits and other BaseException subclasses are not converted to status 1.

    Args:
        argv: Optional argument list forwarded to the parser.

    Returns:
        Zero on normal completion; one for handled configuration, storage, or runtime
        failures.
    """
    runtime_started_at = time.monotonic()
    configure_boot_logging()
    stage = "runtime"
    try:
        options = arguments(argv)
        maintenance = options.pop("migrate_auth_schema", False)
        settings = load_settings(options)
        logger.info(
            "HaruQuantAI entrypoint starting in %s mode",
            "maintenance" if maintenance else "server",
        )
        if maintenance:
            migrate_auth_schema(settings.database_path)
            return 0
        stage = "initialization"
        asyncio.run(run_host(settings, runtime_started_at=runtime_started_at))
    except OSError, ValueError, RuntimeError, sqlite3.Error, HostPersistenceError:
        # No exception text: configuration errors may contain credential values.
        logger.error(  # noqa: TRY400 -- exception values may contain secrets.
            "%s Host startup failed; inspect configuration, schema and boot log", stage
        )
        return 1
    except KeyboardInterrupt:
        logger.info("HaruQuantAI entrypoint interrupted by user; shutdown complete")
        return 0
    finally:
        close_host_logging()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
