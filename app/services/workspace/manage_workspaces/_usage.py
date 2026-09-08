"""Bounded offline usage scenarios for FEAT-WS-MANAGE_WORKSPACES."""

from __future__ import annotations

import hashlib
import shutil
import sqlite3
import tempfile
import uuid
from pathlib import Path

from app.contracts.workspace.errors import (
    WorkspaceAlreadyOpenError,
    WorkspaceCorruptionError,
)
from app.contracts.workspace.manage_workspaces import (
    ManageWorkspaceOperation,
    ManageWorkspacesRequest,
)
from app.services.workspace.manage_workspaces.manage_workspaces import (
    ManageWorkspacesService,
)


def _request(
    operation: ManageWorkspaceOperation,
    workspace: Path,
    *,
    name: str | None = None,
    read_only: bool = False,
    destination_path: Path | None = None,
    backup_manifest_path: Path | None = None,
    fence_token: str | None = None,
    workspace_id: str | None = None,
    expected_revision: int | None = None,
) -> ManageWorkspacesRequest:
    return ManageWorkspacesRequest(
        request_id=str(uuid.uuid4()),
        actor_id="usage-operator",
        account_id="usage-account",
        operation=operation,
        workspace_path=workspace,
        name=name,
        read_only=read_only,
        destination_path=destination_path,
        backup_manifest_path=backup_manifest_path,
        fence_token=fence_token,
        workspace_id=workspace_id,
        expected_revision=expected_revision,
    )


def _run_usage_example() -> None:  # noqa: C901, PLR0915 - executable FR walkthrough.
    """Execute all functional requirements with deterministic local fixtures.

    Raises:
        RuntimeError: If an acceptance observation is not met.
    """
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        workspace = root / "workspace"
        service = ManageWorkspacesService()
        opened = service.manage_workspaces(
            _request(ManageWorkspaceOperation.OPEN, workspace, name="Usage Workspace")
        )
        if opened.workspace is None or opened.fence is None:
            raise RuntimeError("OPEN did not return workspace and fence")

        competitor = ManageWorkspacesService()
        try:
            competitor.manage_workspaces(
                _request(ManageWorkspaceOperation.OPEN, workspace)
            )
        except WorkspaceAlreadyOpenError:
            pass
        else:
            raise RuntimeError("A competing writer acquired the workspace")
        read_only = competitor.manage_workspaces(
            _request(ManageWorkspaceOperation.OPEN, workspace, read_only=True)
        )
        if read_only.fence is None or not read_only.fence.is_read_only:
            raise RuntimeError("Read-only recovery mode was not provided")

        artifact = workspace / "artifacts" / "objects" / "usage.bin"
        artifact.write_bytes(b"immutable usage artifact")
        service.catalogue_artifact(opened.workspace, artifact)
        backups = root / "backups"
        backup = service.manage_workspaces(
            _request(
                ManageWorkspaceOperation.BACKUP,
                workspace,
                workspace_id=opened.workspace.workspace_id,
                expected_revision=opened.workspace_revision,
                fence_token=opened.fence.lock_token,
                destination_path=backups,
            )
        )
        if backup.backup is None:
            raise RuntimeError("BACKUP did not return a manifest")
        backup_root = backups / f"backup_{backup.backup.backup_id}"

        corrupt = root / "corrupt-backup"
        shutil.copytree(backup_root, corrupt)
        (corrupt / "artifacts" / "objects" / "usage.bin").write_bytes(b"corrupt")
        try:
            competitor.manage_workspaces(
                _request(
                    ManageWorkspaceOperation.RESTORE,
                    root / "rejected",
                    backup_manifest_path=corrupt,
                )
            )
        except WorkspaceCorruptionError:
            pass
        else:
            raise RuntimeError("Corrupt restore was accepted")
        restored = competitor.manage_workspaces(
            _request(
                ManageWorkspaceOperation.RESTORE,
                root / "restored",
                workspace_id=opened.workspace.workspace_id,
                backup_manifest_path=backup_root,
            )
        )
        if (
            restored.workspace is None
            or restored.workspace.workspace_id != opened.workspace.workspace_id
        ):
            raise RuntimeError("Restore did not preserve workspace identity")

        staged = workspace / "staging" / "before-promotion.tmp"
        staged.write_bytes(b"staged")
        orphan = workspace / "artifacts" / "objects" / "orphan.bin"
        orphan.write_bytes(b"orphan")
        connection = sqlite3.connect(workspace / "database" / "haruquantai.db")
        try:
            with connection:
                connection.executemany(
                    "INSERT INTO publication_journal "
                    "(publication_id, content_hash, staged_relative_path, "
                    "final_relative_path, state, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        (
                            str(uuid.uuid4()),
                            hashlib.sha256(b"staged").hexdigest(),
                            "staging/before-promotion.tmp",
                            "artifacts/objects/not-promoted.bin",
                            "STAGED",
                            "2026-01-01T00:00:00.000000Z",
                        ),
                        (
                            str(uuid.uuid4()),
                            hashlib.sha256(b"orphan").hexdigest(),
                            "staging/promoted.tmp",
                            "artifacts/objects/orphan.bin",
                            "PROMOTED",
                            "2026-01-01T00:00:00.000000Z",
                        ),
                    ),
                )
        finally:
            connection.close()
        recovered = service.manage_workspaces(
            _request(
                ManageWorkspaceOperation.RECOVER,
                workspace,
                workspace_id=opened.workspace.workspace_id,
                fence_token=opened.fence.lock_token,
            )
        )
        if (
            recovered.recovery is None
            or recovered.recovery.staged_artifacts_cleaned != 1
            or recovered.recovery.orphaned_jobs_reconciled != 1
            or not orphan.exists()
        ):
            raise RuntimeError("Crash reconciliation did not preserve orphan custody")

        service.close()
        reopened = ManageWorkspacesService().manage_workspaces(
            _request(ManageWorkspaceOperation.OPEN, workspace, read_only=True)
        )
        if (
            reopened.workspace is None
            or reopened.workspace.workspace_id != opened.workspace.workspace_id
        ):
            raise RuntimeError("Reopen changed workspace identity")
        print(
            "Usage verification passed: one writer, read-only recovery, "
            "verified restore, stable identity, and orphan custody"
        )


if __name__ == "__main__":
    _run_usage_example()
