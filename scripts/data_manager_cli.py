"""Data Manager Command-Line Interface.

Provides complete parity with Data Manager UI tabs and operations:
  --data             [Data] Tab: Symbol catalog pre-seeded with SQX Build 144
  --instruments      [Instruments] Tab: Point values, tick sizes, spreads, margins
  --sessions         [Sessions] Tab: Trading schedules (24/5 Forex, US Equities)
  --stock-groups     [Stock groups] Tab: S&P 500, Nasdaq 100, Russell 2000, etc.
  --broker-profiles  [Broker profiles] Tab: SQ default, Dukascopy, Darwinex, etc.
  --log              [Log] Tab: Operational progress log events
  --clear-log        Clear operational progress log

Subcommands:
  download <symbol> <instrument> --start-date <YYYY-MM-DD> --end-date <YYYY-MM-DD>
           [--timeframe <M1|TICK>] [--add-missing] [--sq-cdn-true]
  delete   <symbol>  Purge files and delete symbol definition
  clear    <symbol>  Purge files and reset history, retaining definition
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sqlite3
import sys
from contextlib import closing
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Literal

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.host.market_data import (
    MarketDataStore,
)
from app.host.network import HistoricalNetwork
from app.persistence.market import (
    clear_datamgr_log,
    clear_market_symbol,
    delete_market_symbol,
    log_datamgr_operation,
    preseed_native_sqx_datasets,
    read_datamgr_log,
)
from app.plugin.DataSource.dukascopy import (
    CDN_DISCLAIMER_TEXT,
    DUKASCOPY_DISCLAIMER_TEXT,
    RateCorrector,
    _fetch_day,
)
from app.workspace.DataManager import actions


def _workspace_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _format_table(headers: list[str], rows: list[list[str]], title: str = "") -> str:
    """Render a well-aligned ASCII table."""
    if not rows:
        return f"{title}\n(No records found)\n" if title else "(No records found)\n"

    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(widths):
                widths[i] = max(widths[i], len(str(cell)))

    divider = "+-" + "-+-".join("-" * w for w in widths) + "-+"
    header_line = (
        "| " + " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers)) + " |"
    )

    lines: list[str] = []
    if title:
        lines.append(f"=== {title} ===")
    lines.append(divider)
    lines.append(header_line)
    lines.append(divider)
    for row in rows:
        padded = [
            str(row[i] if i < len(row) else "").ljust(widths[i])
            for i in range(len(widths))
        ]
        lines.append("| " + " | ".join(padded) + " |")
    lines.append(divider)
    lines.append(f"Total: {len(rows)} records\n")
    return "\n".join(lines)


def cmd_data(db_path: Path, data_root: Path, limit: int = 50) -> int:
    """Display [Data] Tab: Symbol catalog table."""
    if not db_path.is_file():
        sys.stderr.write(f"Database not found at {db_path}\n")
        return 1

    # Pre-seed native SQX Build 144 records if empty or minimal
    preseed_native_sqx_datasets(db_path)

    store = MarketDataStore(data_root, db_path)
    datasets = store.list_datasets("dukascopy")

    headers = [
        "Symbol",
        "Underlying",
        "Instrument",
        "Timeframe",
        "Broker",
        "From",
        "To",
        "Bars",
        "Status",
    ]
    rows: list[list[str]] = []
    for ds in datasets[:limit]:
        bars = ds.get("bars", 0)
        status = "Ready" if bars > 0 else "Configured"
        rows.append(
            [
                str(ds.get("symbol", "")),
                str(ds.get("underlying", "")),
                str(ds.get("instrument", "")),
                str(ds.get("timeframe", "")),
                str(ds.get("brokerName", "Dukascopy")),
                str(ds.get("from") or "-"),
                str(ds.get("to") or "-"),
                f"{bars:,}" if bars else "0",
                status,
            ]
        )

    title = "[Data] Tab - Symbol Catalog (Native SQX Build 144 Records)"
    output = _format_table(headers, rows, title=title)
    if len(datasets) > limit:
        output += (
            f"(Showing first {limit} of {len(datasets)} records. "
            "Pass full catalog to see all.)\n"
        )
    sys.stdout.write(output + "\n")
    return 0


def cmd_instruments(db_path: Path) -> int:
    """Display [Instruments] Tab: Point values, tick sizes, spreads."""
    if not db_path.is_file():
        sys.stderr.write(f"Database not found at {db_path}\n")
        return 1

    with closing(sqlite3.connect(db_path)) as conn:
        cursor = conn.execute(
            "SELECT symbol, description, point_value, tick_size, "
            "default_spread, min_volume, max_volume, margin_rate, data_type "
            "FROM datamgr_instruments ORDER BY id ASC"
        )
        data = cursor.fetchall()

    headers = [
        "Symbol",
        "Description",
        "Point Value",
        "Tick Size",
        "Spread",
        "Min Vol",
        "Max Vol",
        "Margin",
        "Type",
    ]
    rows = [
        [
            str(r[0]),
            str(r[1] or ""),
            f"{r[2]:,.1f}" if r[2] is not None else "-",
            f"{r[3]:.5f}" if r[3] is not None else "-",
            f"{r[4]:.5f}" if r[4] is not None else "-",
            f"{r[5]:.2f}" if r[5] is not None else "-",
            f"{r[6]:.1f}" if r[6] is not None else "-",
            f"{r[7]:.2f}" if r[7] is not None else "-",
            str(r[8] or "-"),
        ]
        for r in data
    ]

    title = "[Instruments] Tab - Specifications & Pricing"
    sys.stdout.write(_format_table(headers, rows, title=title) + "\n")
    return 0


def cmd_sessions(db_path: Path) -> int:
    """Display [Sessions] Tab: Trading schedules."""
    if not db_path.is_file():
        sys.stderr.write(f"Database not found at {db_path}\n")
        return 1

    with closing(sqlite3.connect(db_path)) as conn:
        cursor = conn.execute(
            "SELECT id, name, timezone, windows_json, is_default, description "
            "FROM datamgr_sessions ORDER BY id ASC"
        )
        data = cursor.fetchall()

    headers = ["ID", "Name", "Timezone", "Default", "Schedule Windows", "Description"]
    rows: list[list[str]] = []
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for r in data:
        sched_desc = ""
        try:
            windows = json.loads(r[3] or "[]")
            if windows:
                d_indices = [w.get("day_of_week", 0) for w in windows]
                min_d = days[min(d_indices)] if d_indices else ""
                max_d = days[max(d_indices)] if d_indices else ""
                o_time = windows[0].get("open_time", "")[:5]
                c_time = windows[0].get("close_time", "")[:5]
                sched_desc = f"{min_d}-{max_d} {o_time}-{c_time}"
        except ValueError, KeyError:
            sched_desc = "Custom"
        rows.append(
            [
                str(r[0]),
                str(r[1]),
                str(r[2]),
                "Yes" if r[4] else "No",
                sched_desc,
                str(r[5] or ""),
            ]
        )

    title = "[Sessions] Tab - Trading Hours & Holidays"
    sys.stdout.write(_format_table(headers, rows, title=title) + "\n")
    return 0


def cmd_stock_groups(db_path: Path) -> int:
    """Display [Stock groups] Tab: Index equity baskets."""
    if not db_path.is_file():
        sys.stderr.write(f"Database not found at {db_path}\n")
        return 1

    with closing(sqlite3.connect(db_path)) as conn:
        cursor = conn.execute(
            "SELECT ID, NAME, SYSTEM, DESC FROM datamgr_stock_group ORDER BY ID ASC"
        )
        data = cursor.fetchall()

    headers = ["ID", "Group Name", "System Default", "Description"]
    rows = [
        [
            str(r[0]),
            str(r[1]),
            "Yes" if r[2] else "No",
            str(r[3] or "Equity Index Basket"),
        ]
        for r in data
    ]

    title = "[Stock groups] Tab - Custom Equity Groups"
    sys.stdout.write(_format_table(headers, rows, title=title) + "\n")
    return 0


def cmd_broker_profiles(db_path: Path) -> int:
    """Display [Broker profiles] Tab: Broker configurations."""
    if not db_path.is_file():
        sys.stderr.write(f"Database not found at {db_path}\n")
        return 1

    with closing(sqlite3.connect(db_path)) as conn:
        cursor = conn.execute(
            "SELECT id, name, postfix, server_timezone, mt_use, stockpicker_use, "
            "enabled FROM datamgr_broker ORDER BY id ASC"
        )
        data = cursor.fetchall()

    headers = [
        "ID",
        "Broker Name",
        "Postfix",
        "Server Timezone",
        "MT Use",
        "Stockpicker",
        "Enabled",
    ]
    rows = [
        [
            str(r[0]),
            str(r[1]),
            str(r[2] or "-"),
            str(r[3] or "UTC"),
            "Yes" if r[4] else "No",
            "Yes" if r[5] else "No",
            "Yes" if r[6] else "No",
        ]
        for r in data
    ]

    title = "[Broker profiles] Tab - Configured Profiles"
    sys.stdout.write(_format_table(headers, rows, title=title) + "\n")
    return 0


def cmd_log(db_path: Path) -> int:
    """Display [Log] Tab: Operational progress log events."""
    if not db_path.is_file():
        sys.stderr.write(f"Database not found at {db_path}\n")
        return 1

    events = read_datamgr_log(db_path)
    if not events:
        sys.stdout.write("[Log] Tab - Operational Log: (No events recorded)\n")
        return 0

    headers = ["Timestamp (UTC)", "Symbol", "Operation", "Status", "Message"]
    rows = [
        [
            e.get("timestamp", "")[:19].replace("T", " "),
            e.get("symbol", ""),
            e.get("operation", ""),
            e.get("status", ""),
            e.get("message", ""),
        ]
        for e in events
    ]

    title = "[Log] Tab - Operational Events & Progress"
    sys.stdout.write(_format_table(headers, rows, title=title) + "\n")
    return 0


def cmd_clear_log(db_path: Path) -> int:
    """Clear operational progress log."""
    if not db_path.is_file():
        sys.stderr.write(f"Database not found at {db_path}\n")
        return 1

    count = clear_datamgr_log(db_path)
    sys.stdout.write(f"Operational progress log cleared ({count} events removed).\n")
    return 0


def cmd_delete(db_path: Path, data_root: Path, symbol: str) -> int:
    """Purge files and delete symbol definition."""
    if not db_path.is_file():
        sys.stderr.write(f"Database not found at {db_path}\n")
        return 1

    success = delete_market_symbol(db_path, data_root, symbol)
    if success:
        log_datamgr_operation(
            db_path,
            symbol,
            "delete",
            "succeeded",
            f"Symbol '{symbol}' deleted and market files purged.",
        )
        sys.stdout.write(f"Symbol '{symbol}' deleted and market files purged.\n")
        return 0
    sys.stderr.write(f"Symbol '{symbol}' not found in Data Manager.\n")
    return 1


def cmd_clear(db_path: Path, data_root: Path, symbol: str) -> int:
    """Purge files and reset history, retaining definition."""
    if not db_path.is_file():
        sys.stderr.write(f"Database not found at {db_path}\n")
        return 1

    success = clear_market_symbol(db_path, data_root, symbol)
    if success:
        log_datamgr_operation(
            db_path,
            symbol,
            "clear",
            "succeeded",
            f"Symbol '{symbol}' history cleared (definition retained).",
        )
        sys.stdout.write(f"Symbol '{symbol}' history cleared (definition retained).\n")
        return 0
    sys.stderr.write(f"Symbol '{symbol}' not found in Data Manager.\n")
    return 1


def cmd_clone_to_timezone(
    args: argparse.Namespace, db_path: Path, data_root: Path
) -> int:
    """Clone symbols to a target timezone."""
    try:
        res = actions.clone_to_timezone(
            db_path,
            data_root,
            args.symbols,
            shift_hours=args.shift_hours,
            timezone_name=args.timezone,
            postfix=args.postfix,
            remove_weekends=args.remove_weekends,
        )
        sys.stdout.write(f"Successfully cloned {len(res)} dataset(s):\n")
        for r in res:
            sym = r["symbol"]
            cnt = r["records"]
            tf = r["timeframe"]
            sys.stdout.write(f"  - {sym}: {cnt} bars/ticks saved ({tf})\n")
        return 0
    except Exception as exc:
        sys.stderr.write(f"Error cloning dataset: {exc}\n")
        return 1


def cmd_delete_datasets(
    args: argparse.Namespace, db_path: Path, data_root: Path
) -> int:
    """Delete symbol definitions or purge files with dependency enforcement."""
    try:
        res = actions.delete_datasets(
            db_path, data_root, args.symbols, mode=getattr(args, "mode", "remove")
        )
        sys.stdout.write(
            f"Successfully processed {res['affected']} symbol(s) "
            f"(mode: {res['mode']}).\n"
        )
        return 0
    except Exception as exc:
        sys.stderr.write(f"Error deleting datasets: {exc}\n")
        return 1


def cmd_export_csv(args: argparse.Namespace, db_path: Path, data_root: Path) -> int:
    """Export dataset to CSV."""
    try:
        out = Path(args.output_path) if args.output_path else None
        res = actions.export_to_csv(
            db_path,
            data_root,
            args.symbol,
            timeframe=args.timeframe,
            date_from=args.date_from,
            date_to=args.date_to,
            output_path=out,
            target_timezone=args.target_timezone,
            header=args.header,
            include_header=not args.no_header,
        )
        sys.stdout.write(
            f"Successfully exported {res['records']} bars to {res['outputPath']}\n"
        )
        return 0
    except Exception as exc:
        sys.stderr.write(f"Error exporting to CSV: {exc}\n")
        return 1


def cmd_export_mt4(args: argparse.Namespace, db_path: Path, data_root: Path) -> int:
    """Export dataset to MT4 .hst and .fxt files."""
    try:
        out = Path(args.output_dir) if args.output_dir else None
        res = actions.export_to_mt4(
            db_path,
            data_root,
            args.symbol,
            mt4_symbol=args.mt4_symbol,
            date_from=args.date_from,
            date_to=args.date_to,
            output_dir=out,
            timeframe=args.timeframe,
            export_mode=args.export_mode,
            target_timezone=args.target_timezone,
            server_name=args.server_name,
            spread=args.spread,
            digits=args.digits,
        )
        sys.stdout.write("Successfully exported MT4 files:\n")
        for f in res["files"]:
            sys.stdout.write(f"  - {f}\n")
        return 0
    except Exception as exc:
        sys.stderr.write(f"Error exporting to MT4: {exc}\n")
        return 1


def cmd_export_mt5(args: argparse.Namespace, db_path: Path, data_root: Path) -> int:
    """Export dataset to MT5 format."""
    try:
        out = Path(args.output_path) if args.output_path else None
        res = actions.export_to_mt5(
            db_path,
            data_root,
            args.symbol,
            timeframe=args.timeframe,
            spread_mode=args.spread_mode,
            spread_points=args.spread_points,
            date_from=args.date_from,
            date_to=args.date_to,
            output_path=out,
            target_timezone=args.target_timezone,
        )
        sys.stdout.write(
            f"Successfully exported MT5 {res['kind']} to {res['outputPath']} "
            f"({res['records']} records)\n"
        )
        return 0
    except Exception as exc:
        sys.stderr.write(f"Error exporting to MT5: {exc}\n")
        return 1


def cmd_save_definitions(
    args: argparse.Namespace, db_path: Path, data_root: Path
) -> int:
    """Save dataset definitions and configurations to JSON."""
    try:
        out = Path(args.file_path) if args.file_path else None
        res = actions.save_definitions(
            db_path, data_root, symbols=args.symbols, file_path=out
        )
        sys.stdout.write(
            f"Backed up {res['datasetsCount']} datasets and "
            f"{res['instrumentsCount']} instruments to {res['filePath']}\n"
        )
        return 0
    except Exception as exc:
        sys.stderr.write(f"Error saving definitions: {exc}\n")
        return 1


def cmd_load_definitions(
    args: argparse.Namespace, db_path: Path, data_root: Path
) -> int:
    """Load and restore dataset definitions from JSON."""
    try:
        res = actions.load_definitions(db_path, data_root, file_path=args.file_path)
        sys.stdout.write(
            f"Restored {res['loadedDatasets']} datasets and "
            f"{res['loadedInstruments']} instruments from {args.file_path}\n"
        )
        return 0
    except Exception as exc:
        sys.stderr.write(f"Error loading definitions: {exc}\n")
        return 1


def cmd_review(args: argparse.Namespace, db_path: Path, data_root: Path) -> int:
    """Review dataset tabular bars, chart bars, or data quality."""
    try:
        if args.quality:
            res_qual = actions.review_quality(
                db_path,
                data_root,
                args.symbol,
                timeframe=args.timeframe,
                session=args.session,
            )
            sys.stdout.write(
                f"Quality Score for {res_qual['symbol']} ({res_qual['timeframe']}): "
                f"{res_qual['qualityScore']}% (Total bars: {res_qual['totalBars']}, "
                f"Errors: {res_qual['totalErrors']})\n"
            )
            if res_qual.get("problems"):
                sys.stdout.write(f"Found {len(res_qual['problems'])} problem(s):\n")
                for p in res_qual["problems"][:10]:
                    sys.stdout.write(f"  - [{p['date']}] {p['problem']}\n")
            return 0
        if args.chart:
            res_chart = actions.review_chart(
                db_path,
                data_root,
                args.symbol,
                timeframe=args.timeframe,
                session=args.session,
                limit=args.limit,
            )
            sys.stdout.write(
                f"Retrieved {len(res_chart['chart'])} chart bars for "
                f"{res_chart['symbol']} ({res_chart['timeframe']})\n"
            )
            return 0

        res_data = actions.review_data(
            db_path,
            data_root,
            args.symbol,
            timeframe=args.timeframe,
            session=args.session,
            offset=args.offset,
            limit=args.limit,
            date_from=args.date_from,
            date_to=args.date_to,
        )
        headers = ["DateTime", "Open", "High", "Low", "Close", "Volume"]
        rows = [[str(c) for c in r] for r in res_data["rows"]]
        title = f"{res_data['symbol']} ({res_data['timeframe']}) Bar Data"
        sys.stdout.write(_format_table(headers, rows, title=title) + "\n")
        return 0
    except Exception as exc:
        sys.stderr.write(f"Error in review: {exc}\n")
        return 1


def cmd_update_all(args: argparse.Namespace, db_path: Path, data_root: Path) -> int:
    """Scan all datasets and queue updates to current date."""
    try:
        res = actions.update_all(db_path, data_root, provider=args.provider)
        sys.stdout.write(f"{res['message']}\n")
        return 0
    except Exception as exc:
        sys.stderr.write(f"Error in update-all: {exc}\n")
        return 1


def cmd_update_selected(
    args: argparse.Namespace, db_path: Path, data_root: Path
) -> int:
    """Queue incremental updates for selected symbols to current date."""
    try:
        res = actions.update_selected(
            db_path, data_root, args.symbols, provider=args.provider
        )
        sys.stdout.write(f"{res['message']}\n")
        return 0
    except Exception as exc:
        sys.stderr.write(f"Error in update-selected: {exc}\n")
        return 1


def cmd_broker_data(args: argparse.Namespace, db_path: Path) -> int:
    """Query available broker instruments and properties."""
    try:
        res = actions.broker_data(db_path, query=args.query, broker_id=args.broker_id)
        headers = [
            "Symbol",
            "Name",
            "Broker",
            "Point Value",
            "Spread",
            "Margin",
            "Digits",
        ]
        rows = [
            [
                r["symbol"],
                r["name"],
                r["brokerName"],
                str(r["pointValue"]),
                str(r["spread"]),
                str(r["marginRate"]),
                str(r["digits"]),
            ]
            for r in res
        ]
        sys.stdout.write(
            _format_table(headers, rows, title="Broker Data Instruments") + "\n"
        )
        return 0
    except Exception as exc:
        sys.stderr.write(f"Error querying broker data: {exc}\n")
        return 1


def cmd_broker_data_update(args: argparse.Namespace, db_path: Path) -> int:
    """Synchronize broker properties across datasets."""
    try:
        res = actions.broker_data_update(
            db_path, profile_ids=args.profile_ids, symbols=args.symbols
        )
        sys.stdout.write(f"{res.get('message', 'Broker data updated')}\n")
        return 0
    except Exception as exc:
        sys.stderr.write(f"Error updating broker data: {exc}\n")
        return 1


async def _run_download_async(  # noqa: PLR0915
    *,
    db_path: Path,
    data_root: Path,
    symbol: str,
    instrument: str,
    start_date_str: str,
    end_date_str: str,
    timeframe: str,
    _overwrite: bool,
    mode: Literal["standard", "cdn", "cdn-cn"],
) -> int:
    """Execute download pipeline matching clean-room Dukascopy implementation."""
    start_date = date.fromisoformat(start_date_str)
    end_date = date.fromisoformat(end_date_str)
    if start_date > end_date:
        sys.stderr.write("Start date must be before or equal to end date.\n")
        return 1

    kind: Literal["ticks", "m1"] = "m1" if timeframe.upper() == "M1" else "ticks"
    underlying = instrument or symbol.removesuffix("_dukascopy").upper()

    store = MarketDataStore(data_root, db_path)

    # Ensure dataset definition exists
    target_id: str = ""
    with closing(sqlite3.connect(db_path)) as conn, conn:
        cursor = conn.execute(
            "SELECT id FROM datamgr_datasets "
            "WHERE lower(symbol)=? OR lower(underlying)=?",
            (symbol.lower(), underlying.lower()),
        )
        row = cursor.fetchone()
        if not row:
            from uuid import uuid4

            target_id = uuid4().hex
            now_iso = datetime.now(UTC).isoformat()
            conn.execute(
                "INSERT INTO datamgr_datasets ("
                "id, source, symbol, underlying, instrument, timeframe, "
                "broker, broker_name, timezone, category, date_from, date_to, "
                "bars, created_at, updated_at"
                ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    target_id,
                    "Dukascopy",
                    symbol,
                    underlying,
                    underlying,
                    "M1" if kind == "m1" else "TICK",
                    "3",
                    "Dukascopy",
                    "UTC",
                    "Forex",
                    "",
                    "",
                    0,
                    now_iso,
                    now_iso,
                ),
            )
        else:
            target_id = str(row[0])

    dataset = store.get_dataset(target_id)

    network = HistoricalNetwork()
    from app.host.capabilities import NetworkAccess

    owner = "plugin.data_manager.dukascopy"
    net_access = NetworkAccess(owner, network)
    corrector = RateCorrector(
        min_delay_seconds=0.05, max_delay_seconds=10.0, success_threshold=100
    )

    total_days = (end_date - start_date).days + 1
    sys.stdout.write(
        f"Starting Dukascopy download for '{symbol}' ({kind.upper()})\n"
        f"Range: {start_date_str} to {end_date_str} ({total_days} days) | "
        f"Mode: {mode}\n"
    )

    published_days = 0
    missing_days = 0
    skipped_days = 0
    total_bars = 0

    from datetime import timedelta

    current = start_date
    offset = 0

    while current <= end_date:
        offset += 1
        pct = (offset / total_days) * 100.0
        # If weekend Saturday (weekday 5), skip immediately
        if current.weekday() == 5:
            skipped_days += 1
            sys.stdout.write(
                f"[{offset}/{total_days}] {current.isoformat()} ({pct:4.1f}%) "
                "- Saturday (market closed, skipped)\n"
            )
            current += timedelta(days=1)
            continue

        try:
            table = await _fetch_day(net_access, dataset, current)
            if table and table.num_rows > 0:
                day_start_dt = datetime(
                    current.year, current.month, current.day, tzinfo=UTC
                )
                start_ms = int(day_start_dt.timestamp() * 1000)
                end_ms = start_ms + (24 * 3600 * 1000) - 1
                period = (
                    f"{current.year}"
                    if kind == "m1"
                    else f"{current.year}_{current.month:02d}"
                )
                store.replace_interval(
                    source="dukascopy",
                    symbol=underlying.lower(),
                    kind=kind,
                    period=period,
                    incoming=table,
                    start_ms=start_ms,
                    end_ms=end_ms,
                    provider_mode=mode,
                )
                published_days += 1
                total_bars += table.num_rows
                corrector.record_success()
                sys.stdout.write(
                    f"[{offset}/{total_days}] {current.isoformat()} ({pct:4.1f}%) "
                    f"- Published {table.num_rows:,} {kind}\n"
                )
            else:
                missing_days += 1
                sys.stdout.write(
                    f"[{offset}/{total_days}] {current.isoformat()} ({pct:4.1f}%) "
                    "- Missing (no data returned)\n"
                )
        except Exception as exc:
            missing_days += 1
            corrector.record_failure()
            sys.stdout.write(
                f"[{offset}/{total_days}] {current.isoformat()} ({pct:4.1f}%) "
                f"- Error: {exc}\n"
            )

        if corrector.delay > 0:
            await asyncio.sleep(min(corrector.delay, 0.5))
        current += timedelta(days=1)

    # Update dataset in database
    now_iso = datetime.now(UTC).isoformat()
    with closing(sqlite3.connect(db_path)) as conn, conn:
        conn.execute(
            "UPDATE datamgr_datasets "
            "SET date_from=?, date_to=?, bars=?, updated_at=? WHERE id=?",
            (start_date_str, end_date_str, total_bars, now_iso, dataset.id),
        )

    log_msg = (
        f"Downloaded {published_days}/{total_days} days ({total_bars:,} bars) "
        f"from {start_date_str} to {end_date_str} via {mode} mode"
    )
    log_datamgr_operation(db_path, symbol, "download", "succeeded", log_msg)

    sys.stdout.write(
        f"\nDownload completed successfully!\n"
        f"  Symbol:          {symbol}\n"
        f"  Underlying:      {underlying}\n"
        f"  Timeframe:       {timeframe}\n"
        f"  Mode:            {mode}\n"
        f"  Days Published:  {published_days}\n"
        f"  Days Missing:    {missing_days}\n"
        f"  Days Skipped:    {skipped_days}\n"
        f"  Total Bars/Rows: {total_bars:,}\n"
    )
    return 0


def cmd_download(args: argparse.Namespace, db_path: Path, data_root: Path) -> int:
    """Download subcommand entrypoint."""
    symbol: str = args.symbol
    instrument: str = args.instrument
    start_date: str = args.start_date
    end_date: str = args.end_date
    timeframe: str = args.timeframe or "M1"
    overwrite: bool = bool(args.overwrite)

    mode: Literal["standard", "cdn", "cdn-cn"] = "standard"
    if getattr(args, "sq_cdn_cn", False):
        mode = "cdn-cn"
    elif getattr(args, "sq_cdn_true", False):
        mode = "cdn"

    return asyncio.run(
        _run_download_async(
            db_path=db_path,
            data_root=data_root,
            symbol=symbol,
            instrument=instrument,
            start_date_str=start_date,
            end_date_str=end_date,
            timeframe=timeframe,
            _overwrite=overwrite,
            mode=mode,
        )
    )


def cmd_disclaimer(source: str = "dukascopy") -> int:
    """Display legal data disclaimer."""
    if source.lower() == "dukascopy":
        sys.stdout.write("=== Dukascopy Bank SA Data Disclaimer ===\n\n")
        sys.stdout.write(DUKASCOPY_DISCLAIMER_TEXT + "\n\n")
        sys.stdout.write("=== StrategyQuant CDN Data Disclaimer ===\n\n")
        sys.stdout.write(CDN_DISCLAIMER_TEXT + "\n")
        return 0
    sys.stderr.write(f"Disclaimer not available for source '{source}'.\n")
    return 1


def cmd_add_symbol(
    db_path: Path,
    symbol: str,
    data_type: str,
    broker_profile: str,
    *,
    instrument: str | None = None,
    postfix: str | None = None,
) -> int:
    """Add a new symbol for the specified broker profile."""
    clean_type = "M1" if data_type.upper() in ("M1", "1M") else "TICK"
    underlying = (instrument or symbol).upper()

    broker_id = "3"
    broker_name = "Dukascopy"
    resolved_postfix = "_dukascopy"

    if Path(db_path).is_file():
        with closing(sqlite3.connect(db_path)) as conn:
            cur = conn.execute(
                "SELECT id, name, postfix FROM datamgr_broker "
                "WHERE lower(name)=? OR id=?",
                (broker_profile.lower(), broker_profile),
            )
            row = cur.fetchone()
            if row:
                broker_id = str(row[0])
                broker_name = str(row[1])
                resolved_postfix = str(row[2]) or ""

    if postfix is not None:
        resolved_postfix = postfix

    full_symbol = (
        f"{underlying}{resolved_postfix}"
        if resolved_postfix and not underlying.endswith(resolved_postfix)
        else underlying
    )

    from uuid import uuid4

    now_iso = datetime.now(UTC).isoformat()
    with closing(sqlite3.connect(db_path)) as conn, conn:
        conn.execute(
            "INSERT INTO datamgr_datasets ("
            "id, source, symbol, underlying, instrument, timeframe, "
            "broker, broker_name, timezone, category, date_from, date_to, "
            "bars, created_at, updated_at"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '', '', 0, ?, ?)",
            (
                uuid4().hex,
                "Dukascopy",
                full_symbol,
                underlying,
                underlying,
                clean_type,
                broker_id,
                broker_name,
                "UTC",
                "Forex",
                now_iso,
                now_iso,
            ),
        )
    details = (
        f"Added Dukascopy data symbol '{full_symbol}' "
        f"(Instrument: {underlying}, Type: {clean_type}, Broker: {broker_name})"
    )
    log_datamgr_operation(
        db_path,
        full_symbol,
        "add_symbol",
        "succeeded",
        details,
    )
    sys.stdout.write(f"{details}.\n")
    return 0


def cmd_import(
    args: argparse.Namespace, db_path: Path, data_root: Path, symbol: str
) -> int:
    """Download/import historical data for existing symbol matching SQX import flow."""
    if not getattr(args, "start_date", None) or not getattr(args, "end_date", None):
        sys.stderr.write("Import requires --start-date and --end-date (YYYY-MM-DD).\n")
        return 1

    mode: Literal["standard", "cdn", "cdn-cn"] = "cdn"
    fast_dl = getattr(args, "fast_download", "sqx-cdn")
    if fast_dl in ("sqx-cdn", "cdn"):
        mode = "cdn"
    elif fast_dl in ("sqx-cdn-cn", "cdn-cn"):
        mode = "cdn-cn"
    elif fast_dl == "standard":
        mode = "standard"

    overwrite = (getattr(args, "redownload", "missing") == "overwrite") or getattr(
        args, "overwrite", False
    )
    instrument = (
        getattr(args, "instrument", None) or symbol.removesuffix("_dukascopy").upper()
    )
    timeframe: str = str(
        getattr(args, "data_type", None) or getattr(args, "timeframe", "M1")
    )

    return asyncio.run(
        _run_download_async(
            db_path=db_path,
            data_root=data_root,
            symbol=symbol,
            instrument=instrument,
            start_date_str=args.start_date,
            end_date_str=args.end_date,
            timeframe=timeframe,
            _overwrite=overwrite,
            mode=mode,
        )
    )


def build_parser() -> argparse.ArgumentParser:  # noqa: PLR0915
    """Build the argument parser for Data Manager CLI."""
    common_parser = argparse.ArgumentParser(add_help=False)
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
        description="HaruQuantAI Data Manager CLI - Full UI Parity",
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


def main(argv: list[str] | None = None) -> int:  # noqa: PLR0911, PLR0912
    """CLI main execution flow."""
    parser = build_parser()
    args = parser.parse_args(argv)

    root = _workspace_root()
    db_path = args.db or root / "data" / "database" / "haruquantai.db"
    data_root = args.data_dir or root / "data"

    if args.data:
        return cmd_data(db_path, data_root)
    if args.instruments:
        return cmd_instruments(db_path)
    if args.sessions:
        return cmd_sessions(db_path)
    if args.stock_groups:
        return cmd_stock_groups(db_path)
    if args.broker_profiles:
        return cmd_broker_profiles(db_path)
    if args.log:
        return cmd_log(db_path)
    if args.clear_log:
        return cmd_clear_log(db_path)

    # Parity actions
    if args.disclaimer:
        return cmd_disclaimer(args.source or "dukascopy")
    if args.add_symbol:
        return cmd_add_symbol(
            db_path=db_path,
            symbol=args.add_symbol,
            data_type=args.data_type,
            broker_profile=args.broker_profile,
            instrument=args.instrument,
            postfix=args.postfix,
        )
    if args.import_symbol:
        return cmd_import(args, db_path, data_root, args.import_symbol)

    if args.subcommand == "download":
        return cmd_download(args, db_path, data_root)
    if args.subcommand in ("clone-to-timezone", "clone"):
        return cmd_clone_to_timezone(args, db_path, data_root)
    if args.subcommand == "delete":
        if len(args.symbols) == 1 and getattr(args, "mode", "remove") == "remove":
            return cmd_delete(db_path, data_root, args.symbols[0])
        return cmd_delete_datasets(args, db_path, data_root)
    if args.subcommand == "clear":
        return cmd_clear(db_path, data_root, args.symbol)
    if args.subcommand == "export-csv":
        return cmd_export_csv(args, db_path, data_root)
    if args.subcommand == "export-mt4":
        return cmd_export_mt4(args, db_path, data_root)
    if args.subcommand == "export-mt5":
        return cmd_export_mt5(args, db_path, data_root)
    if args.subcommand == "save-definitions":
        return cmd_save_definitions(args, db_path, data_root)
    if args.subcommand == "load-definitions":
        return cmd_load_definitions(args, db_path, data_root)
    if args.subcommand == "review":
        return cmd_review(args, db_path, data_root)
    if args.subcommand == "update-all":
        return cmd_update_all(args, db_path, data_root)
    if args.subcommand == "update-selected":
        return cmd_update_selected(args, db_path, data_root)
    if args.subcommand == "broker-data":
        return cmd_broker_data(args, db_path)
    if args.subcommand == "broker-data-update":
        return cmd_broker_data_update(args, db_path)

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
