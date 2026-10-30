"""HTTP routes and servlet API endpoints for AppGridControl.

Description:
    Implements the FastAPI router and request handlers mimicking the donor
    GridControlServlet. Handles the 'getData' command, query parameter routing,
    and returns wire envelopes formatted according to DescriptionsSerializer.

Purpose:
    FEAT-GRID-CONTROL: Server API for distributed grid control.

Key Capabilities:
    - FR-GRID-API-GETDATA: Dispatch 'getData' queries and return serialized gridData.
    - FR-GRID-API-VALIDATION: Validate parameters and reject unsupported commands.

Python API Usage:
    from app.workspace.grid_control.views import create_grid_control_router
    router = create_grid_control_router()

CLI Usage:
    uv run python -m app.workspace.grid_control.views
"""

from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from app.core.host.logging import get_logger
from app.workspace.grid_control.models import GridDataResponse
from app.workspace.grid_control.service import GridControlService

__all__ = ["create_grid_control_router", "grid_control_router"]

_logger = get_logger(__name__)

# Default singleton service instance for global router
_default_service = GridControlService()


def create_grid_control_router(
    service: GridControlService | None = None,
    *,
    prefix: str = "/gridControl",
) -> APIRouter:
    """Create a configured APIRouter for grid control endpoints.

    Args:
        service: Optional GridControlService instance. Defaults to shared service.
        prefix: URL prefix for the router. Defaults to '/gridControl'.

    Returns:
        APIRouter configured with grid control routes.
    """
    svc = service or _default_service
    router = APIRouter(prefix=prefix, tags=["GridControl"])

    @router.get("/")
    @router.post("/")
    async def handle_grid_command(
        request: Request,
        command: str = Query(
            default="getData", description="Servlet command to execute"
        ),
    ) -> JSONResponse:
        """Handle legacy servlet command dispatch matching GridControlServlet."""
        if request.method == "POST" and command == "getData":
            try:
                body = await request.json()
                if isinstance(body, dict) and "command" in body:
                    command = str(body["command"])
            except (json.JSONDecodeError, ValueError) as err:
                _logger.debug("POST body not parsed as JSON command: %s", err)

        if command == "getData":
            _logger.info("FR-GRID-API-GETDATA: Executing command 'getData'")
            snapshot = svc.get_grid_data()
            response = GridDataResponse(grid_data=snapshot)
            return JSONResponse(content=response.to_wire_dict())

        _logger.warning(
            "FR-GRID-API-VALIDATION: Rejecting unknown command '%s'", command
        )
        raise HTTPException(
            status_code=400,
            detail=f"Unknown command '{command}'.",
        )

    @router.get("/getData")
    async def get_grid_data_direct() -> JSONResponse:
        """Direct REST endpoint returning gridData snapshot."""
        _logger.info("FR-GRID-API-GETDATA: Direct endpoint /getData called")
        snapshot = svc.get_grid_data()
        response = GridDataResponse(grid_data=snapshot)
        return JSONResponse(content=response.to_wire_dict())

    return router


grid_control_router = create_grid_control_router()
