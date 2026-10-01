"""Authenticated Data Manager command client.

Description:
    Maps Data Manager CLI options to published workspace and provider operations.
    The running host owns authentication, catalogs, jobs and durable market data.
    Export destinations are local client files; no backend implementation is loaded.
Purpose:
    FEAT-DM-CLI: Script access to the same host operations as the UI.
Key Capabilities:
    - FR-DM-CLI-ROUTES: Explicit published routes; logs each operation.
    - FR-DM-CLI-EXPORT: Atomic client exports; logs destination completion.
    - FR-DM-CLI-ISOLATION: Missing providers fail explicitly; unrelated reads survive.
Python API Usage:
    main(["--data"])
CLI Usage:
    uv run python scripts/data_manager_cli.py --data --url http://127.0.0.1:8000
    uv run python scripts/data_manager_cli.py download GBPUSD GBPUSD --start-date
    2024-01-15 --end-date 2024-01-15
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import os
import re
import sys
import time
import zipfile
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

if __name__ == "__main__" and not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.cli import Client, ClientError
from app.host.logging import close_host_logging, configure_boot_logging, get_logger

logger = get_logger(__name__)


def _client(url: str, username: str) -> Client:
    """Authenticate against the explicitly selected running host."""
    client = Client(url)
    client.initialize(
        username, os.environ.get("HARU_CLIENT_PASSWORD"), output=sys.stderr
    )
    return client


def _invoke(client: Client, operation: str, values: dict[str, Any]) -> Any:
    """Invoke an operation on the DataManager public contribution boundary."""
    logger.info("Data Manager CLI invoking %s", operation)
    return client.request("/contributions/workspace.data_manager/" + operation, values)


def _provider(args: argparse.Namespace) -> str:
    """Validate a provider namespace without importing its implementation."""
    source = getattr(args, "source", None) or "dukascopy"
    if not re.fullmatch(r"[a-z][a-z0-9_]{0,39}", source):
        raise ClientError("Invalid provider name")
    return "sources." + source + "."


def _atomic_output(path: Path, content: bytes) -> None:
    """Replace a client output only after complete bytes are safely written."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
        logger.info("Data Manager CLI export completed: bytes=%d", len(content))
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _definitions(client: Client, args: argparse.Namespace) -> Any:
    """Resolve the actual broker and publish definitions through the owner route."""
    prefix = _provider(args)
    catalog = _invoke(client, prefix + "catalog", {})
    profile = str(args.broker_profile).casefold()
    brokers = [
        row
        for row in catalog["brokers"]
        if str(row["id"]).casefold() == profile or row["name"].casefold() == profile
    ]
    if len(brokers) != 1:
        raise ClientError("Select an available unique broker profile")
    broker = brokers[0]
    postfix = args.postfix if args.postfix is not None else broker["postfix"]
    symbol = args.add_symbol.upper()
    if postfix and symbol.casefold().endswith(postfix.casefold()):
        symbol = symbol[: -len(postfix)]
    return _invoke(
        client,
        prefix + "definitions.add",
        {
            "symbols": [symbol],
            "kind": "m1" if args.data_type.upper() == "M1" else "ticks",
            "broker": str(broker["id"]),
            "postfix": postfix,
            "instruments": [args.instrument or symbol],
        },
    )


def _download(client: Client, args: argparse.Namespace) -> Any:
    """Resolve an exact definition, submit a bounded job and wait for its outcome."""
    prefix = _provider(args)
    symbol = getattr(args, "import_symbol", None) or args.symbol
    kind = getattr(args, "timeframe", None) or args.data_type
    catalog = _invoke(client, prefix + "catalog", {})
    matches = [
        row
        for row in catalog["datasets"]
        if symbol.casefold()
        in (row["symbol"].casefold(), row.get("underlying", "").casefold())
        and row["timeframe"].upper() == kind.upper()
    ]
    if len(matches) != 1:
        raise ClientError("Select an existing unique dataset; use --add-symbol first")
    if not args.start_date or not args.end_date:
        raise ClientError("Download requires --start-date and --end-date")
    mode = "standard"
    if getattr(args, "sq_cdn_cn", False):
        mode = "cdn-cn"
    elif getattr(args, "sq_cdn_true", False):
        mode = "cdn"
    elif getattr(args, "import_symbol", None):
        mode = {"sqx-cdn": "cdn", "sqx-cdn-cn": "cdn-cn", "standard": "standard"}[
            args.fast_download
        ]
    started = _invoke(
        client,
        prefix + "download.start",
        {
            "dataset_id": matches[0]["id"],
            "date_from": args.start_date,
            "date_to": args.end_date,
            "overwrite": getattr(args, "overwrite", False)
            or args.redownload == "overwrite",
            "mode": mode,
        },
    )
    try:
        while True:
            status = _invoke(
                client, prefix + "download.status", {"job_id": started["job_id"]}
            )
            if status["state"] not in ("running", "queued"):
                break
            time.sleep(0.2)
    except KeyboardInterrupt:
        _invoke(client, prefix + "download.cancel", {"job_id": started["job_id"]})
        raise
    if status["state"] != "succeeded":
        raise ClientError("Provider job " + status["state"])
    return status


def dispatch(client: Client, args: argparse.Namespace) -> Any:  # noqa: PLR0911, PLR0912
    """Translate existing command options without duplicating backend algorithms."""
    if args.data:
        return _invoke(client, "actions.list_datasets", {})
    for flag, kind in (
        ("instruments", "instruments"),
        ("sessions", "sessions"),
        ("stock_groups", "groups"),
        ("broker_profiles", "brokers"),
    ):
        if getattr(args, flag):
            return _invoke(client, "catalogs.get", {"kind": kind})
    if args.log or args.clear_log:
        raise ClientError("Operational log commands have no published host operation")
    if args.disclaimer:
        return _invoke(client, _provider(args) + "disclaimer", {})
    if args.add_symbol:
        return _definitions(client, args)
    if args.import_symbol or args.subcommand == "download":
        return _download(client, args)
    command = args.subcommand
    values = {
        key: value
        for key, value in vars(args).items()
        if value is not None
        and key
        not in (
            "url",
            "username",
            "db",
            "data_dir",
            "output_path",
            "output_dir",
            "file_path",
            "subcommand",
        )
    }
    operations = {
        "delete": "actions.delete",
        "clear": "actions.delete",
        "export-csv": "actions.export_to_csv",
        "export-mt4": "actions.export_to_mt4",
        "export-mt5": "actions.export_to_mt5",
        "save-definitions": "actions.save",
        "load-definitions": "actions.load",
        "clone": "actions.clone_to_timezone",
        "clone-to-timezone": "actions.clone_to_timezone",
        "update-all": "actions.update_all",
        "update-selected": "actions.update_selected",
        "broker-data": "actions.broker_data",
        "broker-data-update": "actions.broker_data_update",
    }
    operation: str | None
    if command == "review":
        operation = (
            "actions.review_quality"
            if args.quality
            else "actions.review_chart"
            if args.chart
            else "actions.review_data"
        )
    else:
        operation = operations.get(command)
    if operation is None:
        raise ClientError("No published command selected")
    if command == "clear":
        values.update(symbols=[args.symbol], mode="clear")
    if command in ("clone", "clone-to-timezone"):
        return [
            _invoke(
                client,
                operation,
                {
                    **values,
                    "symbol": symbol,
                    "timezone": f"UTC{args.shift_hours:+d}"
                    if args.shift_hours and args.timezone == "UTC"
                    else args.timezone,
                },
            )
            for symbol in args.symbols
        ]
    if command == "load-definitions":
        with Path(args.file_path).open("rb") as stream:
            content = stream.read(1024 * 1024 + 1)
        if len(content) > 1024 * 1024:
            raise ClientError("Definition transfer exceeds client bound")
        document = json.loads(content)
        values = {
            "definitions": document["datasets"],
            "instruments": document.get("instruments", []),
        }
    if command in ("export-csv", "export-mt5"):
        values["include_header"] = not getattr(args, "no_header", False)
    result = _invoke(client, operation, values)
    if command in ("export-csv", "export-mt5", "save-definitions"):
        destination = getattr(args, "output_path", None) or getattr(
            args, "file_path", None
        )
        if destination:
            _atomic_output(Path(destination), result["content"].encode("utf-8"))
            result = {key: value for key, value in result.items() if key != "content"}
    if command == "export-mt4" and args.output_dir:
        # The host returns a standard ZIP; validate every destination before writes.
        with zipfile.ZipFile(
            io.BytesIO(base64.b64decode(result["archive_base64"], validate=True))
        ) as archive:
            destination = Path(args.output_dir).resolve()
            entries = [
                (member, (destination / member.filename).resolve())
                for member in archive.infolist()
            ]
            if any(
                member.is_dir() or not target.is_relative_to(destination)
                for member, target in entries
            ):
                raise ClientError("Invalid export archive destinations")
            for member, target in entries:
                _atomic_output(target, archive.read(member))
        result = {
            key: value for key, value in result.items() if key != "archive_base64"
        }
    return result


def build_parser() -> argparse.ArgumentParser:  # noqa: PLR0915
    """Build the argument parser for Data Manager CLI."""
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument("--url", default=argparse.SUPPRESS)
    common_parser.add_argument("--username", default=argparse.SUPPRESS)
    common_parser.add_argument(
        "--db",
        type=Path,
        default=None,
        help="Path to SQLite database (default: data/database/haruquantai.db)",
    )
    common_parser.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="Path to data directory (default: data)",
    )

    parser = argparse.ArgumentParser(
        description="HaruQuantAI Data Manager CLI - Published Host Operations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[common_parser],
    )

    # UI Tab flags
    parser.add_argument(
        "--data",
        action="store_true",
        help="[Data] Tab: Symbol catalog pre-seeded with native SQX records",
    )
    parser.add_argument(
        "--instruments",
        action="store_true",
        help="[Instruments] Tab: Point values, tick sizes, pip sizes, spreads",
    )
    parser.add_argument(
        "--sessions",
        action="store_true",
        help="[Sessions] Tab: Trading schedules (24/5 Forex, US Equities, 24/7 Crypto)",
    )
    parser.add_argument(
        "--stock-groups",
        action="store_true",
        help="[Stock groups] Tab: S&P 500, Nasdaq 100, Russell 2000, Dow Jones baskets",
    )
    parser.add_argument(
        "--broker-profiles",
        action="store_true",
        help="[Broker profiles] Tab: SQ default, Dukascopy, Darwinex",
    )
    parser.add_argument(
        "--log",
        action="store_true",
        help="[Log] Tab: Operational progress log events",
    )
    parser.add_argument(
        "--clear-log",
        action="store_true",
        help="Clear operational progress log",
    )

    # Parity options matching SQX and UI Data Manager actions
    parser.add_argument(
        "--source",
        choices=["dukascopy", "tickdownloader", "file"],
        help="Specify data source context (e.g. dukascopy)",
    )
    parser.add_argument(
        "--add-symbol",
        dest="add_symbol",
        help="Add new symbol for the specified data source (e.g. EURUSD)",
    )
    parser.add_argument(
        "--import",
        dest="import_symbol",
        help="Download/import historical data (e.g. EURUSD_dukascopy)",
    )
    parser.add_argument(
        "--disclaimer",
        action="store_true",
        help="Display official data disclaimer for the specified source",
    )
    parser.add_argument(
        "--data-type",
        dest="data_type",
        choices=["M1", "TICK", "m1", "tick"],
        default="M1",
        help="Data type for symbol addition (default: M1)",
    )
    parser.add_argument(
        "--broker-profile",
        dest="broker_profile",
        default="dukascopy",
        help="Broker profile to assign (default: dukascopy)",
    )
    parser.add_argument(
        "--instrument",
        dest="instrument",
        help="Target instrument mapping (defaults to underlying symbol)",
    )
    parser.add_argument(
        "--postfix",
        dest="postfix",
        help="Data postfix (default: broker postfix or _dukascopy)",
    )
    parser.add_argument(
        "--start-date",
        dest="start_date",
        help="Start date for import (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--end-date",
        dest="end_date",
        help="End date for import (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--redownload",
        dest="redownload",
        choices=["missing", "overwrite"],
        default="missing",
        help="Redownload policy: 'missing' (add only missing) or 'overwrite'",
    )
    parser.add_argument(
        "--fast-download",
        dest="fast_download",
        choices=["sqx-cdn", "sqx-cdn-cn", "standard"],
        default="sqx-cdn",
        help="Fast download source: 'sqx-cdn', 'sqx-cdn-cn', or 'standard'",
    )

    subparsers = parser.add_subparsers(dest="subcommand", required=False)

    # download subcommand
    dl_parser = subparsers.add_parser(
        "download",
        help="Download historical bars from Dukascopy / SQ CDN",
        parents=[common_parser],
    )
    dl_parser.add_argument("symbol", help="Target symbol (e.g. GBPUSD_dukascopy)")
    dl_parser.add_argument("instrument", help="Target instrument (e.g. GBPUSD)")
    dl_parser.add_argument(
        "--start-date", required=True, help="Start date (YYYY-MM-DD)"
    )
    dl_parser.add_argument("--end-date", required=True, help="End date (YYYY-MM-DD)")
    dl_parser.add_argument(
        "--timeframe",
        choices=["M1", "TICK", "m1", "tick"],
        default="M1",
        help="Data timeframe (default: M1)",
    )
    dl_parser.add_argument(
        "--add-missing",
        action="store_true",
        default=True,
        help="Add only missing data (default: True)",
    )
    dl_parser.add_argument(
        "--overwrite", action="store_true", help="Overwrite existing data"
    )
    dl_parser.add_argument(
        "--sq-cdn-true",
        "--sq-cdn",
        dest="sq_cdn_true",
        action="store_true",
        help="Download from StrategyQuant CDN (Fast)",
    )
    dl_parser.add_argument(
        "--sq-cdn-cn",
        action="store_true",
        help="Download from StrategyQuant Hong Kong CDN (Fast)",
    )
    dl_parser.add_argument(
        "--standard",
        action="store_true",
        help="Download directly from standard Dukascopy servers",
    )

    # clone-to-timezone subcommand
    clone_parser = subparsers.add_parser(
        "clone-to-timezone",
        aliases=["clone"],
        help="Clone datasets with timezone shift and weekend removal",
        parents=[common_parser],
    )
    clone_parser.add_argument("symbols", nargs="+", help="Symbol(s) to clone")
    clone_parser.add_argument(
        "--shift-hours", type=int, default=0, help="Hour offset (e.g. 2 for +2h)"
    )
    clone_parser.add_argument(
        "--timezone", default="UTC", help="Target timezone identifier (e.g. UTC+2)"
    )
    clone_parser.add_argument(
        "--postfix",
        default="_{timeframe}_{cloneTime}",
        help="Naming template postfix (default: _{timeframe}_{cloneTime})",
    )
    clone_parser.add_argument(
        "--remove-weekends",
        action="store_true",
        help="Filter out weekend bars outside market opening",
    )

    # delete subcommand
    del_parser = subparsers.add_parser(
        "delete",
        help="Delete symbol record(s) and purge files with dependency check",
        parents=[common_parser],
    )
    del_parser.add_argument("symbols", nargs="+", help="Symbol(s) to delete")
    del_parser.add_argument(
        "--mode",
        choices=["remove", "clear"],
        default="remove",
        help="Mode: 'remove' (purge and delete definition) or 'clear' (purge files)",
    )

    # clear subcommand
    clr_parser = subparsers.add_parser(
        "clear",
        help="Clear symbol history and purge files, keeping definition",
        parents=[common_parser],
    )
    clr_parser.add_argument("symbol", help="Symbol to clear")

    # export-csv subcommand
    exp_csv_parser = subparsers.add_parser(
        "export-csv",
        help="Export dataset bars to CSV with custom timeframe and timezone",
        parents=[common_parser],
    )
    exp_csv_parser.add_argument("symbol", help="Source symbol to export")
    exp_csv_parser.add_argument(
        "--timeframe", default="M1", help="Target timeframe (e.g. M1, M5, H1, D1)"
    )
    exp_csv_parser.add_argument("--date-from", help="Start date (YYYY-MM-DD)")
    exp_csv_parser.add_argument("--date-to", help="End date (YYYY-MM-DD)")
    exp_csv_parser.add_argument(
        "--output-path", type=Path, help="Target destination CSV file path"
    )
    exp_csv_parser.add_argument(
        "--target-timezone", help="Timezone shift (e.g. +2h or Original)"
    )
    exp_csv_parser.add_argument("--header", help="Custom CSV header string")
    exp_csv_parser.add_argument(
        "--no-header", action="store_true", help="Omit column header in CSV"
    )

    # export-mt4 subcommand
    exp_mt4_parser = subparsers.add_parser(
        "export-mt4",
        help="Export dataset to MetaTrader 4 .hst and .fxt test models",
        parents=[common_parser],
    )
    exp_mt4_parser.add_argument("symbol", help="Source symbol to export")
    exp_mt4_parser.add_argument("--mt4-symbol", help="MetaTrader symbol name")
    exp_mt4_parser.add_argument(
        "--output-dir", type=Path, help="Export output directory"
    )
    exp_mt4_parser.add_argument("--timeframe", default="All", help="Timeframe or 'All'")
    exp_mt4_parser.add_argument(
        "--export-mode",
        choices=["All", "hst", "fxt"],
        default="All",
        help="Export mode ('All', 'hst', or 'fxt')",
    )
    exp_mt4_parser.add_argument("--target-timezone", help="Timezone shift (e.g. +2h)")
    exp_mt4_parser.add_argument(
        "--server-name", default="MetaQuotes-Demo", help="Broker server name for FXT"
    )
    exp_mt4_parser.add_argument(
        "--spread", type=int, default=20, help="Fixed spread in points for FXT"
    )
    exp_mt4_parser.add_argument("--date-from", help="Start date (YYYY-MM-DD)")
    exp_mt4_parser.add_argument("--date-to", help="End date (YYYY-MM-DD)")
    exp_mt4_parser.add_argument(
        "--digits", type=int, default=5, help="Price decimal digits"
    )

    # export-mt5 subcommand
    exp_mt5_parser = subparsers.add_parser(
        "export-mt5",
        help="Export dataset to MetaTrader 5 bar or tick format",
        parents=[common_parser],
    )
    exp_mt5_parser.add_argument("symbol", help="Source symbol to export")
    exp_mt5_parser.add_argument(
        "--timeframe", default="M1", help="Timeframe (e.g. M1, TICK)"
    )
    exp_mt5_parser.add_argument(
        "--output-path", type=Path, help="Destination file path"
    )
    exp_mt5_parser.add_argument(
        "--spread-mode",
        choices=["real", "fixed"],
        default="real",
        help="Spread mode ('real' or 'fixed')",
    )
    exp_mt5_parser.add_argument(
        "--spread-points",
        type=int,
        default=10,
        help="Spread points if fixed spread",
    )
    exp_mt5_parser.add_argument("--date-from", help="Start date (YYYY-MM-DD)")
    exp_mt5_parser.add_argument("--date-to", help="End date (YYYY-MM-DD)")
    exp_mt5_parser.add_argument("--target-timezone", help="Target timezone shift")

    # save-definitions subcommand
    save_parser = subparsers.add_parser(
        "save-definitions",
        help="Export and backup dataset definitions to portable JSON",
        parents=[common_parser],
    )
    save_parser.add_argument(
        "--file-path", type=Path, help="Target JSON backup file path"
    )
    save_parser.add_argument(
        "--symbols", nargs="*", help="Specific symbols to back up (default: all)"
    )

    # load-definitions subcommand
    load_parser = subparsers.add_parser(
        "load-definitions",
        help="Restore dataset definitions and metadata from JSON",
        parents=[common_parser],
    )
    load_parser.add_argument(
        "file_path", type=Path, help="Source JSON backup file to load"
    )

    # review subcommand
    review_parser = subparsers.add_parser(
        "review",
        help="Inspect dataset data table, chart candles, or data quality",
        parents=[common_parser],
    )
    review_parser.add_argument("symbol", help="Symbol to inspect")
    review_parser.add_argument(
        "--timeframe", default="M1", help="Bar timeframe (default: M1)"
    )
    review_parser.add_argument(
        "--session", default="Default", help="Trading session profile"
    )
    review_parser.add_argument(
        "--quality",
        action="store_true",
        help="Run data quality audit (gaps, spikes, leaks)",
    )
    review_parser.add_argument(
        "--chart", action="store_true", help="Retrieve OHLC candlestick chart series"
    )
    review_parser.add_argument(
        "--offset", type=int, default=0, help="Row pagination offset"
    )
    review_parser.add_argument(
        "--limit", type=int, default=50, help="Row count limit (default: 50)"
    )
    review_parser.add_argument("--date-from", help="Filter start date (YYYY-MM-DD)")
    review_parser.add_argument("--date-to", help="Filter end date (YYYY-MM-DD)")

    # update-all subcommand
    up_all_parser = subparsers.add_parser(
        "update-all",
        help="Scan and queue incremental updates for all datasets to current date",
        parents=[common_parser],
    )
    up_all_parser.add_argument(
        "--provider", default="dukascopy", help="Data provider (default: dukascopy)"
    )

    # update-selected subcommand
    up_sel_parser = subparsers.add_parser(
        "update-selected",
        help="Queue incremental updates for selected symbols to current date",
        parents=[common_parser],
    )
    up_sel_parser.add_argument("symbols", nargs="+", help="Symbols to update")
    up_sel_parser.add_argument(
        "--provider", default="dukascopy", help="Data provider (default: dukascopy)"
    )

    # broker-data subcommand
    b_data_parser = subparsers.add_parser(
        "broker-data",
        help="Query available broker instruments and trading specifications",
        parents=[common_parser],
    )
    b_data_parser.add_argument("--query", help="Filter query for symbol or description")
    b_data_parser.add_argument("--broker-id", help="Filter by broker profile ID")

    # broker-data-update subcommand
    b_up_parser = subparsers.add_parser(
        "broker-data-update",
        help="Synchronize broker properties (spreads, margins) across datasets",
        parents=[common_parser],
    )
    b_up_parser.add_argument(
        "--profile-ids", nargs="*", help="Specific broker profile IDs to sync"
    )
    b_up_parser.add_argument("--symbols", nargs="*", help="Specific symbols to sync")

    return parser


def main(argv: list[str] | None = None) -> int:
    """Run authenticated operations; preserve explicit errors and structured output."""
    parser = build_parser()
    args = parser.parse_args(argv)
    selected = args.subcommand or any(
        (
            args.data,
            args.instruments,
            args.sessions,
            args.stock_groups,
            args.broker_profiles,
            args.log,
            args.clear_log,
            args.disclaimer,
            args.add_symbol,
            args.import_symbol,
        )
    )
    if not selected:
        parser.print_help()
        return 0
    try:
        if args.db is not None or args.data_dir is not None:
            raise ClientError(
                "Database/data-directory overrides are owned by the running host"
            )
        client = _client(
            getattr(args, "url", "http://127.0.0.1:8000"),
            getattr(args, "username", "operator"),
        )
        result = dispatch(client, args)
        sys.stdout.write(json.dumps(result) + "\n")
        if isinstance(result, dict) and (
            result.get("success") is False
            or result.get("outcome") in ("empty", "partial")
        ):
            return 2
        return 0
    except (OSError, ValueError, TimeoutError) as error:
        logger.error("Data Manager CLI failed: %s", type(error).__name__)  # noqa: TRY400 -- redact transport diagnostics.
        sys.stderr.write(
            (str(error) if isinstance(error, ClientError) else type(error).__name__)
            + "\n"
        )
        return 1


if __name__ == "__main__":
    configure_boot_logging()
    try:
        sys.exit(main())
    finally:
        close_host_logging()
