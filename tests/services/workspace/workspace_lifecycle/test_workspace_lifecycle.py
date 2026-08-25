"""Unit tests for FEAT-WS-MANAGE_WORKSPACES (Workspace Lifecycle)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest.mock import patch

import pytest

from app.contracts.workspace.capabilities import MANAGE_WORKSPACES_CAPABILITY
from app.contracts.workspace.errors import (
    WorkspaceAlreadyOpenError,
    WorkspaceCorruptionError,
    WorkspaceError,
    WorkspaceNotFoundError,
    WorkspaceStorageError,
)
from app.contracts.workspace.models import (
    WorkspaceRestorePlan,
    WorkspaceStatus,
)
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.workspace.workspace_lifecycle.feature import (
    feature,
)
from app.services.workspace.workspace_lifecycle.workspace_lifecycle import (
    CURRENT_SCHEMA_VERSION,
    SUBDIRECTORIES,
    WorkspaceLifecycleService,
)

if TYPE_CHECKING:
    from app.kernel.capability import CapabilityKey


@pytest.fixture
def service() -> WorkspaceLifecycleService:
    """Fixture providing a fresh WorkspaceLifecycleService instance."""
    return WorkspaceLifecycleService()


def test_ws_initialize_workspace(
    tmp_path: Path, service: WorkspaceLifecycleService
) -> None:
    """Test FR-WS-INITIALIZE_WORKSPACE: Atomic workspace creation and schema setup."""
    ws_path = tmp_path / "my_workspace"
    ws_ref = service.initialize_workspace(ws_path, name="Test WS")

    assert ws_ref.name == "Test WS"
    assert ws_ref.status == WorkspaceStatus.READY
    assert ws_ref.root_path == ws_path.resolve()
    assert ws_ref.workspace_id

    for sub in SUBDIRECTORIES:
        assert (ws_path / sub).is_dir(), f"Missing sub-directory {sub}"

    db_path = ws_path / "metadata" / "workspace.db"
    assert db_path.is_file()

    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT journal_mode FROM pragma_journal_mode();")
        assert cursor.fetchone()[0].lower() == "wal"

        cursor.execute("SELECT id, name FROM workspace;")
        row = cursor.fetchone()
        assert row[0] == ws_ref.workspace_id
        assert row[1] == "Test WS"

        cursor.execute("SELECT version, name FROM schema_migrations;")
        migration_row = cursor.fetchone()
        assert migration_row[0] == 1
        assert migration_row[1] == "base_workspace_schema_v1"
    finally:
        conn.close()

    with pytest.raises(WorkspaceError) as exc_info:
        service.initialize_workspace(ws_path)
    assert exc_info.value.error_code == "WORKSPACE_ALREADY_EXISTS"


def test_ws_initialize_unwritable_path(service: WorkspaceLifecycleService) -> None:
    """Test FR-WS-INITIALIZE_WORKSPACE raises WorkspaceStorageError on unwritable path."""
    with (
        patch("pathlib.Path.mkdir", side_effect=OSError("Permission denied")),
        pytest.raises(WorkspaceStorageError),
    ):
        service.initialize_workspace(Path("/invalid/nonexistent/path"))


def test_ws_migrate_workspace_schema(
    tmp_path: Path, service: WorkspaceLifecycleService
) -> None:
    """Test FR-WS-MIGRATE_WORKSPACE_SCHEMA: Transactional schema versioning and idempotency."""
    ws_path = tmp_path / "migrate_workspace"
    ws_ref = service.initialize_workspace(ws_path)

    ver = service.migrate_workspace_schema(ws_ref)
    assert ver.schema_version == CURRENT_SCHEMA_VERSION
    assert ver.database_engine == "sqlite3"

    ver2 = service.migrate_workspace_schema(ws_path)
    assert ver2.schema_version == CURRENT_SCHEMA_VERSION

    with pytest.raises(WorkspaceNotFoundError):
        service.migrate_workspace_schema(tmp_path / "missing_ws")


def test_ws_fence_workspace_writers(
    tmp_path: Path, service: WorkspaceLifecycleService
) -> None:
    """Test FR-WS-FENCE_WORKSPACE_WRITERS: Exclusive writer lock and diagnostic access."""
    ws_path = tmp_path / "fenced_workspace"
    ws_ref = service.initialize_workspace(ws_path)

    fence = service.fence_workspace_writers(ws_ref, read_only=False)
    assert fence.is_write_locked
    assert not fence.is_read_only
    assert (ws_path / ".workspace.lock").exists()

    fence_same_proc = service.fence_workspace_writers(ws_ref, read_only=False)
    assert fence_same_proc.lock_token == fence.lock_token

    ro_fence = service.fence_workspace_writers(ws_ref, read_only=True)
    assert ro_fence.is_read_only
    assert not ro_fence.is_write_locked

    with patch(
        "app.services.workspace.workspace_lifecycle.workspace_lifecycle._is_process_alive",
        return_value=True,
    ):
        lock_path = ws_path / ".workspace.lock"
        fake_payload = {
            "workspace_id": ws_ref.workspace_id,
            "holder_pid": 999999,
            "lock_token": "foreign_token",
            "acquired_at": "2026-08-24T00:00:00Z",
        }
        lock_path.write_text(json.dumps(fake_payload), encoding="utf-8")

        with pytest.raises(WorkspaceAlreadyOpenError) as exc_info:
            service.fence_workspace_writers(ws_ref, read_only=False)
        assert exc_info.value.error_code == "WORKSPACE_ALREADY_OPEN"
        assert exc_info.value.holder_pid == 999999

    with patch(
        "app.services.workspace.workspace_lifecycle.workspace_lifecycle._is_process_alive",
        return_value=False,
    ):
        lock_path.write_text(json.dumps(fake_payload), encoding="utf-8")
        recovered_fence = service.fence_workspace_writers(ws_ref, read_only=False)
        assert recovered_fence.is_write_locked

    service.release_writer_fence(recovered_fence, ws_ref)
    assert not (ws_path / ".workspace.lock").exists()

    with pytest.raises(WorkspaceNotFoundError):
        service.fence_workspace_writers(tmp_path / "missing_ws")


def test_ws_recover_workspace_state(
    tmp_path: Path, service: WorkspaceLifecycleService
) -> None:
    """Test FR-WS-RECOVER_WORKSPACE_STATE: Cleanup of uncommitted staging files and locks."""
    ws_path = tmp_path / "recovery_workspace"
    ws_ref = service.initialize_workspace(ws_path)

    staging_file_1 = ws_path / "staging" / "temp1.tmp"
    staging_file_2 = ws_path / "staging" / "temp2.tmp"
    staging_file_1.write_bytes(b"temp_data_1")
    staging_file_2.write_bytes(b"temp_data_2")

    stale_lock = ws_path / ".workspace.lock"
    stale_lock.write_text(
        json.dumps({"holder_pid": 999999, "lock_token": "dead_lock"}),
        encoding="utf-8",
    )

    with patch(
        "app.services.workspace.workspace_lifecycle.workspace_lifecycle._is_process_alive",
        return_value=False,
    ):
        summary = service.recover_workspace_state(ws_ref)
        assert summary.staged_artifacts_cleaned == 2
        assert len(summary.findings) >= 2
        assert not staging_file_1.exists()
        assert not staging_file_2.exists()
        assert not stale_lock.exists()

    with pytest.raises(WorkspaceNotFoundError):
        service.recover_workspace_state(tmp_path / "missing_ws")


def test_ws_backup_and_restore(
    tmp_path: Path, service: WorkspaceLifecycleService
) -> None:
    """Test FR-WS-BACKUP_WORKSPACE and restore: Consistent snapshot and checksum checks."""
    ws_path = tmp_path / "source_workspace"
    ws_ref = service.initialize_workspace(ws_path, name="Production Workspace")

    artifact_dir = ws_path / "artifacts" / "objects"
    test_artifact = artifact_dir / "blob_abc123.bin"
    test_artifact.write_bytes(b"deterministic_historical_bars_payload")

    backup_dest = tmp_path / "backups"
    manifest = service.backup_workspace(ws_ref, backup_dest)

    assert manifest.workspace_id == ws_ref.workspace_id
    assert manifest.file_count >= 2
    assert manifest.manifest_checksum
    assert len(manifest.files) >= 2

    target_path = tmp_path / "restored_workspace"
    plan = WorkspaceRestorePlan(
        backup_manifest_path=backup_dest / f"backup_{manifest.backup_id}",
        target_path=target_path,
        verify_checksums=True,
    )
    restored_ref = service.restore_workspace(plan)

    assert restored_ref.workspace_id == ws_ref.workspace_id
    assert restored_ref.name == "Production Workspace"
    assert restored_ref.status == WorkspaceStatus.READY
    assert (target_path / "metadata" / "workspace.db").is_file()
    assert (target_path / "artifacts" / "objects" / "blob_abc123.bin").is_file()

    with pytest.raises(WorkspaceStorageError):
        service.restore_workspace(plan)

    corrupted_target = tmp_path / "corrupted_target"
    backup_folder = backup_dest / f"backup_{manifest.backup_id}"
    manifest_json = backup_folder / "backup.json"
    manifest_dict = json.loads(manifest_json.read_text(encoding="utf-8"))
    manifest_dict["files"][0]["sha256_hash"] = "00000000000000000000000000000000"
    manifest_json.write_text(json.dumps(manifest_dict), encoding="utf-8")

    corrupted_plan = WorkspaceRestorePlan(
        backup_manifest_path=backup_folder,
        target_path=corrupted_target,
        verify_checksums=True,
    )
    with pytest.raises(WorkspaceCorruptionError):
        service.restore_workspace(corrupted_plan)
    assert not corrupted_target.exists() or not any(corrupted_target.iterdir())


@pytest.mark.asyncio
async def test_workspace_feature_mount_and_spec() -> None:
    """Verify feature specification, mounting, and capability provision."""
    feat = feature()
    assert feat.spec.feature_id == "FEAT-WS-MANAGE_WORKSPACES"
    assert feat.spec.domain == "workspace"
    assert MANAGE_WORKSPACES_CAPABILITY in feat.spec.provides

    registry = ServiceRegistry()
    scope = FeatureScope(owner_id=feat.spec.feature_id)
    event_bus = EventBus()

    def registrar(
        cap: CapabilityKey[Any],
        impl: object,
        sc: FeatureScope,
    ) -> None:
        registry.register(cap, impl, owner_id=feat.spec.feature_id, scope=sc)

    context = DefaultFeatureContext(
        spec=feat.spec,
        scope=scope,
        resolver=registry.resolve,
        provider_registrar=registrar,
        event_bus=event_bus,
    )

    await feat.mount(context, {})
    resolved = registry.resolve(MANAGE_WORKSPACES_CAPABILITY)
    assert resolved is not None
    assert isinstance(resolved, WorkspaceLifecycleService)

    await scope.close()


def test_workspace_lifecycle_usage_scenarios() -> None:
    """Verify the __main__ usage scenarios run successfully."""
    from app.services.workspace.workspace_lifecycle.workspace_lifecycle import (
        _run_usage_scenarios,
    )

    _run_usage_scenarios()
