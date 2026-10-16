"""Historical dataset catalog management, partitioned Parquet bar/tick storage.

Description:
    Provides domain logic for dataset catalog records (`datamgr_datasets`),
    partitioned Apache Parquet time-series persistence, chart review slicing,
    interactive bar editing, and multi-platform export (CSV, MetaTrader 4, and
    MetaTrader 5). Unifies historical market data representations under canonical
    `DataInfo` and `ChartDef` without importing `sqlite3`.

Purpose:
    FEAT-DATAMGR-DATA: Historical dataset catalog and Parquet bar/tick lifecycle.

Key Capabilities:
    - FR-DATAMGR-DATA-CHART-DEF: Market data request specification and resample
      compatibility abstraction.
      Associated: `ChartDef`.
      Logging: Zero logging overhead.
    - FR-DATAMGR-DATA-CATALOG-MODEL: Unified historical market dataset catalog
      metadata record and domain abstraction.
      Associated: `DataInfo`.
      Logging: Zero logging overhead.
    - FR-DATAMGR-DATA-CATALOG-CRUD: Manage dataset catalog records in
      `datamgr_datasets`.
      Associated: `DataManagerDataService.list_datasets()`,
      `DataManagerDataService.upsert_dataset()`,
      `DataManagerDataService.delete_dataset()`.
      Logging: Emits INFO on dataset creation, clearing, deletion, and
      mass actions.
    - FR-DATAMGR-DATA-PARQUET-IO: Read and write bar and tick series to
      partitioned Parquet files.
      Associated: `DataManagerDataService.write_bars_dataframe()`,
      `DataManagerDataService.read_bars_dataframe()`.
      Logging: Emits DEBUG on Parquet file I/O with record counts and paths.
    - FR-DATAMGR-DATA-REVIEW-AND-EDIT: Slice chart bars, paginate rows,
      and commit edits.
      Associated: `DataManagerDataService.get_review_chart_bars()`,
      `DataManagerDataService.save_review_changes()`.
      Logging: Emits INFO on manual bar updates and row deletions.
    - FR-DATAMGR-DATA-EXPORT-ENGINE: Manage CSV export formats and export to
      MT4/MT5/CSV.
      Associated: `DataManagerDataService.export_datasets()`,
      `DataManagerDataService.save_csv_format()`.
      Logging: Emits INFO on dataset export with artifact format and count.

Python API Usage:
    ```python
    from app.workspace.data_manager.data import (
        ChartDef,
        DataInfo,
        DataManagerDataService,
    )

    chart = ChartDef(symbol="EURUSD", timeframe="M1")
    info = DataInfo(symbol="EURUSD", timeframe="M1")
    service = DataManagerDataService()
    datasets = service.list_datasets()
    df = service.read_bars_dataframe(datasets[0].id) if datasets else None
    ```

CLI Usage:
    ```bash
    uv run python -m app.workspace.data_manager.data
    ```
"""

from __future__ import annotations

import bisect
import io
import json
import re
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]
from app.host.logging import get_logger
from app.host.persistence.create import create_schema, insert_row
from app.host.persistence.delete import delete_row_by_pk, delete_rows
from app.host.persistence.read import read_rows, resolve_connection
from app.host.persistence.update import update_row_by_pk

from ._common import ChartDef, DataInfo
from .log import DataManagerLogService

__all__ = [
    "ChartBarSlice",
    "ChartDef",
    "DataInfo",
    "DataManagerDataService",
    "ExportArtifactResult",
]

logger = get_logger(__name__)

CHART_DEF_FR = "FR-DATAMGR-DATA-CHART-DEF"
CATALOG_MODEL_FR = "FR-DATAMGR-DATA-CATALOG-MODEL"
CATALOG_CRUD_FR = "FR-DATAMGR-DATA-CATALOG-CRUD"
PARQUET_IO_FR = "FR-DATAMGR-DATA-PARQUET-IO"
REVIEW_EDIT_FR = "FR-DATAMGR-DATA-REVIEW-AND-EDIT"
EXPORT_ENGINE_FR = "FR-DATAMGR-DATA-EXPORT-ENGINE"


@dataclass(frozen=True)
class ChartBarSlice:
    """Represents a lightweight OHLCV bar for chart rendering."""

    time: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    spread: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert chart bar to dictionary representation."""
        return {
            "time": self.time,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "spread": self.spread,
        }


@dataclass(frozen=True)
class ExportArtifactResult:
    """Represents an exported file artifact."""

    target_id: str
    symbol: str
    format: str
    filename: str
    rows_exported: int
    content: str
    output_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert export result to dictionary representation."""
        return {
            "target_id": self.target_id,
            "symbol": self.symbol,
            "format": self.format,
            "filename": self.filename,
            "rows_exported": self.rows_exported,
            "content": self.content,
            "output_path": self.output_path,
        }


def _slugify(name: str) -> str:
    """Sanitize directory names for partition paths."""
    clean = re.sub(r"[^A-Za-z0-9_.-]", "_", name)
    return clean.strip("_") or "default"


def _prepare_tick_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Validate and normalize tick time-series columns."""
    clean_df = df.copy()
    if "bid" not in clean_df.columns or "ask" not in clean_df.columns:
        msg = "Tick dataset requires 'bid' and 'ask' price columns"
        raise ValueError(msg)
    for col in ("bid", "ask"):
        clean_df[col] = clean_df[col].astype(float)
        if (clean_df[col] <= 0).any():
            msg = f"Non-positive price found in tick column '{col}'"
            raise ValueError(msg)
    if "volume" not in clean_df.columns:
        clean_df["volume"] = 1.0
    clean_df["volume"] = clean_df["volume"].astype(float)
    if "spread" not in clean_df.columns:
        clean_df["spread"] = (clean_df["ask"] - clean_df["bid"]).fillna(0.0)
    clean_df["spread"] = clean_df["spread"].astype(float)
    return clean_df


def _prepare_bar_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Validate and normalize OHLCV bar time-series columns."""
    clean_df = df.copy()
    required_cols = ("open", "high", "low", "close")
    missing = [c for c in required_cols if c not in clean_df.columns]
    if missing:
        msg = f"Bar dataset missing required columns: {missing}"
        raise ValueError(msg)
    for col in ("open", "high", "low", "close"):
        clean_df[col] = clean_df[col].astype(float)
    if "volume" not in clean_df.columns:
        clean_df["volume"] = 0.0
    clean_df["volume"] = clean_df["volume"].astype(float)
    if "spread" not in clean_df.columns:
        clean_df["spread"] = 0.0
    clean_df["spread"] = clean_df["spread"].astype(float)
    return clean_df


def _ensure_timestamp_column(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure timestamp column exists and is sorted."""
    clean_df = df.copy()
    if "timestamp" not in clean_df.columns:
        if clean_df.index.name == "timestamp" or isinstance(
            clean_df.index, pd.DatetimeIndex
        ):
            clean_df = clean_df.reset_index()
        else:
            now_utc = datetime.now(UTC)
            clean_df["timestamp"] = [
                (now_utc + timedelta(minutes=i)).strftime("%Y-%m-%d %H:%M:%S")
                for i in range(len(clean_df))
            ]
    clean_df["timestamp"] = clean_df["timestamp"].astype(str)
    return clean_df


def _format_mt4(df: pd.DataFrame, decimals: int) -> str:
    """Format DataFrame as MT4 CSV text."""
    lines: list[str] = []
    for _, r in df.iterrows():
        ts_val = str(r["timestamp"])
        date_part, time_part = (
            ts_val.split(" ") if " " in ts_val else (ts_val[:10], ts_val[11:16])
        )
        date_clean = date_part.replace("-", ".")
        lines.append(
            f"{date_clean},{time_part},{r['open']:.{decimals}f},"
            f"{r['high']:.{decimals}f},{r['low']:.{decimals}f},"
            f"{r['close']:.{decimals}f},{int(r['volume'])}"
        )
    return "\n".join(lines)


def _format_mt5(df: pd.DataFrame, decimals: int) -> str:
    """Format DataFrame as MT5 tab-delimited text."""
    lines = [
        "<DATE>\t<TIME>\t<OPEN>\t<HIGH>\t<LOW>\t<CLOSE>\t<TICKVOL>\t<VOL>\t<SPREAD>"
    ]
    for _, r in df.iterrows():
        ts_val = str(r["timestamp"])
        date_part, time_part = (
            ts_val.split(" ") if " " in ts_val else (ts_val[:10], ts_val[11:19])
        )
        date_clean = date_part.replace("-", ".")
        lines.append(
            f"{date_clean}\t{time_part}\t{r['open']:.{decimals}f}\t"
            f"{r['high']:.{decimals}f}\t{r['low']:.{decimals}f}\t"
            f"{r['close']:.{decimals}f}\t{int(r['volume'])}\t"
            f"{int(r['volume'])}\t{int(r.get('spread', 0))}"
        )
    return "\n".join(lines)


def _format_series(df: pd.DataFrame) -> str:
    """Format DataFrame as JSON series array."""
    series_data = [
        {
            "datetime": str(r["timestamp"]),
            "open": float(r["open"]),
            "high": float(r["high"]),
            "low": float(r["low"]),
            "close": float(r["close"]),
            "volume": float(r["volume"]),
        }
        for _, r in df.iterrows()
    ]
    return json.dumps(series_data)


def _format_standard_csv(df: pd.DataFrame, decimals: int) -> str:
    """Format DataFrame as standard CSV text."""
    lines = ["DateTime,Open,High,Low,Close,Volume,Spread"]
    for _, r in df.iterrows():
        spr = r.get("spread", 0.0)
        lines.append(
            f"{r['timestamp']},{r['open']:.{decimals}f},"
            f"{r['high']:.{decimals}f},{r['low']:.{decimals}f},"
            f"{r['close']:.{decimals}f},{r['volume']:.2f},"
            f"{spr}"
        )
    return "\n".join(lines)


def _export_single_dataset(
    *,
    rec: DataInfo | None,
    tid: str,
    df: pd.DataFrame,
    export_format: str,
    decimals: int,
    date_from: Any,
    date_to: Any,
) -> ExportArtifactResult | None:
    """Filter and serialize a single dataset to requested format."""
    if df.empty:
        return None
    filtered_df = df
    if date_from:
        filtered_df = filtered_df[filtered_df["timestamp"] >= str(date_from)]
    if date_to:
        filtered_df = filtered_df[filtered_df["timestamp"] <= str(date_to)]
    if filtered_df.empty:
        return None

    symbol = rec.symbol if rec else tid.rsplit(":", maxsplit=1)[-1]
    tf = rec.timeframe if rec else "M1"
    if export_format == "MT4":
        content = _format_mt4(filtered_df, decimals)
        filename = f"{symbol}_{tf}.csv"
    elif export_format == "MT5":
        content = _format_mt5(filtered_df, decimals)
        filename = f"{symbol}_{tf}_MT5.txt"
    elif export_format == "SERIES":
        content = _format_series(filtered_df)
        filename = f"{symbol}_{tf}_series.json"
    else:
        content = _format_standard_csv(filtered_df, decimals)
        filename = f"{symbol}_{tf}.csv"

    return ExportArtifactResult(
        target_id=str(rec.id) if rec else tid,
        symbol=symbol,
        format=export_format,
        filename=filename,
        rows_exported=len(filtered_df),
        content=content,
    )


class DataManagerDataService:
    """Service governing dataset catalog CRUD, Parquet storage, and export."""

    def __init__(
        self,
        db_path: Path | str | None = None,
        data_dir: Path | str | None = None,
        log_service: DataManagerLogService | None = None,
    ) -> None:
        """Initialize data service with database path, data dir, and log service."""
        self.db_path = Path(db_path) if db_path is not None else None
        self.data_dir = Path(data_dir) if data_dir is not None else Path("data")
        self.log_service = log_service

    def parquet_path_for(
        self,
        dataset_id: str,
        source: str = "file",
        symbol: str = "",
        timeframe: str = "M1",
    ) -> Path:
        """Derive the partitioned Parquet file path for a dataset."""
        s_slug = _slugify(source)
        sym_slug = _slugify(symbol or dataset_id.rsplit(":", maxsplit=1)[-1])
        tf_slug = _slugify(timeframe)
        id_slug = _slugify(dataset_id)
        base = (self.data_dir / "history").resolve()
        path = (base / s_slug / sym_slug / f"{tf_slug}_{id_slug}.parquet").resolve()
        if not path.is_relative_to(base):
            msg = f"Path traversal detected for dataset '{dataset_id}'"
            raise ValueError(msg)
        return path

    def _safe_resolve_parquet_path(self, path_str: str) -> Path:
        """Resolve and validate that a path is contained within data_dir."""
        base = self.data_dir.resolve()
        resolved = Path(path_str).resolve()
        if not resolved.is_relative_to(base):
            msg = f"Security error: path {resolved} traverses outside {base}"
            raise ValueError(msg)
        return resolved

    def invalidate_quality_report(self, dataset_id: str) -> None:
        """Invalidate cached quality report for a dataset and reset score."""
        with resolve_connection(self.db_path) as conn:
            delete_rows(conn, "datamgr_quality", where={"dataset_id": dataset_id})
            update_row_by_pk(
                conn,
                "datamgr_datasets",
                {"id": dataset_id},
                {"quality_score": 0.0},
            )

    def list_datasets(
        self,
        source: str | None = None,
        symbol: str | None = None,
    ) -> list[DataInfo]:
        """List dataset catalog records matching optional filters."""
        where: dict[str, Any] = {}
        if source:
            where["source"] = source.strip()
        if symbol:
            where["symbol"] = symbol.strip().upper()

        with resolve_connection(self.db_path) as conn:
            rows = read_rows(
                conn,
                "datamgr_datasets",
                where=where or None,
                order_by="symbol ASC",
            )
        return [DataInfo.from_row(r) for r in rows]

    def get_dataset(self, dataset_id: str) -> DataInfo | None:
        """Retrieve a dataset catalog record by its unique ID."""
        clean = dataset_id.strip()
        with resolve_connection(self.db_path) as conn:
            rows = read_rows(
                conn,
                "datamgr_datasets",
                where={"id": clean},
                limit=1,
            )
        if not rows:
            return None
        return DataInfo.from_row(rows[0])

    def upsert_dataset(
        self,
        payload: Mapping[str, Any],
        bars_df: pd.DataFrame | None = None,
    ) -> DataInfo:
        """Create or update a dataset catalog record."""
        clean_id = str(payload.get("id", "")).strip()
        symbol = str(payload.get("symbol", clean_id.split(":")[-1])).strip().upper()
        if not clean_id:
            source = str(payload.get("source", "file")).strip()
            clean_id = f"{source}:{symbol}"

        now_iso = datetime.now(UTC).isoformat()
        canonical_path = self.parquet_path_for(
            clean_id,
            str(payload.get("source", "file")),
            symbol,
            str(payload.get("timeframe", "M1")),
        )
        caller_path = payload.get("path")
        if caller_path:
            resolved_caller = self._safe_resolve_parquet_path(str(caller_path))
            chosen_path = str(resolved_caller)
        else:
            chosen_path = str(canonical_path)

        row_data: dict[str, Any] = {
            "id": clean_id,
            "source": str(payload.get("source", "file")),
            "symbol": symbol,
            "underlying": str(payload.get("underlying", symbol)),
            "instrument": str(payload.get("instrument", symbol)),
            "timeframe": str(payload.get("timeframe", "M1")),
            "broker": str(payload.get("broker", "Default")),
            "broker_name": str(payload.get("broker_name", "Default")),
            "timezone": str(payload.get("timezone", "UTC")),
            "category": str(payload.get("category", "Forex")),
            "date_from": str(payload.get("date_from", "")),
            "date_to": str(payload.get("date_to", "")),
            "bars": int(payload.get("bars", 0)),
            "created_at": str(payload.get("created_at", now_iso)),
            "updated_at": now_iso,
            "path": chosen_path,
            "data_kind": str(payload.get("data_kind", "bars")),
            "quality_score": float(payload.get("quality_score", 1.0)),
        }

        existing = self.get_dataset(clean_id)
        with resolve_connection(self.db_path) as conn:
            if existing is not None:
                update_row_by_pk(conn, "datamgr_datasets", {"id": clean_id}, row_data)
            else:
                insert_row(conn, "datamgr_datasets", row_data)

        rec = DataInfo.from_row(row_data)
        logger.info(
            "%s: Upserted dataset id=%s symbol=%s bars=%d",
            CATALOG_CRUD_FR,
            rec.id,
            rec.symbol,
            rec.bars,
            extra={
                "fr_id": CATALOG_CRUD_FR,
                "dataset_id": rec.id,
                "symbol": rec.symbol,
                "bars": rec.bars,
            },
        )

        if bars_df is not None and not bars_df.empty:
            return self.write_bars_dataframe(str(rec.id), bars_df)

        return rec

    def update_dataset(self, dataset_id: str, updates: Mapping[str, Any]) -> DataInfo:
        """Update fields of an existing dataset record."""
        existing = self.get_dataset(dataset_id)
        if existing is None:
            raise KeyError(f"Dataset '{dataset_id}' not found.")

        data = existing.to_dict()
        data.update(updates)
        return self.upsert_dataset(data)

    def write_bars_dataframe(self, dataset_id: str, df: pd.DataFrame) -> DataInfo:
        """Persist sorted OHLCV bars or ticks DataFrame to Parquet."""
        rec = self.get_dataset(dataset_id)
        if rec is None:
            rec = self.upsert_dataset({"id": dataset_id})

        pq_path = self._safe_resolve_parquet_path(rec.path)
        pq_path.parent.mkdir(parents=True, exist_ok=True)

        clean_df = _ensure_timestamp_column(df)
        is_tick = rec.data_kind == "ticks" or (
            "bid" in clean_df.columns
            and "ask" in clean_df.columns
            and "open" not in clean_df.columns
        )
        clean_df = (
            _prepare_tick_dataframe(clean_df)
            if is_tick
            else _prepare_bar_dataframe(clean_df)
        )

        clean_df.to_parquet(pq_path, index=False)

        bars_count = len(clean_df)
        date_from = str(clean_df["timestamp"].iloc[0]) if bars_count > 0 else ""
        date_to = str(clean_df["timestamp"].iloc[-1]) if bars_count > 0 else ""

        self.invalidate_quality_report(dataset_id)

        updated = self.update_dataset(
            dataset_id,
            {
                "bars": bars_count,
                "date_from": date_from,
                "date_to": date_to,
                "path": str(pq_path),
                "data_kind": "ticks" if is_tick else "bars",
            },
        )
        logger.debug(
            "%s: Wrote %d bars to %s for dataset %s",
            PARQUET_IO_FR,
            bars_count,
            pq_path,
            dataset_id,
            extra={
                "fr_id": PARQUET_IO_FR,
                "bars": bars_count,
                "path": str(pq_path),
                "dataset_id": dataset_id,
            },
        )
        return updated

    def read_bars_dataframe(self, dataset_id: str) -> pd.DataFrame:
        """Read historical bars from Parquet or return empty DataFrame."""
        rec = self.get_dataset(dataset_id)
        raw_path = (
            rec.path if rec and rec.path else str(self.parquet_path_for(dataset_id))
        )
        pq_path = self._safe_resolve_parquet_path(raw_path)

        if pq_path.is_file():
            df = pd.read_parquet(pq_path)
            logger.debug(
                "%s: Read %d bars from %s",
                PARQUET_IO_FR,
                len(df),
                pq_path,
                extra={"fr_id": PARQUET_IO_FR, "bars": len(df)},
            )
            return df

        logger.debug(
            "%s: No physical parquet file for %s at %s; returning empty DataFrame",
            PARQUET_IO_FR,
            dataset_id,
            pq_path,
            extra={"fr_id": PARQUET_IO_FR, "dataset_id": dataset_id},
        )
        return pd.DataFrame()

    def import_dataset(self, payload: Mapping[str, Any]) -> DataInfo:
        """Import historical dataset from CSV text or synthetic generation."""
        symbol = str(payload.get("symbol", "EURUSD")).strip().upper()
        source = str(payload.get("source", "file")).strip()
        timeframe = str(payload.get("timeframe", "M1")).strip()
        dataset_id = str(payload.get("id") or f"{source}:{symbol}")

        csv_content = payload.get("csv_content") or payload.get("data")
        if isinstance(csv_content, str) and csv_content.strip():
            df = pd.read_csv(io.StringIO(csv_content))
            # Standardize columns
            col_map = {c.lower(): c for c in df.columns}
            rename_dict: dict[str, str] = {}
            for col in (
                "timestamp",
                "datetime",
                "time",
                "date",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "spread",
            ):
                if col in col_map:
                    target = "timestamp" if col in ("datetime", "time", "date") else col
                    rename_dict[col_map[col]] = target
            df = df.rename(columns=rename_dict)
        else:
            df = self.read_bars_dataframe(dataset_id)

        rec = self.upsert_dataset(
            {
                "id": dataset_id,
                "source": source,
                "symbol": symbol,
                "timeframe": timeframe,
                "category": str(payload.get("category", "Forex")),
                "timezone": str(payload.get("timezone", "UTC")),
            },
            bars_df=df if not df.empty else None,
        )

        if self.log_service:
            self.log_service.append_log(
                action="IMPORT",
                message=f"Imported {rec.bars} bars for {rec.symbol} ({rec.timeframe})",
                symbol=rec.symbol,
                details={"bars": rec.bars, "dataset_id": rec.id},
            )
            self.log_service.record_operation(
                symbol=rec.symbol,
                operation="IMPORT",
                status="SUCCESS",
                message="Dataset imported",
                rows_affected=rec.bars,
            )

        logger.info(
            "%s: Imported dataset id=%s symbol=%s bars=%d",
            CATALOG_CRUD_FR,
            rec.id,
            rec.symbol,
            rec.bars,
            extra={
                "fr_id": CATALOG_CRUD_FR,
                "dataset_id": rec.id,
                "bars": rec.bars,
            },
        )
        return rec

    def clear_dataset(self, dataset_id: str) -> dict[str, Any]:
        """Clear all historical bars for a dataset, resetting counters to 0."""
        rec = self.get_dataset(dataset_id)
        if rec and rec.path:
            pq_file = self._safe_resolve_parquet_path(rec.path)
            if pq_file.is_file():
                try:
                    pq_file.unlink(missing_ok=True)
                except OSError:
                    logger.exception(
                        "%s: Failed to unlink parquet file %s",
                        CATALOG_CRUD_FR,
                        pq_file,
                    )
                    raise

        self.invalidate_quality_report(dataset_id)
        self.update_dataset(
            dataset_id,
            {
                "bars": 0,
                "date_from": "",
                "date_to": "",
            },
        )
        if self.log_service and rec:
            self.log_service.append_log(
                action="CLEAR",
                message=f"Cleared historical bars for {rec.symbol}",
                symbol=rec.symbol,
            )

        logger.info(
            "%s: Cleared dataset id=%s",
            CATALOG_CRUD_FR,
            dataset_id,
            extra={"fr_id": CATALOG_CRUD_FR, "dataset_id": dataset_id},
        )
        return {"id": dataset_id, "cleared": True}

    def delete_dataset(self, dataset_id: str) -> dict[str, Any]:
        """Delete dataset catalog record and physical Parquet files."""
        rec = self.get_dataset(dataset_id)
        if rec and rec.path:
            pq_file = self._safe_resolve_parquet_path(rec.path)
            if pq_file.is_file():
                try:
                    pq_file.unlink(missing_ok=True)
                except OSError:
                    logger.exception(
                        "%s: Failed to unlink parquet file %s",
                        CATALOG_CRUD_FR,
                        pq_file,
                    )
                    raise

        self.invalidate_quality_report(dataset_id)
        with resolve_connection(self.db_path) as conn:
            delete_row_by_pk(conn, "datamgr_datasets", {"id": dataset_id})

        if self.log_service and rec:
            self.log_service.append_log(
                action="DELETE",
                message=f"Deleted dataset {rec.id}",
                symbol=rec.symbol,
            )

        logger.info(
            "%s: Deleted dataset id=%s",
            CATALOG_CRUD_FR,
            dataset_id,
            extra={"fr_id": CATALOG_CRUD_FR, "dataset_id": dataset_id},
        )
        return {"id": dataset_id, "deleted": True}

    def mass_delete_datasets(
        self,
        dataset_ids: Sequence[str],
        action: str = "remove",
        force: bool = False,
    ) -> dict[str, Any]:
        """Clear or delete multiple datasets in batch."""
        _ = force
        act = action.strip().lower()
        count = 0
        for did in dataset_ids:
            if act == "clear":
                self.clear_dataset(did)
                count += 1
            else:
                self.delete_dataset(did)
                count += 1

        logger.info(
            "%s: Mass-action %s on %d datasets",
            CATALOG_CRUD_FR,
            act,
            count,
            extra={"fr_id": CATALOG_CRUD_FR, "action": act, "count": count},
        )
        return {
            "affected_count": count,
            "action": act,
            "dataset_ids": list(dataset_ids),
        }

    def get_review_chart_bars(
        self,
        symbol: str,
        timeframe: str = "M1",
        max_bars: int = 250,
        *,
        dataset_id: str | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Retrieve recent chart bars for interactive chart review."""
        effective_limit = limit if limit is not None else max_bars
        logger.debug(
            "%s: Slicing chart bars for %s (tf=%s, limit=%d, offset=%d)",
            REVIEW_EDIT_FR,
            symbol,
            timeframe,
            effective_limit,
            offset,
            extra={"fr_id": REVIEW_EDIT_FR, "timeframe": timeframe},
        )
        did = dataset_id or f"file:{symbol.upper()}"
        df = self.read_bars_dataframe(did)
        if df.empty:
            return []

        sliced_df = df.iloc[offset:] if offset > 0 else df
        tail_df = sliced_df.tail(effective_limit)
        bars: list[dict[str, Any]] = []
        for _, row in tail_df.iterrows():
            ts_str = str(row["timestamp"])
            bars.append(
                {
                    "datetime": ts_str,
                    "time": ts_str,
                    "open": float(row.get("open", row.get("bid", 0.0))),
                    "high": float(row.get("high", row.get("bid", 0.0))),
                    "low": float(row.get("low", row.get("bid", 0.0))),
                    "close": float(row.get("close", row.get("ask", 0.0))),
                    "volume": float(row.get("volume", 0.0)),
                    "spread": float(row.get("spread", 0.0)),
                }
            )

        logger.debug(
            "%s: Sliced %d review chart bars for %s",
            REVIEW_EDIT_FR,
            len(bars),
            symbol,
            extra={
                "fr_id": REVIEW_EDIT_FR,
                "bars": len(bars),
                "symbol": symbol,
            },
        )
        return bars

    def get_review_rows(
        self,
        dataset_id: str,
        limit: int = 500,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Retrieve paginated tabular rows for dataset editing."""
        df = self.read_bars_dataframe(dataset_id)
        if df.empty:
            return []

        slice_df = df.iloc[offset : offset + limit]
        rows: list[dict[str, Any]] = []
        for idx, (_, r) in enumerate(slice_df.iterrows()):
            ts = str(r["timestamp"])
            rows.append(
                {
                    "id": offset + idx,
                    "timestamp": ts,
                    "time": ts,
                    "open": float(r["open"]),
                    "high": float(r["high"]),
                    "low": float(r["low"]),
                    "close": float(r["close"]),
                    "volume": float(r["volume"]),
                    "spread": float(r.get("spread", 0.0)),
                }
            )
        return rows

    def save_review_changes(
        self,
        dataset_id: str,
        changed_bars: Sequence[Mapping[str, Any]],
        deleted_timestamps: Sequence[str | int],
    ) -> dict[str, Any]:
        """Apply manual bar edits and row deletions to dataset's Parquet file."""
        df = self.read_bars_dataframe(dataset_id)
        if df.empty:
            return {"updated_count": 0, "deleted_count": 0, "bars": 0}

        del_set = {str(ts) for ts in deleted_timestamps}

        # Apply bar changes first to rows not scheduled for deletion
        ts_index_map = {str(ts): idx for idx, ts in enumerate(df["timestamp"])}
        updated_count = 0
        for bar in changed_bars:
            ts = str(bar.get("timestamp") or bar.get("time", ""))
            if ts and ts in ts_index_map and ts not in del_set:
                row_idx = ts_index_map[ts]
                for col in (
                    "open",
                    "high",
                    "low",
                    "close",
                    "volume",
                    "spread",
                    "bid",
                    "ask",
                ):
                    if col in bar:
                        df.at[row_idx, col] = float(bar[col])
                updated_count += 1

        # Apply deletions and cleanly reset index to prevent NaN rows
        if del_set:
            df = df[~df["timestamp"].astype(str).isin(del_set)].reset_index(drop=True)

        updated_rec = self.write_bars_dataframe(dataset_id, df)
        logger.info(
            "%s: Saved review changes (updated=%d, deleted=%d, total_bars=%d)",
            REVIEW_EDIT_FR,
            updated_count,
            len(del_set),
            updated_rec.bars,
            extra={
                "fr_id": REVIEW_EDIT_FR,
                "updated_count": updated_count,
                "deleted_count": len(del_set),
            },
        )
        return {
            "updated_count": updated_count,
            "deleted_count": len(del_set),
            "bars": updated_rec.bars,
        }

    def get_index_for_date(self, dataset_id: str, target_date: str) -> int:
        """Binary search dataset timestamps to find row index for target date."""
        df = self.read_bars_dataframe(dataset_id)
        if df.empty:
            return -1

        timestamps = list(df["timestamp"].astype(str))
        clean_target = target_date.strip()
        idx = bisect.bisect_left(timestamps, clean_target)
        if idx >= len(timestamps):
            return len(timestamps) - 1
        return idx

    def list_csv_formats(self) -> list[dict[str, Any]]:
        """List custom CSV export format specifications from host_entities."""
        with resolve_connection(self.db_path) as conn:
            rows = read_rows(
                conn,
                "host_entities",
                where={"entity_type": "datamgr_csv_format"},
            )

        formats: list[dict[str, Any]] = [
            {
                "name": "Standard SQX CSV",
                "delimiter": ",",
                "date_format": "YYYY.MM.DD",
                "time_format": "HH:mm",
                "columns": ["Date", "Time", "Open", "High", "Low", "Close", "Volume"],
            }
        ]
        for r in rows:
            try:
                payload = json.loads(str(r.get("payload", "{}")))
                formats.append(payload)
            except (json.JSONDecodeError, TypeError, KeyError) as exc:
                logger.debug(
                    "%s: Skipping malformed CSV format: %s",
                    EXPORT_ENGINE_FR,
                    exc,
                )
        return formats

    def save_csv_format(self, format_payload: Mapping[str, Any]) -> dict[str, Any]:
        """Save custom CSV export format specification in host_entities."""
        name = str(format_payload.get("name", "Custom")).strip()
        now_iso = datetime.now(UTC).isoformat()
        payload_json = json.dumps(dict(format_payload))

        with resolve_connection(self.db_path) as conn:
            delete_rows(
                conn,
                "host_entities",
                where={
                    "entity_id": name,
                    "entity_type": "datamgr_csv_format",
                },
            )
            insert_row(
                conn,
                "host_entities",
                {
                    "entity_id": name,
                    "entity_type": "datamgr_csv_format",
                    "scope": "workspace",
                    "payload": payload_json,
                    "revision": 1,
                    "created_at_utc": now_iso,
                    "updated_at_utc": now_iso,
                },
            )

        logger.info(
            "%s: Saved custom CSV format '%s'",
            EXPORT_ENGINE_FR,
            name,
            extra={"fr_id": EXPORT_ENGINE_FR, "format_name": name},
        )
        return dict(format_payload)

    def delete_csv_format(self, name: str) -> dict[str, Any]:
        """Delete custom CSV format specification from host_entities."""
        clean = name.strip()
        with resolve_connection(self.db_path) as conn:
            count = delete_rows(
                conn,
                "host_entities",
                where={
                    "entity_id": clean,
                    "entity_type": "datamgr_csv_format",
                },
            )
        return {"name": clean, "deleted": count > 0}

    def export_datasets(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        """Export dataset bars to CSV, MetaTrader 4, MetaTrader 5, or Series formats."""
        export_format = str(
            payload.get("format") or payload.get("export_type", "CSV")
        ).upper()
        target_ids = payload.get("dataset_ids") or payload.get("symbols", [])
        if isinstance(target_ids, str):
            target_ids = [target_ids]

        date_from = payload.get("date_from")
        date_to = payload.get("date_to")
        decimals = int(payload.get("decimals", 5))

        artifacts: list[ExportArtifactResult] = []
        for tid in target_ids:
            rec = self.get_dataset(tid)
            df = self.read_bars_dataframe(str(rec.id) if rec else tid)
            artifact = _export_single_dataset(
                rec=rec,
                tid=tid,
                df=df,
                export_format=export_format,
                decimals=decimals,
                date_from=date_from,
                date_to=date_to,
            )
            if artifact is not None:
                artifacts.append(artifact)

        if self.log_service:
            self.log_service.append_log(
                action="EXPORT",
                message=f"Exported {len(artifacts)} datasets in {export_format} format",
                details={"format": export_format, "count": len(artifacts)},
            )

        logger.info(
            "%s: Exported %d datasets in format %s",
            EXPORT_ENGINE_FR,
            len(artifacts),
            export_format,
            extra={
                "fr_id": EXPORT_ENGINE_FR,
                "format": export_format,
                "count": len(artifacts),
            },
        )
        return {
            "format": export_format,
            "exported_count": len(artifacts),
            "artifacts": [a.to_dict() for a in artifacts],
        }


def main() -> None:
    """Execute real-usage demonstration of DataManagerDataService and models."""
    chart = ChartDef(symbol="EURUSD", timeframe="M1")
    info = DataInfo(symbol="EURUSD", timeframe="M1", decimals=5)
    print(f"ChartDef created: symbol={chart.symbol}, timeframe={chart.timeframe}")
    print(f"DataInfo created: symbol={info.symbol}, rows={info.rows}")

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
        temp_path = Path(temp_dir)
        db_file = temp_path / "test_data.db"
        with resolve_connection(db_file) as conn:
            create_schema(conn)

        service = DataManagerDataService(db_path=db_file, data_dir=temp_path / "data")
        sample_csv = "\n".join(
            ["DateTime,Open,High,Low,Close,Volume,Spread"]
            + [
                f"2026-01-01 00:{i:02d}:00,1.1000,1.1005,1.0995,1.1002,100,1.0"
                for i in range(10)
            ]
        )
        rec = service.import_dataset(
            {
                "symbol": "EURUSD",
                "timeframe": "M1",
                "source": "file",
                "csv_content": sample_csv,
            }
        )
        print(f"Imported dataset: {rec.id} (bars={rec.bars})")

        chart_bars = service.get_review_chart_bars("EURUSD", max_bars=5)
        print(f"Loaded {len(chart_bars)} chart bars for EURUSD")
        for b in chart_bars:
            print(f" - {b['time']}: O={b['open']} C={b['close']}")

        export_res = service.export_datasets(
            {"dataset_ids": [str(rec.id)], "format": "MT4"}
        )
        print(f"Exported result: count={export_res['exported_count']}")


if __name__ == "__main__":
    main()
