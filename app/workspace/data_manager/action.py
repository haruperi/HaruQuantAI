"""Data Manager high-level actions, transforms, multi-format export, and audits.

Description:
    Provides high-level dataset actions for the Data Manager workspace, including
    timezone cloning with timestamp shifting, multi-dataset deletion, custom-delimited
    CSV export, format configuration persistence, MetaTrader 4 FXT/HST and MetaTrader 5
    export, data review statistics, paginated raw bar inspection, data quality audit
    with gap and envelope anomaly detection, and selective/catalog-wide data updates.

Purpose:
    FEAT-DATAMGR-ACTIONS: High-level data transformation, export, review, and audits.

Key Capabilities:
    - FR-DATAMGR-ACT-CLONE-TZ: Clone price data with timezone shift
      [Actions.clone_to_timezone()] -> INFO.
    - FR-DATAMGR-ACT-DELETE: Delete dataset catalog entries and files
      [Actions.delete()] -> INFO.
    - FR-DATAMGR-ACT-EXPORT-CSV: Export price data to custom CSV
      [Actions.export_to_csv()] -> INFO.
    - FR-DATAMGR-ACT-NEW-FORMAT: Persist CSV export format specification
      [Actions.new_format()] -> INFO.
    - FR-DATAMGR-ACT-EXPORT-MT4: Export price data to MT4 FXT and HST
      [Actions.export_to_mt4()] -> INFO.
    - FR-DATAMGR-ACT-EXPORT-MT5: Export price data to MT5 format
      [Actions.export_to_mt5()] -> INFO.
    - FR-DATAMGR-ACT-REVIEW: Dataset summary statistics and bounds
      [Actions.review()] -> INFO.
    - FR-DATAMGR-ACT-REVIEW-DATA: Extract paginated raw bar records
      [Actions.review_data()] -> INFO.
    - FR-DATAMGR-ACT-QUALITY: Data quality audit and gap analysis
      [Actions.quality()] -> INFO.
    - FR-DATAMGR-ACT-UPDATE: Download updates for selected datasets
      [Actions.update()] -> INFO.
    - FR-DATAMGR-ACT-UPDATE-ALL: Download updates for all datasets
      [Actions.update_all()] -> INFO.

Python API Usage:
    ```python
    from app.workspace.data_manager.action import Actions

    service = Actions()
    review = service.review("ds:dukascopy:EURUSD:M1")
    quality = service.quality("ds:dukascopy:EURUSD:M1")
    ```

CLI Usage:
    ```bash
    uv run python -m app.cli -action clone symbols=EURUSD timezone=EET
    uv run python -m app.cli -action quality symbols=EURUSD
    ```
"""

from __future__ import annotations

import csv
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import polars as pl
from app.host.logging import get_logger
from app.host.persistence import HostPersistence
from app.services.brokers.files import encode_fxt_bytes, encode_hst_bytes
from app.workspace.data_manager.data import Data

__all__ = ["Actions", "ActionsCLI"]

logger = get_logger(__name__)

CLONE_TZ_FR = "FR-DATAMGR-ACT-CLONE-TZ"
DELETE_FR = "FR-DATAMGR-ACT-DELETE"
EXPORT_CSV_FR = "FR-DATAMGR-ACT-EXPORT-CSV"
NEW_FORMAT_FR = "FR-DATAMGR-ACT-NEW-FORMAT"
EXPORT_MT4_FR = "FR-DATAMGR-ACT-EXPORT-MT4"
EXPORT_MT5_FR = "FR-DATAMGR-ACT-EXPORT-MT5"
REVIEW_FR = "FR-DATAMGR-ACT-REVIEW"
REVIEW_DATA_FR = "FR-DATAMGR-ACT-REVIEW-DATA"
QUALITY_FR = "FR-DATAMGR-ACT-QUALITY"
UPDATE_FR = "FR-DATAMGR-ACT-UPDATE"
UPDATE_ALL_FR = "FR-DATAMGR-ACT-UPDATE-ALL"

_DEFAULT_EXPORT_COLUMNS = (
    "Date",
    "Time",
    "Open",
    "High",
    "Low",
    "Close",
    "Volume",
)

_COMMON_TZ_OFFSETS: dict[str, int] = {
    "UTC": 0,
    "GMT": 0,
    "EST": -5,
    "EDT": -4,
    "CST": -6,
    "CDT": -5,
    "MST": -7,
    "MDT": -6,
    "PST": -8,
    "PDT": -7,
    "EET": 2,
    "EEST": 3,
    "CET": 1,
    "CEST": 2,
    "JST": 9,
    "AEST": 10,
    "AEDT": 11,
}

_FRIDAY = 4
_MONDAY = 0
_MAX_WEEKEND_GAP_DAYS = 3
_SPIKE_PCT_THRESHOLD = 0.10


@dataclass(frozen=True)
class _Config:
    """Internal configuration parameters for dataset actions."""

    default_preview_limit: int = 100
    max_preview_limit: int = 1000
    default_gap_minutes: int = 60
    default_price_precision: int = 5


def _format_cell(col: str, dt: datetime, row: Mapping[str, Any]) -> str:
    """Format single cell value for custom delimited export."""
    c = col.lower()
    if c == "date":
        res = dt.strftime("%Y.%m.%d")
    elif c == "time":
        res = dt.strftime("%H:%M:%S")
    elif c in ("datetime", "timestamp"):
        res = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    elif c in ("open", "high", "low", "close"):
        res = f"{float(row.get(c, 0.0)):.5f}"
    elif c in ("volume", "vol", "tick_volume"):
        res = str(int(row.get("volume", 1)))
    elif c == "spread":
        res = str(int(row.get("spread", 0)))
    else:
        res = str(row.get(col, ""))
    return res


class Actions:
    """Service providing high-level dataset operations, transforms, and exports."""

    def __init__(
        self, data_service: Data | None = None, config: _Config | None = None
    ) -> None:
        self._data_service = data_service or Data()
        self._config = config or _Config()

    def clone_to_timezone(
        self,
        dataset_id: str,
        target_timezone: str,
        *,
        new_symbol: str | None = None,
        shift_hours: int | None = None,
        remove_weekends: bool = False,
    ) -> dict[str, Any]:
        """Clone price data to a specified timezone offset with bar timestamp shifts."""
        ds = self._ensure_dataset_exists(dataset_id)
        if ds.get("source") == "cloned" or ds.get("data_kind") == "cloned":
            raise ValueError(
                f"Dataset '{dataset_id}' is cloned data. You cannot clone it again."
            )
        lineage_raw = ds.get("lineage_json") or "{}"
        with_lineage = (
            json.loads(lineage_raw) if isinstance(lineage_raw, str) else lineage_raw
        )
        if with_lineage.get("source_data_id") or with_lineage.get("cloned_from"):
            raise ValueError(
                f"Dataset '{dataset_id}' is cloned data. You cannot clone it again."
            )

        eff_shift = (
            shift_hours
            if shift_hours is not None
            else self._calculate_tz_offset(ds.get("timezone", "UTC"), target_timezone)
        )
        bars_df = self._read_dataset_bars(dataset_id)
        if bars_df.is_empty():
            raise ValueError(f"Dataset '{dataset_id}' contains no price data to clone.")

        orig_sym = ds["symbol"]
        clean_tz = target_timezone.replace("/", "_").replace(" ", "_")
        cloned_sym = new_symbol or f"{orig_sym}_{clean_tz}"
        tf = ds.get("timeframe", "M1")

        shifted_records: list[dict[str, Any]] = []
        delta = timedelta(hours=eff_shift)
        for row in bars_df.iter_rows(named=True):
            ts = self._parse_iso_ts(row["timestamp"])
            shifted_ts = ts + delta
            if remove_weekends and shifted_ts.weekday() in (5, 6):
                continue
            item = dict(row)
            item["timestamp"] = shifted_ts.strftime("%Y-%m-%dT%H:%M:%SZ")
            shifted_records.append(item)

        if not shifted_records:
            raise ValueError("All bars were filtered out during timezone cloning.")

        cloned_id = f"ds:cloned:{cloned_sym}:{tf}"
        cloned_df = pl.DataFrame(shifted_records)
        target_path = self._write_parquet_partition("cloned", cloned_sym, tf, cloned_df)

        min_d = shifted_records[0]["timestamp"][:10]
        max_d = shifted_records[-1]["timestamp"][:10]
        now_iso = datetime.now(UTC).isoformat()
        new_record = {
            "id": cloned_id,
            "source": "cloned",
            "symbol": cloned_sym,
            "underlying": ds.get("underlying", cloned_sym),
            "instrument": ds.get("instrument", cloned_sym),
            "timeframe": tf,
            "broker": ds.get("broker", "default"),
            "broker_name": ds.get("broker_name", "Cloned Series"),
            "timezone": target_timezone,
            "category": ds.get("category", "Cloned"),
            "date_from": min_d,
            "date_to": max_d,
            "bars": len(shifted_records),
            "created_at": now_iso,
            "updated_at": now_iso,
            "path": str(target_path),
            "data_kind": "cloned",
            "quality_score": ds.get("quality_score", 100.0),
            "lineage_json": json.dumps(
                {
                    "source_data_id": dataset_id,
                    "cloned_from": dataset_id,
                    "shift_hours": eff_shift,
                    "target_timezone": target_timezone,
                    "remove_weekends": remove_weekends,
                    "cloned_at": now_iso,
                }
            ),
            "schema_version": 1,
        }
        HostPersistence.create_record("datamgr_datasets", new_record)
        logger.info(
            "%s: Cloned dataset %s to %s (shift=%dh, bars=%d)",
            CLONE_TZ_FR,
            dataset_id,
            cloned_id,
            eff_shift,
            len(shifted_records),
            extra={"fr_id": CLONE_TZ_FR, "dataset_id": cloned_id},
        )
        return {
            "dataset_id": cloned_id,
            "source_dataset_id": dataset_id,
            "symbol": cloned_sym,
            "target_timezone": target_timezone,
            "shift_hours": eff_shift,
            "bars": len(shifted_records),
            "path": str(target_path),
        }

    def delete(
        self, dataset_ids: Sequence[str] | str, *, delete_files: bool = True
    ) -> dict[str, Any]:
        """Delete one or more dataset catalog entries and optional storage files."""
        ids = [dataset_ids] if isinstance(dataset_ids, str) else list(dataset_ids)
        deleted_details: list[dict[str, Any]] = []
        for did in ids:
            try:
                res = self._data_service.delete(did, delete_files=delete_files)
                deleted_details.append(res)
            except (ValueError, KeyError, OSError, RuntimeError) as exc:
                deleted_details.append(
                    {"deleted_id": did, "deleted": False, "error": str(exc)}
                )

        success_ids = [
            str(d.get("deleted_id") or d.get("dataset_id") or d.get("id"))
            for d in deleted_details
            if d.get("deleted_count", 0) > 0 or d.get("deleted", True)
        ]
        logger.info(
            "%s: Deleted %d of %d dataset(s)",
            DELETE_FR,
            len(success_ids),
            len(ids),
            extra={"fr_id": DELETE_FR, "deleted_count": len(success_ids)},
        )
        return {
            "deleted_count": len(success_ids),
            "total_requested": len(ids),
            "deleted_ids": success_ids,
            "details": deleted_details,
        }

    def export_to_csv(
        self,
        dataset_id: str,
        output_path: Path | str,
        *,
        format_name: str | None = None,
        custom_format: Mapping[str, Any] | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        session: str | None = None,
    ) -> dict[str, Any]:
        """Export price data to CSV format with custom headers and delimiters."""
        self._ensure_dataset_exists(dataset_id)
        df = self._read_dataset_bars(dataset_id)
        if df.is_empty():
            raise ValueError(f"Dataset '{dataset_id}' contains no data to export.")

        filtered = self._apply_date_range(df, date_from, date_to)
        fmt = self._resolve_csv_format(format_name, custom_format)
        delimiter = str(fmt.get("delimiter", ","))
        include_header = bool(fmt.get("include_header", True))
        cols = list(fmt.get("columns", _DEFAULT_EXPORT_COLUMNS))

        dest = Path(output_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        row_count = 0
        with dest.open("w", encoding="utf-8", newline="") as fp:
            writer = csv.writer(fp, delimiter=delimiter)
            if include_header:
                writer.writerow(cols)
            for row in filtered.iter_rows(named=True):
                vals = self._extract_csv_row_values(row, cols)
                writer.writerow(vals)
                row_count += 1

        logger.info(
            "%s: Exported %d rows to %s",
            EXPORT_CSV_FR,
            row_count,
            dest,
            extra={"fr_id": EXPORT_CSV_FR, "rows_exported": row_count},
        )
        return {
            "dataset_id": dataset_id,
            "output_path": str(dest),
            "rows_exported": row_count,
            "format": format_name or "custom",
            "delimiter": delimiter,
            "session": session,
        }

    def new_format(self, format_spec: Mapping[str, Any]) -> dict[str, Any]:
        """Create and persist new CSV export format configurations."""
        name = str(format_spec.get("name", "")).strip()
        if not name:
            raise ValueError("Parameter 'name' is required for format configuration.")

        payload: dict[str, Any] = {
            "name": name,
            "delimiter": str(format_spec.get("delimiter", ",")),
            "include_header": bool(format_spec.get("include_header", True)),
            "header": str(format_spec.get("header", "")),
            "columns": list(format_spec.get("columns", _DEFAULT_EXPORT_COLUMNS)),
            "created_at": datetime.now(UTC).isoformat(),
        }
        HostPersistence.create_entity(
            "datamgr_export_format",
            {
                "entity_id": name,
                "scope": "global",
                "payload": json.dumps(payload),
            },
        )
        logger.info(
            "%s: Registered CSV export format '%s'",
            NEW_FORMAT_FR,
            name,
            extra={"fr_id": NEW_FORMAT_FR, "format_name": name},
        )
        return payload

    def export_to_mt4(
        self,
        dataset_id: str,
        output_dir: Path | str,
        *,
        mode: str = "all",
        symbol_alias: str | None = None,
        period: int = 1,
        digits: int = 5,
    ) -> dict[str, Any]:
        """Export price data to MetaTrader 4 FXT and HST binary files."""
        ds = self._ensure_dataset_exists(dataset_id)
        df = self._read_dataset_bars(dataset_id)
        if df.is_empty():
            raise ValueError(f"Dataset '{dataset_id}' contains no data to export.")

        target_dir = Path(output_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        sym = symbol_alias or ds["symbol"]
        mt4_rows: list[dict[str, Any]] = []
        for r in df.iter_rows(named=True):
            dt = self._parse_iso_ts(r["timestamp"])
            mt4_rows.append(
                {
                    "time": int(dt.timestamp()),
                    "open": float(r["open"]),
                    "high": float(r["high"]),
                    "low": float(r["low"]),
                    "close": float(r["close"]),
                    "volume": int(r.get("volume", 1)),
                    "tick_volume": int(r.get("volume", 1)),
                    "spread": int(r.get("spread", 0)),
                }
            )

        created_files: list[str] = []
        eff_mode = mode.lower()
        if eff_mode in ("all", "hst"):
            hst_bytes = encode_hst_bytes(
                mt4_rows, sym, period=period, digits=digits, version=401
            )
            hst_path = target_dir / f"{sym}{period}.hst"
            hst_path.write_bytes(hst_bytes)
            created_files.append(str(hst_path))

        if eff_mode in ("all", "fxt"):
            fxt_bytes = encode_fxt_bytes(mt4_rows, sym, period=period, version=405)
            fxt_path = target_dir / f"{sym}{period}_0.fxt"
            fxt_path.write_bytes(fxt_bytes)
            created_files.append(str(fxt_path))

        logger.info(
            "%s: Exported %d bars to MT4 files (%s)",
            EXPORT_MT4_FR,
            len(mt4_rows),
            ", ".join(created_files),
            extra={"fr_id": EXPORT_MT4_FR, "files_count": len(created_files)},
        )
        return {
            "dataset_id": dataset_id,
            "symbol": sym,
            "files": created_files,
            "record_count": len(mt4_rows),
        }

    def export_to_mt5(
        self,
        dataset_id: str,
        output_dir: Path | str,
        *,
        symbol_alias: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        spread_type: str = "real",
        fixed_spread: int = 10,
    ) -> dict[str, Any]:
        """Export price data to MetaTrader 5 delimited format."""
        ds = self._ensure_dataset_exists(dataset_id)
        df = self._read_dataset_bars(dataset_id)
        if df.is_empty():
            raise ValueError(f"Dataset '{dataset_id}' contains no data to export.")

        filtered = self._apply_date_range(df, date_from, date_to)
        target_dir = Path(output_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        sym = symbol_alias or ds["symbol"]
        tf = ds.get("timeframe", "M1")
        out_file = target_dir / f"{sym}_{tf}.csv"

        count = 0
        with out_file.open("w", encoding="utf-8", newline="") as fp:
            writer = csv.writer(fp, delimiter="\t")
            writer.writerow(
                [
                    "<DATE>",
                    "<TIME>",
                    "<OPEN>",
                    "<HIGH>",
                    "<LOW>",
                    "<CLOSE>",
                    "<TICKVOL>",
                    "<VOL>",
                    "<SPREAD>",
                ]
            )
            for row in filtered.iter_rows(named=True):
                dt = self._parse_iso_ts(row["timestamp"])
                d_str = dt.strftime("%Y.%m.%d")
                t_str = dt.strftime("%H:%M:%S")
                spd = (
                    int(row.get("spread", fixed_spread))
                    if spread_type == "real"
                    else fixed_spread
                )
                writer.writerow(
                    [
                        d_str,
                        t_str,
                        f"{float(row['open']):.5f}",
                        f"{float(row['high']):.5f}",
                        f"{float(row['low']):.5f}",
                        f"{float(row['close']):.5f}",
                        int(row.get("volume", 1)),
                        int(row.get("volume", 1)),
                        spd,
                    ]
                )
                count += 1

        logger.info(
            "%s: Exported %d bars to MT5 format at %s",
            EXPORT_MT5_FR,
            count,
            out_file,
            extra={"fr_id": EXPORT_MT5_FR, "rows_exported": count},
        )
        return {
            "dataset_id": dataset_id,
            "symbol": sym,
            "output_path": str(out_file),
            "rows_exported": count,
        }

    def review(self, dataset_id: str) -> dict[str, Any]:
        """Open data review modal to view data details and summary statistics."""
        ds = self._ensure_dataset_exists(dataset_id)
        df = self._read_dataset_bars(dataset_id)
        stats: dict[str, Any] = {
            "total_records": len(df),
            "date_from": ds.get("date_from"),
            "date_to": ds.get("date_to"),
            "min_price": 0.0,
            "max_price": 0.0,
            "avg_volume": 0.0,
            "completeness_score": 100.0,
        }
        if not df.is_empty():
            stats["min_price"] = float(df["low"].min())  # type: ignore[arg-type]
            stats["max_price"] = float(df["high"].max())  # type: ignore[arg-type]
            stats["avg_volume"] = float(df["volume"].mean())  # type: ignore[arg-type]
            stats["date_from"] = str(df["timestamp"][0])[:10]
            stats["date_to"] = str(df["timestamp"][-1])[:10]

        logger.info(
            "%s: Computed review statistics for %s (%d bars)",
            REVIEW_FR,
            dataset_id,
            stats["total_records"],
            extra={"fr_id": REVIEW_FR, "dataset_id": dataset_id},
        )
        return {"dataset": ds, "statistics": stats}

    def review_data(
        self,
        dataset_id: str,
        *,
        offset: int = 0,
        limit: int = 100,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> dict[str, Any]:
        """Display raw bar table in data review."""
        self._ensure_dataset_exists(dataset_id)
        df = self._read_dataset_bars(dataset_id)
        filtered = self._apply_date_range(df, date_from, date_to)
        total = len(filtered)
        eff_limit = min(max(1, limit), self._config.max_preview_limit)
        eff_offset = max(0, offset)
        sliced = filtered.slice(eff_offset, eff_limit)

        columns = list(sliced.columns)
        rows: list[list[Any]] = [
            [row[col] for col in columns] for row in sliced.iter_rows(named=True)
        ]
        logger.info(
            "%s: Sliced %d rows (offset=%d) for %s",
            REVIEW_DATA_FR,
            len(rows),
            eff_offset,
            dataset_id,
            extra={"fr_id": REVIEW_DATA_FR, "rows_returned": len(rows)},
        )
        return {
            "dataset_id": dataset_id,
            "offset": eff_offset,
            "limit": eff_limit,
            "total_records": total,
            "columns": columns,
            "rows": rows,
        }

    def quality(
        self,
        dataset_id: str,
        *,
        max_gap_minutes: int = 60,
        check_envelope: bool = True,
        check_spikes: bool = True,
    ) -> dict[str, Any]:
        """Perform data quality audit and gap analysis across timeframes."""
        self._ensure_dataset_exists(dataset_id)
        df = self._read_dataset_bars(dataset_id)
        if df.is_empty():
            return {
                "dataset_id": dataset_id,
                "quality_score": 0.0,
                "total_records": 0,
                "total_errors": 0,
                "problems": {},
                "anomalies": [],
            }

        anomalies: list[dict[str, Any]] = []
        gap_count = 0
        envelope_count = 0
        weekend_count = 0
        spike_count = 0

        prev_dt: datetime | None = None
        prev_close: float | None = None
        max_gap = timedelta(minutes=max_gap_minutes)

        for row in df.iter_rows(named=True):
            dt = self._parse_iso_ts(row["timestamp"])
            o, h, low_val, c = (
                float(row["open"]),
                float(row["high"]),
                float(row["low"]),
                float(row["close"]),
            )

            # Check weekend bars
            if dt.weekday() in (5, 6):
                weekend_count += 1
                anomalies.append({"timestamp": row["timestamp"], "type": "weekend_bar"})

            # Check OHLC envelope validity
            is_env_invalid = (
                h < low_val
                or o > h
                or o < low_val
                or c > h
                or c < low_val
                or low_val <= 0.0
            )
            if check_envelope and is_env_invalid:
                envelope_count += 1
                anomalies.append(
                    {
                        "timestamp": row["timestamp"],
                        "type": "envelope_error",
                        "ohlc": [o, h, low_val, c],
                    }
                )

            # Check gaps (excluding standard weekend transition)
            if prev_dt is not None:
                gap = dt - prev_dt
                is_weekend_gap = (
                    prev_dt.weekday() == _FRIDAY
                    and dt.weekday() == _MONDAY
                    and gap.days <= _MAX_WEEKEND_GAP_DAYS
                )
                if gap > max_gap and not is_weekend_gap:
                    gap_count += 1
                    anomalies.append(
                        {
                            "timestamp": row["timestamp"],
                            "type": "time_gap",
                            "minutes": int(gap.total_seconds() / 60),
                        }
                    )

            # Check price spike outliers (>10% instant step)
            if check_spikes and prev_close is not None and prev_close > 0.0:
                pct = abs(o - prev_close) / prev_close
                if pct > _SPIKE_PCT_THRESHOLD:
                    spike_count += 1
                    anomalies.append(
                        {
                            "timestamp": row["timestamp"],
                            "type": "price_spike",
                            "pct_change": round(pct * 100.0, 2),
                        }
                    )

            prev_dt = dt
            prev_close = c

        total_bars = len(df)
        total_errors = len(anomalies)
        deduction = (total_errors / max(1, total_bars)) * 100.0
        score = round(max(0.0, 100.0 - deduction), 2)

        summary = {
            "gaps": gap_count,
            "envelope_errors": envelope_count,
            "weekend_bars": weekend_count,
            "price_spikes": spike_count,
            "total_errors": total_errors,
        }
        logger.info(
            "%s: Quality audit for %s: score=%.2f, errors=%d",
            QUALITY_FR,
            dataset_id,
            score,
            total_errors,
            extra={"fr_id": QUALITY_FR, "quality_score": score},
        )
        return {
            "dataset_id": dataset_id,
            "quality_score": score,
            "total_records": total_bars,
            "total_errors": total_errors,
            "problems": summary,
            "anomalies": anomalies[:50],
        }

    def update(
        self, dataset_ids: Sequence[str] | str, *, mode: str = "missing"
    ) -> dict[str, Any]:
        """Update selected data to download up to date."""
        ids = [dataset_ids] if isinstance(dataset_ids, str) else list(dataset_ids)
        updates: list[dict[str, Any]] = []
        for did in ids:
            ds = self._ensure_dataset_exists(did)
            src = ds.get("source", "dukascopy")
            sym = ds["symbol"]
            tf = ds.get("timeframe", "M1")
            d_to = ds.get("date_to")
            res = self._data_service.import_data(src, sym, tf, start=d_to, mode=mode)
            updates.append({"id": did, "result": res})

        logger.info(
            "%s: Updated %d dataset(s)",
            UPDATE_FR,
            len(updates),
            extra={"fr_id": UPDATE_FR, "updated_count": len(updates)},
        )
        return {"updated_count": len(updates), "updates": updates}

    def update_all(self, *, mode: str = "missing") -> dict[str, Any]:
        """Update all data to download up to date."""
        all_ds = self._data_service.list_datasets()
        ids = [r["id"] for r in all_ds if r.get("source") != "cloned"]
        res = self.update(ids, mode=mode)
        logger.info(
            "%s: Triggered update_all across %d dataset(s)",
            UPDATE_ALL_FR,
            len(ids),
            extra={"fr_id": UPDATE_ALL_FR, "total_datasets": len(ids)},
        )
        return {
            "total_datasets": len(all_ds),
            "updated_count": res["updated_count"],
            "updates": res["updates"],
        }

    # Private internal helpers
    def _ensure_dataset_exists(self, dataset_id: str) -> dict[str, Any]:
        records = HostPersistence.read_records("datamgr_datasets", {"id": dataset_id})
        if not records:
            raise ValueError(f"Dataset '{dataset_id}' not found.")
        return dict(records[0])

    def _read_dataset_bars(self, dataset_id: str) -> pl.DataFrame:
        ds = self._ensure_dataset_exists(dataset_id)
        path_str = ds.get("path")
        if not path_str or not Path(path_str).exists():
            return pl.DataFrame()
        return pl.read_parquet(path_str)

    def _apply_date_range(
        self, df: pl.DataFrame, date_from: str | None, date_to: str | None
    ) -> pl.DataFrame:
        res = df
        if date_from and not res.is_empty():
            res = res.filter(pl.col("timestamp") >= date_from)
        if date_to and not res.is_empty():
            res = res.filter(pl.col("timestamp") <= date_to)
        return res

    def _parse_iso_ts(self, val: Any) -> datetime:
        s = str(val).strip()
        if "T" in s:
            clean = s.replace("Z", "+00:00")
            dt = datetime.fromisoformat(clean)
            return dt if dt.tzinfo else dt.replace(tzinfo=UTC)
        try:
            return datetime.fromtimestamp(float(s), tz=UTC)
        except ValueError:
            return datetime.strptime(s, "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)

    def _calculate_tz_offset(self, from_tz: str, to_tz: str) -> int:
        if from_tz in _COMMON_TZ_OFFSETS and to_tz in _COMMON_TZ_OFFSETS:
            return _COMMON_TZ_OFFSETS[to_tz] - _COMMON_TZ_OFFSETS[from_tz]
        try:
            now = datetime.now(UTC)
            z1 = ZoneInfo(from_tz).utcoffset(now)
            z2 = ZoneInfo(to_tz).utcoffset(now)
            s1 = int(z1.total_seconds() / 3600) if z1 else 0
            s2 = int(z2.total_seconds() / 3600) if z2 else 0
            return s2 - s1
        except ZoneInfoNotFoundError:
            return 0

    def _write_parquet_partition(
        self, source: str, symbol: str, timeframe: str, df: pl.DataFrame
    ) -> Path:
        market_dir: Path = self._data_service.market_dir
        target: Path = market_dir / source / timeframe / symbol / "cloned.parquet"
        target.parent.mkdir(parents=True, exist_ok=True)
        df.write_parquet(target, compression="zstd", compression_level=6)
        return target

    def _resolve_csv_format(
        self, format_name: str | None, custom_format: Mapping[str, Any] | None
    ) -> dict[str, Any]:
        if custom_format:
            return dict(custom_format)
        if format_name:
            records = HostPersistence.read_entity("datamgr_export_format", format_name)
            if records:
                raw_payload = records[0].get("payload", "{}")
                if isinstance(raw_payload, str):
                    parsed: dict[str, Any] = json.loads(raw_payload)
                    return parsed
                if isinstance(raw_payload, dict):
                    return raw_payload
        return {
            "delimiter": ",",
            "include_header": True,
            "columns": list(_DEFAULT_EXPORT_COLUMNS),
        }

    def _extract_csv_row_values(
        self, row: Mapping[str, Any], columns: Sequence[str]
    ) -> list[str]:
        dt = self._parse_iso_ts(row["timestamp"])
        return [_format_cell(col, dt, row) for col in columns]


class ActionsCLI:
    """Headless command-line dispatcher for Data Manager action operations."""

    @classmethod
    def dispatch_action(cls, args: Sequence[str], service: Actions) -> dict[str, Any]:
        """Dispatch headless action commands."""
        params: dict[str, str] = {}
        action = "review"
        for arg in args:
            if "=" in arg:
                k, v = arg.split("=", 1)
                params[k.strip().lower()] = v.strip()
            elif not arg.startswith("-"):
                action = arg.strip().lower()

        action = params.get("action", action)
        sym = params.get("symbol") or params.get("id") or "ds:dukascopy:EURUSD:M1"
        if action == "review":
            return service.review(sym)
        if action == "quality":
            return service.quality(sym)
        if action == "delete":
            return service.delete(sym)
        if action == "update":
            return service.update(sym)
        if action == "update_all":
            return service.update_all()
        raise ValueError(f"Unsupported action command: '{action}'")
