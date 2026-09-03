"""Comprehensive automated tests for Partitioned Parquet Market Data Store."""

from __future__ import annotations

import tempfile
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import numpy as np
import polars as pl
import pyarrow as pa
import pytest
from app.contracts.data.market_data_store import ScanRangeQuery
from app.services.data.market_data_store.config import MarketDataStoreConfig
from app.services.data.market_data_store.market_data_store import MarketDataStoreService
from app.services.data.market_data_store.schema import (
    price_to_ticks,
    ticks_to_price,
)


@pytest.fixture
def temp_store_env():
    """Create isolated temporary store configuration and service instance."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        storage_root = tmp_path / "market_data"
        catalog_db = tmp_path / "catalog.duckdb"

        config = MarketDataStoreConfig(
            storage_root=storage_root,
            compression="zstd",
            compression_level=6,
            min_rows_per_group=1000,
            max_rows_per_group=5000,
            max_rows_per_file=10000,
            manifest_database_path=catalog_db,
        )
        service = MarketDataStoreService(config=config)
        try:
            yield service, storage_root
        finally:
            service.close()


def test_fixed_point_conversions():
    """Verify price to tick integer conversions and round-trip fidelity."""
    tick_size = 0.00001
    price = 1.08534
    ticks = price_to_ticks(price, tick_size)
    assert ticks == 108534
    restored = ticks_to_price(ticks, tick_size)
    assert round(float(restored), 5) == price

    # Decimal precision tests
    dec_tick = Decimal("0.001")
    dec_price = Decimal("145.678")
    assert price_to_ticks(dec_price, dec_tick) == 145678


def test_append_ticks_and_immutability(temp_store_env):
    """Verify tick appending creates immutable part files and updates catalog."""
    service, _ = temp_store_env
    source = "mt5-pepperstone"
    symbol = "EURUSD"
    rng = np.random.default_rng(42)

    # Batch 1: 5,000 ticks on 2026-08-01
    base_time = datetime(2026, 8, 1, 10, 0, 0, tzinfo=UTC)
    n_rows = 5000
    times = [base_time + timedelta(milliseconds=i * 100) for i in range(n_rows)]
    bids = 1.08500 + np.sin(np.linspace(0, 10, n_rows)) * 0.00200
    asks = bids + 0.00012
    vols = rng.integers(100, 5000, size=n_rows)

    df1 = pl.DataFrame(
        {
            "datetime": times,
            "bid": bids,
            "ask": asks,
            "volume": vols,
        }
    )

    receipt1 = service.append_ticks(
        df1, source=source, symbol=symbol, tick_size=0.00001
    )
    assert receipt1.row_count == n_rows
    assert len(receipt1.part_paths) == 1
    part1_path = Path(receipt1.part_paths[0])
    assert part1_path.exists()
    assert "source=mt5-pepperstone" in str(part1_path)
    assert "symbol=EURUSD" in str(part1_path)
    assert "year=2026" in str(part1_path)
    assert "month=08" in str(part1_path)

    # Batch 2: Append 3,000 additional ticks for the same month
    times2 = [base_time + timedelta(hours=1, milliseconds=i * 100) for i in range(3000)]
    bids2 = 1.08600 + np.sin(np.linspace(0, 5, 3000)) * 0.00100
    asks2 = bids2 + 0.00010
    vols2 = rng.integers(100, 3000, size=3000)

    df2 = pl.DataFrame(
        {
            "datetime": times2,
            "bid": bids2,
            "ask": asks2,
            "volume": vols2,
        }
    )

    receipt2 = service.append_ticks(
        df2, source=source, symbol=symbol, tick_size=0.00001
    )
    assert receipt2.row_count == 3000
    assert len(receipt2.part_paths) == 1
    part2_path = Path(receipt2.part_paths[0])
    assert part2_path.exists()

    # Invariant: part 1 was NOT overwritten or recreated
    assert part1_path != part2_path
    assert part1_path.exists()

    # Verify DuckDB manifest has both parts recorded
    latest_ts = service.get_latest_timestamp(
        dataset="ticks", source=source, symbol=symbol
    )
    assert latest_ts is not None
    assert latest_ts == times2[-1]


def test_polars_lazy_scan_ticks(temp_store_env):
    """Verify Polars lazy scan range queries, pushdown, and price restoration."""
    service, _ = temp_store_env
    source = "dukascopy"
    symbol = "USDJPY"

    base_time = datetime(2026, 8, 10, 0, 0, 0, tzinfo=UTC)
    n = 2000
    times = [base_time + timedelta(seconds=i) for i in range(n)]
    bids = 145.000 + np.linspace(0, 1.0, n)
    asks = bids + 0.015

    df = pl.DataFrame(
        {
            "datetime": times,
            "bid": bids,
            "ask": asks,
            "volume": np.ones(n, dtype=int),
        }
    )

    service.append_ticks(df, source=source, symbol=symbol, tick_size=0.001)

    # Query range with price restoration
    q = ScanRangeQuery(
        source=source,
        symbol=symbol,
        start=base_time + timedelta(seconds=100),
        end=base_time + timedelta(seconds=500),
        restore_prices=True,
        tick_size=0.001,
    )

    lf = service.scan_ticks(q)
    res = lf.collect()
    assert len(res) == 400
    assert "bid" in res.columns
    assert "ask" in res.columns
    assert "spread" in res.columns
    assert pytest.approx(res["spread"][0], abs=1e-5) == 0.015


def test_append_and_scan_bars(temp_store_env):
    """Verify M1 bars appending, partitioning, and scanning."""
    service, _ = temp_store_env
    source = "binance"
    symbol = "BTCUSDT"
    rng = np.random.default_rng(123)

    base_time = datetime(2026, 5, 1, 0, 0, 0, tzinfo=UTC)
    n_bars = 1440  # 1 full day of M1
    times = [base_time + timedelta(minutes=i) for i in range(n_bars)]
    opens = 65000.0 + np.cumsum(rng.standard_normal(n_bars) * 10)
    highs = opens + 15.0
    lows = opens - 15.0
    closes = opens + 2.0
    vols = rng.integers(10, 100, size=n_bars)

    df_bars = pl.DataFrame(
        {
            "datetime": times,
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
            "volume": vols,
        }
    )

    receipt = service.append_bars(
        df_bars, source=source, symbol=symbol, timeframe="M1", tick_size=0.01
    )
    assert receipt.row_count == n_bars

    part_file = Path(receipt.part_paths[0])
    assert "timeframe=M1" in str(part_file)

    q = ScanRangeQuery(
        source=source,
        symbol=symbol,
        timeframe="M1",
        start=base_time + timedelta(hours=2),
        end=base_time + timedelta(hours=8),
        tick_size=0.01,
    )

    scanned_bars = service.scan_bars(q).collect()
    assert len(scanned_bars) == 360  # 6 hours * 60 minutes
    assert "open" in scanned_bars.columns
    assert "close" in scanned_bars.columns


def test_duckdb_sql_analytics(temp_store_env):
    """Verify DuckDB direct SQL queries over partitioned Parquet files."""
    service, _ = temp_store_env
    source = "dukascopy"
    symbol = "EURUSD"

    base_time = datetime(2026, 8, 1, 12, 0, 0, tzinfo=UTC)
    times = [base_time + timedelta(seconds=i) for i in range(1000)]
    bids = 1.08500 + np.linspace(0, 0.00100, 1000)
    asks = bids + 0.00010

    df = pl.DataFrame({"datetime": times, "bid": bids, "ask": asks, "volume": 100})
    service.append_ticks(df, source=source, symbol=symbol, tick_size=0.00001)

    rel = service.query_sql(
        """
        SELECT
            symbol,
            count(*) AS tick_count,
            avg(ask_ticks - bid_ticks) AS avg_spread_ticks,
            max(datetime) AS last_tick_time
        FROM ticks
        WHERE source = 'dukascopy' AND symbol = 'EURUSD'
        GROUP BY symbol
        """
    )
    res = rel.fetchall()
    assert len(res) == 1
    assert res[0][0] == "EURUSD"
    assert res[0][1] == 1000
    assert pytest.approx(res[0][2], abs=0.1) == 10.0


def test_empty_batch_handling(temp_store_env):
    """Verify empty tables return zero-row receipts without error."""
    service, _ = temp_store_env
    empty_tab = pa.table(
        {
            "datetime": pa.array([], type=pa.timestamp("us", tz="UTC")),
            "bid": [],
            "ask": [],
        }
    )
    receipt = service.append_ticks(empty_tab, source="empty", symbol="EURUSD")
    assert receipt.row_count == 0
    assert len(receipt.part_paths) == 0

    receipt_bar = service.append_bars(
        pa.table({"datetime": [], "open": [], "high": [], "low": [], "close": []}),
        source="empty",
        symbol="EURUSD",
    )
    assert receipt_bar.row_count == 0


def test_deduplication_and_sorting(temp_store_env):
    """Verify out-of-order and duplicated ticks are sorted and deduped."""
    service, _ = temp_store_env
    source = "test-feed"
    symbol = "GBPUSD"

    dt1 = datetime(2026, 8, 1, 10, 0, 1, tzinfo=UTC)
    dt2 = datetime(2026, 8, 1, 10, 0, 0, tzinfo=UTC)  # earlier!
    dt3 = datetime(2026, 8, 1, 10, 0, 1, tzinfo=UTC)  # duplicate of dt1

    df = pl.DataFrame(
        {
            "datetime": [dt1, dt2, dt3],
            "bid": [1.2500, 1.2490, 1.2500],
            "ask": [1.2502, 1.2492, 1.2502],
            "sequence": [0, 0, 0],
        }
    )

    receipt = service.append_ticks(df, source=source, symbol=symbol, tick_size=0.0001)
    assert receipt.row_count == 2  # 1 duplicate removed

    q = ScanRangeQuery(
        source=source,
        symbol=symbol,
        start=datetime(2026, 8, 1, 0, 0, 0, tzinfo=UTC),
        end=datetime(2026, 8, 2, 0, 0, 0, tzinfo=UTC),
        restore_prices=False,
    )
    res = service.scan_ticks(q).collect()
    assert len(res) == 2
    assert res["datetime"][0] == dt2
    assert res["datetime"][1] == dt1


def test_catalog_summary_and_stats(temp_store_env):
    """Verify catalog summary statistics aggregation across datasets."""
    service, _ = temp_store_env
    dt = datetime(2026, 8, 1, 12, 0, 0, tzinfo=UTC)
    df = pl.DataFrame({"datetime": [dt], "bid": [1.0850], "ask": [1.0851]})
    service.append_ticks(df, source="srcA", symbol="EURUSD", tick_size=0.0001)

    df_bar = pl.DataFrame(
        {
            "datetime": [dt],
            "open": [1.0850],
            "high": [1.0855],
            "low": [1.0845],
            "close": [1.0852],
        }
    )
    service.append_bars(
        df_bar, source="srcA", symbol="EURUSD", timeframe="M1", tick_size=0.0001
    )

    summary = service.catalog.get_summary()
    assert len(summary) == 2
    datasets = {s["dataset"] for s in summary}
    assert "ticks" in datasets
    assert "bars" in datasets


def test_catalog_list_parts(temp_store_env):
    """Verify listing catalog parts with range filtering."""
    service, _ = temp_store_env
    dt1 = datetime(2026, 8, 1, 10, 0, 0, tzinfo=UTC)
    dt2 = datetime(2026, 8, 2, 10, 0, 0, tzinfo=UTC)

    df1 = pl.DataFrame({"datetime": [dt1], "bid": [1.0850], "ask": [1.0851]})
    df2 = pl.DataFrame({"datetime": [dt2], "bid": [1.0860], "ask": [1.0861]})

    service.append_ticks(df1, source="srcB", symbol="EURUSD", tick_size=0.0001)
    service.append_ticks(df2, source="srcB", symbol="EURUSD", tick_size=0.0001)

    all_parts = service.catalog.list_parts("ticks", "srcB", "EURUSD")
    assert len(all_parts) == 2

    # Filter by time range
    filtered = service.catalog.list_parts(
        "ticks", "srcB", "EURUSD", start=dt1, end=dt1 + timedelta(hours=1)
    )
    assert len(filtered) == 1
    assert filtered[0].minimum_datetime == dt1


@pytest.mark.asyncio
async def test_feature_lifecycle():
    """Verify MarketDataStoreFeature mount, capability provision, and unmount."""
    from app.contracts.data.capabilities import MARKET_DATA_STORE_CAPABILITY
    from app.services.data.market_data_store.feature import (
        MarketDataStoreFeature,
        feature,
    )

    feat = feature()
    assert isinstance(feat, MarketDataStoreFeature)

    # Mock FeatureContext
    class DummyContext:
        def __init__(self):
            self.capabilities = {}

        def provide(self, key, provider):
            self.capabilities[key] = provider

    ctx = DummyContext()
    with tempfile.TemporaryDirectory() as tmp_dir:
        config = {
            "storage_root": str(Path(tmp_dir) / "data"),
            "manifest_database_path": str(Path(tmp_dir) / "cat.duckdb"),
        }
        await feat.mount(ctx, config)
        assert MARKET_DATA_STORE_CAPABILITY in ctx.capabilities
        assert feat.service is not None

        await feat.unmount(ctx)
        assert feat.service is None
