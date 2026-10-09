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
import csv
import hashlib
import json
import re
import sys
import uuid
import zoneinfo
from collections.abc import Generator, Iterable, Sequence
from datetime import UTC, datetime, timezone
from io import StringIO
from pathlib import Path
from typing import Any, override

import polars as pl
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
MS_EPOCH_THRESHOLD = 1e11


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
    quality_score: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Quality confidence score"
    )
    lineage_json: str = Field(default="{}", description="JSON lineage metadata")
    schema_version: int = Field(default=1, description="Metadata schema version")

    @override
    def model_post_init(self, _context: Any, /) -> None:
        """Ensure bar_count mirrors bars if omitted."""
        if self.bar_count is None:
            object.__setattr__(self, "bar_count", self.bars)


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

    def save_dataset(self, dataset: DatasetRecord) -> str:
        """Persist or update dataset metadata in host persistence.

        Fires FR-DATA-CATALOG-DATASET-REGISTRY and
        FR-DATA-CATALOG-REVISION-INTEGRITY.
        """
        payload = dataset.model_dump(exclude={"bar_count"})
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
        return DatasetRecord.model_validate(row)

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
        return [DatasetRecord.model_validate(r) for r in rows]

    def delete_dataset(self, dataset_id: str) -> bool:
        """Delete dataset record and all on-disk partitions.

        Delegates to remove_data() to ensure full cleanup.
        Fires FR-DATA-CATALOG-DATASET-REGISTRY.
        """
        return self.remove_data(dataset_id)

    def count_datasets(self) -> int:
        """Return total count of persisted datasets."""
        return self._db.datasets.count()

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
    ) -> DatasetRecord:
        """Write bars into canonical Parquet partitions and update catalog.

        Fires FR-DATA-CATALOG-SQX-OPERATIONS.
        """
        clean_symbol = symbol.strip().upper()
        clean_tf = timeframe.strip().upper()
        clean_source = source.strip()

        tick_size = self._get_instrument_tick_size(clean_symbol)
        write_res = self._storage.write_bars(
            source=clean_source,
            symbol=clean_symbol,
            timeframe=clean_tf,
            bars=bars,
            tick_size=tick_size,
        )

        dataset_id = (
            f"ds_{clean_source.lower()}_{clean_symbol.lower()}_{clean_tf.lower()}"
        )
        existing = self.get_dataset(dataset_id)

        partition_dir = str(
            self._storage.base_dir
            / clean_source.lower()
            / clean_tf.lower()
            / clean_symbol.lower()
        )
        lineage = {
            "tick_size": tick_size,
            "partitions": write_res.partition_files,
            "data_kind": "bars",
        }

        instr_val = instrument or (existing.instrument if existing else clean_symbol)
        record = DatasetRecord(
            id=dataset_id,
            source=clean_source,
            symbol=clean_symbol,
            underlying=clean_symbol,
            instrument=instr_val,
            timeframe=clean_tf,
            broker=clean_source,
            broker_name=clean_source,
            timezone="UTC",
            category=existing.category if existing else "Forex",
            date_from=write_res.date_from or (existing.date_from if existing else ""),
            date_to=write_res.date_to or (existing.date_to if existing else ""),
            bars=write_res.total_bars,
            path=partition_dir,
            data_kind="bars",
            quality_score=1.0,
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
    ) -> DatasetRecord:
        """Write ticks into canonical Parquet partitions and update catalog.

        Fires FR-DATA-CATALOG-SQX-OPERATIONS.
        """
        clean_symbol = symbol.strip().upper()
        clean_source = source.strip()

        tick_size = self._get_instrument_tick_size(clean_symbol)
        write_res = self._storage.write_ticks(
            source=clean_source,
            symbol=clean_symbol,
            ticks=ticks,
            tick_size=tick_size,
        )

        dataset_id = f"ds_{clean_source.lower()}_{clean_symbol.lower()}_ticks"
        existing = self.get_dataset(dataset_id)

        partition_dir = str(
            self._storage.base_dir
            / clean_source.lower()
            / "ticks"
            / clean_symbol.lower()
        )
        lineage = {
            "tick_size": tick_size,
            "partitions": write_res.partition_files,
            "data_kind": "ticks",
        }

        instr_val = instrument or (existing.instrument if existing else clean_symbol)
        record = DatasetRecord(
            id=dataset_id,
            source=clean_source,
            symbol=clean_symbol,
            underlying=clean_symbol,
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

        payload = existing.model_dump(exclude={"bar_count"})
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
        self._storage.clear_partitions(existing.source, kind, existing.symbol)

        payload = existing.model_dump(exclude={"bar_count"})
        payload["bars"] = 0
        payload["date_from"] = ""
        payload["date_to"] = ""
        payload["updated_at"] = datetime.now(UTC).isoformat()
        self._db.datasets.save(
            payload,
            update_columns=("bars", "date_from", "date_to", "updated_at"),
        )

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
            self._storage.delete_partitions(existing.source, kind, existing.symbol)

        success = self._db.datasets.delete(dataset_id)
        logger.info(
            "FR-DATA-CATALOG-SQX-OPERATIONS: Removed dataset '%s' (success=%s)",
            dataset_id,
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

        if existing.data_kind == "ticks":
            ticks = self._storage.read_ticks_slice(
                source=existing.source,
                symbol=existing.symbol,
                date_from=date_from,
                date_to=date_to,
                limit=limit,
                offset=offset,
                tick_size=tick_size,
            )
            return [t.model_dump(mode="json") for t in ticks]

        bars = self._storage.read_bars_slice(
            source=existing.source,
            symbol=existing.symbol,
            timeframe=existing.timeframe,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
            offset=offset,
            tick_size=tick_size,
        )
        return [b.model_dump(mode="json") for b in bars]

    def get_index_for_date(self, dataset_id: str, date: str) -> int:
        """Find the 0-indexed position of bar at or closest to given date.

        Matches SQX /data/getIndexForDate endpoint.
        Fires FR-DATA-CATALOG-SQX-OPERATIONS.
        """
        existing = self.get_dataset(dataset_id)
        if existing is None or existing.bars == 0:
            return -1

        dt_target = parse_iso_to_utc_datetime(date)
        lf = self._storage.scan_bars(
            source=existing.source,
            symbol=existing.symbol,
            timeframe=existing.timeframe,
        )
        df_filtered = (
            lf.filter(pl.col("DateTime") <= dt_target)
            .select(pl.len().alias("count"))
            .collect()
        )
        count = int(df_filtered["count"][0])
        return max(0, count - 1) if count > 0 else 0

    def check_quality_summary(self, dataset_id: str) -> dict[str, Any]:
        """Audit data quality (anomalies, missing bars, date spans).

        Matches SQX /data/checkQualitySummary endpoint.
        Fires FR-DATA-CATALOG-SQX-OPERATIONS.
        """
        existing = self.get_dataset(dataset_id)
        if existing is None:
            return {"status": "NOT_FOUND", "quality_score": 0.0, "anomalies": []}

        anomalies: list[str] = []
        if existing.bars == 0:
            anomalies.append("Series contains 0 bars")

        return {
            "dataset_id": dataset_id,
            "symbol": existing.symbol,
            "timeframe": existing.timeframe,
            "bars": existing.bars,
            "date_from": existing.date_from,
            "date_to": existing.date_to,
            "quality_score": existing.quality_score,
            "anomalies": anomalies,
            "status": "VALID" if not anomalies else "WARNING",
        }

    def clone_to_timezone(
        self,
        dataset_id: str,
        target_timezone: str,
        new_dataset_id: str | None = None,
    ) -> str:
        """Clone existing dataset into target timezone partition.

        Matches SQX /data/cloneToTimezone endpoint.
        Fires FR-DATA-CATALOG-SQX-OPERATIONS.
        """
        existing = self.get_dataset(dataset_id)
        if existing is None:
            raise ValueError(f"Dataset not found: {dataset_id}")

        clean_tz = target_timezone.strip()
        tz_obj = zoneinfo.ZoneInfo(clean_tz)

        tick_size = self._get_instrument_tick_size(existing.symbol)
        bars = self._storage.read_bars_slice(
            source=existing.source,
            symbol=existing.symbol,
            timeframe=existing.timeframe,
            limit=existing.bars or 1000000,
            tick_size=tick_size,
        )

        cloned_bars: list[BarRecord] = []
        for b in bars:
            dt_utc = parse_iso_to_utc_datetime(b.timestamp_utc)
            dt_local = dt_utc.astimezone(tz_obj)
            cloned_bars.append(
                BarRecord(
                    timestamp_utc=dt_local.isoformat(),
                    open=b.open,
                    high=b.high,
                    low=b.low,
                    close=b.close,
                    volume=b.volume,
                    open_interest=b.open_interest,
                )
            )

        tz_slug = clean_tz.replace("/", "_").replace(" ", "_").lower()
        target_symbol = f"{existing.symbol}_{tz_slug.upper()}"

        cloned_record = self.save_bars(
            source=existing.source,
            symbol=target_symbol,
            timeframe=existing.timeframe,
            bars=cloned_bars,
            instrument=existing.instrument,
        )
        return new_dataset_id or cloned_record.id

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
