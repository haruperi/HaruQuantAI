"""CLI parsers and command execution for Data Manager baskets service."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from app.workspace.data_manager.cli_formatters import (
    BasketsCLI,
    format_basket_table,
)

from .feature import Baskets

__all__ = [
    "BasketsCLI",
    "format_basket_table",
    "register_basket_commands",
    "run_basket_command",
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


def register_basket_commands(resources: Any) -> None:
    """Register stock group (basket) catalog operations."""
    basket = resources.add_parser("basket", help="Manage stock groups and memberships")
    commands = basket.add_subparsers(dest="basket_command", required=True)
    listing = commands.add_parser("list", help="List stock groups")
    listing.add_argument("--page", type=_positive_int, default=1)
    listing.add_argument("--page-size", type=_positive_int, default=50)
    for command in ("add", "edit"):
        parser = commands.add_parser(command)
        if command == "edit":
            parser.add_argument("basket_names", nargs="+")
        parser.add_argument(
            "--name", required=command == "add", default=argparse.SUPPRESS
        )
        parser.add_argument("--description", default=argparse.SUPPRESS)
        if command == "add":
            parser.add_argument(
                "--system", action=argparse.BooleanOptionalAction, default=False
            )
    for command in ("delete", "update-data"):
        parser = commands.add_parser(command)
        parser.add_argument("basket_names", nargs="+")
        if command == "update-data":
            parser.add_argument("--data-dir")
    commands.add_parser("list-stocks").add_argument("basket_name")
    edit = commands.add_parser("edit-stocks")
    edit.add_argument("basket_name")
    edit.add_argument(
        "--stocks", required=True, help="Ticker;from;to lines or JSON membership array"
    )
    for command in ("import-stocks", "export-stocks"):
        parser = commands.add_parser(command)
        parser.add_argument("basket_name")
        parser.add_argument("csv_path")
    for command in ("load", "save"):
        parser = commands.add_parser(command)
        parser.add_argument("json_path")
        if command == "save":
            parser.add_argument("--baskets", nargs="+")


def run_basket_command(
    arguments: argparse.Namespace, parser: Any
) -> dict[str, Any] | None:
    """Dispatch basket commands and render their catalog responses."""
    pkg = sys.modules.get(__package__ or "")
    factory = getattr(pkg, "Baskets", Baskets) if pkg else Baskets
    service = factory()
    command = arguments.basket_command
    fields = {
        key: value
        for key, value in vars(arguments).items()
        if key in {"name", "description", "system"}
    }
    result = _execute_basket(service, arguments, fields, parser)
    if not result["success"] or command in {
        "list-stocks",
        "edit-stocks",
        "import-stocks",
        "export-stocks",
        "update-data",
        "save",
    }:
        return result
    rows = [result["data"]] if command == "add" else result["data"]
    if command == "list":
        pages = max(1, (len(rows) + arguments.page_size - 1) // arguments.page_size)
        if arguments.page > pages:
            parser.error("--page exceeds the number of catalog pages")
        print(f"Page {arguments.page} of {pages} | {len(rows)} stock groups")
        start = (arguments.page - 1) * arguments.page_size
        rows = rows[start : start + arguments.page_size]
    else:
        print(result["message"])
    print(format_basket_table(rows))
    return None


def _execute_basket(
    service: Baskets, arguments: argparse.Namespace, fields: dict[str, Any], parser: Any
) -> dict[str, Any]:
    command = arguments.basket_command
    if command in {"add", "edit"}:
        result = (
            service.add(**fields)
            if command == "add"
            else service.edit(arguments.basket_names, fields)
        )
    elif command == "delete":
        result = service.delete(arguments.basket_names)
    else:
        return _basket_file_or_data(service, arguments, parser)
    return result


def _basket_file_or_data(
    service: Baskets, arguments: argparse.Namespace, parser: Any
) -> dict[str, Any]:
    command = arguments.basket_command
    result: dict[str, Any]
    if command == "list-stocks":
        result = service.list_stocks(arguments.basket_name)
    elif command == "edit-stocks":
        stocks = arguments.stocks
        if stocks.lstrip().startswith("["):
            try:
                stocks = _profile_json(stocks, container=list)
            except argparse.ArgumentTypeError as error:
                parser.error(str(error))
        result = service.edit_stocks(arguments.basket_name, stocks)
    elif command in {"import-stocks", "export-stocks"}:
        result = getattr(service, command.replace("-", "_"))(
            arguments.basket_name, arguments.csv_path
        )
    elif command == "load":
        result = service.load(arguments.json_path)
    elif command == "save":
        result = service.save(arguments.json_path, arguments.baskets)
    elif command == "update-data":
        result = service.update_data(
            arguments.basket_names, data_dir=arguments.data_dir
        )
    else:
        result = service.list()
    return result
