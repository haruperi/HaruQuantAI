"""CLI parsers and command execution for Data Manager symbols service."""

from __future__ import annotations

import argparse
from typing import TYPE_CHECKING, Any

from ._helpers import SymbolsCLI

if TYPE_CHECKING:
    from .feature import Symbols

__all__ = [
    "register_symbol_commands",
    "run_symbol_command",
]


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


def _validate_symbol_edit(
    fields: dict[str, Any], names: list[str], parser: Any
) -> None:
    """Require edit values and restrict renaming to one symbol."""
    if not fields:
        parser.error("symbol edit requires at least one field to update")
    if "name" in fields and len(names) > 1:
        parser.error("--name can only rename one symbol at a time")


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


def register_symbol_commands(resources: Any) -> None:
    """Register symbol catalog parsers under data-manager."""
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


def run_symbol_command(
    arguments: argparse.Namespace, parser: Any
) -> dict[str, Any] | None:
    """Dispatch catalog commands and render successful table results."""
    from .feature import Symbols

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
