# ruff: noqa: N999
"""Consolidated offline usage example for the Data domain (D-DATA).

Demonstrates deterministic, secret-safe, and offline execution of all 8
data domain features plus domain persistence (9 total):
1. Data Metadata Persistence & SQX System Seeding (FEAT-PERSISTENCE-DATA)
2. Instrument Specifications, Constraints & Aliasing (FEAT-DATA-INSTRUMENTS)
3. Trading Sessions, Schedules & Timezones (FEAT-DATA-SESSIONS)
4. Tabular Ingestion & Multi-Format Egress (FEAT-DATA-IMPORTS-EXPORTS)
5. Immutable Datasets & Parquet Manifest Storage (FEAT-DATA-DATASETS)
6. Time-Series Quality Anomaly Detection & Repair (FEAT-DATA-QUALITY)
7. Session-Aware Resampling, 4-Price Ticks & Cloning (FEAT-DATA-RESAMPLING)
8. Dynamic Asset Baskets & Point-in-Time Universes (FEAT-DATA-UNIVERSES)
9. Governed Market Data Retrieval & Synchronization (FEAT-DATA-MARKET_DATA)

Run with:
    `uv run python -m tests.examples.04_data`
"""

from __future__ import annotations

import asyncio
import sys
import tempfile
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

# Ensure project root is on sys.path for direct script execution
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.contracts.brokers import (
    BROKER_DUKASCOPY,
    ConnectionHealth,
    ConnectionState,
)
from app.contracts.data import (
    DATA_DATASETS,
    DATA_IMPORTS_EXPORTS,
    DATA_INSTRUMENTS,
    DATA_MARKET_DATA,
    DATA_PERSISTENCE,
    DATA_QUALITY,
    DATA_RESAMPLING,
    DATA_SESSIONS,
    DATA_SYNC,
    DATA_UNIVERSES,
    BarRecord,
    BasketConstituent,
    RepairPolicy,
    UniverseBasket,
    build_market_data_request,
)
from app.kernel.bootstrapper import Runtime
from app.kernel.context import FeatureContext
from app.kernel.feature import FeatureSpec
from app.services.data.datasets import (
    DatasetConfig,
    DatasetFeature,
)
from app.services.data.imports_exports import (
    ImportExportConfig,
    ImportExportFeature,
)
from app.services.data.instruments import (
    InstrumentCatalogConfig,
    InstrumentCatalogFeature,
)
from app.services.data.market_data import (
    MarketDataConfig,
    MarketDataFeature,
)
from app.services.data.quality import (
    QualityConfig,
    QualityFeature,
)
from app.services.data.resampling import (
    ResamplingConfig,
    ResamplingFeature,
)
from app.services.data.sessions import (
    SessionConfig,
    SessionFeature,
)
from app.services.data.universes import (
    UniverseConfig,
    UniverseFeature,
)
from app.services.persistence.data import (
    DataPersistenceConfig,
    DataPersistenceFeature,
)
from app.services.persistence.database import (
    DatabaseConfig,
    DatabaseFeature,
)


async def example_04_persistence(runtime: Runtime) -> None:
    """Demonstrate database persistence and default profile pre-seeding."""
    persist = runtime.require(DATA_PERSISTENCE)
    eurusd = await persist.get_instrument("EURUSD")
    assert eurusd is not None
    print(
        f"\n[1/9] Data Persistence pre-seeded instrument: {eurusd.symbol} "
        f"({eurusd.description}), decimals={eurusd.decimals}"
    )

    session = await persist.get_session("24/5 Forex")
    assert session is not None
    print(
        f"      Pre-seeded default session: {session.name} "
        f"({len(session.windows)} windows, tz={session.timezone})"
    )


async def example_04_instruments(runtime: Runtime) -> None:
    """Demonstrate instrument constraint checking and broker alias resolution."""
    cat = runtime.require(DATA_INSTRUMENTS)
    # Register an alias
    await cat.add_alias("EURUSD", "EUR/USD_MT5", broker_id=1, notes="Demo MT5")

    resolved = await cat.resolve_alias("EUR/USD_MT5", broker_id=1)
    inst = await cat.get_instrument("EUR/USD_MT5")
    assert inst is not None
    print(
        f"\n[2/9] Instrument Catalog resolved alias: 'EUR/USD_MT5' -> {resolved} "
        f"(tick_size={inst.tick_size}, point_value={inst.point_value})"
    )


async def example_04_sessions(runtime: Runtime) -> None:
    """Demonstrate trading sessions, window checks, and timezone conversion."""
    sessions = runtime.require(DATA_SESSIONS)
    default_sess = await sessions.get_default_session()

    # Monday 10:00 UTC
    dt = datetime(2026, 6, 1, 10, 0, 0, tzinfo=UTC)
    in_session = sessions.is_in_session(dt, default_sess)

    # Convert to Tokyo time
    tokyo_dt = sessions.convert_timezone(dt, "UTC", "Asia/Tokyo")
    print(
        f"\n[3/9] Sessions & Timezones: {dt.isoformat()} in '{default_sess.name}': "
        f"{in_session}, Tokyo time: {tokyo_dt.strftime('%Y-%m-%d %H:%M:%S')}"
    )


async def example_04_datasets(runtime: Runtime) -> str:
    """Demonstrate persisting immutable bars to Parquet with SHA-256 manifest."""
    ds = runtime.require(DATA_DATASETS)
    base_time = datetime(2026, 6, 1, 10, 0, 0, tzinfo=UTC)

    bars = [
        BarRecord(
            timestamp=base_time + timedelta(minutes=i),
            open=1.0500 + i * 0.0001,
            high=1.0508 + i * 0.0001,
            low=1.0495 + i * 0.0001,
            close=1.0503 + i * 0.0001,
            volume=100.0 + i,
            source="demo_stream",
        )
        for i in range(15)
    ]

    manifest = await ds.persist_bars(
        symbol="EURUSD",
        timeframe="M1",
        source_id="demo",
        bars=bars,
        lineage={"engine": "HaruQuantAI_Demo"},
    )
    print(
        f"\n[4/9] Datasets: Published immutable version {manifest.dataset_id} "
        f"({manifest.row_count} bars, sha256={manifest.sha256_hash[:12]}...)"
    )
    return manifest.dataset_id


async def example_04_imports_exports(runtime: Runtime, tmp_dir: Path) -> None:
    """Demonstrate tabular CSV ingestion and dataset export."""
    impexp = runtime.require(DATA_IMPORTS_EXPORTS)

    sample_csv = tmp_dir / "sample_m1.csv"
    sample_csv.write_text(
        "Date;Time;Open;High;Low;Close;Volume\n"
        "2026.06.01;11:00:00;1.0520;1.0530;1.0510;1.0525;120\n"
        "2026.06.01;11:01:00;1.0525;1.0535;1.0520;1.0530;180\n",
        encoding="utf-8",
    )

    # Auto-sniffing delimiter and format without explicit format_spec
    import_res = await impexp.import_tabular_file(
        str(sample_csv), symbol="EURUSD", timeframe="M1", format_spec=None
    )
    print(
        f"\n[5/9] Imports/Exports: Auto-sniffed & imported {import_res.records_imported} bars "
        f"from semicolon CSV into {import_res.dataset_id}"
    )

    # 1. Export to CSV
    export_out = tmp_dir / "exported_eurusd.csv"
    export_res = await impexp.export_dataset(
        import_res.dataset_id, str(export_out), format_name="csv"
    )
    print(
        f"      Exported {export_res.records_exported} bars to "
        f"{Path(export_res.destination_path).name} ({export_res.bytes_written} bytes)"
    )

    # 2. Export to MetaTrader 4 HST
    mt4_out = tmp_dir / "EURUSD1.hst"
    mt4_res = await impexp.export_dataset(
        import_res.dataset_id, str(mt4_out), format_name="mt4_hst"
    )
    print(
        f"      Exported to MetaTrader 4 HST: {Path(mt4_res.destination_path).name} "
        f"({mt4_res.bytes_written} bytes)"
    )

    # 3. Export to MetaTrader 5 Binary
    mt5_out = tmp_dir / "EURUSD_M1.mt5b"
    mt5_res = await impexp.export_dataset(
        import_res.dataset_id, str(mt5_out), format_name="mt5"
    )
    print(
        f"      Exported to MetaTrader 5 Binary: {Path(mt5_res.destination_path).name} "
        f"({mt5_res.bytes_written} bytes)"
    )


async def example_04_quality(runtime: Runtime) -> None:
    """Demonstrate quality anomaly detection and repair ledger."""
    quality = runtime.require(DATA_QUALITY)
    base_time = datetime(2026, 6, 1, 10, 0, 0, tzinfo=UTC)

    raw_bars = [
        BarRecord(timestamp=base_time, open=1.05, high=1.06, low=1.04, close=1.05),
        # Duplicate timestamp
        BarRecord(timestamp=base_time, open=1.05, high=1.06, low=1.04, close=1.05),
        # Crossed bar (Low > High)
        BarRecord(
            timestamp=base_time + timedelta(minutes=1),
            open=1.05,
            high=1.03,
            low=1.07,
            close=1.05,
        ),
    ]

    report = quality.evaluate_quality(raw_bars, timeframe="M1")
    print(
        f"\n[6/9] Quality Service: Scanned 3 bars -> quality_score={report.quality_score:.2f}, "
        f"anomalies detected={len(report.anomalies)}"
    )

    repaired, audit = quality.repair_data(
        raw_bars, RepairPolicy(drop_invalid_ohlc=True)
    )
    print(
        f"      Repaired dataset: {audit.repaired_count}/{audit.original_count} bars retained, "
        f"modifications applied={audit.modifications_count}"
    )


async def example_04_resampling(runtime: Runtime) -> None:
    """Demonstrate session-aware bar aggregation and 4-price ticks."""
    resampling = runtime.require(DATA_RESAMPLING)
    base_time = datetime(2026, 6, 1, 10, 0, 0, tzinfo=UTC)

    bars = [
        BarRecord(
            timestamp=base_time + timedelta(minutes=i),
            open=1.0500 + i * 0.0001,
            high=1.0505 + i * 0.0001,
            low=1.0495 + i * 0.0001,
            close=1.0502 + i * 0.0001,
            volume=10.0,
        )
        for i in range(10)
    ]

    m5_bars = resampling.resample_bars(bars, target_timeframe="M5")
    assert len(m5_bars) == 2
    print(
        f"\n[7/9] Resampling: Aggregated 10 M1 bars into {len(m5_bars)} M5 bars "
        f"(total volume={sum(b.volume for b in m5_bars)})"
    )

    ticks = resampling.generate_4price_ticks(m5_bars[0])
    print(
        f"      Generated 4-price ticks for M5 bar: Open={ticks[0].bid}, Low={ticks[1].bid}, "
        f"High={ticks[2].bid}, Close={ticks[3].bid}"
    )


async def example_04_universes(runtime: Runtime) -> None:
    """Demonstrate point-in-time constituent tracking eliminating survivorship bias."""
    univ = runtime.require(DATA_UNIVERSES)

    basket = UniverseBasket(
        name="Crypto_Majors",
        description="Major cryptocurrencies with historical rotation",
        is_system=False,
        constituents=[
            BasketConstituent(symbol="BTCUSD"),
            BasketConstituent(symbol="ETHUSD"),
            BasketConstituent(
                symbol="SOLUSD",
                date_from=datetime(2021, 1, 1, tzinfo=UTC),
            ),
        ],
    )
    saved = await univ.save_basket(basket)

    # In 2020: SOL was not yet a member
    const_2020 = await univ.get_point_in_time_constituents(
        saved.id, as_of=datetime(2020, 6, 1, tzinfo=UTC)
    )
    # In 2022: SOL is active
    const_2022 = await univ.get_point_in_time_constituents(
        saved.id, as_of=datetime(2022, 6, 1, tzinfo=UTC)
    )
    print(
        f"\n[8/9] Universes & Baskets: Point-in-time constituents for '{saved.name}':\n"
        f"      As of 2020: {const_2020} (Survivorship-bias protected)\n"
        f"      As of 2022: {const_2022}"
    )


class DemoDukascopyConnector:
    """Mock Dukascopy feed connector for realistic offline sync demonstration."""

    def __init__(self) -> None:
        self.provider_name = "dukascopy"

    async def connect(self, config: Any) -> None:
        pass

    async def disconnect(self) -> None:
        pass

    def is_connected(self) -> bool:
        return True

    async def get_health(self) -> ConnectionHealth:
        return ConnectionHealth(provider="dukascopy", state=ConnectionState.READY)

    async def stream_historical_bars(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime,
    ) -> AsyncIterator[BarRecord]:
        for i in range(5):
            yield BarRecord(
                timestamp=start_time + timedelta(minutes=i),
                open=1.0500 + i * 0.0001,
                high=1.0505 + i * 0.0001,
                low=1.0495 + i * 0.0001,
                close=1.0502 + i * 0.0001,
                volume=10.0,
            )


class DemoFeedFeature:
    """Register demo feed connector under BROKER_DUKASCOPY."""

    spec = FeatureSpec(
        name="demo.feed",
        provides=frozenset({BROKER_DUKASCOPY}),
    )

    async def start(self, context: FeatureContext) -> None:
        context.provide(BROKER_DUKASCOPY, DemoDukascopyConnector())


async def example_04_market_data(runtime: Runtime, dataset_id: str) -> None:
    """Demonstrate governed market data retrieval with transparent caching."""
    client = runtime.require(DATA_MARKET_DATA)
    sync_svc = runtime.require(DATA_SYNC)

    req = build_market_data_request(
        source_id=dataset_id,
        symbol="EURUSD",
        data_kind="bars",
        timeframe="M1",
        start=datetime(2026, 6, 1, 10, 0, 0, tzinfo=UTC),
        end=datetime(2026, 6, 1, 10, 5, 0, tzinfo=UTC),
    )

    bars = await client.fetch_market_data(req)
    print(
        f"\n[9/9] Market Data Client fetched {len(bars)} bars via request specification"
    )

    sync_report = await sync_svc.sync_connectors()
    print(
        f"      Connector synchronization verified: {len(sync_report.providers_synced)} "
        f"provider(s) synced ({sync_report.providers_synced}), "
        f"total_records={sync_report.total_records}"
    )


async def run_data_demonstration() -> None:
    """Execute end-to-end demonstration of all 9 Data domain capabilities."""
    with tempfile.TemporaryDirectory() as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)
        db_path = tmp_dir / "data_demo.db"
        storage_path = tmp_dir / "datasets"

        features = (
            lambda: DatabaseFeature(DatabaseConfig(database_path=db_path)),
            lambda: DataPersistenceFeature(
                DataPersistenceConfig(preseed_defaults=True)
            ),
            lambda: InstrumentCatalogFeature(InstrumentCatalogConfig()),
            lambda: SessionFeature(SessionConfig()),
            lambda: DatasetFeature(DatasetConfig(storage_dir=storage_path)),
            lambda: QualityFeature(QualityConfig()),
            lambda: ImportExportFeature(ImportExportConfig()),
            lambda: ResamplingFeature(ResamplingConfig()),
            lambda: UniverseFeature(UniverseConfig()),
            DemoFeedFeature,
            lambda: MarketDataFeature(MarketDataConfig()),
        )

        async with Runtime(features) as runtime:
            print("=" * 80)
            print("HARUQUANTAI DATA DOMAIN (D-DATA) OFFLINE DEMONSTRATION")
            print("=" * 80)

            await example_04_persistence(runtime)
            await example_04_instruments(runtime)
            await example_04_sessions(runtime)
            dataset_id = await example_04_datasets(runtime)
            await example_04_imports_exports(runtime, tmp_dir)
            await example_04_quality(runtime)
            await example_04_resampling(runtime)
            await example_04_universes(runtime)
            await example_04_market_data(runtime, dataset_id)

            print("\n" + "=" * 80)
            print("ALL 9 DATA DOMAIN CAPABILITIES VERIFIED SUCCESSFULLY OFFLINE")
            print("=" * 80)


def main() -> None:
    """Run offline demonstration."""
    asyncio.run(run_data_demonstration())


if __name__ == "__main__":
    main()
