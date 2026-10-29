"""Tests for DataCatalog service, DatasetRef, and DataBatch contracts."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd  # type: ignore[import-untyped]
import polars as pl
import pyarrow.parquet as pq
import pytest
from app.core.data.catalog import DataBatch, DataCatalog, DatasetRef
from app.core.data.market_storage import encode_frame
from app.core.enums import Timeframe
from app.core.host.persistence import HostPersistence
from app.core.jobs.manager import JobCancelledError, JobContext
from app.core.lib.errors import DomainError


@pytest.fixture
def persistence_gateway(tmp_path: Path) -> HostPersistence:
    """Provide a fresh isolated SQLite persistence instance."""
    db_file = tmp_path / "test_catalog.db"
    conn = sqlite3.connect(db_file)
    conn.close()
    gateway = HostPersistence(db_file)
    gateway.ensure_datasets_schema()
    return gateway


def test_dataset_ref_properties_and_validation() -> None:
    """Verify DatasetRef normalization, safe component validation, and id formatting."""
    ref = DatasetRef(symbol="EURUSD", timeframe=Timeframe.PERIOD_M1, source="dukascopy")
    assert ref.symbol == "EURUSD"
    assert ref.timeframe == "M1"
    assert ref.source == "dukascopy"
    assert ref.dataset_id == "dukascopy:EURUSD:M1"

    # Default source and lowercase timeframe normalization
    ref_default = DatasetRef(symbol="GBPUSD", timeframe="m5")
    assert ref_default.source == "default"
    assert ref_default.timeframe == "M5"
    assert ref_default.dataset_id == "default:GBPUSD:M5"

    # Path traversal rejected by safe_component
    with pytest.raises(ValueError, match="Use a safe alphanumeric source or symbol"):
        DatasetRef(symbol="../EURUSD")


def test_data_batch_empty_and_conversions() -> None:
    """Verify DataBatch empty predicate and pandas/arrow conversions."""
    ref = DatasetRef(symbol="EURUSD", timeframe="M1")
    empty_df = pl.DataFrame(
        schema={
            "DateTime": pl.Datetime("us", "UTC"),
            "Open": pl.Float64,
            "High": pl.Float64,
            "Low": pl.Float64,
            "Close": pl.Float64,
            "Volume": pl.UInt64,
        }
    )
    batch = DataBatch(
        ref=ref,
        frame=empty_df,
        start=None,
        end=None,
        row_count=0,
        tick_size=0.0001,
    )
    assert batch.is_empty is True
    assert batch.to_pandas().empty
    assert len(batch.to_arrow()) == 0


def test_catalog_two_partitions_and_bounds(
    persistence_gateway: HostPersistence, tmp_path: Path
) -> None:
    """Concrete Fixture 1: Two sequential partitions query with bounds and count."""
    tick_size = 0.0001
    p1 = tmp_path / "part_20260101.parquet"
    p2 = tmp_path / "part_20260102.parquet"

    df1 = pd.DataFrame(
        {
            "DateTime": [
                datetime(2026, 1, 1, 0, 0, tzinfo=UTC),
                datetime(2026, 1, 1, 0, 1, tzinfo=UTC),
                datetime(2026, 1, 1, 0, 2, tzinfo=UTC),
            ],
            "Open": [1.1000, 1.1010, 1.1025],
            "High": [1.1020, 1.1030, 1.1040],
            "Low": [1.0990, 1.1005, 1.1020],
            "Close": [1.1010, 1.1025, 1.1035],
            "Volume": [100, 150, 200],
        }
    )
    df2 = pd.DataFrame(
        {
            "DateTime": [
                datetime(2026, 1, 2, 0, 0, tzinfo=UTC),
                datetime(2026, 1, 2, 0, 1, tzinfo=UTC),
            ],
            "Open": [1.1050, 1.1060],
            "High": [1.1070, 1.1080],
            "Low": [1.1045, 1.1055],
            "Close": [1.1060, 1.1075],
            "Volume": [120, 180],
        }
    )
    pq.write_table(encode_frame(df1, "M1", tick_size), p1)
    pq.write_table(encode_frame(df2, "M1", tick_size), p2)

    # Register in datamgr_datasets
    record = {
        "id": "test_src:EURUSD:M1",
        "source": "test_src",
        "symbol": "EURUSD",
        "underlying": "EURUSD",
        "timeframe": "M1",
        "broker": "Default",
        "timezone": "UTC",
        "category": "Forex",
        "date_from": "2026-01-01T00:00:00+00:00",
        "date_to": "2026-01-02T00:01:00+00:00",
        "bars": 5,
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-02T12:00:00+00:00",
        "path": str(tmp_path),
        "data_kind": "bars",
        "quality_score": 1.0,
        "lineage_json": json.dumps(
            {
                "partitions": [str(p1), str(p2)],
                "tick_size": tick_size,
                "storage": "canonical-partitions-v1",
            }
        ),
        "schema_version": 1,
    }
    persistence_gateway.create_records(
        "datamgr_datasets",
        record,  # type: ignore[arg-type]
    )

    catalog = DataCatalog(persistence_gateway)
    ref = DatasetRef(source="test_src", symbol="EURUSD", timeframe="M1")

    # Metadata check
    info = catalog.get_dataset_info(ref)
    assert info is not None
    assert info.symbol == "EURUSD"
    assert info.bars == 5

    # Full query -> 5 rows
    batch = catalog.read(ref)
    assert batch.row_count == 5
    assert not batch.is_empty
    assert batch.frame["Close"].to_list() == [1.1010, 1.1025, 1.1035, 1.1060, 1.1075]

    # Bounded query across partition boundary -> 3 rows
    bounded = catalog.read(
        ref,
        start=datetime(2026, 1, 1, 0, 1, tzinfo=UTC),
        end=datetime(2026, 1, 2, 0, 0, tzinfo=UTC),
    )
    assert bounded.row_count == 3
    assert bounded.frame["DateTime"].to_list() == [
        datetime(2026, 1, 1, 0, 1, tzinfo=UTC),
        datetime(2026, 1, 1, 0, 2, tzinfo=UTC),
        datetime(2026, 1, 2, 0, 0, tzinfo=UTC),
    ]

    # Tail count query -> 2 rows
    tailed = catalog.read(ref, count=2)
    assert tailed.row_count == 2
    assert tailed.frame["Close"].to_list() == [1.1060, 1.1075]


def test_catalog_gap_empty_range_returns_empty_batch(
    persistence_gateway: HostPersistence, tmp_path: Path
) -> None:
    """Concrete Fixture 2: Querying a gap or range with no data returns empty DataBatch."""
    tick_size = 0.0001
    p1 = tmp_path / "part_20260101.parquet"
    df1 = pd.DataFrame(
        {
            "DateTime": [datetime(2026, 1, 1, 0, 0, tzinfo=UTC)],
            "Open": [1.1000],
            "High": [1.1020],
            "Low": [1.0990],
            "Close": [1.1010],
            "Volume": [100],
        }
    )
    pq.write_table(encode_frame(df1, "M1", tick_size), p1)

    record = {
        "id": "gap_src:EURUSD:M1",
        "source": "gap_src",
        "symbol": "EURUSD",
        "underlying": "EURUSD",
        "timeframe": "M1",
        "broker": "Default",
        "timezone": "UTC",
        "category": "Forex",
        "date_from": "2026-01-01T00:00:00+00:00",
        "date_to": "2026-01-01T00:00:00+00:00",
        "bars": 1,
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-01T00:00:00+00:00",
        "path": str(tmp_path),
        "data_kind": "bars",
        "quality_score": 1.0,
        "lineage_json": json.dumps(
            {
                "partitions": [str(p1)],
                "tick_size": tick_size,
                "storage": "canonical-partitions-v1",
            }
        ),
        "schema_version": 1,
    }
    persistence_gateway.create_records(
        "datamgr_datasets",
        record,  # type: ignore[arg-type]
    )

    catalog = DataCatalog(persistence_gateway)
    ref = DatasetRef(source="gap_src", symbol="EURUSD", timeframe="M1")

    # Query range far in the future
    batch = catalog.read(
        ref,
        start=datetime(2026, 5, 1, 0, 0, tzinfo=UTC),
        end=datetime(2026, 5, 2, 0, 0, tzinfo=UTC),
    )
    assert batch.row_count == 0
    assert batch.is_empty is True


def test_catalog_stale_revision_raises_error(
    persistence_gateway: HostPersistence,
) -> None:
    """Concrete Fixture 3: Querying with a stale revision raises STALE_CATALOG_REVISION."""
    record = {
        "id": "stale_src:EURUSD:M1",
        "source": "stale_src",
        "symbol": "EURUSD",
        "underlying": "EURUSD",
        "timeframe": "M1",
        "broker": "Default",
        "timezone": "UTC",
        "category": "Forex",
        "date_from": "2026-01-01T00:00:00+00:00",
        "date_to": "2026-01-01T00:00:00+00:00",
        "bars": 0,
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-02T00:00:00+00:00",
        "path": "",
        "data_kind": "bars",
        "quality_score": 1.0,
        "lineage_json": "{}",
        "schema_version": 2,
    }
    persistence_gateway.create_records(
        "datamgr_datasets",
        record,  # type: ignore[arg-type]
    )

    catalog = DataCatalog(persistence_gateway)
    stale_ref = DatasetRef(
        source="stale_src",
        symbol="EURUSD",
        timeframe="M1",
        revision="2020-01-01T00:00:00+00:00",
    )

    with pytest.raises(DomainError) as exc_info:
        catalog.read(stale_ref)
    assert exc_info.value.code == "STALE_CATALOG_REVISION"


def test_catalog_missing_partition_raises_corrupt_storage(
    persistence_gateway: HostPersistence, tmp_path: Path
) -> None:
    """Concrete Fixture 4: Manifest partition deleted on disk raises CORRUPT_DATASET_STORAGE."""
    deleted_path = tmp_path / "deleted.parquet"
    record = {
        "id": "miss_src:EURUSD:M1",
        "source": "miss_src",
        "symbol": "EURUSD",
        "underlying": "EURUSD",
        "timeframe": "M1",
        "broker": "Default",
        "timezone": "UTC",
        "category": "Forex",
        "date_from": "2026-01-01T00:00:00+00:00",
        "date_to": "2026-01-01T00:00:00+00:00",
        "bars": 10,
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-01T00:00:00+00:00",
        "path": str(tmp_path),
        "data_kind": "bars",
        "quality_score": 1.0,
        "lineage_json": json.dumps(
            {
                "partitions": [str(deleted_path)],
                "tick_size": 0.0001,
            }
        ),
        "schema_version": 1,
    }
    persistence_gateway.create_records(
        "datamgr_datasets",
        record,  # type: ignore[arg-type]
    )

    catalog = DataCatalog(persistence_gateway)
    ref = DatasetRef(source="miss_src", symbol="EURUSD", timeframe="M1")

    with pytest.raises(DomainError) as exc_info:
        catalog.read(ref)
    assert exc_info.value.code == "CORRUPT_DATASET_STORAGE"


def test_catalog_dynamic_resampling_from_base_m1(
    persistence_gateway: HostPersistence, tmp_path: Path
) -> None:
    """Concrete Fixture 5: Requesting higher timeframe M5 resamples base M1 dataset."""
    tick_size = 0.0001
    p1 = tmp_path / "m1_data.parquet"
    df1 = pd.DataFrame(
        {
            "DateTime": [
                datetime(2026, 1, 1, 0, 0, tzinfo=UTC),
                datetime(2026, 1, 1, 0, 1, tzinfo=UTC),
                datetime(2026, 1, 1, 0, 2, tzinfo=UTC),
                datetime(2026, 1, 1, 0, 3, tzinfo=UTC),
                datetime(2026, 1, 1, 0, 4, tzinfo=UTC),
            ],
            "Open": [1.1000, 1.1010, 1.1025, 1.1030, 1.1040],
            "High": [1.1020, 1.1030, 1.1040, 1.1050, 1.1060],
            "Low": [1.0990, 1.1005, 1.1020, 1.1025, 1.1035],
            "Close": [1.1010, 1.1025, 1.1035, 1.1045, 1.1055],
            "Volume": [100, 150, 200, 120, 180],
        }
    )
    pq.write_table(encode_frame(df1, "M1", tick_size), p1)

    # Register only M1 in catalog
    record = {
        "id": "resamp_src:EURUSD:M1",
        "source": "resamp_src",
        "symbol": "EURUSD",
        "underlying": "EURUSD",
        "timeframe": "M1",
        "broker": "Default",
        "timezone": "UTC",
        "category": "Forex",
        "date_from": "2026-01-01T00:00:00+00:00",
        "date_to": "2026-01-01T00:04:00+00:00",
        "bars": 5,
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-01T00:00:00+00:00",
        "path": str(tmp_path),
        "data_kind": "bars",
        "quality_score": 1.0,
        "lineage_json": json.dumps(
            {
                "partitions": [str(p1)],
                "tick_size": tick_size,
                "storage": "canonical-partitions-v1",
            }
        ),
        "schema_version": 1,
    }
    persistence_gateway.create_records(
        "datamgr_datasets",
        record,  # type: ignore[arg-type]
    )

    catalog = DataCatalog(persistence_gateway)
    # Query M5
    ref_m5 = DatasetRef(source="resamp_src", symbol="EURUSD", timeframe="M5")
    batch = catalog.read(ref_m5)
    assert batch.row_count == 1
    bar = batch.frame.to_dicts()[0]
    assert bar["DateTime"] == datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
    assert bar["Open"] == 1.1000
    assert bar["High"] == 1.1060
    assert bar["Low"] == 1.0990
    assert bar["Close"] == 1.1055
    assert bar["Volume"] == 750


def test_catalog_dataset_not_found(persistence_gateway: HostPersistence) -> None:
    """Assert query for nonexistent dataset raises DATASET_NOT_FOUND."""
    catalog = DataCatalog(persistence_gateway)
    ref = DatasetRef(source="unknown_src", symbol="UNKNOWN", timeframe="M1")
    with pytest.raises(DomainError) as exc_info:
        catalog.read(ref)
    assert exc_info.value.code == "DATASET_NOT_FOUND"


def test_catalog_invalid_time_range(
    persistence_gateway: HostPersistence,
) -> None:
    """Assert start after end raises INVALID_TIME_RANGE."""
    catalog = DataCatalog(persistence_gateway)
    ref = DatasetRef(source="any", symbol="EURUSD", timeframe="M1")
    with pytest.raises(DomainError) as exc_info:
        catalog.read(
            ref,
            start=datetime(2026, 1, 2, tzinfo=UTC),
            end=datetime(2026, 1, 1, tzinfo=UTC),
        )
    assert exc_info.value.code == "INVALID_TIME_RANGE"


def test_catalog_cooperative_cancellation(
    persistence_gateway: HostPersistence, tmp_path: Path
) -> None:
    """Verify cooperative cancellation via JobContext."""
    record = {
        "id": "cancel_src:EURUSD:M1",
        "source": "cancel_src",
        "symbol": "EURUSD",
        "underlying": "EURUSD",
        "timeframe": "M1",
        "broker": "Default",
        "timezone": "UTC",
        "category": "Forex",
        "date_from": "2026-01-01T00:00:00+00:00",
        "date_to": "2026-01-01T00:00:00+00:00",
        "bars": 0,
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-01T00:00:00+00:00",
        "path": "",
        "data_kind": "bars",
        "quality_score": 1.0,
        "lineage_json": "{}",
        "schema_version": 1,
    }
    persistence_gateway.create_records(
        "datamgr_datasets",
        record,  # type: ignore[arg-type]
    )
    catalog = DataCatalog(persistence_gateway)
    ref = DatasetRef(source="cancel_src", symbol="EURUSD", timeframe="M1")

    ctx = JobContext(job_id="test_cancel", scratch_dir=tmp_path)
    ctx.cancel()
    with pytest.raises(JobCancelledError):
        catalog.read(ref, context=ctx)
