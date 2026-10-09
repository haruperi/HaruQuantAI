"""Exclusive database access and storage CRUD for the application.

Description:
    This is the only application module permitted to import database drivers,
    open connections, execute SQL, or manage schemas and database transactions.
    Small stores group related CRUD, queries, aggregates, storage serialization,
    and atomic conditional writes. DatabaseManager owns handles; stores return
    records and results. Connection/transaction methods are internal infrastructure:
    other application modules must never borrow handles or supply connections.

    Business logic MUST NOT be added here. Configuration validation and snapshots
    belong to app.host.settings; job lifecycle and worker lease policy belong to
    app.host.jobs; scope binding belongs to app.host.session; startup recovery
    sequencing belongs to app.host.bootstrap. Trading defaults and interpretation
    belong to workspace services. Python, HTTP and CLI access belongs to each
    business owner: settings access in settings, lease access in jobs, recovery
    access in bootstrap, and database inspection in diagnostics.
    No service callbacks, domain-model imports, business seeds, job-state
    decisions, authorization decisions, or transport dependencies
    are allowed in this module. Future features add narrow CRUD operations here
    and call them from their owning service.

    Domain services supply complete creation records, business defaults, domain
    timestamps and conflict-update field choices. CRUD must not invent missing
    trading values, session definitions, dataset IDs or quality scores. Existing
    schema DEFAULT declarations remain compatibility infrastructure; storage
    audit timestamps, revisions and serialization constraints belong here.

Purpose:
    FEAT-HOST-PERSISTENCE: Exclusive transactional database access and storage CRUD.
    Preserve storage consistency without deciding application behavior.

Key Capabilities:
    - FR-HOST-PERSISTENCE-SCHEMA-VERIFICATION: Create and inspect storage schemas.
      Associated: `SchemaManager.initialize()`, `SchemaManager.verify_schema()`,
        `SchemaManager.drop_obsolete_sessions()`
      Logging: INFO initialization; ERROR incompatible required tables/version.
    - FR-HOST-PERSISTENCE-TRANSACTIONS: Atomic writes and connection ownership.
      Associated: `DatabaseManager.connection()`, `DatabaseManager.transaction()`
      Logging: DEBUG access/commit; WARNING rollback; ERROR contention.
    - FR-HOST-PERSISTENCE-TYPED-REPOSITORY: Scoped JSON entity CRUD and revisions.
      Associated: `TypedRepository.get()`, `save()`, `delete()`, `list()`
      Logging: DEBUG reads; INFO writes; WARNING revision conflicts.
    - FR-HOST-PERSISTENCE-SETTINGS: Setting reads, batch writes/deletes and backups.
      Associated: `SettingsStore.read_all()`, `SettingsStore.update_batch()`,
        `SettingsStore.backup_to()`
      Logging: DEBUG reads; INFO changes; WARNING unavailable/corrupt data.
    - FR-HOST-PERSISTENCE-JOBS: Job row reads/writes and conditional field updates.
      Associated: `JobStore.get_job()`, `upsert_job()`, `update_statuses()`
      Logging: DEBUG reads; INFO writes and affected-row count.
    - FR-HOST-PERSISTENCE-LEASES: Atomic reservation row predicates and CRUD.
      Associated: `LeaseStore.acquire()`, `renew()`, `release()`, `prune_expired()`
      Logging: DEBUG conditional results/reads; INFO deleted-row count.
    - FR-HOST-PERSISTENCE-INSTRUMENTS: Instrument row CRUD.
      Associated: `InstrumentStore.create()`, `get_by_symbol()`, `update()`, `delete()`
      Logging: DEBUG reads; INFO writes without payload values.
    - FR-HOST-PERSISTENCE-SESSIONS: Trading-session row CRUD.
      Associated: `SessionStore.upsert()`, `get_by_name()`, `delete()`
      Logging: DEBUG reads; INFO write results.
    - FR-HOST-PERSISTENCE-HOST-SESSIONS: Login lifecycle record CRUD.
      Associated: `HostSessionStore.initialize()`, `create()`, `list_records()`,
        `update_status()`
      Logging: INFO storage verification/writes and counts; DEBUG reads.
    - FR-HOST-PERSISTENCE-DATASETS: Metadata CRUD and bar aggregates.
      Associated: `DatasetStore.save()`, `get_by_id()`, `sum_bars()`
      Logging: DEBUG reads; INFO writes.
    - FR-HOST-PERSISTENCE-BASKETS: Transactional group and membership CRUD.
      Associated: `BasketStore.save()`, `get()`, `delete()`, `count()`
      Logging: DEBUG reads; INFO write/delete results.
    - FR-HOST-PERSISTENCE-BROKERS: Optional legacy broker row queries.
      Associated: `BrokerStore.list_profiles()`
      Logging: DEBUG read and table availability; no business fallback profiles.
    - FR-HOST-PERSISTENCE-ANALYTICAL-QUERY: Direct DuckDB analytical query execution.
      Associated: `query_duckdb()`, `DatabaseManager.query_duckdb()`
      Logging: DEBUG execution with query text.
    - FR-HOST-PERSISTENCE-INTEGRITY-CHECK: Query physical SQLite integrity.
      Associated: `DatabaseManager.check_integrity()`
      Logging: INFO clean result; ERROR detected corruption.

Python API Usage:
    ```python
    from app.host.persistence import DatabaseManager

    db = DatabaseManager(":memory:")
    db.initialize()  # Storage only; domain services initialize business defaults.
    rows = db.datasets.list_datasets(limit=50)
    db.close()
    ```

CLI Usage:
    No persistence CLI or business orchestration lives here. Diagnostics owns it:
    ```bash
    uv run python -m app.host.diagnostics --status --db path/to/database.db
    uv run python -m app.host.diagnostics --integrity-check --db path/to/database.db
    ```
"""

from __future__ import annotations

import contextlib
import json
import re
import sqlite3
import threading
from collections.abc import Generator, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from app.host.logging import get_logger

logger = get_logger(__name__)


DEFAULT_DATABASE_PATH: Path = (
    Path(__file__).resolve().parents[2] / "data" / "database" / "haruquantai.db"
)
MAX_BATCH_SIZE: int = 100
MAX_READ_LIMIT: int = 1000
DEFAULT_READ_LIMIT: int = 50
SCHEMA_VERSION: int = 1

__all__ = [
    "DEFAULT_DATABASE_PATH",
    "DEFAULT_READ_LIMIT",
    "MAX_BATCH_SIZE",
    "MAX_READ_LIMIT",
    "SCHEMA_VERSION",
    "BasketStore",
    "BrokerStore",
    "CorruptDataError",
    "DatabaseManager",
    "DatabaseStatus",
    "DatasetStore",
    "EntityRecord",
    "HostSessionRecord",
    "HostSessionStore",
    "IncompatibleSchemaError",
    "InstrumentStore",
    "JobStore",
    "LeaseExpiredError",
    "LeaseStore",
    "MigrationRecord",
    "Page",
    "PersistenceError",
    "RevisionConflictError",
    "SchemaManager",
    "SessionStore",
    "SettingRecord",
    "SettingsPage",
    "SettingsStore",
    "StorageBusyError",
    "TypedRepository",
    "ValidationError",
    "canonical_json",
    "get_database_manager",
    "now_utc_iso",
    "query_duckdb",
    "validate_identifier",
    "validate_json_depth",
]

# Internal constants for persistence invariants and bounded operations
_MAX_IDENTIFIER_LENGTH: int = 128
_IDENTIFIER_PATTERN: re.Pattern[str] = re.compile(r"^[A-Za-z0-9_.:-]+$")
_MAX_PAYLOAD_BYTES: int = 1024 * 1024  # 1 MiB
_MAX_JSON_DEPTH: int = 16
_BUSY_TIMEOUT_MS: int = 5000
_BUSY_TIMEOUT_SECONDS: float = 5.0
_CURRENT_SCHEMA_VERSION: int = 1


# ============================================================================
# Enums and Domain Models
# ============================================================================


class MigrationRecord(BaseModel):
    """Schema migration ledger entry."""

    version: int = Field(ge=1, description="Monotonic schema version number.")
    name: str = Field(description="Descriptive identifier of migration.")
    applied_at_utc: datetime = Field(description="UTC timestamp of migration commit.")
    checksum: str = Field(description="SHA-256 digest of migration SQL script.")


class EntityRecord(BaseModel):
    """Authoritative storage envelope for a persisted domain entity."""

    entity_id: str = Field(description="Unique entity identifier within type.")
    entity_type: str = Field(description="Categorical entity type name.")
    scope: str = Field(description="Tenant or namespace scope.")
    payload: dict[str, Any] = Field(description="Structured JSON payload.")
    revision: int = Field(
        ge=1, description="Monotonic optimistic concurrency revision."
    )
    created_at_utc: datetime = Field(description="UTC timestamp of creation.")
    updated_at_utc: datetime = Field(description="UTC timestamp of last write.")


class DatabaseStatus(BaseModel):
    """Operational health snapshot of the host SQLite persistence engine."""

    database_path: str = Field(description="Absolute path to database file.")
    is_connected: bool = Field(description="Whether database responds to queries.")
    journal_mode: str = Field(description="Active SQLite journal mode (e.g., WAL).")
    schema_version: int = Field(description="Highest applied schema migration version.")
    table_count: int = Field(ge=0, description="Total user tables in database.")
    integrity_status: str = Field(description="Result of PRAGMA integrity_check.")


class Page[T](BaseModel):
    """Keyset or offset paginated collection of typed records."""

    items: list[T] = Field(description="List of records in the current page.")
    total_count: int = Field(ge=0, description="Total matching records count.")
    next_cursor: str | None = Field(
        default=None, description="Cursor for fetching next page, if any."
    )


class SettingRecord(BaseModel):
    """Auditable record for a scoped configuration setting."""

    scope: str
    key: str
    value: Any
    schema_version: int = 1
    updated_at_utc: str


class SettingsPage(BaseModel):
    """Paginated slice of setting records."""

    items: list[SettingRecord]
    next_key: str | None = None


# ============================================================================
# Exceptions
# ============================================================================


class PersistenceError(Exception):
    """Base exception for all database and persistence failures."""


class ValidationError(PersistenceError):
    """Raised when an identifier, depth, or payload violates constraints."""


class IncompatibleSchemaError(PersistenceError):
    """Raised when database schema definition is corrupt, altered, or unsupported."""


class StorageBusyError(PersistenceError):
    """Raised when SQLite locks or transactions time out under concurrent load."""


class RevisionConflictError(PersistenceError):
    """Raised when an optimistic concurrency revision mismatch occurs."""


class LeaseExpiredError(PersistenceError):
    """Raised when attempting to renew or operate on an expired/stolen lease."""


class CorruptDataError(PersistenceError):
    """Raised when persisted record content fails deserialization or validation."""


# ============================================================================
# Validation Primitives
# ============================================================================


def validate_identifier(value: str, field_name: str) -> None:
    """Validate that an identifier string satisfies format and length constraints.

    Args:
        value: Identifier string to check.
        field_name: Descriptive name of the identifier field for errors.

    Raises:
        ValidationError: If identifier is empty, exceeds max length, or has
            invalid chars.
    """
    if not value:
        raise ValidationError(f"{field_name} must not be empty")
    if len(value) > _MAX_IDENTIFIER_LENGTH:
        msg = (
            f"{field_name} length {len(value)} exceeds maximum of "
            f"{_MAX_IDENTIFIER_LENGTH} characters"
        )
        raise ValidationError(msg)
    if not _IDENTIFIER_PATTERN.match(value):
        msg = (
            f"{field_name} '{value}' contains invalid characters; "
            "must match alphanumeric, underscore, dot, colon, or hyphen"
        )
        raise ValidationError(msg)


def validate_json_depth(obj: Any, depth: int = 1) -> None:
    """Recursively validate that JSON object nesting does not exceed safe limits.

    Args:
        obj: Python data structure to inspect.
        depth: Current nesting depth level.

    Raises:
        ValidationError: If nesting depth exceeds _MAX_JSON_DEPTH.
    """
    if depth > _MAX_JSON_DEPTH:
        msg = f"JSON structure exceeds maximum nesting depth of {_MAX_JSON_DEPTH}"
        raise ValidationError(msg)
    if isinstance(obj, dict):
        for val in obj.values():
            validate_json_depth(val, depth + 1)
    elif isinstance(obj, list):
        for item in obj:
            validate_json_depth(item, depth + 1)


def canonical_json(obj: Any) -> str:
    """Serialize a Python object to canonical sorted-key JSON string with size checks.

    Args:
        obj: Object to serialize.

    Returns:
        Compact, sorted JSON string representation.

    Raises:
        ValidationError: If serialization fails, contains non-finite floats,
            or exceeds size.
    """
    validate_json_depth(obj)
    try:
        encoded = json.dumps(
            obj,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        msg = "Object payload is not serializable to strict JSON"
        raise ValidationError(msg) from exc

    raw_bytes = encoded.encode("utf-8")
    if len(raw_bytes) > _MAX_PAYLOAD_BYTES:
        msg = (
            f"Serialized payload of {len(raw_bytes)} bytes exceeds maximum "
            f"limit of {_MAX_PAYLOAD_BYTES} bytes"
        )
        raise ValidationError(msg)
    return encoded


def now_utc_iso() -> str:
    """Return current UTC timestamp in ISO 8601 format."""
    return datetime.now(UTC).isoformat()


def _validate_columns(record: Mapping[str, Any], allowed: frozenset[str]) -> None:
    """Reject update/insert fields outside a fixed storage-column allowlist."""
    if set(record) - allowed:
        raise ValidationError("Unsupported storage column")


def _require_columns(record: Mapping[str, Any], columns: tuple[str, ...]) -> None:
    """Reject incomplete inserts before opening a write transaction."""
    if set(columns) - set(record):
        raise ValidationError("Incomplete storage record")


# ============================================================================
# Database Connection & Transaction Manager
# ============================================================================


class DatabaseManager:
    """Central host authority for SQLite database connections, WAL, and transactions."""

    def __init__(
        self,
        database_path: Path | str | None = None,
        *,
        busy_timeout: float = _BUSY_TIMEOUT_SECONDS,
    ) -> None:
        """Initialize DatabaseManager with database file path or ':memory:'.

        Args:
            database_path: Filesystem path to SQLite database or ':memory:'. Defaults
                to DEFAULT_DATABASE_PATH.
            busy_timeout: Lock timeout in seconds.
        """
        self._is_memory = str(database_path) == ":memory:"
        self._busy_timeout = busy_timeout
        self._lock = threading.Lock()

        if self._is_memory:
            self.database_path = Path(":memory:")
            self._mem_conn: sqlite3.Connection | None = sqlite3.connect(
                ":memory:", check_same_thread=False, autocommit=True
            )
            self._mem_conn.row_factory = sqlite3.Row
            self._mem_conn.execute("PRAGMA foreign_keys = ON;")
            self._mem_conn.execute(
                f"PRAGMA busy_timeout = {int(self._busy_timeout * 1000)};"
            )
        else:
            self._mem_conn = None
            resolved = (
                Path(database_path).resolve()
                if database_path is not None
                else DEFAULT_DATABASE_PATH.resolve()
            )
            self.database_path = resolved
            self.database_path.parent.mkdir(parents=True, exist_ok=True)

        self.schema = SchemaManager(self)
        self.leases = LeaseStore(self)
        self.instruments = InstrumentStore(self)
        self.sessions = SessionStore(self)
        self.datasets = DatasetStore(self)
        self.baskets = BasketStore(self)
        self.brokers = BrokerStore(self)

    @property
    def is_memory(self) -> bool:
        """Return True if database connection is backed by in-memory SQLite store."""
        return self._is_memory

    def connect(self) -> sqlite3.Connection:
        """Establish a new configured SQLite connection with pragmas applied.

        Returns:
            Configured sqlite3.Connection instance.
        """
        if self._is_memory and self._mem_conn is not None:
            return self._mem_conn
        conn = sqlite3.connect(
            str(self.database_path),
            timeout=self._busy_timeout,
            autocommit=True,
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute(f"PRAGMA busy_timeout = {int(self._busy_timeout * 1000)};")
        return conn

    @contextlib.contextmanager
    def connection(self, *, query_only: bool = False) -> Generator[sqlite3.Connection]:
        """Context manager providing an active SQLite connection, closed on exit.

        Args:
            query_only: If True, opens connection in read-only mode for persistent db.

        Yields:
            Configured sqlite3.Connection instance.
        """
        logger.debug(
            "Database connection access",
            extra={"fr_id": "FR-HOST-PERSISTENCE-TRANSACTIONS"},
        )
        if self._is_memory and self._mem_conn is not None:
            with self._lock:
                yield self._mem_conn
        elif query_only:
            uri = f"file:{self.database_path.as_posix()}?mode=ro"
            try:
                conn = sqlite3.connect(
                    uri,
                    timeout=self._busy_timeout,
                    uri=True,
                    autocommit=True,
                )
            except sqlite3.OperationalError as exc:
                if "busy" in str(exc).lower() or "locked" in str(exc).lower():
                    raise StorageBusyError(
                        "Database connection timed out under lock"
                    ) from exc
                raise PersistenceError("Failed to open database connection") from exc

            conn.row_factory = sqlite3.Row
            try:
                conn.execute(f"PRAGMA busy_timeout = {int(self._busy_timeout * 1000)};")
                conn.execute("PRAGMA foreign_keys = ON;")
                conn.execute("PRAGMA synchronous = NORMAL;")
                conn.execute("PRAGMA query_only = ON;")
                yield conn
            finally:
                conn.close()
        else:
            try:
                conn = self.connect()
            except sqlite3.OperationalError as exc:
                if "busy" in str(exc).lower() or "locked" in str(exc).lower():
                    raise StorageBusyError(
                        "Database connection timed out under lock"
                    ) from exc
                raise PersistenceError("Failed to open database connection") from exc
            try:
                yield conn
            finally:
                conn.close()

    @contextlib.contextmanager
    def transaction(self) -> Generator[sqlite3.Connection]:
        """Context manager executing a serialized `BEGIN IMMEDIATE` transaction.

        Yields:
            Active sqlite3.Connection within transaction.

        Raises:
            StorageBusyError: If the database is locked or busy.
            PersistenceError: If a database error occurs during execution.
        """
        if self._is_memory and self._mem_conn is not None:
            with self._lock:
                conn = self._mem_conn
                try:
                    conn.execute("BEGIN IMMEDIATE;")
                    yield conn
                    conn.execute("COMMIT;")
                except Exception:
                    with contextlib.suppress(sqlite3.Error):
                        conn.execute("ROLLBACK;")
                    raise
        else:
            conn = self.connect()
            try:
                conn.execute("BEGIN IMMEDIATE;")
                logger.debug(
                    "Transaction started",
                    extra={"fr_id": "FR-HOST-PERSISTENCE-TRANSACTIONS"},
                )
                yield conn
                conn.execute("COMMIT;")
                logger.debug(
                    "Transaction committed",
                    extra={"fr_id": "FR-HOST-PERSISTENCE-TRANSACTIONS"},
                )
            except sqlite3.OperationalError as exc:
                with contextlib.suppress(sqlite3.Error):
                    conn.execute("ROLLBACK;")
                if "locked" in str(exc).lower() or "busy" in str(exc).lower():
                    logger.exception(
                        "Database busy timeout during transaction",
                        extra={"error": str(exc)},
                    )
                    raise StorageBusyError(
                        f"Database contention timeout: {exc}"
                    ) from exc
                logger.exception(
                    "Operational error during transaction",
                    extra={"error": str(exc)},
                )
                raise PersistenceError(f"Database operational error: {exc}") from exc
            except Exception as exc:
                with contextlib.suppress(sqlite3.Error):
                    conn.execute("ROLLBACK;")
                logger.warning(
                    "Transaction rolled back due to error",
                    extra={"error": str(exc)},
                )
                raise
            finally:
                conn.close()

    def close(self) -> None:
        """Close connection if in-memory."""
        if self._is_memory and self._mem_conn is not None:
            with self._lock:
                self._mem_conn.close()
                self._mem_conn = None

    def check_integrity(self) -> str:
        """Run SQLite PRAGMA integrity_check and return status string.

        Returns:
            Status result ("ok" on clean database).
        """
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check;")
            row = cursor.fetchone()
            result = str(row[0]) if row else "unknown"

        if result.lower() != "ok":
            logger.error(
                "PRAGMA integrity_check reported corruption",
                extra={
                    "integrity_result": result,
                    "fr_id": "FR-HOST-PERSISTENCE-INTEGRITY-CHECK",
                },
            )
        else:
            logger.info(
                "Database integrity verified",
                extra={
                    "database": str(self.database_path),
                    "fr_id": "FR-HOST-PERSISTENCE-INTEGRITY-CHECK",
                },
            )
        return result

    def get_status(self) -> DatabaseStatus:
        """Retrieve operational health metrics snapshot for the database.

        Returns:
            DatabaseStatus record.
        """
        is_connected = False
        journal_mode = "unknown"
        table_count = 0
        schema_version = 0

        try:
            with self.connection() as conn:
                is_connected = True
                cur = conn.cursor()
                cur.execute("PRAGMA journal_mode;")
                j_row = cur.fetchone()
                if j_row:
                    journal_mode = str(j_row[0])

                cur.execute(
                    "SELECT COUNT(*) FROM sqlite_master "
                    "WHERE type='table' AND name NOT LIKE 'sqlite_%';"
                )
                t_row = cur.fetchone()
                if t_row:
                    table_count = int(t_row[0])

                cur.execute(
                    "SELECT COUNT(*) FROM sqlite_master "
                    "WHERE type='table' AND name='schema_migrations';"
                )
                if cur.fetchone()[0] > 0:
                    cur.execute(
                        "SELECT COALESCE(MAX(version), 0) FROM schema_migrations;"
                    )
                    s_row = cur.fetchone()
                    if s_row:
                        schema_version = int(s_row[0])
        except (sqlite3.Error, OSError, PersistenceError) as exc:
            logger.warning("Failed to query database status", extra={"error": str(exc)})

        integrity = self.check_integrity() if is_connected else "disconnected"

        return DatabaseStatus(
            database_path=str(self.database_path),
            is_connected=is_connected,
            journal_mode=journal_mode,
            schema_version=schema_version,
            table_count=table_count,
            integrity_status=integrity,
        )

    def initialize(self) -> None:
        """Initialize core schemas and verify database readiness."""
        self.schema.initialize()

    def query_duckdb(self, query: str, *args: Any, **kwargs: Any) -> Any:
        """Execute analytical DuckDB SQL query directly over Parquet files or memory.

        Fires FR-HOST-PERSISTENCE-ANALYTICAL-QUERY.
        """
        return query_duckdb(query, *args, **kwargs)


class _DefaultDatabaseHolder:
    """Internal singleton holder avoiding module global mutation."""

    instance: DatabaseManager | None = None


def query_duckdb(query: str, *args: Any, **kwargs: Any) -> Any:
    """Execute analytical DuckDB SQL query directly over Parquet files or memory.

    Centralizes DuckDB database driver imports within app.host.persistence to
    satisfy architectural driver isolation requirements.

    Fires FR-HOST-PERSISTENCE-ANALYTICAL-QUERY.
    """
    import duckdb

    logger.debug(
        "FR-HOST-PERSISTENCE-ANALYTICAL-QUERY: Executing DuckDB query",
        extra={"fr_id": "FR-HOST-PERSISTENCE-ANALYTICAL-QUERY", "query": query},
    )
    return duckdb.query(query, *args, **kwargs)


def get_database_manager(
    database_path: Path | str | None = None,
    *,
    busy_timeout: float = _BUSY_TIMEOUT_SECONDS,
) -> DatabaseManager:
    """Obtain authoritative DatabaseManager, using default database location if omitted.

    Args:
        database_path: Optional path to SQLite database. Defaults to
            DEFAULT_DATABASE_PATH.
        busy_timeout: Timeout in seconds for SQLite lock waits.

    Returns:
        Configured DatabaseManager instance.
    """
    if database_path is not None:
        return DatabaseManager(database_path, busy_timeout=busy_timeout)
    if _DefaultDatabaseHolder.instance is None:
        _DefaultDatabaseHolder.instance = DatabaseManager(
            DEFAULT_DATABASE_PATH, busy_timeout=busy_timeout
        )
    return _DefaultDatabaseHolder.instance


# ============================================================================
# Schema Migration Manager
# ============================================================================


class SchemaManager:
    """Manages schema migrations, version assertions, and compatibility verification."""

    def __init__(self, db: DatabaseManager) -> None:
        self._db = db
        self._initialized = False

    def initialize(self, force: bool = False) -> None:
        """Initialize migration ledger and create authoritative control tables."""
        if self._initialized and not force:
            return
        with self._db.transaction() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    applied_at_utc TEXT NOT NULL,
                    checksum TEXT NOT NULL
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS host_entities (
                    entity_id TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    revision INTEGER NOT NULL DEFAULT 1,
                    created_at_utc TEXT NOT NULL,
                    updated_at_utc TEXT NOT NULL,
                    PRIMARY KEY (entity_id, entity_type)
                );
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_host_entities_scope
                ON host_entities (scope, entity_type);
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS host_leases (
                    lease_key TEXT PRIMARY KEY,
                    holder_id TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    acquired_at_utc TEXT NOT NULL,
                    expires_at_utc TEXT NOT NULL,
                    metadata TEXT NOT NULL
                );
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_host_leases_expiry
                ON host_leases (expires_at_utc);
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS host_settings (
                    scope TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value_json TEXT NOT NULL,
                    schema_version INTEGER NOT NULL DEFAULT 1,
                    updated_at_utc TEXT NOT NULL,
                    PRIMARY KEY (scope, key)
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS host_jobs (
                    job_id TEXT PRIMARY KEY,
                    owner TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    status TEXT NOT NULL,
                    progress REAL NOT NULL DEFAULT 0.0,
                    accepted INTEGER NOT NULL DEFAULT 0,
                    rejected INTEGER NOT NULL DEFAULT 0,
                    message TEXT NOT NULL DEFAULT '',
                    attempt_id INTEGER NOT NULL DEFAULT 1,
                    max_retries INTEGER NOT NULL DEFAULT 0,
                    retry_count INTEGER NOT NULL DEFAULT 0,
                    dedup_key TEXT,
                    parent_job_id TEXT,
                    child_job_ids_json TEXT NOT NULL DEFAULT '[]',
                    budget_json TEXT NOT NULL DEFAULT '{}',
                    submitted_at_utc TEXT NOT NULL DEFAULT '',
                    started_at_utc TEXT,
                    finished_at_utc TEXT,
                    error_message TEXT,
                    error_location TEXT
                );
                """
            )
            # Ensure columns and backward-compatibility for host_jobs
            table_info = conn.execute("PRAGMA table_info(host_jobs);").fetchall()
            cols = {r["name"] for r in table_info}
            required_cols = {
                "owner": "TEXT NOT NULL DEFAULT 'default'",
                "kind": "TEXT NOT NULL DEFAULT 'compute'",
                "status": "TEXT NOT NULL DEFAULT 'completed'",
                "progress": "REAL NOT NULL DEFAULT 0.0",
                "accepted": "INTEGER NOT NULL DEFAULT 0",
                "rejected": "INTEGER NOT NULL DEFAULT 0",
                "message": "TEXT NOT NULL DEFAULT ''",
                "attempt_id": "INTEGER NOT NULL DEFAULT 1",
                "max_retries": "INTEGER NOT NULL DEFAULT 0",
                "retry_count": "INTEGER NOT NULL DEFAULT 0",
                "dedup_key": "TEXT",
                "parent_job_id": "TEXT",
                "child_job_ids_json": "TEXT NOT NULL DEFAULT '[]'",
                "budget_json": "TEXT NOT NULL DEFAULT '{}'",
                "submitted_at_utc": "TEXT NOT NULL DEFAULT ''",
                "started_at_utc": "TEXT",
                "finished_at_utc": "TEXT",
                "error_message": "TEXT",
                "error_location": "TEXT",
            }
            for col_name, col_def in required_cols.items():
                if col_name not in cols:
                    conn.execute(
                        f"ALTER TABLE host_jobs ADD COLUMN {col_name} {col_def};"
                    )

            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_host_jobs_owner ON host_jobs(owner);"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_host_jobs_status ON host_jobs(status);"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_host_jobs_dedup "
                "ON host_jobs(dedup_key);"
            )

            # Datamgr market data control tables
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS datamgr_instruments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL UNIQUE,
                    connection TEXT DEFAULT '',
                    broker_id INTEGER DEFAULT 0,
                    description TEXT DEFAULT '',
                    tick_size REAL NOT NULL DEFAULT 0.00001,
                    tick_step REAL NOT NULL DEFAULT 0.00001,
                    tick_value_in_money REAL NOT NULL DEFAULT 10.0,
                    point_value REAL NOT NULL DEFAULT 100000.0,
                    decimals INTEGER NOT NULL DEFAULT 5,
                    default_spread REAL NOT NULL DEFAULT 0.0001,
                    default_slippage REAL NOT NULL DEFAULT 0.0,
                    min_volume REAL NOT NULL DEFAULT 0.01,
                    max_volume REAL NOT NULL DEFAULT 100.0,
                    lot_step REAL NOT NULL DEFAULT 0.01,
                    margin_rate REAL NOT NULL DEFAULT 0.05,
                    swap_long REAL NOT NULL DEFAULT 0.0,
                    swap_short REAL NOT NULL DEFAULT 0.0,
                    swap_3day_day INTEGER NOT NULL DEFAULT 3,
                    commissions TEXT DEFAULT '0.0',
                    data_type TEXT DEFAULT 'Forex',
                    alias TEXT DEFAULT '',
                    exchange TEXT DEFAULT '',
                    country TEXT DEFAULT '',
                    sector TEXT DEFAULT '',
                    created_at_utc TEXT NOT NULL,
                    updated_at_utc TEXT NOT NULL
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS datamgr_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT DEFAULT '',
                    timezone TEXT NOT NULL DEFAULT 'UTC',
                    windows_json TEXT NOT NULL DEFAULT '[]',
                    holidays_json TEXT NOT NULL DEFAULT '[]',
                    is_default INTEGER NOT NULL DEFAULT 0
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS datamgr_datasets (
                    id TEXT PRIMARY KEY,
                    source TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    underlying TEXT NOT NULL,
                    instrument TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    broker TEXT NOT NULL,
                    broker_name TEXT NOT NULL,
                    timezone TEXT NOT NULL,
                    category TEXT NOT NULL,
                    date_from TEXT NOT NULL,
                    date_to TEXT NOT NULL,
                    bars INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    path TEXT NOT NULL DEFAULT '',
                    data_kind TEXT NOT NULL DEFAULT 'bars',
                    quality_score REAL NOT NULL DEFAULT 1.0,
                    lineage_json TEXT NOT NULL DEFAULT '{}',
                    schema_version INTEGER NOT NULL DEFAULT 1
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS datamgr_stock_group (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    system INTEGER NOT NULL DEFAULT 0,
                    description TEXT DEFAULT ''
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS datamgr_stock (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT NOT NULL,
                    basket_id INTEGER NOT NULL,
                    date_from TEXT NOT NULL,
                    date_to TEXT,
                    FOREIGN KEY(basket_id) REFERENCES datamgr_stock_group(id)
                );
                """
            )

            # Record initial schema version if not recorded
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM schema_migrations WHERE version = 1;")
            now_str = datetime.now(UTC).isoformat()
            if cur.fetchone()[0] == 0:
                conn.execute(
                    """
                    INSERT INTO schema_migrations (
                        version, name, applied_at_utc, checksum
                    ) VALUES (1, 'initial_host_control_tables', ?, 'v1_canonical_hash');
                    """,
                    (now_str,),
                )

        self._initialized = True
        logger.info(
            "Host database schema initialized",
            extra={
                "version": _CURRENT_SCHEMA_VERSION,
                "fr_id": "FR-HOST-PERSISTENCE-SCHEMA-VERIFICATION",
            },
        )

    def list_migrations(self) -> list[MigrationRecord]:
        """List all applied schema migration records in ascending version order."""
        with self._db.connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT version, name, applied_at_utc, checksum "
                "FROM schema_migrations ORDER BY version ASC;"
            )
            rows = cur.fetchall()

        return [
            MigrationRecord(
                version=r["version"],
                name=r["name"],
                applied_at_utc=datetime.fromisoformat(r["applied_at_utc"]),
                checksum=r["checksum"],
            )
            for r in rows
        ]

    def verify_schema(self) -> bool:
        """Verify that required tables exist and schema version is compatible.

        Returns:
            True if schema is valid.

        Raises:
            IncompatibleSchemaError: If required tables are missing or schema
                is corrupt.
        """
        required_tables = {"schema_migrations", "host_entities", "host_leases"}
        with self._db.connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
            existing_tables = {row[0] for row in cur.fetchall()}

            missing = required_tables - existing_tables
            if missing:
                msg = f"Incompatible database schema: missing required tables {missing}"
                logger.error(
                    msg,
                    extra={"fr_id": "FR-HOST-PERSISTENCE-SCHEMA-VERIFICATION"},
                )
                raise IncompatibleSchemaError(msg)

            cur.execute("SELECT MAX(version) FROM schema_migrations;")
            row = cur.fetchone()
            current_ver = row[0] if row and row[0] is not None else 0
            if current_ver < _CURRENT_SCHEMA_VERSION:
                msg = (
                    f"Outdated database schema version {current_ver}; "
                    f"expected at least {_CURRENT_SCHEMA_VERSION}"
                )
                logger.error(
                    msg,
                    extra={"fr_id": "FR-HOST-PERSISTENCE-SCHEMA-VERIFICATION"},
                )
                raise IncompatibleSchemaError(msg)

        return True

    def drop_obsolete_sessions(
        self, *, expected_count: int, expires_before: float
    ) -> int:
        """Drop the obsolete table only when its schema and row predicates match.

        The caller owns backup, approval and cutoff policy. This operation never
        runs during initialization and never changes the singular host_session.
        """
        if expected_count < 0 or not (0 < expires_before < float("inf")):
            raise ValidationError("Invalid obsolete-table cleanup predicates")
        logger.debug(
            "Inspecting obsolete session storage",
            extra={"fr_id": "FR-HOST-PERSISTENCE-SCHEMA-VERIFICATION"},
        )
        with self._db.transaction() as conn:
            objects = conn.execute(
                "SELECT type, name, tbl_name, sql FROM sqlite_master"
            ).fetchall()
            if not any(row["name"] == "host_sessions" for row in objects):
                logger.info(
                    "Obsolete session table already absent",
                    extra={"fr_id": "FR-HOST-PERSISTENCE-SCHEMA-VERIFICATION"},
                )
                return 0
            columns = conn.execute("PRAGMA table_info(host_sessions)").fetchall()
            shape = [
                (r["name"], r["type"], r["notnull"], r["dflt_value"], r["pk"])
                for r in columns
            ]
            if shape != [
                ("token_hash", "TEXT", 0, None, 1),
                ("username", "TEXT", 1, None, 0),
                ("issued_at", "REAL", 1, None, 0),
                ("expires_at", "REAL", 1, None, 0),
                ("revoked", "INTEGER", 1, "0", 0),
            ]:
                raise IncompatibleSchemaError("Obsolete session schema differs")
            for row in objects:
                if row["type"] == "table" and row["name"] == "host_sessions":
                    continue
                if row["sql"] and re.search(
                    r"\bhost_sessions\b", str(row["sql"]), re.IGNORECASE
                ):
                    raise IncompatibleSchemaError("Obsolete table has dependencies")
            row = conn.execute(
                "SELECT COUNT(*) AS total, COUNT(CASE WHEN "
                "typeof(issued_at) IN ('real', 'integer') AND "
                "typeof(expires_at) IN ('real', 'integer') AND "
                "issued_at <= expires_at AND expires_at <= ? "
                "THEN 1 END) AS matched FROM host_sessions",
                (expires_before,),
            ).fetchone()
            if row is None:
                raise CorruptDataError("Obsolete table count unavailable")
            if row["total"] != expected_count or row["matched"] != expected_count:
                raise RevisionConflictError(
                    "Obsolete session rows differ from approval"
                )
            conn.execute("DROP TABLE host_sessions")
        logger.info(
            "Obsolete session table removed",
            extra={
                "row_count": expected_count,
                "fr_id": "FR-HOST-PERSISTENCE-SCHEMA-VERIFICATION",
            },
        )
        return expected_count


# ============================================================================
# Narrow Typed Repository
# ============================================================================


class TypedRepository[T: BaseModel]:
    """Narrow, parameterized entity repository with monotonic revision concurrency."""

    def __init__(
        self,
        db: DatabaseManager,
        *,
        entity_type: str,
        model_cls: type[T],
        scope: str = "workspace",
    ) -> None:
        """Initialize TypedRepository for a given entity type and Pydantic model.

        Args:
            db: Central host DatabaseManager.
            entity_type: Categorical name of entity collection.
            model_cls: Pydantic model class for serialization/deserialization.
            scope: Default authorization or tenant scope.
        """
        validate_identifier(entity_type, "entity_type")
        validate_identifier(scope, "scope")
        self._db = db
        self.entity_type = entity_type
        self.model_cls = model_cls
        self.scope = scope

    def get(
        self,
        entity_id: str,
    ) -> T | None:
        """Retrieve and deserialize an entity by ID if present.

        Args:
            entity_id: Unique entity identifier.

        Returns:
            Deserialized Pydantic model instance, or None if absent.
        """
        logger.debug(
            "TypedRepository.get storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-TYPED-REPOSITORY"},
        )
        validate_identifier(entity_id, "entity_id")
        sql = (
            "SELECT payload FROM host_entities "
            "WHERE entity_id = ? AND entity_type = ? AND scope = ?;"
        )
        params = (entity_id, self.entity_type, self.scope)

        with self._db.connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            row = cur.fetchone()

        if row is None:
            return None

        try:
            raw_payload = json.loads(row["payload"])
            return self.model_cls.model_validate(raw_payload)
        except Exception as exc:
            msg = (
                f"Corrupt data encountered deserializing {self.entity_type}:{entity_id}"
            )
            logger.exception(msg, extra={"error": str(exc)})
            raise CorruptDataError(msg) from exc

    def get_record(
        self,
        entity_id: str,
    ) -> EntityRecord | None:
        """Retrieve full EntityRecord envelope including revision metadata.

        Args:
            entity_id: Unique entity identifier.

        Returns:
            EntityRecord record, or None if absent.
        """
        logger.debug(
            "TypedRepository.get_record storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-TYPED-REPOSITORY"},
        )
        validate_identifier(entity_id, "entity_id")
        sql = (
            "SELECT entity_id, entity_type, scope, payload, revision, "
            "created_at_utc, updated_at_utc FROM host_entities "
            "WHERE entity_id = ? AND entity_type = ? AND scope = ?;"
        )
        params = (entity_id, self.entity_type, self.scope)

        with self._db.connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            row = cur.fetchone()

        if row is None:
            return None

        try:
            return EntityRecord(
                entity_id=row["entity_id"],
                entity_type=row["entity_type"],
                scope=row["scope"],
                payload=json.loads(row["payload"]),
                revision=row["revision"],
                created_at_utc=datetime.fromisoformat(row["created_at_utc"]),
                updated_at_utc=datetime.fromisoformat(row["updated_at_utc"]),
            )
        except Exception as exc:
            msg = f"Corrupt envelope for entity {self.entity_type}:{entity_id}"
            raise CorruptDataError(msg) from exc

    def save(
        self,
        entity_id: str,
        model: T,
        *,
        expected_revision: int | None = None,
    ) -> EntityRecord:
        """Save or update entity, verifying optimistic concurrency revision.

        Args:
            entity_id: Unique entity identifier.
            model: Pydantic model payload to persist.
            expected_revision: Expected current revision for optimistic
                concurrency check.

        Returns:
            Updated EntityRecord envelope.

        Raises:
            RevisionConflictError: If expected_revision does not match persisted record.
        """
        logger.debug(
            "TypedRepository.save storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-TYPED-REPOSITORY"},
        )
        validate_identifier(entity_id, "entity_id")
        payload_dict = model.model_dump(mode="json")
        payload_json = canonical_json(payload_dict)
        now_dt = datetime.now(UTC)
        now_str = now_dt.isoformat()

        def _execute(conn: sqlite3.Connection) -> EntityRecord:
            cur = conn.cursor()
            cur.execute(
                "SELECT revision, created_at_utc FROM host_entities "
                "WHERE entity_id = ? AND entity_type = ? AND scope = ?;",
                (entity_id, self.entity_type, self.scope),
            )
            existing = cur.fetchone()

            if existing is not None:
                current_rev = int(existing["revision"])
                created_at = existing["created_at_utc"]
                if expected_revision is not None and expected_revision != current_rev:
                    msg = (
                        f"Revision conflict for {self.entity_type}:{entity_id}: "
                        f"expected {expected_revision}, but current is {current_rev}"
                    )
                    logger.warning(
                        msg,
                        extra={"fr_id": "FR-HOST-PERSISTENCE-REVISION-CONCURRENCY"},
                    )
                    raise RevisionConflictError(msg)

                new_rev = current_rev + 1
                cur.execute(
                    """
                    UPDATE host_entities
                    SET payload = ?, revision = ?, updated_at_utc = ?
                    WHERE entity_id = ? AND entity_type = ? AND scope = ?;
                    """,
                    (
                        payload_json,
                        new_rev,
                        now_str,
                        entity_id,
                        self.entity_type,
                        self.scope,
                    ),
                )
                logger.info(
                    "Entity updated",
                    extra={
                        "entity_id": entity_id,
                        "entity_type": self.entity_type,
                        "revision": new_rev,
                        "fr_id": "FR-HOST-PERSISTENCE-TYPED-REPOSITORY",
                    },
                )
                return EntityRecord(
                    entity_id=entity_id,
                    entity_type=self.entity_type,
                    scope=self.scope,
                    payload=payload_dict,
                    revision=new_rev,
                    created_at_utc=datetime.fromisoformat(created_at),
                    updated_at_utc=now_dt,
                )

            # Insert new record
            if expected_revision is not None and expected_revision != 0:
                msg = (
                    f"Revision conflict on insert for {self.entity_type}:{entity_id}: "
                    f"expected {expected_revision}, record does not exist"
                )
                raise RevisionConflictError(msg)

            new_rev = 1
            cur.execute(
                """
                INSERT INTO host_entities (
                    entity_id, entity_type, scope, payload, revision,
                    created_at_utc, updated_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    entity_id,
                    self.entity_type,
                    self.scope,
                    payload_json,
                    new_rev,
                    now_str,
                    now_str,
                ),
            )
            logger.info(
                "Entity created",
                extra={
                    "entity_id": entity_id,
                    "entity_type": self.entity_type,
                    "revision": new_rev,
                    "fr_id": "FR-HOST-PERSISTENCE-TYPED-REPOSITORY",
                },
            )
            return EntityRecord(
                entity_id=entity_id,
                entity_type=self.entity_type,
                scope=self.scope,
                payload=payload_dict,
                revision=new_rev,
                created_at_utc=now_dt,
                updated_at_utc=now_dt,
            )

        with self._db.transaction() as conn:
            return _execute(conn)

    def delete(
        self,
        entity_id: str,
        *,
        expected_revision: int | None = None,
    ) -> bool:
        """Delete an entity by ID with optional expected revision check.

        Args:
            entity_id: Unique entity identifier.
            expected_revision: Optional revision concurrency assertion.

        Returns:
            True if entity was deleted; False if not found.
        """
        logger.debug(
            "TypedRepository.delete storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-TYPED-REPOSITORY"},
        )
        validate_identifier(entity_id, "entity_id")

        def _execute(conn: sqlite3.Connection) -> bool:
            cur = conn.cursor()
            if expected_revision is not None:
                cur.execute(
                    "SELECT revision FROM host_entities "
                    "WHERE entity_id = ? AND entity_type = ? AND scope = ?;",
                    (entity_id, self.entity_type, self.scope),
                )
                row = cur.fetchone()
                if row is None:
                    return False
                curr_rev = int(row["revision"])
                if curr_rev != expected_revision:
                    msg = (
                        f"Revision conflict on delete for "
                        f"{self.entity_type}:{entity_id}: "
                        f"expected {expected_revision}, current is {curr_rev}"
                    )
                    raise RevisionConflictError(msg)

            cur.execute(
                "DELETE FROM host_entities "
                "WHERE entity_id = ? AND entity_type = ? AND scope = ?;",
                (entity_id, self.entity_type, self.scope),
            )
            return cur.rowcount > 0

        with self._db.transaction() as conn:
            return _execute(conn)

    def list(
        self,
        *,
        cursor: str | None = None,
        limit: int = 50,
    ) -> Page[T]:
        """List entities ordered by entity_id with keyset pagination.

        Args:
            cursor: Optional entity_id cursor representing pagination position.
            limit: Maximum items to retrieve per page (bounded 1..500).

        Returns:
            Page containing deserialized models and next cursor.
        """
        logger.debug(
            "TypedRepository.list storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-TYPED-REPOSITORY"},
        )
        clamped_limit = max(1, min(limit, 500))
        with self._db.connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT COUNT(*) FROM host_entities "
                "WHERE entity_type = ? AND scope = ?;",
                (self.entity_type, self.scope),
            )
            total = int(cur.fetchone()[0])

            if cursor:
                cur.execute(
                    "SELECT entity_id, payload FROM host_entities "
                    "WHERE entity_type = ? AND scope = ? AND entity_id > ? "
                    "ORDER BY entity_id ASC LIMIT ?;",
                    (self.entity_type, self.scope, cursor, clamped_limit + 1),
                )
            else:
                cur.execute(
                    "SELECT entity_id, payload FROM host_entities "
                    "WHERE entity_type = ? AND scope = ? "
                    "ORDER BY entity_id ASC LIMIT ?;",
                    (self.entity_type, self.scope, clamped_limit + 1),
                )

            rows = cur.fetchall()

        has_more = len(rows) > clamped_limit
        result_rows = rows[:clamped_limit]
        items: list[T] = []

        for r in result_rows:
            raw_payload = json.loads(r["payload"])
            items.append(self.model_cls.model_validate(raw_payload))

        next_cursor = result_rows[-1]["entity_id"] if has_more and result_rows else None
        return Page(items=items, total_count=total, next_cursor=next_cursor)


# ============================================================================
# Authoritative Settings Store
# ============================================================================


class SettingsStore:
    """Authoritative SQLite persistence manager for scoped host settings.

    Provides transactional, parameterized CRUD operations against the `host_settings`
    table with strict connection lifecycles, concurrency serialization, and
    isolated storage paths.
    """

    def __init__(
        self,
        db_path: Path | str | None = None,
        *,
        busy_timeout: float = _BUSY_TIMEOUT_SECONDS,
        db: DatabaseManager | None = None,
    ) -> None:
        """Initialize SettingsStore with an authoritative database file path or manager.

        Args:
            db_path: Optional path to the SQLite database file or ':memory:'.
            busy_timeout: Timeout in seconds for SQLite lock waits.
            db: Optional preexisting DatabaseManager instance.
        """
        self._db: DatabaseManager = db or DatabaseManager(
            db_path, busy_timeout=busy_timeout
        )
        self._busy_timeout: float = busy_timeout

    @property
    def db_path(self) -> Path:
        """Return the resolved database file path."""
        return self._db.database_path

    @property
    def db(self) -> DatabaseManager:
        """Return the underlying DatabaseManager instance."""
        return self._db

    def initialize(self) -> None:
        """Verify existing database schema or create required table transactionally.

        Raises:
            IncompatibleSchemaError: If the existing table schema is incompatible.
            PersistenceError: If table creation or schema verification fails.
        """
        logger.debug(
            "SettingsStore.initialize storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-SETTINGS"},
        )
        self._db.schema.initialize()
        with self._db.connection(query_only=False) as conn:
            try:
                row = conn.execute(
                    "SELECT sql FROM sqlite_master WHERE type = 'table' "
                    "AND name = 'host_settings'"
                ).fetchone()

                if row is None:
                    self._create_settings_table(conn)
                    self._ensure_revision_exists(conn)
                    logger.info(
                        "FR-HOST-SETTINGS-SCHEMA: Initialized host_settings table.",
                        extra={
                            "db_path": str(self._db.database_path),
                            "fr_id": "FR-HOST-SETTINGS-SCHEMA",
                        },
                    )
                    return

                self._verify_existing_schema(conn)
                self._ensure_revision_exists(conn)
                logger.debug(
                    "FR-HOST-SETTINGS-SCHEMA: Verified host_settings schema.",
                    extra={"fr_id": "FR-HOST-SETTINGS-SCHEMA"},
                )
            except sqlite3.OperationalError as exc:
                if "busy" in str(exc).lower() or "locked" in str(exc).lower():
                    raise StorageBusyError(
                        "Database is busy during schema initialization"
                    ) from exc
                raise PersistenceError("Failed to initialize database schema") from exc

    def _create_settings_table(self, conn: sqlite3.Connection) -> None:
        """Create the host_settings table inside an immediate transaction."""
        conn.execute("BEGIN IMMEDIATE")
        conn.execute(
            """
            CREATE TABLE host_settings (
                scope TEXT NOT NULL,
                key TEXT NOT NULL,
                value_json TEXT NOT NULL,
                schema_version INTEGER NOT NULL DEFAULT 1,
                updated_at_utc TEXT NOT NULL,
                PRIMARY KEY (scope, key)
            )
            """
        )
        conn.execute("COMMIT")

    def _verify_existing_schema(self, conn: sqlite3.Connection) -> None:
        """Verify columns and constraints of existing host_settings table.

        Raises:
            IncompatibleSchemaError: If any column definition or constraint mismatches.
        """
        info_rows = conn.execute("PRAGMA table_info(host_settings)").fetchall()
        cols: dict[str, sqlite3.Row] = {r["name"]: r for r in info_rows}
        required: dict[str, tuple[str, int, int]] = {
            "scope": ("TEXT", 1, 1),
            "key": ("TEXT", 1, 2),
            "value_json": ("TEXT", 1, 0),
            "schema_version": ("INTEGER", 1, 0),
            "updated_at_utc": ("TEXT", 1, 0),
        }

        for col_name, (expected_type, notnull, pk) in required.items():
            if col_name not in cols:
                raise IncompatibleSchemaError(
                    f"Missing required column '{col_name}' in host_settings"
                )
            col = cols[col_name]
            if (
                col["type"].upper() != expected_type
                or col["notnull"] != notnull
                or col["pk"] != pk
            ):
                raise IncompatibleSchemaError(
                    f"Incompatible column definition for '{col_name}' in host_settings"
                )

    def _ensure_revision_exists(self, conn: sqlite3.Connection) -> None:
        """Ensure the internal _system:revision key exists in host_settings."""
        row = conn.execute(
            "SELECT value_json FROM host_settings "
            "WHERE scope = '_system' AND key = 'revision'"
        ).fetchone()
        if row is None:
            now_ts = now_utc_iso()
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(
                """
                INSERT OR IGNORE INTO host_settings (
                    scope, key, value_json, schema_version, updated_at_utc
                )
                VALUES ('_system', 'revision', '1', ?, ?)
                """,
                (SCHEMA_VERSION, now_ts),
            )
            conn.execute("COMMIT")

    def get_revision(self) -> int:
        """Query current monotonic revision counter."""
        logger.debug(
            "SettingsStore.get_revision storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-SETTINGS"},
        )
        if not self._db.is_memory and not self._db.database_path.exists():
            return 1
        with self._db.connection(query_only=True) as conn:
            try:
                row = conn.execute(
                    "SELECT value_json FROM host_settings "
                    "WHERE scope = '_system' AND key = 'revision'"
                ).fetchone()
                if row is not None:
                    return int(json.loads(row["value_json"]))
            except (sqlite3.Error, ValueError, TypeError) as exc:
                logger.debug(
                    "FR-HOST-SETTINGS-LOAD: Revision query fallback (%s)",
                    exc,
                    extra={"fr_id": "FR-HOST-SETTINGS-LOAD"},
                )
        return 1

    def read_settings(
        self,
        scope: str,
        *,
        key: str | None = None,
        after_key: str | None = None,
        limit: int = DEFAULT_READ_LIMIT,
    ) -> SettingsPage:
        """Query scoped host settings with pagination and optional single key lookup."""
        logger.debug(
            "SettingsStore.read_settings storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-SETTINGS"},
        )
        validate_identifier(scope, "scope")
        if key is not None:
            validate_identifier(key, "key")
        if after_key is not None:
            validate_identifier(after_key, "after_key")
        if not (1 <= limit <= MAX_READ_LIMIT):
            raise ValidationError(
                f"limit must be between 1 and {MAX_READ_LIMIT}, got {limit}"
            )

        if not self._db.is_memory and not self._db.database_path.exists():
            return SettingsPage(items=[], next_key=None)

        with self._db.connection(query_only=True) as conn:
            try:
                if key is not None:
                    return self._read_single_key(conn, scope, key)
                return self._read_paginated_keys(conn, scope, after_key, limit)
            except sqlite3.OperationalError as exc:
                if "busy" in str(exc).lower() or "locked" in str(exc).lower():
                    raise StorageBusyError(
                        "Database is busy while reading settings"
                    ) from exc
                raise PersistenceError("Failed to query host settings") from exc

    def _read_single_key(
        self, conn: sqlite3.Connection, scope: str, key: str
    ) -> SettingsPage:
        """Read a single key from host_settings."""
        row = conn.execute(
            """
            SELECT scope, key, value_json, schema_version, updated_at_utc
            FROM host_settings
            WHERE scope = ? AND key = ?
            """,
            (scope, key),
        ).fetchone()
        if row is None:
            return SettingsPage(items=[], next_key=None)

        record = self._row_to_record(row)
        return SettingsPage(items=[record], next_key=None)

    def _read_paginated_keys(
        self,
        conn: sqlite3.Connection,
        scope: str,
        after_key: str | None,
        limit: int,
    ) -> SettingsPage:
        """Read a keyset-paginated slice of settings."""
        if after_key is not None:
            rows = conn.execute(
                """
                SELECT scope, key, value_json, schema_version, updated_at_utc
                FROM host_settings
                WHERE scope = ? AND key > ?
                ORDER BY key ASC
                LIMIT ?
                """,
                (scope, after_key, limit + 1),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT scope, key, value_json, schema_version, updated_at_utc
                FROM host_settings
                WHERE scope = ?
                ORDER BY key ASC
                LIMIT ?
                """,
                (scope, limit + 1),
            ).fetchall()

        has_more = len(rows) > limit
        display_rows = rows[:limit] if has_more else rows
        next_cursor = display_rows[-1]["key"] if has_more and display_rows else None

        records = [self._row_to_record(r) for r in display_rows]
        return SettingsPage(items=records, next_key=next_cursor)

    def read_all(self) -> tuple[int, list[SettingRecord]]:
        """Read configuration records and their global storage revision."""
        logger.debug(
            "SettingsStore.read_all storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-SETTINGS"},
        )
        if not self._db.is_memory and not self._db.database_path.exists():
            return 1, []
        with self._db.connection(query_only=True) as conn:
            try:
                rows = conn.execute(
                    "SELECT * FROM host_settings ORDER BY scope, key"
                ).fetchall()
            except sqlite3.OperationalError as exc:
                logger.warning(
                    "Settings storage read unavailable",
                    extra={
                        "error_type": type(exc).__name__,
                        "fr_id": "FR-HOST-PERSISTENCE-SETTINGS",
                    },
                )
                return 1, []
        revision = 1
        records: list[SettingRecord] = []
        for row in rows:
            if row["scope"] == "_system" and row["key"] == "revision":
                try:
                    revision = int(json.loads(row["value_json"]))
                except (ValueError, TypeError) as exc:
                    raise CorruptDataError("Corrupt settings revision") from exc
                continue
            try:
                records.append(self._row_to_record(row))
            except CorruptDataError:
                logger.warning(
                    "Skipping corrupt settings row",
                    extra={"fr_id": "FR-HOST-PERSISTENCE-SETTINGS"},
                )
        logger.debug(
            "Read settings records",
            extra={"count": len(records), "fr_id": "FR-HOST-PERSISTENCE-SETTINGS"},
        )
        return revision, records

    def _validate_batch_changes(
        self, changes: dict[str, dict[str, Any]]
    ) -> list[tuple[str, str, Any, str]]:
        """Validate all items in a batch update mapping."""
        total_items = sum(len(v) for v in changes.values() if isinstance(v, dict))
        if total_items > MAX_BATCH_SIZE:
            raise ValidationError(
                f"Total batch items {total_items} exceeds limit {MAX_BATCH_SIZE}"
            )

        validated_items: list[tuple[str, str, Any, str]] = []
        for scope, scope_changes in changes.items():
            validate_identifier(scope, "scope")
            if not isinstance(scope_changes, dict):
                raise ValidationError(
                    f"Scope changes for '{scope}' must be a dictionary"
                )
            for key, val in scope_changes.items():
                validate_identifier(key, "key")
                encoded = canonical_json(val)
                validated_items.append((scope, key, val, encoded))

        return validated_items

    def _check_revision_match(
        self, expected_revision: int | None, current_revision: int
    ) -> None:
        """Verify that expected revision matches current revision."""
        if expected_revision is not None and expected_revision != current_revision:
            logger.warning(
                "FR-HOST-SETTINGS-UPDATE: Revision conflict. Current: %d, Expected: %d",
                current_revision,
                expected_revision,
                extra={"fr_id": "FR-HOST-SETTINGS-UPDATE"},
            )
            raise RevisionConflictError(
                f"Settings revision conflict: expected {expected_revision}, "
                f"but current is {current_revision}"
            )

    def update_batch(
        self,
        changes: dict[str, dict[str, Any]],
        *,
        expected_revision: int | None = None,
        deletions: tuple[tuple[str, str], ...] = (),
    ) -> tuple[int, list[SettingRecord]]:
        """Atomically update multiple scoped settings with optimistic locking."""
        logger.debug(
            "SettingsStore.update_batch storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-SETTINGS"},
        )
        if not changes and not deletions:
            return self.read_all()

        validated_items = self._validate_batch_changes(changes)
        updates = {(scope, key) for scope, key, _, _ in validated_items}
        if len(deletions) > MAX_BATCH_SIZE or len(set(deletions)) != len(deletions):
            raise ValidationError("Invalid settings deletion batch.")
        for scope, key in deletions:
            validate_identifier(scope, "scope")
            validate_identifier(key, "key")
            if scope == "_system" or (scope, key) in updates:
                raise ValidationError("Protected or ambiguous settings deletion.")

        with self._db.transaction() as conn:
            self._check_table_exists(conn)

            rev_row = conn.execute(
                "SELECT value_json FROM host_settings "
                "WHERE scope = '_system' AND key = 'revision'"
            ).fetchone()
            current_revision = (
                int(json.loads(rev_row["value_json"])) if rev_row is not None else 1
            )

            self._check_revision_match(expected_revision, current_revision)

            now_ts = now_utc_iso()
            changed_count = 0
            for scope, key, _val, raw_json in validated_items:
                existing = conn.execute(
                    "SELECT value_json FROM host_settings WHERE scope = ? AND key = ?",
                    (scope, key),
                ).fetchone()
                if existing is not None and existing["value_json"] == raw_json:
                    continue

                conn.execute(
                    """
                    INSERT INTO host_settings (
                        scope, key, value_json, schema_version, updated_at_utc
                    )
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(scope, key) DO UPDATE SET
                        value_json = excluded.value_json,
                        schema_version = excluded.schema_version,
                        updated_at_utc = excluded.updated_at_utc
                    """,
                    (scope, key, raw_json, SCHEMA_VERSION, now_ts),
                )
                changed_count += 1

            for scope, key in deletions:
                cursor = conn.execute(
                    "DELETE FROM host_settings WHERE scope = ? AND key = ?",
                    (scope, key),
                )
                changed_count += cursor.rowcount

            new_revision = (
                current_revision + 1 if changed_count > 0 else current_revision
            )
            if changed_count > 0:
                conn.execute(
                    """
                    INSERT INTO host_settings (
                        scope, key, value_json, schema_version, updated_at_utc
                    )
                    VALUES ('_system', 'revision', ?, ?, ?)
                    ON CONFLICT(scope, key) DO UPDATE SET
                        value_json = excluded.value_json,
                        schema_version = excluded.schema_version,
                        updated_at_utc = excluded.updated_at_utc
                    """,
                    (json.dumps(new_revision), SCHEMA_VERSION, now_ts),
                )

        logger.info(
            "FR-HOST-SETTINGS-UPDATE: Atomically updated %d setting(s). Revision: %d",
            changed_count,
            new_revision,
            extra={
                "changed_count": changed_count,
                "revision": new_revision,
                "fr_id": "FR-HOST-SETTINGS-UPDATE",
            },
        )
        return self.read_all()

    def backup_to(self, destination: Path) -> None:
        """Create a consistent SQLite backup without overwriting an existing file."""
        target = destination.resolve()
        if self._db.is_memory or not self.db_path.exists():
            raise ValidationError("Backup requires an existing file database.")
        if target == self.db_path.resolve() or target.exists():
            raise ValidationError("Backup destination must be a new file.")
        target.parent.mkdir(parents=True, exist_ok=True)
        # Exclusive creation closes the existence-check race before SQLite opens it.
        with target.open("xb"):
            pass
        try:
            with self._db.connection(query_only=True) as source:
                backup = sqlite3.connect(str(target), timeout=self._busy_timeout)
                try:
                    source.backup(backup)
                    if backup.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                        raise PersistenceError("Backup integrity verification failed.")
                finally:
                    backup.close()
        except sqlite3.Error as exc:
            logger.error(  # noqa: TRY400 - Never expose database exception payloads.
                "Settings database backup failed",
                extra={"fr_id": "FR-HOST-PERSISTENCE-SETTINGS"},
            )
            raise PersistenceError("Settings database backup failed.") from exc
        logger.info(
            "Settings database backup completed",
            extra={"fr_id": "FR-HOST-PERSISTENCE-SETTINGS"},
        )

    def _check_table_exists(self, conn: sqlite3.Connection) -> None:
        """Verify that the host_settings table exists."""
        row = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' "
            "AND name = 'host_settings'"
        ).fetchone()
        if row is None:
            raise IncompatibleSchemaError(
                "Table 'host_settings' does not exist in target database"
            )

    @staticmethod
    def _row_to_record(row: sqlite3.Row) -> SettingRecord:
        """Convert SQLite Row to SettingRecord."""
        if row["schema_version"] != SCHEMA_VERSION:
            raise CorruptDataError(
                f"Unsupported schema version {row['schema_version']} "
                f"for key '{row['key']}'"
            )
        try:
            value = json.loads(row["value_json"])
        except (ValueError, TypeError) as exc:
            raise CorruptDataError(
                f"Corrupt JSON payload in row for key '{row['key']}'"
            ) from exc

        return SettingRecord(
            scope=str(row["scope"]),
            key=str(row["key"]),
            value=value,
            schema_version=int(row["schema_version"]),
            updated_at_utc=str(row["updated_at_utc"]),
        )


# ============================================================================
# Datamgr Entities Persistence (Instruments, Sessions, Datasets)
# ============================================================================


class InstrumentStore:
    """Authoritative host persistence operations for datamgr_instruments."""

    _columns = frozenset(
        {
            "connection",
            "broker_id",
            "description",
            "tick_size",
            "tick_step",
            "tick_value_in_money",
            "point_value",
            "decimals",
            "default_spread",
            "default_slippage",
            "min_volume",
            "max_volume",
            "lot_step",
            "margin_rate",
            "swap_long",
            "swap_short",
            "swap_3day_day",
            "commissions",
            "data_type",
            "alias",
            "exchange",
            "country",
            "sector",
            "created_at_utc",
            "updated_at_utc",
        }
    )

    def __init__(self, db: DatabaseManager) -> None:
        """Initialize with parent DatabaseManager."""
        self._db = db

    def create(self, record: dict[str, Any]) -> int:
        """Insert a new instrument record and return its generated ID."""
        logger.debug(
            "InstrumentStore.create storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-INSTRUMENTS"},
        )
        columns = [
            "symbol",
            "connection",
            "broker_id",
            "description",
            "tick_size",
            "tick_step",
            "tick_value_in_money",
            "point_value",
            "decimals",
            "default_spread",
            "default_slippage",
            "min_volume",
            "max_volume",
            "lot_step",
            "margin_rate",
            "swap_long",
            "swap_short",
            "swap_3day_day",
            "commissions",
            "data_type",
            "alias",
            "exchange",
            "country",
            "sector",
            "created_at_utc",
            "updated_at_utc",
        ]
        _validate_columns(record, self._columns | {"symbol"})
        _require_columns(record, tuple(columns))
        values = [record[col] for col in columns]
        sql = (
            "INSERT INTO datamgr_instruments ("
            "symbol, connection, broker_id, description, "
            "tick_size, tick_step, tick_value_in_money, point_value, "
            "decimals, default_spread, default_slippage, min_volume, "
            "max_volume, lot_step, margin_rate, swap_long, "
            "swap_short, swap_3day_day, commissions, data_type, "
            "alias, exchange, country, sector, "
            "created_at_utc, updated_at_utc"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, "
            "?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"
        )
        with self._db.transaction() as conn:
            cur = conn.cursor()
            cur.execute(sql, values)
            last_id = cur.lastrowid or 0
        logger.info(
            "Created instrument in datamgr_instruments: %s (id=%d)",
            record["symbol"],
            last_id,
            extra={"fr_id": "FR-HOST-PERSISTENCE-INSTRUMENTS"},
        )
        return last_id

    def get_by_symbol(self, symbol: str) -> dict[str, Any] | None:
        """Retrieve instrument record by symbol name."""
        logger.debug(
            "InstrumentStore.get_by_symbol storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-INSTRUMENTS"},
        )
        sql = "SELECT * FROM datamgr_instruments WHERE symbol = ?;"
        with self._db.connection(query_only=True) as conn:
            cur = conn.cursor()
            cur.execute(sql, (symbol,))
            row = cur.fetchone()
            if row is not None:
                return dict(row)
        return None

    def insert_if_absent(self, record: Mapping[str, Any]) -> bool:
        """Insert supplied instrument fields without replacing an existing symbol."""
        logger.debug(
            "InstrumentStore.insert_if_absent storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-INSTRUMENTS"},
        )
        columns = tuple(record)
        _validate_columns(record, self._columns | {"symbol"})
        placeholders = ", ".join("?" for _ in columns)
        sql = (
            f"INSERT OR IGNORE INTO datamgr_instruments ({', '.join(columns)}) "  # noqa: S608 - fixed columns/placeholders only
            f"VALUES ({placeholders})"
        )
        with self._db.transaction() as conn:
            inserted = conn.execute(sql, tuple(record.values())).rowcount > 0
        logger.info(
            "Instrument insert-if-absent completed",
            extra={"inserted": inserted, "fr_id": "FR-HOST-PERSISTENCE-INSTRUMENTS"},
        )
        return inserted

    def list_instruments(
        self,
        connection: str | None = None,
        data_type: str | None = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """List instruments with optional connection or data_type filter."""
        logger.debug(
            "InstrumentStore.list_instruments storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-INSTRUMENTS"},
        )
        if connection and data_type:
            sql = (
                "SELECT * FROM datamgr_instruments WHERE connection = ? "
                "AND data_type = ? ORDER BY symbol ASC LIMIT ? OFFSET ?;"
            )
            params = [connection, data_type, limit, offset]
        elif connection:
            sql = (
                "SELECT * FROM datamgr_instruments WHERE connection = ? "
                "ORDER BY symbol ASC LIMIT ? OFFSET ?;"
            )
            params = [connection, limit, offset]
        elif data_type:
            sql = (
                "SELECT * FROM datamgr_instruments WHERE data_type = ? "
                "ORDER BY symbol ASC LIMIT ? OFFSET ?;"
            )
            params = [data_type, limit, offset]
        else:
            sql = (
                "SELECT * FROM datamgr_instruments ORDER BY symbol ASC "
                "LIMIT ? OFFSET ?;"
            )
            params = [limit, offset]

        with self._db.connection(query_only=True) as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            return [dict(r) for r in cur.fetchall()]

    def update(self, symbol: str, updates: dict[str, Any]) -> bool:
        """Update fields for a symbol in datamgr_instruments."""
        logger.debug(
            "InstrumentStore.update storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-INSTRUMENTS"},
        )
        if not updates:
            return True
        updates_copy = dict(updates)
        updates_copy.pop("id", None)
        updates_copy.pop("symbol", None)
        _validate_columns(updates_copy, self._columns)
        if not updates_copy:
            return True
        set_clause = ", ".join(f"{k} = ?" for k in updates_copy)
        sql = f"UPDATE datamgr_instruments SET {set_clause} WHERE symbol = ?;"  # noqa: S608
        params = [*list(updates_copy.values()), symbol]
        with self._db.transaction() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            success = cur.rowcount > 0
        logger.info(
            "Updated instrument %s (success=%s)",
            symbol,
            success,
            extra={"fr_id": "FR-HOST-PERSISTENCE-INSTRUMENTS"},
        )
        return success

    def delete(self, symbol: str) -> bool:
        """Delete an instrument record by symbol."""
        logger.debug(
            "InstrumentStore.delete storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-INSTRUMENTS"},
        )
        sql = "DELETE FROM datamgr_instruments WHERE symbol = ?;"
        with self._db.transaction() as conn:
            cur = conn.cursor()
            cur.execute(sql, (symbol,))
            success = cur.rowcount > 0
        logger.info(
            "Deleted instrument %s (success=%s)",
            symbol,
            success,
            extra={"fr_id": "FR-HOST-PERSISTENCE-INSTRUMENTS"},
        )
        return success

    def count(self) -> int:
        """Return total instrument count."""
        logger.debug(
            "InstrumentStore.count storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-INSTRUMENTS"},
        )
        sql = "SELECT COUNT(*) FROM datamgr_instruments;"
        with self._db.connection(query_only=True) as conn:
            cur = conn.cursor()
            cur.execute(sql)
            row = cur.fetchone()
            return int(row[0]) if row else 0


class HostSessionRecord(BaseModel):
    """Stored login lifecycle metadata without a usable bearer token."""

    session_id: str
    token_hash: str = Field(repr=False)
    username: str
    peer_id: str
    created_at_utc: str
    expires_at_utc: str
    revoked_at_utc: str | None = None
    status: str


class HostSessionStore:
    """CRUD for the existing singular host_session login lifecycle table."""

    def __init__(self, db: DatabaseManager) -> None:
        self._db = db
        self._initialized = False

    @property
    def db_path(self) -> Path:
        """Return the storage target for service binding checks."""
        return self._db.database_path

    def initialize(self) -> None:
        """Create the identical singular schema if absent, then verify columns."""
        if self._initialized:
            return
        with self._db.transaction() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS host_session ("
                "session_id TEXT PRIMARY KEY, token_hash TEXT NOT NULL UNIQUE, "
                "username TEXT NOT NULL, peer_id TEXT NOT NULL, "
                "created_at_utc TEXT NOT NULL, expires_at_utc TEXT NOT NULL, "
                "revoked_at_utc TEXT, status TEXT NOT NULL)"
            )
            columns = conn.execute("PRAGMA table_info(host_session)").fetchall()
            shape = [(r["name"], r["type"], r["notnull"], r["pk"]) for r in columns]
            if shape != [
                ("session_id", "TEXT", 0, 1),
                ("token_hash", "TEXT", 1, 0),
                ("username", "TEXT", 1, 0),
                ("peer_id", "TEXT", 1, 0),
                ("created_at_utc", "TEXT", 1, 0),
                ("expires_at_utc", "TEXT", 1, 0),
                ("revoked_at_utc", "TEXT", 0, 0),
                ("status", "TEXT", 1, 0),
            ]:
                raise IncompatibleSchemaError("Host session schema differs")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_host_session_status "
                "ON host_session(status)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_host_session_peer_id "
                "ON host_session(peer_id)"
            )
            conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_host_session_token_hash "
                "ON host_session(token_hash)"
            )
        self._initialized = True
        logger.info(
            "Host session storage verified",
            extra={"fr_id": "FR-HOST-PERSISTENCE-HOST-SESSIONS"},
        )

    def create(self, record: HostSessionRecord) -> None:
        """Insert caller-provided metadata atomically."""
        self.initialize()
        with self._db.transaction() as conn:
            conn.execute(
                "INSERT INTO host_session (session_id,token_hash,username,peer_id,"
                "created_at_utc,expires_at_utc,revoked_at_utc,status) "
                "VALUES (?,?,?,?,?,?,?,?)",
                tuple(record.model_dump().values()),
            )
        logger.info(
            "Host session record inserted",
            extra={"fr_id": "FR-HOST-PERSISTENCE-HOST-SESSIONS"},
        )

    def list_records(
        self, *, peer_id: str, limit: int = 1000
    ) -> list[HostSessionRecord]:
        """Read a bounded set of records belonging to the requested issuer."""
        if not 1 <= limit <= MAX_READ_LIMIT:
            raise ValidationError("Invalid host session read limit")
        self.initialize()
        with self._db.connection(query_only=True) as conn:
            rows = conn.execute(
                "SELECT * FROM host_session WHERE peer_id=? "
                "ORDER BY created_at_utc,session_id LIMIT ?",
                (peer_id, limit),
            ).fetchall()
        logger.debug(
            "Host session records read",
            extra={"fr_id": "FR-HOST-PERSISTENCE-HOST-SESSIONS", "count": len(rows)},
        )
        return [HostSessionRecord.model_validate(dict(row)) for row in rows]

    def update_status(
        self,
        *,
        peer_id: str,
        expected_status: str,
        status: str,
        revoked_at_utc: str | None,
        token_hash: str | None = None,
        username: str | None = None,
    ) -> int:
        """Conditionally update only the requested issuer and optional row filters."""
        self.initialize()
        sql = (
            "UPDATE host_session SET status=?,revoked_at_utc=? "
            "WHERE peer_id=? AND status=?"
        )
        values: list[str | None] = [status, revoked_at_utc, peer_id, expected_status]
        if token_hash is not None:
            sql += " AND token_hash=?"
            values.append(token_hash)
        if username is not None:
            sql += " AND username=?"
            values.append(username)
        with self._db.transaction() as conn:
            count = conn.execute(sql, values).rowcount
        logger.info(
            "Host session records updated",
            extra={"fr_id": "FR-HOST-PERSISTENCE-HOST-SESSIONS", "count": count},
        )
        return count


class SessionStore:
    """Authoritative host persistence operations for datamgr_sessions."""

    _columns = frozenset(
        {
            "description",
            "timezone",
            "windows_json",
            "holidays_json",
            "is_default",
        }
    )

    def __init__(self, db: DatabaseManager) -> None:
        """Initialize with parent DatabaseManager."""
        self._db = db

    def create(self, record: dict[str, Any]) -> int:
        """Insert a new session definition and return its generated ID."""
        logger.debug(
            "SessionStore.create storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-SESSIONS"},
        )
        columns = (
            "name",
            "description",
            "timezone",
            "windows_json",
            "holidays_json",
            "is_default",
        )
        _validate_columns(record, self._columns | {"name"})
        _require_columns(record, columns)
        values = [record[col] for col in columns]
        sql = (
            "INSERT INTO datamgr_sessions ("
            "name, description, timezone, windows_json, holidays_json, is_default"
            ") VALUES (?, ?, ?, ?, ?, ?);"
        )
        with self._db.transaction() as conn:
            cur = conn.cursor()
            cur.execute(sql, values)
            last_id = cur.lastrowid or 0
        logger.info(
            "Created session in datamgr_sessions: %s (id=%d)",
            record.get("name"),
            last_id,
            extra={"fr_id": "FR-HOST-PERSISTENCE-SESSIONS"},
        )
        return last_id

    def get_by_name(self, name: str) -> dict[str, Any] | None:
        """Retrieve session record by name."""
        logger.debug(
            "SessionStore.get_by_name storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-SESSIONS"},
        )
        sql = "SELECT * FROM datamgr_sessions WHERE name = ?;"
        with self._db.connection(query_only=True) as conn:
            cur = conn.cursor()
            cur.execute(sql, (name,))
            row = cur.fetchone()
            if row is not None:
                return dict(row)
        return None

    def upsert(self, record: Mapping[str, Any], *, only_if_absent: bool = False) -> int:
        """Atomically insert or update a session and return its existing/new ID."""
        logger.debug(
            "SessionStore.upsert storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-SESSIONS"},
        )
        columns = tuple(record)
        _validate_columns(record, self._columns | {"name"})
        placeholders = ", ".join("?" for _ in columns)
        updates = ", ".join(
            f"{col} = excluded.{col}" for col in columns if col != "name"
        )
        action = (
            "DO NOTHING"
            if only_if_absent or not updates
            else f"DO UPDATE SET {updates}"
        )
        sql = (
            f"INSERT INTO datamgr_sessions ({', '.join(columns)}) "  # noqa: S608 - fixed columns/placeholders only
            f"VALUES ({placeholders}) ON CONFLICT(name) {action}"
        )
        with self._db.transaction() as conn:
            conn.execute(sql, tuple(record.values()))
            row = conn.execute(
                "SELECT id FROM datamgr_sessions WHERE name = ?", (record["name"],)
            ).fetchone()
            session_id = int(row["id"])
        logger.info(
            "Session upsert completed",
            extra={"session_id": session_id, "fr_id": "FR-HOST-PERSISTENCE-SESSIONS"},
        )
        return session_id

    def list_sessions(self, limit: int = 1000, offset: int = 0) -> list[dict[str, Any]]:
        """List sessions in ascending name order."""
        logger.debug(
            "SessionStore.list_sessions storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-SESSIONS"},
        )
        sql = "SELECT * FROM datamgr_sessions ORDER BY name ASC LIMIT ? OFFSET ?;"
        with self._db.connection(query_only=True) as conn:
            cur = conn.cursor()
            cur.execute(sql, (limit, offset))
            return [dict(r) for r in cur.fetchall()]

    def update(self, name: str, updates: dict[str, Any]) -> bool:
        """Update fields for a session by name."""
        logger.debug(
            "SessionStore.update storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-SESSIONS"},
        )
        if not updates:
            return True
        updates_copy = dict(updates)
        updates_copy.pop("id", None)
        updates_copy.pop("name", None)
        _validate_columns(updates_copy, self._columns)
        set_clause = ", ".join(f"{k} = ?" for k in updates_copy)
        sql = f"UPDATE datamgr_sessions SET {set_clause} WHERE name = ?;"  # noqa: S608
        params = [*list(updates_copy.values()), name]
        with self._db.transaction() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            success = cur.rowcount > 0
        logger.info(
            "Updated session %s (success=%s)",
            name,
            success,
            extra={"fr_id": "FR-HOST-PERSISTENCE-SESSIONS"},
        )
        return success

    def delete(self, name: str) -> bool:
        """Delete session definition by name."""
        logger.debug(
            "SessionStore.delete storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-SESSIONS"},
        )
        sql = "DELETE FROM datamgr_sessions WHERE name = ?;"
        with self._db.transaction() as conn:
            cur = conn.cursor()
            cur.execute(sql, (name,))
            success = cur.rowcount > 0
        logger.info(
            "Deleted session %s (success=%s)",
            name,
            success,
            extra={"fr_id": "FR-HOST-PERSISTENCE-SESSIONS"},
        )
        return success

    def count(self) -> int:
        """Return total session definitions count."""
        logger.debug(
            "SessionStore.count storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-SESSIONS"},
        )
        sql = "SELECT COUNT(*) FROM datamgr_sessions;"
        with self._db.connection(query_only=True) as conn:
            cur = conn.cursor()
            cur.execute(sql)
            row = cur.fetchone()
            return int(row[0]) if row else 0


class DatasetStore:
    """Authoritative host persistence operations for datamgr_datasets."""

    def __init__(self, db: DatabaseManager) -> None:
        """Initialize with parent DatabaseManager."""
        self._db = db

    def sum_bars(self) -> int:
        """Return the sum of stored dataset bar counts."""
        logger.debug(
            "DatasetStore.sum_bars storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-DATASETS"},
        )
        with self._db.connection(query_only=True) as conn:
            row = conn.execute(
                "SELECT COALESCE(SUM(bars), 0) FROM datamgr_datasets"
            ).fetchone()
        logger.debug(
            "Dataset bar sum read", extra={"fr_id": "FR-HOST-PERSISTENCE-DATASETS"}
        )
        return int(row[0])

    def save(self, record: dict[str, Any], *, update_columns: tuple[str, ...]) -> str:
        """Insert a complete row or update caller-selected columns on conflict."""
        logger.debug(
            "DatasetStore.save storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-DATASETS"},
        )
        columns = [
            "id",
            "source",
            "symbol",
            "underlying",
            "instrument",
            "timeframe",
            "broker",
            "broker_name",
            "timezone",
            "category",
            "date_from",
            "date_to",
            "bars",
            "created_at",
            "updated_at",
            "path",
            "data_kind",
            "quality_score",
            "lineage_json",
            "schema_version",
        ]
        _validate_columns(record, frozenset(columns))
        _require_columns(record, tuple(columns))
        _validate_columns(dict.fromkeys(update_columns), frozenset(columns) - {"id"})
        values = [record[col] for col in columns]
        dataset_id = str(record["id"])
        updates = ", ".join(f"{col} = excluded.{col}" for col in update_columns)
        action = f"DO UPDATE SET {updates}" if updates else "DO NOTHING"
        placeholders = ", ".join("?" for _ in columns)
        sql = (
            f"INSERT INTO datamgr_datasets ({', '.join(columns)}) "  # noqa: S608 - fixed column allowlist and placeholders
            f"VALUES ({placeholders}) ON CONFLICT(id) {action}"
        )
        with self._db.transaction() as conn:
            cur = conn.cursor()
            cur.execute(sql, values)
        logger.info(
            "Saved dataset in datamgr_datasets: %s",
            dataset_id,
            extra={"fr_id": "FR-HOST-PERSISTENCE-DATASETS"},
        )
        return dataset_id

    def get_by_id(self, dataset_id: str) -> dict[str, Any] | None:
        """Retrieve dataset record by primary ID."""
        logger.debug(
            "DatasetStore.get_by_id storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-DATASETS"},
        )
        sql = "SELECT * FROM datamgr_datasets WHERE id = ?;"
        with self._db.connection(query_only=True) as conn:
            cur = conn.cursor()
            cur.execute(sql, (dataset_id,))
            row = cur.fetchone()
            if row is not None:
                return dict(row)
        return None

    def list_datasets(
        self,
        source: str | None = None,
        symbol: str | None = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """List datasets matching optional source and symbol filters."""
        logger.debug(
            "DatasetStore.list_datasets storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-DATASETS"},
        )
        if source and symbol:
            sql = (
                "SELECT * FROM datamgr_datasets WHERE source = ? "
                "AND symbol = ? ORDER BY symbol ASC, timeframe ASC LIMIT ? OFFSET ?;"
            )
            params = [source, symbol, limit, offset]
        elif source:
            sql = (
                "SELECT * FROM datamgr_datasets WHERE source = ? "
                "ORDER BY symbol ASC, timeframe ASC LIMIT ? OFFSET ?;"
            )
            params = [source, limit, offset]
        elif symbol:
            sql = (
                "SELECT * FROM datamgr_datasets WHERE symbol = ? "
                "ORDER BY symbol ASC, timeframe ASC LIMIT ? OFFSET ?;"
            )
            params = [symbol, limit, offset]
        else:
            sql = (
                "SELECT * FROM datamgr_datasets ORDER BY symbol ASC, "
                "timeframe ASC LIMIT ? OFFSET ?;"
            )
            params = [limit, offset]

        with self._db.connection(query_only=True) as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            return [dict(r) for r in cur.fetchall()]

    def delete(self, dataset_id: str) -> bool:
        """Delete dataset record by ID."""
        logger.debug(
            "DatasetStore.delete storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-DATASETS"},
        )
        sql = "DELETE FROM datamgr_datasets WHERE id = ?;"
        with self._db.transaction() as conn:
            cur = conn.cursor()
            cur.execute(sql, (dataset_id,))
            success = cur.rowcount > 0
        logger.info(
            "Deleted dataset %s (success=%s)",
            dataset_id,
            success,
            extra={"fr_id": "FR-HOST-PERSISTENCE-DATASETS"},
        )
        return success

    def count(self) -> int:
        """Return total dataset records count."""
        logger.debug(
            "DatasetStore.count storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-DATASETS"},
        )
        sql = "SELECT COUNT(*) FROM datamgr_datasets;"
        with self._db.connection(query_only=True) as conn:
            cur = conn.cursor()
            cur.execute(sql)
            row = cur.fetchone()
            return int(row[0]) if row else 0


class LeaseStore:
    """Store reservations with atomic holder/expiry predicates supplied by callers."""

    def __init__(self, db: DatabaseManager) -> None:
        self._db = db

    def get(self, lease_key: str) -> dict[str, Any] | None:
        """Read one reservation row without interpreting its lifecycle."""
        with self._db.connection(query_only=True) as conn:
            row = conn.execute(
                "SELECT * FROM host_leases WHERE lease_key = ?", (lease_key,)
            ).fetchone()
        logger.debug("Lease row read", extra={"fr_id": "FR-HOST-PERSISTENCE-LEASES"})
        return self._row_to_record(row) if row is not None else None

    def acquire(self, record: Mapping[str, Any], observed_at_utc: str) -> bool:
        """Conditionally insert/replace a row by its holder and expiration."""
        metadata = canonical_json(record["metadata"])
        with self._db.transaction() as conn:
            cursor = conn.execute(
                """INSERT INTO host_leases
                (lease_key, holder_id, scope, acquired_at_utc, expires_at_utc, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(lease_key) DO UPDATE SET
                    holder_id = excluded.holder_id, scope = excluded.scope,
                    acquired_at_utc = excluded.acquired_at_utc,
                    expires_at_utc = excluded.expires_at_utc,
                    metadata = excluded.metadata
                WHERE host_leases.holder_id = excluded.holder_id
                   OR host_leases.expires_at_utc < ?""",
                (
                    record["lease_key"],
                    record["holder_id"],
                    record["scope"],
                    record["acquired_at_utc"],
                    record["expires_at_utc"],
                    metadata,
                    observed_at_utc,
                ),
            )
            changed = cursor.rowcount > 0
        logger.debug(
            "Conditional lease write completed",
            extra={"changed": changed, "fr_id": "FR-HOST-PERSISTENCE-LEASES"},
        )
        return changed

    def renew(
        self,
        lease_key: str,
        holder_id: str,
        observed_at_utc: str,
        expires_at_utc: str,
    ) -> dict[str, Any] | None:
        """Update expiry and read the resulting row within one transaction."""
        with self._db.transaction() as conn:
            cursor = conn.execute(
                "UPDATE host_leases SET expires_at_utc = ? "
                "WHERE lease_key = ? AND holder_id = ? AND expires_at_utc >= ?",
                (expires_at_utc, lease_key, holder_id, observed_at_utc),
            )
            row = (
                conn.execute(
                    "SELECT * FROM host_leases WHERE lease_key = ?", (lease_key,)
                ).fetchone()
                if cursor.rowcount
                else None
            )
            record = self._row_to_record(row) if row is not None else None
        logger.debug(
            "Conditional lease renewal completed",
            extra={"changed": row is not None, "fr_id": "FR-HOST-PERSISTENCE-LEASES"},
        )
        return record

    def release(self, lease_key: str, holder_id: str) -> bool:
        """Delete a row only when its key and holder match."""
        with self._db.transaction() as conn:
            changed = (
                conn.execute(
                    "DELETE FROM host_leases WHERE lease_key = ? AND holder_id = ?",
                    (lease_key, holder_id),
                ).rowcount
                > 0
            )
        logger.debug(
            "Conditional lease delete completed",
            extra={"changed": changed, "fr_id": "FR-HOST-PERSISTENCE-LEASES"},
        )
        return changed

    def list_active(self, observed_at_utc: str) -> list[dict[str, Any]]:
        """Read rows after a caller-supplied expiration cutoff."""
        with self._db.connection(query_only=True) as conn:
            rows = conn.execute(
                "SELECT * FROM host_leases WHERE expires_at_utc > ? "
                "ORDER BY expires_at_utc",
                (observed_at_utc,),
            ).fetchall()
        logger.debug("Lease rows read", extra={"fr_id": "FR-HOST-PERSISTENCE-LEASES"})
        return [self._row_to_record(row) for row in rows]

    def prune_expired(self, observed_at_utc: str) -> int:
        """Delete rows at or before a caller-supplied expiration cutoff."""
        with self._db.transaction() as conn:
            count = conn.execute(
                "DELETE FROM host_leases WHERE expires_at_utc <= ?", (observed_at_utc,)
            ).rowcount
        logger.info(
            "Lease rows deleted",
            extra={"count": count, "fr_id": "FR-HOST-PERSISTENCE-LEASES"},
        )
        return count

    @staticmethod
    def _row_to_record(row: sqlite3.Row) -> dict[str, Any]:
        """Decode stored JSON without interpreting worker policy."""
        record = dict(row)
        record["metadata"] = json.loads(record["metadata"])
        return record


class JobStore:
    """Persist explicit job fields without interpreting job lifecycle or budgets."""

    _columns = (
        "job_id",
        "owner",
        "kind",
        "status",
        "progress",
        "accepted",
        "rejected",
        "message",
        "attempt_id",
        "max_retries",
        "retry_count",
        "dedup_key",
        "parent_job_id",
        "child_job_ids_json",
        "budget_json",
        "submitted_at_utc",
        "started_at_utc",
        "finished_at_utc",
        "error_message",
        "error_location",
    )

    def __init__(
        self,
        db_path: Path | str | None = None,
        *,
        busy_timeout: float = _BUSY_TIMEOUT_SECONDS,
        db: DatabaseManager | None = None,
    ) -> None:
        self._db = db or DatabaseManager(db_path, busy_timeout=busy_timeout)

    @property
    def db_path(self) -> Path | str:
        """Return the configured database location."""
        return ":memory:" if self._db.is_memory else self._db.database_path

    @property
    def db(self) -> DatabaseManager:
        """Return the manager used by this store."""
        return self._db

    def initialize(self) -> None:
        """Ensure the storage schema exists."""
        self._db.initialize()

    def upsert_job(self, record: Mapping[str, Any]) -> None:
        """Write one complete job storage record."""
        self.initialize()
        placeholders = ", ".join("?" for _ in self._columns)
        sql = (
            f"INSERT OR REPLACE INTO host_jobs ({', '.join(self._columns)}) "  # noqa: S608 - fixed columns/placeholders only
            f"VALUES ({placeholders})"
        )
        with self._db.transaction() as conn:
            conn.execute(sql, tuple(record[column] for column in self._columns))
        logger.info("Job row saved", extra={"fr_id": "FR-HOST-PERSISTENCE-JOBS"})

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        """Read one job storage record by ID."""
        self.initialize()
        with self._db.connection(query_only=True) as conn:
            row = conn.execute(
                "SELECT * FROM host_jobs WHERE job_id = ?", (job_id,)
            ).fetchone()
        logger.debug("Job row read", extra={"fr_id": "FR-HOST-PERSISTENCE-JOBS"})
        return dict(row) if row is not None else None

    def list_jobs(
        self,
        owner: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Read recent job rows with optional field filters."""
        self.initialize()
        filters = []
        parameters: list[Any] = []
        for column, value in (("owner", owner), ("status", status)):
            if value is not None:
                filters.append(f"{column} = ?")
                parameters.append(value)
        where = " WHERE " + " AND ".join(filters) if filters else ""
        sql = f"SELECT * FROM host_jobs{where} ORDER BY submitted_at_utc DESC LIMIT ?"  # noqa: S608
        with self._db.connection(query_only=True) as conn:
            rows = conn.execute(sql, (*parameters, limit)).fetchall()
        logger.debug("Job rows read", extra={"fr_id": "FR-HOST-PERSISTENCE-JOBS"})
        return [dict(row) for row in rows]

    def update_statuses(
        self,
        matching_statuses: tuple[str, ...],
        *,
        status: str,
        finished_at_utc: str,
        error_message: str,
    ) -> int:
        """Atomically update fields on rows matching caller-supplied statuses."""
        self.initialize()
        if not matching_statuses:
            return 0
        placeholders = ", ".join("?" for _ in matching_statuses)
        sql = (
            "UPDATE host_jobs SET status = ?, finished_at_utc = ?, error_message = ? "  # noqa: S608 - fixed columns/placeholders only
            f"WHERE status IN ({placeholders})"
        )
        with self._db.transaction() as conn:
            count = conn.execute(
                sql, (status, finished_at_utc, error_message, *matching_statuses)
            ).rowcount
        logger.info(
            "Job rows updated",
            extra={"count": count, "fr_id": "FR-HOST-PERSISTENCE-JOBS"},
        )
        return count


class BasketStore:
    """Own group/member CRUD and their shared transaction boundary."""

    def __init__(self, db: DatabaseManager) -> None:
        self._db = db

    def save(
        self,
        name: str,
        description: str,
        members: list[dict[str, Any]],
        *,
        system: int = 0,
    ) -> int:
        """Replace a group's membership atomically without domain defaults."""
        with self._db.transaction() as conn:
            conn.execute(
                "INSERT INTO datamgr_stock_group (name, description, system) "
                "VALUES (?, ?, ?) ON CONFLICT(name) DO UPDATE SET "
                "description = excluded.description, system = excluded.system",
                (name, description, system),
            )
            row = conn.execute(
                "SELECT id FROM datamgr_stock_group WHERE name = ?", (name,)
            ).fetchone()
            group_id = int(row["id"])
            conn.execute("DELETE FROM datamgr_stock WHERE basket_id = ?", (group_id,))
            conn.executemany(
                "INSERT INTO datamgr_stock (ticker, basket_id, date_from, date_to) "
                "VALUES (?, ?, ?, ?)",
                [
                    (
                        m["ticker"],
                        group_id,
                        m.get("date_from") or "",
                        m.get("date_to"),
                    )
                    for m in members
                ],
            )
        logger.info("Basket rows saved", extra={"fr_id": "FR-HOST-PERSISTENCE-BASKETS"})
        return group_id

    def get(self, name: str) -> dict[str, Any] | None:
        """Read a group and its ordered members in one read transaction."""
        with self._db.connection(query_only=True) as conn:
            conn.execute("BEGIN")
            try:
                row = conn.execute(
                    "SELECT * FROM datamgr_stock_group WHERE name = ?", (name,)
                ).fetchone()
                if row is None:
                    record = None
                else:
                    record = dict(row)
                    record["members"] = [
                        dict(member)
                        for member in conn.execute(
                            "SELECT * FROM datamgr_stock WHERE basket_id = ? "
                            "ORDER BY id",
                            (row["id"],),
                        ).fetchall()
                    ]
            finally:
                conn.execute("ROLLBACK")
        logger.debug("Basket rows read", extra={"fr_id": "FR-HOST-PERSISTENCE-BASKETS"})
        return record

    def get_by_id(self, basket_id: int) -> dict[str, Any] | None:
        """Read a group and its ordered members by ID in one read transaction."""
        with self._db.connection(query_only=True) as conn:
            conn.execute("BEGIN")
            try:
                row = conn.execute(
                    "SELECT * FROM datamgr_stock_group WHERE id = ?", (basket_id,)
                ).fetchone()
                if row is None:
                    record = None
                else:
                    record = dict(row)
                    record["members"] = [
                        dict(member)
                        for member in conn.execute(
                            "SELECT * FROM datamgr_stock WHERE basket_id = ? "
                            "ORDER BY id",
                            (row["id"],),
                        ).fetchall()
                    ]
            finally:
                conn.execute("ROLLBACK")
        logger.debug(
            "Basket rows read by id", extra={"fr_id": "FR-HOST-PERSISTENCE-BASKETS"}
        )
        return record

    def list_names(self) -> list[str]:
        """Read group names in alphabetical order."""
        with self._db.connection(query_only=True) as conn:
            rows = conn.execute(
                "SELECT name FROM datamgr_stock_group ORDER BY name"
            ).fetchall()
        logger.debug(
            "Basket names read", extra={"fr_id": "FR-HOST-PERSISTENCE-BASKETS"}
        )
        return [str(row["name"]) for row in rows]

    def list_groups(self) -> list[dict[str, Any]]:
        """Read all stock groups with constituent counts in alphabetical order."""
        with self._db.connection(query_only=True) as conn:
            rows = conn.execute(
                "SELECT g.id, g.name, g.description, g.system, "
                "COUNT(s.id) AS member_count "
                "FROM datamgr_stock_group g "
                "LEFT JOIN datamgr_stock s ON g.id = s.basket_id "
                "GROUP BY g.id "
                "ORDER BY g.name"
            ).fetchall()
        logger.debug(
            "Basket groups list read", extra={"fr_id": "FR-HOST-PERSISTENCE-BASKETS"}
        )
        return [dict(row) for row in rows]

    def delete(self, name: str) -> bool:
        """Delete a non-system group and its members in one transaction."""
        with self._db.transaction() as conn:
            row: sqlite3.Row | None = conn.execute(
                "SELECT id, system FROM datamgr_stock_group WHERE name = ?", (name,)
            ).fetchone()
            if row is not None:
                if int(row["system"]) == 1:
                    logger.warning(
                        "Cannot delete system stock group",
                        extra={
                            "basket_name": name,
                            "fr_id": "FR-HOST-PERSISTENCE-BASKETS",
                        },
                    )
                    return False
                conn.execute(
                    "DELETE FROM datamgr_stock WHERE basket_id = ?", (row["id"],)
                )
                conn.execute(
                    "DELETE FROM datamgr_stock_group WHERE id = ?", (row["id"],)
                )
        deleted: bool = row is not None
        logger.info(
            "Basket delete completed",
            extra={"deleted": deleted, "fr_id": "FR-HOST-PERSISTENCE-BASKETS"},
        )
        return deleted

    def count(self) -> int:
        """Return the number of stored groups."""
        with self._db.connection(query_only=True) as conn:
            row = conn.execute("SELECT COUNT(*) FROM datamgr_stock_group").fetchone()
        logger.debug(
            "Basket count read", extra={"fr_id": "FR-HOST-PERSISTENCE-BASKETS"}
        )
        return int(row[0])


class BrokerStore:
    """Read optional legacy broker storage without defining broker defaults."""

    def __init__(self, db: DatabaseManager) -> None:
        self._db = db

    def list_profiles(self) -> list[dict[str, Any]]:
        """Return existing legacy rows, or an empty list if the table is absent."""
        with self._db.connection(query_only=True) as conn:
            exists: sqlite3.Row | None = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' "
                "AND name='datamgr_broker'"
            ).fetchone()
            rows: list[sqlite3.Row] = (
                conn.execute("SELECT * FROM datamgr_broker ORDER BY id").fetchall()
                if exists
                else []
            )
        logger.debug(
            "Broker rows read",
            extra={
                "table_exists": exists is not None,
                "fr_id": "FR-HOST-PERSISTENCE-BROKERS",
            },
        )
        return [dict(row) for row in rows]
