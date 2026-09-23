"""Host process bootstrap: configuration, telemetry, and server lifecycle.

The backend host listens on ``127.0.0.1:8000`` by default (frontend stays on
3000), writes dated logs under ``data/logs``, persists host settings in
``data/database/haruquantai.db``, jails file exchange to ``data/exchange``,
scans for domains under ``app/workspace`` and ``app/plugins``, and serves
the built UI from ``app/ui/dist`` when present.

Every value is overridable through the ``HARUQUANTAI_*`` environment
variables documented on :class:`HostConfig` fields, and configuration fails
closed: an empty address, a non-integer or out-of-range port, or an empty
domain-root list aborts startup instead of guessing. This module is the
single composition point where config becomes services becomes a running
server; it contains no feature logic itself.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

import uvicorn

from app.host.catalog import CatalogService
from app.host.commands import ExchangeFiles
from app.host.events import EventBus
from app.host.lifecycle import LifecycleState
from app.host.sessions import SessionManager
from app.host.settings import DEFAULT_DATABASE_PATH, SettingsStore
from app.host.telemetry import configure_host_logging
from app.host.webserver import HostServices, create_app

DEFAULT_ADDRESS = "127.0.0.1"
DEFAULT_PORT = 8000
MIN_PORT = 1
MAX_PORT = 65535
DEFAULT_LOG_DIR = Path("data/logs")
DEFAULT_EXCHANGE_ROOT = Path("data/exchange")
DEFAULT_UI_DIST = Path("app/ui/dist")
DEFAULT_DOMAIN_ROOTS = "app/workspace,app/plugins"
DEFAULT_CORS_ORIGINS = "http://127.0.0.1:3000,http://localhost:3000"

ENV_ADDRESS = "HARUQUANTAI_HOST_ADDRESS"
ENV_PORT = "HARUQUANTAI_HOST_PORT"
ENV_LOG_DIR = "HARUQUANTAI_HOST_LOG_DIR"
ENV_PASSWORD = "HARUQUANTAI_HOST_PASSWORD"  # pragma: allowlist secret # noqa: S105
ENV_DATABASE_PATH = "HARUQUANTAI_DATABASE_PATH"
ENV_EXCHANGE_ROOT = "HARUQUANTAI_EXCHANGE_ROOT"
ENV_DOMAIN_ROOTS = "HARUQUANTAI_DOMAIN_ROOTS"
ENV_UI_DIST = "HARUQUANTAI_UI_DIST"
ENV_CORS_ORIGINS = "HARUQUANTAI_CORS_ORIGINS"


@dataclass(frozen=True)
class HostConfig:
    """Resolved host runtime configuration.

    Attributes:
        address: Listen address (default ``127.0.0.1``; loopback only
            unless deliberately widened).
        port: Listen port (default ``8000``; frontend owns 3000).
        log_dir: Directory for dated log files (default ``data/logs``).
        password: Required login password (locked mode), or ``None`` for
            documented research mode.
        database_path: Settings database location
            (default ``data/database/haruquantai.db``).
        exchange_root: Jail root for sandboxed file exchange
            (default ``data/exchange``).
        domain_roots: Parent directories scanned for domain manifests
            (default ``app/workspace`` and ``app/plugins``).
        ui_dist: Built-UI directory served at ``/`` with SPA fallback, or
            ``None`` to disable static serving.
    """

    address: str
    port: int
    log_dir: Path
    password: str | None
    database_path: Path
    exchange_root: Path
    domain_roots: tuple[Path, ...]
    ui_dist: Path | None
    cors_origins: tuple[str, ...] = (
        "http://127.0.0.1:3000",
        "http://localhost:3000",
    )


def config_from_env(env: Mapping[str, str] | None = None) -> HostConfig:
    """Resolve host configuration from ``env`` (defaults to the process env).

    Raises:
        ValueError: If any provided value is empty or out of range.
    """
    source = os.environ if env is None else env
    address = source.get(ENV_ADDRESS, DEFAULT_ADDRESS)
    if not address.strip():
        raise ValueError(f"{ENV_ADDRESS} must not be empty")

    raw_port = source.get(ENV_PORT, str(DEFAULT_PORT))
    try:
        port = int(raw_port)
    except ValueError as err:
        raise ValueError(f"{ENV_PORT} must be an integer, got {raw_port!r}") from err
    if not MIN_PORT <= port <= MAX_PORT:
        raise ValueError(
            f"{ENV_PORT} must be within {MIN_PORT}..{MAX_PORT}, got {port}"
        )

    raw_roots = source.get(ENV_DOMAIN_ROOTS, DEFAULT_DOMAIN_ROOTS)
    domain_roots = tuple(
        Path(part.strip()) for part in raw_roots.split(",") if part.strip()
    )
    if not domain_roots:
        raise ValueError(f"{ENV_DOMAIN_ROOTS} must list at least one directory")

    raw_ui_dist = source.get(ENV_UI_DIST, str(DEFAULT_UI_DIST))
    ui_dist = Path(raw_ui_dist) if raw_ui_dist.strip() else None

    raw_cors = source.get(ENV_CORS_ORIGINS, DEFAULT_CORS_ORIGINS)
    cors_origins = tuple(part.strip() for part in raw_cors.split(",") if part.strip())

    return HostConfig(
        address=address,
        port=port,
        log_dir=Path(source.get(ENV_LOG_DIR, str(DEFAULT_LOG_DIR))),
        password=source.get(ENV_PASSWORD) or None,
        database_path=Path(source.get(ENV_DATABASE_PATH, str(DEFAULT_DATABASE_PATH))),
        exchange_root=Path(source.get(ENV_EXCHANGE_ROOT, str(DEFAULT_EXCHANGE_ROOT))),
        domain_roots=domain_roots,
        ui_dist=ui_dist,
        cors_origins=cors_origins,
    )


def build_services(config: HostConfig) -> HostServices:
    """Assemble every host feature service from resolved configuration.

    Construction validates the scoped host settings table or initializes it
    in a new database; tests use isolated temporary databases.

    Args:
        config: Fully resolved host configuration.

    Returns:
        A :class:`~app.host.webserver.HostServices` bundle ready for
        ``create_app``.
    """
    return HostServices(
        sessions=SessionManager(config.password),
        events=EventBus(),
        settings=SettingsStore(config.database_path),
        catalog=CatalogService(config.domain_roots),
        exchange=ExchangeFiles(config.exchange_root),
        lifecycle=LifecycleState(),
        ui_dist=config.ui_dist,
        cors_origins=config.cors_origins,
    )


def run(config: HostConfig | None = None) -> None:
    """Run the host server until interrupted or gracefully shut down.

    Order matters: telemetry first (so startup itself is logged), then
    services, then the application; finally the uvicorn server is attached
    to ``app.state`` so the session-protected ``POST /api/v1/shutdown``
    endpoint can flip its graceful-exit flag. Ctrl+C is handled by uvicorn
    with the same graceful teardown.

    Args:
        config: Override configuration; defaults to :func:`config_from_env`.
    """
    resolved = config if config is not None else config_from_env()
    logger = configure_host_logging(resolved.log_dir)
    services = build_services(resolved)
    application = create_app(services, logger)
    logger.info(
        "HaruQuantAI host starting on http://%s:%s (logs: %s)",
        resolved.address,
        resolved.port,
        resolved.log_dir,
    )
    server = uvicorn.Server(
        uvicorn.Config(
            application, host=resolved.address, port=resolved.port, log_config=None
        )
    )
    application.state.uvicorn_server = server
    server.run()
    logger.info("HaruQuantAI host stopped")
