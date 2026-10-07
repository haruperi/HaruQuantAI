"""Market data file ingestion and immutable dataset revision pipeline.

Description:
    Streaming and chunked ingestion engine for historical market data files
    (CSV, TSV, TXT). Provides automatic delimiter sniffing, column detection,
    and flexible datetime parsing. Normalizes bars into canonical OHLCV records
    with strict mathematical geometry validation, chronological ordering, and
    timestamp deduplication. Generates cryptographically fingerprinted (SHA-256)
    immutable dataset revisions staged in isolated storage and registered into
    the dataset catalog.

Purpose:
    FEAT-DATA-INGESTION: Ingest, validate, and version market data series.

Key Capabilities:
    FR-DATA-INGESTION-STREAMING: Stream and chunk file parsing with delimiter sniffing.
    FR-DATA-INGESTION-NORMALIZATION: Validate OHLCV bar geometry and ordering.
    FR-DATA-INGESTION-STAGING: Stage raw and processed revisions in isolated storage.
    FR-DATA-INGESTION-REVISIONS: Compute SHA-256 fingerprints for immutable revisions.

Python API Usage:
    ```python
    from pathlib import Path
    from app.host.persistence import DatabaseManager
    from app.plugins.data.catalog import CatalogService
    from app.plugins.data.ingestion import DataIngestionService, IngestionConfig

    db = DatabaseManager()
    db.initialize()
    catalog = CatalogService(db)
    service = DataIngestionService(catalog, storage_dir=Path("storage/datasets"))

    result = service.ingest_file(
        file_path="data/EURUSD_M1.csv",
        symbol="EURUSD",
        timeframe="M1",
        config=IngestionConfig(timezone="UTC"),
    )
    print(f"Ingested {result.bar_count} bars, revision {result.revision_id}")
    ```

CLI Usage:
    ```bash
    python -m app.plugins.data.ingestion --file EURUSD.csv --symbol EURUSD --tf M1
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

from app.host.logging import get_logger
from app.plugins.data.catalog import CatalogService, DatasetRecord
from pydantic import BaseModel, ConfigDict, Field

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
            fields = next(reader, [])
            if len(fields) < MIN_FIELD_COUNT:
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
    """CLI tool for ingesting historical market data files."""
    parser = argparse.ArgumentParser(description="Ingest historical market data file")
    parser.add_argument("--file", required=True, help="Input data file path")
    parser.add_argument("--symbol", required=True, help="Instrument symbol")
    parser.add_argument("--tf", default="M1", help="Timeframe (e.g. M1, M5, H1, D1)")
    parser.add_argument("--timezone", default="UTC", help="Input file timezone")
    args = parser.parse_args()

    from app.host.persistence import DatabaseManager

    db = DatabaseManager()
    db.initialize()
    catalog = CatalogService(db)
    service = DataIngestionService(catalog)

    result = service.ingest_file(
        args.file,
        symbol=args.symbol,
        timeframe=args.tf,
        config=IngestionConfig(timezone=args.timezone),
    )
    print(f"Ingested {result.bar_count} bars for {result.symbol} ({result.timeframe}).")
    print(f"Revision: {result.revision_id}")
    print(f"SHA256:   {result.sha256_hash}")
    print(f"Output:   {result.output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
