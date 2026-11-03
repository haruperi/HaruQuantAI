"""Bootstrap the HaruQuantAI FastAPI backend.

Description:
    Creates the HTTP application and composition root, owning host service
    lifespan, settings reload, diagnostic telemetry, workspace directory
    verification, and reverse teardown on termination. Run `python -m app.main`
    to start Uvicorn using stored host and port settings. ASGI servers can
    import `app.main:app`. Resources initialize during lifespan startup, not
    module import.

Purpose:
    FEAT-HOST-LIFECYCLE: Unified composition root, diagnostics, and graceful
    service lifecycle.

Key Capabilities:
    - FR-HOST-LIFECYCLE-STARTUP-INIT: Composition root startup (create_app -> INFO).
    - FR-HOST-LIFECYCLE-SERVICE-ROLLBACK: Rollback on error (lifespan -> ERROR).
    - FR-HOST-LIFECYCLE-JOB-SHUTDOWN: Worker stop (_shutdown_workspace_jobs -> INFO).
    - FR-HOST-LIFECYCLE-REVERSE-TEARDOWN: Reverse teardown (lifespan -> INFO).

Python API Usage:
    ```python
    from app.main import create_app

    application = create_app()
    ```

CLI Usage:
    ```bash
    uv run python -m app.main
    ```
"""

from __future__ import annotations

import argparse
import mimetypes
from asyncio import to_thread
from collections.abc import AsyncGenerator, Callable, Mapping, Sequence
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, Request, Response

from app.core.data.catalog import DataCatalog
from app.core.host.logging import (
    configure_logging_from_settings,
    emit_startup_diagnostics,
    get_logger,
    shutdown_logging,
)
from app.core.host.persistence import HostPersistence
from app.core.host.resources import ResourceMonitor, inspect_workspace_directories
from app.core.host.session import SessionManager, Vault
from app.core.host.settings import SettingsManager
from app.core.host.transport import CredentialTester, install_transport
from app.core.jobs.manager import JobManager
from app.workspace.data_manager.data.partition_files import (
    recover_catalog_publications,
)
from app.workspace.data_manager.logs import Logs

logger = get_logger(__name__)
_MAX_PORT = 65535
_GRACEFUL_SHUTDOWN_SECONDS = 5


def _is_reserved_path(path_str: str) -> bool:
    normalized = "/" + path_str.strip("/")
    for prefix in ("/api", "/events", "/health"):
        if normalized == prefix or normalized.startswith(prefix + "/"):
            return True
    return False


def _resolve_media_type(path: Path) -> str:
    if path.suffix == ".js":
        return "application/javascript"
    if path.suffix == ".css":
        return "text/css"
    if path.suffix == ".html":
        return "text/html"
    mime, _ = mimetypes.guess_type(str(path))
    return mime or "application/octet-stream"


def _make_response(
    status_code: int,
    media_type: str,
    headers: Mapping[str, str] | None = None,
    content: bytes = b"",
    *,
    is_head: bool = False,
) -> Response:
    body = b"" if is_head else content
    return Response(
        content=body,
        status_code=status_code,
        media_type=media_type,
        headers=dict(headers or {}),
    )


def _serve_file(path: Path, is_asset: bool, *, is_head: bool) -> Response:
    cache = "public, max-age=31536000, immutable" if is_asset else "no-cache"
    return _make_response(
        200,
        _resolve_media_type(path),
        {"Cache-Control": cache},
        path.read_bytes(),
        is_head=is_head,
    )


def _is_asset_path(candidate: Path, assets_dir: Path) -> bool:
    try:
        candidate.relative_to(assets_dir)
        return True
    except ValueError:
        return False


def install_web_build(application: FastAPI, build_dir: Path) -> None:
    """Serve the static React/Vite production build and SPA client routes."""
    resolved_build_dir = build_dir.resolve()
    assets_dir = (resolved_build_dir / "assets").resolve()

    @application.api_route(
        "/{full_path:path}",
        methods=["GET", "HEAD"],
        include_in_schema=False,
    )
    async def serve_spa_or_asset(
        request: Request,
        full_path: str = "",
    ) -> Response:
        is_head = request.method == "HEAD"
        if _is_reserved_path(full_path):
            return _make_response(
                404,
                "application/json",
                content=b'{"detail":"Not Found"}',
                is_head=is_head,
            )

        index_file = resolved_build_dir / "index.html"
        if not index_file.is_file():
            return _make_response(
                503,
                "application/json",
                {"Cache-Control": "no-store"},
                b'{"detail":"Web build unavailable"}',
                is_head=is_head,
            )

        clean = full_path.lstrip("/")
        candidate = index_file if not clean else (resolved_build_dir / clean).resolve()
        try:
            candidate.relative_to(resolved_build_dir)
        except ValueError:
            return _make_response(
                404,
                "application/json",
                content=b'{"detail":"Not Found"}',
                is_head=is_head,
            )

        if candidate.is_file():
            return _serve_file(
                candidate,
                _is_asset_path(candidate, assets_dir),
                is_head=is_head,
            )

        if clean == "assets" or clean.startswith("assets/") or candidate.suffix:
            return _make_response(
                404,
                "application/json",
                content=b'{"detail":"Not Found"}',
                is_head=is_head,
            )

        return _serve_file(index_file, is_asset=False, is_head=is_head)


async def _shutdown_workspace_jobs(application: FastAPI) -> None:
    """Release lazy workspace workers before host persistence is detached."""
    for name in ("basket_jobs", "download_jobs", "code_editor_jobs", "job_manager"):
        if (jobs := getattr(application.state, name, None)) is not None:
            await to_thread(jobs.shutdown, wait=True, cancel_futures=True)
            delattr(application.state, name)
            logger.info("FR-host-editor-job-lifecycle: worker service released")
    if hasattr(application.state, "code_editor_compilation"):
        del application.state.code_editor_compilation


def _register_routers(application: FastAPI) -> None:
    """Register workspace API routers."""
    from app.workspace.ai.routes import ai_router
    from app.workspace.code_editor import code_editor_router
    from app.workspace.data_manager import create_router
    from app.workspace.grid_control import grid_control_router
    from app.workspace.home import home_router
    from app.workspace.trading.routes import trading_router

    application.include_router(create_router())
    application.include_router(code_editor_router)
    application.include_router(grid_control_router)
    application.include_router(trading_router)
    application.include_router(ai_router)
    application.include_router(home_router)


def _run_startup_diagnostics(settings: Any) -> None:
    """Execute non-fatal logging configuration and environment diagnostics."""
    try:
        configure_logging_from_settings(settings)
    except Exception as exc:  # noqa: BLE001
        logger.debug("Troubleshooting logging setup skipped: %s", exc)
    try:
        emit_startup_diagnostics(app_version="1.0.0", settings=settings)
    except Exception as exc:  # noqa: BLE001
        logger.debug("Startup diagnostics emission skipped: %s", exc)
    try:
        inspect_workspace_directories(settings)
    except Exception as exc:  # noqa: BLE001
        logger.debug("Workspace directories inspection skipped: %s", exc)


async def _teardown_services(application: FastAPI) -> None:
    """Cleanly stop workers, close external connections, and detach state."""
    try:
        await _shutdown_workspace_jobs(application)
    finally:
        try:
            if (mt5 := getattr(application.state, "data_mt5", None)) is not None:
                await mt5.close()
        finally:
            for name in (
                "data_mt5",
                "home_service",
                "data_catalog",
                "data_logs",
                "sessions",
                "settings",
                "persistence",
            ):
                if hasattr(application.state, name):
                    delattr(application.state, name)


def _create_lifespan(
    persistence: HostPersistence | None = None,
    projects_dir: Path | None = None,
    scratch_root: Path | None = None,
) -> Callable[[FastAPI], AbstractAsyncContextManager[None]]:
    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncGenerator[None]:
        logger.info("Backend starting")
        gateway = persistence if persistence is not None else HostPersistence()
        settings = SettingsManager(gateway)
        try:
            await to_thread(settings.reload)
        except Exception:
            # Settings can contain credentials; omit exception text and traceback.
            logger.error("Backend startup failed while loading settings")  # noqa: TRY400
            raise
        application.state.persistence = gateway
        application.state.settings = settings
        _run_startup_diagnostics(settings)
        try:
            application.state.data_logs = Logs()
            job_manager = JobManager(
                persistence=gateway,
                resource_mgr=ResourceMonitor(scratch_root=scratch_root)
                if scratch_root is not None
                else None,
                reconcile_on_startup=True,
            )
            application.state.job_manager = job_manager
            catalog = DataCatalog(gateway)
            application.state.data_catalog = catalog
            await to_thread(recover_catalog_publications, gateway)

            def scopes_for(username: str) -> tuple[str, ...]:
                access = settings.get_scope("user_access")
                return ("*:*",) if username == access["username"] else ()

            application.state.sessions = SessionManager(
                gateway, scope_resolver=scopes_for
            )
            if not hasattr(application.state, "home_service"):
                from app.workspace.home import HomeService

                application.state.home_service = HomeService(
                    persistence=gateway,
                    job_manager=job_manager,
                    data_catalog=catalog,
                    settings_manager=settings,
                    projects_dir=projects_dir,
                )
            logger.info("Backend startup completed")
            yield
        finally:
            logger.info("Backend shutting down")
            await _teardown_services(application)
            logger.info("Backend shutdown completed")

    return lifespan


def create_app(
    persistence: HostPersistence | None = None,
    *,
    vault: Vault | None = None,
    connection_testers: Mapping[str, CredentialTester] | None = None,
    web_build_dir: Path | None = None,
    projects_dir: Path | None = None,
    scratch_root: Path | None = None,
) -> FastAPI:
    """Create an independent application with shared host services in app.state."""
    application = FastAPI(
        title="HaruQuantAI Backend",
        lifespan=_create_lifespan(persistence, projects_dir, scratch_root),
    )
    from app.core.host.session import WindowsCredentialVault
    from app.workspace.data_manager.sources.connections import build_provider_testers

    application.state.vault = vault if vault is not None else WindowsCredentialVault()
    application.state.connection_testers = {
        **build_provider_testers(),
        **dict(connection_testers or {}),
    }
    install_transport(application)
    _register_routers(application)

    @application.get("/health", tags=["host"])
    async def health() -> dict[str, str]:
        """Report that the backend is running after successful startup."""
        return {"status": "ok"}

    web_dir = (
        web_build_dir
        if web_build_dir is not None
        else Path(__file__).resolve().parent / "web" / "dist"
    )
    install_web_build(application, web_dir)

    return application


app = create_app()


def main(argv: Sequence[str] | None = None) -> None:
    """Start the backend using persisted bind settings and central logging."""
    try:
        parser = argparse.ArgumentParser(description="HaruQuantAI backend server")
        parser.add_argument(
            "--reload", action="store_true", help="Restart on Python source changes"
        )
        parser.add_argument(
            "--host", type=str, default=None, help="Bind host address override"
        )
        parser.add_argument(
            "--port", type=int, default=None, help="Bind port number override"
        )
        arguments = parser.parse_args(argv)
        settings = SettingsManager()
        host = (
            arguments.host
            if arguments.host is not None
            else settings.get("host", "host")
        )
        port = (
            arguments.port
            if arguments.port is not None
            else settings.get("host", "port")
        )
        if not isinstance(host, str) or not host.strip():
            raise ValueError("host.host must be a non-empty string")
        if (
            isinstance(port, bool)
            or not isinstance(port, int)
            or not 1 <= port <= _MAX_PORT
        ):
            raise ValueError("host.port must be an integer between 1 and 65535")
        _run_startup_diagnostics(settings)
        logger.info(
            "Starting backend server; host=%s; port=%d; reload=%s",
            host,
            port,
            arguments.reload,
        )
        uvicorn.run(
            "app.main:app",
            host=host,
            port=port,
            log_config=None,
            # The UI event stream can remain open indefinitely during shutdown.
            timeout_graceful_shutdown=_GRACEFUL_SHUTDOWN_SECONDS,
            reload=arguments.reload,
            reload_dirs=[str(Path(__file__).resolve().parent)]
            if arguments.reload
            else None,
        )
    finally:
        shutdown_logging()


if __name__ == "__main__":
    main()
