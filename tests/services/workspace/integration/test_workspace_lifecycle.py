"""Integration test for WF-WS-001 (Workspace Lifecycle workflow)."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from app.contracts.workspace.capabilities import MANAGE_WORKSPACES_CAPABILITY
from app.contracts.workspace.models import WorkspaceRestorePlan, WorkspaceStatus
from app.contracts.workspace.ports import ManageWorkspacesCapability
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.workspace.workspace_lifecycle.feature import feature

if TYPE_CHECKING:
    from app.kernel.capability import CapabilityKey


@pytest.mark.asyncio
async def test_workspace_lifecycle_workflow(tmp_path: Path) -> None:
    """Verify WF-WS-001: end-to-end lifecycle through mounted capability context."""
    feat = feature()
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

    # 1. Mount feature through lifecycle context
    await feat.mount(context, {})

    # 2. Resolve capability through registry
    workspace_service = registry.resolve(MANAGE_WORKSPACES_CAPABILITY)
    assert workspace_service is not None
    assert isinstance(workspace_service, ManageWorkspacesCapability)

    ws_root = tmp_path / "lifecycle_ws"
    backup_root = tmp_path / "backups"
    restore_root = tmp_path / "restored_ws"

    # 3. FR-WS-INITIALIZE_WORKSPACE: Atomically initialize
    ref = workspace_service.initialize_workspace(ws_root, name="Lifecycle Test WS")
    assert ref.status == WorkspaceStatus.READY
    assert (ws_root / "metadata" / "workspace.db").exists()

    # 4. FR-WS-MIGRATE_WORKSPACE_SCHEMA: Transactional migrations
    ver = workspace_service.migrate_workspace_schema(ref)
    assert ver.schema_version >= 1

    # 5. FR-WS-FENCE_WORKSPACE_WRITERS: Acquire writer fence
    fence = workspace_service.fence_workspace_writers(ref, read_only=False)
    assert fence.is_write_locked

    # 6. FR-WS-RECOVER_WORKSPACE_STATE: Recover staged artifacts
    staged_file = ws_root / "staging" / "test_uncommitted.tmp"
    staged_file.write_text("in-flight work", encoding="utf-8")
    recovery = workspace_service.recover_workspace_state(ref)
    assert recovery.staged_artifacts_cleaned == 1
    assert not staged_file.exists()

    # 7. Add sample committed artifact
    sample_blob = ws_root / "artifacts" / "objects" / "sample_series.parquet"
    sample_blob.write_bytes(b"PARQUET_MAGIC_SAMPLE_DATA")

    # 8. FR-WS-BACKUP_WORKSPACE: Produce verified backup snapshot
    manifest = workspace_service.backup_workspace(ref, backup_root)
    assert manifest.file_count >= 2

    # Release fence before unmount/restore
    workspace_service.release_writer_fence(fence, ref)

    # 9. Verified restore into empty workspace
    restore_plan = WorkspaceRestorePlan(
        backup_manifest_path=backup_root / f"backup_{manifest.backup_id}",
        target_path=restore_root,
        verify_checksums=True,
    )
    restored = workspace_service.restore_workspace(restore_plan)
    assert restored.workspace_id == ref.workspace_id
    assert (restore_root / "metadata" / "workspace.db").exists()
    assert (restore_root / "artifacts" / "objects" / "sample_series.parquet").exists()

    # 10. Clean scope teardown
    await scope.close()
