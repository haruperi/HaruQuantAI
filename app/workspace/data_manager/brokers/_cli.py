"""CLI parsers and command execution for Data Manager broker profiles service."""

from __future__ import annotations

import argparse
import json
import sys
from functools import partial
from typing import Any

from ._helpers import BrokersCLI, format_broker_table
from .feature import Brokers

__all__ = [
    "BrokersCLI",
    "format_broker_table",
    "register_broker_commands",
    "run_broker_command",
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


def register_broker_commands(resources: Any) -> None:
    """Register shared broker catalog operations."""
    profile = resources.add_parser("broker", help="Manage broker profiles")
    commands = profile.add_subparsers(dest="broker_command", required=True)
    listing = commands.add_parser("list", help="List broker profiles by page")
    listing.add_argument("--page", type=_positive_int, default=1)
    listing.add_argument("--page-size", type=_positive_int, default=50)
    fields = {
        "description": str,
        "server-timezone": str,
        "postfix": str,
        "clock-policy": partial(_profile_json, container=dict),
        "clock-policy-revision": int,
    }
    flags = ("is-system", "stockpicker-use", "mt-use", "enabled")
    for command in ("add", "edit"):
        parser = commands.add_parser(command, help=f"{command.title()} broker profiles")
        if command == "edit":
            parser.add_argument("broker_names", nargs="+")
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
    delete = commands.add_parser("delete", help="Delete one or more broker profiles")
    delete.add_argument("broker_names", nargs="+")
    for command in ("load", "save"):
        transfer = commands.add_parser(command, help=f"{command.title()} broker JSON")
        transfer.add_argument("json_path")


def run_broker_command(
    arguments: argparse.Namespace, parser: Any
) -> dict[str, Any] | None:
    """Dispatch broker commands and render their catalog responses."""
    pkg = sys.modules.get(__package__ or "")
    factory = getattr(pkg, "Brokers", Brokers) if pkg else Brokers
    service = factory()
    formatter = format_broker_table
    command = arguments.broker_command
    if command in {"add", "edit"}:
        fields = {
            key: value
            for key, value in vars(arguments).items()
            if key
            not in {
                "command",
                "resource",
                "broker_command",
                "broker_names",
                "handler",
            }
        }
        result = (
            service.add(**fields)
            if command == "add"
            else service.edit(arguments.broker_names, fields)
        )
    elif command == "delete":
        result = service.delete(arguments.broker_names)
    elif command in {"load", "save"}:
        result = getattr(service, command)(arguments.json_path)
    else:
        result = service.list()
    if not result["success"]:
        return result
    if command == "save":
        print(f"Saved {result['data']['count']} brokers to {result['data']['path']}")
        return None
    rows = [result["data"]] if command == "add" else result["data"]
    if command == "list":
        pages = max(1, (len(rows) + arguments.page_size - 1) // arguments.page_size)
        if arguments.page > pages:
            parser.error("--page exceeds the number of catalog pages")
        start = (arguments.page - 1) * arguments.page_size
        print(f"Page {arguments.page} of {pages} | {len(rows)} brokers")
        rows = rows[start : start + arguments.page_size]
    else:
        print(result["message"])
    print(formatter(rows))
    return None
