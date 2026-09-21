"""Immutable normalized dataset versions and Parquet manifest storage.

Feature:
    FEAT-DATA-DATASETS

Purpose:
    Provides content-addressed, immutable dataset versioning, Parquet columnar
    storage, lineage tracking, and manifest management matching StrategyQuant X
    custom data and history storage specifications.

Invariants:
    * Published datasets are immutable once created; SHA-256 integrity is enforced.
    * Storage files are written atomically using temporary files and filesystem replace.
    * Timestamps in manifests and loaded records are strictly timezone-aware UTC.
"""

from __future__ import annotations

import asyncio
import hashlib
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, override

import pyarrow as pa

try:
    import pyarrow.parquet as pq
except ImportError:
    pq = None

from app.contracts.data import (
    DATA_DATASETS,
    DATA_PERSISTENCE,
    BarRecord,
    DataPersistenceService,
    DatasetManifest,
    DatasetNotFoundError,
    TickRecord,
)
from app.contracts.data import (
    DatasetService as IDatasetService,
)
from app.kernel.feature import FeatureSpec
from app.kernel.logging import get_logger

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext

logger = get_logger(__name__)


def _require_pq() -> Any:
    """Return pyarrow.parquet module or raise RuntimeError if unavailable."""
    if pq is None:
        msg = "Parquet support is unavailable (pyarrow.parquet failed to load)"
        raise RuntimeError(msg)
    return pq


BARS_SCHEMA: pa.Schema = pa.schema(
    [
        pa.field("timestamp_utc", pa.timestamp("us")),
        pa.field("open", pa.float64()),
        pa.field("high", pa.float64()),
        pa.field("low", pa.float64()),
        pa.field("close", pa.float64()),
        pa.field("volume", pa.float64()),
        pa.field("source", pa.string()),
        pa.field("anomaly_flags", pa.int64()),
    ]
)

TICKS_SCHEMA: pa.Schema = pa.schema(
    [
        pa.field("timestamp_utc", pa.timestamp("us")),
        pa.field("bid", pa.float64()),
        pa.field("ask", pa.float64()),
        pa.field("sequence", pa.int64()),
        pa.field("bid_volume", pa.float64()),
        pa.field("ask_volume", pa.float64()),
        pa.field("flags", pa.int64()),
    ]
)


def _compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 digest of a local file."""
    hasher = hashlib.sha256()
    with file_path.open("rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def _atomic_write_parquet(table: pa.Table, target_file: Path) -> str:
    """Write table to temporary file and atomically replace target, returning SHA256."""
    target_file.parent.mkdir(parents=True, exist_ok=True)
    temp_file = target_file.with_name(
        f"{target_file.stem}.tmp_{uuid.uuid4().hex[:8]}.parquet"
    )
    try:
        _require_pq().write_table(
            table, temp_file, compression="zstd", compression_level=3
        )
        temp_file.replace(target_file)
    finally:
        temp_file.unlink(missing_ok=True)
    return _compute_sha256(target_file)


def _compute_bars_content_hash(bars: list[BarRecord]) -> str:
    """Compute deterministic SHA-256 hash over normalized bar records."""
    hasher = hashlib.sha256()
    for b in bars:
        ts_us = int(b.timestamp.astimezone(UTC).timestamp() * 1_000_000)
        hasher.update(
            f"{ts_us}:{b.open:.8f}:{b.high:.8f}:{b.low:.8f}:{b.close:.8f}:"
            f"{b.volume:.8f}:{b.source}:{b.anomaly_flags}\n".encode()
        )
    return hasher.hexdigest()


def _compute_ticks_content_hash(ticks: list[TickRecord]) -> str:
    """Compute deterministic SHA-256 hash over normalized tick records."""
    hasher = hashlib.sha256()
    for t in ticks:
        ts_us = int(t.timestamp.astimezone(UTC).timestamp() * 1_000_000)
        hasher.update(
            f"{ts_us}:{t.sequence}:{t.bid:.8f}:{t.ask:.8f}:{t.bid_volume:.8f}:"
            f"{t.ask_volume:.8f}:{t.flags}\n".encode()
        )
    return hasher.hexdigest()


def _file_exists(file_path: str | Path) -> bool:
    """Check if file exists synchronously."""
    return Path(file_path).exists()


def _read_parquet_bars(
    file_path: Path,
    start: datetime | None,
    end: datetime | None,
) -> list[BarRecord]:
    """Synchronous worker to read bars from Parquet with range filtering."""
    if not file_path.exists():
        msg = f"Parquet file {file_path} does not exist"
        raise DatasetNotFoundError(msg)

    table = _require_pq().read_table(file_path)
    df_dict = table.to_pydict()

    ts_col = df_dict["timestamp_utc"]
    open_col = df_dict["open"]
    high_col = df_dict["high"]
    low_col = df_dict["low"]
    close_col = df_dict["close"]
    vol_col = df_dict["volume"]
    src_col = df_dict.get("source", [""] * len(ts_col))
    anom_col = df_dict.get("anomaly_flags", [0] * len(ts_col))

    bars: list[BarRecord] = []
    for i, raw_ts in enumerate(ts_col):
        if isinstance(raw_ts, datetime):
            ts = raw_ts if raw_ts.tzinfo else raw_ts.replace(tzinfo=UTC)
        else:
            ts = datetime.fromtimestamp(raw_ts / 1_000_000, tz=UTC)

        if start and ts < start:
            continue
        if end and ts > end:
            continue

        bars.append(
            BarRecord(
                timestamp=ts,
                open=float(open_col[i]),
                high=float(high_col[i]),
                low=float(low_col[i]),
                close=float(close_col[i]),
                volume=float(vol_col[i]),
                source=str(src_col[i]),
                anomaly_flags=int(anom_col[i]),
            )
        )
    return bars


def _read_parquet_ticks(
    file_path: Path,
    start: datetime | None,
    end: datetime | None,
) -> list[TickRecord]:
    """Synchronous worker to read ticks from Parquet with range filtering."""
    if not file_path.exists():
        msg = f"Parquet file {file_path} does not exist"
        raise DatasetNotFoundError(msg)

    table = _require_pq().read_table(file_path)
    df_dict = table.to_pydict()

    ts_col = df_dict["timestamp_utc"]
    bid_col = df_dict["bid"]
    ask_col = df_dict["ask"]
    seq_col = df_dict.get("sequence", [0] * len(ts_col))
    bid_v_col = df_dict.get("bid_volume", [0.0] * len(ts_col))
    ask_v_col = df_dict.get("ask_volume", [0.0] * len(ts_col))
    flag_col = df_dict.get("flags", [0] * len(ts_col))

    ticks: list[TickRecord] = []
    for i, raw_ts in enumerate(ts_col):
        if isinstance(raw_ts, datetime):
            ts = raw_ts if raw_ts.tzinfo else raw_ts.replace(tzinfo=UTC)
        else:
            ts = datetime.fromtimestamp(raw_ts / 1_000_000, tz=UTC)

        if start and ts < start:
            continue
        if end and ts > end:
            continue

        ticks.append(
            TickRecord(
                timestamp=ts,
                bid=float(bid_col[i]),
                ask=float(ask_col[i]),
                sequence=int(seq_col[i]),
                bid_volume=float(bid_v_col[i]),
                ask_volume=float(ask_v_col[i]),
                flags=int(flag_col[i]),
            )
        )
    return ticks


@dataclass(slots=True, frozen=True)
class DatasetConfig:
    """Configuration for dataset service."""

    storage_dir: Path = Path("data/datasets")


class DatasetServiceImpl(IDatasetService):
    """Concrete implementation of DatasetService protocol."""

    def __init__(
        self,
        persistence: DataPersistenceService,
        config: DatasetConfig | None = None,
    ) -> None:
        """Initialize dataset service.

        Args:
            persistence: Database persistence service.
            config: Optional configuration.
        """
        self._persistence = persistence
        self._config = config or DatasetConfig()

    @override
    async def get_manifest(self, dataset_id: str) -> DatasetManifest | None:
        """Retrieve dataset manifest by unique dataset ID."""
        return await self._persistence.get_dataset_manifest(dataset_id)

    @override
    async def list_manifests(
        self, symbol: str | None = None, timeframe: str | None = None
    ) -> list[DatasetManifest]:
        """List dataset manifests matching optional filter criteria."""
        return await self._persistence.list_dataset_manifests(
            symbol=symbol, timeframe=timeframe
        )

    @override
    async def save_manifest(self, manifest: DatasetManifest) -> DatasetManifest:
        """Register an immutable dataset manifest."""
        return await self._persistence.save_dataset_manifest(manifest)

    @override
    async def persist_bars(
        self,
        symbol: str,
        timeframe: str,
        source_id: str,
        bars: list[BarRecord],
        *,
        lineage: dict[str, Any] | None = None,
        quality_score: float | None = None,
    ) -> DatasetManifest:
        """Persist normalized bars into Parquet dataset and publish manifest."""
        clean_symbol = symbol.strip().upper()
        if not bars:
            msg = f"Cannot persist empty bar list for {clean_symbol}"
            raise ValueError(msg)

        sorted_bars = sorted(bars, key=lambda b: b.timestamp)
        start_time = sorted_bars[0].timestamp
        end_time = sorted_bars[-1].timestamp

        content_hash = _compute_bars_content_hash(sorted_bars)
        dataset_id = (
            f"ds_{clean_symbol.lower()}_{timeframe.lower()}_{content_hash[:16]}"
        )

        existing = await self._persistence.get_dataset_manifest(dataset_id)
        if existing is not None:
            file_exists = await asyncio.to_thread(_file_exists, existing.parquet_path)
            if file_exists:
                logger.info(
                    "bars_dataset_idempotent_republish",
                    dataset_id=dataset_id,
                    symbol=clean_symbol,
                )
                return existing

        timestamps = [
            b.timestamp.astimezone(UTC).replace(tzinfo=None) for b in sorted_bars
        ]
        opens = [b.open for b in sorted_bars]
        highs = [b.high for b in sorted_bars]
        lows = [b.low for b in sorted_bars]
        closes = [b.close for b in sorted_bars]
        volumes = [b.volume for b in sorted_bars]
        sources = [b.source for b in sorted_bars]
        anomalies = [b.anomaly_flags for b in sorted_bars]

        table = pa.Table.from_arrays(
            [
                pa.array(timestamps, type=pa.timestamp("us")),
                pa.array(opens, type=pa.float64()),
                pa.array(highs, type=pa.float64()),
                pa.array(lows, type=pa.float64()),
                pa.array(closes, type=pa.float64()),
                pa.array(volumes, type=pa.float64()),
                pa.array(sources, type=pa.string()),
                pa.array(anomalies, type=pa.int64()),
            ],
            schema=BARS_SCHEMA,
        )

        out_path = self._config.storage_dir / clean_symbol / f"{dataset_id}.parquet"
        sha256_hash = await asyncio.to_thread(_atomic_write_parquet, table, out_path)

        manifest = DatasetManifest(
            dataset_id=dataset_id,
            symbol=clean_symbol,
            timeframe=timeframe,
            data_kind="bars",
            source_id=source_id,
            start_time=start_time,
            end_time=end_time,
            row_count=len(sorted_bars),
            parquet_path=str(out_path.resolve()),
            sha256_hash=sha256_hash,
            schema_version=1,
            quality_score=quality_score if quality_score is not None else 1.0,
            lineage=lineage or {},
            created_at=datetime.now(UTC),
        )

        await self._persistence.save_dataset_manifest(manifest)
        logger.info(
            "bars_dataset_persisted",
            dataset_id=dataset_id,
            rows=len(sorted_bars),
            symbol=clean_symbol,
        )
        return manifest

    @override
    async def load_bars(
        self,
        dataset_id: str,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[BarRecord]:
        """Load normalized bars from a published dataset version."""
        manifest = await self.get_manifest(dataset_id)
        if manifest is None:
            msg = f"Dataset {dataset_id} not found"
            raise DatasetNotFoundError(msg)

        parquet_file = Path(manifest.parquet_path)
        return await asyncio.to_thread(_read_parquet_bars, parquet_file, start, end)

    @override
    async def persist_ticks(
        self,
        symbol: str,
        source_id: str,
        ticks: list[TickRecord],
        *,
        lineage: dict[str, Any] | None = None,
        quality_score: float | None = None,
    ) -> DatasetManifest:
        """Persist normalized ticks into Parquet dataset and publish manifest."""
        clean_symbol = symbol.strip().upper()
        if not ticks:
            msg = f"Cannot persist empty tick list for {clean_symbol}"
            raise ValueError(msg)

        sorted_ticks = sorted(ticks, key=lambda t: (t.timestamp, t.sequence))
        start_time = sorted_ticks[0].timestamp
        end_time = sorted_ticks[-1].timestamp

        content_hash = _compute_ticks_content_hash(sorted_ticks)
        dataset_id = f"ds_{clean_symbol.lower()}_ticks_{content_hash[:16]}"

        existing = await self._persistence.get_dataset_manifest(dataset_id)
        if existing is not None:
            file_exists = await asyncio.to_thread(_file_exists, existing.parquet_path)
            if file_exists:
                logger.info(
                    "ticks_dataset_idempotent_republish",
                    dataset_id=dataset_id,
                    symbol=clean_symbol,
                )
                return existing

        timestamps = [
            t.timestamp.astimezone(UTC).replace(tzinfo=None) for t in sorted_ticks
        ]
        bids = [t.bid for t in sorted_ticks]
        asks = [t.ask for t in sorted_ticks]
        sequences = [t.sequence for t in sorted_ticks]
        bid_vols = [t.bid_volume for t in sorted_ticks]
        ask_vols = [t.ask_volume for t in sorted_ticks]
        flags = [t.flags for t in sorted_ticks]

        table = pa.Table.from_arrays(
            [
                pa.array(timestamps, type=pa.timestamp("us")),
                pa.array(bids, type=pa.float64()),
                pa.array(asks, type=pa.float64()),
                pa.array(sequences, type=pa.int64()),
                pa.array(bid_vols, type=pa.float64()),
                pa.array(ask_vols, type=pa.float64()),
                pa.array(flags, type=pa.int64()),
            ],
            schema=TICKS_SCHEMA,
        )

        out_path = self._config.storage_dir / clean_symbol / f"{dataset_id}.parquet"
        sha256_hash = await asyncio.to_thread(_atomic_write_parquet, table, out_path)

        manifest = DatasetManifest(
            dataset_id=dataset_id,
            symbol=clean_symbol,
            timeframe="tick",
            data_kind="ticks",
            source_id=source_id,
            start_time=start_time,
            end_time=end_time,
            row_count=len(sorted_ticks),
            parquet_path=str(out_path.resolve()),
            sha256_hash=sha256_hash,
            schema_version=1,
            quality_score=quality_score if quality_score is not None else 1.0,
            lineage=lineage or {},
            created_at=datetime.now(UTC),
        )

        await self._persistence.save_dataset_manifest(manifest)
        logger.info(
            "ticks_dataset_persisted",
            dataset_id=dataset_id,
            rows=len(sorted_ticks),
            symbol=clean_symbol,
        )
        return manifest

    @override
    async def load_ticks(
        self,
        dataset_id: str,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[TickRecord]:
        """Load normalized ticks from a published dataset version."""
        manifest = await self.get_manifest(dataset_id)
        if manifest is None:
            msg = f"Dataset {dataset_id} not found"
            raise DatasetNotFoundError(msg)

        parquet_file = Path(manifest.parquet_path)
        return await asyncio.to_thread(_read_parquet_ticks, parquet_file, start, end)


SPEC: FeatureSpec = FeatureSpec(
    name="data.datasets",
    provides=frozenset({DATA_DATASETS}),
    requires=frozenset({DATA_PERSISTENCE}),
    optional=frozenset(),
    description="Immutable normalized dataset versions and Parquet storage.",
)


class DatasetFeature:
    """Wire dataset feature into kernel composition lifecycle."""

    def __init__(self, config: DatasetConfig | None = None) -> None:
        """Initialize feature with optional configuration.

        Args:
            config: Optional dataset configuration.
        """
        self._config = config or DatasetConfig()

    @property
    def spec(self) -> FeatureSpec:
        """Return immutable feature specification."""
        return SPEC

    async def start(self, context: FeatureContext) -> None:
        """Resolve persistence and provide dataset service.

        Args:
            context: Lifecycle feature context.
        """
        persistence = context.require(DATA_PERSISTENCE)
        service = DatasetServiceImpl(persistence, self._config)
        context.provide(DATA_DATASETS, service)
        logger.info("data_datasets_feature_started")


def feature() -> DatasetFeature:
    """Return an unmounted DatasetFeature instance.

    Returns:
        New DatasetFeature instance.
    """
    return DatasetFeature()


__all__ = [
    "BARS_SCHEMA",
    "SPEC",
    "TICKS_SCHEMA",
    "DatasetConfig",
    "DatasetFeature",
    "DatasetServiceImpl",
    "feature",
]
