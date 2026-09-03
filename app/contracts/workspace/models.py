"""Public domain models and data transfer objects for Workspace capabilities."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, StringConstraints, model_validator

# These wire aliases and base classes are annotation-only for readers but
# Pydantic resolves them at class-creation time, so they must remain runtime
# imports.
from app.contracts.common.models import (
    CapabilityIdentifier,
    ContentHash,
    ResultState,
    UtcTimestamp,
    Uuid7,
    WireModel,
)


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


@dataclass(frozen=True, slots=True)
class DiagnosticBundleManifest:
    """Manifest metadata for an exported redacted diagnostic bundle.

    Attributes:
        bundle_id: Unique UUID identifier for the diagnostic bundle.
        created_at: ISO 8601 UTC timestamp of bundle creation.
        build_version: Application release version string.
        build_commit: Git commit or build identifier.
        schema_version: Schema version of the target workspace if available.
        workspace_id: ID of the inspected workspace if available.
        log_entries_count: Number of redacted structured log records included.
        job_records_count: Number of job state records included.
        integrity_findings: Integrity check findings (empty if healthy).
        redaction_summary: Count of redacted secrets, tokens, or paths.
    """

    bundle_id: str
    created_at: str
    build_version: str
    build_commit: str
    schema_version: int | None
    workspace_id: str | None
    log_entries_count: int
    job_records_count: int
    integrity_findings: tuple[str, ...] = field(default_factory=tuple)
    redaction_summary: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class DiagnosticBundleRef:
    """Reference to a generated diagnostic bundle archive and its manifest.

    Attributes:
        bundle_id: Unique UUID identifier for the bundle.
        archive_path: Filesystem path to the generated zip archive.
        checksum_sha256: Cryptographic SHA-256 digest of the archive file.
        file_size_bytes: Size of the bundle archive in bytes.
        manifest: Detailed manifest describing bundle contents and findings.
    """

    bundle_id: str
    archive_path: Path
    checksum_sha256: str
    file_size_bytes: int
    manifest: DiagnosticBundleManifest


# ---------------------------------------------------------------------------
# Ratified v1 wire contracts (additive; the frozen v1 dataclasses above stay
# unchanged as process contracts). Wire projections of frozen records are
# named ``<Record>Wire``; wire-native records keep their inventory names.
# ``schema_version`` is the record-level ``Literal[1]`` marker except for the
# four collision-exception records (WorkspaceVersion, WorkspaceBackupManifest,
# SystemReadiness, DiagnosticBundleManifest), which keep it as the workspace
# database schema number. Process-local paths and secret tokens never enter
# wire schemas or generated UI types.

# Constrained local string aliases reused across Workspace wire records.
type NonEmptyStr = Annotated[str, StringConstraints(min_length=1)]
type Name1To160 = Annotated[str, StringConstraints(min_length=1, max_length=160)]
type SecretName = Annotated[
    str, StringConstraints(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
]
# Domain assumption: IANA zone names are limited to zone/path segments made
# of letters, digits, ``+``, ``-``, and ``_``; this is a syntactic wire
# check, not tzdb resolution.
type IanaTimezone = Annotated[
    str,
    StringConstraints(pattern=r"^[A-Za-z0-9+\-_]+(?:/[A-Za-z0-9+\-_]+)*$"),
]
# Domain assumption: BCP 47 tags are a primary language subtag of 2-8
# letters followed by optional 1-8 alphanumeric subtags; this is a
# syntactic wire check, not language-subtag-registry resolution.
type Bcp47LanguageTag = Annotated[
    str,
    StringConstraints(pattern=r"^[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*$"),
]
# Domain assumption: IP literals are range-checked dotted-quad IPv4 or
# colon-separated IPv6 forms; full IPv6 group grammar (compression counts,
# IPv4-mapped tails) stays in the process layer.
type IpLiteral = Annotated[
    str,
    StringConstraints(
        pattern=(
            r"^(?:(?:(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\.){3}"
            r"(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)|[0-9A-Fa-f:]*:[0-9A-Fa-f:.]+)$"
        )
    ),
]
# Domain assumption: runtime platform tokens are single uppercase words of
# letters, digits, underscore, and hyphen (e.g. ``X86_64``).
type UppercaseToken = Annotated[str, StringConstraints(pattern=r"^[A-Z][A-Z0-9_-]*$")]
# Domain assumption: endpoints carry an RFC 3986 scheme plus a non-blank
# hierarchical part; dereferenceability is verified by the process layer.
type UriStr = Annotated[
    str,
    StringConstraints(pattern=r"^[A-Za-z][A-Za-z0-9+.-]*://\S+$"),
]
# Workspace-relative POSIX path: non-empty segments, no backslashes, and no
# leading root; ``..`` segments are rejected by record validators.
type RelativePosixPath = Annotated[
    str,
    StringConstraints(pattern=r"^[^/\\]+(?:/[^/\\]+)*$"),
]
type NonNegativeInt = Annotated[int, Field(ge=0)]

# Closed literal unions reused across Workspace wire records. The artifact
# state reuses ``ResultState`` from ``app/contracts/common/`` per Shared
# Contracts §4.3 instead of redeclaring an equivalent union.
type WorkspaceStatusValue = Literal[
    "UNINITIALIZED",
    "READY",
    "MIGRATING",
    "LOCKED",
    "RECOVERING",
    "CORRUPTED",
]
type HealthState = Literal["HEALTHY", "DEGRADED", "UNHEALTHY"]
type LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
type AuthenticationModeValue = Literal["LOCAL_SESSION", "NONLOCAL_TOKEN"]
type WorkerLeaseState = Literal["ACTIVE", "RELEASED", "EXPIRED", "SUPERSEDED"]
type DeploymentMode = Literal["DESKTOP", "HOSTED"]
type AuthorizationOutcome = Literal["ALLOW", "DENY"]


def _require_present(fields: tuple[tuple[str, object], ...]) -> None:
    """Reject an operation request that omits a required field.

    Args:
        fields: ``(field name, value)`` pairs that must not be None.

    Raises:
        ValueError: Any listed field is None.
    """
    for name, value in fields:
        if value is None:
            raise ValueError("required field is missing: " + name)


def _require_absent(fields: tuple[tuple[str, object], ...]) -> None:
    """Reject an operation request that sets a forbidden field.

    Args:
        fields: ``(field name, value)`` pairs that must be None.

    Raises:
        ValueError: Any listed field is not None.
    """
    for name, value in fields:
        if value is not None:
            raise ValueError("forbidden field is set: " + name)


def _require_empty(fields: tuple[tuple[str, tuple[object, ...]], ...]) -> None:
    """Reject an operation request that populates a forbidden sequence.

    Args:
        fields: ``(field name, sequence)`` pairs that must be empty.

    Raises:
        ValueError: Any listed sequence is nonempty.
    """
    for name, value in fields:
        if value:
            raise ValueError("forbidden field is set: " + name)


def _validate_relative_directory(name: str, value: str) -> None:
    """Reject absolute or parent-traversing workspace directories.

    Args:
        name: Field name reported in the validation error.
        value: Declared workspace-relative directory path.

    Raises:
        ValueError: The path anchors to a filesystem root or Windows drive,
            uses a backslash separator, or traverses with a ``..`` segment.
    """
    # Workspace directories are relative, so no absolute anchors and no
    # ``..`` segments; a colon marks a Windows drive anchor.
    if value.startswith("/") or "\\" in value or ":" in value:
        raise ValueError(name + " must be a workspace-relative path")
    if ".." in value.split("/"):
        raise ValueError(name + " must not contain '..' segments")


class WorkspaceRefWire(WireModel):
    """Wire projection of the immutable workspace identity description.

    The v1 ``root_path`` field is process-local and excluded; ``status``
    mirrors the v1 ``WorkspaceStatus`` states.
    """

    workspace_id: Uuid7
    name: Name1To160
    status: WorkspaceStatusValue = "READY"
    created_at: UtcTimestamp
    schema_version: Literal[1] = 1


class WorkspaceVersionWire(WireModel):
    """Wire projection of applied workspace schema migration metadata.

    Collision exception: ``schema_version`` stays the workspace database
    schema number, so this record carries no record-level ``Literal[1]``
    field; its wire-schema identity is the workspace namespace v1.
    """

    schema_version: int = Field(ge=0)
    app_version: NonEmptyStr
    applied_at: UtcTimestamp
    database_engine: NonEmptyStr = "sqlite3"


class WorkspaceSettingsWire(WireModel):
    """Wire form of the v1 ``WorkspaceSettings`` fields.

    Directories are workspace-relative, contain no ``..`` segments or
    absolute anchors, and are mutually distinct.
    """

    timezone: IanaTimezone
    locale: Bcp47LanguageTag
    worker_count: int = Field(ge=1)
    worker_memory_mb: int = Field(ge=1)
    max_artifact_size_mb: int = Field(ge=1)
    max_total_artifact_gb: int = Field(ge=1)
    artifacts_dir: str = "artifacts"
    logs_dir: str = "logs"
    cache_dir: str = "cache"
    exports_dir: str = "exports"
    log_level: LogLevel = "INFO"
    log_retention_days: int = Field(default=30, ge=1)
    retention_days: int = Field(default=365, ge=1)

    @model_validator(mode="after")
    def validate_directories(self) -> WorkspaceSettingsWire:
        """Reject non-relative, parent-traversing, or duplicate directories.

        Returns:
            The validated settings.

        Raises:
            ValueError: A directory anchors to a filesystem root or drive,
                traverses with ``..``, or duplicates another directory.
        """
        directories = (
            ("artifacts_dir", self.artifacts_dir),
            ("logs_dir", self.logs_dir),
            ("cache_dir", self.cache_dir),
            ("exports_dir", self.exports_dir),
        )
        for name, value in directories:
            _validate_relative_directory(name, value)
        if len({value for _, value in directories}) != len(directories):
            raise ValueError("workspace directories must be mutually distinct")
        return self


class WorkspaceConfigurationWire(WireModel):
    """Wire projection of one immutable versioned workspace configuration."""

    workspace_id: Uuid7
    version: int = Field(ge=1)
    settings: WorkspaceSettingsWire
    created_at: UtcTimestamp
    schema_version: Literal[1] = 1


class ServerRuntimeSettingsWire(WireModel):
    """Wire form of the v1 ``ServerRuntimeSettings`` fields."""

    port: int = Field(ge=1, le=65535)
    bind_address: IpLiteral = "127.0.0.1"
    headless: bool = False
    authentication_mode: AuthenticationModeValue = "LOCAL_SESSION"
    allow_non_loopback: bool = False
    worker_cpu_percent: int = Field(default=100, ge=1, le=100)
    global_cpu_percent: int = Field(default=100, ge=1, le=100)
    worker_memory_mb: int = Field(default=1024, ge=1)
    global_memory_mb: int = Field(default=4096, ge=1)

    @model_validator(mode="after")
    def validate_non_loopback_authentication(self) -> ServerRuntimeSettingsWire:
        """Reject non-loopback bindings without nonlocal authentication.

        Returns:
            The validated runtime settings.

        Raises:
            ValueError: ``allow_non_loopback`` is true while
                ``authentication_mode`` is not ``NONLOCAL_TOKEN``.
        """
        if self.allow_non_loopback and self.authentication_mode != "NONLOCAL_TOKEN":
            raise ValueError(
                "allow_non_loopback requires authentication_mode NONLOCAL_TOKEN"
            )
        return self


class ServerRuntimeValidationWire(WireModel):
    """Wire form of the v1 ``ServerRuntimeValidation`` fields."""

    valid: bool
    errors: tuple[NonEmptyStr, ...] = ()
    port_available: bool = True

    @model_validator(mode="after")
    def validate_validity_consistency(self) -> ServerRuntimeValidationWire:
        """Reject a validity flag that contradicts its evidence.

        Returns:
            The validated outcome.

        Raises:
            ValueError: ``valid`` is true while errors exist or the port is
                unavailable, or ``valid`` is false without either cause.
        """
        if self.valid != (not self.errors and self.port_available):
            raise ValueError(
                "valid must be false exactly when errors exist or the port is "
                "unavailable"
            )
        return self


class RuntimeConfigurationWire(WireModel):
    """Wire projection of the validated launcher/server runtime state."""

    settings: ServerRuntimeSettingsWire
    validation: ServerRuntimeValidationWire
    schema_version: Literal[1] = 1


class StorageGuardPolicyWire(WireModel):
    """Wire projection of the workspace storage guard thresholds.

    The policy carries limits only; the admission ``StorageGuardDecision``
    remains the distinct frozen v1 port result.
    """

    min_free_space_mb: int = Field(default=512, ge=1)
    max_artifact_size_mb: int = Field(default=4096, ge=1)
    schema_version: Literal[1] = 1


class WorkspaceWriterLease(WireModel):
    """Wire-native writer lease fencing one workspace writer.

    At most one active lease may exist per workspace and expired leases are
    reclaimed at startup; the paired fence's secret ``lock_token`` stays
    process-local.
    """

    lease_id: Uuid7
    workspace_id: Uuid7
    holder_pid: int = Field(ge=1)
    acquired_at: UtcTimestamp
    expires_at: UtcTimestamp
    is_read_only: bool = False
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_expiry(self) -> WorkspaceWriterLease:
        """Reject leases that expire at or before acquisition.

        Returns:
            The validated lease.

        Raises:
            ValueError: ``expires_at`` is not after ``acquired_at``.
        """
        # UtcTimestamp strings use one fixed-width format, so lexicographic
        # order equals chronological order.
        if self.expires_at <= self.acquired_at:
            raise ValueError("expires_at must be after acquired_at")
        return self


class WorkspaceWriterFenceWire(WireModel):
    """Wire projection of an acquired workspace writer fence.

    The secret ``lock_token`` is process-local; a second writer receives
    ``WORKSPACE_ALREADY_OPEN`` from the frozen v1 port.
    """

    workspace_id: Uuid7
    holder_pid: int = Field(ge=1)
    acquired_at: UtcTimestamp
    is_write_locked: bool = True
    is_read_only: bool = False
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_exclusive_mode(self) -> WorkspaceWriterFenceWire:
        """Reject fences that are both or neither lock and read-only.

        Returns:
            The validated fence.

        Raises:
            ValueError: ``is_write_locked`` equals ``is_read_only``.
        """
        if self.is_write_locked == self.is_read_only:
            raise ValueError(
                "exactly one of is_write_locked and is_read_only must be true"
            )
        return self


class BackupFileRecordWire(WireModel):
    """Wire form of one checksummed file inside a backup manifest."""

    relative_path: RelativePosixPath
    sha256_hash: ContentHash
    size_bytes: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_relative_path(self) -> BackupFileRecordWire:
        """Reject backup paths that traverse outside the workspace root.

        Returns:
            The validated file record.

        Raises:
            ValueError: ``relative_path`` contains a ``..`` segment.
        """
        if ".." in self.relative_path.split("/"):
            raise ValueError("relative_path must not contain '..' segments")
        return self


class WorkspaceBackupManifestWire(WireModel):
    """Wire projection of a consistent workspace backup snapshot.

    Collision exception: ``schema_version`` stays the workspace database
    schema number captured at backup time. The v1 empty-string
    ``manifest_checksum`` default is a process-local construction
    convenience; the wire form requires the canonical hash.
    """

    backup_id: Uuid7
    workspace_id: Uuid7
    schema_version: int = Field(ge=0)
    created_at: UtcTimestamp
    file_count: int = Field(ge=0)
    total_bytes: int = Field(ge=0)
    files: tuple[BackupFileRecordWire, ...] = ()
    manifest_checksum: ContentHash

    @model_validator(mode="after")
    def validate_file_totals(self) -> WorkspaceBackupManifestWire:
        """Reject inventories that contradict their aggregate counters.

        Returns:
            The validated manifest.

        Raises:
            ValueError: ``file_count`` or ``total_bytes`` disagrees with the
                ``files`` records.
        """
        if self.file_count != len(self.files):
            raise ValueError("file_count must equal the number of files")
        if self.total_bytes != sum(record.size_bytes for record in self.files):
            raise ValueError("total_bytes must equal the summed file sizes")
        return self


class WorkspaceRestorePlanWire(WireModel):
    """Wire projection of a backup restore plan.

    The plan references the backup by identity; the v1 ``Path``-based plan
    remains the process contract and restore always targets empty staging.
    """

    backup_id: Uuid7
    verify_checksums: bool = True
    schema_version: Literal[1] = 1


class SecretRef(WireModel):
    """Wire-native opaque reference to one stored workspace secret.

    Secret values never enter wire schemas, manifests, or logs; names are
    unique per workspace (``secret_refs(workspace_id, name UNIQUE)``).
    """

    secret_id: Uuid7
    workspace_id: Uuid7
    name: SecretName
    created_at: UtcTimestamp
    updated_at: UtcTimestamp
    row_version: int = Field(default=1, ge=1)
    schema_version: Literal[1] = 1


class PrincipalRef(WireModel):
    """Wire-native reference to one authenticated hosted principal.

    The authority discriminator is the provider identity; the principal
    replaces the local-session token in hosted mode.
    """

    principal_id: Uuid7
    auth_provider: NonEmptyStr
    schema_version: Literal[1] = 1


class LocalSessionWire(WireModel):
    """Wire projection of an ephemeral local launcher session.

    The secret ``token`` is process-local and never appears in wire schemas
    or generated UI types.
    """

    session_id: Uuid7
    client_id: NonEmptyStr
    client_host: IpLiteral
    issued_at: UtcTimestamp
    expires_at: UtcTimestamp
    is_loopback: bool = True
    is_launcher_connected: bool = True
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_expiry(self) -> LocalSessionWire:
        """Reject sessions that expire at or before issuance.

        Returns:
            The validated session.

        Raises:
            ValueError: ``expires_at`` is not after ``issued_at``.
        """
        if self.expires_at <= self.issued_at:
            raise ValueError("expires_at must be after issued_at")
        return self


class SystemHealthWire(WireModel):
    """Wire projection of the pre-readiness system health summary."""

    status: HealthState = "HEALTHY"
    healthy: bool = True
    checked_at: UtcTimestamp
    components: dict[NonEmptyStr, HealthState] = Field(default_factory=dict)
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_health_consistency(self) -> SystemHealthWire:
        """Reject a health flag that contradicts the classified status.

        Returns:
            The validated health summary.

        Raises:
            ValueError: ``healthy`` differs from ``status == HEALTHY``.
        """
        if self.healthy != (self.status == "HEALTHY"):
            raise ValueError("healthy must equal (status == HEALTHY)")
        return self


class SystemReadinessWire(WireModel):
    """Wire projection of the secret-free system readiness report.

    Collision exception: ``schema_version`` stays the open workspace's
    database schema number, or None when no workspace is open.
    """

    ready: bool
    healthy: bool
    build_version: NonEmptyStr
    build_commit: NonEmptyStr
    schema_version: int | None = Field(ge=0)
    migrations_current: bool
    state_recovered: bool
    worker_capacity: int = Field(ge=0)
    active_workers: int = Field(ge=0)
    checked_at: UtcTimestamp
    reasons: tuple[NonEmptyStr, ...] = ()

    @model_validator(mode="after")
    def validate_readiness(self) -> SystemReadinessWire:
        """Reject impossible worker counts and unearned readiness.

        Returns:
            The validated readiness report.

        Raises:
            ValueError: ``active_workers`` exceeds ``worker_capacity`` or
                ``ready`` is true before migrations and state recovery
                complete.
        """
        if self.active_workers > self.worker_capacity:
            raise ValueError("active_workers must not exceed worker_capacity")
        if self.ready and not (self.migrations_current and self.state_recovered):
            raise ValueError("ready requires migrations_current and state_recovered")
        return self


class DiagnosticBundleManifestWire(WireModel):
    """Wire projection of the redacted diagnostic bundle manifest.

    Collision exception: ``schema_version`` stays the inspected workspace's
    database schema number. Defined before ``DiagnosticBundleRefWire``
    because the reference embeds it; registry order still follows the
    README inventory. Bundles never disclose session tokens, connection
    secrets, or unredacted secret values.
    """

    bundle_id: Uuid7
    created_at: UtcTimestamp
    build_version: NonEmptyStr
    build_commit: NonEmptyStr
    schema_version: int | None = Field(ge=0)
    workspace_id: Uuid7 | None
    log_entries_count: int = Field(ge=0)
    job_records_count: int = Field(ge=0)
    integrity_findings: tuple[NonEmptyStr, ...] = ()
    redaction_summary: dict[NonEmptyStr, NonNegativeInt] = Field(default_factory=dict)


class DiagnosticBundleRefWire(WireModel):
    """Wire projection of a generated diagnostic bundle reference.

    The ``archive_path`` is process-local and excluded; the wire form
    references the bundle by identity, checksum, size, and manifest.
    """

    bundle_id: Uuid7
    checksum_sha256: ContentHash
    file_size_bytes: int = Field(ge=0)
    manifest: DiagnosticBundleManifestWire
    schema_version: Literal[1] = 1


class WorkerCapabilityDescriptor(WireModel):
    """Wire-native registration facts describing one worker build.

    Registration alone confers no trust; ``capabilities`` lists supported
    task/profile/plugin capability versions and ``artifact_locality`` lists
    artifact content hashes present locally.
    """

    capabilities: tuple[CapabilityIdentifier, ...] = Field(min_length=1)
    build_hash: ContentHash
    os_family: UppercaseToken
    architecture: UppercaseToken
    cpu_cores: int = Field(ge=1)
    memory_mb: int = Field(ge=1)
    artifact_locality: tuple[ContentHash, ...] = ()
    heartbeat_interval_seconds: int = Field(ge=1)
    schema_version: Literal[1] = 1


class WorkerRegistration(WireModel):
    """Wire-native registered remote worker identity and liveness.

    Trust requires channel authentication, not registration; stale workers
    (past ``heartbeat_expires_at``) and untrusted workers receive no
    assignments.
    """

    worker_id: Uuid7
    descriptor: WorkerCapabilityDescriptor
    endpoint: UriStr
    registered_at: UtcTimestamp
    last_heartbeat_at: UtcTimestamp
    heartbeat_expires_at: UtcTimestamp
    trusted: bool = False
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_heartbeat_window(self) -> WorkerRegistration:
        """Reject heartbeat timestamps outside the registration window.

        Returns:
            The validated registration.

        Raises:
            ValueError: ``last_heartbeat_at`` precedes ``registered_at`` or
                ``heartbeat_expires_at`` is not after ``last_heartbeat_at``.
        """
        if self.last_heartbeat_at < self.registered_at:
            raise ValueError("last_heartbeat_at must be at or after registered_at")
        if self.heartbeat_expires_at <= self.last_heartbeat_at:
            raise ValueError("heartbeat_expires_at must be after last_heartbeat_at")
        return self


class WorkerLease(WireModel):
    """Wire-native fenced job execution lease held by one worker.

    ``(job_id, attempt_no, fencing_token)`` is unique and a commit is
    accepted only for the current token before expiry; scoped job
    credentials are ``SecretRef`` identities, never values.
    """

    job_id: Uuid7
    attempt_no: int = Field(ge=1)
    worker_id: Uuid7
    worker_build_hash: ContentHash
    fencing_token: int = Field(ge=1)
    acquired_at: UtcTimestamp
    last_heartbeat_at: UtcTimestamp
    expires_at: UtcTimestamp
    heartbeat_interval_seconds: int = Field(ge=1)
    state: WorkerLeaseState
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_lease_window(self) -> WorkerLease:
        """Reject lease timestamps outside the acquisition window.

        Returns:
            The validated lease.

        Raises:
            ValueError: ``expires_at`` is not after ``acquired_at`` or
                ``last_heartbeat_at`` precedes ``acquired_at``.
        """
        if self.expires_at <= self.acquired_at:
            raise ValueError("expires_at must be after acquired_at")
        if self.last_heartbeat_at < self.acquired_at:
            raise ValueError("last_heartbeat_at must be at or after acquired_at")
        return self


class WorkerTaskEnvelope(WireModel):
    """Wire-native assignment envelope dispatching one task attempt.

    Reassignment to another compatible worker changes only ``envelope_id``,
    ``assigned_worker_id``, and ``assigned_at``; the input hashes stay
    invariant so seeds and canonical output are unchanged.
    """

    envelope_id: Uuid7
    task_run_id: Uuid7
    job_id: Uuid7
    attempt_no: int = Field(ge=1)
    fencing_token: int = Field(ge=1)
    assigned_worker_id: Uuid7
    assigned_at: UtcTimestamp
    input_hashes: tuple[ContentHash, ...] = ()
    locality_hints: tuple[ContentHash, ...] = ()
    schema_version: Literal[1] = 1


class ArtifactChunk(WireModel):
    """One content-addressed chunk of an artifact transfer plan."""

    index: int = Field(ge=0)
    offset_bytes: int = Field(ge=0)
    size_bytes: int = Field(ge=1)
    chunk_hash: ContentHash


class ArtifactManifest(WireModel):
    """Wire-native content-addressed artifact manifest and chunk plan.

    Chunk plans are sorted by ``index`` starting at 0 and contiguous from
    ``offset_bytes`` 0; commit additionally requires concatenating the
    chunk bytes to reproduce ``size_bytes`` and ``content_hash``. The
    byte-level hash reproduction is verified by the process layer;
    corruption or interruption never yields ``COMMITTED``.
    """

    artifact_id: Uuid7
    kind: NonEmptyStr
    content_hash: ContentHash
    size_bytes: int = Field(ge=0)
    media_type: NonEmptyStr
    # Artifact payload schema number per PROJECT §22.3, not the record
    # marker carried by ``schema_version``.
    artifact_schema_version: int = Field(ge=1)
    state: ResultState
    chunks: tuple[ArtifactChunk, ...] = ()
    created_at: UtcTimestamp
    committed_at: UtcTimestamp | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_chunk_plan_and_commit(self) -> ArtifactManifest:
        """Reject unordered chunk plans and inconsistent commit evidence.

        Returns:
            The validated manifest.

        Raises:
            ValueError: Chunk indices are not ``0..n-1`` in order, offsets
                are not contiguous from zero, ``committed_at`` presence
                contradicts the state, or a committed manifest's chunk
                bytes do not reproduce ``size_bytes``.
        """
        expected_offset = 0
        for position, chunk in enumerate(self.chunks):
            if chunk.index != position:
                raise ValueError("chunks must be sorted by index starting at 0")
            if chunk.offset_bytes != expected_offset:
                raise ValueError("chunks must be contiguous from offset_bytes 0")
            expected_offset += chunk.size_bytes
        if (self.committed_at is not None) != (self.state == "COMMITTED"):
            raise ValueError("committed_at is present exactly when state is COMMITTED")
        if self.state == "COMMITTED" and expected_offset != self.size_bytes:
            raise ValueError("committed chunk bytes must reproduce size_bytes")
        return self


class HostedWorkspaceContext(WireModel):
    """Wire-native isolation scope assignment for one hosted workspace.

    No two hosted contexts may share a value of the same scope kind; that
    cross-record uniqueness is enforced by the owning store, while the six
    scopes map one-to-one to the isolated concerns of
    FR-WS-ISOLATE_HOSTED_WORKSPACES.
    """

    workspace_id: Uuid7
    deployment_mode: DeploymentMode
    metadata_scope: NonEmptyStr
    artifact_scope: NonEmptyStr
    queue_scope: NonEmptyStr
    credential_scope: NonEmptyStr
    quota_scope: NonEmptyStr
    plugin_permission_scope: NonEmptyStr
    schema_version: Literal[1] = 1


class WorkspaceAuthorizationDecision(WireModel):
    """Wire-native fail-closed authorization decision for hosted access.

    Missing evidence or policy uncertainty yields ``DENY``; a ``DENY``
    outcome is a typed success result of ``HostWorkspacesCapability``,
    not a transport failure.
    """

    decision_id: Uuid7
    principal: PrincipalRef
    workspace_id: Uuid7
    action: NonEmptyStr
    outcome: AuthorizationOutcome
    reason: str = ""
    decided_at: UtcTimestamp
    expires_at: UtcTimestamp | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_reason_presence(self) -> WorkspaceAuthorizationDecision:
        """Reject reasons on allow and missing reasons on deny.

        Returns:
            The validated decision.

        Raises:
            ValueError: ``reason`` is nonempty for ``ALLOW`` or empty for
                ``DENY``.
        """
        if (self.outcome == "ALLOW") != (self.reason == ""):
            raise ValueError("reason is empty exactly when outcome is ALLOW")
        return self


class DistributeWorkersRequest(WireModel):
    """Operation-discriminated distributed worker pool request.

    ``REGISTER`` requires ``descriptor`` and ``endpoint`` and forbids the
    rest; ``AUTHENTICATE`` and ``HEARTBEAT`` require ``worker_id`` only;
    ``ACQUIRE_LEASE`` requires ``worker_id``, ``job_id``, and
    ``attempt_no``; ``RELEASE_LEASE`` additionally requires
    ``fencing_token``; ``ASSIGN_TASK`` requires ``job_id``, ``attempt_no``,
    and ``task_run_id`` with optional scheduler hints; ``PREPARE_TRANSFER``
    requires a STAGED ``artifact``; ``COMMIT_TRANSFER`` requires
    ``artifact_id``, ``job_id``, ``attempt_no``, and ``fencing_token``.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal[
        "REGISTER",
        "AUTHENTICATE",
        "HEARTBEAT",
        "ACQUIRE_LEASE",
        "RELEASE_LEASE",
        "ASSIGN_TASK",
        "PREPARE_TRANSFER",
        "COMMIT_TRANSFER",
    ]
    descriptor: WorkerCapabilityDescriptor | None = None
    endpoint: UriStr | None = None
    worker_id: Uuid7 | None = None
    job_id: Uuid7 | None = None
    attempt_no: int | None = Field(default=None, ge=1)
    fencing_token: int | None = Field(default=None, ge=1)
    task_run_id: Uuid7 | None = None
    required_capabilities: tuple[CapabilityIdentifier, ...] = ()
    locality_hints: tuple[ContentHash, ...] = ()
    artifact: ArtifactManifest | None = None
    artifact_id: Uuid7 | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> DistributeWorkersRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing, forbidden fields are
                set, or ``PREPARE_TRANSFER`` carries a non-STAGED artifact.
        """
        match self.operation:
            case "REGISTER":
                _require_present(
                    (("descriptor", self.descriptor), ("endpoint", self.endpoint))
                )
                _require_absent(
                    (
                        ("worker_id", self.worker_id),
                        ("job_id", self.job_id),
                        ("attempt_no", self.attempt_no),
                        ("fencing_token", self.fencing_token),
                        ("task_run_id", self.task_run_id),
                        ("artifact", self.artifact),
                        ("artifact_id", self.artifact_id),
                    )
                )
                _require_empty(
                    (
                        ("required_capabilities", self.required_capabilities),
                        ("locality_hints", self.locality_hints),
                    )
                )
            case "AUTHENTICATE" | "HEARTBEAT":
                _require_present((("worker_id", self.worker_id),))
                _require_absent(
                    (
                        ("descriptor", self.descriptor),
                        ("endpoint", self.endpoint),
                        ("job_id", self.job_id),
                        ("attempt_no", self.attempt_no),
                        ("fencing_token", self.fencing_token),
                        ("task_run_id", self.task_run_id),
                        ("artifact", self.artifact),
                        ("artifact_id", self.artifact_id),
                    )
                )
                _require_empty(
                    (
                        ("required_capabilities", self.required_capabilities),
                        ("locality_hints", self.locality_hints),
                    )
                )
            case "ACQUIRE_LEASE":
                _require_present(
                    (
                        ("worker_id", self.worker_id),
                        ("job_id", self.job_id),
                        ("attempt_no", self.attempt_no),
                    )
                )
                _require_absent(
                    (
                        ("descriptor", self.descriptor),
                        ("endpoint", self.endpoint),
                        ("fencing_token", self.fencing_token),
                        ("task_run_id", self.task_run_id),
                        ("artifact", self.artifact),
                        ("artifact_id", self.artifact_id),
                    )
                )
                _require_empty(
                    (
                        ("required_capabilities", self.required_capabilities),
                        ("locality_hints", self.locality_hints),
                    )
                )
            case "RELEASE_LEASE":
                _require_present(
                    (
                        ("worker_id", self.worker_id),
                        ("job_id", self.job_id),
                        ("attempt_no", self.attempt_no),
                        ("fencing_token", self.fencing_token),
                    )
                )
                _require_absent(
                    (
                        ("descriptor", self.descriptor),
                        ("endpoint", self.endpoint),
                        ("task_run_id", self.task_run_id),
                        ("artifact", self.artifact),
                        ("artifact_id", self.artifact_id),
                    )
                )
                _require_empty(
                    (
                        ("required_capabilities", self.required_capabilities),
                        ("locality_hints", self.locality_hints),
                    )
                )
            case "ASSIGN_TASK":
                _require_present(
                    (
                        ("job_id", self.job_id),
                        ("attempt_no", self.attempt_no),
                        ("task_run_id", self.task_run_id),
                    )
                )
                _require_absent(
                    (
                        ("descriptor", self.descriptor),
                        ("endpoint", self.endpoint),
                        ("worker_id", self.worker_id),
                        ("fencing_token", self.fencing_token),
                        ("artifact", self.artifact),
                        ("artifact_id", self.artifact_id),
                    )
                )
            case "PREPARE_TRANSFER":
                _require_present((("artifact", self.artifact),))
                _require_absent(
                    (
                        ("descriptor", self.descriptor),
                        ("endpoint", self.endpoint),
                        ("worker_id", self.worker_id),
                        ("job_id", self.job_id),
                        ("attempt_no", self.attempt_no),
                        ("fencing_token", self.fencing_token),
                        ("task_run_id", self.task_run_id),
                        ("artifact_id", self.artifact_id),
                    )
                )
                _require_empty(
                    (
                        ("required_capabilities", self.required_capabilities),
                        ("locality_hints", self.locality_hints),
                    )
                )
                if self.artifact is not None and self.artifact.state != "STAGED":
                    raise ValueError("PREPARE_TRANSFER requires a STAGED artifact")
            case "COMMIT_TRANSFER":
                _require_present(
                    (
                        ("artifact_id", self.artifact_id),
                        ("job_id", self.job_id),
                        ("attempt_no", self.attempt_no),
                        ("fencing_token", self.fencing_token),
                    )
                )
                _require_absent(
                    (
                        ("descriptor", self.descriptor),
                        ("endpoint", self.endpoint),
                        ("worker_id", self.worker_id),
                        ("task_run_id", self.task_run_id),
                        ("artifact", self.artifact),
                    )
                )
                _require_empty(
                    (
                        ("required_capabilities", self.required_capabilities),
                        ("locality_hints", self.locality_hints),
                    )
                )
        return self


class DistributeWorkersSuccess(WireModel):
    """Successful distributed worker pool operation result.

    ``registration`` is returned for REGISTER, AUTHENTICATE, and HEARTBEAT;
    ``lease`` for ACQUIRE_LEASE; ``envelope`` for ASSIGN_TASK; ``artifact``
    carries the STAGED chunk plan for PREPARE_TRANSFER and the COMMITTED
    manifest for COMMIT_TRANSFER.
    """

    outcome: Literal["SUCCESS"] = "SUCCESS"
    request_id: Uuid7
    result_version: Literal[1] = 1
    registration: WorkerRegistration | None = None
    lease: WorkerLease | None = None
    envelope: WorkerTaskEnvelope | None = None
    artifact: ArtifactManifest | None = None
    schema_version: Literal[1] = 1


class HostWorkspacesRequest(WireModel):
    """Operation-discriminated hosted workspace boundary request.

    ``PROVISION`` requires ``context``; ``DESCRIBE`` requires
    ``workspace_id``; ``AUTHORIZE`` requires ``workspace_id``,
    ``principal``, and ``action``.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["PROVISION", "DESCRIBE", "AUTHORIZE"]
    context: HostedWorkspaceContext | None = None
    workspace_id: Uuid7 | None = None
    principal: PrincipalRef | None = None
    action: NonEmptyStr | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> HostWorkspacesRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing or forbidden fields are
                set for the selected operation.
        """
        match self.operation:
            case "PROVISION":
                _require_present((("context", self.context),))
                _require_absent(
                    (
                        ("workspace_id", self.workspace_id),
                        ("principal", self.principal),
                        ("action", self.action),
                    )
                )
            case "DESCRIBE":
                _require_present((("workspace_id", self.workspace_id),))
                _require_absent(
                    (
                        ("context", self.context),
                        ("principal", self.principal),
                        ("action", self.action),
                    )
                )
            case "AUTHORIZE":
                _require_present(
                    (
                        ("workspace_id", self.workspace_id),
                        ("principal", self.principal),
                        ("action", self.action),
                    )
                )
                _require_absent((("context", self.context),))
        return self


class HostWorkspacesSuccess(WireModel):
    """Successful hosted workspace boundary operation result.

    ``context`` is returned for PROVISION and DESCRIBE; ``decision`` is
    returned for AUTHORIZE, where ``DENY`` is a typed success outcome and
    never a failure.
    """

    outcome: Literal["SUCCESS"] = "SUCCESS"
    request_id: Uuid7
    result_version: Literal[1] = 1
    context: HostedWorkspaceContext | None = None
    decision: WorkspaceAuthorizationDecision | None = None
    schema_version: Literal[1] = 1


# Wire projections register under their inventory names (``<Record>`` ->
# ``<Record>Wire``); wire-native and request/success records register
# directly. Nested components (``WorkspaceSettingsWire``,
# ``ServerRuntimeSettingsWire``, ``ServerRuntimeValidationWire``,
# ``BackupFileRecordWire``, ``ArtifactChunk``) are inline record parts, not
# registered public records.


class WatchlistItemRecord(WireModel):
    """One watched symbol inside an account watchlist.

    ``source_id`` names the provider-facing directory source; ``sort_order``
    is the caller's stable display order.
    """

    source_id: NonEmptyStr
    symbol: NonEmptyStr
    sort_order: int = Field(ge=0)
    asset_class: str = ""
    schema_version: Literal[1] = 1


class WatchlistRecord(WireModel):
    """One account-owned named, ordered collection of watched symbols."""

    watchlist_id: Uuid7
    account_id: NonEmptyStr
    name: Name1To160
    is_default: bool = False
    sort_order: int = Field(default=0, ge=0)
    items: tuple[WatchlistItemRecord, ...] = ()
    created_at: UtcTimestamp
    updated_at: UtcTimestamp
    schema_version: Literal[1] = 1


class ManageWatchlistsRequest(WireModel):
    """Operation-discriminated account watchlist request.

    LIST requires no operation fields; CREATE requires ``name``; UPDATE
    requires ``watchlist_id`` plus any of ``name``/``symbols``/
    ``is_default``/``sort_order``; DELETE requires ``watchlist_id``.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    account_id: NonEmptyStr
    operation: Literal["LIST", "CREATE", "UPDATE", "DELETE"]
    watchlist_id: Uuid7 | None = None
    name: Name1To160 | None = None
    symbols: tuple[NonEmptyStr, ...] = Field(default=(), max_length=500)
    is_default: bool | None = None
    sort_order: int | None = Field(default=None, ge=0)
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> ManageWatchlistsRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing or forbidden fields
                are set for the selected operation.
        """
        _validate_watchlists_operation(self)
        return self


def _forbid(request: ManageWatchlistsRequest, field_name: str) -> None:
    """Reject one forbidden operation field.

    Args:
        request: Request under validation.
        field_name: Field that must be absent.

    Raises:
        ValueError: The field is set for the selected operation.
    """
    if getattr(request, field_name) is not None:
        message = f"{request.operation} forbids {field_name}"
        raise ValueError(message)


def _validate_list(request: ManageWatchlistsRequest) -> None:
    """Enforce the LIST request shape.

    Args:
        request: Request under validation.

    Raises:
        ValueError: A forbidden field is set.
    """
    for field_name in ("watchlist_id", "name", "is_default", "sort_order"):
        _forbid(request, field_name)
    if request.symbols:
        raise ValueError("LIST forbids symbols")


def _validate_create(request: ManageWatchlistsRequest) -> None:
    """Enforce the CREATE request shape.

    Args:
        request: Request under validation.

    Raises:
        ValueError: The name is missing or the id is set.
    """
    if request.name is None:
        raise ValueError("CREATE requires name")
    _forbid(request, "watchlist_id")


def _validate_delete(request: ManageWatchlistsRequest) -> None:
    """Enforce the DELETE request shape.

    Args:
        request: Request under validation.

    Raises:
        ValueError: The id is missing or a mutable field is set.
    """
    if request.watchlist_id is None:
        raise ValueError("DELETE requires watchlist_id")
    for field_name in ("name", "is_default", "sort_order"):
        _forbid(request, field_name)
    if request.symbols:
        raise ValueError("DELETE forbids symbols")


def _validate_update(request: ManageWatchlistsRequest) -> None:
    """Enforce the UPDATE request shape.

    Args:
        request: Request under validation.

    Raises:
        ValueError: The id is missing or no field is present.
    """
    if request.watchlist_id is None:
        raise ValueError("UPDATE requires watchlist_id")
    if (
        request.name is None
        and not request.symbols
        and request.is_default is None
        and request.sort_order is None
    ):
        raise ValueError("UPDATE requires at least one field")


_OPERATION_VALIDATORS: dict[str, Callable[[ManageWatchlistsRequest], None]] = {
    "LIST": _validate_list,
    "CREATE": _validate_create,
    "UPDATE": _validate_update,
    "DELETE": _validate_delete,
}


def _validate_watchlists_operation(request: ManageWatchlistsRequest) -> None:
    """Enforce per-operation request shapes.

    Args:
        request: Request under validation.

    Raises:
        ValueError: Required fields are missing or forbidden fields are
            set for the selected operation.
    """
    validator = _OPERATION_VALIDATORS.get(request.operation)
    if validator is not None:
        validator(request)


class ManageWatchlistsSuccess(WireModel):
    """Successful account watchlist operation result.

    ``watchlists`` is returned for LIST, ``watchlist`` for CREATE and
    UPDATE, and ``deleted`` for DELETE.
    """

    outcome: Literal["SUCCESS"] = "SUCCESS"
    request_id: Uuid7
    result_version: Literal[1] = 1
    watchlists: tuple[WatchlistRecord, ...] = ()
    watchlist: WatchlistRecord | None = None
    deleted: bool = False
    schema_version: Literal[1] = 1


WIRE_MODELS: dict[str, type[WireModel]] = {
    "WorkspaceRef": WorkspaceRefWire,
    "WorkspaceVersion": WorkspaceVersionWire,
    "WorkspaceConfiguration": WorkspaceConfigurationWire,
    "RuntimeConfiguration": RuntimeConfigurationWire,
    "StorageGuardPolicy": StorageGuardPolicyWire,
    "WorkspaceWriterLease": WorkspaceWriterLease,
    "WorkspaceWriterFence": WorkspaceWriterFenceWire,
    "WorkspaceBackupManifest": WorkspaceBackupManifestWire,
    "WorkspaceRestorePlan": WorkspaceRestorePlanWire,
    "SecretRef": SecretRef,
    "PrincipalRef": PrincipalRef,
    "LocalSession": LocalSessionWire,
    "SystemHealth": SystemHealthWire,
    "SystemReadiness": SystemReadinessWire,
    "DiagnosticBundleRef": DiagnosticBundleRefWire,
    "DiagnosticBundleManifest": DiagnosticBundleManifestWire,
    "WorkerCapabilityDescriptor": WorkerCapabilityDescriptor,
    "WorkerRegistration": WorkerRegistration,
    "WorkerLease": WorkerLease,
    "WorkerTaskEnvelope": WorkerTaskEnvelope,
    "ArtifactManifest": ArtifactManifest,
    "HostedWorkspaceContext": HostedWorkspaceContext,
    "WorkspaceAuthorizationDecision": WorkspaceAuthorizationDecision,
    "DistributeWorkersRequest": DistributeWorkersRequest,
    "DistributeWorkersSuccess": DistributeWorkersSuccess,
    "HostWorkspacesRequest": HostWorkspacesRequest,
    "HostWorkspacesSuccess": HostWorkspacesSuccess,
    "WatchlistItemRecord": WatchlistItemRecord,
    "WatchlistRecord": WatchlistRecord,
    "ManageWatchlistsRequest": ManageWatchlistsRequest,
    "ManageWatchlistsSuccess": ManageWatchlistsSuccess,
}
