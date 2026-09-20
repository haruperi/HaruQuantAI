"""Tests for reference-safe retention feature (FEAT-PERSISTENCE-RETENTION)."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from app.contracts.persistence import (
    ARTIFACT_STORE,
    DATABASE_SERVICE,
    RETENTION_SERVICE,
    RetentionReferenceBlockedError,
)
from app.kernel.bootstrapper import Runtime
from app.services.persistence.artifacts import (
    ArtifactConfig,
    ArtifactFeature,
    ArtifactServiceImpl,
)
from app.services.persistence.databanks import (
    DatabankConfig,
    DatabankServiceImpl,
)
from app.services.persistence.database import (
    DatabaseConfig,
    DatabaseFeature,
    DatabaseServiceImpl,
)
from app.services.persistence.retention import (
    RetentionConfig,
    RetentionFeature,
    RetentionServiceImpl,
    feature,
)


def test_retention_plan_eligible_and_blocked(tmp_path: Path) -> None:
    """Test purge planning correctly categorizes eligible vs blocked artifacts."""
    db_file = tmp_path / "retention_test.db"
    art_dir = tmp_path / "artifacts"
    staging_dir = tmp_path / "staging"

    db_service = DatabaseServiceImpl(DatabaseConfig(database_path=db_file))
    art_store = ArtifactServiceImpl(
        db_service,
        ArtifactConfig(artifacts_dir=art_dir, staging_dir=staging_dir),
    )
    retention = RetentionServiceImpl(
        db_service,
        art_store,
        RetentionConfig(artifacts_dir=art_dir),
    )

    # 1. Orphan artifact (eligible)
    orphan = art_store.store_artifact(b"orphan_payload", "text/plain")

    # 2. Databank member artifact (blocked)
    member_art = art_store.store_artifact(b"member_payload", "text/plain")
    db_service.execute_mutation(
        "INSERT INTO persistence_databanks "
        "(project_name, databank_name, capacity, default_view, auto_sync_policy, created_at_utc) "
        "VALUES ('Project1', 'Results', 100, 'Default', 'never', '2026-09-20T12:00:00Z');"
    )
    db_service.execute_mutation(
        "INSERT INTO persistence_databank_members "
        "(project_name, databank_name, artifact_id, fitness, ranking_value, "
        "metrics_json, annotations_json, added_at_utc) "
        "VALUES ('Project1', 'Results', ?, 1.5, 100.0, '{}', '{}', '2026-09-20T12:00:00Z');",
        (member_art.artifact_id,),
    )

    # 3. Parent artifact referenced in lineage (blocked)
    parent_art = art_store.store_artifact(b"parent_payload", "text/plain")
    _child_art = art_store.store_artifact(
        b"child_payload", "text/plain", parent_ids=[parent_art.artifact_id]
    )

    # 4. External reference artifact (blocked)
    ext_art = art_store.store_artifact(b"ext_payload", "text/plain")

    plan = retention.plan_purge(
        [
            orphan.artifact_id,
            member_art.artifact_id,
            parent_art.artifact_id,
            ext_art.artifact_id,
            "non_existent_id",
        ],
        active_references={ext_art.artifact_id: ["job_worker_123"]},
    )

    assert plan.eligible_artifact_ids == (orphan.artifact_id,)
    assert set(plan.blocked_artifact_ids) == {
        member_art.artifact_id,
        parent_art.artifact_id,
        ext_art.artifact_id,
        "non_existent_id",
    }
    assert any("databank" in r for r in plan.blocking_reasons[member_art.artifact_id])
    assert any("parent" in r for r in plan.blocking_reasons[parent_art.artifact_id])
    assert any("external" in r for r in plan.blocking_reasons[ext_art.artifact_id])
    assert any("catalog" in r for r in plan.blocking_reasons["non_existent_id"])


def test_dry_run_and_real_purge(tmp_path: Path) -> None:
    """Test dry-run vs real deletion and audit recording."""
    db_file = tmp_path / "purge_exec.db"
    art_dir = tmp_path / "artifacts"
    staging_dir = tmp_path / "staging"

    db_service = DatabaseServiceImpl(DatabaseConfig(database_path=db_file))
    art_store = ArtifactServiceImpl(
        db_service,
        ArtifactConfig(artifacts_dir=art_dir, staging_dir=staging_dir),
    )
    retention = RetentionServiceImpl(
        db_service,
        art_store,
        RetentionConfig(artifacts_dir=art_dir),
    )

    rec = art_store.store_artifact(b"purgeable_data", "text/plain")
    payload_file = art_dir / f"{rec.artifact_id}.bin"
    assert payload_file.exists()

    plan = retention.plan_purge([rec.artifact_id])
    assert plan.eligible_artifact_ids == (rec.artifact_id,)

    # 1. Dry run
    report_dry = retention.execute_purge(plan, dry_run=True)
    assert report_dry.purged_count == 1
    assert report_dry.reclaimed_bytes == len(b"purgeable_data")
    assert payload_file.exists()
    assert art_store.get_artifact(rec.artifact_id) is not None
    assert len(retention.get_audit_history()) == 0

    # 2. Real purge
    report_real = retention.execute_purge(plan, dry_run=False)
    assert report_real.purged_count == 1
    assert not payload_file.exists()
    assert art_store.get_artifact(rec.artifact_id) is None

    audit_logs = retention.get_audit_history(report_real.operation_id)
    assert len(audit_logs) == 1
    assert audit_logs[0]["artifact_id"] == rec.artifact_id
    assert audit_logs[0]["reason"] == "retention_policy"


def test_retention_feature_lifecycle(tmp_path: Path) -> None:
    """Test runtime composition of RetentionFeature."""

    async def _test() -> None:
        db_file = tmp_path / "runtime_ret.db"
        art_dir = tmp_path / "runtime_artifacts"
        runtime = Runtime(
            [
                lambda: DatabaseFeature(DatabaseConfig(database_path=db_file)),
                lambda: ArtifactFeature(ArtifactConfig(artifacts_dir=art_dir)),
                lambda: RetentionFeature(RetentionConfig(artifacts_dir=art_dir)),
            ]
        )
        async with runtime:
            art_store = runtime.require(ARTIFACT_STORE)
            ret_service = runtime.require(RETENTION_SERVICE)

            art = art_store.store_artifact(b"test_runtime_retention", "text/plain")
            plan = ret_service.plan_purge([art.artifact_id])
            assert plan.eligible_artifact_ids == (art.artifact_id,)
            report = ret_service.execute_purge(plan)
            assert report.purged_count == 1

    asyncio.run(_test())


def test_retention_factory() -> None:
    """Test zero-argument factory returns RetentionFeature."""
    f = feature()
    assert isinstance(f, RetentionFeature)
    assert f.spec.name == "persistence.retention"
    assert DATABASE_SERVICE in f.spec.requires
    assert ARTIFACT_STORE in f.spec.requires
    assert RETENTION_SERVICE in f.spec.provides


def test_stale_plan_purge_fails_closed(tmp_path: Path) -> None:
    """Test that an execute_purge call fails closed if plan becomes stale."""
    db_file = tmp_path / "stale_plan.db"
    art_dir = tmp_path / "artifacts"
    staging_dir = tmp_path / "staging"

    db_service = DatabaseServiceImpl(DatabaseConfig(database_path=db_file))
    art_store = ArtifactServiceImpl(
        db_service,
        ArtifactConfig(artifacts_dir=art_dir, staging_dir=staging_dir),
    )
    databanks = DatabankServiceImpl(db_service, art_store, DatabankConfig())
    retention = RetentionServiceImpl(
        db_service,
        art_store,
        RetentionConfig(artifacts_dir=art_dir),
    )

    databanks.create_databank("ProjectX", "Alpha")
    rec = art_store.store_artifact(b"initial_orphan", "text/plain")

    # Step 1: Create a valid plan where rec is eligible
    plan = retention.plan_purge([rec.artifact_id])
    assert plan.eligible_artifact_ids == (rec.artifact_id,)

    # Step 2: Now add this artifact to a databank, making the plan stale
    databanks.add_member(
        "ProjectX",
        "Alpha",
        rec.artifact_id,
        fitness=1.0,
        ranking_value=1.0,
        metrics={},
    )

    # Step 3: Attempt execute_purge with the stale plan -> must raise
    with pytest.raises(RetentionReferenceBlockedError, match="Stale retention plan"):
        retention.execute_purge(plan)

    # Verify artifact payload and catalog remain intact, and no audit row exists
    payload_file = art_dir / f"{rec.artifact_id}.bin"
    assert payload_file.exists()
    assert art_store.get_artifact(rec.artifact_id) is not None
    assert len(retention.get_audit_history()) == 0
