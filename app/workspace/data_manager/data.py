"""Data Manager dataset operations, historical Parquet storage, and catalog persistence.

Description:
    Provides dataset mutation, symbol registration, broker market data ingestion,
    canonical partitioned Parquet persistence (Zstandard level 6 compression with
    integer tick price units), Polars lazy scans, and DuckDB analytical querying
    for the Data Manager workspace. Operates on the authoritative datamgr_datasets
    catalog table and data/market partitioned historical storage.

Purpose:
    FEAT-DATAMGR-DATA: Data Manager dataset catalog and historical market data.

Key Capabilities:
    - FR-DATAMGR-DATA-EDIT: Edit dataset values [Data.edit()].
    - FR-DATAMGR-DATA-ADD: Register data symbols [Data.add()].
    - FR-DATAMGR-DATA-IMPORT: Ingest broker price history [Data.import_data()].
    - FR-DATAMGR-DATA-STORAGE: Partitioned Parquet ZSTD [Data._save_partitions()].
    - FR-DATAMGR-DATA-READ: Polars & DuckDB queries [Data.read_polars()].

Python API Usage:
    ```python
    from app.workspace.data_manager.data import Data, DataCLI

    service = Data()
    service.add("dukascopy", "EURUSD", "M1")
    summary = service.import_data("dukascopy", "EURUSD", "M1", mode="overwrite")
    lf = service.read_polars("dukascopy", "EURUSD", "M1")
    ```

CLI Usage:
    ```bash
    uv run python -m app.workspace.data_manager.data
    ```
"""

from __future__ import annotations

import asyncio
import calendar
import contextlib
import inspect
import json
import os
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd  # type: ignore[import-untyped]
import polars as pl
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
from app.host.logging import get_logger
from app.host.persistence import HostPersistence
from app.services.brokers.base import get_broker
from app.services.include.enums import Timeframe

__all__ = ["M1_ARROW_SCHEMA", "TICK_ARROW_SCHEMA", "Data", "DataCLI"]

logger = get_logger(__name__)

EDIT_FR = "FR-DATAMGR-DATA-EDIT"
ADD_FR = "FR-DATAMGR-DATA-ADD"
IMPORT_FR = "FR-DATAMGR-DATA-IMPORT"
STORAGE_FR = "FR-DATAMGR-DATA-STORAGE"
READ_FR = "FR-DATAMGR-DATA-READ"

_CONTROL_START = 32
_TEXT_LIMIT = 500

_ALLOWED_EDIT_COLUMNS = frozenset(
    {
        "source",
        "symbol",
        "underlying",
        "instrument",
        "timeframe",
        "broker",
        "broker_name",
        "timezone",
        "category",
        "date_from",
        "date_to",
        "bars",
        "path",
        "data_kind",
        "quality_score",
        "lineage_json",
        "schema_version",
    }
)

# Canonical historical Parquet schemas
TICK_ARROW_SCHEMA = pa.schema(
    [
        pa.field("DateTime", pa.timestamp("us", tz="UTC")),
        pa.field("Bid", pa.int64()),
        pa.field("Ask", pa.int64()),
        pa.field("Flags", pa.uint16()),
    ]
)

M1_ARROW_SCHEMA = pa.schema(
    [
        pa.field("DateTime", pa.timestamp("us", tz="UTC")),
        pa.field("Open", pa.int64()),
        pa.field("High", pa.int64()),
        pa.field("Low", pa.int64()),
        pa.field("Close", pa.int64()),
        pa.field("Volume", pa.uint64()),
    ]
)


@dataclass(frozen=True)
class _Config:
    """Internal module configuration for Data manager."""

    table: str = "datamgr_datasets"
    market_dir: Path = Path("data/market")

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to standard dictionary."""
        return {"table": self.table, "market_dir": str(self.market_dir)}


def _resolve_tick_size(symbol: str, explicit_tick_size: float | None = None) -> float:
    """Resolve tick size for symbol from explicit argument, DB, or asset defaults."""
    if explicit_tick_size is not None and explicit_tick_size > 0:
        return float(explicit_tick_size)

    sym = symbol.upper().strip()
    try:
        rows = HostPersistence.read_records(
            "datamgr_instruments", {"symbol": sym}, limit=1
        )
        if rows:
            price_val = rows[0].get("price")
            if isinstance(price_val, str) and price_val.strip():
                price_data = json.loads(price_val)
                if isinstance(price_data, dict) and "tick_size" in price_data:
                    ts = float(price_data["tick_size"])
                    if ts > 0:
                        return ts
    except (KeyError, ValueError, LookupError, OSError) as err:
        logger.debug(
            "%s: Instrument tick_size lookup failed for %s: %s",
            STORAGE_FR,
            sym,
            err,
        )

    return 0.001 if "JPY" in sym else 0.00001


def _standardize_df_index(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure DataFrame has a UTC tz-aware DatetimeIndex."""
    clean_df = df.copy()
    col_map = {str(c).lower(): c for c in clean_df.columns}
    if not isinstance(clean_df.index, pd.DatetimeIndex):
        if "datetime" in col_map:
            clean_df.index = pd.to_datetime(clean_df[col_map["datetime"]], utc=True)
        elif "timestamp" in col_map:
            clean_df.index = pd.to_datetime(clean_df[col_map["timestamp"]], utc=True)
        else:
            clean_df.index = pd.to_datetime(clean_df.index, utc=True)
    elif clean_df.index.tz is None:
        clean_df.index = clean_df.index.tz_localize("UTC")
    else:
        clean_df.index = clean_df.index.tz_convert("UTC")
    return clean_df


def _format_bars_to_arrow(df: pd.DataFrame, tick_size: float) -> pa.Table:
    """Format DataFrame of bars to canonical M1 Arrow table with integer tick prices."""
    if df.empty:
        return pa.Table.from_batches([], schema=M1_ARROW_SCHEMA)

    clean_df = _standardize_df_index(df)
    col_map = {str(c).lower(): c for c in clean_df.columns}
    for req in ("open", "high", "low", "close"):
        if req not in col_map:
            raise ValueError(
                f"Missing required price column '{req}' in bars DataFrame."
            )

    dt_series = clean_df.index.to_series().dt.tz_convert("UTC")
    open_ticks = (
        (clean_df[col_map["open"]].astype(float) / tick_size).round().astype("int64")
    )
    high_ticks = (
        (clean_df[col_map["high"]].astype(float) / tick_size).round().astype("int64")
    )
    low_ticks = (
        (clean_df[col_map["low"]].astype(float) / tick_size).round().astype("int64")
    )
    close_ticks = (
        (clean_df[col_map["close"]].astype(float) / tick_size).round().astype("int64")
    )

    if "volume" in col_map:
        vol = (
            clean_df[col_map["volume"]].fillna(0).round().clip(lower=0).astype("uint64")
        )
    else:
        vol = pd.Series(0, index=clean_df.index, dtype="uint64")

    return pa.Table.from_arrays(
        [
            pa.array(dt_series, type=pa.timestamp("us", tz="UTC")),
            pa.array(open_ticks, type=pa.int64()),
            pa.array(high_ticks, type=pa.int64()),
            pa.array(low_ticks, type=pa.int64()),
            pa.array(close_ticks, type=pa.int64()),
            pa.array(vol, type=pa.uint64()),
        ],
        schema=M1_ARROW_SCHEMA,
    )


def _format_ticks_to_arrow(df: pd.DataFrame, tick_size: float) -> pa.Table:
    """Format DataFrame of ticks to canonical Arrow table with integer tick prices."""
    if df.empty:
        return pa.Table.from_batches([], schema=TICK_ARROW_SCHEMA)

    clean_df = _standardize_df_index(df)
    col_map = {str(c).lower(): c for c in clean_df.columns}
    for req in ("bid", "ask"):
        if req not in col_map:
            raise ValueError(
                f"Missing required price column '{req}' in ticks DataFrame."
            )

    dt_series = clean_df.index.to_series().dt.tz_convert("UTC")
    bid_ticks = (
        (clean_df[col_map["bid"]].astype(float) / tick_size).round().astype("int64")
    )
    ask_ticks = (
        (clean_df[col_map["ask"]].astype(float) / tick_size).round().astype("int64")
    )
    if "flags" in col_map:
        flags = clean_df[col_map["flags"]].fillna(0).astype("uint16")
    else:
        flags = pd.Series(0, index=clean_df.index, dtype="uint16")

    return pa.Table.from_arrays(
        [
            pa.array(dt_series, type=pa.timestamp("us", tz="UTC")),
            pa.array(bid_ticks, type=pa.int64()),
            pa.array(ask_ticks, type=pa.int64()),
            pa.array(flags, type=pa.uint16()),
        ],
        schema=TICK_ARROW_SCHEMA,
    )


def _get_m1_partition_path(
    base_dir: Path, source: str, timeframe: str, symbol: str, year: int
) -> Path:
    """Generate partition path for M1 bars: source/timeframe/symbol/year.parquet."""
    return (
        base_dir
        / source.lower().strip()
        / timeframe.lower().strip()
        / symbol.lower().strip()
        / f"{year}.parquet"
    )


def _get_tick_partition_path(
    base_dir: Path, source: str, symbol: str, year: int, month: int
) -> Path:
    """Generate partition path for ticks: source/ticks/symbol/year/month.parquet."""
    month_str = f"{month:02d}-{calendar.month_abbr[month].lower()}"
    return (
        base_dir
        / source.lower().strip()
        / "ticks"
        / symbol.lower().strip()
        / str(year)
        / f"{month_str}.parquet"
    )


def _write_parquet_atomic(
    target_path: Path, table: pa.Table, metadata: Mapping[str, str] | None = None
) -> None:
    """Write table to temporary parquet file with ZSTD lvl 6 then atomically replace."""
    target_path.parent.mkdir(parents=True, exist_ok=True)
    if metadata:
        meta_dict = {
            **(table.schema.metadata or {}),
            **{k.encode("utf-8"): str(v).encode("utf-8") for k, v in metadata.items()},
        }
        table = table.replace_schema_metadata(meta_dict)

    tmp_path = target_path.with_suffix(f".tmp.{os.getpid()}.parquet")
    try:
        pq.write_table(table, tmp_path, compression="zstd", compression_level=6)
        tmp_path.replace(target_path)
    finally:
        if tmp_path.exists():
            with contextlib.suppress(OSError):
                tmp_path.unlink()


def _write_or_merge_partition(
    part_path: Path,
    new_table: pa.Table,
    mode: str,
    metadata: Mapping[str, str] | None = None,
) -> None:
    """Write or merge new table into partition based on overwrite/missing mode."""
    part_path.parent.mkdir(parents=True, exist_ok=True)
    if not part_path.exists():
        _write_parquet_atomic(part_path, new_table, metadata=metadata)
        return

    existing_table = pq.read_table(part_path)
    if mode == "missing":
        existing_dts = set(existing_table["DateTime"].to_pylist())
        mask = [dt not in existing_dts for dt in new_table["DateTime"].to_pylist()]
        if not any(mask):
            return
        filtered_new = new_table.filter(pa.array(mask, type=pa.bool_()))
        combined = pa.concat_tables([existing_table, filtered_new])
        final_table = combined.take(pc.sort_indices(combined["DateTime"]))
        _write_parquet_atomic(part_path, final_table, metadata=metadata)
    else:
        new_dts_set = set(new_table["DateTime"].to_pylist())
        keep_mask = [
            dt not in new_dts_set for dt in existing_table["DateTime"].to_pylist()
        ]
        if any(keep_mask):
            existing_retained = existing_table.filter(
                pa.array(keep_mask, type=pa.bool_())
            )
            combined = pa.concat_tables([existing_retained, new_table])
            final_table = combined.take(pc.sort_indices(combined["DateTime"]))
        else:
            final_table = new_table
        _write_parquet_atomic(part_path, final_table, metadata=metadata)


def _partition_and_store(
    clean_df: pd.DataFrame,
    *,
    is_tick: bool,
    base_path: Path,
    src: str,
    sym: str,
    tf: str,
    unit_scale: float,
    norm_mode: str,
) -> None:
    """Slice DataFrame by date and store partitions in Parquet ZSTD."""
    part_meta = {
        "source": src,
        "symbol": sym,
        "timeframe": tf,
        "tick_size": str(unit_scale),
        "compression": "zstd:6",
    }
    if is_tick:
        for (year, month), sub_df in clean_df.groupby(
            [clean_df.index.year, clean_df.index.month]
        ):
            part_table = _format_ticks_to_arrow(sub_df, unit_scale)
            part_file = _get_tick_partition_path(
                base_path, src, sym, int(year), int(month)
            )
            _write_or_merge_partition(
                part_file, part_table, norm_mode, metadata=part_meta
            )
    else:
        for year, sub_df in clean_df.groupby(clean_df.index.year):
            part_table = _format_bars_to_arrow(sub_df, unit_scale)
            part_file = _get_m1_partition_path(base_path, src, tf, sym, int(year))
            _write_or_merge_partition(
                part_file, part_table, norm_mode, metadata=part_meta
            )


class Data:
    """Service implementing dataset management and historical Parquet storage."""

    def __init__(self, config: _Config | None = None) -> None:
        """Initialize Data service with optional internal configuration."""
        self._config = config or _Config()

    def add(
        self,
        source: str,
        symbol: str,
        timeframe: str = "M1",
        *,
        underlying: str | None = None,
        instrument: str | None = None,
        broker: str | None = None,
        broker_name: str | None = None,
        timezone: str = "UTC",
        category: str = "Forex",
        dataset_id: str | None = None,
        path: str | None = None,
        data_kind: str | None = None,
        quality_score: float = 1.0,
        lineage: Mapping[str, Any] | None = None,
        date_from: str = "",
        date_to: str = "",
        bars: int = 0,
    ) -> dict[str, Any]:
        """Register a new data symbol record into the datamgr_datasets table."""
        self._validate_text("source", source)
        self._validate_text("symbol", symbol)
        self._validate_text("timeframe", timeframe)

        src = source.lower().strip()
        sym = symbol.upper().strip()
        tf = timeframe.upper().strip()
        is_tick = tf in ("TICK", "TICKS")
        kind = data_kind or ("ticks" if is_tick else "bars")
        target_id = dataset_id or f"{src}:{sym}:{tf}"
        self._validate_dataset_id(target_id)

        existing = HostPersistence.read_records(
            self._config.table, {"id": target_id}, limit=1
        )
        if existing:
            raise ValueError(f"Dataset '{target_id}' already exists in catalog.")

        now_iso = datetime.now(UTC).isoformat()
        rel_path = (
            path
            or f"data/market/{src}/{'ticks' if is_tick else tf.lower()}/{sym.lower()}"
        )

        record = {
            "id": target_id,
            "source": src,
            "symbol": sym,
            "underlying": (underlying or sym).upper().strip(),
            "instrument": (instrument or sym).upper().strip(),
            "timeframe": tf,
            "broker": (broker or src).lower().strip(),
            "broker_name": (broker_name or src.title()).strip(),
            "timezone": timezone,
            "category": category,
            "date_from": date_from,
            "date_to": date_to,
            "bars": max(0, int(bars)),
            "created_at": now_iso,
            "updated_at": now_iso,
            "path": rel_path,
            "data_kind": kind,
            "quality_score": float(quality_score),
            "lineage_json": json.dumps(dict(lineage or {})),
            "schema_version": 1,
        }

        try:
            HostPersistence.create_record(self._config.table, record)
        except Exception as err:
            logger.error(  # noqa: TRY400
                "%s: Failed to create dataset '%s': %s",
                ADD_FR,
                target_id,
                err,
                extra={"fr_id": ADD_FR, "dataset_id": target_id},
            )
            raise RuntimeError(f"Failed to add dataset '{target_id}': {err}") from err

        logger.info(
            "%s: Registered dataset '%s' for symbol '%s' (%s)",
            ADD_FR,
            target_id,
            sym,
            tf,
            extra={"fr_id": ADD_FR, "dataset_id": target_id, "symbol": sym},
        )
        return record

    def import_data(
        self,
        source: str,
        symbol: str,
        timeframe: str = "M1",
        start: str | datetime | None = None,
        end: str | datetime | None = None,
        *,
        mode: str = "overwrite",
        tick_size: float | None = None,
        underlying: str | None = None,
        instrument: str | None = None,
        broker: str | None = None,
        broker_name: str | None = None,
        category: str = "Forex",
        broker_client: Any = None,
        base_dir: Path | str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Download and import tick and minute price data from data source."""
        norm_mode = mode.lower().strip()
        if norm_mode not in ("overwrite", "missing"):
            raise ValueError(
                f"Unsupported import mode '{mode}'. Must be 'overwrite' or 'missing'."
            )

        src = source.lower().strip()
        sym = symbol.upper().strip()
        tf = timeframe.upper().strip()
        is_tick = tf in ("TICK", "TICKS")
        dataset_id = f"{src}:{sym}:{tf}"
        extra = {"fr_id": IMPORT_FR, "dataset_id": dataset_id, "mode": norm_mode}

        client = broker_client if broker_client is not None else get_broker(src)
        logger.info(
            "%s: Querying broker '%s' for '%s' (%s, mode=%s)",
            IMPORT_FR,
            src,
            sym,
            tf,
            norm_mode,
            extra=extra,
        )

        df = self._query_broker(
            client,
            sym=sym,
            tf=tf,
            is_tick=is_tick,
            start=start,
            end=end,
            **kwargs,
        )
        base_path = Path(base_dir or self._config.market_dir)
        part_root = base_path / src / ("ticks" if is_tick else tf.lower()) / sym.lower()

        if df is None or df.empty:
            logger.warning(
                "%s: No data returned from broker '%s' for '%s' (%s)",
                IMPORT_FR,
                src,
                sym,
                tf,
                extra=extra,
            )
            return {
                "dataset_id": dataset_id,
                "source": src,
                "symbol": sym,
                "timeframe": tf,
                "mode": norm_mode,
                "rows_imported": 0,
                "total_bars": 0,
                "date_from": "",
                "date_to": "",
                "partitions": [],
                "path": str(part_root.as_posix()),
            }

        unit_scale = _resolve_tick_size(sym, tick_size)
        clean_df = _standardize_df_index(df)
        _partition_and_store(
            clean_df,
            is_tick=is_tick,
            base_path=base_path,
            src=src,
            sym=sym,
            tf=tf,
            unit_scale=unit_scale,
            norm_mode=norm_mode,
        )

        return self._sync_catalog(
            dataset_id,
            part_root,
            src=src,
            sym=sym,
            tf=tf,
            underlying=underlying,
            instrument=instrument,
            broker=broker,
            broker_name=broker_name,
            category=category,
            is_tick=is_tick,
            unit_scale=unit_scale,
            norm_mode=norm_mode,
            imported_rows=len(df),
        )

    def _query_broker(
        self,
        client: Any,
        *,
        sym: str,
        tf: str,
        is_tick: bool,
        start: str | datetime | None,
        end: str | datetime | None,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """Execute market data retrieval against broker backend."""
        if is_tick:
            res = client.get_ticks(sym, start=start, end=end, **kwargs)
        else:
            try:
                tf_enum = Timeframe(tf)
            except ValueError:
                tf_enum = getattr(Timeframe, f"PERIOD_{tf}", Timeframe.PERIOD_M1)
            res = client.get_bars(sym, tf_enum, start=start, end=end, **kwargs)

        async def _resolve(val: Any) -> pd.DataFrame:
            if inspect.isawaitable(val):
                out: pd.DataFrame = await val
                return out
            return val

        return asyncio.run(_resolve(res))

    def _sync_catalog(
        self,
        dataset_id: str,
        part_root: Path,
        *,
        src: str,
        sym: str,
        tf: str,
        underlying: str | None,
        instrument: str | None,
        broker: str | None,
        broker_name: str | None,
        category: str,
        is_tick: bool,
        unit_scale: float,
        norm_mode: str,
        imported_rows: int,
    ) -> dict[str, Any]:
        """Compute statistics across partitions and update datamgr_datasets."""
        partition_files = sorted(part_root.rglob("*.parquet"))
        total_bars = 0
        min_dts: list[datetime] = []
        max_dts: list[datetime] = []

        for pf in partition_files:
            meta = pq.read_metadata(pf)
            total_bars += meta.num_rows
            if meta.num_rows > 0:
                ts_col = pq.read_table(pf, columns=["DateTime"])["DateTime"]
                min_dts.append(ts_col[0].as_py())
                max_dts.append(ts_col[-1].as_py())

        date_from_iso = min(min_dts).isoformat() if min_dts else ""
        date_to_iso = max(max_dts).isoformat() if max_dts else ""
        now_iso = datetime.now(UTC).isoformat()
        rel_path = str(part_root.as_posix())

        existing_record = HostPersistence.read_records(
            self._config.table, {"id": dataset_id}, limit=1
        )
        catalog_row = {
            "source": src,
            "symbol": sym,
            "underlying": (underlying or sym).upper().strip(),
            "instrument": (instrument or sym).upper().strip(),
            "timeframe": tf,
            "broker": (broker or src).lower().strip(),
            "broker_name": (broker_name or src.title()).strip(),
            "timezone": "UTC",
            "category": category,
            "date_from": date_from_iso,
            "date_to": date_to_iso,
            "bars": total_bars,
            "path": rel_path,
            "data_kind": "ticks" if is_tick else "bars",
            "quality_score": 1.0,
            "lineage_json": json.dumps(
                {
                    "tick_size": unit_scale,
                    "compression": "zstd:6",
                    "partitions": [p.as_posix() for p in partition_files],
                    "last_mode": norm_mode,
                }
            ),
            "updated_at": now_iso,
        }

        if existing_record:
            HostPersistence.update_record(
                self._config.table, {"id": dataset_id}, catalog_row
            )
        else:
            catalog_row.update(
                {"id": dataset_id, "created_at": now_iso, "schema_version": 1}
            )
            HostPersistence.create_record(self._config.table, catalog_row)

        logger.info(
            "%s: Ingested %d records into %d partitions for '%s' (mode=%s)",
            IMPORT_FR,
            imported_rows,
            len(partition_files),
            dataset_id,
            norm_mode,
            extra={
                "fr_id": IMPORT_FR,
                "dataset_id": dataset_id,
                "rows": imported_rows,
                "total_bars": total_bars,
            },
        )

        return {
            "dataset_id": dataset_id,
            "source": src,
            "symbol": sym,
            "timeframe": tf,
            "mode": norm_mode,
            "rows_imported": imported_rows,
            "total_bars": total_bars,
            "date_from": date_from_iso,
            "date_to": date_to_iso,
            "partitions": [p.as_posix() for p in partition_files],
            "path": rel_path,
        }

    def read_polars(
        self,
        source: str,
        symbol: str,
        timeframe: str = "M1",
        base_dir: Path | str | None = None,
    ) -> pl.LazyFrame:
        """Return Polars LazyFrame scanning partitioned Parquet storage."""
        base = Path(base_dir or self._config.market_dir)
        is_tick = timeframe.upper() in ("TICK", "TICKS")
        target_dir = (
            base
            / source.lower().strip()
            / ("ticks" if is_tick else timeframe.lower().strip())
            / symbol.lower().strip()
        )
        files = list(target_dir.rglob("*.parquet"))
        if not files:
            raise FileNotFoundError(
                f"No parquet partitions found for {source}:{symbol}:{timeframe} at "
                f"{target_dir}"
            )

        logger.info(
            "%s: Polars scan initialized for %s (%d files)",
            READ_FR,
            target_dir.as_posix(),
            len(files),
            extra={"fr_id": READ_FR, "source": source, "symbol": symbol},
        )
        return pl.scan_parquet(str(target_dir / "**" / "*.parquet"))

    def query_duckdb(self, sql: str) -> Any:
        """Execute analytical DuckDB SQL query directly over Parquet files."""
        logger.info(
            "%s: Executing DuckDB query: %s",
            READ_FR,
            sql[:120],
            extra={"fr_id": READ_FR, "sql": sql[:120]},
        )
        return duckdb.query(sql)

    def edit(
        self,
        dataset_id: str,
        updates: Mapping[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Edit an existing dataset record in the datamgr_datasets table."""
        combined = dict(updates or {})
        combined.update(kwargs)
        extra = {"fr_id": EDIT_FR, "dataset_id": dataset_id}

        try:
            self._validate_dataset_id(dataset_id)
            clean_updates = self._validate_and_prepare_updates(dataset_id, combined)
            self._ensure_dataset_exists(dataset_id)
        except (TypeError, ValueError, LookupError) as err:
            logger.warning("%s: Edit request rejected: %s", EDIT_FR, err, extra=extra)
            raise

        try:
            HostPersistence.update_record(
                self._config.table, {"id": dataset_id}, clean_updates
            )
        except Exception as err:
            logger.error(  # noqa: TRY400
                "%s: Persistence failed: %s", EDIT_FR, err, extra=extra
            )
            raise RuntimeError(
                f"Failed to update dataset '{dataset_id}': {err}"
            ) from err

        rows = HostPersistence.read_records(
            self._config.table, {"id": dataset_id}, limit=1
        )
        if not rows:
            logger.error(
                "%s: Record missing after update: %s",
                EDIT_FR,
                dataset_id,
                extra=extra,
            )
            raise RuntimeError(f"Updated dataset '{dataset_id}' could not be re-read.")

        updated_record = rows[0]
        logger.info(
            "%s: Dataset '%s' updated (%s)",
            EDIT_FR,
            dataset_id,
            ", ".join(sorted(clean_updates.keys())),
            extra={**extra, "updated_fields": sorted(clean_updates.keys())},
        )
        return updated_record

    def _validate_dataset_id(self, dataset_id: Any) -> None:
        """Validate that dataset_id is a valid non-empty string."""
        if not isinstance(dataset_id, str):
            raise TypeError("Dataset ID must be a string.")
        if not dataset_id.strip():
            raise ValueError("Dataset ID must be a non-empty string.")
        if any(ord(c) < _CONTROL_START for c in dataset_id):
            raise ValueError("Dataset ID cannot contain control characters.")

    def _validate_text(self, field_name: str, value: Any) -> str:
        """Validate non-empty string field without control characters."""
        if not isinstance(value, str):
            raise TypeError(f"Field '{field_name}' must be a string.")
        if not value.strip():
            raise ValueError(f"Field '{field_name}' must be a non-empty string.")
        if any(ord(c) < _CONTROL_START for c in value):
            raise ValueError(f"Field '{field_name}' cannot contain control characters.")
        return value.strip()

    def _ensure_dataset_exists(self, dataset_id: str) -> dict[str, Any]:
        """Ensure that dataset exists in catalog and return existing row."""
        rows = HostPersistence.read_records(
            self._config.table, {"id": dataset_id}, limit=1
        )
        if not rows:
            raise LookupError(f"Dataset '{dataset_id}' not found in catalog.")
        return rows[0]

    def _validate_and_prepare_updates(
        self, dataset_id: str, updates: dict[str, Any]
    ) -> dict[str, Any]:
        """Validate updates dictionary and return sanitized persistence dictionary."""
        if not updates:
            raise ValueError("Updates payload cannot be empty.")

        clean: dict[str, Any] = {}
        for key, val in updates.items():
            if not isinstance(key, str):
                raise TypeError("Update column keys must be strings.")
            if key == "id":
                if val != dataset_id:
                    raise ValueError("Dataset primary key 'id' cannot be modified.")
                continue
            if key == "created_at":
                raise ValueError("Field 'created_at' cannot be modified.")
            if key not in _ALLOWED_EDIT_COLUMNS:
                raise ValueError(f"Unknown or non-editable column: '{key}'")
            clean[key] = self._sanitize_column_value(key, val)

        if not clean:
            raise ValueError("No editable values provided in updates payload.")

        clean["updated_at"] = datetime.now(UTC).isoformat()
        return clean

    def _sanitize_column_value(self, column: str, value: Any) -> Any:
        """Validate and cast individual column values according to schema."""
        if column in ("bars", "schema_version", "quality_score"):
            return self._sanitize_numeric(column, value)
        if column == "lineage_json":
            return self._sanitize_json(column, value)
        return self._sanitize_text(column, value)

    def _sanitize_numeric(self, column: str, value: Any) -> int | float:
        """Validate and cast numeric columns."""
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"Column '{column}' must be a number.")

        if column == "bars":
            int_val = int(value)
            if int_val < 0:
                raise ValueError(f"Column '{column}' cannot be negative.")
            return int_val

        if column == "schema_version":
            return int(value)

        float_val = float(value)
        if not (0.0 <= float_val <= 1.0):
            raise ValueError(f"Column '{column}' must be between 0.0 and 1.0.")
        return float_val

    def _sanitize_json(self, column: str, value: Any) -> str:
        """Validate and cast JSON column values."""
        if isinstance(value, Mapping):
            return json.dumps(value)
        if isinstance(value, str):
            try:
                json.loads(value)
            except (ValueError, TypeError) as err:
                raise ValueError(f"Column '{column}' must be valid JSON.") from err
            return value
        raise TypeError(f"Column '{column}' must be JSON string or mapping.")

    def _sanitize_text(self, column: str, value: Any) -> str:
        """Validate string text columns."""
        if not isinstance(value, str):
            raise TypeError(f"Column '{column}' must be a string.")
        if len(value) > _TEXT_LIMIT:
            raise ValueError(
                f"Column '{column}' exceeds length limit of {_TEXT_LIMIT} characters."
            )
        if any(ord(c) < _CONTROL_START for c in value):
            raise ValueError(f"Column '{column}' contains control characters.")
        return value


# Python aliases for import keyword compatibility
Data.import_ = Data.import_data  # type: ignore[attr-defined]
setattr(Data, "import", Data.import_data)


class DataCLI:
    """Headless CLI formatter for Data service."""

    @classmethod
    def format_output(cls, data: Mapping[str, Any]) -> str:
        """Format dataset record into human-readable terminal output."""
        logger.debug("Formatting CLI output (%d keys)", len(data))
        lines = [f"{k}: {v}" for k, v in sorted(data.items())]
        return "\n".join(lines)


if __name__ == "__main__":
    service = Data()
    records = HostPersistence.read_records("datamgr_datasets", limit=1)
    if records:
        target_id = str(records[0]["id"])
        result = service.edit(target_id, {"broker_name": records[0]["broker_name"]})
        print(DataCLI.format_output(result))
    else:
        print("No datasets found in datamgr_datasets.")
