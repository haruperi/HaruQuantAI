"""Tests for FEAT-DATA-DATASETS (app/services/data/datasets.py)."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from app.contracts.data import (
    BarRecord,
    TickRecord,
)
from app.services.data.datasets import (
    DatasetConfig,
    DatasetServiceImpl,
)
from app.services.persistence.data import (
    DataPersistenceConfig,
    DataPersistenceServiceImpl,
)
from app.services.persistence.database import (
    DatabaseConfig,
    DatabaseServiceImpl,
)


async def _setup_datasets(tmp_path: Path) -> DatasetServiceImpl:
    db_file = tmp_path / "test_datasets.db"
    db = DatabaseServiceImpl(DatabaseConfig(database_path=db_file))
    persist = DataPersistenceServiceImpl(
        db, DataPersistenceConfig(preseed_defaults=True)
    )
    await persist.initialize_schema()
    cfg = DatasetConfig(storage_dir=tmp_path / "datasets")
    return DatasetServiceImpl(persist, cfg)


def test_bars_parquet_persistence_and_loading(tmp_path: Path) -> None:
    """Verify storing and loading normalized bars in Parquet format."""

    async def _test() -> None:
        service = await _setup_datasets(tmp_path)
        base_time = datetime(2026, 6, 1, 10, 0, 0, tzinfo=UTC)

        bars = [
            BarRecord(
                timestamp=base_time + timedelta(minutes=i),
                open=1.0500 + i * 0.0001,
                high=1.0505 + i * 0.0001,
                low=1.0495 + i * 0.0001,
                close=1.0502 + i * 0.0001,
                volume=100.0 + i,
                source="test_feed",
            )
            for i in range(10)
        ]

        manifest = await service.persist_bars(
            symbol="EURUSD",
            timeframe="M1",
            source_id="test_src",
            bars=bars,
        )
        assert manifest.dataset_id.startswith("ds_eurusd_m1_")
        assert manifest.row_count == 10
        assert manifest.sha256_hash != ""
        assert await asyncio.to_thread(Path(manifest.parquet_path).exists)

        # Load all bars
        loaded = await service.load_bars(manifest.dataset_id)
        assert len(loaded) == 10
        assert loaded[0].open == pytest.approx(1.0500)
        assert loaded[-1].close == pytest.approx(1.0511)

        # Range filter
        range_start = base_time + timedelta(minutes=2)
        range_end = base_time + timedelta(minutes=5)
        filtered = await service.load_bars(
            manifest.dataset_id, start=range_start, end=range_end
        )
        assert len(filtered) == 4

    asyncio.run(_test())


def test_ticks_parquet_persistence_and_loading(tmp_path: Path) -> None:
    """Verify storing and loading normalized ticks in Parquet format."""

    async def _test() -> None:
        service = await _setup_datasets(tmp_path)
        base_time = datetime(2026, 6, 1, 10, 0, 0, tzinfo=UTC)

        ticks = [
            TickRecord(
                timestamp=base_time + timedelta(seconds=i),
                bid=1.0500 + i * 0.00005,
                ask=1.0501 + i * 0.00005,
                sequence=i,
                bid_volume=1.5,
                ask_volume=2.0,
            )
            for i in range(20)
        ]

        manifest = await service.persist_ticks(
            symbol="EURUSD",
            source_id="test_ticks",
            ticks=ticks,
        )
        assert manifest.dataset_id.startswith("ds_eurusd_ticks_")
        assert manifest.row_count == 20
        assert manifest.data_kind == "ticks"

        loaded = await service.load_ticks(manifest.dataset_id)
        assert len(loaded) == 20
        assert loaded[0].bid == pytest.approx(1.0500)
        assert loaded[-1].ask == pytest.approx(1.05105)

    asyncio.run(_test())


def test_list_manifests(tmp_path: Path) -> None:
    """Verify querying manifests by symbol and timeframe."""

    async def _test() -> None:
        service = await _setup_datasets(tmp_path)
        base_time = datetime(2026, 6, 1, 10, 0, 0, tzinfo=UTC)

        bars = [
            BarRecord(
                timestamp=base_time,
                open=1.0,
                high=1.1,
                low=0.9,
                close=1.05,
            )
        ]
        await service.persist_bars("GBPUSD", "H1", "src1", bars)
        await service.persist_bars("EURUSD", "M1", "src2", bars)

        # Filter by symbol
        gbp_list = await service.list_manifests(symbol="GBPUSD")
        assert len(gbp_list) == 1
        assert gbp_list[0].symbol == "GBPUSD"

        # Filter by timeframe
        m1_list = await service.list_manifests(timeframe="M1")
        assert len(m1_list) == 1
        assert m1_list[0].symbol == "EURUSD"

    asyncio.run(_test())


def test_content_addressed_determinism_and_idempotence(tmp_path: Path) -> None:
    """Verify content-addressed dataset ID determinism and idempotent republishing."""

    async def _test() -> None:
        service = await _setup_datasets(tmp_path)
        base_time = datetime(2026, 6, 1, 10, 0, 0, tzinfo=UTC)

        bars = [
            BarRecord(
                timestamp=base_time + timedelta(minutes=i),
                open=1.1000 + i * 0.001,
                high=1.1010 + i * 0.001,
                low=1.0990 + i * 0.001,
                close=1.1005 + i * 0.001,
                volume=50.0,
                source="feed1",
            )
            for i in range(5)
        ]

        m1 = await service.persist_bars(
            "EURUSD", "M1", "feed1", bars, quality_score=0.98
        )
        m2 = await service.persist_bars(
            "EURUSD", "M1", "feed1", bars, quality_score=0.98
        )

        assert m1.dataset_id == m2.dataset_id
        assert m1.sha256_hash == m2.sha256_hash
        assert m1.quality_score == pytest.approx(0.98)

        # Mutate one bar price and verify ID changes
        mutated_bars = list(bars)
        mutated_bars[0] = BarRecord(
            timestamp=base_time,
            open=1.2000,
            high=1.2010,
            low=1.1990,
            close=1.2005,
            volume=50.0,
            source="feed1",
        )
        m3 = await service.persist_bars("EURUSD", "M1", "feed1", mutated_bars)
        assert m3.dataset_id != m1.dataset_id

    asyncio.run(_test())
