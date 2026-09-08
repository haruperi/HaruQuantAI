"""Acceptance tests for the three owned workspace-management requirements."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from app.contracts.workspace.errors import (
    WorkspaceAlreadyOpenError,
    WorkspaceCorruptionError,
    WorkspaceError,
)
from app.contracts.workspace.manage_workspaces import (
    ManageWorkspaceOperation,
    ManageWorkspacesRequest,
)
from app.contracts.workspace.models import WorkspaceRestorePlan
from app.services.workspace.manage_workspaces._backup import _canonical_json
from app.services.workspace.manage_workspaces.manage_workspaces import (
    ManageWorkspacesService,
)


def _open_request(
    workspace: Path, *, read_only: bool = False
) -> ManageWorkspacesRequest:
    return ManageWorkspacesRequest(
        request_id=str(uuid.uuid4()),
        actor_id="tester",
        account_id="account-a",
        operation=ManageWorkspaceOperation.OPEN,
        workspace_path=workspace,
        read_only=read_only,
    )


def test_trc_manage_workspaces_001(tmp_path: Path) -> None:
    """One concurrent writer wins; read-only and stable reopen remain available."""
    workspace = tmp_path / "workspace"
    initializer = ManageWorkspacesService()
    initial = initializer.initialize_workspace(
        workspace, "Concurrent Workspace", account_id="account-a"
    )
    workspace_id = initial.workspace_id

    barrier = threading.Barrier(3)
    outcomes: list[str] = []
    winners: list[ManageWorkspacesService] = []

    def compete() -> None:
        service = ManageWorkspacesService()
        barrier.wait()
        try:
            service.manage_workspaces(_open_request(workspace))
        except WorkspaceAlreadyOpenError:
            outcomes.append("denied")
        else:
            outcomes.append("acquired")
            winners.append(service)

    threads = [threading.Thread(target=compete) for _ in range(2)]
    for thread in threads:
        thread.start()
    barrier.wait()
    for thread in threads:
        thread.join()
    assert sorted(outcomes) == ["acquired", "denied"]
    assert len(winners) == 1

    read_only = ManageWorkspacesService().manage_workspaces(
        _open_request(workspace, read_only=True)
    )
    assert read_only.fence is not None
    assert read_only.fence.is_read_only
    assert read_only.workspace is not None
    assert read_only.workspace.workspace_id == workspace_id

    winners[0].close()
    reopened = ManageWorkspacesService().manage_workspaces(
        _open_request(workspace, read_only=True)
    )
    assert reopened.workspace is not None
    assert reopened.workspace.workspace_id == workspace_id


def _rewrite_manifest(path: Path, transform: Callable[[dict[str, Any]], None]) -> None:
    document = json.loads(path.read_text(encoding="utf-8"))
    document.pop("manifest_checksum")
    transform(document)
    document["manifest_checksum"] = hashlib.sha256(
        _canonical_json(document)
    ).hexdigest()
    path.write_bytes(_canonical_json(document))


def test_trc_manage_workspaces_002(tmp_path: Path) -> None:
    """Restore rejects corruption before promotion and reconciles all references."""
    workspace = tmp_path / "workspace"
    service = ManageWorkspacesService()
    opened = service.manage_workspaces(_open_request(workspace))
    assert opened.workspace is not None
    assert opened.fence is not None
    artifact = workspace / "artifacts" / "objects" / "series.bin"
    artifact.write_bytes(b"immutable-series")
    digest = service.catalogue_artifact(opened.workspace, artifact)
    backup = service.backup_workspace(opened.workspace, tmp_path / "backups")
    backup_root = tmp_path / "backups" / f"backup_{backup.backup_id}"

    corrupted = backup_root / "artifacts" / "objects" / "series.bin"
    corrupted.write_bytes(b"corrupted")
    rejected = tmp_path / "rejected"
    with pytest.raises(WorkspaceCorruptionError):
        service.restore_workspace(WorkspaceRestorePlan(backup_root, rejected))
    assert not rejected.exists()

    corrupted.write_bytes(b"immutable-series")
    traversal_manifest = backup_root / "backup.json"
    _rewrite_manifest(
        traversal_manifest,
        lambda value: value["files"][0].__setitem__("relative_path", "../outside.db"),
    )
    with pytest.raises(WorkspaceCorruptionError):
        service.restore_workspace(WorkspaceRestorePlan(backup_root, rejected))
    assert not rejected.exists()

    backup = service.backup_workspace(opened.workspace, tmp_path / "valid")
    valid_root = tmp_path / "valid" / f"backup_{backup.backup_id}"
    restored = service.restore_workspace(
        WorkspaceRestorePlan(valid_root, tmp_path / "restored")
    )
    assert restored.workspace_id == opened.workspace.workspace_id
    restored_artifact = restored.root_path / "artifacts" / "objects" / "series.bin"
    assert restored_artifact.read_bytes() == b"immutable-series"
    assert hashlib.sha256(restored_artifact.read_bytes()).hexdigest() == digest
    assert backup.file_count == len(backup.files)
    assert backup.total_bytes == sum(record.size_bytes for record in backup.files)


def test_trc_manage_workspaces_003(tmp_path: Path) -> None:
    """Crash points preserve committed evidence and report orphan custody."""
    workspace = tmp_path / "workspace"
    service = ManageWorkspacesService()
    opened = service.manage_workspaces(_open_request(workspace))
    assert opened.workspace is not None
    staged = workspace / "staging" / "pending.bin"
    staged.write_bytes(b"pending")
    orphan = workspace / "artifacts" / "objects" / "orphan.bin"
    orphan.write_bytes(b"orphan")
    committed = workspace / "artifacts" / "objects" / "committed.bin"
    committed.write_bytes(b"committed")
    committed_hash = service.catalogue_artifact(opened.workspace, committed)
    connection = sqlite3.connect(workspace / "database" / "haruquantai.db")
    try:
        with connection:
            connection.executemany(
                "INSERT INTO publication_journal "
                "(publication_id, content_hash, staged_relative_path, "
                "final_relative_path, state, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    (
                        "before",
                        hashlib.sha256(b"pending").hexdigest(),
                        "staging/pending.bin",
                        "artifacts/objects/pending.bin",
                        "STAGED",
                        "2026-01-01T00:00:00.000000Z",
                    ),
                    (
                        "after",
                        hashlib.sha256(b"orphan").hexdigest(),
                        "staging/after.bin",
                        "artifacts/objects/orphan.bin",
                        "PROMOTED",
                        "2026-01-01T00:00:00.000000Z",
                    ),
                ),
            )
    finally:
        connection.close()

    summary = service.recover_workspace_state(opened.workspace)
    assert summary.staged_artifacts_cleaned == 1
    assert summary.orphaned_jobs_reconciled == 1
    assert not staged.exists()
    assert orphan.exists()
    assert committed.exists()
    assert any("orphan custody retained:after" in item for item in summary.findings)

    connection = sqlite3.connect(workspace / "database" / "haruquantai.db")
    try:
        committed_rows = connection.execute(
            "SELECT content_hash, relative_path FROM artifacts WHERE is_committed = 1"
        ).fetchall()
        journal = connection.execute(
            "SELECT publication_id, state FROM publication_journal"
        ).fetchall()
    finally:
        connection.close()
    assert committed_rows == [(committed_hash, "artifacts/objects/committed.bin")]
    assert journal == [("after", "ORPHANED")]

    repeated = service.recover_workspace_state(opened.workspace)
    assert repeated.staged_artifacts_cleaned == 0
    assert committed.exists()


def test_operation_scope_revision_and_replay(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    service = ManageWorkspacesService()
    request = _open_request(workspace)
    first = service.manage_workspaces(request)
    assert service.manage_workspaces(request) == first
    with pytest.raises(WorkspaceError, match="different input"):
        service.manage_workspaces(
            ManageWorkspacesRequest(
                request_id=request.request_id,
                actor_id=request.actor_id,
                account_id=request.account_id,
                operation=ManageWorkspaceOperation.OPEN,
                workspace_path=workspace,
                read_only=True,
            )
        )
    service.close()
    with pytest.raises(WorkspaceError, match="different account"):
        service.manage_workspaces(
            ManageWorkspacesRequest(
                request_id=str(uuid.uuid4()),
                actor_id="tester",
                account_id="account-b",
                operation=ManageWorkspaceOperation.OPEN,
                workspace_path=workspace,
                read_only=True,
            )
        )
