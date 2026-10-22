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
    - FR-DATAMGR-DATA-STORAGE: Partitioned Parquet ZSTD [_partition_and_store()].
    - FR-DATAMGR-DATA-READ: Polars & DuckDB queries [Data.read_polars()].
    - FR-DATAMGR-DATA-DELETE: Delete dataset catalog record [Data.delete()].
    - FR-DATAMGR-DATA-CLEAR: Clear historical data [Data.clear()].

Python API Usage:
    ```python
    from app.workspace.data_manager.data import Data, DataCLI

    service = Data()
    service.add("dukascopy", "EURUSD", "M1")
    ```

CLI Usage:
    ```bash
    uv run python -m app.cli -symbol action=list
    uv run python -m app.cli -data action=update symbols=EURUSD
    ```
"""

from __future__ import annotations

import asyncio
import calendar
import contextlib
import inspect
import json
import os
import shutil
from collections.abc import Mapping, Sequence
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
DELETE_FR = "FR-DATAMGR-DATA-DELETE"
CLEAR_FR = "FR-DATAMGR-DATA-CLEAR"

_CONTROL_START = 32
_TEXT_LIMIT = 500

_ALLOWED_EDIT_COLUMNS = frozenset(
    (
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
    )
)

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
    table: str = "datamgr_datasets"
    market_dir: Path = Path("data/market")

    def to_dict(self) -> dict[str, Any]:
        return {"table": self.table, "market_dir": str(self.market_dir)}


def _resolve_tick_size(symbol: str, explicit: float | None = None) -> float:
    if explicit is not None and explicit > 0:
        return float(explicit)
    sym = symbol.upper().strip()
    try:
        rows = HostPersistence.read_records(
            "datamgr_instruments", {"symbol": sym}, limit=1
        )
        if rows and isinstance(rows[0].get("price"), str):
            pdata = json.loads(rows[0]["price"])
            if isinstance(pdata, dict) and float(pdata.get("tick_size", 0)) > 0:
                return float(pdata["tick_size"])
    except KeyError, ValueError, LookupError, OSError:
        pass
    return 0.001 if "JPY" in sym else 0.00001


def _standardize_df_index(df: pd.DataFrame) -> pd.DataFrame:
    clean = df.copy()
    cmap = {str(c).lower(): c for c in clean.columns}
    if not isinstance(clean.index, pd.DatetimeIndex):
        dt_col = cmap.get("datetime") or cmap.get("timestamp")
        clean.index = pd.to_datetime(clean[dt_col] if dt_col else clean.index, utc=True)
    elif clean.index.tz is None:
        clean.index = clean.index.tz_localize("UTC")
    else:
        clean.index = clean.index.tz_convert("UTC")
    return clean


def _format_bars_to_arrow(df: pd.DataFrame, tick_size: float) -> pa.Table:
    if df.empty:
        return pa.Table.from_batches([], schema=M1_ARROW_SCHEMA)
    clean = _standardize_df_index(df)
    cmap = {str(c).lower(): c for c in clean.columns}
    for req in ("open", "high", "low", "close"):
        if req not in cmap:
            raise ValueError(f"Missing required price column '{req}' in bars.")
    dt_s = clean.index.to_series().dt.tz_convert("UTC")
    data: dict[str, Any] = {"DateTime": dt_s}
    for c in ("open", "high", "low", "close"):
        data[c.capitalize()] = (
            (clean[cmap[c]].astype(float) / tick_size).round().astype("int64")
        )
    vol = clean[cmap["volume"]].fillna(0) if "volume" in cmap else 0
    data["Volume"] = (
        pd.Series(vol, index=clean.index).round().clip(lower=0).astype("uint64")
    )
    return pa.table(data, schema=M1_ARROW_SCHEMA)


def _format_ticks_to_arrow(df: pd.DataFrame, tick_size: float) -> pa.Table:
    if df.empty:
        return pa.Table.from_batches([], schema=TICK_ARROW_SCHEMA)
    clean = _standardize_df_index(df)
    cmap = {str(c).lower(): c for c in clean.columns}
    for req in ("bid", "ask"):
        if req not in cmap:
            raise ValueError(f"Missing required price column '{req}' in ticks.")
    dt_s = clean.index.to_series().dt.tz_convert("UTC")
    b = (clean[cmap["bid"]].astype(float) / tick_size).round().astype("int64")
    a = (clean[cmap["ask"]].astype(float) / tick_size).round().astype("int64")
    fl = clean[cmap["flags"]].fillna(0) if "flags" in cmap else 0
    fl_s = pd.Series(fl, index=clean.index).astype("uint16")
    return pa.table(
        {"DateTime": dt_s, "Bid": b, "Ask": a, "Flags": fl_s},
        schema=TICK_ARROW_SCHEMA,
    )


def _write_or_merge_partition(
    part_path: Path,
    new_table: pa.Table,
    mode: str,
    metadata: Mapping[str, str] | None = None,
) -> None:
    part_path.parent.mkdir(parents=True, exist_ok=True)
    table = new_table
    if part_path.exists():
        existing = pq.read_table(part_path)
        if mode == "missing":
            exist_dts = set(existing["DateTime"].to_pylist())
            mask = [dt not in exist_dts for dt in new_table["DateTime"].to_pylist()]
            if not any(mask):
                return
            table = pa.concat_tables(
                [existing, new_table.filter(pa.array(mask, type=pa.bool_()))]
            )
        else:
            new_dts = set(new_table["DateTime"].to_pylist())
            mask = pa.array(
                [dt not in new_dts for dt in existing["DateTime"].to_pylist()],
                type=pa.bool_(),
            )
            table = pa.concat_tables([existing.filter(mask), new_table])
        table = table.take(pc.sort_indices(table["DateTime"]))
    if metadata:
        meta_dict = {
            **(table.schema.metadata or {}),
            **{k.encode(): v.encode() for k, v in metadata.items()},
        }
        table = table.replace_schema_metadata(meta_dict)
    tmp_path = part_path.with_suffix(f".tmp.{os.getpid()}.parquet")
    try:
        pq.write_table(table, tmp_path, compression="zstd", compression_level=6)
        tmp_path.replace(part_path)
    finally:
        if tmp_path.exists():
            with contextlib.suppress(OSError):
                tmp_path.unlink()


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
    meta = {
        "source": src,
        "symbol": sym,
        "timeframe": tf,
        "tick_size": str(unit_scale),
        "compression": "zstd:6",
    }
    s_dir, sym_dir = src.lower().strip(), sym.lower().strip()
    if is_tick:
        for (y, m), sub in clean_df.groupby(
            [clean_df.index.year, clean_df.index.month]
        ):
            m_str = f"{int(m):02d}-{calendar.month_abbr[int(m)].lower()}"
            _write_or_merge_partition(
                base_path / s_dir / "ticks" / sym_dir / str(y) / f"{m_str}.parquet",
                _format_ticks_to_arrow(sub, unit_scale),
                norm_mode,
                metadata=meta,
            )
    else:
        for y, sub in clean_df.groupby(clean_df.index.year):
            _write_or_merge_partition(
                base_path / s_dir / tf.lower().strip() / sym_dir / f"{y}.parquet",
                _format_bars_to_arrow(sub, unit_scale),
                norm_mode,
                metadata=meta,
            )


def _parse_cli_params(
    args: Sequence[str], default_act: str
) -> tuple[str, dict[str, str]]:
    params = dict(a.split("=", 1) for a in args if "=" in a)
    action = params.pop("action", None)
    if action is None:
        pos = [a for a in args if "=" not in a]
        action = pos[0].lower() if pos else default_act
    return action.lower(), params


class _FileClient:
    def __init__(self, filepath: str | Path) -> None:
        self._filepath = filepath

    def get_bars(self, *args: Any, **kwargs: Any) -> pd.DataFrame:
        del args, kwargs
        return pd.read_csv(self._filepath)

    def get_ticks(self, *args: Any, **kwargs: Any) -> pd.DataFrame:
        del args, kwargs
        return pd.read_csv(self._filepath)


class Data:
    """Service implementing dataset management and historical Parquet storage."""

    def __init__(self, config: _Config | None = None) -> None:
        self._config = config or _Config()

    @property
    def market_dir(self) -> Path:
        """Return the root market data storage path."""
        return self._config.market_dir

    def list_datasets(
        self, filters: Mapping[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """List dataset records from catalog matching optional column filters."""
        return HostPersistence.read_records(self._config.table, filters, limit=0)

    def delete(self, dataset_id: str, *, delete_files: bool = True) -> dict[str, Any]:
        """Delete dataset record from catalog and optionally purge parquet files."""
        self._validate_dataset_id(dataset_id)
        row = self._ensure_dataset_exists(dataset_id)
        HostPersistence.delete_record(self._config.table, {"id": dataset_id})
        if delete_files and row.get("path") and Path(row["path"]).exists():
            shutil.rmtree(Path(row["path"]), ignore_errors=True)
        logger.info(
            "%s: Deleted '%s'",
            DELETE_FR,
            dataset_id,
            extra={"fr_id": DELETE_FR, "dataset_id": dataset_id},
        )
        return {"deleted_id": dataset_id, "deleted_count": 1}

    def clear(self, dataset_id: str) -> dict[str, Any]:
        """Clear historical price data files and reset catalog statistics."""
        self._validate_dataset_id(dataset_id)
        row = self._ensure_dataset_exists(dataset_id)
        if row.get("path") and Path(row["path"]).exists():
            shutil.rmtree(Path(row["path"]), ignore_errors=True)
            Path(row["path"]).mkdir(parents=True, exist_ok=True)
        now_iso = datetime.now(UTC).isoformat()
        cleared = {
            "bars": 0,
            "date_from": "",
            "date_to": "",
            "lineage_json": json.dumps({"cleared_at": now_iso}),
            "updated_at": now_iso,
        }
        HostPersistence.update_record(self._config.table, {"id": dataset_id}, cleared)
        logger.info(
            "%s: Cleared '%s'",
            CLEAR_FR,
            dataset_id,
            extra={"fr_id": CLEAR_FR, "dataset_id": dataset_id},
        )
        return {"cleared_id": dataset_id, "bars": 0}

    def add(
        self, source: str, symbol: str, timeframe: str = "M1", **kwargs: Any
    ) -> dict[str, Any]:
        """Register a new data symbol record into the datamgr_datasets table."""
        self._validate_text("source", source)
        self._validate_text("symbol", symbol)
        self._validate_text("timeframe", timeframe)

        src, sym = source.lower().strip(), symbol.upper().strip()
        tf = timeframe.upper().strip()
        is_tick = tf in ("TICK", "TICKS")
        target_id = kwargs.get("dataset_id") or f"{src}:{sym}:{tf}"
        self._validate_dataset_id(target_id)

        if HostPersistence.read_records(self._config.table, {"id": target_id}, limit=1):
            raise ValueError(f"Dataset '{target_id}' already exists in catalog.")

        now_iso = datetime.now(UTC).isoformat()
        sub_dir = "ticks" if is_tick else tf.lower()
        rec = {
            "id": target_id,
            "source": src,
            "symbol": sym,
            "timeframe": tf,
            "underlying": (kwargs.get("underlying") or sym).upper().strip(),
            "instrument": (kwargs.get("instrument") or sym).upper().strip(),
            "broker": (kwargs.get("broker") or src).lower().strip(),
            "broker_name": (kwargs.get("broker_name") or src.title()).strip(),
            "timezone": kwargs.get("timezone", "UTC"),
            "category": kwargs.get("category", "Forex"),
            "date_from": kwargs.get("date_from", ""),
            "date_to": kwargs.get("date_to", ""),
            "bars": max(0, int(kwargs.get("bars", 0))),
            "created_at": now_iso,
            "updated_at": now_iso,
            "path": kwargs.get("path") or f"data/market/{src}/{sub_dir}/{sym.lower()}",
            "data_kind": kwargs.get("data_kind") or ("ticks" if is_tick else "bars"),
            "quality_score": float(kwargs.get("quality_score", 1.0)),
            "lineage_json": json.dumps(dict(kwargs.get("lineage") or {})),
            "schema_version": 1,
        }

        try:
            HostPersistence.create_record(self._config.table, rec)
        except Exception as err:
            logger.exception(
                "%s: Create failed '%s'",
                ADD_FR,
                target_id,
                extra={"fr_id": ADD_FR, "dataset_id": target_id},
            )
            raise RuntimeError(f"Failed to add dataset '{target_id}': {err}") from err

        logger.info(
            "%s: Registered '%s'",
            ADD_FR,
            target_id,
            extra={"fr_id": ADD_FR, "dataset_id": target_id, "symbol": sym},
        )
        return rec

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

        src, sym = source.lower().strip(), symbol.upper().strip()
        tf = timeframe.upper().strip()
        is_tick = tf in ("TICK", "TICKS")
        dataset_id = f"{src}:{sym}:{tf}"
        extra = {"fr_id": IMPORT_FR, "dataset_id": dataset_id, "mode": norm_mode}
        client = broker_client if broker_client is not None else get_broker(src)
        logger.info("%s: Query broker '%s' for '%s'", IMPORT_FR, src, sym, extra=extra)

        df = self._query_broker(
            client, sym=sym, tf=tf, is_tick=is_tick, start=start, end=end, **kwargs
        )
        base_path = Path(base_dir or self._config.market_dir)
        part_root = base_path / src / ("ticks" if is_tick else tf.lower()) / sym.lower()

        if df is None or df.empty:
            logger.warning("%s: No data for '%s'", IMPORT_FR, sym, extra=extra)
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
                "path": part_root.as_posix(),
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

        meta = {
            "underlying": kwargs.get("underlying"),
            "instrument": kwargs.get("instrument"),
            "broker": kwargs.get("broker"),
            "broker_name": kwargs.get("broker_name"),
            "category": kwargs.get("category", "Forex"),
            "is_tick": is_tick,
            "unit_scale": unit_scale,
            "norm_mode": norm_mode,
            "rows": len(df),
        }
        return self._sync_catalog(dataset_id, part_root, src, sym=sym, tf=tf, meta=meta)

    def import_file(
        self,
        filepath: str | Path,
        symbol: str,
        source: str = "file",
        timeframe: str = "M1",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Import price data directly from a local CSV file into Parquet storage."""
        return self.import_data(
            source, symbol, timeframe, broker_client=_FileClient(filepath), **kwargs
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
        if is_tick:
            res = client.get_ticks(sym, start=start, end=end, **kwargs)
        else:
            try:
                tf_enum = Timeframe(tf)
            except ValueError:
                tf_enum = getattr(Timeframe, f"PERIOD_{tf}", Timeframe.PERIOD_M1)
            res = client.get_bars(sym, tf_enum, start=start, end=end, **kwargs)

        async def _resolve(val: Any) -> pd.DataFrame:
            return await val if inspect.isawaitable(val) else val

        return asyncio.run(_resolve(res))

    def _sync_catalog(
        self,
        dataset_id: str,
        part_root: Path,
        src: str,
        *,
        sym: str,
        tf: str,
        meta: Mapping[str, Any],
    ) -> dict[str, Any]:
        pfiles = sorted(part_root.rglob("*.parquet"))
        total_bars: int = 0
        min_dts: list[datetime] = []
        max_dts: list[datetime] = []
        for pf in pfiles:
            p_meta = pq.read_metadata(pf)
            total_bars += p_meta.num_rows
            if p_meta.num_rows > 0:
                ts = pq.read_table(pf, columns=["DateTime"])["DateTime"]
                min_dts.append(ts[0].as_py())
                max_dts.append(ts[-1].as_py())

        d_from = min(min_dts).isoformat() if min_dts else ""
        d_to = max(max_dts).isoformat() if max_dts else ""
        now_iso = datetime.now(UTC).isoformat()
        rel_path = part_root.as_posix()

        row = {
            "source": src,
            "symbol": sym,
            "timeframe": tf,
            "underlying": (meta.get("underlying") or sym).upper().strip(),
            "instrument": (meta.get("instrument") or sym).upper().strip(),
            "broker": (meta.get("broker") or src).lower().strip(),
            "broker_name": (meta.get("broker_name") or src.title()).strip(),
            "timezone": "UTC",
            "category": meta.get("category", "Forex"),
            "date_from": d_from,
            "date_to": d_to,
            "bars": total_bars,
            "path": rel_path,
            "quality_score": 1.0,
            "updated_at": now_iso,
            "data_kind": "ticks" if meta.get("is_tick") else "bars",
            "lineage_json": json.dumps(
                {
                    "tick_size": meta.get("unit_scale", 0.0001),
                    "compression": "zstd:6",
                    "partitions": [p.as_posix() for p in pfiles],
                    "last_mode": meta.get("norm_mode", "overwrite"),
                }
            ),
        }

        if HostPersistence.read_records(
            self._config.table, {"id": dataset_id}, limit=1
        ):
            HostPersistence.update_record(self._config.table, {"id": dataset_id}, row)
        else:
            row.update({"id": dataset_id, "created_at": now_iso, "schema_version": 1})
            HostPersistence.create_record(self._config.table, row)

        rows_imported = int(meta.get("rows", 0))
        logger.info(
            "%s: Ingested %d records into %d partitions for '%s'",
            IMPORT_FR,
            rows_imported,
            len(pfiles),
            dataset_id,
            extra={"fr_id": IMPORT_FR, "dataset_id": dataset_id, "rows": rows_imported},
        )
        return {
            "dataset_id": dataset_id,
            "source": src,
            "symbol": sym,
            "timeframe": tf,
            "mode": meta.get("norm_mode", "overwrite"),
            "rows_imported": rows_imported,
            "total_bars": total_bars,
            "date_from": d_from,
            "date_to": d_to,
            "partitions": [p.as_posix() for p in pfiles],
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
        sub_dir = "ticks" if is_tick else timeframe.lower().strip()
        target_dir = base / source.lower().strip() / sub_dir / symbol.lower().strip()
        if not list(target_dir.rglob("*.parquet")):
            raise FileNotFoundError(
                f"No parquet partitions found for {source}:{symbol}:{timeframe}"
            )
        logger.info(
            "%s: Polars scan for %s",
            READ_FR,
            target_dir.as_posix(),
            extra={"fr_id": READ_FR},
        )
        return pl.scan_parquet(str(target_dir / "**" / "*.parquet"))

    def query_duckdb(self, sql: str) -> Any:
        """Execute analytical DuckDB SQL query directly over Parquet files."""
        logger.info("%s: Executing DuckDB query", READ_FR, extra={"fr_id": READ_FR})
        return duckdb.query(sql)

    def edit(
        self, dataset_id: str, updates: Mapping[str, Any] | None = None, **kwargs: Any
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
            logger.exception(
                "%s: Persistence failed for '%s'", EDIT_FR, dataset_id, extra=extra
            )
            raise RuntimeError(
                f"Failed to update dataset '{dataset_id}': {err}"
            ) from err

        rows = HostPersistence.read_records(
            self._config.table, {"id": dataset_id}, limit=1
        )
        if not rows:
            logger.error(
                "%s: Record missing after update for '%s'",
                EDIT_FR,
                dataset_id,
                extra=extra,
            )
            raise RuntimeError(f"Updated dataset '{dataset_id}' could not be re-read.")

        logger.info("%s: Dataset '%s' updated", EDIT_FR, dataset_id, extra=extra)
        return rows[0]

    def _validate_dataset_id(self, dataset_id: Any) -> None:
        if not isinstance(dataset_id, str):
            raise TypeError("Dataset ID must be a string.")
        if not dataset_id.strip():
            raise ValueError("Dataset ID must be a non-empty string.")
        if any(ord(c) < _CONTROL_START for c in dataset_id):
            raise ValueError("Dataset ID must not contain control characters.")

    def _validate_text(self, field_name: str, value: Any) -> str:
        if not isinstance(value, str):
            raise TypeError(f"Field '{field_name}' must be a string.")
        if not value.strip():
            raise ValueError(f"Field '{field_name}' must be a non-empty string.")
        if any(ord(c) < _CONTROL_START for c in value):
            raise ValueError(f"Field '{field_name}' cannot contain control characters.")
        return value.strip()

    def _ensure_dataset_exists(self, dataset_id: str) -> dict[str, Any]:
        rows = HostPersistence.read_records(
            self._config.table, {"id": dataset_id}, limit=1
        )
        if not rows:
            raise LookupError(f"Dataset '{dataset_id}' not found in catalog.")
        return rows[0]

    def _validate_and_prepare_updates(
        self, dataset_id: str, updates: dict[str, Any]
    ) -> dict[str, Any]:
        if not updates:
            raise ValueError("Updates payload cannot be empty.")
        clean: dict[str, Any] = {}
        for key, val in updates.items():
            if not isinstance(key, str):
                raise TypeError("Update column keys must be strings.")
            if key == "id" and val != dataset_id:
                raise ValueError("Dataset primary key 'id' cannot be modified.")
            if key == "created_at":
                raise ValueError("Field 'created_at' cannot be modified.")
            if key in _ALLOWED_EDIT_COLUMNS:
                clean[key] = self._sanitize_column_value(key, val)
            elif key != "id":
                raise ValueError(f"Unknown or non-editable column: '{key}'")
        if not clean:
            raise ValueError("No editable values provided in updates payload.")
        clean["updated_at"] = datetime.now(UTC).isoformat()
        return clean

    def _sanitize_column_value(self, column: str, value: Any) -> Any:
        if column in ("bars", "schema_version", "quality_score"):
            return self._sanitize_numeric(column, value)
        if column == "lineage_json":
            return self._sanitize_json(column, value)
        return self._sanitize_text_value(column, value)

    def _sanitize_numeric(self, col: str, val: Any) -> Any:
        if isinstance(val, bool) or not isinstance(val, (int, float)):
            raise TypeError(f"Column '{col}' must be a number.")
        if col in ("bars", "schema_version"):
            if not isinstance(val, int):
                raise TypeError(f"Column '{col}' must be a number.")
            if col == "bars" and val < 0:
                raise ValueError(f"Column '{col}' cannot be negative.")
            return val
        f_val = float(val)
        if not 0.0 <= f_val <= 1.0:
            raise ValueError(f"Column '{col}' must be between 0.0 and 1.0.")
        return f_val

    def _sanitize_json(self, col: str, val: Any) -> str:
        if isinstance(val, Mapping):
            return json.dumps(val)
        if isinstance(val, str):
            try:
                json.loads(val)
            except Exception as err:
                raise ValueError(f"Column '{col}' must be valid JSON.") from err
            return val
        raise TypeError(f"Column '{col}' must be JSON string or mapping.")

    def _sanitize_text_value(self, col: str, val: Any) -> str:
        if not isinstance(val, str):
            raise TypeError(f"Column '{col}' must be a string.")
        if len(val) > _TEXT_LIMIT:
            raise ValueError(f"Column '{col}' exceeds length limit of {_TEXT_LIMIT}.")
        if any(ord(c) < _CONTROL_START for c in val):
            raise ValueError(f"Column '{col}' contains control characters.")
        return val


Data.import_ = Data.import_data  # type: ignore[attr-defined]
setattr(Data, "import", Data.import_data)


class DataCLI:
    """Headless CLI formatter and dispatcher for Data and Symbol operations."""

    @classmethod
    def format_output(cls, data: Mapping[str, Any]) -> str:
        """Format dataset record into human-readable terminal output."""
        return "\n".join(f"{k}: {v}" for k, v in sorted(data.items()))

    @staticmethod
    def format_symbols_table(
        rows: Sequence[Mapping[str, Any]], csv: bool = False
    ) -> str:
        """Format symbols/datasets into ASCII table or CSV format."""
        if csv:
            keys = "symbol,source,timeframe,date_from,date_to,bars,path"
            kl = keys.split(",")
            lines = [keys] + [",".join(str(r.get(k, "")) for k in kl) for r in rows]
            return "\n".join(lines)
        cols = [
            ("Symbol", "symbol", 10),
            ("Source", "source", 10),
            ("Timeframe", "timeframe", 10),
            ("From", "date_from", 20),
            ("To", "date_to", 20),
            ("Bars", "bars", 8),
        ]
        hdr = "| " + " | ".join(f"{h:<{w}}" for h, _, w in cols) + " |"
        sep = "|-" + "-|-".join("-" * w for _, _, w in cols) + "-|"
        lines = [f"=== Symbols / Datasets ({len(rows)} items) ===", hdr, sep]
        lines.extend(
            "| " + " | ".join(str(r.get(k, ""))[:w].ljust(w) for _, k, w in cols) + " |"
            for r in rows
        )
        return "\n".join(lines)

    @staticmethod
    def _res(cmd: str, act: str, ren: str, **kw: Any) -> dict[str, Any]:
        return {"command": cmd, "action": act, "rendered": ren, **kw}

    @classmethod
    def dispatch_symbol(cls, args: Sequence[str], service: Data) -> dict[str, Any]:
        """Dispatch headless symbol commands."""
        action, params = _parse_cli_params(args, "list")
        if action == "list":
            rows = service.list_datasets()
            csv_m = params.get("csv", "false").lower() == "true"
            return cls._res(
                "symbol",
                action,
                cls.format_symbols_table(rows, csv=csv_m),
                count=len(rows),
                symbols=rows,
            )
        if action == "add":
            return cls._handle_sym_add(params, service)
        if action == "edit":
            return cls._handle_sym_edit(params, service)
        if action in ("delete", "clear"):
            return cls._mutate_symbols(action, params, service)
        if action == "mt5symbols":
            return cls._res("symbol", action, "MT5 symbols.", symbols=[])
        if action == "darwinexsymbols":
            syms = ["NDXm", "GDAXIm", "SP500", "WS30", "EURUSD", "GBPUSD", "USDJPY"]
            return cls._res("symbol", action, "\n".join(syms), symbols=syms)
        raise ValueError(f"Unsupported symbol action: '{action}'")

    @classmethod
    def _handle_sym_add(cls, p: dict[str, str], s: Data) -> dict[str, Any]:
        s_str = p.get("symbols") or p.get("symbol", "")
        syms = [x.strip() for x in s_str.split(",") if x.strip()]
        if not syms:
            raise ValueError(
                "Parameter 'symbols' or 'symbol' is required for action=add."
            )
        src = p.get("datasource") or p.get("source", "dukascopy")
        tf = p.get("datatype") or p.get("timeframe", "M1")
        added = [
            s.add(
                src,
                sym,
                tf,
                broker=p.get("broker"),
                category=p.get("category", "Forex"),
                timezone=p.get("timezone", "UTC"),
            )
            for sym in syms
        ]
        return cls._res(
            "symbol",
            "add",
            f"Added {len(added)} symbol(s) ({', '.join(syms)}).",
            count=len(added),
            added=added,
        )

    @classmethod
    def _handle_sym_edit(cls, p: dict[str, str], s: Data) -> dict[str, Any]:
        sym = p.get("symbol") or p.get("id")
        if not sym:
            raise ValueError("Parameter 'symbol' is required for action=edit.")
        rows = s.list_datasets({"symbol": sym.upper()})
        ds_id = rows[0]["id"] if rows else sym
        updates = {k: v for k, v in p.items() if k in _ALLOWED_EDIT_COLUMNS}
        updated = s.edit(ds_id, updates)
        return cls._res(
            "symbol", "edit", f"Updated dataset '{ds_id}'.", updated=updated
        )

    @classmethod
    def _mutate_symbols(cls, act: str, p: dict[str, str], s: Data) -> dict[str, Any]:
        s_str = p.get("symbols") or p.get("symbol", "")
        syms = [x.strip() for x in s_str.split(",") if x.strip()]
        if not syms:
            raise ValueError(f"Parameter 'symbols' is required for action={act}.")
        fn = s.delete if act == "delete" else s.clear
        out: list[dict[str, Any]] = []
        for sym in syms:
            rows = s.list_datasets({"symbol": sym.upper()})
            ds_ids = [r["id"] for r in rows] if rows else [sym]
            out.extend(fn(ds_id) for ds_id in ds_ids)
        verb = "Deleted" if act == "delete" else "Cleared"
        return cls._res(
            "symbol",
            act,
            f"{verb} {len(out)} dataset(s).",
            count=len(out),
            **{act: out},
        )

    @classmethod
    def dispatch_data(cls, args: Sequence[str], service: Data) -> dict[str, Any]:
        """Dispatch headless price data commands."""
        action, params = _parse_cli_params(args, "update")
        if action == "list":
            rows = service.list_datasets()
            return cls._res(
                "data",
                "list",
                cls.format_symbols_table(rows),
                count=len(rows),
                datasets=rows,
            )
        if action == "timezones":
            tzs = [
                "UTC",
                "US/Eastern",
                "US/Central",
                "US/Pacific",
                "Europe/London",
                "Europe/Berlin",
                "EET",
                "Asia/Tokyo",
                "Australia/Sydney",
            ]
            return cls._res(
                "data", action, "\n".join(tzs), count=len(tzs), timezones=tzs
            )
        if action == "update":
            return cls._handle_data_update(params, service)
        if action == "import":
            return cls._handle_data_import(params, service)
        raise ValueError(f"Unsupported data action: '{action}'")

    @classmethod
    def _handle_data_update(cls, p: dict[str, str], s: Data) -> dict[str, Any]:
        s_str = p.get("symbols") or p.get("symbol", "")
        raw = [x.strip() for x in s_str.split(",") if x.strip()] if s_str else []
        src = p.get("datasource") or p.get("source", "dukascopy")
        tf = p.get("datatype") or p.get("timeframe", "M1")
        mode = (
            "overwrite"
            if p.get("overwrite", "true").lower() in ("true", "1")
            else "missing"
        )
        start, end = (
            p.get("datefrom") or p.get("date_from"),
            p.get("dateto") or p.get("date_to"),
        )
        if not raw:
            ex = s.list_datasets({"source": src.lower()})
            raw = [e["symbol"] for e in ex] if ex else ["EURUSD"]
        sums = [
            s.import_data(src, sym, tf, start=start, end=end, mode=mode) for sym in raw
        ]
        return cls._res(
            "data",
            "update",
            f"Updated {len(sums)} dataset(s).",
            count=len(sums),
            updates=sums,
        )

    @classmethod
    def _handle_data_import(cls, p: dict[str, str], s: Data) -> dict[str, Any]:
        fp, sym = p.get("filepath") or p.get("file"), p.get("symbol", "IMPORT_SYM")
        src = p.get("datasource") or p.get("source", "file")
        tf = p.get("datatype") or p.get("timeframe", "M1")
        if fp and Path(fp).exists():
            res = s.import_file(fp, sym, source=src, timeframe=tf)
            return cls._res(
                "data",
                "import",
                f"Imported {res.get('rows_imported', 0)} rows for {sym}.",
                import_result=res,
            )
        res = s.import_data(src, sym, tf, mode="overwrite")
        return cls._res(
            "data",
            "import",
            f"Imported data for {sym} from {src}.",
            import_result=res,
        )
