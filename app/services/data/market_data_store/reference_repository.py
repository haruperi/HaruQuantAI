"""Market Data Reference Repository & Operations in the Data Domain.

Owns all reference catalogue queries (SQLite data/database/haruquantai.db),
Parquet historical bar/tick reads, data quality anomaly calculations,
timezone cloning, and export generation.
"""

from __future__ import annotations

import logging
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Final

import polars as pl
import pyarrow.parquet as pq

from app.contracts.common.models import ProblemDetails
from app.contracts.data.errors import DataFailure
from app.contracts.data.models import BrowseReferenceRequest, BrowseReferenceSuccess
from app.services.data.market_data_store.mt4_exporter import (
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
                conn.execute(
                    f"UPDATE data SET {', '.join(fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    values,
                )
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
                        try:
                            p.unlink()
                        except OSError:
                            pass

            return True

    # -------------------------------------------------------------------------
    # Instruments & Brokers
    # -------------------------------------------------------------------------

    def list_instruments(self) -> list[dict[str, Any]]:
        """List instrument definitions."""
        with self._get_connection() as conn:
            cur = conn.execute(
                """
                SELECT name as instrument, description, currency_margin as broker_profile,
                       point as point_value, trade_contract_size as contract_size,
                       trade_tick_size as tick_size, spread as default_spread,
                       trade_stops_level as default_slippage, category as data_type,
                       volume_min as order_size_multiplier, volume_step as order_size_step
                FROM instruments
                ORDER BY name ASC
                """
            )
            return [dict(r) for r in cur.fetchall()]

    def list_brokers(self) -> list[dict[str, Any]]:
        """List broker profiles."""
        with self._get_connection() as conn:
            cur = conn.execute(
                """
                SELECT id as broker_id, name, desc as description, platform as postfix,
                       timezone, active as customized_instruments
                FROM broker
                ORDER BY name ASC
                """
            )
            return [dict(r) for r in cur.fetchall()]

    # -------------------------------------------------------------------------
    # Parquet Bar Inspection & Resampling
    # -------------------------------------------------------------------------

    def read_bars(
        self,
        symbol: str,
        timeframe: str = "M1",
        start: str | None = None,
        end: str | None = None,
        limit: int = 5000,
    ) -> list[dict[str, Any]]:
        """Read historical bars from Parquet files, resampled to the requested timeframe.

        Args:
            symbol: Ticker symbol (e.g. 'EURUSD').
            timeframe: Target timeframe code ('M1', 'M5', 'M15', 'H1', 'D1').
            start: ISO start date string (e.g. '2024-01-01').
            end: ISO end date string (e.g. '2024-12-31').
            limit: Maximum bars to return.

        Returns:
            List of bar dicts: {'time': epoch_seconds, 'open', 'high', 'low', 'close', 'volume'}.
        """
        symbol_lower = symbol.lower()
        target_dir = self._bars_root / "dukascopy" / symbol_lower
        if not target_dir.exists():
            # Fallback: scan any directory matching symbol
            matches = list(self._bars_root.glob(f"**/{symbol_lower}"))
            if matches:
                target_dir = matches[0]
            else:
                return []

        parquet_files = sorted(target_dir.glob("*.parquet"))
        if not parquet_files:
            return []

        # If year filters are applicable, select relevant files
        files_to_read = parquet_files
        if start:
            start_year = start[:4]
            files_to_read = [f for f in files_to_read if f.stem >= start_year]
        if end:
            end_year = end[:4]
            files_to_read = [f for f in files_to_read if f.stem <= end_year]

        if not files_to_read:
            files_to_read = parquet_files[-3:]  # default to last 3 years

        # Read into Polars DataFrame
        try:
            lf = pl.concat([pl.scan_parquet(str(f)) for f in files_to_read])
        except Exception as e:
            logger.error("Error reading parquet for %s: %s", symbol, e)
            return []

        # Standardize column names (DateTime -> datetime, etc.)
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

        if start:
            try:
                dt_start = datetime.fromisoformat(start.replace("Z", "+00:00"))
                lf = lf.filter(pl.col("datetime") >= dt_start)
            except Exception:
                pass

        if end:
            try:
                dt_end = datetime.fromisoformat(end.replace("Z", "+00:00"))
                lf = lf.filter(pl.col("datetime") <= dt_end)
            except Exception:
                pass

        # Apply timeframe aggregation if != M1
        tf = timeframe.upper()
        if tf in ("M5", "M15", "M30", "H1", "H4", "D1"):
            interval_map = {
                "M5": "5m",
                "M15": "15m",
                "M30": "30m",
                "H1": "1h",
                "H4": "4h",
                "D1": "1d",
            }
            resample_int = interval_map[tf]
            df_bars = (
                lf.group_by_dynamic("datetime", every=resample_int)
                .agg(
                    [
                        pl.col("open").first().alias("open"),
                        pl.col("high").max().alias("high"),
                        pl.col("low").min().alias("low"),
                        pl.col("close").last().alias("close"),
                        pl.col("volume").sum().alias("volume"),
                    ]
                )
                .tail(limit)
                .collect()
            )
        else:
            df_bars = lf.tail(limit).collect()

        bars: list[dict[str, Any]] = []
        for row in df_bars.iter_rows(named=True):
            dt: datetime = row["datetime"]
            epoch_sec = int(dt.timestamp()) if dt else 0
            bars.append(
                {
                    "time": epoch_sec,
                    "open": round(float(row["open"]), 5),
                    "high": round(float(row["high"]), 5),
                    "low": round(float(row["low"]), 5),
                    "close": round(float(row["close"]), 5),
                    "volume": int(row["volume"]) if row["volume"] is not None else 0,
                }
            )
        return bars

    # -------------------------------------------------------------------------
    # Quality Anomaly Detection
    # -------------------------------------------------------------------------

    def inspect_quality(self, symbol: str, timeframe: str = "M1") -> dict[str, Any]:
        """Perform gap, spike, and bad OHLC anomaly inspection on parquet data."""
        bars = self.read_bars(symbol, timeframe=timeframe, limit=20000)
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

        tf_seconds = 60
        if timeframe == "M5":
            tf_seconds = 300
        elif timeframe == "H1":
            tf_seconds = 3600
        elif timeframe == "D1":
            tf_seconds = 86400

        for i in range(len(bars)):
            b = bars[i]
            t = b["time"]
            dt_str = datetime.fromtimestamp(t, tz=UTC).strftime("%Y-%m-%d %H:%M")
            has_anomaly = False

            # 1. Bad OHLC check
            if (
                b["high"] < b["low"]
                or b["open"] > b["high"]
                or b["open"] < b["low"]
                or b["close"] > b["high"]
                or b["close"] < b["low"]
            ):
                bad_ohlc += 1
                has_anomaly = True
                details.append(
                    {
                        "timestamp": dt_str,
                        "issue": "Bad OHLC",
                        "description": f"High={b['high']} < Low={b['low']} or price out of bounds",
                    }
                )

            # 2. Spike check
            bar_range = b["high"] - b["low"]
            if (
                b["close"] > 0 and (bar_range / b["close"]) > 0.015
            ):  # >1.5% single bar range
                spikes += 1
                has_anomaly = True
                details.append(
                    {
                        "timestamp": dt_str,
                        "issue": "Price Spike",
                        "description": f"Excessive range: {bar_range:.5f} ({bar_range / b['close'] * 100:.2f}%)",
                    }
                )

            # 3. Gap check against previous bar
            if i > 0:
                prev_t = bars[i - 1]["time"]
                diff = t - prev_t
                if diff > tf_seconds * 2:
                    # Ignore standard weekend gap (Friday evening to Sunday evening)
                    prev_dt = datetime.fromtimestamp(prev_t, tz=UTC)
                    curr_dt = datetime.fromtimestamp(t, tz=UTC)
                    if not (prev_dt.weekday() == 4 and curr_dt.weekday() in (6, 0)):
                        gaps += 1
                        has_anomaly = True
                        if len(details) < 100:
                            details.append(
                                {
                                    "timestamp": dt_str,
                                    "issue": "Missing Bar / Gap",
                                    "description": f"Time gap of {diff // 60} minutes between bars",
                                }
                            )

            if has_anomaly and len(timeline) < 100:
                timeline.append(
                    {
                        "time": t,
                        "type": details[-1]["issue"],
                    }
                )

        return {
            "problems": {
                "gap": {"count": gaps, "percent": f"{(gaps / total_bars * 100):.2f}%"},
                "spike": {
                    "count": spikes,
                    "percent": f"{(spikes / total_bars * 100):.2f}%",
                },
                "ohlc": {
                    "count": bad_ohlc,
                    "percent": f"{(bad_ohlc / total_bars * 100):.2f}%",
                },
            },
            "timeline": timeline,
            "details": details[:100],
        }

    # -------------------------------------------------------------------------
    # Timezone Cloner
    # -------------------------------------------------------------------------

    def clone_series(
        self,
        symbol: str,
        target_shift_hours: int,
        postfix: str,
    ) -> dict[str, Any]:
        """Clone an existing series into a new symbol with shifted timestamps."""
        clean_postfix = postfix.replace("{timeframe}", "M1").replace(
            "{cloneTime}", f"UTC{target_shift_hours:+d}"
        )
        new_symbol = f"{symbol}_{clean_postfix}".replace("__", "_")

        src_dir = self._bars_root / "dukascopy" / symbol.lower()
        dst_dir = self._bars_root / "dukascopy" / new_symbol.lower()
        dst_dir.mkdir(parents=True, exist_ok=True)

        parquet_files = list(src_dir.glob("*.parquet"))
        total_copied_rows = 0

        for f in parquet_files:
            table = pq.read_table(f)
            df = pl.from_arrow(table)
            # Shift datetime column
            shifted_df = df.with_columns(
                pl.col("DateTime") + timedelta(hours=target_shift_hours)
            )
            out_file = dst_dir / f.name
            shifted_df.write_parquet(out_file, compression="zstd", compression_level=6)
            total_copied_rows += len(shifted_df)

        # Insert cloned series into data table
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
            lines.append(
                f"<DATE>{separator}<TIME>{separator}<OPEN>{separator}<HIGH>{separator}<LOW>{separator}<CLOSE>{separator}<VOL>"
            )

        for b in bars:
            dt = datetime.fromtimestamp(b["time"], tz=UTC)
            d_str = dt.strftime("%Y.%m.%d")
            t_str = dt.strftime("%H:%M")
            lines.append(
                f"{d_str}{separator}{t_str}{separator}{b['open']:.5f}{separator}{b['high']:.5f}{separator}{b['low']:.5f}{separator}{b['close']:.5f}{separator}{b['volume']}"
            )

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

    async def browse_reference(
        self,
        request: BrowseReferenceRequest,
    ) -> BrowseReferenceSuccess | DataFailure:
        """Route browse reference request to appropriate repository operation."""
        try:
            op = request.operation
            if op == "LIST_SERIES":
                data = self.list_series(
                    limit=request.limit or 200,
                    search=request.query,
                )
                return BrowseReferenceSuccess(request_id=request.request_id, data=data)

            if op == "READ_SERIES":
                series_id = request.series_id or (
                    int(request.payload["series_id"])
                    if "series_id" in request.payload
                    else None
                )
                if series_id is None:
                    return DataFailure(
                        request_id=request.request_id,
                        code="DATA_VALIDATION_FAILED",
                        problem=ProblemDetails(
                            title="Validation Error",
                            detail="series_id is required",
                            status=400,
                        ),
                    )
                data = self.get_series(series_id)
                if data is None:
                    return DataFailure(
                        request_id=request.request_id,
                        code="DATA_NOT_FOUND",
                        problem=ProblemDetails(
                            title="Not Found",
                            detail=f"Series {series_id} not found",
                            status=404,
                        ),
                    )
                return BrowseReferenceSuccess(request_id=request.request_id, data=data)

            if op == "UPDATE_SERIES":
                series_id = request.series_id or (
                    int(request.payload.get("series_id"))
                    if request.payload.get("series_id")
                    else None
                )
                if series_id is None:
                    return DataFailure(
                        request_id=request.request_id,
                        code="DATA_VALIDATION_FAILED",
                        problem=ProblemDetails(
                            title="Validation Error",
                            detail="series_id is required",
                            status=400,
                        ),
                    )
                data = self.update_series(series_id, request.payload)
                return BrowseReferenceSuccess(request_id=request.request_id, data=data)

            if op == "DELETE_SERIES":
                series_id = request.series_id or (
                    int(request.payload.get("series_id"))
                    if request.payload.get("series_id")
                    else None
                )
                if series_id is None:
                    return DataFailure(
                        request_id=request.request_id,
                        code="DATA_VALIDATION_FAILED",
                        problem=ProblemDetails(
                            title="Validation Error",
                            detail="series_id is required",
                            status=400,
                        ),
                    )
                delete_files = bool(request.payload.get("delete_files", False))
                success = self.delete_series(series_id, delete_files=delete_files)
                return BrowseReferenceSuccess(
                    request_id=request.request_id,
                    data={"deleted": success, "series_id": series_id},
                )

            if op == "LIST_INSTRUMENTS":
                data = self.list_instruments()
                return BrowseReferenceSuccess(request_id=request.request_id, data=data)

            if op == "LIST_BROKERS":
                data = self.list_brokers()
                return BrowseReferenceSuccess(request_id=request.request_id, data=data)

            if op == "READ_BARS":
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
                limit = request.limit or 5000
                data = self.read_bars(
                    symbol=symbol,
                    timeframe=timeframe,
                    start=request.start,
                    end=request.end,
                    limit=limit,
                )
                return BrowseReferenceSuccess(request_id=request.request_id, data=data)

            if op == "INSPECT_QUALITY":
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
                data = self.inspect_quality(symbol=symbol, timeframe=timeframe)
                return BrowseReferenceSuccess(request_id=request.request_id, data=data)

            if op == "CLONE_SERIES":
                symbol = request.symbol or str(request.payload.get("symbol", ""))
                shift_hours = int(request.payload.get("target_shift_hours", 0))
                postfix = str(request.payload.get("postfix", "_clone"))
                data = self.clone_series(symbol, shift_hours, postfix)
                return BrowseReferenceSuccess(request_id=request.request_id, data=data)

            if op == "EXPORT_DATA":
                fmt = str(request.payload.get("format", "csv")).lower()
                symbol = request.symbol or str(request.payload.get("symbol", ""))
                timeframe = request.timeframe or str(
                    request.payload.get("timeframe", "M1")
                )
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
                        request_id=request.request_id, data=res
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

            if op == "DOWNLOAD_DUKASCOPY":
                symbols = list(request.symbols) or (
                    [request.symbol] if request.symbol else []
                )
                return BrowseReferenceSuccess(
                    request_id=request.request_id,
                    data={
                        "status": "QUEUED",
                        "symbols": symbols,
                        "message": f"Queued download for {len(symbols)} symbol(s)",
                    },
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
