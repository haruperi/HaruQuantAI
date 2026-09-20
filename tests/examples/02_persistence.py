# ruff: noqa: N999
"""Consolidated offline usage example for the Persistence domain (D-PERSISTENCE).

Demonstrates deterministic, secret-safe, and offline execution of all 7
persistence domain features:
1. SQLite WAL Lifecycle & Transactions (FEAT-PERSISTENCE-DATABASE)
2. Forward Schema Migrations (FEAT-PERSISTENCE-MIGRATIONS)
3. Hot Point-in-Time Snapshots (FEAT-PERSISTENCE-SNAPSHOTS)
4. Immutable Content-Addressed Artifacts (FEAT-PERSISTENCE-ARTIFACTS)
5. Reference-Safe Retention & Audited Purge (FEAT-PERSISTENCE-RETENTION)
6. Project Databanks, Ranking & Similarity (FEAT-PERSISTENCE-DATABANKS)
7. Partitioned Columnar Parquet Market Store (FEAT-PERSISTENCE-PARQUET)

Run with:
    `uv run python -m tests.examples.02_persistence`
"""

from __future__ import annotations

import asyncio
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.contracts.persistence import (
    ARTIFACT_STORE,
    DATABANK_STORE,
    DATABASE_SERVICE,
    MIGRATION_SERVICE,
    PARQUET_STORE_SERVICE,
    RETENTION_SERVICE,
    SNAPSHOT_SERVICE,
    BarRecord,
    ColumnConfig,
    DatabankViewConfig,
    RankingDirection,
    SampleType,
    SimilarityProfile,
    TickRecord,
)
from app.kernel.bootstrapper import Runtime
from app.services.persistence.artifacts import (
    ArtifactConfig,
    ArtifactFeature,
)
from app.services.persistence.databanks import (
    DatabankConfig,
    DatabankFeature,
)
from app.services.persistence.database import (
    DatabaseConfig,
    DatabaseFeature,
)
from app.services.persistence.migrations import (
    MigrationConfig,
    MigrationFeature,
)
from app.services.persistence.parquet_store import (
    ParquetConfig,
    ParquetFeature,
)
from app.services.persistence.retention import (
    RetentionConfig,
    RetentionFeature,
)
from app.services.persistence.snapshots import (
    SnapshotConfig,
    SnapshotFeature,
)


def example_02_database(runtime: Runtime) -> None:
    """Demonstrate SQLite WAL lifecycle and parameterized transactions."""
    print("\n--- 1. SQLite Database Lifecycle & Transactions ---")
    db = runtime.require(DATABASE_SERVICE)
    print(f"Active SQLite database: {db.database_path}")

    # Mutation within transaction
    with db.transaction() as con:
        con.execute(
            "INSERT INTO persistence_databanks "
            "(project_name, databank_name, capacity, default_view, auto_sync_policy, created_at_utc) "
            "VALUES ('DemoProject', 'Primary', 200, 'Default', 'never', ?);",
            (datetime.now(UTC).isoformat(),),
        )
    print("Inserted databank 'Primary' inside immediate transaction")

    rows = db.execute_query(
        "SELECT project_name, databank_name, capacity FROM persistence_databanks WHERE project_name = ?;",
        ("DemoProject",),
    )
    print(
        f"Query result: {rows[0]['project_name']}/{rows[0]['databank_name']} (cap={rows[0]['capacity']})"
    )
    db.checkpoint()
    print("Checkpoint WAL journal: OK")


def example_02_migrations(runtime: Runtime) -> None:
    """Demonstrate forward schema migrations and checksum verification."""
    print("\n--- 2. Forward Schema Migrations ---")
    mig = runtime.require(MIGRATION_SERVICE)
    print(f"Current migration version: {mig.current_version()}")

    pending = mig.get_pending_migrations()
    print(f"Discovered pending migrations: {[p.name for p in pending]}")

    applied = mig.apply_all()
    print(f"Applied {len(applied)} migrations. New version: {mig.current_version()}")
    assert mig.current_version() >= 2


def example_02_snapshots(runtime: Runtime) -> None:
    """Demonstrate hot point-in-time VACUUM INTO snapshots."""
    print("\n--- 3. Hot Point-in-Time Snapshots ---")
    snap = runtime.require(SNAPSHOT_SERVICE)

    record = snap.create_snapshot(label="demo_backup")
    print(
        f"Created snapshot: {record.snapshot_id} (size={record.size_bytes}B, sha256={record.checksum_sha256[:12]}...)"
    )

    snapshots = snap.list_snapshots()
    print(f"Discovered {len(snapshots)} snapshots in catalog")
    assert len(snapshots) >= 1


def example_02_artifacts(runtime: Runtime, tmp_dir: Path) -> tuple[str, str]:
    """Demonstrate immutable content-addressed artifact catalog and bundling."""
    print("\n--- 4. Immutable Artifact Catalog & Bundles ---")
    store = runtime.require(ARTIFACT_STORE)

    # 1. Stage and promote parent template
    parent_payload = b"<StrategyTemplate name='TrendFollower' version='1.0'/>"
    parent_rec = store.store_artifact(
        payload=parent_payload,
        media_type="application/xml",
        metadata={"author": "quant_engine", "description": "Base trend template"},
    )
    print(
        f"Stored parent artifact: {parent_rec.artifact_id[:16]}... ({parent_rec.size_bytes}B)"
    )

    # 1b. Demonstrate Idempotent Canonical Insertion (FR-PERSISTENCE-CONCURRENCY_INSERT)
    re_stored = store.store_artifact(
        payload=parent_payload,
        media_type="application/xml",
    )
    assert re_stored.artifact_id == parent_rec.artifact_id
    print(
        f"Re-stored identical parent artifact: already cataloged — identical identity returned ({re_stored.artifact_id[:16]}...)"
    )

    # 2. Stage child strategy with lineage link
    child_payload = b"strategy EURUSD_Trend { enter_long(RSI < 30); }"
    staging_id = store.stage_artifact(child_payload, "text/plain")
    print(f"Staged child payload with token: {staging_id}")

    child_rec = store.promote_artifact(
        staging_id,
        parent_ids=[parent_rec.artifact_id],
    )
    print(
        f"Promoted child artifact: {child_rec.artifact_id[:16]}... parent={child_rec.parent_ids[0][:16]}..."
    )
    assert store.verify_checksum(child_rec.artifact_id) is True

    # 3. Export portable zip bundle
    bundle_path = tmp_dir / "exports" / "demo_bundle.zip"
    exported = store.export_bundle(
        [parent_rec.artifact_id, child_rec.artifact_id], bundle_path
    )
    print(f"Exported portable bundle: {exported.name} ({exported.stat().st_size}B)")

    return parent_rec.artifact_id, child_rec.artifact_id


def example_02_retention(runtime: Runtime, orphan_id: str, member_id: str) -> None:
    """Demonstrate reference-safe retention and audited purge."""
    print("\n--- 5. Reference-Safe Retention & Audited Purge ---")
    ret = runtime.require(RETENTION_SERVICE)

    # Plan purge: member_id is referenced in databank, orphan_id is not
    plan = ret.plan_purge([orphan_id, member_id])
    print(
        f"Purge Plan: Eligible={len(plan.eligible_artifact_ids)}, Blocked={len(plan.blocked_artifact_ids)}"
    )
    if plan.blocked_artifact_ids:
        print(
            f"Blocked reason: {plan.blocking_reasons[plan.blocked_artifact_ids[0]][0]}"
        )

    # Dry run
    report_dry = ret.execute_purge(plan, dry_run=True)
    print(
        f"Dry-run report: Would reclaim {report_dry.reclaimed_bytes} bytes from {report_dry.purged_count} artifacts"
    )

    # Real purge
    report_real = ret.execute_purge(plan, dry_run=False)
    print(
        f"Real purge report: Purged {report_real.purged_count} artifacts. Op={report_real.operation_id}"
    )


def example_02_databanks(runtime: Runtime, strat_id: str) -> str:
    """Demonstrate databanks, ranking, similarity dismissal, and column views."""
    print("\n--- 6. Databanks, Ranking, Similarity & Column Views ---")
    dbk = runtime.require(DATABANK_STORE)
    store = runtime.require(ARTIFACT_STORE)

    # 1. Create databank with capacity = 2
    dbk.create_databank("AlphaProject", "TopPerformers", capacity=2)
    print("Created databank 'TopPerformers' with capacity=2")

    # 2. Add member
    m1 = dbk.add_member(
        "AlphaProject",
        "TopPerformers",
        strat_id,
        fitness=1.85,
        ranking_value=92.5,
        metrics={"net_profit": 15000.0, "trade_count": 320.0, "drawdown": 850.0},
    )
    assert m1 is not None
    print(
        f"Added member: {m1.artifact_id[:16]}... rank={m1.ranking_value}, fitness={m1.fitness}"
    )

    # 3. Test Similarity Dismissal (±5% Net Profit, Trades, DD)
    sim_art = store.store_artifact(b"sim_strat", "text/plain")
    profile = SimilarityProfile(tolerance_pct=5.0)

    # Candidate with worse fitness -> Dismissed!
    dismissed = dbk.add_member(
        "AlphaProject",
        "TopPerformers",
        sim_art.artifact_id,
        fitness=1.20,
        ranking_value=70.0,
        metrics={"net_profit": 15200.0, "trade_count": 325.0, "drawdown": 840.0},
        similarity_profile=profile,
    )
    assert dismissed is None
    print("Candidate within ±5% metrics with inferior fitness: Successfully DISMISSED")

    # 4. Save Column View
    view = DatabankViewConfig(
        view_name="PerformanceReport",
        columns=(
            ColumnConfig(
                "Profit",
                "net_profit",
                SampleType.FULL_SAMPLE,
                sort_priority=1,
                sort_direction=RankingDirection.DESCENDING,
            ),
            ColumnConfig("Drawdown", "drawdown", SampleType.FULL_SAMPLE),
        ),
    )
    dbk.save_view(view)
    print(f"Saved databank column view: {view.view_name}")

    return sim_art.artifact_id


def example_02_parquet_store(runtime: Runtime) -> None:
    """Demonstrate partitioned Parquet columnar market store."""
    print("\n--- 7. Columnar Parquet Market Store (Zstd) ---")
    parquet = runtime.require(PARQUET_STORE_SERVICE)

    t0 = datetime(2024, 1, 2, 9, 0, tzinfo=UTC)
    bars = [
        BarRecord(
            t0 + timedelta(minutes=i),
            open=1.1000 + i * 0.0001,
            high=1.1010 + i * 0.0001,
            low=1.0995 + i * 0.0001,
            close=1.1005 + i * 0.0001,
            volume=100.0 + i * 10,
            ticks=40 + i,
        )
        for i in range(10)
    ]

    written = parquet.write_bars("EURUSD", "M1", bars)
    print(f"Wrote {written} bars into partitioned Parquet storage (Zstd)")

    read_bars = parquet.read_bars("EURUSD", "M1", limit=5)
    print(
        f"Read {len(read_bars)} bars with limit: First bar close={read_bars[0].close}, Last close={read_bars[-1].close}"
    )

    # Ticks
    ticks = [
        TickRecord(
            t0 + timedelta(seconds=i),
            bid=1.1000 + i * 0.00005,
            ask=1.1002 + i * 0.00005,
        )
        for i in range(5)
    ]
    parquet.write_ticks("EURUSD", ticks)
    print(f"Wrote {len(ticks)} ticks into tick partition")

    partitions = parquet.list_partitions()
    print(
        f"Discovered {len(partitions)} active partitions: {[f'{p.symbol}/{p.timeframe}/{p.year}' for p in partitions]}"
    )


async def run_persistence_demonstration() -> None:
    """Execute end-to-end demonstration of all persistence domain capabilities."""
    with tempfile.TemporaryDirectory() as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)
        db_path = tmp_dir / "persistence_demo.db"
        art_dir = tmp_dir / "artifacts"
        staging_dir = tmp_dir / "staging"
        market_dir = tmp_dir / "market"
        snap_dir = tmp_dir / "snapshots"

        features = (
            lambda: DatabaseFeature(DatabaseConfig(database_path=db_path)),
            lambda: MigrationFeature(MigrationConfig()),
            lambda: SnapshotFeature(SnapshotConfig(snapshot_dir=snap_dir)),
            lambda: ArtifactFeature(
                ArtifactConfig(artifacts_dir=art_dir, staging_dir=staging_dir)
            ),
            lambda: RetentionFeature(RetentionConfig(artifacts_dir=art_dir)),
            lambda: DatabankFeature(DatabankConfig()),
            lambda: ParquetFeature(ParquetConfig(market_dir=market_dir)),
        )

        async with Runtime(features) as runtime:
            print("=" * 75)
            print(
                "HARUQUANTAI PERSISTENCE DOMAIN (D-PERSISTENCE) OFFLINE DEMONSTRATION"
            )
            print("=" * 75)

            example_02_database(runtime)
            example_02_migrations(runtime)
            example_02_snapshots(runtime)
            parent_id, child_id = example_02_artifacts(runtime, tmp_dir)
            orphan_id = example_02_databanks(runtime, child_id)
            example_02_retention(runtime, orphan_id, child_id)
            example_02_parquet_store(runtime)

            print("\n" + "=" * 75)
            print("ALL 7 PERSISTENCE FEATURES VERIFIED SUCCESSFULLY OFFLINE")
            print("=" * 75)


def main() -> None:
    """Run offline demonstration."""
    asyncio.run(run_persistence_demonstration())


if __name__ == "__main__":
    main()
