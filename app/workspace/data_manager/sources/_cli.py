"""CLI commands for Data Manager historical sources and Dukascopy."""

from __future__ import annotations

import argparse
import asyncio
import sys
from collections.abc import Callable
from typing import Any, cast

from ._base import Sources
from ._helpers import PROVIDERS, capabilities
from .dukascopy import Dukascopy

__all__ = [
    "register_dukascopy_commands",
    "register_source_commands",
    "run_dukascopy_command",
    "run_source_command",
]


def _get_dukascopy_service() -> Any:
    cli_mod = sys.modules.get("app.workspace.data_manager.sources._cli")
    if cli_mod and getattr(cli_mod, "Dukascopy", Dukascopy) is not Dukascopy:
        return cli_mod.Dukascopy()
    mod = sys.modules.get("app.workspace.data_manager.sources")
    cls = getattr(mod, "Dukascopy", Dukascopy) if mod else Dukascopy
    return cls()


def _get_sources_service() -> Any:
    cli_mod = sys.modules.get("app.workspace.data_manager.sources._cli")
    if cli_mod and getattr(cli_mod, "Sources", Sources) is not Sources:
        return cli_mod.Sources()
    mod = sys.modules.get("app.workspace.data_manager.sources")
    cls = getattr(mod, "Sources", Sources) if mod else Sources
    return cls()


# --- Dukascopy CLI ---


def register_dukascopy_commands(resources: Any) -> None:
    """Register Dukascopy dataset management and ingestion CLI subcommands."""
    duk = resources.add_parser(
        "dukascopy",
        help="Manage Dukascopy catalog, disclaimers, and market data downloads",
    )
    commands = duk.add_subparsers(dest="dukascopy_command", required=True)

    commands.add_parser(
        "disclaimer", help="Display Dukascopy data disclaimer and licensing terms"
    )

    cat_cmd = commands.add_parser(
        "catalog", help="List available Dukascopy symbols and categories"
    )
    cat_cmd.add_argument("--category", default=None, help="Filter by category")
    cat_cmd.add_argument("--search", default=None, help="Filter by symbol or name")

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

    down_cmd = commands.add_parser(
        "download", help="Download historical bars or ticks to partitioned Parquet"
    )
    down_cmd.add_argument(
        "--download-type",
        choices=["standard", "cdn"],
        default="cdn",
        help="Select direct datafeed or CDN with direct fallback",
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
    modes = down_cmd.add_mutually_exclusive_group()
    modes.add_argument(
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

    modes.add_argument(
        "--missing-only",
        dest="overwrite",
        action="store_false",
        help="Fetch only missing history (default)",
    )
    down_cmd.set_defaults(overwrite=False)


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
        download_type=args.download_type,
    )


def _execute_catalog(service: Dukascopy, args: argparse.Namespace) -> dict[str, Any]:
    return service.get_catalog(category=args.category, search=args.search)


def run_dukascopy_command(
    arguments: argparse.Namespace, parser: argparse.ArgumentParser
) -> dict[str, Any]:
    """Execute Dukascopy subcommand and return standard response payload."""
    del parser
    service = _get_dukascopy_service()
    command = arguments.dukascopy_command
    dispatch: dict[str, Callable[[], dict[str, Any]]] = {
        "disclaimer": service.disclaimer,
        "catalog": lambda: _execute_catalog(service, arguments),
        "add": lambda: _execute_add(service, arguments),
        "download": lambda: _execute_download(service, arguments),
    }
    action = dispatch.get(command)
    if action is None:
        return {"success": False, "message": f"Unknown dukascopy command: {command}"}
    return action()


# --- Broker Sources CLI ---


def register_source_commands(resources: Any) -> None:
    """Register one consistent CLI for each independent source or crypto market."""
    for provider in PROVIDERS:
        parser = resources.add_parser(
            provider, help=f"Manage {provider} historical data"
        )
        commands = parser.add_subparsers(dest="source_command", required=True)
        commands.add_parser("capabilities", help="Show native supported resolutions")
        commands.add_parser("list", help="List persisted datasets")
        add = commands.add_parser("add", help="Register datasets in SQLite")
        add.add_argument("symbols", nargs="+")
        add.add_argument("--postfix", default="")
        add.add_argument(
            "--timeframe",
            choices=capabilities(provider)["timeframes"],
            default=capabilities(provider)["default_timeframe"],
        )
        add.add_argument(
            "--tick-size",
            type=float,
            default=1e-8,
            help="Integer price storage unit (default: 1e-8)",
        )
        add.add_argument("--broker", default="SQ default")
        download = commands.add_parser(
            "download", help="Fetch real data and publish Parquet/catalog updates"
        )
        download.add_argument(
            "symbol", help="Registered dataset symbol, including postfix"
        )
        download.add_argument(
            "--timeframe", default=capabilities(provider)["default_timeframe"]
        )
        download.add_argument("--from", dest="date_from", required=True)
        download.add_argument("--to", dest="date_to", required=True)
        modes = download.add_mutually_exclusive_group()
        modes.add_argument("--overwrite", action="store_true")
        modes.add_argument(
            "--missing-only",
            dest="overwrite",
            action="store_false",
            help="Fetch only missing history (default)",
        )
        download.set_defaults(overwrite=False)
        if provider == "mt5":
            download.add_argument(
                "--wait-seconds",
                type=float,
                default=30,
                help="Wait for the EA using MT5_BRIDGE_* environment settings",
            )


def run_source_command(arguments: argparse.Namespace, parser: Any) -> dict[str, Any]:
    """Execute a source command with the same service used by backend jobs."""
    del parser
    service = _get_sources_service()
    provider = arguments.resource
    try:
        if arguments.source_command == "capabilities":
            return {"success": True, "data": capabilities(provider)}
        if arguments.source_command == "list":
            return cast(
                "dict[str, Any]",
                service.gateway.read_records(
                    "datamgr_datasets", filters={"source": provider}, limit=1000
                ),
            )
        if arguments.source_command == "add":
            return cast(
                "dict[str, Any]",
                service.add(
                    provider,
                    [
                        {
                            "symbol": symbol + arguments.postfix,
                            "underlying": symbol,
                            "timeframe": arguments.timeframe,
                            "tick_size": arguments.tick_size,
                            "broker": arguments.broker,
                        }
                        for symbol in arguments.symbols
                    ],
                ),
            )
        if provider == "mt5":
            return asyncio.run(_mt5_download(service, arguments))
        return cast(
            "dict[str, Any]",
            service.download(
                f"{provider}:{arguments.symbol.upper()}:{arguments.timeframe.upper()}",
                arguments.date_from,
                arguments.date_to,
                overwrite=arguments.overwrite,
            ),
        )
    except (ValueError, RuntimeError, OSError, TimeoutError) as error:
        return {
            "success": False,
            "error": {"code": "download_failed", "message": str(error)},
        }


async def _mt5_download(
    service: Sources, arguments: argparse.Namespace
) -> dict[str, Any]:
    from app.workspace.brokers.metatrader import create_mt5_client
    from app.workspace.data_manager.data.coverage import missing_ranges

    dataset_id = f"mt5:{arguments.symbol.upper()}:{arguments.timeframe.upper()}"
    row = service.record(dataset_id)
    lower = Dukascopy.parse_date_bound(arguments.date_from)
    upper = Dukascopy.parse_date_bound(arguments.date_to, is_end=True)
    if lower is None or upper is None or lower > upper:
        raise ValueError("Choose a valid date range")
    if not missing_ranges(row, lower, upper, overwrite=arguments.overwrite):
        return service.download(dataset_id, lower, upper, overwrite=False)
    client = create_mt5_client()
    async with client:
        await client.wait_connected(timeout=arguments.wait_seconds)
        service.client_factory = lambda _: client
        return await asyncio.to_thread(
            service.download,
            f"mt5:{arguments.symbol.upper()}:{arguments.timeframe.upper()}",
            arguments.date_from,
            arguments.date_to,
            overwrite=arguments.overwrite,
        )
