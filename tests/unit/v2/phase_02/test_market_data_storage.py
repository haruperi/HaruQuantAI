"""
Description:
    Unit tests for MarketDataStorage and StrategyQuant X DataManagerData domain
    operations. Validates integer tick unit pricing, PyArrow ZSTD-6 partitioned
    parquet writing, Polars lazy scans, DuckDB queries, bi5/gz decompression,
    and complete dataset lifecycle (create, read, edit, clear, remove).

Purpose:
    FEAT-DATA-STORAGE: Canonical historical market data partitioned Parquet engine.

Key Capabilities:
    FR-DATA-STORAGE-SCHEMAS: Validates Arrow schemas with integer tick units.
    FR-DATA-STORAGE-PARTITIONING: Validates tick and bar partition hierarchy paths.
    FR-DATA-STORAGE-WRITER: Validates PyArrow ZSTD-6 partitioned writes and dedup.
    FR-DATA-STORAGE-POLARS-SCAN: Validates Polars lazy scan execution and filtering.
    FR-DATA-STORAGE-DUCKDB-SQL: Validates DuckDB direct SQL queries over parquet.
    FR-DATA-STORAGE-DECOMPRESSION: Validates payload decompression (bi5, gz, zip).
    FR-DATA-CATALOG-SQX-OPERATIONS: Validates SQX DataManagerData operations.

Python API Usage:
    Run via pytest:
    `pytest tests/unit/v2/phase_02/test_market_data_storage.py -v --no-cov`
"""

from __future__ import annotations

import gzip
import logging
import lzma
import zipfile
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path

import pyarrow.parquet as pq
import pytest
from app.host.persistence import DatabaseManager
from app.workspace.data_manager.data import CatalogService
from app.workspace.data_manager.instruments import (
    InstrumentDefinition,
    InstrumentService,
)
from app.workspace.data_manager.storage import (
    BarRecord,
    MarketDataStorage,
    TickRecord,
    decompress_payload,
    from_tick_units,
    get_bar_partition_path,
    get_tick_partition_path,
    to_tick_units,
)


@pytest.fixture
def storage_setup(
    tmp_path: Path,
) -> tuple[DatabaseManager, CatalogService, MarketDataStorage, Path]:
    """Create isolated test database, catalog service, and storage engine."""
    db_file = tmp_path / "test_storage.db"
    db = DatabaseManager(database_path=db_file)
    db.initialize()

    # Seed baseline instruments
    instr_svc = InstrumentService(db)
    instr_svc.save_instrument(
        InstrumentDefinition(
            symbol="EURUSD",
            data_type="Forex",
            point_value=100000.0,
            tick_size=0.00001,
            decimals=5,
        )
    )
    instr_svc.save_instrument(
        InstrumentDefinition(
            symbol="ES",
            data_type="Futures",
            point_value=50.0,
            tick_size=0.25,
            decimals=2,
        )
    )

    market_dir = tmp_path / "market"
    storage = MarketDataStorage(base_dir=market_dir)
    catalog = CatalogService(db=db, storage=storage)
    return db, catalog, storage, market_dir


def test_integer_tick_units_conversion() -> None:
    """Validate price to integer tick units conversion and reversible decoding."""
    # 5 decimal forex
    tick_size_5 = 0.00001
    price_eurusd = 1.10254
    units = to_tick_units(price_eurusd, tick_size_5)
    assert units == 110254
    assert from_tick_units(units, tick_size_5) == 1.10254

    # 2 decimal futures (0.25 tick)
    tick_size_es = 0.25
    price_es = 5025.75
    units_es = to_tick_units(price_es, tick_size_es)
    assert units_es == 20103
    assert from_tick_units(units_es, tick_size_es) == 5025.75


def test_partition_paths(
    storage_setup: tuple[DatabaseManager, CatalogService, MarketDataStorage, Path],
) -> None:
    """Validate deterministic partition paths for ticks and M1 bars."""
    _, _, storage, base_dir = storage_setup

    dt = datetime(2025, 4, 15, 10, 30, tzinfo=UTC)

    # Tick partition: source / ticks / symbol / year / month
    tick_path = get_tick_partition_path(storage.base_dir, "dukascopy", "EURUSD", dt)
    expected_tick = (
        base_dir / "dukascopy" / "ticks" / "eurusd" / "2025" / "04-apr.parquet"
    )
    assert tick_path == expected_tick

    # Bar partition: source / timeframe / symbol / year
    bar_path = get_bar_partition_path(
        storage.base_dir, "dukascopy", "M1", "EURUSD", 2025
    )
    expected_bar = base_dir / "dukascopy" / "m1" / "eurusd" / "2025.parquet"
    assert bar_path == expected_bar


def test_write_and_read_bars(
    storage_setup: tuple[DatabaseManager, CatalogService, MarketDataStorage, Path],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Validate writing M1 bars with ZSTD-6, reading via Polars and DuckDB."""
    caplog.set_level(logging.DEBUG)
    _, _, storage, _ = storage_setup

    bars = [
        BarRecord(
            timestamp_utc="2025-04-15T09:30:00Z",
            open=1.10000,
            high=1.10500,
            low=1.09800,
            close=1.10200,
            volume=150.0,
        ),
        BarRecord(
            timestamp_utc="2025-04-15T09:31:00Z",
            open=1.10200,
            high=1.10600,
            low=1.10100,
            close=1.10400,
            volume=220.0,
        ),
        BarRecord(
            timestamp_utc="2025-04-15T09:32:00Z",
            open=1.10400,
            high=1.10450,
            low=1.10150,
            close=1.10250,
            volume=180.0,
        ),
    ]

    result = storage.write_bars(
        source="dukascopy",
        symbol="EURUSD",
        timeframe="M1",
        bars=bars,
        tick_size=0.00001,
    )

    assert result.total_bars == 3
    assert len(result.partition_files) == 1
    assert "2025.parquet" in result.partition_files[0]

    # Verify Parquet metadata and compression
    parquet_file = Path(result.partition_files[0])
    assert parquet_file.exists()
    meta = pq.read_metadata(parquet_file)
    assert meta.num_rows == 3
    assert meta.row_group(0).column(0).compression == "ZSTD"

    # Polars scan
    lf = storage.scan_bars("dukascopy", "EURUSD", "M1")
    df = lf.collect()
    assert len(df) == 3
    assert df["Open"][0] == 110000
    assert df["Close"][2] == 110250

    # DuckDB direct SQL query
    posix_path = parquet_file.as_posix()
    rel = storage.query_duckdb(f"SELECT SUM(Volume) AS total_vol FROM '{posix_path}'")
    row = rel.fetchone()
    assert row is not None
    assert row[0] == 550

    # Slice reader
    slice_bars = storage.read_bars_slice("dukascopy", "EURUSD", "M1", limit=2)
    assert len(slice_bars) == 2
    assert slice_bars[0].open == 1.10000
    assert slice_bars[1].high == 1.10600


def test_write_and_read_ticks(
    storage_setup: tuple[DatabaseManager, CatalogService, MarketDataStorage, Path],
) -> None:
    """Validate writing ticks with ZSTD-6 into year/month partition."""
    _, _, storage, _ = storage_setup

    ticks = [
        TickRecord(
            timestamp_utc="2025-04-15T10:00:00.123456Z",
            bid=1.10200,
            ask=1.10210,
            flags=1,
        ),
        TickRecord(
            timestamp_utc="2025-04-15T10:00:01.654321Z",
            bid=1.10205,
            ask=1.10215,
            flags=2,
        ),
    ]

    result = storage.write_ticks(
        source="dukascopy",
        symbol="EURUSD",
        ticks=ticks,
        tick_size=0.00001,
    )

    assert result.total_bars == 2
    assert len(result.partition_files) == 1
    assert "04-apr.parquet" in result.partition_files[0]

    # Verify Parquet schema
    table = pq.read_table(result.partition_files[0])
    assert table.schema.names == ["DateTime", "Bid", "Ask", "Flags"]

    # Read slice
    slice_ticks = storage.read_ticks_slice("dukascopy", "EURUSD")
    assert len(slice_ticks) == 2
    assert slice_ticks[0].bid == 1.10200
    assert slice_ticks[0].ask == 1.10210


def test_payload_decompression() -> None:
    """Validate decompress_payload for bi5, gzip, zip, and raw formats."""
    sample_text = b"DateTime,Open,High,Low,Close,Volume\n"

    # Gzip
    gz_bytes = gzip.compress(sample_text)
    assert decompress_payload(gz_bytes) == sample_text

    # Zip
    zip_buf = BytesIO()
    with zipfile.ZipFile(zip_buf, "w") as zf:
        zf.writestr("data.csv", sample_text)
    assert decompress_payload(zip_buf.getvalue()) == sample_text

    # Dukascopy bi5 (synthetic alone header)
    lzma_alone = lzma.compress(sample_text, format=lzma.FORMAT_ALONE)
    assert decompress_payload(lzma_alone) == sample_text

    # Raw bytes uncompressed
    assert decompress_payload(sample_text) == sample_text


def test_sqx_catalog_operations(
    storage_setup: tuple[DatabaseManager, CatalogService, MarketDataStorage, Path],
) -> None:
    """Validate StrategyQuant X DataManagerData domain operations."""
    _, catalog, _, _ = storage_setup

    bars = [
        BarRecord(
            timestamp_utc="2025-04-15T09:30:00Z",
            open=1.10000,
            high=1.10500,
            low=1.09800,
            close=1.10200,
            volume=150.0,
        ),
        BarRecord(
            timestamp_utc="2025-04-15T09:31:00Z",
            open=1.10200,
            high=1.10600,
            low=1.10100,
            close=1.10400,
            volume=220.0,
        ),
    ]

    # 1. Add / Create (save_bars)
    ds = catalog.save_bars("dukascopy", "EURUSD", "M1", bars)
    assert ds.id == "ds_dukascopy_eurusd_m1"
    assert ds.bars == 2
    assert ds.symbol == "EURUSD"

    # 2. Read / View (review_chart)
    chart_bars = catalog.review_chart(ds.id)
    assert len(chart_bars) == 2
    assert chart_bars[0]["open"] == 1.10000

    # 3. Read / View (get_index_for_date)
    idx = catalog.get_index_for_date(ds.id, "2025-04-15T09:30:30Z")
    assert idx == 0

    # 4. Read / View (check_quality_summary)
    quality = catalog.check_quality_summary(ds.id)
    assert quality["status"] == "VALID"
    assert quality["bars"] == 2

    # 5. Update / Edit (edit_dataset)
    success = catalog.edit_dataset(ds.id, symbol_new="EURUSD_NEW", category="Custom")
    assert success is True
    updated_ds = catalog.get_dataset(ds.id)
    assert updated_ds is not None
    assert updated_ds.symbol == "EURUSD_NEW"
    assert updated_ds.category == "Custom"

    # 6. Clear Data (deletes parquet files, keeps record in DB)
    clear_ok = catalog.clear_data(ds.id)
    assert clear_ok is True
    cleared_ds = catalog.get_dataset(ds.id)
    assert cleared_ds is not None
    assert cleared_ds.bars == 0

    # 7. Remove Data (deletes parquet and deletes DB row)
    remove_ok = catalog.remove_data(ds.id)
    assert remove_ok is True
    assert catalog.get_dataset(ds.id) is None
