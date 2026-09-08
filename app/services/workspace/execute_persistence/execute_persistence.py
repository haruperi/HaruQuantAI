"""Bounded SQLite persistence service for feature-owned transactions.

Owns bounded transaction execution, ordered additive migrations, and append-only
evidence custody. Enforces strict namespace table fencing, optimistic revision
checks, and evidence immutability.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import sqlite3
from pathlib import Path
from typing import Any

from app.composition.logging import get_logger
from app.contracts.workspace.errors import (
    EvidenceImmutableError,
    MigrationChecksumError,
    NamespaceAccessDeniedError,
    PersistenceError,
    RevisionConflictError,
    WorkspaceMigrationError,
    WorkspaceNotFoundError,
    WorkspaceStorageError,
)
from app.contracts.workspace.persistence import (
    EvidenceRecord,
    ExportEvidenceRequest,
    ExportEvidenceResult,
    FeatureMigrationManifest,
    MigrationResult,
    NamespaceRegistration,
    PersistenceTransactionRequest,
    PersistenceTransactionResult,
)
from app.services.workspace.execute_persistence.config import (
    ExecutePersistenceConfig,
)

logger = get_logger(__name__)

_SQL_TABLE_PATTERN = re.compile(
    r"\b(?:FROM|INTO|UPDATE|JOIN|TABLE)\s+([A-Za-z0-9_]+)",
    re.IGNORECASE,
)
_SQL_DISALLOWED_EVIDENCE_OPS = re.compile(
    r"^\s*(?:UPDATE|DELETE|DROP|TRUNCATE)\b",
    re.IGNORECASE,
)

_SQL_INTERNAL_SCHEMA = """
CREATE TABLE IF NOT EXISTS _persistence_migrations (
    namespace TEXT NOT NULL,
    version INTEGER NOT NULL,
    name TEXT NOT NULL,
    applied_at TEXT NOT NULL,
    checksum TEXT NOT NULL,
    PRIMARY KEY (namespace, version)
);

CREATE TABLE IF NOT EXISTS _persistence_revisions (
    namespace TEXT PRIMARY KEY,
    revision INTEGER NOT NULL DEFAULT 1,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS _persistence_idempotency (
    request_id TEXT PRIMARY KEY,
    namespace TEXT NOT NULL,
    fingerprint TEXT NOT NULL,
    result_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS _persistence_evidence (
    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    evidence_id TEXT NOT NULL UNIQUE,
    workspace_id TEXT NOT NULL,
    namespace TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TRIGGER IF NOT EXISTS _trg_evidence_no_update
BEFORE UPDATE ON _persistence_evidence
BEGIN
    SELECT RAISE(ABORT, 'Evidence records are immutable and cannot be updated');
END;

CREATE TRIGGER IF NOT EXISTS _trg_evidence_no_delete
BEFORE DELETE ON _persistence_evidence
BEGIN
    SELECT RAISE(ABORT, 'Evidence records are immutable and cannot be deleted');
END;
"""

_SQL_GET_IDEMPOTENCY = (
    "SELECT result_json FROM _persistence_idempotency WHERE request_id = ?"
)

_SQL_GET_REVISION = "SELECT revision FROM _persistence_revisions WHERE namespace = ?"

_SQL_UPSERT_REVISION = """
INSERT INTO _persistence_revisions (namespace, revision, updated_at)
VALUES (?, ?, ?)
ON CONFLICT(namespace) DO UPDATE SET
    revision = ?,
    updated_at = ?
"""

_SQL_INSERT_IDEMPOTENCY = """
INSERT INTO _persistence_idempotency
(request_id, namespace, fingerprint, result_json, created_at)
VALUES (?, ?, ?, ?, ?)
"""

_SQL_GET_MIGRATIONS = """
SELECT version, checksum FROM _persistence_migrations
WHERE namespace = ?
ORDER BY version ASC
"""

_SQL_INSERT_MIGRATION = """
INSERT INTO _persistence_migrations
(namespace, version, name, applied_at, checksum)
VALUES (?, ?, ?, ?, ?)
"""

_SQL_CHECK_EVIDENCE_EXISTS = (
    "SELECT evidence_id FROM _persistence_evidence WHERE evidence_id = ?"
)

_SQL_INSERT_EVIDENCE = """
INSERT INTO _persistence_evidence
(evidence_id, workspace_id, namespace, content_hash, payload_json, created_at)
VALUES (?, ?, ?, ?, ?, ?)
"""

_SQL_COUNT_EVIDENCE = """
SELECT COUNT(*) as count FROM _persistence_evidence
WHERE namespace = ? AND workspace_id = ?
"""

_SQL_EXPORT_EVIDENCE = """
SELECT
    evidence_id, workspace_id, namespace, content_hash,
    payload_json, created_at, sequence
FROM _persistence_evidence
WHERE namespace = ? AND workspace_id = ?
ORDER BY sequence ASC
LIMIT ? OFFSET ?
"""


def _utc_now_iso() -> str:
    """Return an ISO-8601 UTC timestamp."""
    return dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _db_path(workspace_path: Path) -> Path:
    """Return the canonical database path for persistence execution."""
    if workspace_path.suffix == ".db":
        return workspace_path
    central_db = workspace_path / "database" / "haruquantai.db"
    if central_db.exists():
        return central_db
    return workspace_path / "haruquantai.db"


class ExecutePersistenceService:
    """Bounded transaction and migration service for stateful workspace features."""

    def __init__(self, config: ExecutePersistenceConfig | None = None) -> None:
        """Initialize the persistence service with bounded configuration.

        Args:
            config: Runtime configuration or defaults.
        """
        self._config = config or ExecutePersistenceConfig()
        self._registrations: dict[str, NamespaceRegistration] = {}

    def close(self) -> None:
        """Release any held resources upon feature disposal."""
        self._registrations.clear()

    def _connect(self, db_path: Path) -> sqlite3.Connection:
        """Establish a configured SQLite connection in WAL mode.

        Args:
            db_path: Path to the SQLite database file.

        Returns:
            Configured sqlite3 connection.

        Raises:
            WorkspaceStorageError: If connection cannot be established.
        """
        if not db_path.parent.exists():
            db_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            conn = sqlite3.connect(
                str(db_path),
                timeout=self._config.busy_timeout_seconds,
            )
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys=ON")
            timeout_ms = int(self._config.busy_timeout_seconds * 1000)
            conn.execute(f"PRAGMA busy_timeout={timeout_ms}")
            conn.execute("PRAGMA journal_mode=WAL")
            self._ensure_internal_schema(conn)
            return conn
        except sqlite3.Error as error:
            msg = f"Database connection failed: {error}"
            raise WorkspaceStorageError(msg) from error

    def _ensure_internal_schema(self, connection: sqlite3.Connection) -> None:
        """Create internal persistence and evidence tables if not present."""
        with connection:
            connection.executescript(_SQL_INTERNAL_SCHEMA)

    def _get_workspace_id(
        self,
        connection: sqlite3.Connection,
        default_path: Path,
    ) -> str:
        """Look up workspace ID from the metadata table or derive from path.

        Args:
            connection: SQLite connection.
            default_path: Fallback path.

        Returns:
            Resolved workspace ID string.
        """
        try:
            cursor = connection.execute("SELECT id FROM workspace LIMIT 1")
            row = cursor.fetchone()
            if row and row["id"]:
                return str(row["id"])
        except sqlite3.Error:
            pass
        return default_path.name

    def register_namespace(self, registration: NamespaceRegistration) -> None:
        """Register namespace and allowed/evidence table boundaries.

        Args:
            registration: Declared namespace and table boundaries.
        """
        self._registrations[registration.namespace] = registration

    def _extract_tables(self, sql: str) -> set[str]:
        """Extract referenced table names from a SQL statement.

        Args:
            sql: SQL statement to inspect.

        Returns:
            Set of extracted table names in lowercase.
        """
        matches = _SQL_TABLE_PATTERN.findall(sql)
        tables: set[str] = set()
        for match in matches:
            clean = match.strip().strip("`\"'[]")
            if clean:
                tables.add(clean.lower())
        return tables

    def _validate_table_access(
        self,
        namespace: str,
        sql: str,
    ) -> None:
        """Verify that SQL statements only target tables declared for this namespace.

        Args:
            namespace: Declaring feature namespace.
            sql: SQL statement to execute.

        Raises:
            NamespaceAccessDeniedError: If an undeclared table is targeted.
            EvidenceImmutableError: If UPDATE or DELETE targets an evidence table.
        """
        registration = self._registrations.get(namespace)
        if not registration:
            msg = f"Namespace '{namespace}' is not registered with persistence provider"
            raise NamespaceAccessDeniedError(
                namespace=namespace,
                message=msg,
            )

        allowed_tables = {t.lower() for t in registration.allowed_tables}
        evidence_tables = {t.lower() for t in registration.evidence_tables}
        all_allowed = allowed_tables | evidence_tables
        referenced_tables = self._extract_tables(sql)

        for table in referenced_tables:
            # Internal persistence tables are managed internally
            if table.startswith("_persistence_"):
                raise NamespaceAccessDeniedError(
                    namespace=namespace,
                    table=table,
                    message="Direct access to internal persistence tables is forbidden",
                )
            if table not in all_allowed:
                msg = (
                    f"Namespace '{namespace}' is not authorized to access "
                    f"table '{table}'"
                )
                raise NamespaceAccessDeniedError(
                    namespace=namespace,
                    table=table,
                    message=msg,
                )
            if table in evidence_tables and _SQL_DISALLOWED_EVIDENCE_OPS.search(sql):
                msg = (
                    f"Table '{table}' is declared append-only evidence "
                    f"and cannot be updated or deleted"
                )
                raise EvidenceImmutableError(
                    namespace=namespace,
                    message=msg,
                )

    def _check_idempotency(
        self,
        connection: sqlite3.Connection,
        request_id: str,
    ) -> PersistenceTransactionResult | None:
        """Return cached transaction result if previously executed.

        Args:
            connection: Active database connection.
            request_id: Unique request identifier.

        Returns:
            Cached result if present, else None.
        """
        cursor = connection.execute(
            _SQL_GET_IDEMPOTENCY,
            (request_id,),
        )
        cached_row = cursor.fetchone()
        if not cached_row:
            return None
        cached_data = json.loads(cached_row["result_json"])
        return PersistenceTransactionResult(
            request_id=cached_data["request_id"],
            namespace=cached_data["namespace"],
            rows_affected=cached_data["rows_affected"],
            new_revision=cached_data["new_revision"],
            results=tuple(
                tuple(row for row in result_set)
                for result_set in cached_data.get("results", ())
            ),
            schema_version=cached_data.get("schema_version", 1),
        )

    def _record_idempotency(
        self,
        connection: sqlite3.Connection,
        request: PersistenceTransactionRequest,
        result: PersistenceTransactionResult,
        now_iso: str,
    ) -> None:
        """Record idempotency receipt for a completed transaction.

        Args:
            connection: Active database connection.
            request: Original transaction request.
            result: Transaction execution result.
            now_iso: UTC timestamp.
        """
        result_payload = {
            "request_id": result.request_id,
            "namespace": result.namespace,
            "rows_affected": result.rows_affected,
            "new_revision": result.new_revision,
            "results": [list(rs) for rs in result.results],
            "schema_version": result.schema_version,
        }
        fingerprint = hashlib.sha256(
            f"{request.actor_id}:{request.account_id}:{request.namespace}".encode()
        ).hexdigest()
        connection.execute(
            _SQL_INSERT_IDEMPOTENCY,
            (
                request.request_id,
                request.namespace,
                fingerprint,
                json.dumps(result_payload),
                now_iso,
            ),
        )

    def execute_transaction(
        self,
        request: PersistenceTransactionRequest,
    ) -> PersistenceTransactionResult:
        """Execute a namespace-bound transaction with idempotency and optimistic locks.

        Args:
            request: Validated transaction request.

        Returns:
            Transaction outcome with row counts and updated revision.

        Raises:
            NamespaceAccessDeniedError: If undeclared tables/namespaces are accessed.
            RevisionConflictError: If expected_revision does not match current state.
            EvidenceImmutableError: If UPDATE/DELETE targets evidence.
            WorkspaceStorageError: If execution fails.
            PersistenceError: If statement limit is exceeded.
        """
        if len(request.statements) > self._config.max_statements_per_tx:
            msg = (
                f"Transaction exceeds maximum allowed statements "
                f"({self._config.max_statements_per_tx})"
            )
            raise PersistenceError(msg)

        # Validate access for all statements before executing any
        for statement in request.statements:
            self._validate_table_access(request.namespace, statement.sql)

        db_path = _db_path(request.workspace_path)
        connection = self._connect(db_path)
        try:
            cached = self._check_idempotency(connection, request.request_id)
            if cached:
                return cached

            cursor = connection.execute(
                _SQL_GET_REVISION,
                (request.namespace,),
            )
            rev_row = cursor.fetchone()
            current_revision = int(rev_row["revision"]) if rev_row else 1

            if (
                request.expected_revision is not None
                and current_revision != request.expected_revision
            ):
                raise RevisionConflictError(
                    namespace=request.namespace,
                    expected=request.expected_revision,
                    actual=current_revision,
                )

            total_rows_affected = 0
            results_list: list[tuple[dict[str, Any], ...]] = []
            now_iso = _utc_now_iso()

            with connection:
                for statement in request.statements:
                    stmt_cursor = connection.execute(
                        statement.sql,
                        statement.parameters,
                    )
                    if stmt_cursor.description:
                        rows = tuple(dict(row) for row in stmt_cursor.fetchall())
                        results_list.append(rows)
                    else:
                        total_rows_affected += max(0, stmt_cursor.rowcount)

                new_revision = current_revision + 1
                connection.execute(
                    _SQL_UPSERT_REVISION,
                    (
                        request.namespace,
                        new_revision,
                        now_iso,
                        new_revision,
                        now_iso,
                    ),
                )

                result = PersistenceTransactionResult(
                    request_id=request.request_id,
                    namespace=request.namespace,
                    rows_affected=total_rows_affected,
                    new_revision=new_revision,
                    results=tuple(results_list),
                    schema_version=1,
                )
                self._record_idempotency(connection, request, result, now_iso)

            return result
        except sqlite3.IntegrityError as error:
            if "Evidence records are immutable" in str(error):
                raise EvidenceImmutableError(
                    namespace=request.namespace,
                    message=str(error),
                ) from error
            msg = f"Transaction integrity error: {error}"
            raise WorkspaceStorageError(msg) from error
        except sqlite3.Error as error:
            msg = f"Transaction execution error: {error}"
            raise WorkspaceStorageError(msg) from error
        finally:
            connection.close()

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
            Migration result.

        Raises:
            MigrationChecksumError: If an applied migration has a changed checksum.
            WorkspaceMigrationError: If a migration script fails to execute.
        """
        db_path = _db_path(workspace_path)
        connection = self._connect(db_path)
        try:
            # 1. Fetch applied migrations
            cursor = connection.execute(
                _SQL_GET_MIGRATIONS,
                (manifest.namespace,),
            )
            applied_map = {row["version"]: row["checksum"] for row in cursor.fetchall()}

            current_version = max(applied_map.keys(), default=0)
            applied_new: list[int] = []
            now_iso = _utc_now_iso()

            with connection:
                for migration in manifest.migrations:
                    if migration.version in applied_map:
                        recorded = applied_map[migration.version]
                        if recorded != migration.checksum:
                            raise MigrationChecksumError(
                                namespace=manifest.namespace,
                                version=migration.version,
                                recorded_checksum=recorded,
                                provided_checksum=migration.checksum,
                            )
                        continue

                    # Apply new migration
                    try:
                        connection.executescript(migration.sql)
                        connection.execute(
                            _SQL_INSERT_MIGRATION,
                            (
                                manifest.namespace,
                                migration.version,
                                migration.name,
                                now_iso,
                                migration.checksum,
                            ),
                        )
                        applied_new.append(migration.version)
                        current_version = migration.version
                    except sqlite3.Error as error:
                        msg = (
                            f"Migration {migration.version} "
                            f"('{migration.name}') failed: {error}"
                        )
                        raise WorkspaceMigrationError(
                            msg,
                            version=migration.version,
                        ) from error

            return MigrationResult(
                namespace=manifest.namespace,
                current_version=current_version,
                applied_versions=tuple(applied_new),
            )
        finally:
            connection.close()

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
            The stored evidence record with assigned sequence.

        Raises:
            EvidenceImmutableError: If duplicate evidence ID or mutation is attempted.
            WorkspaceStorageError: If insertion fails.
        """
        db_path = _db_path(workspace_path)
        connection = self._connect(db_path)
        try:
            with connection:
                # Check for duplicate evidence_id
                cursor = connection.execute(
                    _SQL_CHECK_EVIDENCE_EXISTS,
                    (evidence.evidence_id,),
                )
                if cursor.fetchone() is not None:
                    msg = (
                        f"Evidence '{evidence.evidence_id}' already exists "
                        f"and cannot be overwritten"
                    )
                    raise EvidenceImmutableError(
                        namespace=namespace,
                        evidence_id=evidence.evidence_id,
                        message=msg,
                    )

                cursor = connection.execute(
                    _SQL_INSERT_EVIDENCE,
                    (
                        evidence.evidence_id,
                        evidence.workspace_id,
                        namespace,
                        evidence.content_hash,
                        evidence.payload_json,
                        evidence.created_at,
                    ),
                )
                seq = int(cursor.lastrowid or 0)

            return EvidenceRecord(
                evidence_id=evidence.evidence_id,
                workspace_id=evidence.workspace_id,
                namespace=namespace,
                content_hash=evidence.content_hash,
                payload_json=evidence.payload_json,
                created_at=evidence.created_at,
                sequence=seq,
            )
        except sqlite3.Error as error:
            msg = f"Failed to append evidence: {error}"
            raise WorkspaceStorageError(msg) from error
        finally:
            connection.close()

    def export_evidence(
        self,
        request: ExportEvidenceRequest,
    ) -> ExportEvidenceResult:
        """Return bounded, stable-ordered paged evidence within workspace scope.

        Args:
            request: Export request.

        Returns:
            Paged export result.

        Raises:
            WorkspaceNotFoundError: If workspace database does not exist.
            WorkspaceStorageError: If query fails.
        """
        db_path = _db_path(request.workspace_path)
        if not db_path.exists():
            raise WorkspaceNotFoundError(str(db_path))

        effective_limit = min(request.limit, self._config.max_export_limit)
        connection = self._connect(db_path)
        try:
            ws_id = self._get_workspace_id(connection, request.workspace_path)

            cursor = connection.execute(
                _SQL_COUNT_EVIDENCE,
                (request.namespace, ws_id),
            )
            total_count = int(cursor.fetchone()["count"])

            cursor = connection.execute(
                _SQL_EXPORT_EVIDENCE,
                (request.namespace, ws_id, effective_limit, request.offset),
            )
            records = tuple(
                EvidenceRecord(
                    evidence_id=row["evidence_id"],
                    workspace_id=row["workspace_id"],
                    namespace=row["namespace"],
                    content_hash=row["content_hash"],
                    payload_json=row["payload_json"],
                    created_at=row["created_at"],
                    sequence=row["sequence"],
                )
                for row in cursor.fetchall()
            )

            has_more = (request.offset + len(records)) < total_count
            return ExportEvidenceResult(
                namespace=request.namespace,
                records=records,
                total_count=total_count,
                has_more=has_more,
                limit=effective_limit,
                offset=request.offset,
            )
        except sqlite3.Error as error:
            msg = f"Failed to export evidence: {error}"
            raise WorkspaceStorageError(msg) from error
        finally:
            connection.close()
