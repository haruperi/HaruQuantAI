"""Tests for Parquet columnar market store feature (FEAT-PERSISTENCE-PARQUET)."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.contracts.persistence import (
    PARQUET_STORE_SERVICE,
    BarRecord,
    TickRecord,
)
from app.kernel.bootstrapper import Runtime
from app.services.persistence.parquet_store import (
    ParquetConfig,
    ParquetFeature,
    ParquetStoreServiceImpl,
    feature,
)


def test_write_and_read_bars(tmp_path: Path) -> None:
    """Test partitioned bars writing, date-range filtering, and limits."""
    market_dir = tmp_path / "market"
    store = ParquetStoreServiceImpl(ParquetConfig(market_dir=market_dir))

    t0 = datetime(2024, 1, 1, 12, 0, tzinfo=UTC)
    t1 = datetime(2024, 6, 1, 12, 0, tzinfo=UTC)
    t2 = datetime(2025, 1, 1, 12, 0, tzinfo=UTC)

    bars = [
        BarRecord(
            t0,
            open=1.1000,
            high=1.1050,
            low=1.0990,
            close=1.1020,
            volume=100.0,
            ticks=50,
        ),
        BarRecord(
            t1,
            open=1.1020,
            high=1.1080,
            low=1.1010,
            close=1.1070,
            volume=150.0,
            ticks=75,
        ),
        BarRecord(
            t2,
            open=1.1070,
            high=1.1100,
            low=1.1050,
            close=1.1090,
            volume=200.0,
            ticks=90,
        ),
    ]

    written = store.write_bars("EURUSD", "M1", bars)
    assert written == 3

    # Check partition files created
    p2024 = market_dir / "EURUSD" / "M1" / "2024.parquet"
    p2025 = market_dir / "EURUSD" / "M1" / "2025.parquet"
    assert p2024.is_file()
    assert p2025.is_file()

    # Read all bars
    all_bars = store.read_bars("EURUSD", "M1")
    assert len(all_bars) == 3
    assert all_bars[0].timestamp_utc == t0
    assert all_bars[2].timestamp_utc == t2

    # Read with time range filter
    filtered = store.read_bars(
        "EURUSD",
        "M1",
        start_time_utc=datetime(2024, 5, 1, tzinfo=UTC),
        end_time_utc=datetime(2024, 12, 31, tzinfo=UTC),
    )
    assert len(filtered) == 1
    assert filtered[0].timestamp_utc == t1

    # Read with limit
    limited = store.read_bars("EURUSD", "M1", limit=2)
    assert len(limited) == 2
    assert limited[0].timestamp_utc == t0
    assert limited[1].timestamp_utc == t1


def test_bars_deduplication_and_merge(tmp_path: Path) -> None:
    """Test merging and updating existing bars partitions."""
    market_dir = tmp_path / "market"
    store = ParquetStoreServiceImpl(ParquetConfig(market_dir=market_dir))

    t0 = datetime(2024, 1, 1, 12, 0, tzinfo=UTC)
    t1 = datetime(2024, 1, 1, 12, 1, tzinfo=UTC)

    # Initial write
    store.write_bars(
        "GBPUSD",
        "M1",
        [
            BarRecord(
                t0,
                open=1.2000,
                high=1.2050,
                low=1.1990,
                close=1.2020,
                volume=50.0,
                ticks=25,
            )
        ],
    )

    # Second write with update to t0 and new bar t1
    store.write_bars(
        "GBPUSD",
        "M1",
        [
            BarRecord(
                t0,
                open=1.2000,
                high=1.2060,
                low=1.1990,
                close=1.2050,
                volume=120.0,
                ticks=60,
            ),
            BarRecord(
                t1,
                open=1.2050,
                high=1.2090,
                low=1.2040,
                close=1.2080,
                volume=80.0,
                ticks=40,
            ),
        ],
    )

    bars = store.read_bars("GBPUSD", "M1")
    assert len(bars) == 2
    assert bars[0].timestamp_utc == t0
    assert bars[0].volume == 120.0
    assert bars[0].high == 1.2060
    assert bars[1].timestamp_utc == t1


def test_write_and_read_ticks(tmp_path: Path) -> None:
    """Test tick series writing and reading."""
    market_dir = tmp_path / "market"
    store = ParquetStoreServiceImpl(ParquetConfig(market_dir=market_dir))

    t0 = datetime(2024, 3, 15, 10, 0, 0, tzinfo=UTC)
    t1 = t0 + timedelta(milliseconds=100)
    t2 = t0 + timedelta(milliseconds=250)

    ticks = [
        TickRecord(t0, bid=1.0500, ask=1.0502, bid_volume=1.5, ask_volume=2.0),
        TickRecord(t1, bid=1.0501, ask=1.0503, bid_volume=1.0, ask_volume=1.2),
        TickRecord(t2, bid=1.0502, ask=1.0504, bid_volume=3.0, ask_volume=2.5),
    ]

    written = store.write_ticks("USDJPY", ticks)
    assert written == 3

    tick_file = market_dir / "USDJPY" / "tick" / "2024.parquet"
    assert tick_file.is_file()

    read_back = store.read_ticks("USDJPY")
    assert len(read_back) == 3
    assert read_back[0].bid == 1.0500
    assert read_back[2].ask == 1.0504

    # Limit
    limited = store.read_ticks("USDJPY", limit=1)
    assert len(limited) == 1
    assert limited[0].timestamp_utc == t0


def test_list_and_delete_partitions(tmp_path: Path) -> None:
    """Test partition discovery and partition deletion."""
    market_dir = tmp_path / "market"
    store = ParquetStoreServiceImpl(ParquetConfig(market_dir=market_dir))

    t24 = datetime(2024, 1, 1, tzinfo=UTC)
    t25 = datetime(2025, 1, 1, tzinfo=UTC)

    store.write_bars("EURUSD", "M1", [BarRecord(t24, 1.0, 1.1, 0.9, 1.05, 10.0, 5)])
    store.write_bars("EURUSD", "M1", [BarRecord(t25, 1.0, 1.1, 0.9, 1.05, 10.0, 5)])
    store.write_ticks("EURUSD", [TickRecord(t24, 1.0, 1.01, 1.0, 1.0)])

    partitions = store.list_partitions()
    assert len(partitions) == 3

    # Delete 2024 M1 partition
    assert store.delete_partition("EURUSD", "M1", 2024) is True
    assert store.delete_partition("EURUSD", "M1", 2024) is False

    remaining = store.list_partitions()
    assert len(remaining) == 2
    assert not any(p.timeframe == "M1" and p.year == 2024 for p in remaining)


def test_empty_and_missing_handling(tmp_path: Path) -> None:
    """Test graceful handling of empty inputs and non-existent series."""
    market_dir = tmp_path / "market"
    store = ParquetStoreServiceImpl(ParquetConfig(market_dir=market_dir))

    assert store.write_bars("NONE", "M1", []) == 0
    assert store.write_ticks("NONE", []) == 0
    assert store.read_bars("NONEXISTENT", "M1") == []
    assert store.read_ticks("NONEXISTENT") == []
    assert store.delete_partition("NONE", "M1", 2099) is False


def test_parquet_feature_lifecycle(tmp_path: Path) -> None:
    """Test runtime composition of ParquetFeature."""

    async def _test() -> None:
        market_dir = tmp_path / "runtime_market"
        runtime = Runtime(
            [lambda: ParquetFeature(ParquetConfig(market_dir=market_dir))]
        )
        async with runtime:
            service = runtime.require(PARQUET_STORE_SERVICE)
            t = datetime(2024, 5, 1, tzinfo=UTC)
            count = service.write_bars(
                "TEST", "M5", [BarRecord(t, 1.0, 1.1, 0.9, 1.0, 10.0, 1)]
            )
            assert count == 1
            read = service.read_bars("TEST", "M5")
            assert len(read) == 1

    asyncio.run(_test())


def test_parquet_factory() -> None:
    """Test zero-argument factory returns ParquetFeature."""
    f = feature()
    assert isinstance(f, ParquetFeature)
    assert f.spec.name == "persistence.parquet"
    assert PARQUET_STORE_SERVICE in f.spec.provides
