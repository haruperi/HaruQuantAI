"""Public contract for opening, recovering, and backing up workspaces.

The contract is local-path aware: host paths never cross a remote wire boundary,
but callers receive one versioned, operation-discriminated API. Requests carry
actor, account, request, and expected-revision context so the provider can apply
scope, idempotency, and optimistic concurrency before consequential mutations.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from app.contracts.workspace.models import (
        WorkspaceBackupManifest,
        WorkspaceRecoverySummary,
        WorkspaceRef,
        WorkspaceWriterFence,
    )


class ManageWorkspaceOperation(StrEnum):
    """Operations admitted by ``workspace.manage-workspaces@1``."""

    OPEN = "OPEN"
    BACKUP = "BACKUP"
    RESTORE = "RESTORE"
    RECOVER = "RECOVER"
    RELEASE = "RELEASE"


@dataclass(frozen=True, slots=True)
class ManageWorkspacesRequest:
    """Validated local request for one workspace lifecycle operation."""

    request_id: str
    actor_id: str
    account_id: str
    operation: ManageWorkspaceOperation
    workspace_path: Path
    expected_revision: int | None = None
    workspace_id: str | None = None
    name: str | None = None
    read_only: bool = False
    destination_path: Path | None = None
    backup_manifest_path: Path | None = None
    fence_token: str | None = None
    verify_checksums: bool = True
    schema_version: int = 1

    def __post_init__(self) -> None:  # noqa: C901 - validates a tagged request union.
        """Reject missing identity and operation-specific shape errors.

        Raises:
            ValueError: If identity, version, revision, or operation shape is invalid.
        """
        for field_name in ("request_id", "actor_id", "account_id"):
            if not getattr(self, field_name).strip():
                message = f"{field_name} must be non-empty"
                raise ValueError(message)
        if self.schema_version != 1:
            raise ValueError("schema_version must be 1")
        if self.expected_revision is not None and self.expected_revision < 1:
            raise ValueError("expected_revision must be positive")
        if self.operation is ManageWorkspaceOperation.BACKUP:
            if self.destination_path is None:
                raise ValueError("BACKUP requires destination_path")
        elif self.operation is ManageWorkspaceOperation.RESTORE:
            if self.backup_manifest_path is None:
                raise ValueError("RESTORE requires backup_manifest_path")
        elif self.operation is ManageWorkspaceOperation.RELEASE:
            if not self.fence_token:
                raise ValueError("RELEASE requires fence_token")
        elif self.destination_path is not None or self.backup_manifest_path is not None:
            raise ValueError("backup/restore paths are forbidden for this operation")


@dataclass(frozen=True, slots=True)
class ManageWorkspacesSuccess:
    """Successful result from one workspace management request."""

    request_id: str
    operation: ManageWorkspaceOperation
    workspace: WorkspaceRef | None = None
    fence: WorkspaceWriterFence | None = None
    backup: WorkspaceBackupManifest | None = None
    recovery: WorkspaceRecoverySummary | None = None
    released: bool = False
    workspace_revision: int = 1
    result_version: int = 1


@runtime_checkable
class ManageWorkspacesCapability(Protocol):
    """Version-one workspace lifecycle capability."""

    def manage_workspaces(
        self,
        request: ManageWorkspacesRequest,
    ) -> ManageWorkspacesSuccess:
        """Execute one validated workspace lifecycle request.

        Returns:
            A versioned success receipt.

        Raises:
            WorkspaceError: If the request is denied or cannot be completed.
            ValueError: If the request conflicts with an earlier request ID.
        """
        ...
