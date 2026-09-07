"""Structured logging and redaction tests for workspace management."""

from __future__ import annotations

import hashlib
import logging
import uuid
from pathlib import Path

import pytest
from app.composition.logging import BoundLogger
from app.contracts.workspace.errors import WorkspaceAlreadyOpenError
from app.contracts.workspace.manage_workspaces import (
    ManageWorkspaceOperation,
    ManageWorkspacesRequest,
)
from app.services.workspace.manage_workspaces.manage_workspaces import (
    ManageWorkspacesService,
    logger,
)


def _request(
    operation: ManageWorkspaceOperation,
    workspace: Path,
    *,
    request_id: str,
    destination_path: Path | None = None,
    fence_token: str | None = None,
) -> ManageWorkspacesRequest:
    return ManageWorkspacesRequest(
        request_id=request_id,
        actor_id="actor-sensitive-sentinel",
        account_id="account-sensitive-sentinel",
        operation=operation,
        workspace_path=workspace,
        name="workspace-sensitive-sentinel",
        destination_path=destination_path,
        fence_token=fence_token,
    )


def _rendered_records(records: list[logging.LogRecord]) -> str:
    return "\n".join(
        f"{record.getMessage()} {getattr(record, 'fields', {})!r}" for record in records
    )


def test_custom_logger_emits_safe_structured_lifecycle_events(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Successful operations emit structured events without sensitive values."""
    assert isinstance(logger, BoundLogger)
    caplog.set_level(logging.DEBUG, logger="haruquantai")
    workspace = tmp_path / "path-sensitive-sentinel" / "workspace"
    backup_root = tmp_path / "backup-sensitive-sentinel"
    service = ManageWorkspacesService()

    opened = service.manage_workspaces(
        _request(
            ManageWorkspaceOperation.OPEN,
            workspace,
            request_id="request-open-safe",
        )
    )
    assert opened.workspace is not None
    assert opened.fence is not None
    artifact = workspace / "artifacts" / "objects" / "sensitive-filename.bin"
    artifact.write_bytes(b"sensitive-artifact-payload")
    content_hash = service.catalogue_artifact(workspace, artifact)
    backed_up = service.manage_workspaces(
        _request(
            ManageWorkspaceOperation.BACKUP,
            workspace,
            request_id="request-backup-safe",
            destination_path=backup_root,
            fence_token=opened.fence.lock_token,
        )
    )
    assert backed_up.backup is not None

    events = {getattr(record, "event", None) for record in caplog.records}
    assert "workspace.initialized" in events
    assert "workspace.fence.acquired" in events
    assert "workspace.opened" in events
    assert "workspace.backup.completed" in events
    assert "workspace.request.completed" in events
    rendered = _rendered_records(caplog.records)
    forbidden = (
        str(workspace),
        str(backup_root),
        "path-sensitive-sentinel",
        "backup-sensitive-sentinel",
        "actor-sensitive-sentinel",
        "account-sensitive-sentinel",
        "workspace-sensitive-sentinel",
        "sensitive-filename.bin",
        opened.fence.lock_token,
        content_hash,
        hashlib.sha256(b"sensitive-artifact-payload").hexdigest(),
    )
    assert all(value not in rendered for value in forbidden)
    service.close()


def test_writer_denial_logs_code_without_exception_details(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Writer contention logs a bounded denial without path or lock token leakage."""
    caplog.set_level(logging.DEBUG, logger="haruquantai")
    workspace = tmp_path / "denied-path-sensitive-sentinel"
    owner = ManageWorkspacesService()
    opened = owner.manage_workspaces(
        _request(
            ManageWorkspaceOperation.OPEN,
            workspace,
            request_id=str(uuid.uuid4()),
        )
    )
    assert opened.fence is not None

    contender = ManageWorkspacesService()
    with pytest.raises(WorkspaceAlreadyOpenError):
        contender.manage_workspaces(
            _request(
                ManageWorkspaceOperation.OPEN,
                workspace,
                request_id=str(uuid.uuid4()),
            )
        )

    failed = [
        record
        for record in caplog.records
        if getattr(record, "event", None) == "workspace.request.failed"
    ]
    assert len(failed) == 1
    assert failed[0].error_code == "WORKSPACE_ALREADY_OPEN"
    rendered = _rendered_records(caplog.records)
    assert "denied-path-sensitive-sentinel" not in rendered
    assert opened.fence.lock_token not in rendered
    owner.close()
