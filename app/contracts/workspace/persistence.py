"""Public contract for bounded feature-owned persistence execution.

The persistence capability lets stateful features execute transactions, apply
schema migrations, and retain immutable append-only evidence scoped strictly to
their declared namespace without receiving unrestricted database connections or
interfering with other features' state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol, runtime_checkable


class PersistenceOperation(StrEnum):
    """Operations supported by ``workspace.persistence@1``."""

    EXECUTE_TRANSACTION = "EXECUTE_TRANSACTION"
    APPLY_MIGRATIONS = "APPLY_MIGRATIONS"
    APPEND_EVIDENCE = "APPEND_EVIDENCE"
    EXPORT_EVIDENCE = "EXPORT_EVIDENCE"
    REGISTER_NAMESPACE = "REGISTER_NAMESPACE"


@dataclass(frozen=True, slots=True)
class NamespaceRegistration:
    """Declared namespace boundaries for a stateful feature."""

    namespace: str
    allowed_tables: tuple[str, ...] = ()
    evidence_tables: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Validate namespace declaration.

        Raises:
            ValueError: If namespace is empty or whitespace.
        """
        if not self.namespace.strip():
            raise ValueError("namespace must be non-empty")


@dataclass(frozen=True, slots=True)
class FeatureMigration:
    """One additive schema migration step."""

    version: int
    name: str
    sql: str
    checksum: str

    def __post_init__(self) -> None:
        """Validate migration attributes.

        Raises:
            ValueError: If version is not positive or fields are empty.
        """
        if self.version < 1:
            raise ValueError("migration version must be positive")
        if not self.name.strip():
            raise ValueError("migration name must be non-empty")
        if not self.sql.strip():
            raise ValueError("migration sql must be non-empty")
        if not self.checksum.strip():
            raise ValueError("migration checksum must be non-empty")


@dataclass(frozen=True, slots=True)
class FeatureMigrationManifest:
    """Ordered additive schema migration manifest for a feature namespace."""

    namespace: str
    migrations: tuple[FeatureMigration, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        """Validate migration ordering.

        Raises:
            ValueError: If namespace is empty or versions are not strictly ascending.
        """
        if not self.namespace.strip():
            raise ValueError("namespace must be non-empty")
        previous_version = 0
        for migration in self.migrations:
            if migration.version <= previous_version:
                msg = (
                    f"Migrations must be strictly ascending: "
                    f"{migration.version} <= {previous_version}"
                )
                raise ValueError(msg)
            previous_version = migration.version


@dataclass(frozen=True, slots=True)
class PersistenceStatement:
    """One SQL statement with bound positional parameters."""

    sql: str
    parameters: tuple[Any, ...] = ()

    def __post_init__(self) -> None:
        """Validate statement.

        Raises:
            ValueError: If sql is empty.
        """
        if not self.sql.strip():
            raise ValueError("statement sql must be non-empty")


@dataclass(frozen=True, slots=True)
class PersistenceTransactionRequest:
    """Request to execute one namespace-bound transaction."""

    request_id: str
    actor_id: str
    account_id: str
    workspace_path: Path
    namespace: str
    statements: tuple[PersistenceStatement, ...]
    expected_revision: int | None = None
    schema_version: int = 1

    def __post_init__(self) -> None:
        """Validate transaction request shape.

        Raises:
            ValueError: If any identifier is empty or invalid.
        """
        for field_name in ("request_id", "actor_id", "account_id", "namespace"):
            if not getattr(self, field_name).strip():
                msg = f"{field_name} must be non-empty"
                raise ValueError(msg)
        if self.schema_version != 1:
            raise ValueError("schema_version must be 1")
        if self.expected_revision is not None and self.expected_revision < 1:
            raise ValueError("expected_revision must be positive")
        if not self.statements:
            raise ValueError("statements must not be empty")


@dataclass(frozen=True, slots=True)
class PersistenceTransactionResult:
    """Outcome of an executed namespace-bound transaction."""

    request_id: str
    namespace: str
    rows_affected: int
    new_revision: int
    results: tuple[tuple[dict[str, Any], ...], ...] = ()
    schema_version: int = 1


@dataclass(frozen=True, slots=True)
class EvidenceRecord:
    """Immutable append-only evidence record."""

    evidence_id: str
    workspace_id: str
    namespace: str
    content_hash: str
    payload_json: str
    created_at: str
    sequence: int = 0

    def __post_init__(self) -> None:
        """Validate evidence record attributes.

        Raises:
            ValueError: If required fields are empty.
        """
        for field_name in (
            "evidence_id",
            "workspace_id",
            "namespace",
            "content_hash",
            "payload_json",
            "created_at",
        ):
            if not getattr(self, field_name).strip():
                msg = f"{field_name} must be non-empty"
                raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class ExportEvidenceRequest:
    """Request for bounded, stable-ordered paged evidence export."""

    workspace_path: Path
    namespace: str
    limit: int = 100
    offset: int = 0

    def __post_init__(self) -> None:
        """Validate export request parameters.

        Raises:
            ValueError: If namespace is empty, limit < 1, or offset < 0.
        """
        if not self.namespace.strip():
            raise ValueError("namespace must be non-empty")
        if self.limit < 1:
            raise ValueError("limit must be positive")
        if self.offset < 0:
            raise ValueError("offset must be non-negative")


@dataclass(frozen=True, slots=True)
class ExportEvidenceResult:
    """Paged evidence export result."""

    namespace: str
    records: tuple[EvidenceRecord, ...]
    total_count: int
    has_more: bool
    limit: int
    offset: int


@dataclass(frozen=True, slots=True)
class MigrationResult:
    """Outcome of applying a migration manifest."""

    namespace: str
    current_version: int
    applied_versions: tuple[int, ...]


@runtime_checkable
class PersistenceCapability(Protocol):
    """Capability protocol for bounded feature-owned persistence execution."""

    def register_namespace(self, registration: NamespaceRegistration) -> None:
        """Register allowed and evidence tables for a caller namespace.

        Args:
            registration: Declared namespace and table boundaries.
        """
        ...

    def execute_transaction(
        self,
        request: PersistenceTransactionRequest,
    ) -> PersistenceTransactionResult:
        """Execute a namespace-bound transaction with idempotency and optimistic locks.

        Args:
            request: Validated transaction request.

        Returns:
            Transaction execution outcome with affected row count and new revision.

        Raises:
            NamespaceAccessDeniedError: If undeclared tables/namespaces are accessed.
            RevisionConflictError: If expected_revision does not match current state.
            EvidenceImmutableError: If an UPDATE or DELETE targets an evidence table.
            WorkspaceError: If storage or execution errors occur.
        """
        ...

    def apply_migrations(
        self,
        workspace_path: Path,
        manifest: FeatureMigrationManifest,
    ) -> MigrationResult:
        """Apply ordered additive migrations with checksum verification.

        Args:
            workspace_path: Path to the workspace root.
            manifest: Ordered migration manifest for the namespace.

        Returns:
            Migration result indicating current version and newly applied versions.

        Raises:
            MigrationChecksumError: If an applied migration has a changed checksum.
            WorkspaceMigrationError: If a migration script fails to execute.
        """
        ...

    def append_evidence(
        self,
        workspace_path: Path,
        namespace: str,
        evidence: EvidenceRecord,
    ) -> EvidenceRecord:
        """Append an immutable evidence record.

        Args:
            workspace_path: Path to the workspace root.
            namespace: Declaring feature namespace.
            evidence: Evidence record to append.

        Returns:
            The stored evidence record with assigned monotonic sequence number.

        Raises:
            NamespaceAccessDeniedError: If namespace is undeclared.
            EvidenceImmutableError: If an existing evidence ID is overwritten.
        """
        ...

    def export_evidence(
        self,
        request: ExportEvidenceRequest,
    ) -> ExportEvidenceResult:
        """Return bounded, stable-ordered paged evidence within workspace scope.

        Args:
            request: Export request specifying namespace, limit, and offset.

        Returns:
            Paged export result.

        Raises:
            NamespaceAccessDeniedError: If namespace is undeclared.
            WorkspaceNotFoundError: If workspace does not exist.
        """
        ...
