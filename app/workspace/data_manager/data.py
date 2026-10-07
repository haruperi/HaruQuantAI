"""Authoritative dataset catalog, ingestion pipeline, and revision management.

Description:
    Provides the central registry, metadata catalog, streaming file ingestion,
    and immutable revision management for quantitative market datasets within the
    Data Manager workspace, mirroring SQX DataManagerData. Normalizes bars into
    canonical OHLCV records with geometry verification, chronological ordering,
    and cryptographic SHA-256 fingerprinting. All persistence operations execute
    through the host DatabaseManager.

Purpose:
    FEAT-WORKSPACE-DATAMGR: Dataset catalog, streaming file ingestion, and
    immutable revision lineage management for the Data Manager workspace.

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
    service = DataIngestionService(catalog, storage_dir=Path("storage/datasets"))

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
import re
import sys
import uuid
import zoneinfo
from collections.abc import Generator, Iterable
from datetime import UTC, datetime, timezone
from io import StringIO
from pathlib import Path
from typing import Any, override

from pydantic import BaseModel, ConfigDict, Field

from app.host.logging import get_logger
from app.host.persistence import DatabaseManager
from app.workspace.data_manager.broker import BrokerProfileRecord, BrokerService

logger = get_logger(__name__)

DEFAULT_CHUNK_SIZE = 10000
COMMON_DELIMITERS = [",", ";", "\t", " ", "|"]
MIN_FIELD_COUNT = 5
SEPARATE_DT_MIN_FIELDS = 6
MS_EPOCH_THRESHOLD = 1e11


class BarRecord(BaseModel):
    """Normalized OHLCV market data bar."""

    model_config = ConfigDict(frozen=True)

    timestamp_utc: str = Field(description="ISO 8601 UTC timestamp")
    open: float = Field(gt=0.0, description="Opening price")
    high: float = Field(gt=0.0, description="Highest price")
    low: float = Field(gt=0.0, description="Lowest price")
    close: float = Field(gt=0.0, description="Closing price")
    volume: float = Field(default=0.0, ge=0.0, description="Bar traded volume")
    open_interest: float = Field(default=0.0, ge=0.0, description="Open interest")

    def is_valid_geometry(self) -> bool:
        """Validate bar price envelope consistency."""
        max_oc = max(self.open, self.close)
        min_oc = min(self.open, self.close)
        return self.high >= max_oc and self.low <= min_oc and self.high >= self.low


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
    """Central domain service managing dataset catalogs and broker profiles."""

    def __init__(self, db: DatabaseManager) -> None:
        """Initialize CatalogService with parent DatabaseManager."""
        self._db = db
        self._broker_service = BrokerService(db)

    def save_dataset(self, dataset: DatasetRecord) -> str:
        """Persist or update dataset metadata in host persistence.

        Fires FR-DATA-CATALOG-DATASET-REGISTRY and
        FR-DATA-CATALOG-REVISION-INTEGRITY.
        """
        payload = dataset.model_dump()
        dataset_id = self._db.datasets.save(payload)
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
        """Delete dataset record by ID.

        Fires FR-DATA-CATALOG-DATASET-REGISTRY.
        """
        success = self._db.datasets.delete(dataset_id)
        if success:
            logger.info(
                "FR-DATA-CATALOG-DATASET-REGISTRY: Deleted dataset '%s'",
                dataset_id,
                extra={
                    "dataset_id": dataset_id,
                    "fr_id": "FR-DATA-CATALOG-DATASET-REGISTRY",
                },
            )
        else:
            logger.warning(
                "FR-DATA-CATALOG-DATASET-REGISTRY: Failed deleting dataset '%s'",
                dataset_id,
                extra={
                    "dataset_id": dataset_id,
                    "fr_id": "FR-DATA-CATALOG-DATASET-REGISTRY",
                },
            )
        return success

    def count_datasets(self) -> int:
        """Return total count of persisted datasets."""
        return self._db.datasets.count()

    def check_availability(
        self, symbol: str, timeframe: str = "M1"
    ) -> tuple[bool, str]:
        """Check availability status for a symbol and timeframe pair.

        Returns:
            Tuple of (is_available, status_string) where status is:
            - 'AVAILABLE' if dataset exists with bars > 0
            - 'EMPTY_SERIES' if dataset exists but has 0 bars
            - 'UNAVAILABLE' if no matching dataset is cataloged

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
        self, catalog: CatalogService, storage_dir: Path | str | None = None
    ) -> None:
        """Initialize service with catalog service and target storage root."""
        self._catalog = catalog
        self._storage_dir = (
            Path(storage_dir) if storage_dir else Path("storage/datasets")
        )
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

    def ingest_file(
        self,
        file_path: Path | str,
        symbol: str,
        timeframe: str = "M1",
        source: str = "FileImport",
        config: IngestionConfig | None = None,
    ) -> IngestionResult:
        """Execute full streaming ingestion pipeline for historical file.

        Fires:
            FR-DATA-INGESTION-STREAMING
            FR-DATA-INGESTION-NORMALIZATION
            FR-DATA-INGESTION-STAGING
            FR-DATA-INGESTION-REVISIONS
        """
        cfg = config or IngestionConfig()
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Input data file does not exist: {path}")

        if cfg.delimiter is None or cfg.has_header is None:
            sample_buffer: list[str] = []
            with path.open("r", encoding="utf-8", errors="replace") as f:
                for _ in range(20):
                    line = f.readline()
                    if not line:
                        break
                    sample_buffer.append(line)
            detected_delim, detected_header = self.detect_format("".join(sample_buffer))
            cfg = cfg.model_copy(
                update={
                    "delimiter": cfg.delimiter or detected_delim,
                    "has_header": cfg.has_header
                    if cfg.has_header is not None
                    else detected_header,
                }
            )

        clean_symbol = symbol.strip().upper()
        clean_tf = timeframe.strip().upper()
        revision_id = f"rev_{uuid.uuid4().hex[:12]}"

        symbol_dir = self._storage_dir / clean_symbol / clean_tf
        symbol_dir.mkdir(parents=True, exist_ok=True)
        out_file = symbol_dir / f"{revision_id}.csv"

        logger.info(
            "FR-DATA-INGESTION-STAGING: Staging ingestion for %s/%s to %s",
            clean_symbol,
            clean_tf,
            out_file,
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

        all_bars.sort(key=lambda b: b.timestamp_utc)
        deduped: dict[str, BarRecord] = {}
        for b in all_bars:
            deduped[b.timestamp_utc] = b
        sorted_bars = list(deduped.values())
        sorted_bars.sort(key=lambda b: b.timestamp_utc)

        hasher = hashlib.sha256()
        with out_file.open("w", encoding="utf-8", newline="") as out_csv:
            writer = csv.writer(out_csv)
            writer.writerow(
                [
                    "timestamp",
                    "open",
                    "high",
                    "low",
                    "close",
                    "volume",
                    "open_interest",
                ]
            )
            for bar in sorted_bars:
                row_str = (
                    f"{bar.timestamp_utc},{bar.open:.6f},{bar.high:.6f},"
                    f"{bar.low:.6f},{bar.close:.6f},{bar.volume:.2f},"
                    f"{bar.open_interest:.2f}\n"
                )
                hasher.update(row_str.encode("utf-8"))
                writer.writerow(
                    [
                        bar.timestamp_utc,
                        bar.open,
                        bar.high,
                        bar.low,
                        bar.close,
                        bar.volume,
                        bar.open_interest,
                    ]
                )

        sha256_hash = hasher.hexdigest()
        date_from = sorted_bars[0].timestamp_utc
        date_to = sorted_bars[-1].timestamp_utc
        bar_count = len(sorted_bars)
        dataset_id = f"ds_{clean_symbol.lower()}_{clean_tf.lower()}"

        dataset_record = DatasetRecord(
            id=dataset_id,
            source=source,
            symbol=clean_symbol,
            timeframe=clean_tf,
            bars=bar_count,
            date_from=date_from,
            date_to=date_to,
            path=str(out_file),
            quality_score=1.0,
            schema_version=1,
        )
        self._catalog.save_dataset(dataset_record)

        logger.info(
            "FR-DATA-INGESTION-REVISIONS: Published revision %s for %s (%d bars)",
            revision_id,
            clean_symbol,
            bar_count,
            extra={
                "symbol": clean_symbol,
                "revision_id": revision_id,
                "bars": bar_count,
                "sha256": sha256_hash,
                "fr_id": "FR-DATA-INGESTION-REVISIONS",
            },
        )

        return IngestionResult(
            dataset_id=dataset_id,
            revision_id=revision_id,
            symbol=clean_symbol,
            timeframe=clean_tf,
            bar_count=bar_count,
            date_from=date_from,
            date_to=date_to,
            sha256_hash=sha256_hash,
            output_path=str(out_file),
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
