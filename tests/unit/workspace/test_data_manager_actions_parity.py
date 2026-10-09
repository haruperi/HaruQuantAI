"""Unit tests verifying 100% SQX parity for DataManagerActions.

Key Capabilities Verified:
    - FR-DATA-CATALOG-SQX-OPERATIONS: Clone guard, timezone shift, weekend pruning,
      storage patch, defect review, mass delete with clone guard, and XML interchange.
    - FR-DATA-QUALITY-EXPORT: Custom tokenized CSV formatting, binary MT4 HST/FXT,
      and MT5 advanced export with real spread calculation.
    - FR-DATA-QUALITY-METRICS: 24-hour error distribution and defect inspection.
    - FR-DATA-STORAGE-WRITER: Parquet partition patching and atomic mutation.
"""

from __future__ import annotations

import struct
from pathlib import Path

import pytest
from app.host.persistence import DatabaseManager
from app.host.resources import ResourceManager
from app.workspace.data_manager.actions.transform.transforms import (
    MT4_FXT_HEADER_LEN,
    MT4_FXT_VERSION,
    MT4_HST_VERSION,
    SeriesTransformer,
)
from app.workspace.data_manager.data import BarRecord, CatalogService
from app.workspace.data_manager.instruments import InstrumentService
from app.workspace.data_manager.routes import create_data_router
from app.workspace.data_manager.storage import MarketDataStorage
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def test_db(tmp_path: Path) -> DatabaseManager:
    """Fixture providing an isolated SQLite database."""
    db_file = tmp_path / "test_actions_parity.db"
    db = DatabaseManager(database_path=db_file)
    db.initialize()
    InstrumentService(db).ensure_defaults()
    return db


@pytest.fixture
def storage(tmp_path: Path) -> MarketDataStorage:
    """Fixture providing an isolated market data storage."""
    return MarketDataStorage(tmp_path / "market_data")


@pytest.fixture
def catalog(test_db: DatabaseManager, storage: MarketDataStorage) -> CatalogService:
    """Fixture providing CatalogService wired to isolated storage and database."""
    return CatalogService(db=test_db, storage=storage)


@pytest.fixture
def sample_bars() -> list[BarRecord]:
    """Fixture providing sequential M1 bars."""
    return [
        BarRecord(
            timestamp_utc="2025-01-03T10:00:00+00:00",  # Friday
            open=1.1000,
            high=1.1020,
            low=1.0990,
            close=1.1010,
            volume=100.0,
        ),
        BarRecord(
            timestamp_utc="2025-01-03T10:01:00+00:00",  # Friday
            open=1.1010,
            high=1.1030,
            low=1.1005,
            close=1.1025,
            volume=120.0,
        ),
        BarRecord(
            timestamp_utc="2025-01-04T10:00:00+00:00",  # Saturday
            open=1.1025,
            high=1.1035,
            low=1.1020,
            close=1.1030,
            volume=50.0,
        ),
        BarRecord(
            timestamp_utc="2025-01-05T10:00:00+00:00",  # Sunday
            open=1.1030,
            high=1.1040,
            low=1.1025,
            close=1.1035,
            volume=60.0,
        ),
        BarRecord(
            timestamp_utc="2025-01-06T10:00:00+00:00",  # Monday
            open=1.1035,
            high=1.1050,
            low=1.1030,
            close=1.1045,
            volume=200.0,
        ),
    ]


def test_clone_to_timezone_hour_shift_and_lineage(
    catalog: CatalogService,
    storage: MarketDataStorage,
    sample_bars: list[BarRecord],
) -> None:
    """Test clone_to_timezone applying fixed hour shift and setting source_data_id."""
    ds = catalog.save_bars(
        source="Dukascopy",
        symbol="EURUSD",
        timeframe="M1",
        bars=sample_bars,
    )

    cloned_id = catalog.clone_to_timezone(
        dataset_id=ds.id,
        timezone_type="hours",
        shift_hours=5,
        remove_weekends=False,
    )

    cloned = catalog.get_dataset(cloned_id)
    assert cloned is not None
    assert cloned.source_data_id == ds.id
    assert cloned.symbol == "EURUSD_M1_+5H"
    assert cloned.bars == 5

    cloned_bars = storage.read_bars_slice(
        source=cloned.source,
        symbol=cloned.symbol,
        timeframe=cloned.timeframe,
        limit=10,
    )
    assert len(cloned_bars) == 5
    # First bar was 10:00:00 UTC, shifted by +5 hours -> 15:00:00 UTC
    assert cloned_bars[0].timestamp_utc == "2025-01-03T15:00:00+00:00"


def test_clone_to_timezone_weekend_pruning(
    catalog: CatalogService,
    storage: MarketDataStorage,
    sample_bars: list[BarRecord],
) -> None:
    """Test clone_to_timezone removes Saturday and Sunday bars when remove_weekends=True."""
    ds = catalog.save_bars(
        source="Dukascopy",
        symbol="GBPUSD",
        timeframe="M1",
        bars=sample_bars,
    )

    cloned_id = catalog.clone_to_timezone(
        dataset_id=ds.id,
        timezone_type="hours",
        shift_hours=0,
        remove_weekends=True,
    )

    cloned = catalog.get_dataset(cloned_id)
    assert cloned is not None
    assert cloned.bars == 3  # Friday (2 bars) + Monday (1 bar)
    cloned_bars = storage.read_bars_slice(
        source=cloned.source,
        symbol=cloned.symbol,
        timeframe=cloned.timeframe,
        limit=10,
    )
    assert len(cloned_bars) == 3
    timestamps = [b.timestamp_utc for b in cloned_bars]
    assert "2025-01-04T10:00:00+00:00" not in timestamps
    assert "2025-01-05T10:00:00+00:00" not in timestamps


def test_clone_guard_cannot_clone_again(
    catalog: CatalogService,
    sample_bars: list[BarRecord],
) -> None:
    """Test clone guard prevents cloning an already-cloned dataset."""
    ds = catalog.save_bars(
        source="Dukascopy",
        symbol="USDJPY",
        timeframe="M1",
        bars=sample_bars,
    )

    cloned_id = catalog.clone_to_timezone(
        dataset_id=ds.id,
        shift_hours=2,
    )

    with pytest.raises(
        ValueError, match=r"is cloned data\. You cannot clone it again\."
    ):
        catalog.clone_to_timezone(dataset_id=cloned_id, shift_hours=3)


def test_get_review_rows_and_index_for_date(
    catalog: CatalogService,
    sample_bars: list[BarRecord],
) -> None:
    """Test get_review_rows and get_index_for_date methods."""
    ds = catalog.save_bars(
        source="Dukascopy",
        symbol="AUDUSD",
        timeframe="M1",
        bars=sample_bars,
    )

    # get_review_rows
    res = catalog.get_review_rows(dataset_id=ds.id, limit=2, offset=1)
    rows = res["rows"]
    assert len(rows) == 2
    assert rows[0]["open"] == sample_bars[1].open
    assert rows[0]["close"] == sample_bars[1].close

    # get_index_for_date
    idx = catalog.get_index_for_date(
        dataset_id=ds.id, target_date="2025-01-04T10:00:00+00:00"
    )
    assert idx == 2


def test_save_data_changes_storage_patch(
    catalog: CatalogService,
    storage: MarketDataStorage,
    sample_bars: list[BarRecord],
) -> None:
    """Test save_data_changes writes modified cells and removes deleted rows from storage."""
    ds = catalog.save_bars(
        source="Dukascopy",
        symbol="NZDUSD",
        timeframe="M1",
        bars=sample_bars,
    )

    # Modify bar 1, delete bar 3
    modified_bar = sample_bars[0].model_copy(update={"close": 1.1550})
    deleted_timestamp = sample_bars[2].timestamp_utc

    updated = catalog.save_data_changes(
        dataset_id=ds.id,
        changed_bars=[modified_bar],
        deleted_timestamps={deleted_timestamp},
    )

    assert updated.bars == 4

    remaining_bars = storage.read_bars_slice(
        source=updated.source,
        symbol=updated.symbol,
        timeframe=updated.timeframe,
        limit=10,
    )
    assert len(remaining_bars) == 4
    assert remaining_bars[0].close == 1.1550
    assert deleted_timestamp not in [b.timestamp_utc for b in remaining_bars]


def test_quality_summary_and_details(
    catalog: CatalogService,
    sample_bars: list[BarRecord],
) -> None:
    """Test check_quality_summary and check_quality_details inspection."""
    anomalous_bars = list(sample_bars)
    anomalous_bars.append(
        BarRecord(
            timestamp_utc="2025-01-06T15:00:00+00:00",
            open=1.1000,
            high=1.0900,  # Invalid OHLC: high < open
            low=1.0800,
            close=1.0950,
            volume=50.0,
        )
    )
    ds = catalog.save_bars(
        source="Dukascopy",
        symbol="USDCAD",
        timeframe="M1",
        bars=anomalous_bars,
    )

    summary = catalog.check_quality_summary(dataset_id=ds.id)
    assert "distribution" in summary
    assert len(summary["distribution"]) == 24
    assert summary["counts"]["ohlc"] >= 1

    details = catalog.check_quality_details(dataset_id=ds.id, limit=10)
    assert len(details) >= 1
    assert any("OHLC" in d.get("reason", "") for d in details)


def test_mass_delete_with_clone_dependency_guard(
    catalog: CatalogService,
    sample_bars: list[BarRecord],
) -> None:
    """Test mass_delete clone dependency guard prevents accidental parent deletion."""
    parent = catalog.save_bars(
        source="Dukascopy",
        symbol="EURCHF",
        timeframe="M1",
        bars=sample_bars,
    )

    cloned_id = catalog.clone_to_timezone(dataset_id=parent.id, shift_hours=1)
    cloned = catalog.get_dataset(cloned_id)
    assert cloned is not None
    assert cloned.source_data_id == parent.id

    # Attempting to delete parent without force should raise error
    with pytest.raises(ValueError, match="CLONE_DEPENDENCY"):
        catalog.mass_delete(dataset_ids=[parent.id], action="remove", force=False)

    # With force=True, deletion succeeds
    result = catalog.mass_delete(dataset_ids=[parent.id], action="remove", force=True)
    assert result["results"][parent.id] is True
    assert catalog.get_dataset(parent.id) is None


def test_mass_delete_clear_action(
    catalog: CatalogService,
    sample_bars: list[BarRecord],
) -> None:
    """Test mass_delete with action='clear' clears bars but preserves record."""
    ds = catalog.save_bars(
        source="Dukascopy",
        symbol="EURJPY",
        timeframe="M1",
        bars=sample_bars,
    )

    catalog.mass_delete(dataset_ids=[ds.id], action="clear")
    dataset = catalog.get_dataset(ds.id)
    assert dataset is not None
    assert dataset.bars == 0
    assert dataset.date_from == ""
    assert dataset.date_to == ""


def test_catalog_xml_export_and_import(
    catalog: CatalogService,
    sample_bars: list[BarRecord],
) -> None:
    """Test catalog XML export and import round-trip."""
    ds = catalog.save_bars(
        source="Dukascopy",
        symbol="XAUUSD",
        timeframe="M1",
        bars=sample_bars,
    )

    xml_text = catalog.export_catalog_xml([ds.id])
    assert "<Data>" in xml_text
    assert f'<DataInfo id="{ds.id}"' in xml_text
    assert 'symbol="XAUUSD"' in xml_text

    result = catalog.import_catalog_xml(xml_text)
    assert result["datasets_imported"] >= 1


def test_export_csv_custom_tokens(
    tmp_path: Path,
    sample_bars: list[BarRecord],
) -> None:
    """Test SeriesTransformer.export_csv_custom token rendering."""
    transformer = SeriesTransformer()
    out_file = tmp_path / "custom_export.csv"

    transformer.export_csv_custom(
        bars=sample_bars,
        output_path=out_file,
        symbol="EURUSD",
        items=[
            "[symbol]",
            "[date:yyyy-MM-dd]",
            "[time:HH:mm:ss]",
            "[open]",
            "[high]",
            "[low]",
            "[close]",
            "[volume]",
            "[spread]",
        ],
        delimiter=";",
        include_header=True,
    )

    assert out_file.exists()
    lines = out_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == len(sample_bars) + 1
    # Check first data line
    cols = lines[1].split(";")
    assert cols[0] == "EURUSD"
    assert cols[1] == "2025-01-03"
    assert cols[2] == "10:00:00"
    assert float(cols[3]) == 1.1000
    assert cols[8] == "0"


def test_export_mt4_binary_hst_and_fxt(
    tmp_path: Path,
    sample_bars: list[BarRecord],
) -> None:
    """Test SeriesTransformer MT4 binary HST and FXT generation."""
    transformer = SeriesTransformer()

    # HST export (v401)
    hst_file = tmp_path / "EURUSD1.hst"
    transformer.export_mt4_binary(
        bars=sample_bars,
        output_path=hst_file,
        symbol="EURUSD",
        period=1,
        digits=5,
    )
    assert hst_file.exists()
    hst_bytes = hst_file.read_bytes()
    version = struct.unpack_from("<i", hst_bytes, 0)[0]
    assert version == MT4_HST_VERSION
    # Header is 148 bytes, each record is 60 bytes
    assert len(hst_bytes) == 148 + len(sample_bars) * 60

    # FXT export (v405)
    fxt_file = tmp_path / "EURUSD1_0.fxt"
    transformer.export_mt4_fxt_binary(
        bars=sample_bars,
        output_path=fxt_file,
        symbol="EURUSD",
    )
    assert fxt_file.exists()
    fxt_bytes = fxt_file.read_bytes()
    fxt_ver = struct.unpack_from("<i", fxt_bytes, 0)[0]
    assert fxt_ver == MT4_FXT_VERSION
    assert len(fxt_bytes) == MT4_FXT_HEADER_LEN + len(sample_bars) * 56


def test_export_mt5_advanced_real_spread(
    tmp_path: Path,
    sample_bars: list[BarRecord],
) -> None:
    """Test SeriesTransformer MT5 advanced export with real spread."""
    transformer = SeriesTransformer()
    mt5_file = tmp_path / "EURUSD_M1_MT5.csv"

    transformer.export_mt5_advanced(
        bars=sample_bars,
        output_path=mt5_file,
        symbol="EURUSD",
        real_spread=True,
    )

    assert mt5_file.exists()
    lines = mt5_file.read_text(encoding="utf-8").strip().splitlines()
    assert lines[0] == (
        "<DATE>\t<TIME>\t<OPEN>\t<HIGH>\t<LOW>\t<CLOSE>\t<TICKVOL>\t<VOL>\t<SPREAD>"
    )
    cols = lines[1].split("\t")
    assert len(cols) == 9
    assert cols[0] == "2025.01.03"
    assert cols[1] == "10:00:00"
    # High: 1.1020, Low: 1.0990 -> diff: 0.0030 -> spread in points (10000) = 30
    assert cols[8] == "30"


def test_data_routes_integration(
    test_db: DatabaseManager,
    sample_bars: list[BarRecord],
    tmp_path: Path,
) -> None:
    """Test REST API routes for new DataManager actions."""
    res_mgr = ResourceManager(tmp_path / "resources")
    router = create_data_router(db_manager=test_db, resource_manager=res_mgr)
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    catalog = CatalogService(
        db=test_db,
        storage=MarketDataStorage(base_dir=tmp_path / "resources" / "datasets"),
    )
    ds = catalog.save_bars(
        source="Dukascopy",
        symbol="USDCHF",
        timeframe="M1",
        bars=sample_bars,
    )

    # Review data
    resp = client.get(f"/data/datasets/{ds.id}/review-data?limit=2&offset=0")
    assert resp.status_code == 200
    assert len(resp.json()["data"]["rows"]) == 2

    # Index for date
    resp = client.get(
        f"/data/datasets/{ds.id}/index-for-date?target_date=2025-01-03T10:01:00%2B00:00"
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["index"] == 1

    # Quality summary
    resp = client.get(f"/data/datasets/{ds.id}/quality-summary")
    assert resp.status_code == 200
    assert "errorDistribution" in resp.json()["data"]

    # Save CSV format profile
    profile = {
        "name": "CustomTestProfile",
        "header": "D;T;O;H;L;C;V",
        "items": ["[date:yyyyMMdd]", "[time:HHmmss]", "[open]", "[close]"],
        "delimiter": ";",
    }
    resp = client.post("/data/export/csv/formats", json=profile)
    assert resp.status_code == 200

    # List CSV format profiles
    resp = client.get("/data/export/csv/formats")
    assert resp.status_code == 200
    names = [p["name"] for p in resp.json()["data"]["formats"]]
    assert "CustomTestProfile" in names

    # Delete CSV format profile
    resp = client.post(
        "/data/export/csv/formats/delete", json={"name": "CustomTestProfile"}
    )
    assert resp.status_code == 200
