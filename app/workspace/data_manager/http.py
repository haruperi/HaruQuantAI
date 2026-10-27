"""Authenticated Data Manager HTTP adapter for the browser workspace."""

from __future__ import annotations

import json
from typing import Any, cast

from fastapi import APIRouter, Depends, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.host.response import ErrorCode
from app.host.transport import (
    TransportError,
    _require,  # pyright: ignore[reportPrivateUsage]
)
from app.workspace.data_manager.baskets import register_basket_routes
from app.workspace.data_manager.brokers import register_broker_routes
from app.workspace.data_manager.custom import register_custom_routes
from app.workspace.data_manager.data import Data
from app.workspace.data_manager.dukascopy_http import register_dukascopy_routes
from app.workspace.data_manager.help import Help
from app.workspace.data_manager.logs import register_log_routes
from app.workspace.data_manager.sessions import register_session_routes
from app.workspace.data_manager.symbols import register_symbol_routes

TABS = (
    "data",
    "symbols",
    "sessions",
    "brokers",
    "custom-data",
    "chart",
    "home",
    "stock-groups",
    "log",
)
CORE_TABS = {"data", "symbols", "sessions", "brokers", "custom-data"}


def _access(request: Request) -> None:
    """Apply the host's UI session and scope checks to domain requests."""
    scope = "data:read" if request.method == "GET" else "data:write"
    if request.headers.get("x-peer-id") == "cli" and request.url.path.startswith(
        "/api/v1/data/logs"
    ):
        token = request.headers.get("authorization", "").removeprefix("Bearer ")
        sessions = request.app.state.sessions
        if sessions.validate_session(token, "cli") is None:
            raise TransportError(ErrorCode.UNAUTHORIZED, "A CLI session is required")
        if not sessions.authorize(token, "cli", scope):
            raise TransportError(ErrorCode.FORBIDDEN, "Capability is not granted")
    else:
        _require(request, scope)


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


def _ok(data: Any) -> dict[str, Any]:
    return {"status": "success", "success": True, "data": data}


def _json(value: Any) -> dict[str, Any]:
    return json.loads(value) if isinstance(value, str) else value or {}


def create_router() -> APIRouter:
    """Register browser workspace and symbol commands within their domain."""
    router = APIRouter(prefix="/api/v1/data", dependencies=[Depends(_access)])

    @router.get("/home/datasets")
    def datasets() -> dict[str, Any]:
        return _ok(_service_data(Data().list()))

    @router.get("/workspace")
    def workspace() -> dict[str, Any]:
        return _ok(
            {
                "tabs": [
                    {
                        "id": key,
                        "title": key.replace("-", " ").title(),
                        "core": key in CORE_TABS,
                    }
                    for key in TABS
                ],
                "active_tab": "data",
                "layout": {"core_group": "catalogs", "chart_position": "right"},
            }
        )

    @router.post("/workspace/tabs/{tab}")
    def open_tab(tab: str) -> dict[str, Any]:
        tab = "symbols" if tab == "instruments" else tab
        if tab not in TABS:
            raise TransportError(ErrorCode.NOT_FOUND, "Unknown workspace tab")
        return _ok(
            {
                "active_tab": tab,
                "selection": None,
                "preview": {
                    "state": "unavailable",
                    "reason": "Select a saved dataset to preview bars.",
                    "rows": [],
                    "limit": 500,
                },
            }
        )

    _source_routes(router)
    register_symbol_routes(router)
    register_session_routes(router)
    register_broker_routes(router)
    register_basket_routes(router)
    register_log_routes(router)
    register_custom_routes(router)
    _help_routes(router)
    register_dukascopy_routes(router)
    return router


def _service_data(response: dict[str, Any]) -> Any:
    if not response["success"]:
        error: dict[str, Any] = response.get("error") or {}
        raise TransportError(
            ErrorCode(error.get("code", "internal")), response["message"]
        )
    return response["data"]


def _help_routes(router: APIRouter) -> None:
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


def _source_routes(router: APIRouter) -> None:
    @router.get("/sources/{provider}/{action}")
    @router.post("/sources/{provider}/{action}")
    async def source_command(
        provider: str, action: str, request: Request, body: dict[str, Any] | None = None
    ) -> Any:
        from app.workspace.data_manager.source_mt5 import bridge_action
        from app.workspace.data_manager.sources import Sources, capabilities

        try:
            if action == "capabilities":
                return _ok(capabilities(provider))
            if provider == "mt5" and (
                action == "status" or (action == "connect" and request.method == "POST")
            ):
                return _ok(await bridge_action(action, request.app))
            if action == "add" and request.method == "POST":
                return _response(
                    Sources(request.app.state.persistence).add(
                        provider, (body or {}).get("definitions", [])
                    )
                )
            raise TransportError(ErrorCode.VALIDATION, "Unknown source operation")
        except (ValueError, TypeError) as error:
            raise TransportError(ErrorCode.VALIDATION, str(error)) from error
