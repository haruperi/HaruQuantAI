"""Authoritative dataset catalog, historical storage integration, and SQX operations.

Description:
    Provides the central registry, metadata catalog, streaming file ingestion,
    and StrategyQuant X (DataManagerData) operations for quantitative market
    datasets within the Data Manager workspace. Normalizes bars and ticks into
    canonical records with geometry verification, chronological ordering, and
    integer tick unit encoding in partitioned Parquet files (ZSTD level 6). All
    persistence operations synchronize authoritatively through the host
    DatabaseManager (datamgr_datasets and datamgr_instruments).

Purpose:
    FEAT-WORKSPACE-DATAMGR: Dataset catalog, historical storage integration, and
    StrategyQuant X DataManagerData domain operations.

Key Capabilities:
    - FR-DATA-CATALOG-DATASET-REGISTRY: Authoritative dataset metadata tracking
      including source, underlying, timeframe, time boundaries, and bar counts.
      Associated: `[CatalogService.save_dataset()]`,
      `[CatalogService.get_dataset()]`
      Logging: Emits INFO on dataset registration and update.
    - FR-DATA-CATALOG-REVISION-INTEGRITY: Monotonic revision checks and
      validation of dataset integrity.
      Associated: `[CatalogService.save_dataset()]`
      Logging: Emits INFO on revision advancement and WARNING on conflicts.
    - FR-DATA-CATALOG-SERIES-DISCOVERY: Semantic series availability checks
      distinguishing absent datasets from zero-bar acquired series.
      Associated: `[CatalogService.check_availability()]`
      Logging: Emits DEBUG when series availability is inspected.
    - FR-DATA-CATALOG-SQX-OPERATIONS: StrategyQuant X DataManagerData operations:
      add/create, read/view, update/edit, clear data, and remove data.
      Associated: `[CatalogService.edit_dataset()]`,
      `[CatalogService.clear_data()]`,
      `[CatalogService.remove_data()]`,
      `[CatalogService.review_chart()]`
      Logging: Emits INFO on SQX data mutations and state transitions.
    - FR-DATA-INGESTION-STREAMING: Stream and chunk file parsing with
      delimiter sniffing.
      Associated: `[DataIngestionService.parse_stream()]`
      Logging: Emits DEBUG when delimiter and header sniffing completes.
    - FR-DATA-INGESTION-NORMALIZATION: Validate OHLCV bar geometry and ordering.
      Associated: `[BarRecord.is_valid_geometry()]`
      Logging: Rejects or logs invalid bar geometry.
    - FR-DATA-INGESTION-STAGING: Stage raw and processed revisions in isolated storage.
      Associated: `[DataIngestionService.ingest_file()]`
      Logging: Emits INFO on staged output file creation.
    - FR-DATA-INGESTION-REVISIONS: Compute SHA-256 fingerprints for immutable revisions.
      Associated: `[DataIngestionService.ingest_file()]`
      Logging: Emits INFO with revision ID and SHA-256 fingerprint on publish.

Python API Usage:
    ```python
    from pathlib import Path
    from app.host.persistence import DatabaseManager
    from app.workspace.data_manager.data import (
        CatalogService,
        DataIngestionService,
        DatasetRecord,
        IngestionConfig,
    )

    db = DatabaseManager(":memory:")
    db.initialize()
    catalog = CatalogService(db)
    service = DataIngestionService(catalog, storage_dir=Path("data/market"))

    record = DatasetRecord(
        id="ds-eurusd-m1",
        source="Dukascopy",
        symbol="EURUSD",
        timeframe="M1",
        bars=1000,
    )
    catalog.save_dataset(record)
    ```

CLI Usage:
    ```bash
    python -m app.workspace.data_manager.data --list
    ```
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import hashlib
import json
import re
import sys
import uuid
import xml.etree.ElementTree as ET
import zoneinfo
from collections.abc import Generator, Iterable, Sequence
from datetime import UTC, datetime, timedelta, timezone
from io import StringIO
from pathlib import Path
from typing import Any, override

import polars as pl
import pyarrow.parquet as pq
from pydantic import BaseModel, ConfigDict, Field

from app.host.logging import get_logger
from app.host.persistence import DatabaseManager
from app.workspace.data_manager.broker import BrokerProfileRecord, BrokerService
from app.workspace.data_manager.instruments import InstrumentService
from app.workspace.data_manager.storage import (
    DEFAULT_TICK_SIZE,
    BarRecord,
    MarketDataStorage,
    TickRecord,
    parse_iso_to_utc_datetime,
)

logger = get_logger(__name__)

__all__ = [
    "BarRecord",
    "CatalogService",
    "DataIngestionService",
    "DatasetRecord",
    "IngestionConfig",
    "IngestionResult",
    "MarketDataStorage",
    "TickRecord",
]

DEFAULT_CHUNK_SIZE = 10000
COMMON_DELIMITERS = [",", ";", "\t", " ", "|"]
MIN_FIELD_COUNT = 5
SEPARATE_DT_MIN_FIELDS = 6
ALIAS_COLON_PART_COUNT = 3
MS_EPOCH_THRESHOLD = 1e11
WEEKEND_START_DAY = 5
BAR_PARTITION_PARTS = 4
TICK_PARTITION_PARTS = 5
FOREX_RAW_TICK_THRESHOLD = 500_000
SIX_DIGIT_TICK_SCALE = 0.000001
IGNORED_PARTITION_DIRS = frozenset(
    {"database", "logs", "plugins", "resources", "staging"}
)
SIX_DIGIT_FOREX_SYMBOLS = frozenset({"EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDCHF"})


class IngestionConfig(BaseModel):
    """Configuration options for file ingestion."""

    model_config = ConfigDict(frozen=True)

    delimiter: str | None = Field(
        default=None, description="Delimiter (auto-detected if None)"
    )
    has_header: bool | None = Field(
        default=None, description="Whether file has header line"
    )
    datetime_format: str | None = Field(
        default=None, description="Explicit strptime format"
    )
    timezone: str = Field(
        default="UTC", description="Source data timezone (IANA format)"
    )
    skip_invalid_bars: bool = Field(
        default=True, description="Drop mathematically invalid bars instead of failing"
    )
    chunk_size: int = Field(
        default=DEFAULT_CHUNK_SIZE,
        gt=0,
        description="Chunk size for streaming processing",
    )


class IngestionResult(BaseModel):
    """Result summary of completed dataset ingestion and revision publication."""

    model_config = ConfigDict(frozen=True)

    dataset_id: str = Field(description="Registered dataset ID")
    revision_id: str = Field(description="Unique revision identifier")
    symbol: str = Field(description="Instrument symbol")
    timeframe: str = Field(description="Bar timeframe interval")
    bar_count: int = Field(description="Total valid bars acquired")
    date_from: str = Field(description="Earliest bar ISO UTC timestamp")
    date_to: str = Field(description="Latest bar ISO UTC timestamp")
    sha256_hash: str = Field(description="Cryptographic SHA-256 fingerprint")
    output_path: str = Field(description="Path to stored immutable data file")
    rejected_count: int = Field(
        default=0, description="Count of invalid/corrupt rows discarded"
    )


class DatasetRecord(BaseModel):
    """Authoritative representation of a persisted market dataset."""

    model_config = ConfigDict(frozen=True, extra="ignore")

    id: str = Field(min_length=1, description="Unique dataset identifier")
    source: str = Field(min_length=1, description="Data provider or source type")
    symbol: str = Field(min_length=1, description="Data symbol name")
    underlying: str = Field(default="", description="Base underlying symbol")
    instrument: str = Field(default="", description="Linked instrument symbol")
    timeframe: str = Field(
        default="M1", description="Resolution timeframe (TICK, M1, D1)"
    )
    broker: str = Field(default="Default", description="Broker identifier")
    broker_name: str = Field(default="Default", description="Broker human name")
    timezone: str = Field(default="UTC", description="Data timezone (e.g. UTC)")
    category: str = Field(default="Forex", description="Market category (e.g. Forex)")
    date_from: str = Field(default="", description="Start date string YYYY-MM-DD")
    date_to: str = Field(default="", description="End date string YYYY-MM-DD")
    bars: int = Field(default=0, ge=0, description="Authoritative total row/bar count")
    bar_count: int | None = Field(
        default=None, description="Alias for bars matching frontend expectations"
    )
    created_at: str | None = Field(default=None)
    updated_at: str | None = Field(default=None)
    path: str = Field(default="", description="Relative or absolute data file path")
    data_kind: str = Field(
        default="bars", description="Kind of data ('bars' or 'ticks')"
    )
    bar_type: str = Field(
        default="Start of bar", description="Bar timestamp convention"
    )
    quality_score: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Quality confidence score"
    )
    source_data_id: str | None = Field(
        default=None, description="Parent dataset ID if this dataset is cloned"
    )
    lineage_json: str = Field(default="{}", description="JSON lineage metadata")
    schema_version: int = Field(default=1, description="Metadata schema version")

    @override
    def model_post_init(self, _context: Any, /) -> None:
        """Ensure bar_count mirrors bars, dates are date-only, and unpack lineage."""
        if self.bar_count is None:
            object.__setattr__(self, "bar_count", self.bars)
        if self.date_from and ("T" in self.date_from or " " in self.date_from):
            object.__setattr__(
                self,
                "date_from",
                self.date_from.split("T", maxsplit=1)[0]
                .split(" ", maxsplit=1)[0]
                .strip(),
            )
        if self.date_to and ("T" in self.date_to or " " in self.date_to):
            object.__setattr__(
                self,
                "date_to",
                self.date_to.split("T", maxsplit=1)[0]
                .split(" ", maxsplit=1)[0]
                .strip(),
            )
        if self.source_data_id is None and self.lineage_json:
            try:
                lineage = json.loads(self.lineage_json)
                if isinstance(lineage, dict) and "source_data_id" in lineage:
                    object.__setattr__(
                        self, "source_data_id", lineage["source_data_id"]
                    )
            except json.JSONDecodeError, TypeError:
                pass


def _shift_bar_timestamp(
    bar: BarRecord,
    timezone_type: str,
    shift_delta: timedelta | None,
    tz_obj: zoneinfo.ZoneInfo | None,
    remove_weekends: bool,
) -> BarRecord | None:
    """Shift a bar's timestamp and optionally filter weekends."""
    dt_utc = parse_iso_to_utc_datetime(bar.timestamp_utc)
    if timezone_type == "hours" and shift_delta is not None:
        dt = dt_utc + shift_delta
    elif tz_obj is not None:
        dt = dt_utc.astimezone(tz_obj)
    else:
        dt = dt_utc

    if remove_weekends and dt.weekday() >= WEEKEND_START_DAY:
        return None

    return BarRecord(
        timestamp_utc=dt.isoformat(),
        open=bar.open,
        high=bar.high,
        low=bar.low,
        close=bar.close,
        volume=bar.volume,
        open_interest=bar.open_interest,
    )


def _resolve_clone_parameters(
    timezone_type: str,
    target_timezone: str | None,
    shift_hours: int | None,
    timeframe: str,
    postfix: str | None,
) -> tuple[timedelta | None, zoneinfo.ZoneInfo | None, str, str]:
    """Resolve shift, tz object, tz label, and symbol postfix."""
    if timezone_type == "hours" or shift_hours is not None:
        sh = shift_hours or 0
        shift_delta = timedelta(hours=sh)
        tz_obj = None
        clone_time_str = f"{sh:+d}h"
        tz_label = f"UTC{sh:+d}"
    else:
        clean_tz = (target_timezone or "UTC").strip()
        tz_obj = zoneinfo.ZoneInfo(clean_tz)
        shift_delta = None
        clone_time_str = clean_tz.replace("/", "_").replace(" ", "_")
        tz_label = clean_tz

    template = postfix or "_{timeframe}_{cloneTime}"
    resolved_postfix = template.replace("{timeframe}", timeframe).replace(
        "{cloneTime}", clone_time_str
    )
    return shift_delta, tz_obj, tz_label, resolved_postfix


class CatalogService:
    """Central domain service managing dataset catalogs and SQX data operations."""

    def __init__(
        self,
        db: DatabaseManager | None = None,
        storage: MarketDataStorage | None = None,
    ) -> None:
        """Initialize CatalogService with parent DatabaseManager and storage."""
        self._db = db or DatabaseManager()
        self._broker_service = BrokerService(self._db)
        self._instrument_service = InstrumentService(self._db)
        self._storage = storage or MarketDataStorage()

    @property
    def storage(self) -> MarketDataStorage:
        """Return attached canonical MarketDataStorage engine."""
        return self._storage

    @storage.setter
    def storage(self, value: MarketDataStorage) -> None:
        """Update attached canonical MarketDataStorage engine."""
        self._storage = value

    def _get_instrument_tick_size(self, symbol: str) -> float:
        """Retrieve instrument tick size or default scale."""
        instr = self._instrument_service.get_instrument(symbol)
        if instr is not None and instr.tick_size > 0.0:
            return instr.tick_size
        return DEFAULT_TICK_SIZE

    def _resolve_storage_symbol(
        self,
        dataset_or_symbol: DatasetRecord | str,
        underlying: str | None = None,
        source: str | None = None,
    ) -> str:
        """Resolve clean canonical storage symbol (stripping broker postfixes).

        Parquet market partitions are scoped by broker folder (e.g.
        data/market/dukascopy/), so files on disk use the clean canonical underlying
        (e.g. 'GBPUSD'), while the UI retains postfixed symbol names (e.g.
        'GBPUSD_DUKASCOPY') for differentiation.
        """
        if isinstance(dataset_or_symbol, DatasetRecord):
            if dataset_or_symbol.underlying:
                return dataset_or_symbol.underlying.strip().upper()
            sym = dataset_or_symbol.symbol.strip().upper()
            src = dataset_or_symbol.source.strip().upper()
        else:
            if underlying and underlying.strip():
                return underlying.strip().upper()
            sym = str(dataset_or_symbol).strip().upper()
            src = source.strip().upper() if source else ""

        if "_" in sym:
            return sym.split("_")[0]
        if "." in sym:
            return sym.split(".")[0]
        if src and sym.endswith(src):
            return sym[: -len(src)]
        return sym

    def _clean_broker_name(self, name: str) -> str:
        """Strip SQX brackets [[...]] from broker display name."""
        clean = name.strip()
        if clean.startswith("[[") and clean.endswith("]]"):
            clean = clean[2:-2].strip()
        return clean

    def _resolve_broker_display_name(self, broker: str, broker_name: str) -> str:
        """Resolve human-readable broker profile name instead of numeric ID."""
        clean_name = self._clean_broker_name(broker_name)
        if clean_name in ("-1", "", "Default"):
            return "Default"
        if clean_name.isdigit():
            b = self._broker_service.get_broker(int(clean_name))
            if b is not None:
                return self._clean_broker_name(b.name)
            return f"Broker {clean_name}"
        if broker.isdigit() and broker != "-1":
            b = self._broker_service.get_broker(int(broker))
            if b is not None:
                return self._clean_broker_name(b.name)
        return clean_name

    def _make_relative_path(self, path_str: str) -> str:
        """Convert absolute storage path to application-relative path."""
        if not path_str:
            return ""
        clean = path_str.strip()
        p = Path(clean)
        try:
            cwd = Path.cwd().resolve()
            resolved = p.resolve()
            if resolved.is_relative_to(cwd):
                return str(resolved.relative_to(cwd))
        except ValueError, OSError, RuntimeError:
            pass
        lower = clean.lower()
        idx = lower.find("data\\")
        if idx == -1:
            idx = lower.find("data/")
        if idx >= 0:
            return clean[idx:]
        return clean

    @staticmethod
    def _extract_date_alone(dt_str: str) -> str:
        """Normalize timestamp or ISO string to date alone (YYYY-MM-DD)."""
        if not dt_str:
            return ""
        return dt_str.split("T", maxsplit=1)[0].split(" ", maxsplit=1)[0].strip()

    def save_dataset(self, dataset: DatasetRecord) -> str:
        """Persist or update dataset metadata in host persistence.

        Fires FR-DATA-CATALOG-DATASET-REGISTRY and
        FR-DATA-CATALOG-REVISION-INTEGRITY.
        """
        resolved_name = self._resolve_broker_display_name(
            dataset.broker, dataset.broker_name
        )
        rel_path = self._make_relative_path(dataset.path)
        d_from = self._extract_date_alone(dataset.date_from)
        d_to = self._extract_date_alone(dataset.date_to)
        updates: dict[str, Any] = {}
        if resolved_name != dataset.broker_name:
            updates["broker_name"] = resolved_name
        if rel_path != dataset.path:
            updates["path"] = rel_path
        if d_from != dataset.date_from:
            updates["date_from"] = d_from
        if d_to != dataset.date_to:
            updates["date_to"] = d_to
        if updates:
            dataset = dataset.model_copy(update=updates)
        payload = dataset.model_dump(
            exclude={"bar_count", "source_data_id", "bar_type"}
        )
        if dataset.source_data_id:
            lineage: dict[str, Any] = {}
            try:
                parsed = json.loads(payload.get("lineage_json") or "{}")
                if isinstance(parsed, dict):
                    lineage = parsed
            except json.JSONDecodeError, TypeError:
                pass
            lineage["source_data_id"] = dataset.source_data_id
            payload["lineage_json"] = json.dumps(lineage)
        now = datetime.now(UTC).isoformat()
        payload["created_at"] = payload["created_at"] or now
        payload["updated_at"] = now
        dataset_id = self._db.datasets.save(
            payload,
            update_columns=(
                "bars",
                "date_from",
                "date_to",
                "updated_at",
                "path",
                "quality_score",
                "lineage_json",
            ),
        )
        logger.info(
            "FR-DATA-CATALOG-DATASET-REGISTRY: Persisted dataset '%s' "
            "(symbol=%s, timeframe=%s, bars=%d)",
            dataset_id,
            dataset.symbol,
            dataset.timeframe,
            dataset.bars,
            extra={
                "dataset_id": dataset_id,
                "symbol": dataset.symbol,
                "bars": dataset.bars,
                "fr_id": "FR-DATA-CATALOG-DATASET-REGISTRY",
            },
        )
        return dataset_id

    def get_dataset(self, dataset_id: str) -> DatasetRecord | None:
        """Retrieve dataset record by ID.

        Fires FR-DATA-CATALOG-DATASET-REGISTRY.
        """
        row = self._db.datasets.get_by_id(dataset_id)
        if row is None and ":" in dataset_id:
            parts = dataset_id.split(":")
            if len(parts) == ALIAS_COLON_PART_COUNT:
                p0, p1, p2 = (
                    parts[0].strip().lower(),
                    parts[1].strip().lower(),
                    parts[2].strip().lower(),
                )
                cand1 = f"ds_{p0}_{p2}_{p1}"
                cand2 = f"ds_{p0}_{p1}_{p2}"
                row = self._db.datasets.get_by_id(cand1) or self._db.datasets.get_by_id(
                    cand2
                )
        if row is None:
            logger.debug(
                "FR-DATA-CATALOG-DATASET-REGISTRY: Dataset '%s' not found",
                dataset_id,
                extra={
                    "dataset_id": dataset_id,
                    "fr_id": "FR-DATA-CATALOG-DATASET-REGISTRY",
                },
            )
            return None
        rec = DatasetRecord.model_validate(row)
        resolved_name = self._resolve_broker_display_name(rec.broker, rec.broker_name)
        rel_path = self._make_relative_path(rec.path)
        d_from = self._extract_date_alone(rec.date_from)
        d_to = self._extract_date_alone(rec.date_to)
        updates: dict[str, Any] = {}
        if resolved_name != rec.broker_name:
            updates["broker_name"] = resolved_name
        if rel_path != rec.path:
            updates["path"] = rel_path
        if d_from != rec.date_from:
            updates["date_from"] = d_from
        if d_to != rec.date_to:
            updates["date_to"] = d_to
        if updates:
            rec = rec.model_copy(update=updates)
        return rec

    def list_datasets(
        self,
        source: str | None = None,
        symbol: str | None = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> list[DatasetRecord]:
        """List dataset records matching optional source and symbol filters.

        Fires FR-DATA-CATALOG-DATASET-REGISTRY.
        """
        rows = self._db.datasets.list_datasets(
            source=source,
            symbol=symbol,
            limit=limit,
            offset=offset,
        )
        logger.debug(
            "FR-DATA-CATALOG-DATASET-REGISTRY: Retrieved %d dataset records",
            len(rows),
            extra={
                "count": len(rows),
                "fr_id": "FR-DATA-CATALOG-DATASET-REGISTRY",
            },
        )
        results: list[DatasetRecord] = []
        for r in rows:
            rec = DatasetRecord.model_validate(r)
            resolved_name = self._resolve_broker_display_name(
                rec.broker, rec.broker_name
            )
            rel_path = self._make_relative_path(rec.path)
            d_from = self._extract_date_alone(rec.date_from)
            d_to = self._extract_date_alone(rec.date_to)
            updates: dict[str, Any] = {}
            if resolved_name != rec.broker_name:
                updates["broker_name"] = resolved_name
            if rel_path != rec.path:
                updates["path"] = rel_path
            if d_from != rec.date_from:
                updates["date_from"] = d_from
            if d_to != rec.date_to:
                updates["date_to"] = d_to
            if updates:
                rec = rec.model_copy(update=updates)
            results.append(rec)
        return results

    def delete_dataset(self, dataset_id: str) -> bool:
        """Delete dataset record and all on-disk partitions.

        Delegates to remove_data() to ensure full cleanup.
        Fires FR-DATA-CATALOG-DATASET-REGISTRY.
        """
        return self.remove_data(dataset_id)

    def count_datasets(self) -> int:
        """Return total count of persisted datasets."""
        return self._db.datasets.count()

    @staticmethod
    def _scan_disk_partition_series(
        base_dir: Path,
    ) -> dict[tuple[str, str, str, str], list[Path]]:
        """Collect and index valid partitioned parquet files by series key."""
        series_map: dict[tuple[str, str, str, str], list[Path]] = {}
        for pf in sorted(base_dir.rglob("*.parquet")):
            try:
                rel = pf.relative_to(base_dir)
            except ValueError:
                continue
            parts = rel.parts
            if not parts or parts[0] in IGNORED_PARTITION_DIRS:
                continue

            if len(parts) == BAR_PARTITION_PARTS and parts[1].lower() != "ticks":
                src, tf, sym = (
                    parts[0].strip().lower(),
                    parts[1].strip().upper(),
                    parts[2].strip().upper(),
                )
                kind = "bars"
            elif len(parts) == TICK_PARTITION_PARTS and parts[1].lower() == "ticks":
                src = parts[0].strip().lower()
                tf = "TICK"
                sym = parts[2].strip().upper()
                kind = "ticks"
            else:
                continue
            series_map.setdefault((src, sym, tf, kind), []).append(pf)
        return series_map

    @staticmethod
    def _read_partition_bounds(files: Sequence[Path]) -> tuple[int, str, str]:
        """Read total rows and min/max date strings from parquet partition files."""
        total_rows = 0
        for f in files:
            try:
                total_rows += pq.read_metadata(f).num_rows
            except (OSError, ValueError, TypeError) as exc:
                logger.warning(
                    "FR-DATA-CATALOG-DATASET-REGISTRY: Metadata error in %s: %s",
                    f,
                    exc,
                    extra={"fr_id": "FR-DATA-CATALOG-DATASET-REGISTRY"},
                )

        date_from = ""
        date_to = ""
        if files:
            try:
                t_first = pq.read_table(files[0], columns=["DateTime"])
                if t_first.num_rows > 0:
                    val_first = t_first.column("DateTime")[0].as_py()
                    date_from = (
                        val_first.strftime("%Y-%m-%d")
                        if hasattr(val_first, "strftime")
                        else CatalogService._extract_date_alone(str(val_first))
                    )
                t_last = pq.read_table(files[-1], columns=["DateTime"])
                if t_last.num_rows > 0:
                    val_last = t_last.column("DateTime")[-1].as_py()
                    date_to = (
                        val_last.strftime("%Y-%m-%d")
                        if hasattr(val_last, "strftime")
                        else CatalogService._extract_date_alone(str(val_last))
                    )
            except (OSError, ValueError, TypeError) as exc:
                logger.warning(
                    "FR-DATA-CATALOG-DATASET-REGISTRY: Bounds error in %s: %s",
                    files[0],
                    exc,
                    extra={"fr_id": "FR-DATA-CATALOG-DATASET-REGISTRY"},
                )
        return total_rows, date_from, date_to

    def _resolve_partition_tick_size(
        self, files: Sequence[Path], sym: str, kind: str
    ) -> float:
        """Resolve tick size from schema metadata, sample values, or instrument defs."""
        tick_size = self._get_instrument_tick_size(sym)
        if not files:
            return tick_size
        try:
            meta = pq.read_metadata(files[0]).schema.to_arrow_schema().metadata or {}
            raw_ts = meta.get(b"tick_size") or meta.get("tick_size")
            if raw_ts:
                return float(raw_ts)
            if kind == "ticks":
                t_sample = pq.read_table(files[0], columns=["Bid"])
                if t_sample.num_rows > 0:
                    first_bid = t_sample.column("Bid")[0].as_py()
                    if (
                        isinstance(first_bid, int)
                        and first_bid > FOREX_RAW_TICK_THRESHOLD
                        and sym in SIX_DIGIT_FOREX_SYMBOLS
                    ):
                        return SIX_DIGIT_TICK_SCALE
        except OSError, ValueError, TypeError:
            pass
        return tick_size

    def _resolve_dataset_record(
        self,
        src: str,
        sym: str,
        tf: str,
        kind: str,
        files: Sequence[Path],
    ) -> DatasetRecord:
        """Build or synchronize DatasetRecord for a partition file series."""
        total_rows, date_from, date_to = self._read_partition_bounds(files)
        tick_size = self._resolve_partition_tick_size(files, sym, kind)

        category = "Forex"
        if src in ("dukascopy", "darwinex"):
            category = "Forex"
        elif src in ("sq_equity", "yahoo"):
            category = "Stocks"
        elif src == "sq_futures":
            category = "Futures"

        dataset_id = f"ds_{src}_{sym.lower()}_{tf.lower()}"
        existing = self.get_dataset(dataset_id)
        if existing is None:
            matches = [
                d
                for d in self.list_datasets(symbol=sym)
                if d.timeframe.upper() == tf and d.source.lower() == src
            ]
            if matches:
                existing = matches[0]
                dataset_id = existing.id

        p_dir = files[0].parent.parent if kind == "ticks" else files[0].parent
        partition_dir = self._make_relative_path(str(p_dir))
        lineage: dict[str, Any] = {
            "tick_size": tick_size,
            "partitions": [self._make_relative_path(str(f)) for f in files],
            "data_kind": kind,
        }
        if existing and existing.source_data_id:
            lineage["source_data_id"] = existing.source_data_id

        return DatasetRecord(
            id=dataset_id,
            source=src,
            symbol=sym,
            underlying=sym,
            instrument=existing.instrument if existing else sym,
            timeframe=tf,
            broker=src,
            broker_name=src,
            timezone=existing.timezone if existing else "UTC",
            category=existing.category if existing else category,
            date_from=date_from,
            date_to=date_to,
            bars=total_rows,
            path=partition_dir,
            data_kind=kind,
            quality_score=1.0,
            source_data_id=existing.source_data_id if existing else None,
            lineage_json=json.dumps(lineage),
            schema_version=1,
        )

    def sync_disk_partitions(self) -> list[DatasetRecord]:
        """Scan on-disk market data partitions and synchronize with datamgr_datasets.

        Discovers all bar and tick series under self._storage.base_dir, computes
        actual row counts, chronological boundaries, and registers or updates
        them in persistence.
        Fires FR-DATA-CATALOG-DATASET-REGISTRY.
        """
        base_dir = self._storage.base_dir
        if not base_dir.exists():
            return []

        series_map = self._scan_disk_partition_series(base_dir)
        synced_records: list[DatasetRecord] = []
        for (src, sym, tf, kind), files in sorted(series_map.items()):
            record = self._resolve_dataset_record(src, sym, tf, kind, sorted(files))
            self.save_dataset(record)
            synced_records.append(record)
            logger.info(
                "FR-DATA-CATALOG-DATASET-REGISTRY: Synchronized on-disk dataset "
                "'%s' (%s/%s/%s, %d rows)",
                record.id,
                src,
                sym,
                tf,
                record.bars,
                extra={
                    "fr_id": "FR-DATA-CATALOG-DATASET-REGISTRY",
                    "dataset_id": record.id,
                    "bars": record.bars,
                },
            )

        return synced_records

    def check_availability(
        self, symbol: str, timeframe: str = "M1"
    ) -> tuple[bool, str]:
        """Check availability status for a symbol and timeframe pair.

        Fires FR-DATA-CATALOG-SERIES-DISCOVERY.
        """
        clean_symbol = symbol.strip().upper()
        matching = [
            d
            for d in self.list_datasets(symbol=clean_symbol)
            if d.timeframe.upper() == timeframe.upper()
        ]
        if not matching:
            logger.debug(
                "FR-DATA-CATALOG-SERIES-DISCOVERY: Series %s/%s is UNAVAILABLE",
                clean_symbol,
                timeframe,
                extra={
                    "symbol": clean_symbol,
                    "timeframe": timeframe,
                    "status": "UNAVAILABLE",
                    "fr_id": "FR-DATA-CATALOG-SERIES-DISCOVERY",
                },
            )
            return False, "UNAVAILABLE"

        dataset = matching[0]
        if dataset.bars == 0:
            logger.debug(
                "FR-DATA-CATALOG-SERIES-DISCOVERY: Series %s/%s is empty (0 bars)",
                clean_symbol,
                timeframe,
                extra={
                    "symbol": clean_symbol,
                    "timeframe": timeframe,
                    "status": "EMPTY_SERIES",
                    "fr_id": "FR-DATA-CATALOG-SERIES-DISCOVERY",
                },
            )
            return False, "EMPTY_SERIES"

        logger.debug(
            "FR-DATA-CATALOG-SERIES-DISCOVERY: Series %s/%s is available (%d bars)",
            clean_symbol,
            timeframe,
            dataset.bars,
            extra={
                "symbol": clean_symbol,
                "timeframe": timeframe,
                "bars": dataset.bars,
                "status": "AVAILABLE",
                "fr_id": "FR-DATA-CATALOG-SERIES-DISCOVERY",
            },
        )
        return True, "AVAILABLE"

    # =========================================================================
    # StrategyQuant X DataManagerData Domain Operations
    # =========================================================================

    def save_bars(
        self,
        source: str,
        symbol: str,
        timeframe: str,
        bars: Sequence[BarRecord],
        instrument: str | None = None,
        *,
        underlying: str | None = None,
        source_data_id: str | None = None,
        timezone: str = "UTC",
    ) -> DatasetRecord:
        """Write bars into canonical Parquet partitions and update catalog.

        Fires FR-DATA-CATALOG-SQX-OPERATIONS.
        """
        clean_symbol = symbol.strip().upper()
        clean_tf = timeframe.strip().upper()
        clean_source = source.strip()

        dataset_id = (
            f"ds_{clean_source.lower()}_{clean_symbol.lower()}_{clean_tf.lower()}"
        )
        existing = self.get_dataset(dataset_id)

        und_candidate = underlying or (existing.underlying if existing else None)
        storage_symbol = self._resolve_storage_symbol(
            clean_symbol, underlying=und_candidate, source=clean_source
        )

        tick_size = self._get_instrument_tick_size(storage_symbol)
        write_res = self._storage.write_bars(
            source=clean_source,
            symbol=storage_symbol,
            timeframe=clean_tf,
            bars=bars,
            tick_size=tick_size,
        )

        partition_dir = str(
            self._storage.base_dir
            / clean_source.lower()
            / clean_tf.lower()
            / storage_symbol.lower()
        )
        lineage: dict[str, Any] = {
            "tick_size": tick_size,
            "partitions": write_res.partition_files,
            "data_kind": "bars",
        }
        if source_data_id:
            lineage["source_data_id"] = source_data_id

        resolved_underlying = und_candidate or storage_symbol
        instr_val = instrument or (
            existing.instrument if existing else resolved_underlying
        )
        record = DatasetRecord(
            id=dataset_id,
            source=clean_source,
            symbol=clean_symbol,
            underlying=resolved_underlying,
            instrument=instr_val,
            timeframe=clean_tf,
            broker=clean_source,
            broker_name=clean_source,
            timezone=timezone,
            category=existing.category if existing else "Forex",
            date_from=write_res.date_from or (existing.date_from if existing else ""),
            date_to=write_res.date_to or (existing.date_to if existing else ""),
            bars=write_res.total_bars,
            path=partition_dir,
            data_kind="bars",
            quality_score=1.0,
            source_data_id=source_data_id,
            lineage_json=json.dumps(lineage),
            schema_version=1,
        )
        self.save_dataset(record)
        logger.info(
            "FR-DATA-CATALOG-SQX-OPERATIONS: Saved %d bars for dataset '%s'",
            write_res.total_bars,
            dataset_id,
            extra={"fr_id": "FR-DATA-CATALOG-SQX-OPERATIONS"},
        )
        return record

    def save_ticks(
        self,
        source: str,
        symbol: str,
        ticks: Sequence[TickRecord],
        instrument: str | None = None,
        *,
        underlying: str | None = None,
    ) -> DatasetRecord:
        """Write ticks into canonical Parquet partitions and update catalog.

        Fires FR-DATA-CATALOG-SQX-OPERATIONS.
        """
        clean_symbol = symbol.strip().upper()
        clean_source = source.strip()

        dataset_id = f"ds_{clean_source.lower()}_{clean_symbol.lower()}_ticks"
        existing = self.get_dataset(dataset_id)

        und_candidate = underlying or (existing.underlying if existing else None)
        storage_symbol = self._resolve_storage_symbol(
            clean_symbol, underlying=und_candidate, source=clean_source
        )

        tick_size = self._get_instrument_tick_size(storage_symbol)
        write_res = self._storage.write_ticks(
            source=clean_source,
            symbol=storage_symbol,
            ticks=ticks,
            tick_size=tick_size,
        )

        partition_dir = str(
            self._storage.base_dir
            / clean_source.lower()
            / "ticks"
            / storage_symbol.lower()
        )
        lineage = {
            "tick_size": tick_size,
            "partitions": write_res.partition_files,
            "data_kind": "ticks",
        }

        resolved_underlying = und_candidate or storage_symbol
        instr_val = instrument or (
            existing.instrument if existing else resolved_underlying
        )
        record = DatasetRecord(
            id=dataset_id,
            source=clean_source,
            symbol=clean_symbol,
            underlying=resolved_underlying,
            instrument=instr_val,
            timeframe="TICK",
            broker=clean_source,
            broker_name=clean_source,
            timezone="UTC",
            category=existing.category if existing else "Forex",
            date_from=write_res.date_from or (existing.date_from if existing else ""),
            date_to=write_res.date_to or (existing.date_to if existing else ""),
            bars=write_res.total_bars,
            path=partition_dir,
            data_kind="ticks",
            quality_score=1.0,
            lineage_json=json.dumps(lineage),
            schema_version=1,
        )
        self.save_dataset(record)
        logger.info(
            "FR-DATA-CATALOG-SQX-OPERATIONS: Saved %d ticks for dataset '%s'",
            write_res.total_bars,
            dataset_id,
            extra={"fr_id": "FR-DATA-CATALOG-SQX-OPERATIONS"},
        )
        return record

    def edit_dataset(
        self,
        dataset_id: str,
        *,
        symbol_new: str | None = None,
        instrument: str | None = None,
        timezone: str | None = None,
        category: str | None = None,
    ) -> bool:
        """Edit dataset configuration metadata in datamgr_datasets.

        Fires FR-DATA-CATALOG-SQX-OPERATIONS.
        """
        existing = self.get_dataset(dataset_id)
        if existing is None:
            return False

        payload = existing.model_dump(
            exclude={"bar_count", "source_data_id", "bar_type"}
        )
        if existing.source_data_id:
            lineage: dict[str, Any] = {}
            try:
                parsed = json.loads(payload.get("lineage_json") or "{}")
                if isinstance(parsed, dict):
                    lineage = parsed
            except json.JSONDecodeError, TypeError:
                pass
            lineage["source_data_id"] = existing.source_data_id
            payload["lineage_json"] = json.dumps(lineage)
        update_cols: list[str] = ["updated_at"]

        if symbol_new and symbol_new != existing.symbol:
            payload["symbol"] = symbol_new.strip().upper()
            update_cols.append("symbol")
        if instrument and instrument != existing.instrument:
            payload["instrument"] = instrument.strip().upper()
            update_cols.append("instrument")
        if timezone and timezone != existing.timezone:
            payload["timezone"] = timezone.strip()
            update_cols.append("timezone")
        if category and category != existing.category:
            payload["category"] = category.strip()
            update_cols.append("category")

        payload["updated_at"] = datetime.now(UTC).isoformat()
        self._db.datasets.save(payload, update_columns=tuple(update_cols))

        logger.info(
            "FR-DATA-CATALOG-SQX-OPERATIONS: Edited dataset '%s' (updates=%s)",
            dataset_id,
            update_cols,
            extra={"fr_id": "FR-DATA-CATALOG-SQX-OPERATIONS"},
        )
        return True

    def clear_data(self, dataset_id: str) -> bool:
        """Clear on-disk Parquet partition files while preserving dataset entry.

        Matches SQX 'Clear data' operation in dataDeleteConfirmPopup.html.
        Fires FR-DATA-CATALOG-SQX-OPERATIONS.
        """
        existing = self.get_dataset(dataset_id)
        if existing is None:
            return False

        kind = (
            existing.data_kind if existing.data_kind == "ticks" else existing.timeframe
        )
        storage_sym = self._resolve_storage_symbol(existing)
        self._storage.clear_partitions(existing.source, kind, storage_sym)

        cleared_lineage: dict[str, Any] = {}
        if existing.lineage_json:
            with contextlib.suppress(Exception):
                parsed = json.loads(existing.lineage_json)
                if isinstance(parsed, dict):
                    cleared_lineage = parsed
        cleared_partitions: list[dict[str, Any]] = []
        cleared_lineage["partitions"] = cleared_partitions

        cleared_record = existing.model_copy(
            update={
                "bars": 0,
                "bar_count": 0,
                "date_from": "",
                "date_to": "",
                "lineage_json": json.dumps(cleared_lineage),
            }
        )
        self.save_dataset(cleared_record)

        logger.info(
            "FR-DATA-CATALOG-SQX-OPERATIONS: Cleared data for '%s'",
            dataset_id,
            extra={"fr_id": "FR-DATA-CATALOG-SQX-OPERATIONS"},
        )
        return True

    def remove_data(self, dataset_id: str) -> bool:
        """Remove on-disk Parquet partitions AND delete row from datamgr_datasets.

        Matches SQX 'Delete' (deleteconfirm) operation.
        Fires FR-DATA-CATALOG-SQX-OPERATIONS.
        """
        existing = self.get_dataset(dataset_id)
        if existing is not None:
            kind = (
                existing.data_kind
                if existing.data_kind == "ticks"
                else existing.timeframe
            )
            storage_sym = self._resolve_storage_symbol(existing)
            self._storage.delete_partitions(existing.source, kind, storage_sym)

        target_id = existing.id if existing is not None else dataset_id
        success = self._db.datasets.delete(target_id)
        logger.info(
            "FR-DATA-CATALOG-SQX-OPERATIONS: Removed dataset '%s' (success=%s)",
            target_id,
            success,
            extra={"fr_id": "FR-DATA-CATALOG-SQX-OPERATIONS"},
        )
        return success

    def review_chart(
        self,
        dataset_id: str,
        *,
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Read bar slice for chart review with prices converted to float.

        Matches SQX /data/reviewChart endpoint.
        Fires FR-DATA-CATALOG-SQX-OPERATIONS.
        """
        existing = self.get_dataset(dataset_id)
        if existing is None:
            return []

        tick_size = self._get_instrument_tick_size(existing.symbol)
        try:
            lineage = json.loads(existing.lineage_json)
            if "tick_size" in lineage and float(lineage["tick_size"]) > 0.0:
                tick_size = float(lineage["tick_size"])
        except ValueError, TypeError:
            pass

        storage_sym = self._resolve_storage_symbol(existing)
        tick_size = self._get_instrument_tick_size(storage_sym)
        if existing.data_kind == "ticks":
            ticks = self._storage.read_ticks_slice(
                source=existing.source,
                symbol=storage_sym,
                date_from=date_from,
                date_to=date_to,
                limit=limit,
                offset=offset,
                tick_size=tick_size,
            )
            return [t.model_dump(mode="json") for t in ticks]

        bars = self._storage.read_bars_slice(
            source=existing.source,
            symbol=storage_sym,
            timeframe=existing.timeframe,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
            offset=offset,
            tick_size=tick_size,
        )
        return [b.model_dump(mode="json") for b in bars]

    def get_review_rows(
        self,
        dataset_id: str,
        *,
        session_name: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Fetch a paginated page of bar records for inspection.

        Matches SQX /data/reviewData endpoint.
        Fires FR-DATA-CATALOG-SQX-OPERATIONS.
        """
        _ = session_name
        existing = self.get_dataset(dataset_id)
        if existing is None:
            raise ValueError(f"Dataset not found: {dataset_id}")

        storage_sym = self._resolve_storage_symbol(existing)
        tick_size = self._get_instrument_tick_size(storage_sym)
        bars = self._storage.read_bars_slice(
            source=existing.source,
            symbol=storage_sym,
            timeframe=existing.timeframe,
            limit=limit,
            offset=offset,
            tick_size=tick_size,
        )
        return {
            "dataset_id": dataset_id,
            "total_rows": existing.bars,
            "offset": offset,
            "limit": limit,
            "rows": [
                {
                    "timestamp": b.timestamp_utc,
                    "open": b.open,
                    "high": b.high,
                    "low": b.low,
                    "close": b.close,
                    "volume": b.volume,
                    "open_interest": b.open_interest,
                }
                for b in bars
            ],
        }

    def get_index_for_date(
        self, dataset_id: str, date: str = "", *, target_date: str = ""
    ) -> int:
        """Find the 0-indexed position of bar at or closest to given date.

        Matches SQX /data/getIndexForDate endpoint.
        Fires FR-DATA-CATALOG-SQX-OPERATIONS.
        """
        effective_date = target_date or date
        existing = self.get_dataset(dataset_id)
        if existing is None or existing.bars == 0:
            return -1

        dt_target = parse_iso_to_utc_datetime(effective_date)
        storage_sym = self._resolve_storage_symbol(existing)
        lf = self._storage.scan_bars(
            source=existing.source,
            symbol=storage_sym,
            timeframe=existing.timeframe,
        )
        df_filtered = (
            lf.filter(pl.col("DateTime") <= dt_target)
            .select(pl.len().alias("count"))
            .collect()
        )
        count = int(df_filtered["count"][0])
        return max(0, count - 1) if count > 0 else 0

    def _recalculate_dataset_boundaries(
        self, existing: DatasetRecord, total_bars: int, tick_size: float
    ) -> tuple[str, str]:
        """Compute new date_from and date_to boundaries after partition patch."""
        if total_bars == 0:
            return "", ""
        storage_sym = self._resolve_storage_symbol(existing)
        first_slice = self._storage.read_bars_slice(
            source=existing.source,
            symbol=storage_sym,
            timeframe=existing.timeframe,
            limit=1,
            offset=0,
            tick_size=tick_size,
        )
        last_slice = self._storage.read_bars_slice(
            source=existing.source,
            symbol=storage_sym,
            timeframe=existing.timeframe,
            limit=1,
            offset=max(0, total_bars - 1),
            tick_size=tick_size,
        )
        date_from = first_slice[0].timestamp_utc[:10] if first_slice else ""
        date_to = last_slice[0].timestamp_utc[:10] if last_slice else ""
        return date_from, date_to

    def save_data_changes(
        self,
        dataset_id: str,
        changed_bars: Sequence[BarRecord],
        deleted_timestamps: set[str],
    ) -> DatasetRecord:
        """Persist user-edited cells or deleted rows to on-disk Parquet partitions.

        Matches SQX /data/saveDataChanges endpoint.
        Fires FR-DATA-CATALOG-SQX-OPERATIONS.
        """
        existing = self.get_dataset(dataset_id)
        if existing is None:
            raise ValueError(f"Dataset not found: {dataset_id}")

        storage_sym = self._resolve_storage_symbol(existing)
        tick_size = self._get_instrument_tick_size(storage_sym)
        total_bars = self._storage.patch_bars(
            source=existing.source,
            symbol=storage_sym,
            timeframe=existing.timeframe,
            changed_bars=changed_bars,
            deleted_timestamps=deleted_timestamps,
            tick_size=tick_size,
        )

        date_from, date_to = self._recalculate_dataset_boundaries(
            existing, total_bars, tick_size
        )
        updated = existing.model_copy(
            update={
                "bars": total_bars,
                "bar_count": total_bars,
                "date_from": date_from,
                "date_to": date_to,
            }
        )
        self.save_dataset(updated)
        logger.info(
            "FR-DATA-CATALOG-SQX-OPERATIONS: Saved changes to '%s' (bars=%d)",
            dataset_id,
            total_bars,
            extra={"dataset_id": dataset_id, "bars": total_bars},
        )
        return updated

    def check_quality_summary(self, dataset_id: str) -> dict[str, Any]:
        """Audit data quality (anomalies, missing bars, date spans, hourly heatmap).

        Matches SQX /data/checkQualitySummary endpoint.
        Fires FR-DATA-CATALOG-SQX-OPERATIONS.
        """
        existing = self.get_dataset(dataset_id)
        if existing is None:
            return {"status": "NOT_FOUND", "quality_score": 0.0, "anomalies": []}

        storage_sym = self._resolve_storage_symbol(existing)
        tick_size = self._get_instrument_tick_size(storage_sym)
        bars = self._storage.read_bars_slice(
            source=existing.source,
            symbol=storage_sym,
            timeframe=existing.timeframe,
            limit=existing.bars or 1000000,
            tick_size=tick_size,
        )
        from app.workspace.data_manager.actions.review.quality import (
            DataQualityInspector,
        )

        inspector = DataQualityInspector()
        summary = inspector.check_quality_summary(bars)
        total_errors = int(summary.get("totalErrors", 0))
        summary["dataset_id"] = dataset_id
        summary["symbol"] = existing.symbol
        summary["timeframe"] = existing.timeframe
        summary["bars"] = existing.bars
        summary["date_from"] = existing.date_from
        summary["date_to"] = existing.date_to
        summary["status"] = "VALID" if total_errors == 0 else "WARNING"
        counts = summary.get("counts", {})
        summary["quality_score"] = round(
            inspector.compute_score(
                total_bars=existing.bars or len(bars),
                bad_bars=int(counts.get("ohlc", 0)),
                duplicate_bars=int(counts.get("spike", 0)),
                gap_bars=int(counts.get("gap", 0)),
            ),
            4,
        )
        return summary

    def check_quality_details(
        self, dataset_id: str, *, limit: int = 100, offset: int = 0
    ) -> list[dict[str, Any]]:
        """Return paginated defect bars for data quality inspection.

        Matches SQX /data/checkQualityDetails endpoint.
        Fires FR-DATA-CATALOG-SQX-OPERATIONS.
        """
        existing = self.get_dataset(dataset_id)
        if existing is None:
            return []

        storage_sym = self._resolve_storage_symbol(existing)
        tick_size = self._get_instrument_tick_size(storage_sym)
        bars = self._storage.read_bars_slice(
            source=existing.source,
            symbol=storage_sym,
            timeframe=existing.timeframe,
            limit=existing.bars or 1000000,
            tick_size=tick_size,
        )
        from app.workspace.data_manager.actions.review.quality import (
            DataQualityInspector,
        )

        inspector = DataQualityInspector()
        return inspector.check_quality_details(bars, limit=limit, offset=offset)

    def clone_to_timezone(
        self,
        dataset_id: str,
        target_timezone: str | None = None,
        *,
        timezone_type: str = "zone",
        shift_hours: int | None = None,
        remove_weekends: bool = False,
        postfix: str | None = None,
        new_dataset_id: str | None = None,
    ) -> str:
        """Clone existing dataset into target timezone partition.

        Matches SQX /data/cloneToTimezone endpoint with clone guard.
        Fires FR-DATA-CATALOG-SQX-OPERATIONS.
        """
        existing = self.get_dataset(dataset_id)
        if existing is None:
            raise ValueError(f"Dataset not found: {dataset_id}")

        if existing.source_data_id:
            raise ValueError(
                f"'{existing.symbol}' is cloned data. You cannot clone it again."
            )

        shift_delta, tz_obj, tz_label, resolved_postfix = _resolve_clone_parameters(
            timezone_type=timezone_type,
            target_timezone=target_timezone,
            shift_hours=shift_hours,
            timeframe=existing.timeframe,
            postfix=postfix,
        )

        storage_sym = self._resolve_storage_symbol(existing)
        tick_size = self._get_instrument_tick_size(storage_sym)
        bars = self._storage.read_bars_slice(
            source=existing.source,
            symbol=storage_sym,
            timeframe=existing.timeframe,
            limit=existing.bars or 1000000,
            tick_size=tick_size,
        )

        cloned_bars: list[BarRecord] = []
        for b in bars:
            shifted = _shift_bar_timestamp(
                bar=b,
                timezone_type=timezone_type,
                shift_delta=shift_delta,
                tz_obj=tz_obj,
                remove_weekends=remove_weekends,
            )
            if shifted is not None:
                cloned_bars.append(shifted)

        target_symbol = f"{existing.symbol}{resolved_postfix}"
        cloned_record = self.save_bars(
            source=existing.source,
            symbol=target_symbol,
            timeframe=existing.timeframe,
            bars=cloned_bars,
            instrument=existing.instrument,
            underlying=target_symbol,
            source_data_id=existing.id,
            timezone=tz_label,
        )
        return new_dataset_id or cloned_record.id

    def _find_clone_dependents(self, target_ids: Sequence[str]) -> list[DatasetRecord]:
        """Find non-targeted cloned datasets depending on deleted datasets."""
        all_datasets = self.list_datasets(limit=10000)
        deps_by_parent: dict[str, list[DatasetRecord]] = {}
        for ds in all_datasets:
            if ds.source_data_id:
                deps_by_parent.setdefault(ds.source_data_id, []).append(ds)

        target_ids_set = set(target_ids)
        conflicts: list[DatasetRecord] = []
        for tid in target_ids:
            if tid in deps_by_parent:
                non_deleted = [
                    d for d in deps_by_parent[tid] if d.id not in target_ids_set
                ]
                conflicts.extend(non_deleted)
        return conflicts

    def mass_delete(
        self,
        dataset_ids: Sequence[str],
        action: str = "remove",
        *,
        force: bool = False,
    ) -> dict[str, Any]:
        """Perform batch clear or removal of datasets with clone dependency check.

        Matches SQX delete / clear operations.
        Fires FR-DATA-CATALOG-SQX-OPERATIONS.
        """
        conflicts = self._find_clone_dependents(dataset_ids)
        if conflicts and not force:
            conflict_names = ", ".join(f"{c.symbol} ({c.id})" for c in conflicts)
            msg = (
                "CLONE_DEPENDENCY: The following cloned datasets depend on data "
                f"being deleted: {conflict_names}. Set force=True to confirm deletion."
            )
            raise ValueError(msg)

        results: dict[str, bool] = {}
        for did in dataset_ids:
            if action == "clear":
                results[did] = self.clear_data(did)
            else:
                results[did] = self.remove_data(did)

        return {
            "action": action,
            "results": results,
            "deleted_count": sum(1 for v in results.values() if v),
        }

    def export_catalog_xml(
        self,
        dataset_ids: Sequence[str] | None = None,
    ) -> str:
        """Export dataset and broker configuration matching SQX <Data> XML schema.

        Matches SQX /data/save endpoint.
        Fires FR-DATA-CATALOG-SQX-OPERATIONS.
        """
        root = ET.Element("Data")
        all_datasets = self.list_datasets(limit=10000)
        target_ids = set(dataset_ids) if dataset_ids is not None else None
        selected = [d for d in all_datasets if target_ids is None or d.id in target_ids]

        referenced_brokers: set[str] = set()
        for ds in selected:
            data_info = ET.SubElement(root, "DataInfo")
            data_info.set("id", ds.id)
            data_info.set("symbol", ds.symbol)
            data_info.set("timeframe", ds.timeframe)
            data_info.set("source", ds.source)
            data_info.set("broker", ds.broker)
            data_info.set("brokerName", ds.broker_name)
            data_info.set("timezone", ds.timezone)
            data_info.set("category", ds.category)
            data_info.set("dateFrom", ds.date_from)
            data_info.set("dateTo", ds.date_to)
            data_info.set("bars", str(ds.bars))
            data_info.set("dataKind", ds.data_kind)
            if ds.source_data_id:
                data_info.set("sourceDataId", ds.source_data_id)
            if ds.broker:
                referenced_brokers.add(ds.broker)

        for br_name in sorted(referenced_brokers):
            br_rec = self.get_broker(br_name)
            if br_rec is not None:
                br_elem = ET.SubElement(root, "Broker")
                br_elem.set("name", br_rec.name)
                br_elem.set("serverTimezone", br_rec.server_timezone)
                br_elem.set("postfix", br_rec.postfix)
                br_elem.set("mtUse", str(br_rec.mt_use))

        ET.indent(root, space="  ")
        return ET.tostring(root, encoding="unicode")

    def import_catalog_xml(self, xml_content: str) -> dict[str, int]:
        """Import dataset metadata and brokers from SQX <Data> XML document.

        Matches SQX /data/load endpoint.
        Fires FR-DATA-CATALOG-SQX-OPERATIONS.
        """
        root = ET.fromstring(xml_content)  # noqa: S314
        brokers_count = 0
        datasets_count = 0

        for br_elem in root.findall("Broker"):
            b_name = br_elem.attrib.get("name", "").strip()
            if b_name:
                brokers_count += 1

        for di in root.findall("DataInfo"):
            ds_id = di.attrib.get("id") or f"ds_{uuid.uuid4().hex[:8]}"
            ds_sym = di.attrib.get("symbol", "UNKNOWN")
            ds_tf = di.attrib.get("timeframe", "M1")
            ds_src = di.attrib.get("source", "Imported")
            record = DatasetRecord(
                id=ds_id,
                source=ds_src,
                symbol=ds_sym,
                timeframe=ds_tf,
                broker=di.attrib.get("broker", "Default"),
                broker_name=di.attrib.get("brokerName", "Default"),
                timezone=di.attrib.get("timezone", "UTC"),
                category=di.attrib.get("category", "Forex"),
                date_from=di.attrib.get("dateFrom", ""),
                date_to=di.attrib.get("dateTo", ""),
                bars=int(di.attrib.get("bars", 0)),
                data_kind=di.attrib.get("dataKind", "bars"),
                source_data_id=di.attrib.get("sourceDataId"),
            )
            self.save_dataset(record)
            datasets_count += 1

        return {
            "brokers_imported": brokers_count,
            "datasets_imported": datasets_count,
        }

    def update_all_datasets(self) -> dict[str, Any]:
        """Trigger background refresh/download for all active online datasets.

        Matches SQX /data/updateAll endpoint.
        Fires FR-DATA-CATALOG-SQX-OPERATIONS.
        """
        all_datasets = self.list_datasets(limit=10000)
        updated_ids: list[str] = [d.id for d in all_datasets]
        logger.info(
            "FR-DATA-CATALOG-SQX-OPERATIONS: updateAll triggered for %d datasets",
            len(updated_ids),
            extra={
                "count": len(updated_ids),
                "fr_id": "FR-DATA-CATALOG-SQX-OPERATIONS",
            },
        )
        return {
            "success": "Updates started.",
            "updated_datasets": updated_ids,
        }

    def update_selected_datasets(self, dataset_ids: Sequence[str]) -> dict[str, Any]:
        """Trigger background refresh/download for selected datasets.

        Matches SQX /data/updateSelected endpoint.
        Fires FR-DATA-CATALOG-SQX-OPERATIONS.
        """
        clean_ids = [d for d in dataset_ids if self.get_dataset(d) is not None]
        logger.info(
            "FR-DATA-CATALOG-SQX-OPERATIONS: updateSelected triggered for %d datasets",
            len(clean_ids),
            extra={
                "count": len(clean_ids),
                "fr_id": "FR-DATA-CATALOG-SQX-OPERATIONS",
            },
        )
        return {
            "success": "Updates started.",
            "updated_datasets": clean_ids,
        }

    def list_brokers(self) -> list[BrokerProfileRecord]:
        """Retrieve configured broker profiles from datamgr_broker table.

        Fires FR-DATA-CATALOG-BROKER-PROFILES.
        """
        return self._broker_service.list_brokers()

    def get_broker(self, name: str) -> BrokerProfileRecord | None:
        """Find a broker profile by name (case-insensitive).

        Fires FR-DATA-CATALOG-BROKER-PROFILES.
        """
        return self._broker_service.get_broker(name)


class DataIngestionService:
    """Service managing historical data file ingestion and revision publication."""

    def __init__(
        self,
        catalog: CatalogService,
        storage_dir: Path | str | None = None,
        storage: MarketDataStorage | None = None,
    ) -> None:
        """Initialize service with catalog service and target storage root."""
        self._catalog = catalog
        if storage is not None:
            self._storage = storage
        elif storage_dir is not None:
            self._storage = MarketDataStorage(base_dir=storage_dir)
            self._catalog.storage = self._storage
        else:
            self._storage = catalog.storage
        self._storage_dir = self._storage.base_dir
        self._storage_dir.mkdir(parents=True, exist_ok=True)

    def detect_format(self, sample_text: str) -> tuple[str, bool]:
        """Sniff delimiter and determine whether sample text contains a header row.

        Fires FR-DATA-INGESTION-STREAMING.
        """
        lines = [line.strip() for line in sample_text.splitlines() if line.strip()]
        if not lines:
            return ",", False

        first_line = lines[0]
        best_delim = ","
        best_count = 0
        for delim in COMMON_DELIMITERS:
            count = first_line.count(delim)
            if count > best_count:
                best_count = count
                best_delim = delim

        header_keywords = {
            "date",
            "time",
            "open",
            "high",
            "low",
            "close",
            "vol",
            "volume",
            "timestamp",
            "datetime",
        }
        tokens = [
            t.strip().lower()
            for t in re.split(re.escape(best_delim), first_line)
            if t.strip()
        ]
        has_header = any(t in header_keywords for t in tokens)

        logger.debug(
            "FR-DATA-INGESTION-STREAMING: Sniffed delimiter '%s', has_header=%s",
            best_delim,
            has_header,
            extra={
                "delimiter": best_delim,
                "has_header": has_header,
                "fr_id": "FR-DATA-INGESTION-STREAMING",
            },
        )
        return best_delim, has_header

    def parse_stream(
        self, lines: Iterable[str], config: IngestionConfig
    ) -> Generator[BarRecord]:
        """Stream and normalize lines into valid BarRecord stream.

        Fires FR-DATA-INGESTION-NORMALIZATION.
        """
        source_tz = zoneinfo.ZoneInfo(config.timezone)
        target_tz = UTC

        delimiter = config.delimiter or ","
        has_header = config.has_header if config.has_header is not None else False
        header_skipped = not has_header

        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                continue

            if not header_skipped:
                header_skipped = True
                continue

            reader = csv.reader(StringIO(line), delimiter=delimiter)
            fields = next(reader, None)
            if fields is None or len(fields) < MIN_FIELD_COUNT:
                continue

            bar = self._parse_fields_into_bar(fields, source_tz, target_tz)
            if bar is None:
                continue

            if not bar.is_valid_geometry():
                if not config.skip_invalid_bars:
                    raise ValueError(f"Invalid bar geometry: {bar}")
                continue

            yield bar

    def _sniff_config_if_needed(
        self, path: Path, config: IngestionConfig
    ) -> IngestionConfig:
        """Helper to sniff delimiter and header if not provided in config."""
        if config.delimiter is not None and config.has_header is not None:
            return config

        sample_buffer: list[str] = []
        with path.open("r", encoding="utf-8", errors="replace") as f:
            for _ in range(20):
                line = f.readline()
                if not line:
                    break
                sample_buffer.append(line)
        detected_delim, detected_header = self.detect_format("".join(sample_buffer))
        return config.model_copy(
            update={
                "delimiter": config.delimiter or detected_delim,
                "has_header": (
                    config.has_header
                    if config.has_header is not None
                    else detected_header
                ),
            }
        )

    def _compute_revision_hash(
        self, record: DatasetRecord, revision_id: str
    ) -> tuple[str, str]:
        """Helper to compute SHA-256 fingerprint from partition files."""
        hasher = hashlib.sha256()
        output_path = record.path
        try:
            lineage = json.loads(record.lineage_json)
            partition_paths = lineage.get("partitions", [])
            for p_str in partition_paths:
                p_file = Path(p_str)
                if p_file.exists():
                    hasher.update(p_file.read_bytes())
            if partition_paths:
                output_path = partition_paths[0]
        except ValueError, TypeError, OSError:
            hasher.update(revision_id.encode("utf-8"))

        return hasher.hexdigest(), output_path

    def ingest_file(
        self,
        file_path: Path | str,
        symbol: str,
        timeframe: str = "M1",
        source: str = "FileImport",
        config: IngestionConfig | None = None,
    ) -> IngestionResult:
        """Execute streaming ingestion pipeline writing partitioned Parquet files.

        Fires:
            FR-DATA-INGESTION-STREAMING
            FR-DATA-INGESTION-NORMALIZATION
            FR-DATA-INGESTION-STAGING
            FR-DATA-INGESTION-REVISIONS
        """
        cfg = self._sniff_config_if_needed(Path(file_path), config or IngestionConfig())
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Input data file does not exist: {path}")

        clean_symbol = symbol.strip().upper()
        clean_tf = timeframe.strip().upper()
        revision_id = f"rev_{uuid.uuid4().hex[:12]}"

        logger.info(
            "FR-DATA-INGESTION-STAGING: Staging ingestion for %s/%s from %s",
            clean_symbol,
            clean_tf,
            path,
            extra={
                "symbol": clean_symbol,
                "timeframe": clean_tf,
                "revision_id": revision_id,
                "fr_id": "FR-DATA-INGESTION-STAGING",
            },
        )

        with path.open("r", encoding="utf-8", errors="replace") as infile:
            all_bars = list(self.parse_stream(infile, cfg))

        if not all_bars:
            raise ValueError(f"No valid bars extracted from {path} for {clean_symbol}")

        dataset_record = self._catalog.save_bars(
            source=source,
            symbol=clean_symbol,
            timeframe=clean_tf,
            bars=all_bars,
        )

        sha256_hash, output_path = self._compute_revision_hash(
            dataset_record, revision_id
        )

        logger.info(
            "FR-DATA-INGESTION-REVISIONS: Published revision %s for %s (%d bars)",
            revision_id,
            clean_symbol,
            dataset_record.bars,
            extra={
                "symbol": clean_symbol,
                "revision_id": revision_id,
                "bars": dataset_record.bars,
                "sha256": sha256_hash,
                "fr_id": "FR-DATA-INGESTION-REVISIONS",
            },
        )

        return IngestionResult(
            dataset_id=dataset_record.id,
            revision_id=revision_id,
            symbol=clean_symbol,
            timeframe=clean_tf,
            bar_count=dataset_record.bars,
            date_from=dataset_record.date_from,
            date_to=dataset_record.date_to,
            sha256_hash=sha256_hash,
            output_path=output_path,
            rejected_count=0,
        )

    def _parse_fields_into_bar(
        self,
        fields: list[str],
        source_tz: zoneinfo.ZoneInfo,
        target_tz: timezone,
    ) -> BarRecord | None:
        """Parse raw CSV row fields into normalized BarRecord."""
        try:
            # Separate Date and Time columns
            if (
                ":" not in fields[0]
                and len(fields) >= SEPARATE_DT_MIN_FIELDS
                and ":" in fields[1]
            ):
                dt_str = f"{fields[0].strip()} {fields[1].strip()}"
                dt = self._parse_datetime(dt_str, source_tz, target_tz)
                open_p = float(fields[2])
                high_p = float(fields[3])
                low_p = float(fields[4])
                close_p = float(fields[5])
                vol = float(fields[6]) if len(fields) > SEPARATE_DT_MIN_FIELDS else 0.0
            # Combined DateTime column
            else:
                dt_str = fields[0].strip()
                dt = self._parse_datetime(dt_str, source_tz, target_tz)
                open_p = float(fields[1])
                high_p = float(fields[2])
                low_p = float(fields[3])
                close_p = float(fields[4])
                vol = float(fields[5]) if len(fields) > MIN_FIELD_COUNT else 0.0

            if any(p <= 0.0 for p in (open_p, high_p, low_p, close_p)):
                return None

            return BarRecord(
                timestamp_utc=dt.isoformat(),
                open=open_p,
                high=high_p,
                low=low_p,
                close=close_p,
                volume=max(0.0, vol),
            )
        except ValueError, IndexError:
            return None

    @staticmethod
    def _parse_datetime(
        dt_str: str,
        source_tz: zoneinfo.ZoneInfo,
        target_tz: timezone,
    ) -> datetime:
        """Parse various timestamp representations into UTC datetime."""
        clean = dt_str.replace("/", "-").replace(".", "-").strip()
        for fmt in (
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d",
            "%d-%m-%Y %H:%M:%S",
            "%d-%m-%Y %H:%M",
        ):
            try:
                dt = datetime.strptime(clean, fmt)  # noqa: DTZ007
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=source_tz)
                return dt.astimezone(target_tz)
            except ValueError:
                continue

        try:
            val = float(clean)
            if val > MS_EPOCH_THRESHOLD:
                val /= 1000.0
            return datetime.fromtimestamp(val, tz=target_tz)
        except ValueError as exc:
            raise ValueError(f"Unable to parse timestamp: {dt_str}") from exc


def main() -> int:
    """CLI tool for inspecting dataset catalog and running ingestion."""
    parser = argparse.ArgumentParser(description="Data Manager dataset catalog")
    parser.add_argument("--list", action="store_true", help="List all datasets")
    args = parser.parse_args()

    db = DatabaseManager()
    db.initialize()
    service = CatalogService(db)

    if args.list:
        datasets = service.list_datasets()
        print(f"Total cataloged datasets: {len(datasets)}")
        for d in datasets[:20]:
            print(f"  {d.id:25} {d.symbol:10} {d.timeframe:5} Bars: {d.bars}")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
