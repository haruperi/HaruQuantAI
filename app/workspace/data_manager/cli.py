"""Data Manager command registration, execution, and formatting utilities.

Description:
    Owns Data Manager headless parsers, service dispatch, output, and exit codes.
    Provides ASCII table formatters and dashboard presentation for the
    Data Manager workspace, rendering dataset catalogs and database summaries.
"""

from __future__ import annotations

import argparse
import json
from functools import partial
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.workspace.data_manager.baskets import Baskets
    from app.workspace.data_manager.symbols import Symbols

from app.workspace.data_manager.cli_formatters import (
    BasketsCLI,
    BrokersCLI,
    CustomDataCLI,
    DataCLI,
    SessionsCLI,
    SymbolsCLI,
    format_basket_table,
    format_broker_table,
    format_custom_table,
    format_data_dashboard,
    format_dataset_table,
    format_review_table,
    format_session_table,
    format_symbol_table,
)

__all__ = [
    "BasketsCLI",
    "BrokersCLI",
    "CustomDataCLI",
    "DataCLI",
    "SessionsCLI",
    "SymbolsCLI",
    "format_basket_table",
    "format_broker_table",
    "format_custom_table",
    "format_data_dashboard",
    "format_dataset_table",
    "format_review_table",
    "format_session_table",
    "format_symbol_table",
    "register_commands",
    "run_command",
]


def register_commands(commands: Any) -> None:
    """Register Data Manager parsers and bind the domain command handler."""
    data_manager = commands.add_parser("data-manager", help="Manage workspace data")
    resources = data_manager.add_subparsers(dest="resource", required=True)
    symbol = resources.add_parser("symbol", help="Access the symbols catalog")
    symbol_commands = symbol.add_subparsers(dest="symbol_command", required=True)
    _symbol_mutation_parsers(symbol_commands)
    symbol_list = symbol_commands.add_parser(
        "list", help="List symbols in the local catalog by page"
    )
    symbol_list.add_argument(
        "--page", type=_positive_int, default=1, help="Page number (default: 1)"
    )
    symbol_list.add_argument(
        "--page-size",
        type=_positive_int,
        default=50,
        help="Symbols per page (default: 50)",
    )
    _profile_parsers(resources, "session")
    _profile_parsers(resources, "broker")
    _basket_parsers(resources)
    from app.workspace.data_manager.custom_cli import register_custom_commands
    from app.workspace.data_manager.dukascopy_cli import register_dukascopy_commands
    from app.workspace.data_manager.help_cli import register_help_commands
    from app.workspace.data_manager.logs_cli import register_log_commands

    register_log_commands(resources)
    register_custom_commands(resources)
    register_help_commands(resources)
    register_dukascopy_commands(resources)
    from app.workspace.data_manager.sources_cli import register_source_commands

    register_source_commands(resources)
    data_manager.set_defaults(handler=partial(run_command, parser=data_manager))


def run_command(
    arguments: argparse.Namespace, *, parser: argparse.ArgumentParser
) -> int:
    """Execute a Data Manager command, emit errors, and return its exit code."""
    from app.workspace.data_manager.custom_cli import run_custom_command
    from app.workspace.data_manager.dukascopy_cli import run_dukascopy_command
    from app.workspace.data_manager.help_cli import run_help_command
    from app.workspace.data_manager.logs_cli import run_log_command

    handlers = {
        "session": _run_profile_command,
        "symbol": _run_symbol_command,
        "broker": _run_profile_command,
        "basket": _run_basket_command,
        "log": run_log_command,
        "custom": run_custom_command,
        "help": run_help_command,
        "dukascopy": run_dukascopy_command,
    }
    from app.workspace.data_manager.sources import PROVIDERS
    from app.workspace.data_manager.sources_cli import run_source_command

    handlers.update(dict.fromkeys(PROVIDERS, run_source_command))
    result = handlers[arguments.resource](arguments, parser)
    if result is None:
        return 0
    print(json.dumps(result, allow_nan=False))
    return 0 if result["success"] else 1


def _profile_json(value: str, *, container: type) -> Any:
    label = "array" if container is list else "object"
    try:
        result = json.loads(value)
    except json.JSONDecodeError as error:
        raise argparse.ArgumentTypeError(f"must be a JSON {label}") from error
    if not isinstance(result, container):
        raise argparse.ArgumentTypeError(f"must be a JSON {label}")
    return result


def _profile_parsers(resources: Any, resource: str) -> None:
    """Register shared broker and session catalog operations."""
    profile = resources.add_parser(resource, help=f"Manage {resource} profiles")
    commands = profile.add_subparsers(dest=f"{resource}_command", required=True)
    listing = commands.add_parser("list", help=f"List {resource} profiles by page")
    listing.add_argument("--page", type=_positive_int, default=1)
    listing.add_argument("--page-size", type=_positive_int, default=50)
    fields = (
        {
            "description": str,
            "timezone": str,
            "broker-id": int,
            "windows": partial(_profile_json, container=list),
            "holidays": partial(_profile_json, container=list),
        }
        if resource == "session"
        else {
            "description": str,
            "server-timezone": str,
            "postfix": str,
            "clock-policy": partial(_profile_json, container=dict),
            "clock-policy-revision": int,
        }
    )
    flags = (
        ("is-default",)
        if resource == "session"
        else ("is-system", "stockpicker-use", "mt-use", "enabled")
    )
    for command in ("add", "edit"):
        parser = commands.add_parser(
            command, help=f"{command.title()} {resource} profiles"
        )
        if command == "edit":
            parser.add_argument(f"{resource}_names", nargs="+")
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
    delete = commands.add_parser(
        "delete", help=f"Delete one or more {resource} profiles"
    )
    delete.add_argument(f"{resource}_names", nargs="+")
    if resource == "session":
        clone = commands.add_parser("clone", help="Clone a session")
        clone.add_argument("source_session")
        clone.add_argument("new_name")
    for command in ("load", "save"):
        transfer = commands.add_parser(
            command, help=f"{command.title()} {resource} JSON"
        )
        transfer.add_argument("json_path")


def _run_profile_command(
    arguments: argparse.Namespace, parser: Any
) -> dict[str, Any] | None:
    """Dispatch broker/session commands and render their catalog responses."""
    from app.workspace.data_manager.brokers import Brokers
    from app.workspace.data_manager.sessions import Sessions

    resource = arguments.resource
    service = Sessions() if resource == "session" else Brokers()
    formatter = format_session_table if resource == "session" else format_broker_table
    command = getattr(arguments, f"{resource}_command")
    if command in {"add", "edit"}:
        fields = {
            key: value
            for key, value in vars(arguments).items()
            if key
            not in {
                "command",
                "resource",
                f"{resource}_command",
                f"{resource}_names",
                "handler",
            }
        }
        result = (
            service.add(**fields)
            if command == "add"
            else service.edit(getattr(arguments, f"{resource}_names"), fields)
        )
    elif command == "clone" and isinstance(service, Sessions):
        result = service.clone(arguments.source_session, arguments.new_name)
    elif command == "delete":
        result = service.delete(getattr(arguments, f"{resource}_names"))
    elif command in {"load", "save"}:
        result = getattr(service, command)(arguments.json_path)
    else:
        result = service.list()
    if not result["success"]:
        return result
    if command == "save":
        print(
            f"Saved {result['data']['count']} {resource}s to {result['data']['path']}"
        )
        return None
    rows = [result["data"]] if command in {"add", "clone"} else result["data"]
    if command == "list":
        pages = max(1, (len(rows) + arguments.page_size - 1) // arguments.page_size)
        if arguments.page > pages:
            parser.error("--page exceeds the number of catalog pages")
        start = (arguments.page - 1) * arguments.page_size
        print(f"Page {arguments.page} of {pages} | {len(rows)} {resource}s")
        rows = rows[start : start + arguments.page_size]
    else:
        print(result["message"])
    print(formatter(rows))
    return None


def _positive_int(value: str) -> int:
    """Parse a positive pagination argument."""
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def _print_symbol_page(result: dict[str, Any], page: int, page_size: int) -> bool:
    """Render one catalog page, returning false for an out-of-range page."""
    symbols = result["data"]
    total = len(symbols)
    pages = max(1, (total + page_size - 1) // page_size)
    if page > pages:
        return False
    start = (page - 1) * page_size
    end = min(start + page_size, total)
    print(
        f"Page {page} of {pages} | Symbols {start + 1 if total else 0}-{end} of {total}"
    )
    print(SymbolsCLI.format_symbol_table(symbols[start:end], limit=None))
    if page < pages:
        print(
            "Next: uv run python -m app.cli data-manager symbol list "
            f"--page {page + 1} --page-size {page_size}"
        )
    return True


def _symbol_mutation_parsers(commands: Any) -> None:
    """Register symbol mutation arguments using service parameter names."""
    add = commands.add_parser("add", help="Create a symbol in the local catalog")
    add.add_argument("--name", required=True, help="Symbol name, e.g. EURUSD")
    add.add_argument("--datasource", required=True, help="Broker profile suffix")
    _symbol_field_arguments(add)
    edit = commands.add_parser(
        "edit", help="Edit an existing symbol in the local catalog"
    )
    edit.add_argument(
        "symbol_names", nargs="+", help="Exact saved symbol names, including suffixes"
    )
    edit.add_argument("--name", default=argparse.SUPPRESS, help="New saved symbol name")
    _symbol_field_arguments(edit)
    delete = commands.add_parser(
        "delete", help="Delete a symbol from the local catalog"
    )
    delete.add_argument(
        "symbol_names", nargs="+", help="Exact saved symbol names, including suffixes"
    )
    update = commands.add_parser("update", help="Update saved symbols from MT5")
    update.add_argument(
        "symbol_names",
        nargs="*",
        help="Names to update; omit to import into an empty catalog",
    )
    clone = commands.add_parser("clone", help="Clone a symbol in the local catalog")
    clone.add_argument("source_symbol", help="Exact saved source symbol name")
    clone.add_argument(
        "new_symbol", help="New symbol name (inherits source datasource)"
    )
    clone.add_argument("--new-datasource", help="Override the source datasource suffix")
    load = commands.add_parser("load", help="Load symbols from a CSV file")
    load.add_argument("csv_path", help="CSV path (quote paths containing spaces)")
    save = commands.add_parser("save", help="Save the full symbol catalog to CSV")
    save.add_argument(
        "csv_path", help="Destination CSV path (existing files are replaced)"
    )


def _symbol_field_arguments(add: Any) -> None:
    """Register shared optional symbol fields without overriding omitted values."""
    for field in (
        "description",
        "exchange",
        "data-type",
        "triple-swap-on",
        "swap-type",
    ):
        add.add_argument(f"--{field}", default=argparse.SUPPRESS)
    for field in (
        "default-spread",
        "pip-size",
        "pip-step",
        "point-value",
        "min-distance",
        "order-size-multiplier",
        "order-size-step",
        "swap-long",
        "swap-short",
        "commission",
    ):
        add.add_argument(f"--{field}", type=float, default=argparse.SUPPRESS)
    add.add_argument("--broker-id", type=int, default=argparse.SUPPRESS)


def _validate_symbol_edit(
    fields: dict[str, Any], names: list[str], parser: Any
) -> None:
    """Require edit values and restrict renaming to one symbol."""
    if not fields:
        parser.error("symbol edit requires at least one field to update")
    if "name" in fields and len(names) > 1:
        parser.error("--name can only rename one symbol at a time")


def _run_symbol_command(
    arguments: argparse.Namespace, parser: Any
) -> dict[str, Any] | None:
    """Dispatch catalog commands and render successful table results."""
    from app.workspace.data_manager.symbols import Symbols

    service = Symbols()
    file_commands = {
        "clone": _clone_or_update_symbols,
        "update": _clone_or_update_symbols,
        "load": _load_symbols,
        "save": _save_symbols,
    }
    if arguments.symbol_command in file_commands:
        return file_commands[arguments.symbol_command](service, arguments)
    if arguments.symbol_command in {"add", "edit"}:
        fields = {
            key: value
            for key, value in vars(arguments).items()
            if key
            not in {"command", "resource", "symbol_command", "symbol_names", "handler"}
        }
        if arguments.symbol_command == "add":
            result = service.add(**fields)
        else:
            _validate_symbol_edit(fields, arguments.symbol_names, parser)
            result = service.edit(arguments.symbol_names, updates=fields)
        if result["success"]:
            print(result["message"])
            rows = (
                [result["data"]]
                if arguments.symbol_command == "add"
                else result["data"]
            )
            print(SymbolsCLI.format_symbol_table(rows, limit=None))
            return None
    elif arguments.symbol_command == "delete":
        result = service.delete(arguments.symbol_names)
        if result["success"]:
            print(result["message"])
            for name in result["data"]:
                print(name)
            return None
    else:
        result = service.list()
        if result["success"]:
            if not _print_symbol_page(result, arguments.page, arguments.page_size):
                parser.error("--page exceeds the number of catalog pages")
            return None
    return result


def _clone_or_update_symbols(
    service: Symbols, arguments: argparse.Namespace
) -> dict[str, Any] | None:
    """Clone or update through the service and display the saved specifications."""
    result = (
        service.mt5update(arguments.symbol_names or None)
        if arguments.symbol_command == "update"
        else service.clone(
            arguments.source_symbol,
            arguments.new_symbol,
            new_datasource=arguments.new_datasource,
        )
    )
    if result["success"]:
        print(result["message"])
        print(
            SymbolsCLI.format_symbol_table(
                result["data"]
                if arguments.symbol_command == "update"
                else [result["data"]],
                limit=None,
            )
        )
        return None
    return result


def _load_symbols(
    service: Symbols, arguments: argparse.Namespace
) -> dict[str, Any] | None:
    """Load a CSV and report imported symbols and skipped row errors."""
    result = service.load(arguments.csv_path)
    if not result["success"]:
        return result
    print(result["message"])
    print(SymbolsCLI.format_symbol_table(result["data"]["loaded"]))
    for error in result["data"]["errors"]:
        print(f"Skipped row {error['row']}: {error['error']}")
    return None


def _save_symbols(
    service: Symbols, arguments: argparse.Namespace
) -> dict[str, Any] | None:
    """Export the full catalog and report the destination and count."""
    catalog = service.list()
    if not catalog["success"]:
        return catalog
    result = service.save(catalog["data"], arguments.csv_path)
    if not result["success"]:
        return result
    print(result["message"])
    print(result["data"]["path"])
    return None


def _basket_parsers(resources: Any) -> None:
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


def _run_basket_command(
    arguments: argparse.Namespace, parser: Any
) -> dict[str, Any] | None:
    from app.workspace.data_manager.baskets import Baskets

    service = Baskets()
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


if __name__ == "__main__":
    from app.workspace.data_manager.data import Data

    data_svc = Data()
    overview = data_svc.overview()
    saved_datasets = data_svc.list()
    print(DataCLI.format_data_dashboard(overview, saved_datasets))
