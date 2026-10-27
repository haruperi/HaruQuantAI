"""FastAPI HTTP routes for Data Manager contextual help and tutorials."""

from __future__ import annotations

from typing import Any, cast

from fastapi import APIRouter, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from .feature import Help

__all__ = ["register_help_routes"]


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


def register_help_routes(router: APIRouter) -> None:
    """Register contextual help and tutorial endpoints on the domain router."""

    @router.get("/help")
    def get_help_guide(request: Request, topic: str = "overview") -> Any:
        service = Help(request.app.state.persistence)
        return _response(service.get_topic(topic))

    @router.get("/help/topics")
    def list_help_topics(request: Request) -> Any:
        service = Help(request.app.state.persistence)
        return _response(service.list_topics())

    @router.get("/help/tutorials")
    def list_help_tutorials(request: Request, topic: str | None = None) -> Any:
        service = Help(request.app.state.persistence)
        return _response(service.list_tutorials(topic))

    @router.get("/help/articles")
    def list_help_articles(request: Request, topic: str | None = None) -> Any:
        service = Help(request.app.state.persistence)
        return _response(service.list_articles(topic))

    @router.get("/help/search")
    def search_help(request: Request, query: str = "") -> Any:
        service = Help(request.app.state.persistence)
        return _response(service.search(query))
