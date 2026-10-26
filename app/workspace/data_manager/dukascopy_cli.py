"""CLI parsers and command execution for Data Manager Dukascopy service."""

from __future__ import annotations

import argparse
from typing import Any

from app.workspace.data_manager.dukascopy import Dukascopy


def register_dukascopy_commands(resources: Any) -> None:
    """Register Dukascopy dataset management and ingestion CLI subcommands."""
    duk = resources.add_parser(
        "dukascopy",
        help="Manage Dukascopy catalog, disclaimers, and market data downloads",
    )
    commands = duk.add_subparsers(dest="dukascopy_command", required=True)

    # Disclaimer
    commands.add_parser(
        "disclaimer", help="Display Dukascopy data disclaimer and licensing terms"
    )

    # Catalog
    cat_cmd = commands.add_parser(
        "catalog", help="List available Dukascopy symbols and categories"
    )
    cat_cmd.add_argument("--category", default=None, help="Filter by category")
    cat_cmd.add_argument("--search", default=None, help="Filter by symbol or name")

    # Add symbols
    add_cmd = commands.add_parser(
        "add", help="Add Dukascopy symbols to local datasets catalog"
    )
    add_cmd.add_argument(
        "symbols", nargs="+", help="Symbol name(s) (e.g. EURUSD GBPUSD)"
    )
    add_cmd.add_argument(
        "--data-type",
        choices=["M1", "TICK", "m1", "tick"],
        default="M1",
        help="Dataset timeframe: M1 or TICK (default: M1)",
    )
    add_cmd.add_argument(
        "--broker", default="default", help="Broker profile ID (default: default)"
    )
    add_cmd.add_argument(
        "--postfix", default="", help="Optional symbol postfix (e.g. _demo)"
    )
    add_cmd.add_argument(
        "--no-disclaimer",
        action="store_true",
        help="Reject disclaimer (will cause command to fail)",
    )

    # Download data
    down_cmd = commands.add_parser(
        "download", help="Download historical bars or ticks to partitioned Parquet"
    )
    down_cmd.add_argument("symbol", help="Target symbol to download (e.g. EURUSD)")
    down_cmd.add_argument(
        "--timeframe",
        choices=["M1", "TICK", "m1", "tick"],
        default="M1",
        help="Data resolution (default: M1)",
    )
    down_cmd.add_argument(
        "--from",
        "--date-from",
        dest="date_from",
        default=None,
        help="Start date (YYYY-MM-DD)",
    )
    down_cmd.add_argument(
        "--to",
        "--date-to",
        dest="date_to",
        default=None,
        help="End date (YYYY-MM-DD)",
    )
    down_cmd.add_argument(
        "--underlying",
        default=None,
        help="Underlying catalogue symbol if using custom symbol name",
    )
    down_cmd.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing Parquet partitions instead of merging",
    )
    down_cmd.add_argument(
        "--count",
        type=int,
        default=None,
        help="Maximum bar/tick count to download (default: all)",
    )


def _execute_add(service: Dukascopy, args: argparse.Namespace) -> dict[str, Any]:
    confirmed = not getattr(args, "no_disclaimer", False)
    return service.add(
        symbols=args.symbols,
        data_type=args.data_type,
        broker=args.broker,
        postfix=args.postfix,
        disclaimer_confirmed=confirmed,
    )


def _execute_download(service: Dukascopy, args: argparse.Namespace) -> dict[str, Any]:
    return service.download(
        symbol=args.symbol,
        timeframe=args.timeframe,
        date_from=args.date_from,
        date_to=args.date_to,
        underlying=args.underlying,
        overwrite=args.overwrite,
        count=args.count,
    )


def _execute_catalog(service: Dukascopy, args: argparse.Namespace) -> dict[str, Any]:
    return service.get_catalog(category=args.category, search=args.search)


def run_dukascopy_command(
    arguments: argparse.Namespace, parser: argparse.ArgumentParser
) -> dict[str, Any]:
    """Execute Dukascopy subcommand and return standard response payload."""
    del parser
    service = Dukascopy()
    command = arguments.dukascopy_command
    dispatch = {
        "disclaimer": service.disclaimer,
        "catalog": lambda: _execute_catalog(service, arguments),
        "add": lambda: _execute_add(service, arguments),
        "download": lambda: _execute_download(service, arguments),
    }
    action = dispatch.get(command)
    if action is None:
        return {"success": False, "message": f"Unknown dukascopy command: {command}"}
    return action()
