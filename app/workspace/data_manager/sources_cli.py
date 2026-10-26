"""Headless registration and historical download commands for broker sources."""

from __future__ import annotations

import argparse
import asyncio
from typing import Any

from app.workspace.data_manager.sources import PROVIDERS, Sources, capabilities


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
    service = Sources()
    provider = arguments.resource
    try:
        if arguments.source_command == "capabilities":
            return {"success": True, "data": capabilities(provider)}
        if arguments.source_command == "list":
            return service.gateway.read_records(
                "datamgr_datasets", filters={"source": provider}, limit=1000
            )
        if arguments.source_command == "add":
            return service.add(
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
            )
        if provider == "mt5":
            return asyncio.run(_mt5_download(service, arguments))
        return service.download(
            f"{provider}:{arguments.symbol.upper()}:{arguments.timeframe.upper()}",
            arguments.date_from,
            arguments.date_to,
            overwrite=arguments.overwrite,
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
    from app.workspace.data_manager.coverage import missing_ranges
    from app.workspace.data_manager.dukascopy import Dukascopy

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
