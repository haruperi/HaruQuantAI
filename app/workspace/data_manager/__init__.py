"""Data Manager workspace package.

Description:
    Provides HTTP router assembly and headless CLI dispatch for all
    Data Manager workspace features (symbols, sessions, brokers, baskets,
    custom indicators, data/storage, logs, help, and historical sources).
"""

from __future__ import annotations

import argparse
import json
from functools import partial
from typing import TYPE_CHECKING, Any, cast

from starlette.requests import Request

if TYPE_CHECKING:
    from fastapi import APIRouter
    from fastapi.responses import JSONResponse

__all__ = [
    "create_router",
    "register_commands",
    "run_command",
]


def _access(request: Request) -> None:
    """Apply the host's UI session and scope checks to domain requests."""
    from app.host.response import ErrorCode
    from app.host.transport import TransportError, _require

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
    from fastapi.encoders import jsonable_encoder
    from fastapi.responses import JSONResponse

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


def create_router() -> APIRouter:
    """Assemble domain router across all Data Manager feature packages."""
    from fastapi import APIRouter, Depends

    from .baskets import register_basket_routes
    from .brokers import register_broker_routes
    from .custom import register_custom_routes
    from .data.http import register_data_routes
    from .help import register_help_routes
    from .logs import register_log_routes
    from .sessions import register_session_routes
    from .sources import register_dukascopy_routes, register_source_routes
    from .symbols import register_symbol_routes

    router = APIRouter(prefix="/api/v1/data", dependencies=[Depends(_access)])

    register_data_routes(router)
    from .sources.files import register_file_routes

    register_file_routes(router)
    from .data.review import register_review_routes

    register_review_routes(router)
    from .data.exports import register_export_routes
    from .data.transforms import register_transform_routes

    register_export_routes(router)
    register_transform_routes(router)
    register_source_routes(router)
    register_symbol_routes(router)
    register_session_routes(router)
    register_broker_routes(router)
    register_basket_routes(router)
    register_log_routes(router)
    register_custom_routes(router)
    register_help_routes(router)
    register_dukascopy_routes(router)
    return router


def register_commands(commands: Any) -> None:
    """Register Data Manager CLI subcommands across all feature packages."""
    from .baskets import register_basket_commands
    from .brokers import register_broker_commands
    from .custom import register_custom_commands
    from .help import register_help_commands
    from .logs import register_log_commands
    from .sessions import register_session_commands
    from .sources import register_dukascopy_commands, register_source_commands
    from .symbols import register_symbol_commands

    data_manager = commands.add_parser("data-manager", help="Manage workspace data")
    resources = data_manager.add_subparsers(dest="resource", required=True)

    register_symbol_commands(resources)
    register_session_commands(resources)
    register_broker_commands(resources)
    register_basket_commands(resources)
    register_log_commands(resources)
    register_custom_commands(resources)
    register_help_commands(resources)
    register_dukascopy_commands(resources)
    register_source_commands(resources)

    data_manager.set_defaults(handler=partial(run_command, parser=data_manager))


def run_command(
    arguments: argparse.Namespace, *, parser: argparse.ArgumentParser
) -> int:
    """Execute a Data Manager command, emit errors, and return its exit code."""
    from .baskets import run_basket_command
    from .brokers import run_broker_command
    from .custom import run_custom_command
    from .help import run_help_command
    from .logs import run_log_command
    from .sessions import run_session_command
    from .sources import PROVIDERS, run_dukascopy_command, run_source_command
    from .symbols import run_symbol_command

    handlers = {
        "session": run_session_command,
        "symbol": run_symbol_command,
        "broker": run_broker_command,
        "basket": run_basket_command,
        "log": run_log_command,
        "custom": run_custom_command,
        "help": run_help_command,
        "dukascopy": run_dukascopy_command,
    }
    handlers.update(dict.fromkeys(PROVIDERS, run_source_command))
    result = handlers[arguments.resource](arguments, parser)
    if result is None:
        return 0
    print(json.dumps(result, allow_nan=False))
    return 0 if result["success"] else 1
