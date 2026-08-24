"""Public capability protocols (ports) for Workspace management."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from pathlib import Path

    from app.contracts.workspace.models import (
        WorkspaceBackupManifest,
        WorkspaceRecoverySummary,
        WorkspaceRef,
        WorkspaceRestorePlan,
        WorkspaceVersion,
        WorkspaceWriterFence,
    )


@runtime_checkable
class ManageWorkspacesCapability(Protocol):
    """Capability protocol for workspace lifecycle operations."""

    def initialize_workspace(
        self,
        path: Path,
        name: str | None = None,
    ) -> WorkspaceRef:
        """Atomically initialize a new workspace at an explicit writable path.

        Creates directory tree (metadata, artifacts, logs, cache, exports, staging,
        backups) and initial SQLite database in WAL mode with base schema.

        Args:
            path: Target filesystem directory path.
            name: Optional human-readable workspace name.

        Returns:
            WorkspaceRef describing the initialized workspace.

        Raises:
            WorkspaceStorageError: If path cannot be created or is not writable.
            WorkspaceError: If workspace already exists or initialization fails.
        """
        ...

    def migrate_workspace_schema(
        self,
        workspace: Path | WorkspaceRef,
    ) -> WorkspaceVersion:
        """Apply ordered, transactional schema migrations to a workspace.

        Records applied migrations and version in the metadata database. Reopening
        an up-to-date database performs no mutations.

        Args:
            workspace: Workspace root path or WorkspaceRef.

        Returns:
            WorkspaceVersion with current schema version.

        Raises:
            WorkspaceNotFoundError: If workspace does not exist.
            WorkspaceMigrationError: If any migration step fails.
        """
        ...

    def fence_workspace_writers(
        self,
        workspace: Path | WorkspaceRef,
        *,
        read_only: bool = False,
    ) -> WorkspaceWriterFence:
        """Acquire an exclusive writer fence or read-only diagnostic lease.

        Args:
            workspace: Workspace root path or WorkspaceRef.
            read_only: True to open in diagnostic read-only mode without write lock.

        Returns:
            WorkspaceWriterFence containing lease and token details.

        Raises:
            WorkspaceNotFoundError: If workspace does not exist.
            WorkspaceAlreadyOpenError: If another active writer holds the fence.
        """
        ...

    def release_writer_fence(
        self,
        fence: WorkspaceWriterFence,
        workspace: Path | WorkspaceRef,
    ) -> None:
        """Release a held writer fence lock.

        Args:
            fence: The active WorkspaceWriterFence to release.
            workspace: Workspace root path or WorkspaceRef.
        """
        ...

    def recover_workspace_state(
        self,
        workspace: Path | WorkspaceRef,
    ) -> WorkspaceRecoverySummary:
        """Recover staged artifacts, expired leases, and nonterminal jobs.

        Args:
            workspace: Workspace root path or WorkspaceRef.

        Returns:
            WorkspaceRecoverySummary with recovery statistics and findings.

        Raises:
            WorkspaceNotFoundError: If workspace does not exist.
        """
        ...

    def backup_workspace(
        self,
        workspace: Path | WorkspaceRef,
        destination_dir: Path,
    ) -> WorkspaceBackupManifest:
        """Create a consistent backup snapshot of metadata and committed artifacts.

        Args:
            workspace: Workspace root path or WorkspaceRef.
            destination_dir: Directory where the backup snapshot/archive is created.

        Returns:
            WorkspaceBackupManifest with file inventory and checksums.

        Raises:
            WorkspaceNotFoundError: If workspace does not exist.
            WorkspaceStorageError: If destination is invalid or write fails.
        """
        ...

    def restore_workspace(
        self,
        plan: WorkspaceRestorePlan,
    ) -> WorkspaceRef:
        """Restore a workspace from a backup manifest into an empty target directory.

        Args:
            plan: WorkspaceRestorePlan describing manifest path and target.

        Returns:
            WorkspaceRef of the restored workspace.

        Raises:
            WorkspaceStorageError: If target path is non-empty or unwritable.
            WorkspaceCorruptionError: If checksum verification fails during restore.
        """
        ...
