"""FastAPI HTTP routes for Data Manager activity logs."""

from __future__ import annotations

from typing import Any, cast

from fastapi import APIRouter, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

__all__ = ["register_log_routes"]


def _response(result: dict[str, Any]) -> JSONResponse:
    """Keep service errors and HTTP status consistent with the host envelope."""
    statuses = {"validation": 422, "not_found": 404, "conflict": 409}
    body = {**result, "status": "success" if result["success"] else "error"}
    code = (
        200
        if result["success"]
        else statuses.get(
            cast("dict[str, Any]", result.get("error") or {}).get("code", "internal"),
            503,
        )
    )
    return JSONResponse(jsonable_encoder(body), status_code=code)


def register_log_routes(router: APIRouter) -> None:
    """Register activity log endpoints on the domain router."""

    @router.get("/logs")
    def logs(
        request: Request, task_id: str | None = None, limit: int = 100, offset: int = 0
    ) -> Any:
        return _response(
            request.app.state.data_logs.list(
                task_id=task_id, limit=limit, offset=offset
            )
        )

    @router.get("/logs/active")
    def active_logs(request: Request) -> Any:
        return _response(request.app.state.data_logs.list_active())

    @router.post("/logs/clear")
    def clear_logs(request: Request) -> Any:
        return _response(request.app.state.data_logs.clear())
