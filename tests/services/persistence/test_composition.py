"""Composition and lifecycle tests for the Persistence domain (D-PERSISTENCE)."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from app.contracts.persistence import (
    ARTIFACT_STORE,
    DATABANK_STORE,
    DATABASE_SERVICE,
)
from app.contracts.workspace import WORKSPACE_PERSISTENCE
from app.kernel.bootstrapper import Runtime
from app.kernel.capability import Capability, CapabilityUnavailableError
from app.kernel.context import FeatureContext
from app.kernel.feature import Feature, FeatureSpec
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
from app.services.persistence.workspace import WorkspacePersistenceFeature


def test_required_capability_absence_blocks_startup(tmp_path: Path) -> None:
    """Test that starting a feature missing a required capability fails closed."""
    db_file = tmp_path / "absence.db"

    runtime = Runtime(
        [
            lambda: DatabaseFeature(DatabaseConfig(database_path=db_file)),
            lambda: DatabankFeature(DatabankConfig()),
        ]
    )

    async def _run() -> None:
        with pytest.raises(
            CapabilityUnavailableError,
            match=r"persistence\.databanks: persistence\.artifacts",
        ):
            async with runtime:
                pass

    asyncio.run(_run())


def test_partial_startup_failure_unwinds(tmp_path: Path) -> None:
    """Test that startup failure unwinds cleanly and revokes provided capabilities."""
    db_file = tmp_path / "unwind.db"
    dummy_cap: Capability[Any] = Capability(
        name="test.dummy", major=1, description="Dummy test capability"
    )

    class FailingFeature:
        @property
        def spec(self) -> FeatureSpec:
            return FeatureSpec(
                name="test.failing",
                provides=frozenset({dummy_cap}),
                requires=frozenset({DATABASE_SERVICE}),
                optional=frozenset(),
                description="Feature that fails during start.",
            )

        async def start(self, context: FeatureContext) -> None:
            context.provide(dummy_cap, object())
            msg = "Simulated startup failure in test feature"
            raise RuntimeError(msg)

    runtime = Runtime(
        [
            lambda: DatabaseFeature(DatabaseConfig(database_path=db_file)),
            FailingFeature,
        ]
    )

    async def _run() -> None:
        with pytest.raises(RuntimeError, match="Simulated startup failure"):
            async with runtime:
                pass

        with pytest.raises(CapabilityUnavailableError):
            runtime.require(DATABASE_SERVICE)

    asyncio.run(_run())


def test_physical_removal_preserves_retained_state(tmp_path: Path) -> None:
    """Test that stopping features preserves physical databases and artifacts on disk."""
    db_file = tmp_path / "preserved.db"
    art_dir = tmp_path / "artifacts"
    staging_dir = tmp_path / "staging"
    market_dir = tmp_path / "market"
    snap_dir = tmp_path / "snapshots"

    all_features: list[Callable[[], Feature]] = [
        lambda: DatabaseFeature(DatabaseConfig(database_path=db_file)),
        lambda: MigrationFeature(MigrationConfig()),
        lambda: SnapshotFeature(SnapshotConfig(snapshot_dir=snap_dir)),
        lambda: ArtifactFeature(
            ArtifactConfig(artifacts_dir=art_dir, staging_dir=staging_dir)
        ),
        lambda: RetentionFeature(RetentionConfig(artifacts_dir=art_dir)),
        lambda: DatabankFeature(DatabankConfig()),
        lambda: ParquetFeature(ParquetConfig(market_dir=market_dir)),
    ]

    saved_artifact_id = ""

    async def _write_initial() -> None:
        nonlocal saved_artifact_id
        async with Runtime(all_features) as rt:
            art = rt.require(ARTIFACT_STORE)
            dbk = rt.require(DATABANK_STORE)
            rec = art.store_artifact(b"preserved_content_payload", "text/plain")
            saved_artifact_id = rec.artifact_id
            dbk.create_databank("ProjectP", "MainBank")
            dbk.add_member(
                "ProjectP",
                "MainBank",
                rec.artifact_id,
                fitness=1.0,
                ranking_value=1.0,
                metrics={},
            )

    asyncio.run(_write_initial())

    payload_path = art_dir / f"{saved_artifact_id}.bin"
    assert payload_path.exists()
    assert payload_path.read_bytes() == b"preserved_content_payload"
    assert db_file.exists()

    minimal_features: list[Callable[[], Feature]] = [
        lambda: DatabaseFeature(DatabaseConfig(database_path=db_file)),
        lambda: MigrationFeature(MigrationConfig()),
    ]

    async def _verify_minimal() -> None:
        async with Runtime(minimal_features) as rt:
            db = rt.require(DATABASE_SERVICE)
            rows = db.execute_query(
                "SELECT artifact_id FROM persistence_artifacts WHERE artifact_id = ?;",
                (saved_artifact_id,),
            )
            assert len(rows) == 1
            assert rows[0]["artifact_id"] == saved_artifact_id

    asyncio.run(_verify_minimal())

    assert payload_path.exists()
    assert payload_path.read_bytes() == b"preserved_content_payload"


def test_workspace_persistence_inherits_database_service_path(tmp_path: Path) -> None:
    """Verify that WorkspacePersistenceFeature dynamically inherits DatabaseService path."""
    db_file = tmp_path / "inherited_workspace.db"

    features: list[Callable[[], Feature]] = [
        lambda: DatabaseFeature(DatabaseConfig(database_path=db_file)),
        WorkspacePersistenceFeature,
    ]

    async def _verify() -> None:
        async with Runtime(features) as rt:
            ws_persist = rt.require(WORKSPACE_PERSISTENCE)
            # Service initialized using db_file: count active jobs without error
            count = ws_persist.count_active_jobs()
            assert count == 0
            assert db_file.exists()

    asyncio.run(_verify())
