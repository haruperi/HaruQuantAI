"""FastAPI route registration and workspace coordinator for Data Manager.

Description:
    Exposes RESTful endpoints for the Data Manager workspace, mounting
    authoritative routes under /data. Coordinates workspace lifecycle and
    delegates dashboard requests directly to Home. Emits structured telemetry
    with zero silent execution.

Purpose:
    FEAT-DATAMGR-ROUTES: Data Manager REST API routes and workspace coordinator.

Key Capabilities:
    - FR-DATAMGR-ROUTES-WORKSPACE-FACADE: Facade (DataManagerWorkspace -> INFO).
    - FR-DATAMGR-ROUTES-FASTAPI-GATEWAY: Routes (create_data_manager_router -> INFO).

Python API Usage:
    ```python
    from app.workspace.data_manager.routes import (
        DataManagerWorkspace,
        create_data_manager_router,
    )

    workspace = DataManagerWorkspace()
    workspace.initialize_defaults()
    router = create_data_manager_router(workspace)
    ```

CLI Usage:
    ```bash
    uv run python -m app.workspace.data_manager.routes
    ```
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from app.host.logging import get_logger
from app.host.response import ApiResponse
from app.host.session import SessionManager, session_manager
from app.host.transport import extract_bearer_token
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse

from .home import Home

if TYPE_CHECKING:
    from app.host.discovery import PluginLifecycleManager
    from app.host.transport import EventBus

__all__ = [
    "DataManagerWorkspace",
    "create_data_manager_router",
]

logger = get_logger(__name__)

FACADE_FR = "FR-DATAMGR-ROUTES-WORKSPACE-FACADE"
GATEWAY_FR = "FR-DATAMGR-ROUTES-FASTAPI-GATEWAY"


class DataManagerWorkspace:
    """Authoritative workspace facade coordinating Data Manager domain services."""

    def __init__(
        self,
        *,
        data_dir: Path | str | None = None,
        event_bus: EventBus | None = None,
        plugin_mgr: PluginLifecycleManager | None = None,
        broker_registry: Any | None = None,
        job_manager: Any | None = None,
    ) -> None:
        """Instantiate workspace with data directory and event broker."""
        self.data_dir = Path(data_dir) if data_dir is not None else Path("data")
        self.event_bus = event_bus
        self.plugin_mgr = plugin_mgr
        self.broker_registry = broker_registry
        self.job_manager = job_manager

        # Initialize retained Home service
        self.home = Home()

        logger.info(
            "%s: Initialized DataManagerWorkspace (data_dir=%s)",
            FACADE_FR,
            self.data_dir,
            extra={"fr_id": FACADE_FR},
        )

    def initialize_defaults(self) -> dict[str, int]:
        """Seed default canonical catalogs."""
        counts = {
            "brokers": 0,
            "instruments": 0,
            "sessions": 0,
            "baskets": 0,
        }
        logger.info(
            "%s: Seeded default catalogs: %s",
            FACADE_FR,
            counts,
            extra={"fr_id": FACADE_FR, "seeded": counts},
        )
        return counts


def _success(data: Any, message: str = "Success") -> JSONResponse:
    return JSONResponse(content=ApiResponse.ok(data=data, meta={"message": message}))


def _register_home_routes(router: APIRouter, ws: DataManagerWorkspace) -> None:
    @router.get("/home/overview")
    def get_home_overview() -> JSONResponse:
        data = ws.home.get_overview()
        return _success(data)

    @router.get("/home/datasets")
    def get_home_datasets() -> JSONResponse:
        datasets = [d.to_dict() for d in ws.home.get_saved_datasets()]
        return _success(datasets)


def create_data_manager_router(
    workspace: DataManagerWorkspace | None = None,
    session_mgr: SessionManager | None = None,
    require_auth: bool = False,
) -> APIRouter:
    """Create and configure the FastAPI APIRouter for Data Manager endpoints."""
    ws = workspace or DataManagerWorkspace()
    effective_session_mgr = session_mgr or session_manager
    dependencies: list[Any] = []
    if require_auth:

        async def _auth_dependency(
            request: Request,
            authorization: str | None = Header(None, alias="Authorization"),
        ) -> None:
            token = extract_bearer_token(
                authorization, request.query_params.get("token")
            )
            if token is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Active session required for Data Manager access.",
                )
            runtime = getattr(request.app.state, "runtime", None)
            mgr: SessionManager = (
                getattr(runtime, "session_manager", None) or effective_session_mgr
            )
            if mgr.verify_session(token) is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired session token.",
                )

        dependencies.append(Depends(_auth_dependency))

    router = APIRouter(
        prefix="/data",
        tags=["Data Manager"],
        dependencies=dependencies,
    )

    _register_home_routes(router, ws)

    logger.info(
        "%s: Registered Data Manager router with %d route rules",
        GATEWAY_FR,
        len(router.routes),
        extra={"fr_id": GATEWAY_FR, "routes_count": len(router.routes)},
    )
    return router


def main() -> None:
    """Execute real-usage demonstration of DataManagerWorkspace and router."""
    workspace = DataManagerWorkspace()
    seeded = workspace.initialize_defaults()
    print(f"Initialized defaults: {seeded}")

    router = create_data_manager_router(workspace)
    print(f"Created Data Manager router with {len(router.routes)} endpoints")

    overview = workspace.home.get_overview()
    print(f"Workspace overview: {overview}")


if __name__ == "__main__":
    main()
