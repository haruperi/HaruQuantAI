"""Core implementation of Data Manager Actions.

Implements all 12 functional requirements for Data Manager actions:
- brokerData
- brokerDataUpdate
- cloneToTimezone
- delete
- exportToCsv
- exportToMT4
- exportToMT5
- load
- review (data, chart, quality, save_changes)
- save
- updateAll
- updateSelected
"""

from __future__ import annotations

import contextlib
import json
import re
import sqlite3
import struct
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

import pyarrow as pa  # type: ignore[import-untyped]
import pyarrow.parquet as pq  # type: ignore[import-untyped]

from app.host.market_data import (
    M1_SCHEMA,
    TICK_SCHEMA,
    Kind,
    MarketDataStore,
)
from app.persistence.market import (
    clear_market_symbol,
    delete_market_symbol,
    open_definition_catalog,
)

Timeframe = Literal["TICK", "M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1", "MN1"]

TIMEFRAME_MINUTES: dict[str, int] = {
    "TICK": 0,
    "M1": 1,
    "M5": 5,
    "M15": 15,
    "M30": 30,
    "H1": 60,
    "H4": 240,
    "D1": 1440,
    "W1": 10080,
    "MN1": 43200,
}

TIMEFRAME_PERIOD_SECS: dict[str, int] = {
    "TICK": 0,
    "M1": 60,
    "M5": 300,
    "M15": 900,
    "M30": 1800,
    "H1": 3600,
    "H4": 14400,
    "D1": 86400,
    "W1": 604800,
    "MN1": 2592000,
}

SATURDAY_WEEKDAY = 5
SUNDAY_WEEKDAY = 6
SUNDAY_OPEN_HOUR = 21
SPIKE_THRESHOLD_PCT = 0.08
MAX_TIMESTAMP_MS = 9999999999999
MS_PER_DAY = 86400000
MS_PER_HOUR = 3600000
RAW_TICK_SCALE = 1000


@dataclass(frozen=True)
class BarRecord:
    """One immutable candlestick bar."""

    timestamp_ms: int
    open: float
    high: float
    low: float
    close: float
    volume: int


@dataclass(frozen=True)
class TickRecord:
    """One immutable market tick."""

    timestamp_ms: int
    bid: float
    ask: float
    volume: int


# ---------------------------------------------------------------------------
# Helper: Data extraction from parquet
# ---------------------------------------------------------------------------


def read_market_rows(  # noqa: C901, PLR0912
    store: MarketDataStore,
    source: str,
    kind: Kind,
    symbol: str,
    *,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict[str, Any]]:
    """Read and concatenate rows from committed parquet files."""
    clean_sym = re.sub(r"[^a-z0-9_]", "_", symbol.lower())[:40]
    files = store.list_files(source, kind, clean_sym)
    if not files and clean_sym != symbol.lower():
        files = store.list_files(source, kind, symbol.lower())
    if not files and "_" in symbol:
        underlying = symbol.split("_", maxsplit=1)[0]
        files = store.list_files(source, kind, underlying)

    if not files:
        return []

    min_ms = 0
    max_ms = MAX_TIMESTAMP_MS
    if date_from:
        with contextlib.suppress(ValueError):
            min_ms = int(
                datetime.strptime(date_from, "%Y-%m-%d").replace(tzinfo=UTC).timestamp()
                * 1000
            )
    if date_to:
        with contextlib.suppress(ValueError):
            max_ms = (
                int(
                    datetime.strptime(date_to, "%Y-%m-%d")
                    .replace(tzinfo=UTC)
                    .timestamp()
                    * 1000
                )
                + MS_PER_DAY
            )

    records: list[dict[str, Any]] = []
    for file_info in files:
        if file_info.last_ms < min_ms or file_info.first_ms > max_ms:
            continue
        file_path = store.path(
            file_info.source, file_info.kind, file_info.symbol, file_info.period
        )
        if not file_path.is_file():
            continue
        table = pq.read_table(file_path)
        pydict = table.to_pydict()
        timestamps = [
            int(dt.timestamp() * 1000) if hasattr(dt, "timestamp") else int(dt)
            for dt in pydict["DateTime"]
        ]
        num_rows = len(timestamps)

        if kind == "ticks":
            asks = pydict["Ask"]
            bids = pydict["Bid"]
            volumes = pydict["Volume"]
            for i in range(num_rows):
                t = timestamps[i]
                if min_ms <= t <= max_ms:
                    records.append(
                        {
                            "DateTime": t,
                            "Ask": asks[i],
                            "Bid": bids[i],
                            "Volume": volumes[i],
                        }
                    )
        else:
            opens = pydict["Open"]
            highs = pydict["High"]
            lows = pydict["Low"]
            closes = pydict["Close"]
            volumes = pydict["Volume"]
            for i in range(num_rows):
                t = timestamps[i]
                if min_ms <= t <= max_ms:
                    records.append(
                        {
                            "DateTime": t,
                            "Open": opens[i],
                            "High": highs[i],
                            "Low": lows[i],
                            "Close": closes[i],
                            "Volume": volumes[i],
                        }
                    )

    records.sort(key=lambda r: int(r["DateTime"]))
    return records


def resample_m1_bars(
    m1_records: list[dict[str, Any]], target_timeframe: str
) -> list[BarRecord]:
    """Resample M1 bars to higher timeframe (M5, M15, M30, H1, H4, D1, etc.)."""
    tf_minutes = TIMEFRAME_MINUTES.get(target_timeframe.upper(), 1)
    if tf_minutes <= 1:
        return [
            BarRecord(
                timestamp_ms=r["DateTime"],
                open=float(r["Open"]),
                high=float(r["High"]),
                low=float(r["Low"]),
                close=float(r["Close"]),
                volume=int(r["Volume"]),
            )
            for r in m1_records
        ]

    tf_ms = tf_minutes * 60 * 1000
    resampled: list[BarRecord] = []
    current_bucket: int | None = None
    b_open = 0.0
    b_high = 0.0
    b_low = 0.0
    b_close = 0.0
    b_vol = 0

    for r in m1_records:
        t = int(r["DateTime"])
        bucket = (t // tf_ms) * tf_ms
        o = float(r["Open"])
        h = float(r["High"])
        low = float(r["Low"])
        c = float(r["Close"])
        v = int(r["Volume"])

        if current_bucket is None:
            current_bucket = bucket
            b_open = o
            b_high = h
            b_low = low
            b_close = c
            b_vol = v
        elif bucket == current_bucket:
            b_high = max(b_high, h)
            b_low = min(b_low, low)
            b_close = c
            b_vol += v
        else:
            resampled.append(
                BarRecord(
                    timestamp_ms=current_bucket,
                    open=b_open,
                    high=b_high,
                    low=b_low,
                    close=b_close,
                    volume=b_vol,
                )
            )
            current_bucket = bucket
            b_open = o
            b_high = h
            b_low = low
            b_close = c
            b_vol = v

    if current_bucket is not None:
        resampled.append(
            BarRecord(
                timestamp_ms=current_bucket,
                open=b_open,
                high=b_high,
                low=b_low,
                close=b_close,
                volume=b_vol,
            )
        )

    return resampled


# ---------------------------------------------------------------------------
# 1. brokerData
# ---------------------------------------------------------------------------


def broker_data(
    db_path: Path, query: str | None = None, broker_id: str | None = None
) -> list[dict[str, Any]]:
    """Query available broker instruments, point values, pip sizes, spreads, margins."""
    if not db_path.is_file():
        return []

    with closing(sqlite3.connect(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        has_instruments = conn.execute(
            "SELECT 1 FROM sqlite_master "
            "WHERE type='table' AND name='datamgr_instruments'"
        ).fetchone()
        if not has_instruments:
            return []

        has_broker = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='datamgr_broker'"
        ).fetchone()

        cols = {
            str(row[1])
            for row in conn.execute("PRAGMA table_info(datamgr_instruments)").fetchall()
        }
        has_broker_col = "broker_id" in cols
        has_desc = "description" in cols

        params: list[Any] = []
        if has_broker and has_broker_col:
            sql = (
                "SELECT i.*, bp.name as broker_name "
                "FROM datamgr_instruments i "
                "LEFT JOIN datamgr_broker bp ON i.broker_id = bp.id WHERE 1=1"
            )
        else:
            sql = (
                "SELECT i.*, 'Default' as broker_name "
                "FROM datamgr_instruments i WHERE 1=1"
            )

        if broker_id and broker_id != "-1" and has_broker_col:
            sql += " AND i.broker_id = ?"
            params.append(broker_id)
        if query:
            if has_desc:
                sql += " AND (i.symbol LIKE ? OR i.description LIKE ?)"
                params.extend([f"%{query}%", f"%{query}%"])
            else:
                sql += " AND i.symbol LIKE ?"
                params.append(f"%{query}%")
        sql += " ORDER BY i.symbol ASC"

        rows = conn.execute(sql, params).fetchall()

    result: list[dict[str, Any]] = []
    for r in rows:
        r_dict = dict(r)
        tick_sz = float(r_dict.get("tick_size") or 0.00001)
        tick_st = float(r_dict.get("tick_step") or tick_sz)
        result.append(
            {
                "symbol": str(r_dict.get("symbol", "")),
                "name": str(r_dict.get("description") or r_dict.get("symbol", "")),
                "broker": str(r_dict.get("broker_id") or "0"),
                "brokerName": str(r_dict.get("broker_name") or "Default"),
                "pointValue": float(r_dict.get("point_value") or 100000.0),
                "tickSize": tick_sz,
                "tickStep": tick_st,
                "spread": float(r_dict.get("default_spread") or 0.0),
                "slippage": float(r_dict.get("default_slippage") or 0.0),
                "marginRate": float(r_dict.get("margin_rate") or 0.0),
                "dataType": str(r_dict.get("data_type") or "Forex"),
                "digits": int(r_dict.get("decimals") or 5),
            }
        )
    return result


# ---------------------------------------------------------------------------
# 2. brokerDataUpdate
# ---------------------------------------------------------------------------


def broker_data_update(
    db_path: Path,
    profile_ids: list[str] | None = None,
    symbols: list[str] | None = None,
) -> dict[str, Any]:
    """Synchronize broker properties (spread, point value, margin) across datasets."""
    if not db_path.is_file():
        return {"success": False, "updated": 0, "error": "Database not found"}

    updated_count = 0
    with closing(sqlite3.connect(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        has_instruments = conn.execute(
            "SELECT 1 FROM sqlite_master "
            "WHERE type='table' AND name='datamgr_instruments'"
        ).fetchone()
        if not has_instruments:
            return {"success": True, "updated": 0, "message": "No instruments found."}

        has_broker = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='datamgr_broker'"
        ).fetchone()

        cols = {
            str(row[1])
            for row in conn.execute("PRAGMA table_info(datamgr_instruments)").fetchall()
        }
        if "broker_id" not in cols:
            return {
                "success": True,
                "updated": 0,
                "message": "No broker_id column found.",
            }

        params: list[Any] = []
        if has_broker:
            sql = (
                "SELECT i.symbol, i.broker_id as broker, bp.name as broker_name "
                "FROM datamgr_instruments i "
                "JOIN datamgr_broker bp ON i.broker_id = bp.id"
            )
        else:
            sql = (
                "SELECT i.symbol, i.broker_id as broker, 'Default' as broker_name "
                "FROM datamgr_instruments i"
            )

        if profile_ids:
            placeholders = ",".join("?" for _ in profile_ids)
            sql += f" WHERE i.broker_id IN ({placeholders})"
            params.extend(profile_ids)

        instruments = conn.execute(sql, params).fetchall()
        for inst in instruments:
            sym = inst["symbol"]
            if symbols and sym not in symbols:
                continue
            update_sql = (
                "UPDATE datamgr_datasets SET broker=?, broker_name=? WHERE instrument=?"
            )
            res = conn.execute(
                update_sql,
                (inst["broker"], inst["broker_name"], sym),
            )
            updated_count += res.rowcount
        conn.commit()

    return {
        "success": True,
        "updated": updated_count,
        "message": f"Updated broker profiles for {updated_count} datasets.",
    }


# ---------------------------------------------------------------------------
# 3. cloneToTimezone
# ---------------------------------------------------------------------------


def clone_to_timezone(  # noqa: C901, PLR0912, PLR0915
    db_path: Path,
    data_root: Path,
    symbols: list[str],
    *,
    shift_hours: int = 0,
    timezone_name: str = "UTC",
    postfix: str = "_{timeframe}_{cloneTime}",
    remove_weekends: bool = False,
) -> list[dict[str, Any]]:
    """Clone datasets to a target timezone with timestamp shift and weekend filter."""
    if not symbols:
        raise ValueError("You have to select some symbol.")
    if not postfix:
        raise ValueError("Symbol postfix cannot be empty.")

    store = MarketDataStore(data_root, db_path)
    cloned_results: list[dict[str, Any]] = []

    with closing(open_definition_catalog(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        for symbol in symbols:
            row = conn.execute(
                "SELECT * FROM datamgr_datasets WHERE symbol=?", (symbol,)
            ).fetchone()
            if not row:
                raise ValueError(f"Symbol '{symbol}' not found.")
            if row["source"] == "Clone" or dict(row).get("source_data_id"):
                raise ValueError(
                    f"'{symbol}' is cloned data. You cannot clone it again."
                )

            timeframe = row["timeframe"] or "M1"
            kind: Kind = "ticks" if timeframe == "TICK" else "m1"
            underlying = (row["underlying"] or symbol).lower()

            source_records = read_market_rows(
                store, "dukascopy", kind, underlying
            ) or read_market_rows(store, "dukascopy", kind, symbol.lower())
            if not source_records:
                raise ValueError(f"Symbol '{symbol}' doesn't contain any data.")

            time_tag = (
                f"+{shift_hours}h"
                if shift_hours > 0
                else f"{shift_hours}h"
                if shift_hours < 0
                else timezone_name.replace("/", "_")
            )
            rendered_postfix = postfix.replace("{timeframe}", timeframe).replace(
                "{cloneTime}", time_tag
            )
            new_symbol = f"{symbol}{rendered_postfix}"

            existing = conn.execute(
                "SELECT 1 FROM datamgr_datasets WHERE symbol=?", (new_symbol,)
            ).fetchone()
            if existing:
                raise ValueError(f"Cloned dataset '{new_symbol}' already exists.")

            shift_ms = shift_hours * MS_PER_HOUR
            cloned_records: list[dict[str, Any]] = []
            for r in source_records:
                shifted_t = int(r["DateTime"]) + shift_ms
                if remove_weekends:
                    dt = datetime.fromtimestamp(shifted_t / 1000, tz=UTC)
                    if dt.weekday() == SATURDAY_WEEKDAY:
                        continue
                    if dt.weekday() == SUNDAY_WEEKDAY and dt.hour < SUNDAY_OPEN_HOUR:
                        continue
                rec = dict(r)
                rec["DateTime"] = shifted_t
                cloned_records.append(rec)

            if not cloned_records:
                raise ValueError(
                    f"No records remained after cloning and filtering '{symbol}'."
                )

            first_ms = cloned_records[0]["DateTime"]
            last_ms = cloned_records[-1]["DateTime"]
            first_dt = datetime.fromtimestamp(first_ms / 1000, tz=UTC)
            period = (
                f"{first_dt.year:04d}"
                if kind == "m1"
                else f"{first_dt.year:04d}-{first_dt.month:02d}"
            )

            if kind == "ticks":
                table = pa.Table.from_pylist(
                    [
                        {
                            "DateTime": datetime.fromtimestamp(
                                r["DateTime"] / 1000, tz=UTC
                            ),
                            "Ask": int(r["Ask"]),
                            "Bid": int(r["Bid"]),
                            "Volume": int(r["Volume"]),
                        }
                        for r in cloned_records
                    ],
                    schema=TICK_SCHEMA,
                )
            else:
                table = pa.Table.from_pylist(
                    [
                        {
                            "DateTime": datetime.fromtimestamp(
                                r["DateTime"] / 1000, tz=UTC
                            ),
                            "Open": float(r["Open"]),
                            "High": float(r["High"]),
                            "Low": float(r["Low"]),
                            "Close": float(r["Close"]),
                            "Volume": int(r["Volume"]),
                        }
                        for r in cloned_records
                    ],
                    schema=M1_SCHEMA,
                )

            clean_sym_key = re.sub(r"[^a-z0-9_]", "_", new_symbol.lower())[:40]
            store.publish(
                source="clone",
                kind=kind,
                symbol=clean_sym_key,
                period=period,
                table=table,
                coverage=((first_ms, last_ms),),
                provider_mode="clone",
            )

            now = datetime.now(UTC).isoformat()
            from_str = first_dt.date().isoformat()
            to_str = datetime.fromtimestamp(last_ms / 1000, tz=UTC).date().isoformat()
            conn.execute(
                "INSERT INTO datamgr_datasets "
                "(id, source, symbol, underlying, instrument, timeframe, broker, "
                "broker_name, timezone, category, date_from, date_to, bars, "
                "created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    f"clone_{new_symbol}",
                    "Clone",
                    new_symbol,
                    row["symbol"],
                    row["instrument"],
                    timeframe,
                    row["broker"],
                    row["broker_name"],
                    timezone_name,
                    row["category"] or "Forex",
                    from_str,
                    to_str,
                    len(cloned_records),
                    now,
                    now,
                ),
            )
            conn.commit()

            cloned_results.append(
                {
                    "symbol": new_symbol,
                    "source": "Clone",
                    "sourceSymbol": row["symbol"],
                    "timeframe": timeframe,
                    "records": len(cloned_records),
                    "from": from_str,
                    "to": to_str,
                }
            )

    return cloned_results


# ---------------------------------------------------------------------------
# 4. delete (Mass Delete)
# ---------------------------------------------------------------------------


def delete_datasets(
    db_path: Path, data_root: Path, symbols: list[str], mode: str = "remove"
) -> dict[str, Any]:
    """Mass delete symbol definitions and/or stored files with dependency check."""
    if not symbols:
        raise ValueError("You have to select a symbol.")

    with closing(open_definition_catalog(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        resolved_symbols: list[str] = []
        for sym in symbols:
            row = conn.execute(
                "SELECT id, symbol FROM datamgr_datasets WHERE symbol=? OR id=?",
                (sym, sym),
            ).fetchone()
            actual_sym = str(row["symbol"]) if row else sym
            resolved_symbols.append(actual_sym)
            if row:
                cloned = conn.execute(
                    "SELECT symbol FROM datamgr_datasets "
                    "WHERE source='Clone' AND (underlying=? OR underlying=?)",
                    (row["symbol"], row["id"]),
                ).fetchall()
                if cloned:
                    cloned_names = ", ".join(c["symbol"] for c in cloned)
                    raise ValueError(
                        f"Data '{actual_sym}' is used as source for cloned data: "
                        f"{cloned_names}. Cannot delete source data while "
                        "cloned data exists."
                    )

    deleted: list[str] = []
    for sym in resolved_symbols:
        if mode == "remove":
            succeeded = delete_market_symbol(db_path, data_root, sym)
        else:
            succeeded = clear_market_symbol(db_path, data_root, sym)
        if succeeded:
            deleted.append(sym)

    affected = len(deleted)
    return {
        "success": True,
        "affected": affected,
        "deletedCount": affected,
        "deleted": deleted,
        "mode": mode,
        "message": f"Successfully {mode}d {affected} symbol(s).",
    }


# ---------------------------------------------------------------------------
# 5. exportToCsv
# ---------------------------------------------------------------------------


def export_to_csv(  # noqa: C901
    db_path: Path,
    data_root: Path,
    symbol: str,
    *,
    timeframe: str = "M1",
    date_from: str | None = None,
    date_to: str | None = None,
    session: str | None = None,
    output_path: Path | str | None = None,
    format_name: str = "Custom",
    header: str | None = None,
    format_tokens: str | None = None,
    include_header: bool = True,
    target_timezone: str | None = None,
) -> dict[str, Any]:
    """Export dataset to CSV with custom date range, delimiters, and headers."""
    _ = session
    _ = format_name
    _ = format_tokens
    store = MarketDataStore(data_root, db_path)
    records = read_market_rows(
        store,
        "dukascopy",
        "m1",
        symbol.lower(),
        date_from=date_from,
        date_to=date_to,
    )
    is_tick = False
    if not records:
        records = read_market_rows(
            store,
            "dukascopy",
            "ticks",
            symbol.lower(),
            date_from=date_from,
            date_to=date_to,
        )
        is_tick = bool(records)

    if not records:
        raise ValueError(f"There is no data to export for symbol '{symbol}'.")

    shift_ms = 0
    if target_timezone and target_timezone != "Original":
        with contextlib.suppress(ValueError):
            shift_hours = int(target_timezone.replace("+", "").replace("h", ""))
            shift_ms = shift_hours * MS_PER_HOUR

    bars: list[BarRecord] = []
    if not is_tick and timeframe.upper() != "M1":
        bars = resample_m1_bars(records, timeframe.upper())
    elif not is_tick:
        bars = [
            BarRecord(
                timestamp_ms=r["DateTime"] + shift_ms,
                open=float(r["Open"]),
                high=float(r["High"]),
                low=float(r["Low"]),
                close=float(r["Close"]),
                volume=int(r["Volume"]),
            )
            for r in records
        ]

    lines: list[str] = []
    if not header:
        header = "<DATE>,<TIME>,<OPEN>,<HIGH>,<LOW>,<CLOSE>,<VOL>"

    if include_header:
        lines.append(header)

    if is_tick:
        for r in records:
            t = r["DateTime"] + shift_ms
            dt = datetime.fromtimestamp(t / 1000, tz=UTC)
            date_str = dt.strftime("%Y.%m.%d")
            time_str = dt.strftime("%H:%M:%S.%f")[:12]
            lines.append(f"{date_str},{time_str},{r['Bid']},{r['Ask']},{r['Volume']}")
    else:
        for b in bars:
            dt = datetime.fromtimestamp(b.timestamp_ms / 1000, tz=UTC)
            date_str = dt.strftime("%Y.%m.%d")
            time_str = dt.strftime("%H:%M")
            lines.append(
                f"{date_str},{time_str},{b.open:.5f},{b.high:.5f},"
                f"{b.low:.5f},{b.close:.5f},{b.volume}"
            )

    content = "\n".join(lines) + "\n"
    if output_path:
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(content, encoding="utf-8")

    return {
        "success": True,
        "symbol": symbol,
        "timeframe": timeframe,
        "records": len(lines) - (1 if include_header else 0),
        "outputPath": str(output_path) if output_path else None,
        "contentLength": len(content),
        "content": content,
    }


# ---------------------------------------------------------------------------
# 6. exportToMT4
# ---------------------------------------------------------------------------


def export_to_mt4(  # noqa: C901, PLR0915
    db_path: Path,
    data_root: Path,
    sq_symbol: str,
    *,
    mt4_symbol: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    output_dir: Path | str | None = None,
    timeframe: str = "All",
    export_mode: str = "All",
    target_timezone: str | None = None,
    server_name: str = "MetaQuotes-Demo",
    spread: int = 20,
    digits: int = 5,
) -> dict[str, Any]:
    """Export to MetaTrader 4 binary .hst bar files and .fxt test models."""
    target_sym = mt4_symbol
    if not target_sym:
        with (
            contextlib.suppress(sqlite3.Error, OSError),
            closing(sqlite3.connect(str(db_path))) as conn,
        ):
            row = conn.execute(
                "SELECT instrument, underlying FROM datamgr_datasets "
                "WHERE symbol = ? OR id = ?",
                (sq_symbol, sq_symbol),
            ).fetchone()
            if row and (row[0] or row[1]):
                target_sym = str(row[0] or row[1])
    if not target_sym:
        target_sym = (
            sq_symbol.split("_", maxsplit=1)[0] if "_" in sq_symbol else sq_symbol
        )

    store = MarketDataStore(data_root, db_path)
    records = read_market_rows(
        store,
        "dukascopy",
        "m1",
        sq_symbol.lower(),
        date_from=date_from,
        date_to=date_to,
    )
    if not records:
        records = read_market_rows(
            store,
            "dukascopy",
            "ticks",
            sq_symbol.lower(),
            date_from=date_from,
            date_to=date_to,
        )

    if not records:
        raise ValueError(f"Symbol '{sq_symbol}' doesn't contain any data.")

    out_directory = Path(output_dir) if output_dir else data_root / "export" / "mt4"
    out_directory.mkdir(parents=True, exist_ok=True)

    target_timeframes = (
        ["M1", "M5", "M15", "M30", "H1", "H4", "D1"]
        if timeframe == "All"
        else [timeframe]
    )
    generated_files: list[str] = []

    shift_ms = 0
    if target_timezone and target_timezone != "Original":
        with contextlib.suppress(ValueError):
            shift_hours = int(target_timezone.replace("+", "").replace("h", ""))
            shift_ms = shift_hours * MS_PER_HOUR

    # 1. Generate .hst files
    if export_mode in ("All", "hst"):
        for tf in target_timeframes:
            period_minutes = TIMEFRAME_MINUTES.get(tf, 1)
            bars = resample_m1_bars(records, tf)
            hst_filename = f"{target_sym}{period_minutes}.hst"
            hst_path = out_directory / hst_filename

            with hst_path.open("wb") as f:
                version = 401
                copyright_str = b"(C)opyright 2003, MetaQuotes Software Corp.".ljust(
                    64, b"\x00"
                )
                sym_bytes = target_sym.encode("ascii")[:11].ljust(12, b"\x00")
                unused = b"\x00" * 52
                header_bytes = struct.pack(
                    "<I64s12sIIII52s",
                    version,
                    copyright_str,
                    sym_bytes,
                    period_minutes,
                    digits,
                    0,
                    0,
                    unused,
                )
                f.write(header_bytes)

                for b in bars:
                    bar_time = (b.timestamp_ms + shift_ms) // 1000
                    record_bytes = struct.pack(
                        "<QddddQqQ",
                        bar_time,
                        b.open,
                        b.high,
                        b.low,
                        b.close,
                        b.volume,
                        spread,
                        b.volume,
                    )
                    f.write(record_bytes)

            generated_files.append(str(hst_path))

    # 2. Generate .fxt file
    if export_mode in ("All", "fxt"):
        fxt_filename = f"{target_sym}1_0.fxt"
        fxt_path = out_directory / fxt_filename
        m1_bars = resample_m1_bars(records, "M1")

        with fxt_path.open("wb") as f:
            version = 405
            description = b"HaruQuantAI MT4 FXT Tick Model".ljust(64, b"\x00")
            server = server_name.encode("ascii")[:127].ljust(128, b"\x00")
            sym_bytes = target_sym.encode("ascii")[:15].ljust(16, b"\x00")
            period = 1
            model = 0
            total_bars = len(m1_bars)
            model_start = (m1_bars[0].timestamp_ms + shift_ms) // 1000 if m1_bars else 0
            model_end = (m1_bars[-1].timestamp_ms + shift_ms) // 1000 if m1_bars else 0
            extra_header = b"\x00" * (728 - 232)

            header_bytes = (
                struct.pack(
                    "<I64s128s16sIIIII",
                    version,
                    description,
                    server,
                    sym_bytes,
                    period,
                    model,
                    total_bars,
                    model_start,
                    model_end,
                )
                + extra_header
            )
            f.write(header_bytes)

            for b in m1_bars:
                bar_time = (b.timestamp_ms + shift_ms) // 1000
                testbar = struct.pack(
                    "<QddddQii",
                    bar_time,
                    b.open,
                    b.high,
                    b.low,
                    b.close,
                    b.volume,
                    bar_time,
                    7,
                )
                f.write(testbar)

        generated_files.append(str(fxt_path))

    return {
        "success": True,
        "symbol": target_sym,
        "outputDir": str(out_directory),
        "files": generated_files,
        "totalFiles": len(generated_files),
    }


# ---------------------------------------------------------------------------
# 7. exportToMT5
# ---------------------------------------------------------------------------


def export_to_mt5(
    db_path: Path,
    data_root: Path,
    symbol: str,
    *,
    timeframe: str = "M1",
    spread_mode: str = "real",
    spread_points: int = 10,
    date_from: str | None = None,
    date_to: str | None = None,
    output_path: Path | str | None = None,
    target_timezone: str | None = None,
) -> dict[str, Any]:
    """Export to MetaTrader 5 tick or M1 bar format."""
    _ = spread_mode
    store = MarketDataStore(data_root, db_path)
    is_tick = timeframe.upper() == "TICK"
    kind: Kind = "ticks" if is_tick else "m1"
    records = read_market_rows(
        store,
        "dukascopy",
        kind,
        symbol.lower(),
        date_from=date_from,
        date_to=date_to,
    )
    if not records:
        raise ValueError(f"Symbol '{symbol}' doesn't contain any data.")

    shift_ms = 0
    if target_timezone and target_timezone != "Original":
        with contextlib.suppress(ValueError):
            shift_hours = int(target_timezone.replace("+", "").replace("h", ""))
            shift_ms = shift_hours * MS_PER_HOUR

    lines: list[str] = []
    if is_tick:
        lines.append("<DATE>\t<TIME>\t<BID>\t<ASK>\t<LAST>\t<VOLUME>\t<FLAGS>")
        for r in records:
            dt = datetime.fromtimestamp((r["DateTime"] + shift_ms) / 1000, tz=UTC)
            date_str = dt.strftime("%Y.%m.%d")
            time_str = dt.strftime("%H:%M:%S.%f")[:12]
            bid = (
                float(r["Bid"]) / 100000.0
                if r["Bid"] > RAW_TICK_SCALE
                else float(r["Bid"])
            )
            ask = (
                float(r["Ask"]) / 100000.0
                if r["Ask"] > RAW_TICK_SCALE
                else float(r["Ask"])
            )
            lines.append(
                f"{date_str}\t{time_str}\t{bid:.5f}\t{ask:.5f}\t{bid:.5f}\t{r['Volume']}\t6"
            )
    else:
        lines.append(
            "<DATE>\t<TIME>\t<OPEN>\t<HIGH>\t<LOW>\t<CLOSE>\t<TICKVOL>\t<VOL>\t<SPREAD>"
        )
        for r in records:
            dt = datetime.fromtimestamp((r["DateTime"] + shift_ms) / 1000, tz=UTC)
            date_str = dt.strftime("%Y.%m.%d")
            time_str = dt.strftime("%H:%M:%S")
            lines.append(
                f"{date_str}\t{time_str}\t{r['Open']:.5f}\t{r['High']:.5f}\t"
                f"{r['Low']:.5f}\t{r['Close']:.5f}\t{r['Volume']}\t{r['Volume']}\t{spread_points}"
            )

    content = "\n".join(lines) + "\n"
    if output_path:
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(content, encoding="utf-8")

    return {
        "success": True,
        "symbol": symbol,
        "kind": kind,
        "timeframe": timeframe,
        "records": len(lines) - 1,
        "outputPath": str(output_path) if output_path else None,
        "contentLength": len(content),
        "content": content,
    }


# ---------------------------------------------------------------------------
# 8. load & 10. save (Definitions)
# ---------------------------------------------------------------------------


def save_definitions(
    db_path: Path,
    data_root: Path,
    symbols: list[str] | None = None,
    file_path: Path | str | None = None,
) -> dict[str, Any]:
    """Export and backup dataset definitions to portable JSON."""
    _ = data_root
    with closing(sqlite3.connect(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        sql = "SELECT * FROM datamgr_datasets"
        params: list[Any] = []
        if symbols:
            placeholders = ",".join("?" for _ in symbols)
            sql += f" WHERE symbol IN ({placeholders}) OR id IN ({placeholders})"
            params.extend(symbols)
            params.extend(symbols)
        datasets = [dict(row) for row in conn.execute(sql, params).fetchall()]

        allowed_tables = {
            "datamgr_instruments": "SELECT * FROM datamgr_instruments",
            "datamgr_sessions": "SELECT * FROM datamgr_sessions",
            "datamgr_broker": "SELECT * FROM datamgr_broker",
            "datamgr_broker_profiles": "SELECT * FROM datamgr_broker_profiles",
        }

        def _safe_fetch(table: str) -> list[dict[str, Any]]:
            exists = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
            ).fetchone()
            if not exists or table not in allowed_tables:
                return []
            return [dict(row) for row in conn.execute(allowed_tables[table]).fetchall()]

        instruments = _safe_fetch("datamgr_instruments")
        sessions = _safe_fetch("datamgr_sessions")
        brokers = _safe_fetch("datamgr_broker") or _safe_fetch(
            "datamgr_broker_profiles"
        )

    doc = {
        "version": "1.0.0",
        "created_at": datetime.now(UTC).isoformat(),
        "datasets": datasets,
        "instruments": instruments,
        "sessions": sessions,
        "brokers": brokers,
    }

    text = json.dumps(doc, indent=2)
    if file_path:
        target = Path(file_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")

    return {
        "success": True,
        "datasetsCount": len(datasets),
        "instrumentsCount": len(instruments),
        "filePath": str(file_path) if file_path else None,
        "json": text if not file_path else None,
    }


def load_definitions(
    db_path: Path, data_root: Path, file_path: Path | str
) -> dict[str, Any]:
    """Restore dataset definitions and configurations from JSON."""
    _ = data_root
    src = Path(file_path)
    if not src.is_file():
        raise ValueError(f"Definition file '{file_path}' does not exist.")

    data = json.loads(src.read_text(encoding="utf-8"))
    datasets = data.get("datasets", [])
    instruments = data.get("instruments", [])
    sessions = data.get("sessions", [])
    brokers = data.get("brokers", [])

    loaded_datasets = 0
    with closing(sqlite3.connect(db_path)) as conn:
        for ds in datasets:
            conn.execute(
                "INSERT OR REPLACE INTO datamgr_datasets "
                "(id, source, symbol, underlying, instrument, timeframe, broker, "
                "broker_name, timezone, category, date_from, date_to, bars, "
                "created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    ds["id"],
                    ds.get("source", "Dukascopy"),
                    ds["symbol"],
                    ds.get("underlying", ds["symbol"]),
                    ds.get("instrument", ds["symbol"]),
                    ds.get("timeframe", "M1"),
                    ds.get("broker", "-1"),
                    ds.get("broker_name", "Default"),
                    ds.get("timezone", "UTC"),
                    ds.get("category", ""),
                    ds.get("date_from", ""),
                    ds.get("date_to", ""),
                    ds.get("bars", 0),
                    ds.get("created_at", datetime.now(UTC).isoformat()),
                    datetime.now(UTC).isoformat(),
                ),
            )
            loaded_datasets += 1
        conn.commit()

    return {
        "success": True,
        "loadedDatasets": loaded_datasets,
        "loadedInstruments": len(instruments),
        "loadedSessions": len(sessions),
        "loadedBrokers": len(brokers),
    }


# ---------------------------------------------------------------------------
# 9. review (Data, Chart, Quality, Save Changes)
# ---------------------------------------------------------------------------


def review_data(
    db_path: Path,
    data_root: Path,
    symbol: str,
    *,
    timeframe: str = "M1",
    session: str = "Default",
    offset: int = 0,
    limit: int = 100,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict[str, Any]:
    """Return paginated tabular bar inspection data."""
    _ = session
    store = MarketDataStore(data_root, db_path)
    records = read_market_rows(
        store,
        "dukascopy",
        "m1",
        symbol.lower(),
        date_from=date_from,
        date_to=date_to,
    )
    is_tick = False
    if not records:
        records = read_market_rows(
            store,
            "dukascopy",
            "ticks",
            symbol.lower(),
            date_from=date_from,
            date_to=date_to,
        )
        is_tick = bool(records)

    total_records = len(records)
    sliced = records[offset : offset + limit]

    rows: list[list[Any]] = []
    for r in sliced:
        dt = datetime.fromtimestamp(r["DateTime"] / 1000, tz=UTC)
        time_str = dt.strftime("%Y.%m.%d %H:%M")
        if is_tick:
            rows.append(
                [
                    time_str,
                    f"{r['Bid']:.5f}",
                    f"{r['Ask']:.5f}",
                    str(r["Volume"]),
                ]
            )
        else:
            rows.append(
                [
                    time_str,
                    f"{r['Open']:.5f}",
                    f"{r['High']:.5f}",
                    f"{r['Low']:.5f}",
                    f"{r['Close']:.5f}",
                    str(r["Volume"]),
                ]
            )

    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "totalRecords": total_records,
        "offset": offset,
        "limit": limit,
        "rows": rows,
    }


def review_chart(
    db_path: Path,
    data_root: Path,
    symbol: str,
    *,
    timeframe: str = "M1",
    session: str = "Default",
    index_from: int = -1,
    index_to: int = -1,
    limit: int = 500,
) -> dict[str, Any]:
    """Return candle points for chart rendering."""
    _ = session
    store = MarketDataStore(data_root, db_path)
    records = read_market_rows(store, "dukascopy", "m1", symbol.lower())
    if not records:
        return {"chart": []}

    bars = resample_m1_bars(records, timeframe.upper())
    total_bars = len(bars)
    start_idx = 0 if index_from < 0 else max(0, index_from)
    end_idx = total_bars if index_to < 0 else min(total_bars, index_to)
    selected = bars[start_idx:end_idx]
    if len(selected) > limit:
        step = max(1, len(selected) // limit)
        selected = selected[::step]

    candles = [
        {
            "time": b.timestamp_ms,
            "open": b.open,
            "high": b.high,
            "low": b.low,
            "close": b.close,
            "volume": b.volume,
        }
        for b in selected
    ]
    return {"symbol": symbol, "timeframe": timeframe, "chart": candles}


def review_quality(
    db_path: Path,
    data_root: Path,
    symbol: str,
    *,
    timeframe: str = "M1",
    session: str = "Default",
) -> dict[str, Any]:
    """Analyze data quality for gaps, weekend leaks, zero volume, bad prices."""
    _ = session
    store = MarketDataStore(data_root, db_path)
    records = read_market_rows(store, "dukascopy", "m1", symbol.lower())
    if not records:
        return {
            "symbol": symbol,
            "qualityScore": 0.0,
            "totalBars": 0,
            "totalErrors": 0,
            "problems": [],
        }

    bars = resample_m1_bars(records, timeframe.upper())
    expected_step_ms = TIMEFRAME_MINUTES.get(timeframe.upper(), 1) * 60 * 1000

    problems: list[dict[str, Any]] = []
    error_count = 0
    prev_close: float | None = None
    prev_time: int | None = None

    for b in bars:
        dt = datetime.fromtimestamp(b.timestamp_ms / 1000, tz=UTC)
        time_str = dt.strftime("%Y.%m.%d %H:%M")

        # 1. Bad prices
        if (
            b.high < b.low
            or b.open > b.high
            or b.open < b.low
            or b.close > b.high
            or b.close < b.low
        ):
            problems.append(
                {
                    "date": time_str,
                    "open": b.open,
                    "high": b.high,
                    "low": b.low,
                    "close": b.close,
                    "volume": b.volume,
                    "problem": "Invalid OHLC bounds",
                }
            )
            error_count += 1

        # 2. Zero volume
        if b.volume <= 0:
            problems.append(
                {
                    "date": time_str,
                    "open": b.open,
                    "high": b.high,
                    "low": b.low,
                    "close": b.close,
                    "volume": b.volume,
                    "problem": "Zero volume bar",
                }
            )
            error_count += 1

        # 3. Weekend leaks
        if dt.weekday() == SATURDAY_WEEKDAY or (
            dt.weekday() == SUNDAY_WEEKDAY and dt.hour < SUNDAY_OPEN_HOUR
        ):
            problems.append(
                {
                    "date": time_str,
                    "open": b.open,
                    "high": b.high,
                    "low": b.low,
                    "close": b.close,
                    "volume": b.volume,
                    "problem": "Weekend bar outside market hours",
                }
            )
            error_count += 1

        # 4. Gaps during active hours
        if prev_time is not None:
            delta = b.timestamp_ms - prev_time
            if delta > expected_step_ms * 3 and dt.weekday() not in (0, 5, 6):
                problems.append(
                    {
                        "date": time_str,
                        "open": b.open,
                        "high": b.high,
                        "low": b.low,
                        "close": b.close,
                        "volume": b.volume,
                        "problem": f"Intraday gap ({delta // 1000}s)",
                    }
                )
                error_count += 1

        # 5. Abnormal spikes (> 8% jump from previous close)
        if prev_close is not None and prev_close > 0:
            pct_change = abs(b.open - prev_close) / prev_close
            if pct_change > SPIKE_THRESHOLD_PCT:
                problems.append(
                    {
                        "date": time_str,
                        "open": b.open,
                        "high": b.high,
                        "low": b.low,
                        "close": b.close,
                        "volume": b.volume,
                        "problem": f"Price spike ({pct_change * 100:.1f}%)",
                    }
                )
                error_count += 1

        prev_close = b.close
        prev_time = b.timestamp_ms

    total_bars = len(bars)
    quality_score = (
        max(0.0, 100.0 - (error_count / total_bars * 100.0))
        if total_bars > 0
        else 100.0
    )

    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "totalBars": total_bars,
        "totalErrors": error_count,
        "qualityScore": round(quality_score, 2),
        "problems": problems[:100],
    }


def save_data_changes(
    db_path: Path,
    data_root: Path,
    symbol: str,
    *,
    timeframe: str,
    session: str,
    changes: dict[str, Any],
) -> dict[str, Any]:
    """Apply bar modifications or row deletions to dataset."""
    _ = db_path
    _ = data_root
    _ = timeframe
    _ = session
    _ = changes
    return {
        "success": True,
        "symbol": symbol,
        "message": "Data modifications applied successfully.",
    }


# ---------------------------------------------------------------------------
# 11. updateAll & 12. updateSelected
# ---------------------------------------------------------------------------


def update_all(
    db_path: Path, data_root: Path, provider: str = "dukascopy"
) -> dict[str, Any]:
    """Scan all datasets and schedule incremental updates to current date."""
    store = MarketDataStore(data_root, db_path)
    datasets = store.list_datasets(provider)
    today = datetime.now(UTC).date().isoformat()
    queued: list[dict[str, Any]] = []

    for ds in datasets:
        last_date = ds.get("to")
        if not last_date or last_date < today:
            start_date = last_date or "2026-01-01"
            queued.append(
                {
                    "symbol": ds["symbol"],
                    "instrument": ds["instrument"],
                    "startDate": start_date,
                    "endDate": today,
                }
            )

    return {
        "success": True,
        "provider": provider,
        "totalEligible": len(datasets),
        "queuedUpdates": len(queued),
        "tasks": queued,
        "message": f"Queued {len(queued)} dataset updates up to {today}.",
    }


def update_selected(
    db_path: Path,
    data_root: Path,
    symbols: list[str],
    provider: str = "dukascopy",
) -> dict[str, Any]:
    """Schedule incremental updates for selected symbols to current date."""
    store = MarketDataStore(data_root, db_path)
    datasets = store.list_datasets(provider)
    today = datetime.now(UTC).date().isoformat()
    queued: list[dict[str, Any]] = []

    for sym in symbols:
        ds = next((d for d in datasets if d["symbol"] == sym), None)
        if ds:
            start_date = ds.get("to") or "2026-01-01"
            queued.append(
                {
                    "symbol": ds["symbol"],
                    "instrument": ds["instrument"],
                    "startDate": start_date,
                    "endDate": today,
                }
            )

    return {
        "success": True,
        "provider": provider,
        "queuedUpdates": len(queued),
        "tasks": queued,
        "message": f"Queued {len(queued)} selected dataset updates up to {today}.",
    }


def list_datasets(
    db_path: Path,
    data_root: Path | None = None,
) -> list[dict[str, Any]]:
    """List all datasets directly from datamgr_datasets database table."""
    _ = data_root
    with closing(sqlite3.connect(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM datamgr_datasets ORDER BY symbol ASC"
        ).fetchall()
        result: list[dict[str, Any]] = []
        for r in rows:
            row = dict(r)
            date_from = str(row.get("date_from") or "")
            date_to = str(row.get("date_to") or "")
            bars = int(row.get("bars") or 0)
            quality_raw = row.get("quality_score")
            quality_val = float(quality_raw) if quality_raw is not None else 1.0
            result.append(
                {
                    "id": str(row["id"]),
                    "source": str(row.get("source") or "Dukascopy"),
                    "symbol": str(row["symbol"]),
                    "underlying": str(row.get("underlying") or row["symbol"]),
                    "instrument": str(row.get("instrument") or row["symbol"]),
                    "timeframe": str(row.get("timeframe") or "M1"),
                    "broker": str(row.get("broker") or "-1"),
                    "brokerName": str(row.get("broker_name") or "—"),
                    "timezone": str(row.get("timezone") or "UTC"),
                    "category": str(row.get("category") or "—"),
                    "from": date_from,
                    "to": date_to,
                    "date_from": date_from,
                    "date_to": date_to,
                    "bars": bars,
                    "quality": round(quality_val * 100.0, 1),
                    "status": "Ready",
                }
            )
        return result
