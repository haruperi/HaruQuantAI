"""Unit tests for BasketService, multi-symbol alignment, and CustomDataService.

Description:
    Validates stock group persistence, basket weighting schemes, multi-symbol series
    alignment (intersection vs union), synthetic aggregate bar calculations, and
    secondary custom series synchronization (Phase 2 Task 2.6).

Purpose:
    FEAT-DATA-BASKETS: Manage stock groups, baskets, and custom data series.

Key Capabilities:
    FR-DATA-BASKETS-GROUPS: Stock group and basket persistence.
    FR-DATA-BASKETS-ALIGNMENT: Multi-symbol timestamp alignment and synthetic bars.
    FR-DATA-CUSTOM-SERIES: Ingestion and synchronization of custom indicator series.

Python API Usage:
    Run via pytest:
    `pytest tests/unit/v2/phase_02/test_custom_data.py -v --no-cov`
"""

from __future__ import annotations

import logging
from pathlib import Path

import pytest
from app.host.persistence import DatabaseManager
from app.workspace.data_manager.baskets import (
    BasketDefinition,
    BasketItem,
    BasketService,
)
from app.workspace.data_manager.custom_data import CustomDataPoint, CustomDataService
from app.workspace.data_manager.data import BarRecord


@pytest.fixture
def test_db(tmp_path: Path) -> DatabaseManager:
    """Fixture providing an isolated SQLite database."""
    db_file = tmp_path / "test_baskets.db"
    db = DatabaseManager(database_path=db_file)
    db.initialize()
    return db


def test_basket_persistence_crud(
    test_db: DatabaseManager, caplog: pytest.LogCaptureFixture
) -> None:
    """Validate full CRUD operations for baskets in datamgr_stock_group."""
    caplog.set_level(logging.DEBUG)
    service = BasketService(test_db)

    assert service.list_baskets() == []
    assert service.get_basket("TechBasket") is None

    basket = BasketDefinition(
        name="TechBasket",
        description="Top Tech Equities",
        items=[
            BasketItem(symbol="AAPL", weight=1.0),
            BasketItem(symbol="MSFT", weight=1.0),
        ],
    )
    group_id = service.save_basket(basket)
    assert group_id > 0

    # FR log verification
    assert any("FR-DATA-BASKETS-GROUPS" in rec.message for rec in caplog.records)

    # Read back
    retrieved = service.get_basket("TechBasket")
    assert retrieved is not None
    assert retrieved.name == "TechBasket"
    assert len(retrieved.items) == 2
    assert retrieved.items[0].symbol == "AAPL"
    assert retrieved.items[0].weight == 1.0

    # Update basket
    updated = retrieved.model_copy(
        update={
            "description": "Updated Description",
            "items": [
                BasketItem(symbol="AAPL", weight=1.0),
                BasketItem(symbol="NVDA", weight=1.0),
            ],
        }
    )
    service.save_basket(updated)
    retrieved2 = service.get_basket("TechBasket")
    assert retrieved2 is not None
    assert retrieved2.description == "Updated Description"
    assert len(retrieved2.items) == 2
    assert retrieved2.items[1].symbol == "NVDA"

    # List
    all_baskets = service.list_baskets()
    assert len(all_baskets) == 1

    # Delete
    assert service.delete_basket("TechBasket") is True
    assert service.get_basket("TechBasket") is None
    assert service.delete_basket("TechBasket") is False


def test_basket_series_alignment_intersection(test_db: DatabaseManager) -> None:
    """Validate intersection alignment (inner join) across multi-symbol series."""
    service = BasketService(test_db)

    # Symbol A has timestamps T1, T2, T3
    bars_a = [
        BarRecord(
            timestamp_utc=f"2026-10-07T10:0{i}:00Z",
            open=100.0 + i,
            high=102.0 + i,
            low=99.0 + i,
            close=101.0 + i,
            volume=50.0,
        )
        for i in range(3)
    ]
    # Symbol B has timestamps T1, T2, T4 (missing T3, extra T4)
    bars_b = [
        BarRecord(
            timestamp_utc="2026-10-07T10:00:00Z",
            open=200.0,
            high=205.0,
            low=198.0,
            close=202.0,
            volume=100.0,
        ),
        BarRecord(
            timestamp_utc="2026-10-07T10:01:00Z",
            open=202.0,
            high=206.0,
            low=200.0,
            close=204.0,
            volume=120.0,
        ),
        BarRecord(
            timestamp_utc="2026-10-07T10:04:00Z",
            open=205.0,
            high=208.0,
            low=203.0,
            close=206.0,
            volume=110.0,
        ),
    ]

    series_dict = {"A": bars_a, "B": bars_b}

    # Intersection: common timestamps are T0 (10:00) and T1 (10:01)
    aligned = service.align_series(series_dict, policy="intersection")
    assert len(aligned) == 2
    assert "A" in aligned[0] and "B" in aligned[0]
    assert aligned[0]["A"].timestamp_utc == "2026-10-07T10:00:00Z"
    assert aligned[1]["B"].timestamp_utc == "2026-10-07T10:01:00Z"


def test_basket_series_alignment_union_forward_fill(
    test_db: DatabaseManager,
) -> None:
    """Validate union alignment (outer join) with forward-fill for missing bars."""
    service = BasketService(test_db)

    bars_a = [
        BarRecord(
            timestamp_utc="2026-10-07T10:00:00Z",
            open=100.0,
            high=102.0,
            low=98.0,
            close=101.0,
            volume=50.0,
        ),
        BarRecord(
            timestamp_utc="2026-10-07T10:02:00Z",
            open=102.0,
            high=104.0,
            low=100.0,
            close=103.0,
            volume=60.0,
        ),
    ]
    bars_b = [
        BarRecord(
            timestamp_utc="2026-10-07T10:00:00Z",
            open=200.0,
            high=205.0,
            low=195.0,
            close=202.0,
            volume=80.0,
        ),
        BarRecord(
            timestamp_utc="2026-10-07T10:01:00Z",
            open=202.0,
            high=206.0,
            low=200.0,
            close=204.0,
            volume=90.0,
        ),
        BarRecord(
            timestamp_utc="2026-10-07T10:02:00Z",
            open=204.0,
            high=207.0,
            low=202.0,
            close=205.0,
            volume=100.0,
        ),
    ]

    series_dict = {"A": bars_a, "B": bars_b}
    aligned = service.align_series(series_dict, policy="union")

    # Timestamps: 10:00, 10:01, 10:02
    assert len(aligned) == 3
    # At 10:01, A should be forward-filled from 10:00 bar
    assert aligned[1]["A"].close == 101.0
    assert aligned[1]["B"].close == 204.0


def test_basket_synthetic_calculation(
    test_db: DatabaseManager, caplog: pytest.LogCaptureFixture
) -> None:
    """Validate weighted average OHLCV synthetic bar calculation."""
    caplog.set_level(logging.DEBUG)
    service = BasketService(test_db)

    basket = BasketDefinition(
        name="EqualBasket",
        items=[
            BasketItem(symbol="AAPL", weight=1.0),
            BasketItem(symbol="MSFT", weight=1.0),
        ],
    )

    bars_aapl = [
        BarRecord(
            timestamp_utc="2026-10-07T10:00:00Z",
            open=100.0,
            high=110.0,
            low=90.0,
            close=105.0,
            volume=100.0,
        )
    ]
    bars_msft = [
        BarRecord(
            timestamp_utc="2026-10-07T10:00:00Z",
            open=200.0,
            high=210.0,
            low=190.0,
            close=205.0,
            volume=200.0,
        )
    ]

    series_dict = {"AAPL": bars_aapl, "MSFT": bars_msft}
    synth_bars = service.compute_basket_series(basket, series_dict)

    assert len(synth_bars) == 1
    synth = synth_bars[0]
    # (100 + 200) / 2 = 150
    assert synth.open == 150.0
    # (110 + 210) / 2 = 160
    assert synth.high == 160.0
    # (90 + 190) / 2 = 140
    assert synth.low == 140.0
    # (105 + 205) / 2 = 155
    assert synth.close == 155.0
    # Volume sum = 300
    assert synth.volume == 300.0

    assert any("FR-DATA-BASKETS-ALIGNMENT" in rec.message for rec in caplog.records)


def test_custom_data_service(
    test_db: DatabaseManager, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Validate CustomDataService persistence and synchronization with price bars."""
    caplog.set_level(logging.DEBUG)
    service = CustomDataService(test_db, storage_dir=tmp_path / "custom")

    assert service.list_custom_series() == []

    points = [
        CustomDataPoint(
            timestamp_utc="2026-10-07T10:00:00Z",
            values={"sentiment": 0.8, "vix": 16.5},
        ),
        CustomDataPoint(
            timestamp_utc="2026-10-07T10:02:00Z",
            values={"sentiment": 0.6, "vix": 17.0},
        ),
    ]

    saved_count = service.save_custom_series("market_sentiment", points)
    assert saved_count == 2

    # Query back
    retrieved = service.get_custom_series("market_sentiment")
    assert len(retrieved) == 2
    assert retrieved[0].values["sentiment"] == 0.8

    # List & Delete
    assert "market_sentiment" in service.list_custom_series()

    # Align with price bars
    bars = [
        BarRecord(
            timestamp_utc="2026-10-07T10:00:00Z",
            open=100.0,
            high=102.0,
            low=99.0,
            close=101.0,
            volume=50.0,
        ),
        BarRecord(
            timestamp_utc="2026-10-07T10:01:00Z",
            open=101.0,
            high=103.0,
            low=100.0,
            close=102.0,
            volume=55.0,
        ),
        BarRecord(
            timestamp_utc="2026-10-07T10:02:00Z",
            open=102.0,
            high=104.0,
            low=101.0,
            close=103.0,
            volume=60.0,
        ),
    ]

    aligned = service.align_with_bars(bars, points, fill_method="forward_fill")
    assert len(aligned) == 3
    # At 10:00: sentiment=0.8
    assert aligned[0]["sentiment"] == 0.8
    # At 10:01: forward filled from 10:00 -> sentiment=0.8
    assert aligned[1]["sentiment"] == 0.8
    # At 10:02: sentiment=0.6
    assert aligned[2]["sentiment"] == 0.6

    assert service.delete_custom_series("market_sentiment") is True
    assert service.get_custom_series("market_sentiment") == []
    assert any("FR-DATA-CUSTOM-SERIES" in rec.message for rec in caplog.records)


def test_custom_data_edge_cases(test_db: DatabaseManager, tmp_path: Path) -> None:
    """Validate error paths and empty fallbacks in CustomDataService."""
    non_existent_dir = tmp_path / "does_not_exist"
    service = CustomDataService(test_db, storage_dir=non_existent_dir)
    assert service.list_custom_series() == []
    assert service.delete_custom_series("unknown") is False
    assert service.align_with_bars([], []) == []

    # Corrupted json series
    bad_dir = tmp_path / "bad_series"
    bad_dir.mkdir(parents=True)
    bad_file = bad_dir / "corrupted.json"
    bad_file.write_text("{not-valid-json", encoding="utf-8")
    bad_service = CustomDataService(test_db, storage_dir=bad_dir)
    assert bad_service.get_custom_series("corrupted") == []

    # Nearest alignment test
    points = [
        CustomDataPoint(timestamp_utc="2026-10-07T10:00:00Z", values={"sentiment": 0.8})
    ]
    bars = [
        BarRecord(
            timestamp_utc="2026-10-07T10:01:00Z",
            open=100.0,
            high=102.0,
            low=99.0,
            close=101.0,
            volume=50.0,
        )
    ]
    aligned_nearest = service.align_with_bars(bars, points, fill_method="nearest")
    assert len(aligned_nearest) == 1
    assert aligned_nearest[0]["sentiment"] == 0.8
