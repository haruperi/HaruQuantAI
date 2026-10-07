"""Unit tests for DataIngestionService and immutable dataset revisions.

Description:
    Tests streaming market data ingestion, delimiter sniffing, header detection,
    bar geometry validation, chronological deduplication, SHA-256 fingerprinting,
    and immutable revision registration into the catalog (Phase 2 Task 2.3).

Purpose:
    FEAT-DATA-INGESTION: Ingest, validate, and version market data series.

Key Capabilities:
    FR-DATA-INGESTION-STREAMING: Delimiter sniffing and chunked stream parsing.
    FR-DATA-INGESTION-NORMALIZATION: Bar geometry validation and sorting.
    FR-DATA-INGESTION-STAGING: Staging in isolated filesystem structure.
    FR-DATA-INGESTION-REVISIONS: Cryptographic fingerprinting and catalog registry.

Python API Usage:
    Run via pytest:
    `pytest tests/unit/v2/phase_02/test_ingestion.py -v --no-cov`
"""

from __future__ import annotations

import logging
from pathlib import Path

import pytest
from app.host.persistence import DatabaseManager
from app.workspace.data_manager.data import (
    BarRecord,
    CatalogService,
    DataIngestionService,
    IngestionConfig,
)

SAMPLE_CSV_CONTENT = """Date,Time,Open,High,Low,Close,Volume
2026.01.05,09:30:00,1.1000,1.1050,1.0980,1.1020,150
2026.01.05,09:31:00,1.1020,1.1060,1.1010,1.1040,220
2026.01.05,09:32:00,1.1040,1.1045,1.1015,1.1025,180
2026.01.05,09:33:00,1.1025,1.1070,1.1020,1.1065,310
"""

SAMPLE_TSV_CONTENT = """datetime\topen\thigh\tlow\tclose\tvolume
2026-01-05T09:30:00Z\t1.1000\t1.1050\t1.0980\t1.1020\t150
2026-01-05T09:31:00Z\t1.1020\t1.1060\t1.1010\t1.1040\t220
"""

SAMPLE_SEMICOLON_UNSORTED = """2026-01-05 10:00:00;100.0;105.0;98.0;102.0;500
2026-01-05 09:00:00;99.0;101.0;98.5;100.0;450
2026-01-05 09:30:00;100.0;103.0;99.5;101.5;600
2026-01-05 09:30:00;100.0;103.5;99.5;101.5;650
"""


@pytest.fixture
def test_setup(tmp_path: Path) -> tuple[CatalogService, DataIngestionService, Path]:
    """Create isolated catalog, database, and ingestion service instances."""
    db = DatabaseManager(database_path=tmp_path / "catalog.db")
    db.initialize()
    catalog = CatalogService(db)
    storage_dir = tmp_path / "datasets"
    service = DataIngestionService(catalog=catalog, storage_dir=storage_dir)
    return catalog, service, storage_dir


def test_detect_format(
    test_setup: tuple[CatalogService, DataIngestionService, Path],
) -> None:
    """Validate delimiter sniffing and header presence detection."""
    _, service, _ = test_setup

    delim, has_hdr = service.detect_format(SAMPLE_CSV_CONTENT)
    assert delim == ","
    assert has_hdr is True

    delim_tsv, has_hdr_tsv = service.detect_format(SAMPLE_TSV_CONTENT)
    assert delim_tsv == "\t"
    assert has_hdr_tsv is True

    delim_semi, has_hdr_semi = service.detect_format(SAMPLE_SEMICOLON_UNSORTED)
    assert delim_semi == ";"
    assert has_hdr_semi is False


def test_bar_geometry_validation() -> None:
    """Validate OHLC envelope consistency checks."""
    # Valid bar
    b_valid = BarRecord(
        timestamp_utc="2026-01-05T10:00:00Z",
        open=1.1000,
        high=1.1050,
        low=1.0950,
        close=1.1020,
        volume=100.0,
    )
    assert b_valid.is_valid_geometry() is True

    # Invalid: high < open
    b_bad_high = BarRecord(
        timestamp_utc="2026-01-05T10:00:00Z",
        open=1.1000,
        high=1.0900,
        low=1.0850,
        close=1.0880,
    )
    assert b_bad_high.is_valid_geometry() is False

    # Invalid: low > close
    b_bad_low = BarRecord(
        timestamp_utc="2026-01-05T10:00:00Z",
        open=1.1000,
        high=1.1050,
        low=1.1030,
        close=1.1010,
    )
    assert b_bad_low.is_valid_geometry() is False


def test_ingest_file_lifecycle(
    test_setup: tuple[CatalogService, DataIngestionService, Path],
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Validate full file ingestion, staging, fingerprinting, and catalog registration."""
    caplog.set_level(logging.DEBUG)
    catalog, service, storage_dir = test_setup

    data_file = tmp_path / "EURUSD_M1.csv"
    data_file.write_text(SAMPLE_CSV_CONTENT, encoding="utf-8")

    result = service.ingest_file(
        file_path=data_file,
        symbol="EURUSD",
        timeframe="M1",
        source="Dukascopy",
        config=IngestionConfig(timezone="UTC"),
    )

    assert result.symbol == "EURUSD"
    assert result.timeframe == "M1"
    assert result.bar_count == 4
    assert len(result.sha256_hash) == 64
    assert Path(result.output_path).exists()

    # FR log verification
    assert any("FR-DATA-INGESTION-STREAMING" in rec.message for rec in caplog.records)
    assert any("FR-DATA-INGESTION-STAGING" in rec.message for rec in caplog.records)
    assert any("FR-DATA-INGESTION-REVISIONS" in rec.message for rec in caplog.records)

    # Verify registered in Catalog
    ds = catalog.get_dataset(result.dataset_id)
    assert ds is not None
    assert ds.symbol == "EURUSD"
    assert ds.timeframe == "M1"
    assert ds.bars == 4
    assert ds.source == "Dukascopy"

    # Verify availability check
    avail, reason = catalog.check_availability("EURUSD", "M1")
    assert avail is True
    assert reason == "AVAILABLE"


def test_ingest_sorting_and_deduplication(
    test_setup: tuple[CatalogService, DataIngestionService, Path],
    tmp_path: Path,
) -> None:
    """Validate chronological sorting and duplicate timestamp resolution."""
    _, service, _ = test_setup

    data_file = tmp_path / "SPY.csv"
    data_file.write_text(SAMPLE_SEMICOLON_UNSORTED, encoding="utf-8")

    result = service.ingest_file(
        file_path=data_file,
        symbol="SPY",
        timeframe="M5",
        config=IngestionConfig(timezone="UTC", delimiter=";", has_header=False),
    )

    # 4 rows input, 2 duplicate timestamps at 09:30:00 -> 3 unique bars
    assert result.bar_count == 3
    # Earliest bar should be 09:00:00 and latest 10:00:00
    assert "09:00:00" in result.date_from
    assert "10:00:00" in result.date_to


def test_ingest_missing_file_error(
    test_setup: tuple[CatalogService, DataIngestionService, Path],
    tmp_path: Path,
) -> None:
    """Validate FileNotFoundError on missing file."""
    _, service, _ = test_setup
    with pytest.raises(FileNotFoundError):
        service.ingest_file(tmp_path / "nonexistent.csv", symbol="AAPL")
