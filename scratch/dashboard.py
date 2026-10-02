"""
StrategyQuant X Data Manager Terminal Dashboard
Unified Catalog Dashboard for `scripts/haruquantai.db` (`DATA` and `INSTRUMENTS` tables)

Matches StrategyQuant X GUI Data Manager Layout:
Columns: Symbol Name, Instrument, Broker profile, Underlying Symbol, Timeframe,
         Timezone, Date from, Date to, Total Days, Total Records, Source, Bar Type, Data Type.
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Unified SQLite Database Path (exact SQX user/data/data.db parity)
UNIFIED_DB_PATH = Path(__file__).resolve().parent / "haruquantai.db"

# Source ID mappings from StrategyQuant X
SOURCE_MAP = {
    1: "File Import",
    2: "Dukascopy",
    3: "SQ Equity",
    4: "SQ Futures",
    5: "History",
    6: "Darwinex",
    7: "Crypto",
    8: "Yahoo",
    9: "MT5",
    10: "TickDownloader",
}

SOURCE_NAME_TO_ID = {
    "file_import": 1,
    "files": 1,
    "dukascopy": 2,
    "sq_equity": 3,
    "sq_futures": 4,
    "history": 5,
    "darwinex": 6,
    "crypto": 7,
    "yahoo": 8,
    "mt5": 9,
    "tick_downloader": 10,
    "tick_downloader_import": 10,
}

DATATYPE_MAP = {
    1: "Forex",
    2: "Futures",
    3: "Stock/ETF",
    4: "Index",
    5: "Commodity",
    6: "Metals",
    7: "Crypto",
    8: "CFD",
}


def get_source_display(source_val: Union[int, str]) -> str:
    """Returns canonical display name of data source."""
    if isinstance(source_val, int):
        return SOURCE_MAP.get(source_val, str(source_val))
    s = str(source_val).lower().strip()
    sid = SOURCE_NAME_TO_ID.get(s)
    if sid:
        return SOURCE_MAP.get(sid, s.capitalize())
    return s.capitalize()


def get_datatype_display(datatype_val: Union[int, str], symbol: str = "") -> str:
    """Classifies asset class / data type matching SQX Data Manager."""
    if isinstance(datatype_val, int):
        return DATATYPE_MAP.get(datatype_val, str(datatype_val))
    s = symbol.upper()
    src = str(datatype_val).lower()
    if src == "crypto":
        return "Crypto"
    if src in ("sq_equity", "yahoo"):
        return "Stock/ETF"
    if src == "sq_futures":
        return "Futures"
    if src == "darwinex":
        return "Forex/CFD"
    if any(metal in s for metal in ("XAU", "XAG", "GOLD", "SILVER")):
        return "Metals"
    return "Forex"


def format_ms_date(ms: Optional[int], is_daily: bool = False) -> str:
    """Formats millisecond epoch timestamp to date string."""
    if not ms or ms <= 0:
        return ""
    try:
        dt = datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc)
        if is_daily:
            return dt.strftime("%Y-%m-%d")
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return ""


def calc_days_ms(dfrom: Optional[int], dto: Optional[int]) -> int:
    """Calculates elapsed calendar days from timestamps."""
    if not dfrom or not dto or dto <= dfrom:
        return 0
    try:
        dt1 = datetime.fromtimestamp(dfrom / 1000.0, tz=timezone.utc)
        dt2 = datetime.fromtimestamp(dto / 1000.0, tz=timezone.utc)
        return max(0, (dt2 - dt1).days) + 1
    except Exception:
        return 0


def fetch_dashboard_rows(
    db_path: Union[str, Path] = UNIFIED_DB_PATH,
    source: Optional[str] = None,
    symbol: Optional[str] = None,
    timeframe: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Queries `DATA` table in `scripts/haruquantai.db` with exact SQX Data Manager parity.
    Exact StrategyQuant X Data Manager layout.
    """
    resolved_db = Path(db_path)
    if not resolved_db.exists():
        return []

    with sqlite3.connect(str(resolved_db)) as conn:
        cur = conn.cursor()
        # Check if SQX DATA table exists
        cur.execute(
            "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='DATA'"
        )
        has_sqx_data = cur.fetchone()[0] > 0

        if not has_sqx_data:
            return []

        query = """
        SELECT
            d.ID,
            d.SYMBOL,
            d.INSTRUMENT,
            b.NAME as BROKER_NAME,
            d.BROKER_ID,
            d.USYMBOL,
            d.TIMEFRAME,
            d.TIMEZONE,
            d.DATEFROM,
            d.DATETO,
            d.ROWS,
            d.SOURCE,
            d.DATATYPE,
            d.SHOW
        FROM DATA d
        LEFT JOIN BROKER b ON d.BROKER_ID = b.ID
        WHERE 1=1
        """
        params: List[Any] = []

        if source and source.lower() not in ("all", "*"):
            src_norm = source.lower().strip()
            src_id = SOURCE_NAME_TO_ID.get(src_norm)
            if src_id is not None:
                query += " AND (d.SOURCE = ? OR LOWER(d.SYMBOL) LIKE ?)"
                params.extend([src_id, f"%{src_norm}%"])
            else:
                query += " AND LOWER(d.SYMBOL) LIKE ?"
                params.append(f"%{src_norm}%")

        if symbol:
            sym_clean = symbol.strip().upper()
            query += " AND (UPPER(d.SYMBOL) LIKE ? OR UPPER(d.USYMBOL) = ?)"
            params.extend([f"%{sym_clean}%", sym_clean])

        if timeframe:
            tf_clean = timeframe.strip().upper()
            query += " AND UPPER(d.TIMEFRAME) = ?"
            params.append(tf_clean)

        query += " ORDER BY d.ID ASC"
        cur.execute(query, params)
        raw_rows = cur.fetchall()

    results: List[Dict[str, Any]] = []
    for r in raw_rows:
        (
            _id,
            sym,
            inst,
            broker_name,
            broker_id,
            usym,
            tf,
            tz,
            dfrom,
            dto,
            rows_cnt,
            src,
            dtype,
            show,
        ) = r

        # Broker Profile: e.g. [[Dukascopy]], SQ default
        if broker_name:
            broker_disp = broker_name
        elif broker_id == -1:
            broker_disp = "SQ default"
        else:
            broker_disp = f"[[Broker {broker_id}]]"

        tf_disp = tf or "M1"
        is_daily = tf_disp.upper() == "D1"
        d_from_str = format_ms_date(dfrom, is_daily)
        d_to_str = format_ms_date(dto, is_daily)
        days = calc_days_ms(dfrom, dto)
        recs = rows_cnt if rows_cnt is not None else 0
        source_disp = get_source_display(src)
        data_type_disp = get_datatype_display(dtype, sym or "")
        bar_type = "Start of bar"

        results.append(
            {
                "Symbol Name": sym or "",
                "Instrument": inst or sym or "",
                "Broker profile": broker_disp,
                "Underlying Symbol": usym or "",
                "Timeframe": tf_disp,
                "Timezone": tz or "",
                "Date from": d_from_str,
                "Date to": d_to_str,
                "Total Days": days,
                "Total Records": recs,
                "Source": source_disp,
                "Bar Type": bar_type,
                "Data Type": data_type_disp,
            }
        )

    return results


def render_dashboard(
    source: Optional[str] = None,
    symbol: Optional[str] = None,
    timeframe: Optional[str] = None,
    all_sources: bool = False,
    db_path: Union[str, Path] = UNIFIED_DB_PATH,
) -> None:
    """
    Renders the StrategyQuant X Data Manager Dashboard in the console.
    Matches the exact 13 columns and visual styling of SQX GUI.
    """
    effective_source = (
        None
        if (all_sources or not source or source.lower() in ("all", "*"))
        else source
    )
    rows = fetch_dashboard_rows(
        db_path=db_path, source=effective_source, symbol=symbol, timeframe=timeframe
    )

    # Fallback to all sources if 0 records found for a specific source
    fallback_used = False
    if not rows and effective_source:
        all_rows = fetch_dashboard_rows(
            db_path=db_path, source=None, symbol=symbol, timeframe=timeframe
        )
        if all_rows:
            fallback_used = True
            rows = all_rows

    headers = [
        "Symbol Name",
        "Instrument",
        "Broker profile",
        "Underlying Symbol",
        "Timeframe",
        "Timezone",
        "Date from",
        "Date to",
        "Total Days",
        "Total Records",
        "Source",
        "Bar Type",
        "Data Type",
    ]

    # Convert records for formatting
    display_rows: List[List[str]] = []
    total_records_sum = 0
    total_days_sum = 0

    for r in rows:
        total_records_sum += r["Total Records"]
        total_days_sum += r["Total Days"]
        display_rows.append(
            [
                r["Symbol Name"],
                r["Instrument"],
                r["Broker profile"],
                r["Underlying Symbol"],
                r["Timeframe"],
                r["Timezone"],
                r["Date from"],
                r["Date to"],
                f"{r['Total Days']:,}",
                f"{r['Total Records']:,}",
                r["Source"],
                r["Bar Type"],
                r["Data Type"],
            ]
        )

    # Width calculations
    widths = [len(h) for h in headers]
    for drow in display_rows:
        for i, val in enumerate(drow):
            widths[i] = max(widths[i], len(val))

    # Banner Header
    print("\n" + "=" * 132)
    print(" StrategyQuant X - Data Manager (Unified Database: scripts/haruquantai.db)")
    print("=" * 132)
    print(
        " Data sources: [Dukascopy] [TickDownloader] [File Import] [SQ Equity] [SQ Futures] [Darwinex] [Crypto] [Yahoo] [MT5]"
    )
    print("-" * 132)

    active_source_label = (
        get_source_display(effective_source)
        if (effective_source and not fallback_used)
        else "All Data Sources"
    )
    print(
        f" View: Data Manager  |  Filter: Source = {active_source_label}  |  Records: {len(display_rows)}  |  Table: DATA"
    )

    if fallback_used and effective_source:
        print(
            f" [Note] No local partitions found for '{effective_source}'. Showing all {len(display_rows)} dataset(s) across catalog."
        )

    print("-" * 132)

    # Print Table Header
    header_line = " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
    sep_line = "-+-".join("-" * widths[i] for i in range(len(headers)))
    print(header_line)
    print(sep_line)

    if not display_rows:
        print(" (No datasets registered in scripts/haruquantai.db)")
    else:
        for drow in display_rows:
            formatted_cells = []
            for i, val in enumerate(drow):
                # Right-align numeric columns
                if headers[i] in ("Total Days", "Total Records"):
                    formatted_cells.append(val.rjust(widths[i]))
                else:
                    formatted_cells.append(val.ljust(widths[i]))
            print(" | ".join(formatted_cells))

    print("-" * 132)
    print(
        f" Summary: {len(display_rows):,} dataset(s) | {total_days_sum:,} total days | {total_records_sum:,} total bars/records"
    )
    print("=" * 132 + "\n")


def dashboard(
    source: Optional[str] = None,
    symbol: Optional[str] = None,
    timeframe: Optional[str] = None,
    all_sources: bool = False,
    db_path: Union[str, Path] = UNIFIED_DB_PATH,
) -> None:
    """Primary dashboard entrypoint matching SQX Data Manager specification."""
    render_dashboard(
        source=source,
        symbol=symbol,
        timeframe=timeframe,
        all_sources=all_sources,
        db_path=db_path,
    )


# CLI Execution
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="StrategyQuant X Unified Data Manager Terminal Dashboard"
    )
    parser.add_argument(
        "--source",
        "-s",
        default=None,
        help="Filter by data source (e.g. dukascopy, crypto, darwinex)",
    )
    parser.add_argument(
        "--symbol", default=None, help="Filter by symbol (e.g. EURUSD, BTCUSDT, AAPL)"
    )
    parser.add_argument(
        "--timeframe",
        "-tf",
        default=None,
        help="Filter by timeframe (e.g. M1, Tick, D1)",
    )
    parser.add_argument(
        "--all", "-a", action="store_true", help="Display all data sources"
    )
    parser.add_argument(
        "--db", default=UNIFIED_DB_PATH, help="Path to unified SQLite database"
    )

    args = parser.parse_args()
    dashboard(
        source=args.source,
        symbol=args.symbol,
        timeframe=args.timeframe,
        all_sources=args.all,
        db_path=args.db,
    )
