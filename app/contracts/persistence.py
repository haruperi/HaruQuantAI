"""Public contracts, protocols, DTOs, and capabilities for the Persistence domain.

Purpose:
    Defines the public boundaries, immutable data transfer objects, typed
    protocols, capability tokens, and error types for SQLite database lifecycles,
    forward schema migrations, hot point-in-time snapshots, immutable
    content-addressed artifacts, reference-safe retention, project-scoped
    databanks, similarity filtering, persisted column views, and partitioned
    columnar Parquet market data storage.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from app.kernel.capability import Capability

# ---------------------------------------------------------------------------
# Capability Tokens
# ---------------------------------------------------------------------------

DATABASE_SERVICE: Capability[DatabaseService] = Capability(
    name="persistence.database",
    major=1,
    description=(
        "SQLite WAL lifecycle, parameterized transactions, and connection management"
    ),
)

MIGRATION_SERVICE: Capability[MigrationService] = Capability(
    name="persistence.migrations",
    major=1,
    description=(
        "Forward schema migrations discovery, checksum verification, and execution"
    ),
)

SNAPSHOT_SERVICE: Capability[SnapshotService] = Capability(
    name="persistence.snapshots",
    major=1,
    description=("Point-in-time database hot snapshots and backup set management"),
)

ARTIFACT_STORE: Capability[ArtifactStore] = Capability(
    name="persistence.artifacts",
    major=1,
    description=(
        "Immutable content-addressed artifact catalog, staging, and package bundles"
    ),
)

RETENTION_SERVICE: Capability[RetentionService] = Capability(
    name="persistence.retention",
    major=1,
    description=(
        "Reference-safe retention graph evaluation and audited purge planning"
    ),
)

DATABANK_STORE: Capability[DatabankStore] = Capability(
    name="persistence.databanks",
    major=1,
    description=(
        "Project databanks, memberships, ranking, similarity dismissal, and"
        " column views"
    ),
)

PARQUET_STORE_SERVICE: Capability[ParquetStoreService] = Capability(
    name="persistence.parquet",
    major=1,
    description=(
        "Partitioned columnar market data time-series storage with Zstd compression"
    ),
)

# ---------------------------------------------------------------------------
# Enums and Value Types
# ---------------------------------------------------------------------------


class AutoSyncPolicy(StrEnum):
    """Synchronization intervals for databanks and project files."""

    NEVER = "never"
    HOURLY = "hourly"
    EVERY_10_MINUTES = "every_10_minutes"
    DAILY = "daily"


class RankingDirection(StrEnum):
    """Direction for ranking and metric sorting."""

    DESCENDING = "descending"
    ASCENDING = "ascending"


class SampleType(StrEnum):
    """Evaluation sample boundaries matching SQX databank view column types."""

    FULL_SAMPLE = "full_sample"
    IN_SAMPLE = "in_sample"
    OUT_OF_SAMPLE = "out_of_sample"


# ---------------------------------------------------------------------------
# Data Transfer Objects (Frozen Dataclasses)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ArtifactMetadata:
    """Metadata describing an immutable stored artifact."""

    media_type: str
    description: str = ""
    author: str = "system"
    tags: tuple[str, ...] = ()
    custom: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ArtifactRecord:
    """Durable receipt and metadata for a cataloged immutable artifact."""

    artifact_id: str
    sha256_hash: str
    media_type: str
    size_bytes: int
    created_at_utc: datetime
    metadata: ArtifactMetadata = field(
        default_factory=lambda: ArtifactMetadata(media_type="application/octet-stream")
    )
    parent_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ArtifactManifest:
    """Manifest describing an exported portable bundle of artifacts."""

    bundle_version: int
    created_at_utc: datetime
    root_artifact_id: str
    artifacts: tuple[ArtifactRecord, ...]


@dataclass(frozen=True, slots=True)
class ColumnConfig:
    """Column definition for databank view projection."""

    name: str
    metric_key: str
    sample_type: SampleType = SampleType.FULL_SAMPLE
    format_spec: str = "{:.2f}"
    is_visible: bool = True
    sort_priority: int | None = None
    sort_direction: RankingDirection = RankingDirection.DESCENDING


@dataclass(frozen=True, slots=True)
class DatabankViewConfig:
    """Persisted configuration for a databank column projection view."""

    view_name: str
    scope: str = "global"
    columns: tuple[ColumnConfig, ...] = ()
    updated_at_utc: datetime = field(
        default_factory=lambda: datetime.now().astimezone()
    )


@dataclass(frozen=True, slots=True)
class SimilarityProfile:
    """Profile parameters for comparing and dismissing similar strategies."""

    name: str = "default_5pct"
    tolerance_pct: float = 5.0
    compare_net_profit: bool = True
    compare_trade_count: bool = True
    compare_drawdown: bool = True
    sample_type: SampleType = SampleType.FULL_SAMPLE


@dataclass(frozen=True, slots=True)
class SimilarityMatchResult:
    """Result of evaluating a candidate strategy against existing members."""

    is_similar: bool
    matched_artifact_id: str | None = None
    candidate_fitness: float = 0.0
    matched_fitness: float = 0.0
    should_admit_candidate: bool = False


@dataclass(frozen=True, slots=True)
class DatabankRecord:
    """Record describing a configured databank inside a project."""

    project_name: str
    databank_name: str
    capacity: int = 1000
    default_view: str = "Default"
    auto_sync_policy: AutoSyncPolicy = AutoSyncPolicy.NEVER
    member_count: int = 0
    created_at_utc: datetime = field(
        default_factory=lambda: datetime.now().astimezone()
    )


@dataclass(frozen=True, slots=True)
class DatabankMemberRecord:
    """Membership entry linking an immutable artifact to a databank."""

    project_name: str
    databank_name: str
    artifact_id: str
    fitness: float
    ranking_value: float
    metrics: Mapping[str, float]
    annotations: Mapping[str, Any] = field(default_factory=dict)
    added_at_utc: datetime = field(default_factory=lambda: datetime.now().astimezone())


@dataclass(frozen=True, slots=True)
class MigrationRecord:
    """Record of a schema migration applied to the control-plane database."""

    version: int
    name: str
    checksum: str
    applied_at_utc: datetime


@dataclass(frozen=True, slots=True)
class SnapshotRecord:
    """Receipt for an atomic point-in-time SQLite hot snapshot."""

    snapshot_id: str
    path: Path
    size_bytes: int
    checksum_sha256: str
    label: str
    created_at_utc: datetime


@dataclass(frozen=True, slots=True)
class RetentionPlan:
    """Plan detailing eligible vs blocked artifacts for a purge operation."""

    target_artifact_ids: tuple[str, ...]
    eligible_artifact_ids: tuple[str, ...]
    blocked_artifact_ids: tuple[str, ...]
    blocking_reasons: Mapping[str, tuple[str, ...]]


@dataclass(frozen=True, slots=True)
class RetentionPurgeReport:
    """Audit report generated after executing a retention purge."""

    operation_id: str
    purged_count: int
    reclaimed_bytes: int
    purged_artifact_ids: tuple[str, ...]
    executed_at_utc: datetime


@dataclass(frozen=True, slots=True)
class BarRecord:
    """Normalized OHLCV bar for columnar Parquet market data storage."""

    timestamp_utc: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    ticks: int = 0


@dataclass(frozen=True, slots=True)
class TickRecord:
    """Normalized bid/ask tick for columnar Parquet market data storage."""

    timestamp_utc: datetime
    bid: float
    ask: float
    bid_volume: float = 0.0
    ask_volume: float = 0.0


@dataclass(frozen=True, slots=True)
class MarketSeriesPartition:
    """Partition description for columnar Parquet files."""

    symbol: str
    timeframe: str
    year: int
    file_path: Path
    record_count: int
    size_bytes: int
    min_timestamp_utc: datetime
    max_timestamp_utc: datetime


# ---------------------------------------------------------------------------
# Protocols (Public Service Contracts)
# ---------------------------------------------------------------------------


@runtime_checkable
class DatabaseService(Protocol):
    """Protocol for SQLite control-plane lifecycle, queries, and transactions."""

    @property
    def database_path(self) -> Path:
        """Return the active SQLite database path."""
        ...

    def execute_query(
        self, sql: str, params: tuple[Any, ...] = ()
    ) -> list[dict[str, Any]]:
        """Execute a read query and return row dictionaries."""
        ...

    def execute_mutation(self, sql: str, params: tuple[Any, ...] = ()) -> int:
        """Execute an insert, update, or delete and return rows affected."""
        ...

    def execute_script(self, sql_script: str) -> None:
        """Execute multiple semicolon-delimited SQL statements."""
        ...

    def transaction(self) -> AbstractContextManager[Any]:
        """Enter a managed transactional context."""
        ...

    def checkpoint(self) -> None:
        """Force a WAL checkpoint to flush writes into the main database."""
        ...

    def hot_snapshot(self, destination_path: Path) -> None:
        """Create an atomic SQLite point-in-time snapshot using VACUUM INTO."""
        ...


@runtime_checkable
class MigrationService(Protocol):
    """Protocol for forward schema migrations and database upgrades."""

    def get_applied_migrations(self) -> list[MigrationRecord]:
        """Return list of applied schema migrations in version order."""
        ...

    def get_pending_migrations(self) -> list[MigrationRecord]:
        """Return list of pending unapplied schema migrations."""
        ...

    def apply_all(self) -> list[MigrationRecord]:
        """Apply all pending migrations sequentially within transactions."""
        ...

    def current_version(self) -> int:
        """Return the current schema version integer."""
        ...


@runtime_checkable
class SnapshotService(Protocol):
    """Protocol for hot point-in-time SQLite snapshots and backup sets."""

    def create_snapshot(
        self, destination_path: Path | None = None, label: str = ""
    ) -> SnapshotRecord:
        """Create an atomic VACUUM INTO hot snapshot."""
        ...

    def list_snapshots(self) -> list[SnapshotRecord]:
        """List available snapshots ordered by creation timestamp."""
        ...

    def restore_snapshot(
        self, snapshot_path: Path, expected_checksum_sha256: str | None = None
    ) -> None:
        """Restore the database from a validated snapshot file."""
        ...


@runtime_checkable
class ArtifactStore(Protocol):
    """Protocol for immutable content-addressed artifact catalog and packaging."""

    def stage_artifact(
        self,
        payload: bytes,
        media_type: str,
        metadata: Mapping[str, Any] | None = None,
    ) -> str:
        """Stage an artifact payload in isolation and return staging token."""
        ...

    def promote_artifact(
        self,
        staging_id: str,
        artifact_id: str | None = None,
        parent_ids: Sequence[str] = (),
    ) -> ArtifactRecord:
        """Validate, hash, promote, and catalog a staged artifact atomically."""
        ...

    def store_artifact(
        self,
        payload: bytes,
        media_type: str,
        metadata: Mapping[str, Any] | None = None,
        parent_ids: Sequence[str] = (),
    ) -> ArtifactRecord:
        """Stage and promote an artifact atomically in a single operation."""
        ...

    def get_artifact(self, artifact_id: str) -> ArtifactRecord | None:
        """Retrieve artifact receipt and metadata by unique ID."""
        ...

    def read_artifact_bytes(self, artifact_id: str) -> bytes:
        """Read the raw immutable content bytes of an artifact."""
        ...

    def verify_checksum(self, artifact_id: str) -> bool:
        """Verify that stored file content matches its cataloged SHA-256 hash."""
        ...

    def get_lineage(self, artifact_id: str) -> list[str]:
        """Return list of parent artifact IDs."""
        ...

    def export_bundle(self, artifact_ids: Sequence[str], target_path: Path) -> Path:
        """Export artifacts and manifest into a portable .zip package bundle."""
        ...

    def import_bundle(self, bundle_path: Path) -> list[ArtifactRecord]:
        """Import, verify, and catalog artifacts from a portable package bundle."""
        ...


@runtime_checkable
class RetentionService(Protocol):
    """Protocol for reference-safe retention graph checking and purge planning."""

    def plan_purge(
        self,
        target_artifact_ids: Sequence[str],
        active_references: Mapping[str, Sequence[str]] | None = None,
    ) -> RetentionPlan:
        """Plan a purge operation, evaluating dependencies and blocking reasons."""
        ...

    def execute_purge(
        self, plan: RetentionPlan, dry_run: bool = False
    ) -> RetentionPurgeReport:
        """Execute or dry-run an audited purge of eligible artifacts."""
        ...

    def get_audit_history(
        self, operation_id: str | None = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        """Retrieve historical audit records for executed purge operations."""
        ...


@runtime_checkable
class DatabankStore(Protocol):
    """Protocol for project-scoped databanks, ranking, similarity, and views."""

    def create_databank(
        self,
        project_name: str,
        databank_name: str,
        capacity: int = 1000,
        default_view: str = "Default",
        auto_sync_policy: AutoSyncPolicy = AutoSyncPolicy.NEVER,
    ) -> DatabankRecord:
        """Create a new project databank."""
        ...

    def get_databank(
        self, project_name: str, databank_name: str
    ) -> DatabankRecord | None:
        """Get databank configuration by project and databank name."""
        ...

    def list_databanks(self, project_name: str) -> list[DatabankRecord]:
        """List all databanks within a project."""
        ...

    def delete_databank(self, project_name: str, databank_name: str) -> bool:
        """Delete a databank and all its memberships."""
        ...

    def clear_databank(self, project_name: str, databank_name: str) -> int:
        """Clear all memberships from a databank without deleting the databank."""
        ...

    def add_member(
        self,
        project_name: str,
        databank_name: str,
        artifact_id: str,
        *,
        fitness: float,
        ranking_value: float,
        metrics: Mapping[str, float],
        annotations: Mapping[str, Any] | None = None,
        similarity_profile: SimilarityProfile | None = None,
    ) -> DatabankMemberRecord | None:
        """Add member with capacity gating, ranking, and similarity evaluation."""
        ...

    def remove_member(
        self, project_name: str, databank_name: str, artifact_id: str
    ) -> bool:
        """Remove a strategy member from a databank."""
        ...

    def copy_member(
        self,
        source_project: str,
        source_databank: str,
        *,
        target_project: str,
        target_databank: str,
        artifact_id: str,
    ) -> DatabankMemberRecord:
        """Copy a member to target databank without duplicating artifact content."""
        ...

    def move_member(
        self,
        source_project: str,
        source_databank: str,
        *,
        target_project: str,
        target_databank: str,
        artifact_id: str,
    ) -> DatabankMemberRecord:
        """Atomically move member from source to target databank."""
        ...

    def get_members(
        self,
        project_name: str,
        databank_name: str,
        limit: int | None = None,
    ) -> list[DatabankMemberRecord]:
        """Return databank members ordered by ranking value."""
        ...

    def evaluate_similarity(
        self,
        project_name: str,
        databank_name: str,
        candidate_metrics: Mapping[str, float],
        profile: SimilarityProfile,
    ) -> SimilarityMatchResult:
        """Check candidate strategy against databank members for metric similarity."""
        ...

    def save_view(self, view_config: DatabankViewConfig) -> None:
        """Save a databank column projection view."""
        ...

    def get_view(self, view_name: str) -> DatabankViewConfig | None:
        """Retrieve a databank column view by name."""
        ...

    def list_views(self) -> list[DatabankViewConfig]:
        """List all saved databank views."""
        ...


@runtime_checkable
class ParquetStoreService(Protocol):
    """Protocol for partitioned columnar market data time-series store."""

    def write_bars(self, symbol: str, timeframe: str, bars: Sequence[BarRecord]) -> int:
        """Write bars into partitioned columnar Parquet files."""
        ...

    def read_bars(
        self,
        symbol: str,
        timeframe: str,
        *,
        start_time_utc: datetime | None = None,
        end_time_utc: datetime | None = None,
        limit: int | None = None,
    ) -> list[BarRecord]:
        """Read bars for a symbol and timeframe within optional time range."""
        ...

    def write_ticks(self, symbol: str, ticks: Sequence[TickRecord]) -> int:
        """Write ticks into partitioned columnar Parquet files."""
        ...

    def read_ticks(
        self,
        symbol: str,
        *,
        start_time_utc: datetime | None = None,
        end_time_utc: datetime | None = None,
        limit: int | None = None,
    ) -> list[TickRecord]:
        """Read ticks for a symbol within optional time range."""
        ...

    def list_partitions(self) -> list[MarketSeriesPartition]:
        """List all discovered market series partitions."""
        ...

    def delete_partition(self, symbol: str, timeframe: str, year: int) -> bool:
        """Delete a single year partition for symbol and timeframe."""
        ...


# ---------------------------------------------------------------------------
# Error Hierarchy
# ---------------------------------------------------------------------------


class PersistenceError(Exception):
    """Base exception for all persistence domain operations."""


class DatabaseConnectionError(PersistenceError):
    """Raised when database connection acquisition or initialization fails."""


class MigrationError(PersistenceError):
    """Raised when schema migration execution or checksum verification fails."""


class SnapshotError(PersistenceError):
    """Raised when hot snapshot creation or restoration fails."""


class ArtifactNotFoundError(PersistenceError):
    """Raised when an artifact ID does not resolve in the catalog."""


class ArtifactCorruptError(PersistenceError):
    """Raised when stored artifact content fails checksum verification."""


class ArtifactIntegrityError(PersistenceError):
    """Raised when artifact promotion or bundling violates integrity constraints."""


class DatabankNotFoundError(PersistenceError):
    """Raised when a requested databank does not exist."""


class DatabankCapacityError(PersistenceError):
    """Raised when databank capacity constraints are violated."""


class DuplicateMemberError(PersistenceError):
    """Raised when attempting to add an already existing member to a databank."""


class RetentionReferenceBlockedError(PersistenceError):
    """Raised when an artifact purge is blocked by active references."""


class ParquetStorageError(PersistenceError):
    """Raised when Parquet file I/O or schema conversion fails."""
