"""Tests for FEAT-DATA-MARKET_DATA (app/services/data/market_data.py)."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from pathlib import Path

import pytest
from app.contracts.brokers import (
    BrokerConnectionConfig,
    ConnectionHealth,
    ConnectionState,
    RawTransportChunk,
)
from app.contracts.data import (
    BarRecord,
    TickRecord,
    build_market_data_request,
)
from app.services.data.datasets import (
    DatasetConfig,
    DatasetServiceImpl,
)
from app.services.data.market_data import (
    MarketDataConfig,
    MarketDataFeature,
    MarketDataServiceImpl,
    feature,
)
from app.services.data.quality import QualityServiceImpl
from app.services.persistence.data import (
    DataPersistenceConfig,
    DataPersistenceServiceImpl,
)
from app.services.persistence.database import (
    DatabaseConfig,
    DatabaseServiceImpl,
)


class MockFeedConnector:
    """Mock broker feed connector for testing market data client."""

    def __init__(
        self,
        name: str,
        with_ticks: bool = False,
        fail: bool = False,
    ) -> None:
        self.provider_name = name
        self.with_ticks = with_ticks
        self.fail = fail

    async def connect(self, config: BrokerConnectionConfig) -> None:
        pass

    async def disconnect(self) -> None:
        pass

    def is_connected(self) -> bool:
        return True

    async def get_health(self) -> ConnectionHealth:
        return ConnectionHealth(
            provider=self.provider_name, state=ConnectionState.READY
        )

    async def stream_raw_data(
        self, symbol: str, start_utc: datetime, end_utc: datetime
    ) -> AsyncIterator[RawTransportChunk]:
        if self.fail:
            msg = "Mock connector stream failure"
            raise RuntimeError(msg)

        if self.with_ticks:
            yield RawTransportChunk(
                provider=self.provider_name,
                symbol=symbol,
                sequence_num=1,
                timestamp_utc=start_utc,
                payload_bytes=b"dummy",
                metadata={
                    "ticks": [
                        TickRecord(
                            timestamp=start_utc,
                            bid=1.0500,
                            ask=1.0502,
                            sequence=1,
                            bid_volume=10.0,
                            ask_volume=10.0,
                        ),
                        TickRecord(
                            timestamp=start_utc,
                            bid=1.0500,
                            ask=1.0502,
                            sequence=1,
                            bid_volume=10.0,
                            ask_volume=10.0,
                        ),
                    ]
                },
            )
            return

        yield RawTransportChunk(
            provider=self.provider_name,
            symbol=symbol,
            sequence_num=1,
            timestamp_utc=start_utc,
            payload_bytes=b"dummy",
            metadata={
                "bars": [
                    BarRecord(
                        timestamp=start_utc,
                        open=1.0500,
                        high=1.0520,
                        low=1.0490,
                        close=1.0510,
                        volume=100.0,
                    ),
                    # Duplicate to test deduplication
                    BarRecord(
                        timestamp=start_utc,
                        open=1.0500,
                        high=1.0520,
                        low=1.0490,
                        close=1.0510,
                        volume=100.0,
                    ),
                ]
            },
        )


async def _setup_market_data(tmp_path: Path) -> MarketDataServiceImpl:
    db_file = tmp_path / "test_md.db"
    db = DatabaseServiceImpl(DatabaseConfig(database_path=db_file))
    persist = DataPersistenceServiceImpl(
        db, DataPersistenceConfig(preseed_defaults=True)
    )
    await persist.initialize_schema()
    ds_svc = DatasetServiceImpl(
        persist, DatasetConfig(storage_dir=tmp_path / "datasets")
    )
    connector = MockFeedConnector("test_provider")
    return MarketDataServiceImpl(
        dataset_service=ds_svc,
        persistence=persist,
        connectors={"test_provider": connector},
        config=MarketDataConfig(enable_caching=True),
    )


def test_build_market_data_request() -> None:
    """Verify market data request specification builder and temporal validation."""
    req = build_market_data_request(
        source_id="dukascopy",
        symbol="EURUSD",
        data_kind="bars",
        timeframe="M5",
        start=datetime(2026, 1, 1, tzinfo=UTC),
        end=datetime(2026, 1, 2, tzinfo=UTC),
    )
    assert req.source_id == "dukascopy"
    assert req.symbol == "EURUSD"
    assert req.timeframe == "M5"
    assert req.data_kind == "bars"

    # Temporal validation: start > end must fail
    with pytest.raises(
        ValueError, match="start timestamp must not be later than end timestamp"
    ):
        build_market_data_request(
            source_id="dukascopy",
            symbol="EURUSD",
            start=datetime(2026, 1, 5, tzinfo=UTC),
            end=datetime(2026, 1, 2, tzinfo=UTC),
        )


def test_fetch_from_connector_with_caching(tmp_path: Path) -> None:
    """Verify fetching data via connector and in-memory caching."""

    async def _test() -> None:
        svc = await _setup_market_data(tmp_path)
        start = datetime(2026, 6, 1, 10, 0, 0, tzinfo=UTC)
        end = datetime(2026, 6, 1, 11, 0, 0, tzinfo=UTC)

        req = build_market_data_request(
            source_id="test_provider",
            symbol="EURUSD",
            data_kind="bars",
            timeframe="M1",
            start=start,
            end=end,
        )

        # First fetch: streams from mock connector and dedupes
        bars = await svc.fetch_market_data(req)
        assert len(bars) == 1  # Duplicate was dropped
        bar0 = bars[0]
        assert isinstance(bar0, BarRecord)
        assert bar0.open == pytest.approx(1.0500)

        # Second fetch: served from in-memory cache
        bars_cached = await svc.fetch_market_data(req)
        assert len(bars_cached) == 1
        assert bars_cached is bars  # Object identity from cache

        # Clear cache
        svc.clear_cache()
        bars_fresh = await svc.fetch_market_data(req)
        assert len(bars_fresh) == 1

    asyncio.run(_test())


def test_sync_connectors(tmp_path: Path) -> None:
    """Verify synchronization across registered connectors and interval recording."""

    async def _test() -> None:
        svc = await _setup_market_data(tmp_path)
        report = await svc.sync_connectors()
        assert len(report.providers_synced) == 1
        assert report.providers_synced[0] == "test_provider"
        assert len(report.errors) == 0
        assert len(report.intervals) >= 1
        assert report.intervals[0].symbol == "EURUSD"
        assert report.intervals[0].records_fetched == 1

        # Test sync with zero connectors -> empty providers_synced, zero records
        svc_empty = MarketDataServiceImpl(
            dataset_service=svc._dataset_service,
            connectors={},
        )
        empty_report = await svc_empty.sync_connectors()
        assert len(empty_report.providers_synced) == 0
        assert empty_report.total_records == 0
        assert len(empty_report.intervals) == 0

    asyncio.run(_test())


def test_market_data_cache_eviction(tmp_path: Path) -> None:
    """Verify max_cache_items FIFO eviction."""

    async def _test() -> None:
        db_file = tmp_path / "test_cache_evict.db"
        db = DatabaseServiceImpl(DatabaseConfig(database_path=db_file))
        persist = DataPersistenceServiceImpl(
            db, DataPersistenceConfig(preseed_defaults=True)
        )
        await persist.initialize_schema()
        ds_svc = DatasetServiceImpl(
            persist, DatasetConfig(storage_dir=tmp_path / "datasets")
        )
        connector = MockFeedConnector("test_provider")
        svc = MarketDataServiceImpl(
            dataset_service=ds_svc,
            connectors={"test_provider": connector},
            config=MarketDataConfig(enable_caching=True, max_cache_items=2),
        )

        r1 = build_market_data_request(
            source_id="test_provider",
            symbol="EURUSD",
            start=datetime(2026, 6, 1, 10, 0, tzinfo=UTC),
            end=datetime(2026, 6, 1, 11, 0, tzinfo=UTC),
        )
        r2 = build_market_data_request(
            source_id="test_provider",
            symbol="GBPUSD",
            start=datetime(2026, 6, 1, 10, 0, tzinfo=UTC),
            end=datetime(2026, 6, 1, 11, 0, tzinfo=UTC),
        )
        r3 = build_market_data_request(
            source_id="test_provider",
            symbol="USDJPY",
            start=datetime(2026, 6, 1, 10, 0, tzinfo=UTC),
            end=datetime(2026, 6, 1, 11, 0, tzinfo=UTC),
        )

        _ = await svc.fetch_market_data(r1)
        _ = await svc.fetch_market_data(r2)
        assert len(svc._cache) == 2

        # Fetch r3: should evict r1 (FIFO)
        _ = await svc.fetch_market_data(r3)
        assert len(svc._cache) == 2
        k1 = svc._make_cache_key(r1)
        assert k1 not in svc._cache

        # r2 and r3 should still be in cache
        k2 = svc._make_cache_key(r2)
        k3 = svc._make_cache_key(r3)
        assert k2 in svc._cache
        assert k3 in svc._cache

    asyncio.run(_test())


def test_fetch_with_quality_evaluation_and_report_persistence(
    tmp_path: Path,
) -> None:
    """Verify quality gate sets anomaly bitmasks and persists quality reports."""

    async def _test() -> None:
        db_file = tmp_path / "test_quality_gate.db"
        db = DatabaseServiceImpl(DatabaseConfig(database_path=db_file))
        persist = DataPersistenceServiceImpl(
            db, DataPersistenceConfig(preseed_defaults=True)
        )
        await persist.initialize_schema()
        ds_svc = DatasetServiceImpl(
            persist, DatasetConfig(storage_dir=tmp_path / "datasets")
        )
        quality_svc = QualityServiceImpl()
        connector = MockFeedConnector("test_provider")
        svc = MarketDataServiceImpl(
            dataset_service=ds_svc,
            persistence=persist,
            quality_service=quality_svc,
            connectors={"test_provider": connector},
            config=MarketDataConfig(enable_caching=False),
        )

        req = build_market_data_request(
            source_id="test_provider",
            symbol="EURUSD",
            data_kind="bars",
            timeframe="M1",
            start=datetime(2026, 6, 1, 10, 0, tzinfo=UTC),
            end=datetime(2026, 6, 1, 11, 0, tzinfo=UTC),
            store_data=True,
        )

        bars = await svc.fetch_market_data(req)
        assert len(bars) == 1

        manifests = await ds_svc.list_manifests(symbol="EURUSD", timeframe="M1")
        assert len(manifests) == 1
        m = manifests[0]
        assert m.quality_score > 0.0

        # QualityReport should be persisted in database
        report = await persist.get_quality_report(f"qr_{m.dataset_id}")
        assert report is not None
        assert report.dataset_id == m.dataset_id
        assert report.total_records == 1

    asyncio.run(_test())


def test_fetch_ticks_from_connector_with_quality_and_persistence(
    tmp_path: Path,
) -> None:
    """Verify fetching ticks via connector with deduplication and quality scoring."""

    async def _test() -> None:
        db_file = tmp_path / "test_ticks_md.db"
        db = DatabaseServiceImpl(DatabaseConfig(database_path=db_file))
        persist = DataPersistenceServiceImpl(
            db, DataPersistenceConfig(preseed_defaults=True)
        )
        await persist.initialize_schema()
        ds_svc = DatasetServiceImpl(
            persist, DatasetConfig(storage_dir=tmp_path / "datasets")
        )
        quality_svc = QualityServiceImpl()
        connector = MockFeedConnector("tick_provider", with_ticks=True)
        svc = MarketDataServiceImpl(
            dataset_service=ds_svc,
            persistence=persist,
            quality_service=quality_svc,
            connectors={"tick_provider": connector},
            config=MarketDataConfig(enable_caching=True),
        )

        req = build_market_data_request(
            source_id="tick_provider",
            symbol="EURUSD",
            data_kind="ticks",
            start=datetime(2026, 6, 1, 10, 0, tzinfo=UTC),
            end=datetime(2026, 6, 1, 11, 0, tzinfo=UTC),
            store_data=True,
        )

        ticks = await svc.fetch_market_data(req)
        assert len(ticks) == 1  # Deduplicated from 2
        t0 = ticks[0]
        assert isinstance(t0, TickRecord)
        assert t0.bid == 1.0500

        # Verify caching returns same object
        ticks_cached = await svc.fetch_market_data(req)
        assert ticks_cached is ticks

        manifests = await ds_svc.list_manifests(symbol="EURUSD")
        assert len(manifests) == 1
        assert manifests[0].data_kind == "ticks"
        assert manifests[0].quality_score > 0.0

        qr = await persist.get_quality_report(f"qr_{manifests[0].dataset_id}")
        assert qr is not None
        assert qr.total_records == 1

    asyncio.run(_test())


def test_search_manifests_fallback_and_dataset_lookup(tmp_path: Path) -> None:
    """Verify dataset manifest search fallback and direct dataset ID fetch."""

    async def _test() -> None:
        db_file = tmp_path / "test_fallback.db"
        db = DatabaseServiceImpl(DatabaseConfig(database_path=db_file))
        persist = DataPersistenceServiceImpl(
            db, DataPersistenceConfig(preseed_defaults=True)
        )
        await persist.initialize_schema()
        ds_svc = DatasetServiceImpl(
            persist, DatasetConfig(storage_dir=tmp_path / "datasets")
        )
        svc = MarketDataServiceImpl(
            dataset_service=ds_svc,
            connectors={},
            config=MarketDataConfig(enable_caching=False),
        )

        # Pre-seed a dataset directly
        bars = [
            BarRecord(
                timestamp=datetime(2026, 6, 1, 10, 0, tzinfo=UTC),
                open=1.1000,
                high=1.1050,
                low=1.0950,
                close=1.1020,
                volume=100.0,
            ),
        ]
        manifest = await ds_svc.persist_bars(
            symbol="EURUSD",
            timeframe="M1",
            source_id="historical_archive",
            bars=bars,
        )

        # 1. Fetch via dataset ID lookup
        req_ds = build_market_data_request(
            source_id=manifest.dataset_id,
            symbol="EURUSD",
            timeframe="M1",
            start=datetime(2026, 6, 1, 9, 0, tzinfo=UTC),
            end=datetime(2026, 6, 1, 12, 0, tzinfo=UTC),
        )
        res_ds = await svc.fetch_market_data(req_ds)
        assert len(res_ds) == 1

        # 2. Fetch via fallback search (unknown source_id)
        req_fallback = build_market_data_request(
            source_id="unknown_exchange",
            symbol="EURUSD",
            timeframe="M1",
            start=datetime(2026, 6, 1, 10, 0, tzinfo=UTC),
            end=datetime(2026, 6, 1, 10, 0, tzinfo=UTC),
        )
        res_fb = await svc.fetch_market_data(req_fallback)
        assert len(res_fb) == 1

        # 3. Fallback search when none match
        req_none = build_market_data_request(
            source_id="unknown_exchange",
            symbol="NONEXISTENT",
            timeframe="M1",
        )
        res_none = await svc.fetch_market_data(req_none)
        assert len(res_none) == 0

    asyncio.run(_test())


def test_connector_sync_error_handling(tmp_path: Path) -> None:
    """Verify sync_connectors records errors without terminating sync."""

    async def _test() -> None:
        db_file = tmp_path / "test_sync_err.db"
        db = DatabaseServiceImpl(DatabaseConfig(database_path=db_file))
        persist = DataPersistenceServiceImpl(
            db, DataPersistenceConfig(preseed_defaults=True)
        )
        await persist.initialize_schema()
        ds_svc = DatasetServiceImpl(
            persist, DatasetConfig(storage_dir=tmp_path / "datasets")
        )
        failing_connector = MockFeedConnector("failing_provider", fail=True)
        working_connector = MockFeedConnector("working_provider", fail=False)

        svc = MarketDataServiceImpl(
            dataset_service=ds_svc,
            connectors={
                "failing_provider": failing_connector,
                "working_provider": working_connector,
            },
        )

        report = await svc.sync_connectors()
        assert len(report.errors) == 1
        assert "failing_provider" in report.errors[0]
        assert "working_provider" in report.providers_synced

    asyncio.run(_test())


def test_market_data_feature_spec_and_instance() -> None:
    """Verify MarketDataFeature spec and factory function."""
    feat = feature()
    assert isinstance(feat, MarketDataFeature)
    assert feat.spec.name == "data.market_data"
