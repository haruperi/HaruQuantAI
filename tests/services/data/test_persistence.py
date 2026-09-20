"""Tests for FEAT-PERSISTENCE-DATA (app/services/persistence/data.py)."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path

import pytest
from app.contracts.data import (
    BasketConstituent,
    BrokerAlias,
    DatasetImmutableError,
    DatasetManifest,
    InstrumentDefinition,
    QualityAnomaly,
    QualityAnomalyType,
    QualityReport,
    SessionDefinition,
    SessionWindow,
    UniverseBasket,
)
from app.services.persistence.data import (
    DataPersistenceConfig,
    DataPersistenceServiceImpl,
)
from app.services.persistence.database import (
    DatabaseConfig,
    DatabaseServiceImpl,
)


def _setup_persistence(tmp_path: Path) -> DataPersistenceServiceImpl:
    db_file = tmp_path / "test_data_persist.db"
    db = DatabaseServiceImpl(DatabaseConfig(database_path=db_file))
    return DataPersistenceServiceImpl(db, DataPersistenceConfig(preseed_defaults=True))


def test_schema_init_and_preseed(tmp_path: Path) -> None:
    """Verify pre-seeding of standard instruments and sessions."""

    async def _test() -> None:
        service = _setup_persistence(tmp_path)
        await service.initialize_schema()

        eurusd = await service.get_instrument("EURUSD")
        assert eurusd is not None
        assert eurusd.symbol == "EURUSD"
        assert eurusd.decimals == 5
        assert eurusd.data_type == "Forex"

        session = await service.get_session("24/5 Forex")
        assert session is not None
        assert session.is_default is True
        assert len(session.windows) == 5

    asyncio.run(_test())


def test_instrument_crud_and_aliases(tmp_path: Path) -> None:
    """Verify instrument lifecycle and broker alias mappings."""

    async def _test() -> None:
        service = _setup_persistence(tmp_path)
        await service.initialize_schema()

        inst = InstrumentDefinition(
            symbol="ETHUSD",
            description="Ethereum / USD",
            tick_size=0.01,
            tick_step=0.01,
            tick_value_in_money=1.0,
            point_value=1.0,
            decimals=2,
            default_spread=0.5,
            data_type="Crypto",
        )
        saved = await service.save_instrument(inst)
        assert saved.symbol == "ETHUSD"

        # Alias mapping
        alias = BrokerAlias(
            canonical_symbol="ETHUSD",
            alias_symbol="ETH/USD",
            broker_id=2,
            notes="RoboForex Crypto",
        )
        await service.save_alias(alias)

        resolved = await service.get_alias("ETH/USD", broker_id=2)
        assert resolved == "ETHUSD"

        # List aliases
        aliases = await service.list_aliases(symbol="ETHUSD")
        assert len(aliases) == 1
        assert aliases[0].alias_symbol == "ETH/USD"

        # Delete instrument
        deleted = await service.delete_instrument("ETHUSD")
        assert deleted is True
        assert await service.get_instrument("ETHUSD") is None

    asyncio.run(_test())


def test_session_lifecycle(tmp_path: Path) -> None:
    """Verify session profile persistence."""

    async def _test() -> None:
        service = _setup_persistence(tmp_path)
        await service.initialize_schema()

        tokyo = SessionDefinition(
            name="Tokyo Equities",
            description="TSE Regular Trading Hours",
            timezone="Asia/Tokyo",
            windows=[
                SessionWindow(
                    day_of_week=0, open_time="09:00:00", close_time="15:00:00"
                )
            ],
            holidays=["2026-01-01"],
            is_default=False,
        )
        saved = await service.save_session(tokyo)
        assert saved.name == "Tokyo Equities"
        assert saved.timezone == "Asia/Tokyo"
        assert len(saved.windows) == 1
        assert saved.holidays == ["2026-01-01"]

        fetched = await service.get_session("Tokyo Equities")
        assert fetched is not None
        assert fetched.description == "TSE Regular Trading Hours"

    asyncio.run(_test())


def test_dataset_manifest_immutability(tmp_path: Path) -> None:
    """Verify dataset manifest persistence and hash-protection."""

    async def _test() -> None:
        service = _setup_persistence(tmp_path)
        await service.initialize_schema()

        now = datetime.now(UTC)
        manifest = DatasetManifest(
            dataset_id="ds_eurusd_m1_test",
            symbol="EURUSD",
            timeframe="M1",
            data_kind="bars",
            source_id="test",
            start_time=now,
            end_time=now,
            row_count=100,
            parquet_path="/tmp/test.parquet",
            sha256_hash="hash_a",
        )
        await service.save_dataset_manifest(manifest)

        # Idempotent re-save of identical manifest succeeds
        saved_again = await service.save_dataset_manifest(manifest)
        assert saved_again.dataset_id == manifest.dataset_id

        # Attempt to overwrite with different hash
        manifest_corrupt = DatasetManifest(
            dataset_id="ds_eurusd_m1_test",
            symbol="EURUSD",
            timeframe="M1",
            data_kind="bars",
            source_id="test",
            start_time=now,
            end_time=now,
            row_count=100,
            parquet_path="/tmp/test.parquet",
            sha256_hash="hash_b_corrupted",
        )
        with pytest.raises(DatasetImmutableError):
            await service.save_dataset_manifest(manifest_corrupt)

        # Attempt to overwrite with different row_count
        manifest_diverged = DatasetManifest(
            dataset_id="ds_eurusd_m1_test",
            symbol="EURUSD",
            timeframe="M1",
            data_kind="bars",
            source_id="test",
            start_time=now,
            end_time=now,
            row_count=200,
            parquet_path="/tmp/test.parquet",
            sha256_hash="hash_a",
        )
        with pytest.raises(DatasetImmutableError):
            await service.save_dataset_manifest(manifest_diverged)

    asyncio.run(_test())


def test_orphan_cache_table_not_in_schema(tmp_path: Path) -> None:
    """Verify data_cache_entries table is not in the clean-room schema."""

    async def _test() -> None:
        service = _setup_persistence(tmp_path)
        await service.initialize_schema()

        rows = service._db.execute_query(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='data_cache_entries';"
        )
        assert len(rows) == 0

    asyncio.run(_test())


def test_basket_and_constituents(tmp_path: Path) -> None:
    """Verify dynamic basket and constituent storage."""

    async def _test() -> None:
        service = _setup_persistence(tmp_path)
        await service.initialize_schema()

        basket = UniverseBasket(
            name="Major Forex",
            description="Top liquidity currency pairs",
            is_system=True,
            constituents=[
                BasketConstituent(symbol="EURUSD"),
                BasketConstituent(symbol="GBPUSD"),
            ],
        )
        saved = await service.save_basket(basket)
        assert saved.id > 0
        assert len(saved.constituents) == 2

        fetched = await service.get_basket("Major Forex")
        assert fetched is not None
        assert len(fetched.constituents) == 2

    asyncio.run(_test())


def test_quality_report_persistence(tmp_path: Path) -> None:
    """Verify quality report storage and serialization."""

    async def _test() -> None:
        service = _setup_persistence(tmp_path)
        await service.initialize_schema()

        report = QualityReport(
            report_id="qr_123",
            dataset_id="ds_eurusd_m1",
            quality_score=0.98,
            total_records=1000,
            anomalies=[
                QualityAnomaly(
                    anomaly_type=QualityAnomalyType.SPIKE,
                    timestamp=datetime.now(UTC),
                    description="Price spike detected",
                    severity="warning",
                    observed_value=1.055,
                )
            ],
            anomaly_counts={"SPIKE": 1},
        )
        await service.save_quality_report(report)

        fetched = await service.get_quality_report("qr_123")
        assert fetched is not None
        assert fetched.quality_score == 0.98
        assert len(fetched.anomalies) == 1
        assert fetched.anomalies[0].anomaly_type == QualityAnomalyType.SPIKE

    asyncio.run(_test())
