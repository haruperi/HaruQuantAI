"""Public domain models and data transfer objects for Workspace capabilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path


class WorkspaceStatus(StrEnum):
    """Lifecycle status of a workspace."""

    UNINITIALIZED = "UNINITIALIZED"
    READY = "READY"
    MIGRATING = "MIGRATING"
    LOCKED = "LOCKED"
    RECOVERING = "RECOVERING"
    CORRUPTED = "CORRUPTED"


@dataclass(frozen=True, slots=True)
class WorkspaceRef:
    """Immutable reference to a local or remote workspace.

    Attributes:
        workspace_id: Unique UUID identifier of the workspace.
        name: Human-readable name of the workspace.
        root_path: Root filesystem path of the workspace.
        status: Current operational status of the workspace.
        created_at: ISO 8601 UTC timestamp of workspace creation.
    """

    workspace_id: str
    name: str
    root_path: Path
    status: WorkspaceStatus = WorkspaceStatus.READY
    created_at: str = ""


@dataclass(frozen=True, slots=True)
class WorkspaceVersion:
    """Version metadata for a workspace schema and database.

    Attributes:
        schema_version: Monotonically increasing schema migration version integer.
        app_version: Application release version that created or migrated the schema.
        applied_at: ISO 8601 UTC timestamp when the schema version was applied.
        database_engine: Relational database engine name (e.g. 'sqlite3').
    """

    schema_version: int
    app_version: str
    applied_at: str
    database_engine: str = "sqlite3"


@dataclass(frozen=True, slots=True)
class SchemaMigrationRecord:
    """Record of a single applied database schema migration.

    Attributes:
        version: Integer migration sequence number.
        name: Name or description of the migration step.
        applied_at: ISO 8601 UTC timestamp of application.
        checksum: SHA-256 hash of the migration script.
    """

    version: int
    name: str
    applied_at: str
    checksum: str


@dataclass(frozen=True, slots=True)
class WorkspaceWriterFence:
    """Lease and lock state fencing writers for a workspace.

    Attributes:
        workspace_id: Unique UUID identifier of the workspace.
        lock_token: Secret token representing this writer session.
        holder_pid: Process ID holding the writer fence.
        acquired_at: ISO 8601 UTC timestamp when the lock was acquired.
        is_write_locked: True if an exclusive writer lock is held.
        is_read_only: True if opened in read-only / diagnostic mode.
    """

    workspace_id: str
    lock_token: str
    holder_pid: int
    acquired_at: str
    is_write_locked: bool = True
    is_read_only: bool = False


@dataclass(frozen=True, slots=True)
class BackupFileRecord:
    """Checksum and size record for an artifact in a backup manifest.

    Attributes:
        relative_path: Path relative to workspace root.
        sha256_hash: Lowercase SHA-256 hexadecimal hash.
        size_bytes: Size of the file in bytes.
    """

    relative_path: str
    sha256_hash: str
    size_bytes: int


@dataclass(frozen=True, slots=True)
class WorkspaceBackupManifest:
    """Manifest describing a consistent workspace snapshot.

    Attributes:
        backup_id: Unique UUID identifier for this backup.
        workspace_id: Workspace UUID that was backed up.
        schema_version: Schema version of the metadata database.
        created_at: ISO 8601 UTC timestamp when backup completed.
        file_count: Total number of files captured in the backup.
        total_bytes: Total byte size of all captured files.
        files: List of file checksum records.
        manifest_checksum: SHA-256 hash of the backup index itself.
    """

    backup_id: str
    workspace_id: str
    schema_version: int
    created_at: str
    file_count: int
    total_bytes: int
    files: tuple[BackupFileRecord, ...] = field(default_factory=tuple)
    manifest_checksum: str = ""


@dataclass(frozen=True, slots=True)
class WorkspaceRestorePlan:
    """Plan for restoring a workspace from a backup manifest.

    Attributes:
        backup_manifest_path: Path to the backup manifest or archive.
        target_path: Empty directory path to restore into.
        verify_checksums: Whether to verify SHA-256 checksums during restore.
    """

    backup_manifest_path: Path
    target_path: Path
    verify_checksums: bool = True


@dataclass(frozen=True, slots=True)
class WorkspaceRecoverySummary:
    """Diagnostic outcome of startup workspace state recovery.

    Attributes:
        workspace_id: Target workspace UUID.
        recovered_at: ISO 8601 UTC timestamp of recovery.
        staged_artifacts_cleaned: Count of incomplete staging files cleared.
        expired_leases_released: Count of expired leases reclaimed.
        orphaned_jobs_reconciled: Count of nonterminal orphan jobs marked failed.
        findings: List of diagnostic warning strings discovered during recovery.
    """

    workspace_id: str
    recovered_at: str
    staged_artifacts_cleaned: int = 0
    expired_leases_released: int = 0
    orphaned_jobs_reconciled: int = 0
    findings: tuple[str, ...] = field(default_factory=tuple)
