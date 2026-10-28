"""Bootstrap the HaruQuantAI FastAPI backend.

Run `python -m app.main` or the `haruquantai` console command to start Uvicorn
using the stored host.host and host.port settings. ASGI servers can import
`app.main:app`. Resources initialize during lifespan startup, not import.
Use `python -m app.main --reload` to restart on Python source changes in app/.
"""

from __future__ import annotations

import argparse
from asyncio import to_thread
from collections.abc import AsyncGenerator, Mapping, Sequence
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI

from app.host.logging import get_logger, shutdown_logging
from app.host.persistence import HostPersistence
from app.host.session import SessionManager
from app.host.settings import SettingsManager
from app.host.transport import CredentialTester, install_transport
from app.host.vault import Vault
from app.workspace.data_manager.data.partition_files import recover_catalog_publications
from app.workspace.data_manager.logs import Logs

logger = get_logger(__name__)
_MAX_PORT = 65535
_GRACEFUL_SHUTDOWN_SECONDS = 5


def create_app(
    persistence: HostPersistence | None = None,
    *,
    vault: Vault | None = None,
    connection_testers: Mapping[str, CredentialTester] | None = None,
) -> FastAPI:
    """Create an independent application with shared host services in app.state."""

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
        application.state.data_logs = Logs()
        await to_thread(recover_catalog_publications, gateway)

        def scopes_for(username: str) -> tuple[str, ...]:
            access = settings.get_scope("user_access")
            return ("*:*",) if username == access["username"] else ()

        application.state.sessions = SessionManager(gateway, scope_resolver=scopes_for)
        logger.info("Backend startup completed")
        try:
            yield
        finally:
            logger.info("Backend shutting down")
            for name in ("basket_jobs", "download_jobs"):
                if (jobs := getattr(application.state, name, None)) is not None:
                    await to_thread(jobs.shutdown, wait=True, cancel_futures=True)
                    delattr(application.state, name)
            if (mt5 := getattr(application.state, "data_mt5", None)) is not None:
                await mt5.close()
            del application.state.data_logs
            del application.state.sessions
            del application.state.settings
            del application.state.persistence
            logger.info("Backend shutdown completed")

    application = FastAPI(title="HaruQuantAI Backend", lifespan=lifespan)
    from app.host.vault import WindowsCredentialVault
    from app.workspace.data_manager.sources.connections import build_provider_testers

    application.state.vault = vault if vault is not None else WindowsCredentialVault()
    application.state.connection_testers = {
        **build_provider_testers(),
        **dict(connection_testers or {}),
    }
    install_transport(application)
    from app.workspace.data_manager import create_router

    application.include_router(create_router())

    from app.workspace.code_editor import code_editor_router

    application.include_router(code_editor_router)

    @application.get("/health", tags=["host"])
    async def health() -> dict[str, str]:
        """Report that the backend is running after successful startup."""
        return {"status": "ok"}

    return application


app = create_app()


def main(argv: Sequence[str] | None = None) -> None:
    """Start the backend using persisted bind settings and central logging."""
    try:
        parser = argparse.ArgumentParser(description="HaruQuantAI backend server")
        parser.add_argument(
            "--reload", action="store_true", help="Restart on Python source changes"
        )
        arguments = parser.parse_args(argv)
        settings = SettingsManager()
        host = settings.get("host", "host")
        port = settings.get("host", "port")
        if not isinstance(host, str) or not host.strip():
            raise ValueError("host.host must be a non-empty string")
        if (
            isinstance(port, bool)
            or not isinstance(port, int)
            or not 1 <= port <= _MAX_PORT
        ):
            raise ValueError("host.port must be an integer between 1 and 65535")
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
