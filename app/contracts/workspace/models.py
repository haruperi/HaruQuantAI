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


class AuthenticationMode(StrEnum):
    """Authentication mode required by the launcher/server runtime."""

    LOCAL_SESSION = "LOCAL_SESSION"
    NONLOCAL_TOKEN = "NONLOCAL_TOKEN"  # noqa: S105 - auth mode name


class JobKind(StrEnum):
    """Job categories admitted through workspace storage guards."""

    DATA_IMPORT = "DATA_IMPORT"
    BACKTEST = "BACKTEST"
    CODE_GENERATION = "CODE_GENERATION"


@dataclass(frozen=True, slots=True)
class WorkspaceSettings:
    """Validated, versioned workspace runtime settings.

    Attributes:
        timezone: IANA timezone identifier.
        locale: BCP 47 locale tag.
        worker_count: Number of local workers (>= 1).
        worker_memory_mb: Per-worker memory limit in MiB (> 0).
        max_artifact_size_mb: Maximum admitted single-artifact size in MiB (> 0).
        max_total_artifact_gb: Maximum total artifact storage in GiB (> 0).
        artifacts_dir: Workspace-relative artifacts directory.
        logs_dir: Workspace-relative logs directory.
        cache_dir: Workspace-relative cache directory.
        exports_dir: Workspace-relative exports directory.
        log_level: Structured-log level name.
        log_retention_days: Log retention window in days (> 0).
        retention_days: Workspace metadata retention window in days (> 0).
    """

    timezone: str
    locale: str
    worker_count: int
    worker_memory_mb: int
    max_artifact_size_mb: int
    max_total_artifact_gb: int
    artifacts_dir: str = "artifacts"
    logs_dir: str = "logs"
    cache_dir: str = "cache"
    exports_dir: str = "exports"
    log_level: str = "INFO"
    log_retention_days: int = 30
    retention_days: int = 365


@dataclass(frozen=True, slots=True)
class WorkspaceSettingsVersion:
    """Immutable persisted version of workspace settings.

    Attributes:
        workspace_id: Owning workspace identifier.
        version: Monotonic settings version number.
        settings: The validated settings payload.
        created_at: ISO 8601 UTC timestamp of the version.
    """

    workspace_id: str
    version: int
    settings: WorkspaceSettings
    created_at: str


@dataclass(frozen=True, slots=True)
class StorageGuardLimits:
    """Configurable workspace storage guard thresholds.

    Attributes:
        min_free_space_mb: Minimum free workspace disk space in MiB.
        max_artifact_size_mb: Maximum admitted projected artifact size in MiB.
    """

    min_free_space_mb: int = 512
    max_artifact_size_mb: int = 4096


@dataclass(frozen=True, slots=True)
class StorageGuardDecision:
    """Admission decision produced by the storage guards.

    Attributes:
        admitted: True when the job may be queued.
        job_kind: The guarded job category.
        required_mb: Projected storage requirement in MiB including the
            minimum free-space reserve.
        available_mb: Currently available workspace disk space in MiB.
        reason: Empty when admitted, otherwise a stable rejection reason.
    """

    admitted: bool
    job_kind: JobKind
    required_mb: float
    available_mb: float
    reason: str = ""


@dataclass(frozen=True, slots=True)
class ServerRuntimeSettings:
    """Launcher/server runtime settings subject to pre-launch validation.

    Attributes:
        bind_address: IP address to bind; loopback by default.
        port: TCP port (1-65535).
        headless: True to run without the browser UI.
        authentication_mode: Authentication mode required for the binding.
        allow_non_loopback: Explicit non-loopback opt-in.
        worker_cpu_percent: Per-worker CPU limit percentage (1-100).
        global_cpu_percent: Global CPU limit percentage (1-100).
        worker_memory_mb: Per-worker memory limit in MiB (> 0).
        global_memory_mb: Global memory limit in MiB (> 0).
    """

    port: int
    bind_address: str = "127.0.0.1"
    headless: bool = False
    authentication_mode: AuthenticationMode = AuthenticationMode.LOCAL_SESSION
    allow_non_loopback: bool = False
    worker_cpu_percent: int = 100
    global_cpu_percent: int = 100
    worker_memory_mb: int = 1024
    global_memory_mb: int = 4096


@dataclass(frozen=True, slots=True)
class ServerRuntimeValidation:
    """Result of pre-launch server runtime validation.

    Attributes:
        valid: True when the settings may launch.
        errors: Field-level validation errors; empty when valid.
        port_available: False when the configured port cannot be bound.
    """

    valid: bool
    errors: tuple[str, ...] = ()
    port_available: bool = True


@dataclass(frozen=True, slots=True)
class ResourceRequirements:
    """Minimum and recommended resource levels of a support profile.

    Attributes:
        minimum_cpu_cores: Minimum CPU core count.
        recommended_cpu_cores: Recommended CPU core count.
        minimum_memory_gb: Minimum total memory in GiB.
        recommended_memory_gb: Recommended total memory in GiB.
        minimum_free_storage_gb: Minimum free storage in GiB.
        recommended_free_storage_gb: Recommended free storage in GiB.
    """

    minimum_cpu_cores: int
    recommended_cpu_cores: int
    minimum_memory_gb: int
    recommended_memory_gb: int
    minimum_free_storage_gb: int
    recommended_free_storage_gb: int


@dataclass(frozen=True, slots=True)
class RuntimeSupportProfile:
    """Versioned runtime support profile published by each release.

    Attributes:
        profile_version: Monotonic support-profile version.
        os_families: Supported operating-system families.
        architectures: Supported machine architectures.
        resources: Minimum and recommended resource levels.
        filesystems: Supported filesystem semantics.
        browsers: Supported browsers.
        required_compilers: Required external compilers and minimum versions.
    """

    profile_version: int
    os_families: tuple[str, ...]
    architectures: tuple[str, ...]
    resources: ResourceRequirements
    filesystems: tuple[str, ...]
    browsers: tuple[str, ...]
    required_compilers: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RuntimeResourceReport:
    """Below-recommended resource findings; empty when resources suffice.

    Attributes:
        warnings: Human-readable below-recommended findings; never a
            capability claim.
    """

    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class LocalSession:
    """Ephemeral session issued for local launcher client access.

    Attributes:
        session_id: Unique UUID identifier for the session.
        token: Cryptographically secure ephemeral session token.
        client_id: Identifier of the connecting launcher client.
        client_host: Host IP address of the client connection.
        issued_at: ISO 8601 UTC timestamp of token issuance.
        expires_at: ISO 8601 UTC timestamp when session expires.
        is_loopback: True if client connection is bound to loopback.
        is_launcher_connected: True if caller is verified launcher-connected.
    """

    session_id: str
    token: str
    client_id: str
    client_host: str
    issued_at: str
    expires_at: str
    is_loopback: bool = True
    is_launcher_connected: bool = True


class HealthStatus(StrEnum):
    """Operational health classification."""

    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"


@dataclass(frozen=True, slots=True)
class SystemHealth:
    """Diagnostic system health summary available before full readiness.

    Attributes:
        status: Overall health classification.
        healthy: True when runtime health checks succeed.
        checked_at: ISO 8601 UTC timestamp of the health check.
        components: Mapping of component names to health status strings.
    """

    status: HealthStatus = HealthStatus.HEALTHY
    healthy: bool = True
    checked_at: str = ""
    components: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SystemReadiness:
    """Readiness status exposing operational readiness without secret disclosure.

    Attributes:
        ready: True only after schema migrations and state recovery succeed.
        healthy: Overall runtime health status.
        build_version: Application release version string.
        build_commit: Git commit or build identifier.
        schema_version: Current workspace metadata schema version if open.
        migrations_current: True if all workspace migrations are applied.
        state_recovered: True if startup workspace state recovery is complete.
        worker_capacity: Configured worker execution capacity.
        active_workers: Count of currently active workers.
        checked_at: ISO 8601 UTC timestamp of readiness check.
        reasons: Diagnostic reasons if system is not fully ready.
    """

    ready: bool
    healthy: bool
    build_version: str
    build_commit: str
    schema_version: int | None
    migrations_current: bool
    state_recovered: bool
    worker_capacity: int
    active_workers: int
    checked_at: str
    reasons: tuple[str, ...] = field(default_factory=tuple)
