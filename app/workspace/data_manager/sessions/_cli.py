"""CLI parsers and command execution for Data Manager trading sessions service."""

from __future__ import annotations

import argparse
import json
from functools import partial
from typing import Any

from ._helpers import SessionsCLI, format_session_table
from .feature import Sessions

__all__ = [
    "SessionsCLI",
    "format_session_table",
    "register_session_commands",
    "run_session_command",
]


def _positive_int(value: str) -> int:
    """Parse a positive pagination argument."""
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def _profile_json(value: str, *, container: type) -> Any:
    label = "array" if container is list else "object"
    try:
        result = json.loads(value)
    except json.JSONDecodeError as error:
        raise argparse.ArgumentTypeError(f"must be a JSON {label}") from error
    if not isinstance(result, container):
        raise argparse.ArgumentTypeError(f"must be a JSON {label}")
    return result


def register_session_commands(resources: Any) -> None:
    """Register trading session catalog operations."""
    profile = resources.add_parser("session", help="Manage session profiles")
    commands = profile.add_subparsers(dest="session_command", required=True)
    listing = commands.add_parser("list", help="List session profiles by page")
    listing.add_argument("--page", type=_positive_int, default=1)
    listing.add_argument("--page-size", type=_positive_int, default=50)
    fields = {
        "description": str,
        "timezone": str,
        "broker-id": int,
        "windows": partial(_profile_json, container=list),
        "holidays": partial(_profile_json, container=list),
    }
    flags = ("is-default",)
    for command in ("add", "edit"):
        parser = commands.add_parser(
            command, help=f"{command.title()} session profiles"
        )
        if command == "edit":
            parser.add_argument("session_names", nargs="+")
        parser.add_argument(
            "--name", required=command == "add", default=argparse.SUPPRESS
        )
        for field, kind in fields.items():
            parser.add_argument(f"--{field}", type=kind, default=argparse.SUPPRESS)
        for flag in flags:
            parser.add_argument(
                f"--{flag}",
                action=argparse.BooleanOptionalAction,
                default=argparse.SUPPRESS,
            )
    delete = commands.add_parser("delete", help="Delete one or more session profiles")
    delete.add_argument("session_names", nargs="+")
    clone = commands.add_parser("clone", help="Clone a session")
    clone.add_argument("source_session")
    clone.add_argument("new_name")
    for command in ("load", "save"):
        transfer = commands.add_parser(command, help=f"{command.title()} session JSON")
        transfer.add_argument("json_path")


def run_session_command(
    arguments: argparse.Namespace, parser: Any
) -> dict[str, Any] | None:
    """Dispatch session commands and render their catalog responses."""
    service = Sessions()
    command = arguments.session_command
    if command in {"add", "edit"}:
        fields = {
            key: value
            for key, value in vars(arguments).items()
            if key
            not in {
                "command",
                "resource",
                "session_command",
                "session_names",
                "handler",
            }
        }
        result = (
            service.add(**fields)
            if command == "add"
            else service.edit(arguments.session_names, fields)
        )
    elif command == "clone":
        result = service.clone(arguments.source_session, arguments.new_name)
    elif command == "delete":
        result = service.delete(arguments.session_names)
    elif command in {"load", "save"}:
        result = getattr(service, command)(arguments.json_path)
    else:
        result = service.list()
    if not result["success"]:
        return result
    if command == "save":
        print(f"Saved {result['data']['count']} sessions to {result['data']['path']}")
        return None
    rows = [result["data"]] if command in {"add", "clone"} else result["data"]
    if command == "list":
        pages = max(1, (len(rows) + arguments.page_size - 1) // arguments.page_size)
        if arguments.page > pages:
            parser.error("--page exceeds the number of catalog pages")
        start = (arguments.page - 1) * arguments.page_size
        print(f"Page {arguments.page} of {pages} | {len(rows)} sessions")
        rows = rows[start : start + arguments.page_size]
    else:
        print(result["message"])
    print(format_session_table(rows))
    return None
