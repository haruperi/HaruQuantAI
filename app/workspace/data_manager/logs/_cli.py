"""CLI access to the running backend's shared Data Manager activity history."""

from __future__ import annotations

import argparse
import os
import sys
from typing import Any

import httpx

from app.core.host.settings import SettingsManager
from app.core.lib.responses import (
    ErrorCode,
    ResponseMetadata,
    StandardError,
    StandardResponse,
)

_MAX_PAGE = 1000

__all__ = ["register_log_commands", "run_log_command"]


def _get_settings_manager() -> Any:
    mod = sys.modules.get("app.workspace.data_manager.logs")
    if mod and hasattr(mod, "SettingsManager"):
        return mod.SettingsManager
    return SettingsManager


def _get_httpx() -> Any:
    mod = sys.modules.get("app.workspace.data_manager.logs")
    if mod and hasattr(mod, "httpx"):
        return mod.httpx
    return httpx


def register_log_commands(resources: Any) -> None:
    """Register read and clear operations; recording remains internal."""
    parser = resources.add_parser("log", help="Access running backend activity logs")
    commands = parser.add_subparsers(dest="log_command", required=True)
    listing = commands.add_parser("list", help="List newest activity entries")
    listing.add_argument("--task-id")
    listing.add_argument("--limit", type=int, default=100)
    listing.add_argument("--offset", type=int, default=0)
    commands.add_parser("list-active", help="List active tasks")
    commands.add_parser("clear", help="Clear activity history, preserving active tasks")


def _failure(code: ErrorCode, message: str) -> dict[str, Any]:
    return StandardResponse.failure(
        message=message,
        error=StandardError(code=code, message=message),
        metadata=ResponseMetadata(operation="logs.cli", duration_ms=0),
    )


def run_log_command(
    arguments: argparse.Namespace, parser: argparse.ArgumentParser
) -> dict[str, Any]:
    """Call the backend with an existing CLI-bound bearer session."""
    token = os.environ.get("HARUQUANTAI_SESSION_TOKEN")
    if not token:
        return _failure(
            ErrorCode.UNAUTHORIZED,
            "Set HARUQUANTAI_SESSION_TOKEN using CLI login first",
        )
    command = arguments.log_command
    params: dict[str, Any] = {}
    if command == "list":
        if not 1 <= arguments.limit <= _MAX_PAGE or arguments.offset < 0:
            parser.error(
                "log limit must be between 1 and 1000; offset must be non-negative"
            )
        params = {"limit": arguments.limit, "offset": arguments.offset}
        if arguments.task_id is not None:
            params["task_id"] = arguments.task_id
    try:
        settings_cls = _get_settings_manager()
        settings = settings_cls()
        settings.reload()
        host = str(settings.get("host", "host", "127.0.0.1"))
        host = "127.0.0.1" if host == "0.0.0.0" else "::1" if host == "::" else host  # noqa: S104
        if ":" in host:
            host = f"[{host}]"
        port = int(settings.get("host", "port", 8000))
        suffix = {"list": "", "list-active": "/active", "clear": "/clear"}[command]
        httpx_mod = _get_httpx()
        with httpx_mod.Client(timeout=10, trust_env=False) as client:
            response = client.request(
                "POST" if command == "clear" else "GET",
                f"http://{host}:{port}/api/v1/data/logs{suffix}",
                params=params,
                headers={"Authorization": f"Bearer {token}", "X-Peer-Id": "cli"},
            )
        result = response.json()
        if not isinstance(result, dict) or not isinstance(result.get("success"), bool):
            return _failure(ErrorCode.UNAVAILABLE, "Invalid backend log response")
        return result
    except httpx.HTTPError, ValueError, OSError, RuntimeError:
        return _failure(
            ErrorCode.UNAVAILABLE,
            "Cannot access backend logs; ensure the backend is running",
        )
