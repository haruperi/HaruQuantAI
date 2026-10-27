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
from typing import Any, cast

from fastapi import APIRouter, Depends, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.host.response import ErrorCode
from app.host.transport import (
    TransportError,
    _require,  # pyright: ignore[reportPrivateUsage]
)
from app.workspace.data_manager.baskets import (
    register_basket_commands,
    register_basket_routes,
    run_basket_command,
)
from app.workspace.data_manager.brokers import (
    register_broker_commands,
    register_broker_routes,
    run_broker_command,
)
from app.workspace.data_manager.custom import (
    register_custom_commands,
    register_custom_routes,
    run_custom_command,
)
from app.workspace.data_manager.data import register_data_routes
from app.workspace.data_manager.help import (
    register_help_commands,
    register_help_routes,
    run_help_command,
)
from app.workspace.data_manager.logs import (
    register_log_commands,
    register_log_routes,
    run_log_command,
)
from app.workspace.data_manager.sessions import (
    register_session_commands,
    register_session_routes,
    run_session_command,
)
from app.workspace.data_manager.sources import (
    PROVIDERS,
    register_dukascopy_commands,
    register_dukascopy_routes,
    register_source_commands,
    register_source_routes,
    run_dukascopy_command,
    run_source_command,
)
from app.workspace.data_manager.symbols import (
    register_symbol_commands,
    register_symbol_routes,
    run_symbol_command,
)

__all__ = [
    "create_router",
    "register_commands",
    "run_command",
]


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


def create_router() -> APIRouter:
    """Assemble domain router across all Data Manager feature packages."""
    router = APIRouter(prefix="/api/v1/data", dependencies=[Depends(_access)])

    register_data_routes(router)
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
