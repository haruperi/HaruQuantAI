"""Tests for hot snapshots feature (FEAT-PERSISTENCE-SNAPSHOTS)."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from app.contracts.persistence import (
    SNAPSHOT_SERVICE,
    SnapshotError,
)
from app.kernel.bootstrapper import Runtime
from app.services.persistence.database import (
    DatabaseConfig,
    DatabaseFeature,
    DatabaseServiceImpl,
)
from app.services.persistence.snapshots import (
    SnapshotConfig,
    SnapshotFeature,
    SnapshotServiceImpl,
    feature,
)


def test_create_snapshot_default_and_explicit(tmp_path: Path) -> None:
    """Test hot snapshot creation with default generated and explicit paths."""
    db_file = tmp_path / "origin.db"
    db_service = DatabaseServiceImpl(DatabaseConfig(database_path=db_file))

    # Insert test record into databanks
    db_service.execute_mutation(
        "INSERT INTO persistence_databanks "
        "(project_name, databank_name, capacity, default_view, auto_sync_policy, created_at_utc) "
        "VALUES ('Alpha', 'Initial', 100, 'Default', 'never', '2026-09-20T12:00:00Z');"
    )

    snap_dir = tmp_path / "snaps"
    snap_service = SnapshotServiceImpl(
        db_service, SnapshotConfig(snapshot_dir=snap_dir)
    )

    # 1. Default destination
    rec1 = snap_service.create_snapshot(label="test_snap_1")
    assert rec1.path.exists()
    assert rec1.path.parent == snap_dir
    assert rec1.size_bytes > 0
    assert len(rec1.checksum_sha256) == 64
    assert rec1.label == "test_snap_1"

    # 2. Explicit destination
    explicit_path = tmp_path / "custom_dir" / "custom_snap.db"
    rec2 = snap_service.create_snapshot(
        destination_path=explicit_path, label="test_snap_2"
    )
    assert rec2.path == explicit_path
    assert explicit_path.exists()
    assert rec2.label == "test_snap_2"


def test_list_snapshots_ordering(tmp_path: Path) -> None:
    """Test discovering and ordering snapshots."""
    db_file = tmp_path / "origin.db"
    db_service = DatabaseServiceImpl(DatabaseConfig(database_path=db_file))
    snap_dir = tmp_path / "snaps"
    snap_service = SnapshotServiceImpl(
        db_service, SnapshotConfig(snapshot_dir=snap_dir)
    )

    rec1 = snap_service.create_snapshot(label="snap1")
    rec2 = snap_service.create_snapshot(label="snap2")

    discovered = snap_service.list_snapshots()
    assert len(discovered) == 2
    ids = [d.snapshot_id for d in discovered]
    assert rec1.snapshot_id in ids
    assert rec2.snapshot_id in ids


def test_restore_snapshot(tmp_path: Path) -> None:
    """Test hot database restoration from snapshot."""
    db_file = tmp_path / "restore_test.db"
    db_service = DatabaseServiceImpl(DatabaseConfig(database_path=db_file))
    snap_dir = tmp_path / "snaps"
    snap_service = SnapshotServiceImpl(
        db_service, SnapshotConfig(snapshot_dir=snap_dir)
    )

    # State 1: 1 row
    db_service.execute_mutation(
        "INSERT INTO persistence_databanks "
        "(project_name, databank_name, capacity, default_view, auto_sync_policy, created_at_utc) "
        "VALUES ('Proj', 'State1', 100, 'Default', 'never', '2026-09-20T12:00:00Z');"
    )
    snapshot = snap_service.create_snapshot(label="state1")

    # State 2: Add 2nd row and delete 1st row
    db_service.execute_mutation(
        "DELETE FROM persistence_databanks WHERE databank_name = 'State1';"
    )
    db_service.execute_mutation(
        "INSERT INTO persistence_databanks "
        "(project_name, databank_name, capacity, default_view, auto_sync_policy, created_at_utc) "
        "VALUES ('Proj', 'State2', 200, 'Default', 'never', '2026-09-20T12:00:00Z');"
    )
    rows_now = db_service.execute_query(
        "SELECT databank_name FROM persistence_databanks;"
    )
    assert [r["databank_name"] for r in rows_now] == ["State2"]

    # Restore snapshot of State 1
    snap_service.restore_snapshot(snapshot.path)

    # Verify State 1 restored
    rows_restored = db_service.execute_query(
        "SELECT databank_name FROM persistence_databanks;"
    )
    assert [r["databank_name"] for r in rows_restored] == ["State1"]


def test_restore_invalid_and_corrupt(tmp_path: Path) -> None:
    """Test restoration errors for missing or corrupt files."""
    db_file = tmp_path / "valid.db"
    db_service = DatabaseServiceImpl(DatabaseConfig(database_path=db_file))
    snap_service = SnapshotServiceImpl(db_service)

    # Non-existent
    with pytest.raises(SnapshotError, match="does not exist"):
        snap_service.restore_snapshot(tmp_path / "missing.db")

    # Corrupt (not SQLite)
    corrupt_file = tmp_path / "corrupt.db"
    corrupt_file.write_text("random noise not sqlite", encoding="utf-8")
    with pytest.raises(SnapshotError, match="Corrupt SQLite snapshot file"):
        snap_service.restore_snapshot(corrupt_file)


def test_snapshot_feature_lifecycle(tmp_path: Path) -> None:
    """Test feature composition and runtime registration."""

    async def _test() -> None:
        db_file = tmp_path / "runtime_snap.db"
        snap_dir = tmp_path / "runtime_snaps"
        runtime = Runtime(
            [
                lambda: DatabaseFeature(DatabaseConfig(database_path=db_file)),
                lambda: SnapshotFeature(SnapshotConfig(snapshot_dir=snap_dir)),
            ]
        )
        async with runtime:
            service = runtime.require(SNAPSHOT_SERVICE)
            rec = service.create_snapshot(label="lifecycle_test")
            assert rec.path.exists()
            assert rec.label == "lifecycle_test"

    asyncio.run(_test())


def test_snapshot_factory() -> None:
    """Test zero-argument factory returns valid SnapshotFeature."""
    f = feature()
    assert isinstance(f, SnapshotFeature)
    assert f.spec.name == "persistence.snapshots"


def test_restore_with_expected_checksum(tmp_path: Path) -> None:
    """Test snapshot restoration with matching and mismatched expected checksums."""
    db_file = tmp_path / "primary.db"
    restore_target_file = tmp_path / "restore_target.db"
    snap_dir = tmp_path / "snapshots"

    db_primary = DatabaseServiceImpl(DatabaseConfig(database_path=db_file))
    db_target = DatabaseServiceImpl(DatabaseConfig(database_path=restore_target_file))
    snap_primary = SnapshotServiceImpl(
        db_primary, SnapshotConfig(snapshot_dir=snap_dir)
    )
    snap_target = SnapshotServiceImpl(db_target, SnapshotConfig(snapshot_dir=snap_dir))

    db_primary.execute_mutation(
        "INSERT INTO persistence_databanks "
        "(project_name, databank_name, capacity, default_view, auto_sync_policy, created_at_utc) "
        "VALUES ('AlphaProj', 'ValidatedBank', 100, 'Default', 'never', '2025-01-01T00:00:00');"
    )
    rec = snap_primary.create_snapshot(label="validated_snapshot")

    bad_hash = "0" * 64
    with pytest.raises(SnapshotError, match="Snapshot checksum verification failed"):
        snap_target.restore_snapshot(rec.path, expected_checksum_sha256=bad_hash)

    assert len(db_target.execute_query("SELECT * FROM persistence_databanks;")) == 0

    snap_target.restore_snapshot(rec.path, expected_checksum_sha256=rec.checksum_sha256)
    restored_rows = db_target.execute_query("SELECT * FROM persistence_databanks;")
    assert len(restored_rows) == 1
    assert restored_rows[0]["databank_name"] == "ValidatedBank"
