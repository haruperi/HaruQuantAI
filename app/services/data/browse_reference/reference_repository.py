"""Market Data Reference Repository & Operations in the Data Domain.

Owns all reference catalogue queries (SQLite data/database/haruquantai.db),
Parquet historical bar/tick reads, data quality anomaly calculations,
timezone cloning, and export generation.
"""

from __future__ import annotations

import contextlib
import logging
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Final, cast

import polars as pl

from app.contracts.common.models import JsonValue, ProblemDetails
from app.contracts.data.errors import DataFailure
from app.contracts.data.models import BrowseReferenceRequest, BrowseReferenceSuccess
from app.services.data.browse_reference.mt4_exporter import (
    export_fxt_file,
    export_hst_file,
)

logger = logging.getLogger(__name__)

_DEFAULT_DB_PATH: Final[Path] = (
    Path(__file__).resolve().parent.parent.parent.parent.parent
    / "data"
    / "database"
    / "haruquantai.db"
)
_DEFAULT_BARS_ROOT: Final[Path] = (
    Path(__file__).resolve().parent.parent.parent.parent.parent
    / "data"
    / "market_data"
    / "bars"
)

_SPIKE_THRESHOLD: Final[float] = 0.015
_FRIDAY_WEEKDAY: Final[int] = 4
_MAX_ANOMALY_DETAILS: Final[int] = 100
_WEEKEND_DAYS: Final[tuple[int, int]] = (6, 0)
_DEFAULT_TF_LIMIT: Final[int] = 5000
_QUALITY_INSPECT_LIMIT: Final[int] = 20000


def _is_bad_ohlc(b: dict[str, Any]) -> bool:
    """Return True if bar has inverted high/low or open/close out of bounds."""
    return bool(
        b["high"] < b["low"]
        or b["open"] > b["high"]
        or b["open"] < b["low"]
        or b["close"] > b["high"]
        or b["close"] < b["low"]
    )


def _is_spike(b: dict[str, Any]) -> tuple[bool, float]:
    """Check if single bar range exceeds spike threshold."""
    bar_range = b["high"] - b["low"]
    if b["close"] > 0 and (bar_range / b["close"]) > _SPIKE_THRESHOLD:
        return True, bar_range
    return False, bar_range


def _is_gap(prev_t: int, curr_t: int, tf_seconds: int) -> bool:
    """Check if gap between bars is an anomaly (not regular weekend)."""
    diff = curr_t - prev_t
    if diff <= tf_seconds * 2:
        return False
    prev_dt = datetime.fromtimestamp(prev_t, tz=UTC)
    curr_dt = datetime.fromtimestamp(curr_t, tz=UTC)
    return not (
        prev_dt.weekday() == _FRIDAY_WEEKDAY and curr_dt.weekday() in _WEEKEND_DAYS
    )


class MarketDataReferenceRepository:
    """Repository handling all market reference database & parquet operations."""

    def __init__(
        self,
        db_path: Path | str | None = None,
        bars_root: Path | str | None = None,
    ) -> None:
        """Initialize the repository.

        Args:
            db_path: Path to haruquantai.db SQLite database.
            bars_root: Path to data/market_data/bars/ root.
        """
        self._db_path = Path(db_path) if db_path else _DEFAULT_DB_PATH
        self._bars_root = Path(bars_root) if bars_root else _DEFAULT_BARS_ROOT

    def _get_connection(self) -> sqlite3.Connection:
        """Open row-factory SQLite connection."""
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        return conn

    # -------------------------------------------------------------------------
    # Series Reference Catalogue
    # -------------------------------------------------------------------------

    def list_series(
        self,
        *,
        limit: int = 200,
        offset: int = 0,
        search: str | None = None,
        source: int | None = None,
        data_type: int | None = None,
        broker_id: int | None = None,
    ) -> list[dict[str, Any]]:
        """List market series records from data table."""
        with self._get_connection() as conn:
            query = """
                SELECT id, source_data_id, connection, symbol, instrument, timeframe,
                       timezone, filename, date_from, date_to, data_type, row_count,
                       decimals, source, seconds_records, usymbol, usymbol_name,
                       remove_weekends, show, basket_id, broker_id
                FROM data
                WHERE 1=1
            """
            params: list[Any] = []
            if search:
                query += " AND (symbol LIKE ? OR instrument LIKE ?)"
                params.extend([f"%{search}%", f"%{search}%"])
            if source is not None:
                query += " AND source = ?"
                params.append(source)
            if data_type is not None:
                query += " AND data_type = ?"
                params.append(data_type)
            if broker_id is not None:
                query += " AND broker_id = ?"
                params.append(broker_id)

            query += " ORDER BY symbol ASC LIMIT ? OFFSET ?"
            params.extend([min(limit, 500), max(offset, 0)])

            cursor = conn.execute(query, params)
            rows = []
            for r in cursor.fetchall():
                d_from = r["date_from"]
                d_to = r["date_to"]
                total_days = None
                if d_from and d_to and d_to > d_from:
                    total_days = round((d_to - d_from) / (86_400 * 1000), 1)

                rows.append(
                    {
                        "series_id": r["id"],
                        "symbol": r["symbol"],
                        "instrument": r["instrument"],
                        "document": r["filename"],
                        "broker_id": r["broker_id"],
                        "usymbol": r["usymbol"],
                        "timeframe": r["timeframe"],
                        "timezone": r["timezone"],
                        "date_from": r["date_from"],
                        "date_to": r["date_to"],
                        "total_days": total_days,
                        "row_count": r["row_count"],
                        "decimals": r["decimals"],
                        "source": r["source"],
                        "bar_type": "start_of_bar",
                        "data_type": r["data_type"],
                        "show": r["show"],
                        "remove_weekends": r["remove_weekends"],
                    }
                )
            return rows

    def get_series(self, series_id: int) -> dict[str, Any] | None:
        """Fetch single series by ID."""
        with self._get_connection() as conn:
            cur = conn.execute("SELECT * FROM data WHERE id = ?", (series_id,))
            r = cur.fetchone()
            if not r:
                return None
            return dict(r)

    def update_series(self, series_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        """Update fields on a market series."""
        with self._get_connection() as conn:
            fields = []
            values = []
            allowed = [
                "symbol",
                "instrument",
                "broker_id",
                "timeframe",
                "timezone",
                "remove_weekends",
                "show",
                "date_from",
                "date_to",
                "row_count",
            ]
            for k in allowed:
                if k in payload:
                    fields.append(f"{k} = ?")
                    values.append(payload[k])

            if fields:
                values.append(series_id)
                set_clause = ", ".join(fields)
                update_sql = (
                    f"UPDATE data SET {set_clause}, "  # noqa: S608 - fields strictly whitelisted above
                    "updated_at = CURRENT_TIMESTAMP WHERE id = ?"
                )
                conn.execute(update_sql, values)
                conn.commit()

            cur = conn.execute("SELECT * FROM data WHERE id = ?", (series_id,))
            row = cur.fetchone()
            return dict(row) if row else {}

    def delete_series(self, series_id: int, delete_files: bool = False) -> bool:
        """Delete a series record and optionally its parquet files."""
        with self._get_connection() as conn:
            cur = conn.execute("SELECT symbol FROM data WHERE id = ?", (series_id,))
            row = cur.fetchone()
            if not row:
                return False
            symbol = row["symbol"]
            conn.execute("DELETE FROM data WHERE id = ?", (series_id,))
            conn.commit()

            if delete_files:
                target_dir = self._bars_root / "dukascopy" / symbol.lower()
                if target_dir.exists():
                    for p in target_dir.glob("*.parquet"):
                        with contextlib.suppress(OSError):
                            p.unlink()

            return True

    # -------------------------------------------------------------------------
    # Instruments & Brokers
    # -------------------------------------------------------------------------

    def list_instruments(self) -> list[dict[str, Any]]:
        """List instrument definitions."""
        with self._get_connection() as conn:
            query = (
                "SELECT name as instrument, description, "
                "currency_margin as broker_profile, "
                "point as point_value, trade_contract_size as contract_size, "
                "trade_tick_size as tick_size, spread as default_spread, "
                "trade_stops_level as default_slippage, category as data_type, "
                "volume_min as order_size_multiplier, "
                "volume_step as order_size_step "
                "FROM instruments ORDER BY name ASC"
            )
            cur = conn.execute(query)
            return [dict(r) for r in cur.fetchall()]

    def list_brokers(self) -> list[dict[str, Any]]:
        """List broker profiles."""
        with self._get_connection() as conn:
            cur = conn.execute(
                """
                SELECT id, name, description, active
                FROM brokers
                ORDER BY name ASC
                """
            )
            return [dict(r) for r in cur.fetchall()]

    # -------------------------------------------------------------------------
    # Parquet Bar Inspection & Resampling
    # -------------------------------------------------------------------------

    def _resolve_parquet_files(
        self,
        symbol: str,
        start: str | None,
        end: str | None,
    ) -> list[Path]:
        """Resolve list of parquet files for symbol and year filters."""
        symbol_lower = symbol.lower()
        target_dir = self._bars_root / "dukascopy" / symbol_lower
        if not target_dir.exists():
            matches = list(self._bars_root.glob(f"**/{symbol_lower}"))
            if not matches:
                return []
            target_dir = matches[0]

        parquet_files = sorted(target_dir.glob("*.parquet"))
        if not parquet_files:
            return []

        files = parquet_files
        if start:
            start_year = start[:4]
            files = [f for f in files if f.stem >= start_year]
        if end:
            end_year = end[:4]
            files = [f for f in files if f.stem <= end_year]

        return files or parquet_files[-3:]

    def _apply_date_filters(
        self,
        lf: pl.LazyFrame,
        start: str | None,
        end: str | None,
    ) -> pl.LazyFrame:
        """Apply start and end ISO datetime filters to LazyFrame."""
        if start:
            with contextlib.suppress(ValueError):
                dt_start = datetime.fromisoformat(start)
                lf = lf.filter(pl.col("datetime") >= dt_start)
        if end:
            with contextlib.suppress(ValueError):
                dt_end = datetime.fromisoformat(end)
                lf = lf.filter(pl.col("datetime") <= dt_end)
        return lf

    def read_bars(
        self,
        symbol: str,
        timeframe: str = "M1",
        start: str | None = None,
        end: str | None = None,
        limit: int = _DEFAULT_TF_LIMIT,
    ) -> list[dict[str, Any]]:
        """Read historical bars from Parquet files resampled to requested timeframe."""
        files_to_read = self._resolve_parquet_files(symbol, start, end)
        if not files_to_read:
            return []

        try:
            lf = pl.concat([pl.scan_parquet(str(f)) for f in files_to_read])
        except OSError, ValueError, pl.exceptions.PolarsError:
            logger.exception("Error reading parquet for %s", symbol)
            return []

        lf = lf.rename(
            {
                "DateTime": "datetime",
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume",
            }
        )
        lf = self._apply_date_filters(lf, start, end)

        tf = timeframe.upper()
        interval_map = {
            "M5": "5m",
            "M15": "15m",
            "M30": "30m",
            "H1": "1h",
            "H4": "4h",
            "D1": "1d",
        }
        if tf in interval_map:
            interval = interval_map[tf]
            lf = (
                lf.sort("datetime")
                .group_by_dynamic("datetime", every=interval)
                .agg(
                    [
                        pl.first("open").alias("open"),
                        pl.max("high").alias("high"),
                        pl.min("low").alias("low"),
                        pl.last("close").alias("close"),
                        pl.sum("volume").alias("volume"),
                    ]
                )
            )

        df = (
            lf.sort("datetime", descending=True).limit(limit).sort("datetime").collect()
        )

        rows = []
        for r in df.iter_rows(named=True):
            dt_val = r["datetime"]
            t_epoch = (
                int(dt_val.timestamp())
                if isinstance(dt_val, datetime)
                else int(dt_val / 1000)
            )
            rows.append(
                {
                    "time": t_epoch,
                    "open": float(r["open"]),
                    "high": float(r["high"]),
                    "low": float(r["low"]),
                    "close": float(r["close"]),
                    "volume": int(r["volume"]),
                }
            )
        return rows

    # -------------------------------------------------------------------------
    # Data Quality Inspection
    # -------------------------------------------------------------------------

    def inspect_quality(self, symbol: str, timeframe: str = "M1") -> dict[str, Any]:
        """Perform gap, spike, and bad OHLC anomaly inspection on parquet data."""
        bars = self.read_bars(symbol, timeframe=timeframe, limit=_QUALITY_INSPECT_LIMIT)
        if not bars:
            return {
                "problems": {
                    "gap": {"count": 0, "percent": "0.00%"},
                    "spike": {"count": 0, "percent": "0.00%"},
                    "ohlc": {"count": 0, "percent": "0.00%"},
                },
                "timeline": [],
                "details": [],
            }

        total_bars = len(bars)
        gaps = 0
        spikes = 0
        bad_ohlc = 0
        details: list[dict[str, Any]] = []
        timeline: list[dict[str, Any]] = []

        tf_seconds_map = {"M5": 300, "H1": 3600, "D1": 86400}
        tf_seconds = tf_seconds_map.get(timeframe, 60)

        for i, b in enumerate(bars):
            t = b["time"]
            dt_str = datetime.fromtimestamp(t, tz=UTC).strftime("%Y-%m-%d %H:%M")
            has_anomaly = False

            if _is_bad_ohlc(b):
                bad_ohlc += 1
                has_anomaly = True
                details.append(
                    {
                        "timestamp": dt_str,
                        "issue": "Bad OHLC",
                        "description": (
                            f"High={b['high']} < Low={b['low']} or price out of bounds"
                        ),
                    }
                )

            is_spike_bar, bar_range = _is_spike(b)
            if is_spike_bar:
                spikes += 1
                has_anomaly = True
                pct = bar_range / b["close"] * 100
                details.append(
                    {
                        "timestamp": dt_str,
                        "issue": "Price Spike",
                        "description": f"Excessive range: {bar_range:.5f} ({pct:.2f}%)",
                    }
                )

            if i > 0 and _is_gap(bars[i - 1]["time"], t, tf_seconds):
                gaps += 1
                has_anomaly = True
                diff = t - bars[i - 1]["time"]
                if len(details) < _MAX_ANOMALY_DETAILS:
                    details.append(
                        {
                            "timestamp": dt_str,
                            "issue": "Missing Bar / Gap",
                            "description": (
                                f"Time gap of {diff // 60} minutes between bars"
                            ),
                        }
                    )

            if has_anomaly and len(timeline) < _MAX_ANOMALY_DETAILS:
                timeline.append({"time": t, "type": details[-1]["issue"]})

        def _pct_fmt(c: int) -> str:
            return f"{(c / total_bars * 100):.2f}%" if total_bars > 0 else "0.00%"

        return {
            "problems": {
                "gap": {"count": gaps, "percent": _pct_fmt(gaps)},
                "spike": {"count": spikes, "percent": _pct_fmt(spikes)},
                "ohlc": {"count": bad_ohlc, "percent": _pct_fmt(bad_ohlc)},
            },
            "total_bars": total_bars,
            "timeline": timeline,
            "details": details[:_MAX_ANOMALY_DETAILS],
        }

    # -------------------------------------------------------------------------
    # Timezone Shift / Cloner
    # -------------------------------------------------------------------------

    def clone_series(
        self,
        symbol: str,
        target_shift_hours: int,
        postfix: str = "_clone",
    ) -> dict[str, Any]:
        """Clone parquet series with a timezone shift in hours."""
        symbol_lower = symbol.lower()
        src_dir = self._bars_root / "dukascopy" / symbol_lower
        if not src_dir.exists():
            return {"error": f"Source directory for {symbol} not found"}

        new_symbol = f"{symbol}{postfix}"
        dst_dir = self._bars_root / "dukascopy" / new_symbol.lower()
        dst_dir.mkdir(parents=True, exist_ok=True)

        parquet_files = list(src_dir.glob("*.parquet"))
        total_copied_rows = 0

        for f in parquet_files:
            df = pl.read_parquet(f)
            shifted_df = df.with_columns(
                pl.col("DateTime") + timedelta(hours=target_shift_hours)
            )
            out_file = dst_dir / f.name
            shifted_df.write_parquet(out_file, compression="zstd", compression_level=6)
            total_copied_rows += len(shifted_df)

        with self._get_connection() as conn:
            src_row = conn.execute(
                "SELECT * FROM data WHERE symbol = ?", (symbol,)
            ).fetchone()
            if src_row:
                conn.execute(
                    """
                    INSERT INTO data (
                        symbol, instrument, timeframe, timezone, filename,
                        date_from, date_to, data_type, row_count, decimals,
                        source, remove_weekends, show
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        new_symbol,
                        src_row["instrument"],
                        src_row["timeframe"],
                        f"UTC{target_shift_hours:+d}",
                        new_symbol,
                        src_row["date_from"],
                        src_row["date_to"],
                        src_row["data_type"],
                        total_copied_rows,
                        src_row["decimals"],
                        src_row["source"],
                        src_row["remove_weekends"],
                        1,
                    ),
                )
                conn.commit()

        return {
            "symbol": new_symbol,
            "rows": total_copied_rows,
            "timezone": f"UTC{target_shift_hours:+d}",
        }

    # -------------------------------------------------------------------------
    # Exporters
    # -------------------------------------------------------------------------

    def export_csv(
        self,
        symbol: str,
        timeframe: str = "M1",
        start: str | None = None,
        end: str | None = None,
        include_header: bool = True,
        separator: str = ",",
    ) -> str:
        """Export bars to CSV formatted string."""
        bars = self.read_bars(
            symbol, timeframe=timeframe, start=start, end=end, limit=50000
        )
        lines = []
        if include_header:
            header_str = separator.join(
                ["<DATE>", "<TIME>", "<OPEN>", "<HIGH>", "<LOW>", "<CLOSE>", "<VOL>"]
            )
            lines.append(header_str)

        for b in bars:
            dt = datetime.fromtimestamp(b["time"], tz=UTC)
            d_str = dt.strftime("%Y.%m.%d")
            t_str = dt.strftime("%H:%M")
            line = separator.join(
                [
                    d_str,
                    t_str,
                    f"{b['open']:.5f}",
                    f"{b['high']:.5f}",
                    f"{b['low']:.5f}",
                    f"{b['close']:.5f}",
                    str(b["volume"]),
                ]
            )
            lines.append(line)

        return "\n".join(lines)

    def export_mt4(
        self,
        symbol: str,
        timeframe: str = "M1",
        target_dir: str | Path | None = None,
        spread: int = 15,
        digits: int = 5,
    ) -> dict[str, Any]:
        """Export bars to MetaTrader 4 HST and FXT files."""
        period_map = {
            "M1": 1,
            "M5": 5,
            "M15": 15,
            "M30": 30,
            "H1": 60,
            "H4": 240,
            "D1": 1440,
        }
        period = period_map.get(timeframe.upper(), 1)
        bars = self.read_bars(symbol, timeframe=timeframe, limit=50000)

        out_dir = Path(target_dir) if target_dir else Path("export")
        out_dir.mkdir(parents=True, exist_ok=True)

        hst_file = out_dir / f"{symbol}{period}.hst"
        fxt_file = out_dir / f"{symbol}{period}_0.fxt"

        hst_count = export_hst_file(hst_file, symbol, period, digits, bars)
        fxt_count = export_fxt_file(
            fxt_file, symbol, period, digits, bars, spread=spread
        )

        return {
            "hst_path": str(hst_file),
            "fxt_path": str(fxt_file),
            "bars_count": hst_count,
            "records_count": fxt_count,
        }

    # -------------------------------------------------------------------------
    # BrowseReferenceCapability Port Adapter
    # -------------------------------------------------------------------------

    def _handle_series_op(
        self, op: str, request: BrowseReferenceRequest
    ) -> BrowseReferenceSuccess | DataFailure | None:
        """Handle series CRUD operations."""
        if op == "LIST_SERIES":
            series_list = self.list_series(
                limit=request.limit or 200,
                search=request.query,
            )
            return BrowseReferenceSuccess(
                request_id=request.request_id, data=cast("JsonValue", series_list)
            )

        if op in ("READ_SERIES", "UPDATE_SERIES", "DELETE_SERIES"):
            return self._handle_single_series_op(op, request)

        return None

    def _handle_single_series_op(
        self, op: str, request: BrowseReferenceRequest
    ) -> BrowseReferenceSuccess | DataFailure:
        """Handle single series read, update, delete operations."""
        raw_id = request.payload.get("series_id")
        s_id = request.series_id or (int(str(raw_id)) if raw_id is not None else None)
        if s_id is None:
            return DataFailure(
                request_id=request.request_id,
                code="DATA_VALIDATION_FAILED",
                problem=ProblemDetails(
                    title="Validation Error",
                    detail="series_id is required",
                    status=400,
                ),
            )
        if op == "READ_SERIES":
            series_data = self.get_series(s_id)
            if series_data is None:
                return DataFailure(
                    request_id=request.request_id,
                    code="DATA_NOT_FOUND",
                    problem=ProblemDetails(
                        title="Not Found",
                        detail=f"Series {s_id} not found",
                        status=404,
                    ),
                )
            return BrowseReferenceSuccess(
                request_id=request.request_id, data=cast("JsonValue", series_data)
            )
        if op == "UPDATE_SERIES":
            updated = self.update_series(s_id, request.payload)
            return BrowseReferenceSuccess(
                request_id=request.request_id, data=cast("JsonValue", updated)
            )
        delete_files = bool(request.payload.get("delete_files", False))
        success = self.delete_series(s_id, delete_files=delete_files)
        return BrowseReferenceSuccess(
            request_id=request.request_id,
            data={"deleted": success, "series_id": s_id},
        )

    def _handle_catalog_op(
        self, op: str, request: BrowseReferenceRequest
    ) -> BrowseReferenceSuccess | None:
        """Handle catalog, instruments, brokers, download config operations."""
        if op == "LIST_INSTRUMENTS":
            return BrowseReferenceSuccess(
                request_id=request.request_id,
                data=cast("JsonValue", self.list_instruments()),
            )
        if op == "LIST_BROKERS":
            return BrowseReferenceSuccess(
                request_id=request.request_id,
                data=cast("JsonValue", self.list_brokers()),
            )
        if op == "DOWNLOAD_CONFIG":
            return BrowseReferenceSuccess(
                request_id=request.request_id,
                data={
                    "available_sources": ["dukascopy"],
                    "default_timeframes": ["M1", "M5", "M15", "H1", "D1"],
                    "timezones": ["UTC", "UTC+1", "UTC+2", "UTC+3", "UTC-5"],
                },
            )
        return None

    def _handle_bars_op(
        self, op: str, request: BrowseReferenceRequest
    ) -> BrowseReferenceSuccess | DataFailure | None:
        """Handle bar retrieval and inspection operations."""
        if op not in ("READ_BARS", "INSPECT_QUALITY"):
            return None
        symbol = request.symbol or ""
        if not symbol:
            return DataFailure(
                request_id=request.request_id,
                code="DATA_VALIDATION_FAILED",
                problem=ProblemDetails(
                    title="Validation Error",
                    detail="symbol is required",
                    status=400,
                ),
            )
        timeframe = request.timeframe or "M1"
        if op == "READ_BARS":
            bars = self.read_bars(
                symbol=symbol,
                timeframe=timeframe,
                start=request.start,
                end=request.end,
                limit=request.limit or _DEFAULT_TF_LIMIT,
            )
            return BrowseReferenceSuccess(
                request_id=request.request_id, data=cast("JsonValue", bars)
            )
        quality = self.inspect_quality(symbol=symbol, timeframe=timeframe)
        return BrowseReferenceSuccess(
            request_id=request.request_id, data=cast("JsonValue", quality)
        )

    def _handle_export_op(
        self, op: str, request: BrowseReferenceRequest
    ) -> BrowseReferenceSuccess | DataFailure | None:
        """Handle data export and cloning operations."""
        if op == "CLONE_SERIES":
            symbol = request.symbol or str(request.payload.get("symbol", ""))
            raw_shift = request.payload.get("target_shift_hours", 0)
            shift_hours = int(str(raw_shift)) if raw_shift is not None else 0
            postfix = str(request.payload.get("postfix", "_clone"))
            cloned = self.clone_series(symbol, shift_hours, postfix)
            return BrowseReferenceSuccess(
                request_id=request.request_id, data=cast("JsonValue", cloned)
            )

        if op == "EXPORT_DATA":
            fmt = str(request.payload.get("format", "csv")).lower()
            symbol = request.symbol or str(request.payload.get("symbol", ""))
            timeframe = request.timeframe or str(request.payload.get("timeframe", "M1"))
            if fmt == "csv":
                content = self.export_csv(
                    symbol,
                    timeframe=timeframe,
                    start=request.start,
                    end=request.end,
                )
                return BrowseReferenceSuccess(
                    request_id=request.request_id,
                    data={
                        "format": "csv",
                        "content": content,
                        "filename": f"{symbol}_{timeframe}.csv",
                    },
                )
            if fmt in ("mt4", "fxt", "hst"):
                res = self.export_mt4(symbol, timeframe=timeframe)
                return BrowseReferenceSuccess(
                    request_id=request.request_id, data=cast("JsonValue", res)
                )
            return DataFailure(
                request_id=request.request_id,
                code="DATA_VALIDATION_FAILED",
                problem=ProblemDetails(
                    title="Unsupported Export Format",
                    detail=f"Format {fmt} is not supported.",
                    status=400,
                ),
            )
        return None

    def _handle_misc_op(
        self, op: str, request: BrowseReferenceRequest
    ) -> BrowseReferenceSuccess | None:
        """Handle batch download and import operations."""
        if op == "DOWNLOAD_DUKASCOPY":
            symbols = list(request.symbols) or (
                [request.symbol] if request.symbol else []
            )
            return BrowseReferenceSuccess(
                request_id=request.request_id,
                data={
                    "status": "QUEUED",
                    "symbols": cast("JsonValue", symbols),
                    "message": f"Queued download for {len(symbols)} symbol(s)",
                },
            )
        if op == "BATCH_ACTION":
            action = str(request.payload.get("action", ""))
            series_ids = request.payload.get("series_ids", [])
            return BrowseReferenceSuccess(
                request_id=request.request_id,
                data={
                    "action": action,
                    "series_ids": series_ids,
                    "status": "COMPLETED",
                },
            )
        if op == "IMPORT_FILE":
            return BrowseReferenceSuccess(
                request_id=request.request_id,
                data={"status": "IMPORTED", "payload": request.payload},
            )
        return None

    async def browse_reference(
        self,
        request: BrowseReferenceRequest,
    ) -> BrowseReferenceSuccess | DataFailure:
        """Route browse reference request to appropriate repository operation."""
        try:
            op = request.operation
            result = (
                self._handle_series_op(op, request)
                or self._handle_catalog_op(op, request)
                or self._handle_bars_op(op, request)
                or self._handle_export_op(op, request)
                or self._handle_misc_op(op, request)
            )
            if result is not None:
                return result

            return DataFailure(
                request_id=request.request_id,
                code="DATA_VALIDATION_FAILED",
                problem=ProblemDetails(
                    title="Unsupported Operation",
                    detail=f"Operation {op} is not supported.",
                    status=400,
                ),
            )

        except Exception as exc:
            logger.exception("Error executing browse_reference %s", request.operation)
            return DataFailure(
                request_id=request.request_id,
                code="DATA_VALIDATION_FAILED",
                problem=ProblemDetails(
                    title="Data Error",
                    detail=str(exc),
                    status=500,
                ),
            )
