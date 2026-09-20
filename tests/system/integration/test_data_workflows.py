"""End-to-end integration workflows tests for the Data domain."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from pathlib import Path

from app.contracts.brokers import (
    BrokerConnectionConfig,
    ConnectionHealth,
    ConnectionState,
    RawTransportChunk,
)
from app.contracts.data import (
    BasketConstituent,
    SessionDefinition,
    SessionWindow,
    TickRecord,
    UniverseBasket,
    build_market_data_request,
)
from app.services.data.datasets import (
    DatasetConfig,
    DatasetServiceImpl,
)
from app.services.data.imports_exports import (
    ImportExportConfig,
    ImportExportServiceImpl,
)
from app.services.data.market_data import (
    MarketDataConfig,
    MarketDataServiceImpl,
)
from app.services.data.quality import (
    QualityConfig,
    QualityServiceImpl,
)
from app.services.data.resampling import (
    ResamplingConfig,
    ResamplingServiceImpl,
)
from app.services.data.sessions import (
    SessionConfig,
    SessionServiceImpl,
)
from app.services.data.universes import (
    UniverseConfig,
    UniverseManagerServiceImpl,
)
from app.services.persistence.data import (
    DataPersistenceConfig,
    DataPersistenceServiceImpl,
)
from app.services.persistence.database import (
    DatabaseConfig,
    DatabaseServiceImpl,
)


class MockIntegrationConnector:
    """Connector providing streaming ticks for integration workflow test."""

    async def connect(self, config: BrokerConnectionConfig) -> None:
        pass

    async def disconnect(self) -> None:
        pass

    def is_connected(self) -> bool:
        return True

    async def get_health(self) -> ConnectionHealth:
        return ConnectionHealth(provider="dukascopy", state=ConnectionState.READY)

    async def stream_raw_data(
        self, symbol: str, start_utc: datetime, end_utc: datetime
    ) -> AsyncIterator[RawTransportChunk]:
        yield RawTransportChunk(
            provider="dukascopy",
            symbol=symbol,
            sequence_num=1,
            timestamp_utc=start_utc,
            payload_bytes=b"raw",
            metadata={
                "ticks": [
                    TickRecord(
                        timestamp=datetime(2026, 6, 1, 10, 0, 1, tzinfo=UTC),
                        bid=1.1200,
                        ask=1.1202,
                        sequence=1,
                        bid_volume=10.0,
                    ),
                    TickRecord(
                        timestamp=datetime(2026, 6, 1, 10, 0, 2, tzinfo=UTC),
                        bid=1.1201,
                        ask=1.1203,
                        sequence=2,
                        bid_volume=15.0,
                    ),
                ]
            },
        )


def test_full_tabular_ingestion_resampling_universe_and_export_workflow(
    tmp_path: Path,
) -> None:
    """Verify complete pipeline: CSV auto-sniff -> quality check -> dataset -> resample -> universe -> MT binary exports."""

    async def _workflow() -> None:
        # 1. Initialize persistence and services
        db_file = tmp_path / "integration.db"
        db = DatabaseServiceImpl(DatabaseConfig(database_path=db_file))
        persist = DataPersistenceServiceImpl(
            db, DataPersistenceConfig(preseed_defaults=True)
        )
        await persist.initialize_schema()

        ds_svc = DatasetServiceImpl(
            persist, DatasetConfig(storage_dir=tmp_path / "datasets")
        )
        quality_svc = QualityServiceImpl(config=QualityConfig())
        session_svc = SessionServiceImpl(persist, SessionConfig())
        universe_svc = UniverseManagerServiceImpl(persist, UniverseConfig())
        resample_svc = ResamplingServiceImpl(
            session_service=session_svc, config=ResamplingConfig()
        )
        impexp_svc = ImportExportServiceImpl(
            dataset_service=ds_svc,
            quality_service=quality_svc,
            session_service=session_svc,
            persistence=persist,
            config=ImportExportConfig(),
        )

        # 2. Write sample tabular bars CSV (semicolon delimited with header)
        csv_file = tmp_path / "EURUSD_bars.csv"
        csv_file.write_text(
            "Date;Time;Open;High;Low;Close;Volume\n"
            "2026.06.01;10:00:00;1.1000;1.1050;1.0990;1.1040;100\n"
            "2026.06.01;10:01:00;1.1040;1.1080;1.1020;1.1070;150\n"
            "2026.06.01;10:02:00;1.1070;1.1090;1.1050;1.1060;120\n"
            "2026.06.01;10:03:00;1.1060;1.1100;1.1040;1.1090;130\n"
            "2026.06.01;10:04:00;1.1090;1.1120;1.1070;1.1110;140\n",
            encoding="utf-8",
        )

        # 3. Ingest with auto-sniffing and quality gating
        import_res = await impexp_svc.import_tabular_file(
            file_path=str(csv_file),
            symbol="EURUSD",
            timeframe="M1",
            format_spec=None,
        )
        assert import_res.records_imported == 5
        assert import_res.error_count == 0
        dataset_id = import_res.dataset_id

        # Verify dataset manifest and deterministic ID
        manifest = await ds_svc.get_manifest(dataset_id)
        assert manifest is not None
        assert manifest.symbol == "EURUSD"
        assert manifest.timeframe == "M1"
        assert manifest.quality_score > 0.0

        # Verify quality report was persisted
        qr = await persist.get_quality_report(f"qr_{dataset_id}")
        assert qr is not None
        assert qr.total_records == 5

        # 4. Resample M1 bars to M5 bars
        m1_bars = await ds_svc.load_bars(dataset_id)
        m5_bars = resample_svc.resample_bars(
            bars=m1_bars,
            target_timeframe="M5",
        )
        assert len(m5_bars) == 1
        assert m5_bars[0].open == 1.1000
        assert m5_bars[0].close == 1.1110
        assert m5_bars[0].volume == 640.0

        # 5. Define Universe and create a basket containing EURUSD
        universe_svc = UniverseManagerServiceImpl(persist, UniverseConfig())
        basket = UniverseBasket(
            name="forex_majors",
            description="Forex Major Pairs",
            is_system=False,
            constituents=[
                BasketConstituent(symbol="EURUSD"),
                BasketConstituent(symbol="GBPUSD"),
            ],
        )
        saved_basket = await universe_svc.save_basket(basket)
        assert len(saved_basket.constituents) == 2
        retrieved = await universe_svc.get_basket("forex_majors")
        assert retrieved is not None
        assert any(c.symbol == "EURUSD" for c in retrieved.constituents)

        # 6. Export M1 dataset to MetaTrader 4 HST and MetaTrader 5 binary
        hst_dest = tmp_path / "exports" / "EURUSD1.hst"
        hst_res = await impexp_svc.export_dataset(
            dataset_id=dataset_id,
            destination_path=str(hst_dest),
            format_name="mt4_hst",
        )
        assert hst_res.records_exported == 5
        assert hst_dest.exists()

        mt5_dest = tmp_path / "exports" / "EURUSD_M1.mt5b"
        mt5_res = await impexp_svc.export_dataset(
            dataset_id=dataset_id,
            destination_path=str(mt5_dest),
            format_name="mt5",
        )
        assert mt5_res.records_exported == 5
        assert mt5_dest.exists()

    asyncio.run(_workflow())


def test_connector_stream_quality_session_and_fxt_export_workflow(
    tmp_path: Path,
) -> None:
    """Verify live connector streaming -> quality gate -> session validation -> FXT export workflow."""

    async def _workflow() -> None:
        db_file = tmp_path / "integration_stream.db"
        db = DatabaseServiceImpl(DatabaseConfig(database_path=db_file))
        persist = DataPersistenceServiceImpl(
            db, DataPersistenceConfig(preseed_defaults=True)
        )
        await persist.initialize_schema()

        ds_svc = DatasetServiceImpl(
            persist, DatasetConfig(storage_dir=tmp_path / "datasets")
        )
        quality_svc = QualityServiceImpl()
        session_svc = SessionServiceImpl(persist)
        connector = MockIntegrationConnector()

        md_svc = MarketDataServiceImpl(
            dataset_service=ds_svc,
            persistence=persist,
            quality_service=quality_svc,
            connectors={"dukascopy": connector},
            config=MarketDataConfig(enable_caching=True),
        )
        impexp_svc = ImportExportServiceImpl(
            dataset_service=ds_svc,
            quality_service=quality_svc,
            session_service=session_svc,
            persistence=persist,
        )

        # 1. Register a London session definition
        session_def = SessionDefinition(
            name="London Trading",
            timezone="UTC",
            windows=[
                SessionWindow(
                    day_of_week=0,
                    open_time="08:00:00",
                    close_time="16:30:00",
                )
            ],
        )
        await session_svc.save_session(session_def)
        retrieved_session = await session_svc.get_session("London Trading")
        assert retrieved_session is not None
        assert (
            session_svc.is_in_session(
                datetime(2026, 6, 1, 10, 0, tzinfo=UTC), retrieved_session
            )
            is True
        )

        # 2. Fetch ticks via MarketDataClient
        req = build_market_data_request(
            source_id="dukascopy",
            symbol="EURUSD",
            data_kind="ticks",
            start=datetime(2026, 6, 1, 10, 0, tzinfo=UTC),
            end=datetime(2026, 6, 1, 11, 0, tzinfo=UTC),
            store_data=True,
        )
        ticks = await md_svc.fetch_market_data(req)
        assert len(ticks) == 2

        # Verify dataset was created
        manifests = await ds_svc.list_manifests(symbol="EURUSD")
        assert len(manifests) == 1
        dataset_id = manifests[0].dataset_id

        # 3. Export to MT4 FXT format
        fxt_dest = tmp_path / "exports" / "EURUSD_ticks.fxt"
        fxt_res = await impexp_svc.export_dataset(
            dataset_id=dataset_id,
            destination_path=str(fxt_dest),
            format_name="mt4_fxt",
        )
        assert fxt_res.records_exported == 2
        assert fxt_dest.exists()

    asyncio.run(_workflow())
