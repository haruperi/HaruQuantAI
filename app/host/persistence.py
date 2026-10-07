"""Authoritative host SQLite persistence, typed repositories, and restart recovery.

Description:
    Provides the central transactional SQLite persistence authority, schema migration
    manager, narrow typed entity repositories, authoritative scoped settings store,
    durable compute job store, distributed cooperative leases, and restart
    reconciliation services for the HaruQuantAI platform host. All SQLite database
    connections, transactions, migrations, and queries across the entire platform are
    strictly centralized within this module. Domain plugins, host configuration
    managers (app.host.settings), compute coordinators (app.host.jobs), and security
    boundaries (app.host.session) never open SQLite handles or execute raw SQL
    directly. This module acts as the sole persistence gateway, enforcing
    connection-per-operation safety, `BEGIN IMMEDIATE` write serialization,
    WAL journaling, foreign keys, and busy timeout management.

    Externally, it participates in four critical host lifecycles: (1) host bootstrap
    calls `DatabaseManager.initialize()` and `RecoveryManager.reconcile_on_startup()`
    during early startup to verify schema integrity, recover interrupted transactions,
    and prune expired leases; (2) domain workspaces and host modules interact via
    `SettingsStore`, `JobStore`, and scoped `PersistenceAccess` capability facades
    without SQL exposure; (3) background worker pools and job admission controllers
    coordinate multi-worker tasks through `LeaseManager` without split-brain lockouts;
    and (4) the browser shell and DevOps tooling inspect storage metrics and run
    physical database integrity checks via `create_persistence_router()`.

    Internally, `DatabaseManager` manages SQLite connections, transaction blocks, and
    WAL settings; `SchemaManager` enforces immutable migration history and runs
    `PRAGMA integrity_check`; `SettingsStore` provides transactional settings CRUD;
    `JobStore` manages compute job state transitions and startup reconciliation;
    `TypedRepository[T]` maps Pydantic models to versioned JSON payload records with
    monotonic revision checks (`expected_revision`); `LeaseManager` provides atomic
    lease acquisition and heartbeats; and `RecoveryManager` audits control tables after
    reboot to reconcile transient states without fabricating false data.

Purpose:
    FEAT-HOST-PERSISTENCE: Authoritative Host Persistence, Repositories, and Recovery.
    Provides transactional SQLite database management, schema migration integrity,
    narrow typed repositories, optimistic revision controls, and restart recovery.

Key Capabilities:
    - FR-HOST-PERSISTENCE-SCHEMA-VERIFICATION: Schema Migrations & Integrity Checking
      Associated: `[SchemaManager.initialize()]`, `[SchemaManager.check_integrity()]`
      Logging: Emits INFO log on schema initialization and migration commits; ERROR
      log on schema drift, checksum mismatch, or integrity corruption.
    - FR-HOST-PERSISTENCE-TRANSACTIONS: Serialized ACID Write Transactions
      Associated: `[DatabaseManager.transaction()]`
      Logging: Emits DEBUG log on transaction begin/commit; WARNING log on rollback;
      ERROR log on busy contention or lock timeouts.
    - FR-HOST-PERSISTENCE-TYPED-REPOSITORY: Narrow Domain Entity Repositories
      Associated: `[TypedRepository.get()]`, `[TypedRepository.save()]`,
      `[TypedRepository.delete()]`, `[TypedRepository.list()]`
      Logging: Emits DEBUG log on entity reads/queries; INFO log on entity mutations
      recording entity ID, type, and updated revision.
    - FR-HOST-PERSISTENCE-REVISION-CONCURRENCY: Optimistic Monotonic Revision Controls
      Associated: `[TypedRepository.save()]`, `[TypedRepository.delete()]`
      Logging: Emits WARNING log with conflict details when an update's expected
      revision diverges from the persisted record.
    - FR-HOST-PERSISTENCE-LEASE-COORDINATION: Cooperative Worker Leases & TTL Heartbeats
      Associated: `[LeaseManager.acquire()]`, `[LeaseManager.renew()]`,
      `[LeaseManager.release()]`
      Logging: Emits INFO log on lease acquisition, renewal, and release; WARNING log
      when lease acquisition is denied due to active holder.
    - FR-HOST-PERSISTENCE-RESTART-RECOVERY: Startup Reconciliation of Orphaned Leases
      Associated: `[RecoveryManager.reconcile_on_startup()]`
      Logging: Emits INFO log detailing purged expired leases, reconciled entities,
      and verified database physical integrity.
    - FR-HOST-PERSISTENCE-INTEGRITY-CHECK: Physical SQLite Verification
      Associated: `[DatabaseManager.check_integrity()]`
      Logging: Emits INFO log on clean PRAGMA integrity check; ERROR log on detected
      database page corruption.
    - FR-HOST-PERSISTENCE-REST-PROJECTION: FastAPI REST Persistence Endpoints
      Associated: `[create_persistence_router()]`
      Logging: Emits DEBUG log on router initialization; INFO log on status,
      lease, schema, and recovery API invocations.

Python API Usage:
    ```python
    from pathlib import Path
    from pydantic import BaseModel
    from app.host.persistence import DatabaseManager, TypedRepository


    class StrategyConfig(BaseModel):
        symbol: str
        timeframe: str


    db = DatabaseManager(Path("data/database/haruquantai.db"))
    db.initialize()

    repo = TypedRepository(db, entity_type="strategy", model_cls=StrategyConfig)

    # Save entity with initial revision
    record = repo.save("strat-01", StrategyConfig(symbol="EURUSD", timeframe="1h"))

    # Update with optimistic concurrency check
    updated = repo.save(
        "strat-01",
        StrategyConfig(symbol="EURUSD", timeframe="4h"),
        expected_revision=record.revision,
    )
    ```

CLI Usage:
    ```bash
    # Check database status and schema migration level
    uv run python -m app.host.persistence --status

    # Run physical database integrity verification
    uv run python -m app.host.persistence --integrity-check

    # Execute startup reconciliation of interrupted states
    uv run python -m app.host.persistence --reconcile
    ```
"""

from __future__ import annotations

import argparse
import contextlib
import json
import re
import sqlite3
import sys
import threading
import uuid
from collections.abc import Callable, Generator, Mapping
from dataclasses import asdict, is_dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.host.logging import get_logger
from app.host.response import StandardResponse

logger = get_logger(__name__)

# Canonical envelope alias matching transport conventions
ApiResponse = StandardResponse

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
    "AcquireLeaseRequest",
    "ApiResponse",
    "CorruptDataError",
    "DatabaseManager",
    "DatabaseStatus",
    "DatasetPersistence",
    "EntityRecord",
    "HostSettingsSnapshot",
    "IncompatibleSchemaError",
    "InstrumentPersistence",
    "JobStore",
    "LeaseExpiredError",
    "LeaseManager",
    "LeaseRecord",
    "LeaseStatus",
    "MigrationRecord",
    "Page",
    "PersistenceAccess",
    "PersistenceError",
    "RecoveryManager",
    "ReleaseLeaseRequest",
    "RenewLeaseRequest",
    "RevisionConflictError",
    "SchemaManager",
    "SessionPersistence",
    "SettingRecord",
    "SettingsPage",
    "SettingsStore",
    "StorageBusyError",
    "TypedRepository",
    "ValidationError",
    "canonical_json",
    "create_persistence_router",
    "get_database_manager",
    "main",
    "now_utc_iso",
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


class LeaseStatus(StrEnum):
    """Lifecycle state of a cooperative worker lease."""

    ACTIVE = "active"
    EXPIRED = "expired"
    RELEASED = "released"


class MigrationRecord(BaseModel):
    """Schema migration ledger entry."""

    version: int = Field(ge=1, description="Monotonic schema version number.")
    name: str = Field(description="Descriptive identifier of migration.")
    applied_at_utc: datetime = Field(description="UTC timestamp of migration commit.")
    checksum: str = Field(description="SHA-256 digest of migration SQL script.")


class LeaseRecord(BaseModel):
    """Cooperative worker lease representation."""

    lease_key: str = Field(description="Unique lease resource identifier.")
    holder_id: str = Field(description="Identity of the active lease holder.")
    scope: str = Field(description="Authorization or tenant scope.")
    acquired_at_utc: datetime = Field(
        description="UTC timestamp when lease was acquired."
    )
    expires_at_utc: datetime = Field(description="UTC timestamp when lease expires.")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary lease metadata attributes."
    )

    @property
    def is_expired(self) -> bool:
        """Return True if lease expiration is in the past."""
        return datetime.now(UTC) > self.expires_at_utc


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


class AcquireLeaseRequest(BaseModel):
    """Request payload for acquiring a cooperative worker lease."""

    lease_key: str = Field(min_length=1)
    holder_id: str = Field(min_length=1)
    ttl_seconds: float = Field(default=30.0, gt=0.0)
    scope: str = Field(default="default")
    metadata: dict[str, Any] = Field(default_factory=dict)


class RenewLeaseRequest(BaseModel):
    """Request payload for renewing an active lease."""

    lease_key: str = Field(min_length=1)
    holder_id: str = Field(min_length=1)
    ttl_seconds: float = Field(default=30.0, gt=0.0)


class ReleaseLeaseRequest(BaseModel):
    """Request payload for releasing a held lease."""

    lease_key: str = Field(min_length=1)
    holder_id: str = Field(min_length=1)


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


class HostSettingsSnapshot(BaseModel):
    """Point-in-time snapshot of the entire host settings dictionary."""

    revision: int
    values: dict[str, dict[str, Any]]


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
        self.leases = LeaseManager(self)
        self.recovery = RecoveryManager(self)
        self.instruments = InstrumentPersistence(self)
        self.sessions = SessionPersistence(self)
        self.datasets = DatasetPersistence(self)

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


class _DefaultDatabaseHolder:
    """Internal singleton holder avoiding module global mutation."""

    instance: DatabaseManager | None = None


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
            if cur.fetchone()[0] == 0:
                now_str = datetime.now(UTC).isoformat()
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
        *,
        connection: sqlite3.Connection | None = None,
    ) -> T | None:
        """Retrieve and deserialize an entity by ID if present.

        Args:
            entity_id: Unique entity identifier.
            connection: Optional external transaction connection.

        Returns:
            Deserialized Pydantic model instance, or None if absent.
        """
        validate_identifier(entity_id, "entity_id")
        sql = (
            "SELECT payload FROM host_entities "
            "WHERE entity_id = ? AND entity_type = ? AND scope = ?;"
        )
        params = (entity_id, self.entity_type, self.scope)

        if connection is not None:
            cur = connection.cursor()
            cur.execute(sql, params)
            row = cur.fetchone()
        else:
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
        *,
        connection: sqlite3.Connection | None = None,
    ) -> EntityRecord | None:
        """Retrieve full EntityRecord envelope including revision metadata.

        Args:
            entity_id: Unique entity identifier.
            connection: Optional external transaction connection.

        Returns:
            EntityRecord record, or None if absent.
        """
        validate_identifier(entity_id, "entity_id")
        sql = (
            "SELECT entity_id, entity_type, scope, payload, revision, "
            "created_at_utc, updated_at_utc FROM host_entities "
            "WHERE entity_id = ? AND entity_type = ? AND scope = ?;"
        )
        params = (entity_id, self.entity_type, self.scope)

        if connection is not None:
            cur = connection.cursor()
            cur.execute(sql, params)
            row = cur.fetchone()
        else:
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
        connection: sqlite3.Connection | None = None,
    ) -> EntityRecord:
        """Save or update entity, verifying optimistic concurrency revision.

        Args:
            entity_id: Unique entity identifier.
            model: Pydantic model payload to persist.
            expected_revision: Expected current revision for optimistic
                concurrency check.
            connection: Optional external transaction connection.

        Returns:
            Updated EntityRecord envelope.

        Raises:
            RevisionConflictError: If expected_revision does not match persisted record.
        """
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

        if connection is not None:
            return _execute(connection)
        with self._db.transaction() as conn:
            return _execute(conn)

    def delete(
        self,
        entity_id: str,
        *,
        expected_revision: int | None = None,
        connection: sqlite3.Connection | None = None,
    ) -> bool:
        """Delete an entity by ID with optional expected revision check.

        Args:
            entity_id: Unique entity identifier.
            expected_revision: Optional revision concurrency assertion.
            connection: Optional external transaction connection.

        Returns:
            True if entity was deleted; False if not found.
        """
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

        if connection is not None:
            return _execute(connection)
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
# Cooperative Lease Manager
# ============================================================================


class LeaseManager:
    """Manages cooperative worker locks, heartbeats, and TTL expiration."""

    def __init__(self, db: DatabaseManager) -> None:
        self._db = db

    def acquire(
        self,
        lease_key: str,
        holder_id: str,
        *,
        ttl_seconds: float = 30.0,
        scope: str = "default",
        metadata: dict[str, Any] | None = None,
    ) -> LeaseRecord:
        """Atomically acquire or reclaim an expired cooperative lease.

        Args:
            lease_key: Unique lease resource key.
            holder_id: Unique worker or process identifier.
            ttl_seconds: Lease duration in seconds.
            scope: Ownership or tenant scope.
            metadata: Optional arbitrary structured lease attributes.

        Returns:
            LeaseRecord representing acquired lease.

        Raises:
            StorageBusyError: If lease is held by another worker and unexpired.
        """
        validate_identifier(lease_key, "lease_key")
        validate_identifier(holder_id, "holder_id")
        validate_identifier(scope, "scope")

        meta_json = canonical_json(metadata or {})
        now_dt = datetime.now(UTC)
        expires_dt = datetime.fromtimestamp(now_dt.timestamp() + ttl_seconds, tz=UTC)
        now_str = now_dt.isoformat()
        expires_str = expires_dt.isoformat()

        with self._db.transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT holder_id, expires_at_utc FROM host_leases "
                "WHERE lease_key = ?;",
                (lease_key,),
            )
            existing = cur.fetchone()

            if existing is not None:
                current_holder = existing["holder_id"]
                current_exp = datetime.fromisoformat(existing["expires_at_utc"])
                if now_dt <= current_exp and current_holder != holder_id:
                    msg = (
                        f"Lease '{lease_key}' is actively held by "
                        f"worker '{current_holder}' until {current_exp.isoformat()}"
                    )
                    logger.warning(
                        msg,
                        extra={"fr_id": "FR-HOST-PERSISTENCE-LEASE-COORDINATION"},
                    )
                    raise StorageBusyError(msg)

                cur.execute(
                    """
                    UPDATE host_leases
                    SET holder_id = ?, scope = ?, acquired_at_utc = ?,
                        expires_at_utc = ?, metadata = ?
                    WHERE lease_key = ?;
                    """,
                    (holder_id, scope, now_str, expires_str, meta_json, lease_key),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO host_leases (
                        lease_key, holder_id, scope, acquired_at_utc,
                        expires_at_utc, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?);
                    """,
                    (lease_key, holder_id, scope, now_str, expires_str, meta_json),
                )

        logger.info(
            "Lease acquired",
            extra={
                "lease_key": lease_key,
                "holder_id": holder_id,
                "expires_at": expires_str,
                "fr_id": "FR-HOST-PERSISTENCE-LEASE-COORDINATION",
            },
        )
        return LeaseRecord(
            lease_key=lease_key,
            holder_id=holder_id,
            scope=scope,
            acquired_at_utc=now_dt,
            expires_at_utc=expires_dt,
            metadata=metadata or {},
        )

    def renew(
        self,
        lease_key: str,
        holder_id: str,
        *,
        ttl_seconds: float = 30.0,
    ) -> LeaseRecord:
        """Renew an actively held lease, extending expiration time.

        Args:
            lease_key: Unique lease resource key.
            holder_id: Holder identifier attempting renewal.
            ttl_seconds: Extended duration in seconds.

        Returns:
            Updated LeaseRecord.

        Raises:
            LeaseExpiredError: If lease does not exist, has expired, or is held
                by other.
        """
        validate_identifier(lease_key, "lease_key")
        now_dt = datetime.now(UTC)
        expires_dt = datetime.fromtimestamp(now_dt.timestamp() + ttl_seconds, tz=UTC)
        expires_str = expires_dt.isoformat()

        with self._db.transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT holder_id, scope, acquired_at_utc, expires_at_utc, metadata "
                "FROM host_leases WHERE lease_key = ?;",
                (lease_key,),
            )
            existing = cur.fetchone()

            if existing is None:
                msg = f"Lease '{lease_key}' does not exist, cannot renew"
                raise LeaseExpiredError(msg)

            if existing["holder_id"] != holder_id:
                msg = (
                    f"Lease '{lease_key}' is held by '{existing['holder_id']}', "
                    f"not '{holder_id}'"
                )
                raise LeaseExpiredError(msg)

            cur_exp = datetime.fromisoformat(existing["expires_at_utc"])
            if now_dt > cur_exp:
                msg = f"Lease '{lease_key}' has already expired"
                raise LeaseExpiredError(msg)

            cur.execute(
                "UPDATE host_leases SET expires_at_utc = ? WHERE lease_key = ?;",
                (expires_str, lease_key),
            )
            scope = existing["scope"]
            acq_dt = datetime.fromisoformat(existing["acquired_at_utc"])
            meta_dict = json.loads(existing["metadata"])

        logger.info(
            "Lease renewed",
            extra={
                "lease_key": lease_key,
                "holder_id": holder_id,
                "new_expires_at": expires_str,
                "fr_id": "FR-HOST-PERSISTENCE-LEASE-COORDINATION",
            },
        )
        return LeaseRecord(
            lease_key=lease_key,
            holder_id=holder_id,
            scope=scope,
            acquired_at_utc=acq_dt,
            expires_at_utc=expires_dt,
            metadata=meta_dict,
        )

    def release(self, lease_key: str, holder_id: str) -> bool:
        """Release a held lease if the caller is the registered holder.

        Args:
            lease_key: Unique lease resource key.
            holder_id: Holder identifier attempting release.

        Returns:
            True if released; False if lease absent or held by another worker.
        """
        validate_identifier(lease_key, "lease_key")
        with self._db.transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                "DELETE FROM host_leases WHERE lease_key = ? AND holder_id = ?;",
                (lease_key, holder_id),
            )
            released = cur.rowcount > 0

        if released:
            logger.info(
                "Lease released",
                extra={
                    "lease_key": lease_key,
                    "holder_id": holder_id,
                    "fr_id": "FR-HOST-PERSISTENCE-LEASE-COORDINATION",
                },
            )
        return released

    def list_active(self) -> list[LeaseRecord]:
        """List all active unexpired leases."""
        now_str = datetime.now(UTC).isoformat()
        with self._db.connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT lease_key, holder_id, scope, acquired_at_utc, "
                "expires_at_utc, metadata FROM host_leases "
                "WHERE expires_at_utc > ? ORDER BY expires_at_utc ASC;",
                (now_str,),
            )
            rows = cur.fetchall()

        return [
            LeaseRecord(
                lease_key=r["lease_key"],
                holder_id=r["holder_id"],
                scope=r["scope"],
                acquired_at_utc=datetime.fromisoformat(r["acquired_at_utc"]),
                expires_at_utc=datetime.fromisoformat(r["expires_at_utc"]),
                metadata=json.loads(r["metadata"]),
            )
            for r in rows
        ]

    def prune_expired(self) -> int:
        """Prune all expired leases from storage.

        Returns:
            Number of deleted expired lease records.
        """
        now_str = datetime.now(UTC).isoformat()
        with self._db.transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                "DELETE FROM host_leases WHERE expires_at_utc <= ?;",
                (now_str,),
            )
            return int(cur.rowcount)


# ============================================================================
# Restart Recovery Manager
# ============================================================================


class RecoveryManager:
    """Reconciles interrupted writes, dead leases, and asserts integrity on boot."""

    def __init__(self, db: DatabaseManager) -> None:
        self._db = db

    def reconcile_on_startup(self) -> dict[str, Any]:
        """Perform comprehensive startup recovery and integrity verification.

        Returns:
            Dictionary report summarizing recovery outcome.
        """
        logger.info(
            "Starting host persistence recovery audit",
            extra={"fr_id": "FR-HOST-PERSISTENCE-RESTART-RECOVERY"},
        )
        # 1. Verify physical integrity
        integrity = self._db.check_integrity()
        if integrity.lower() != "ok":
            msg = (
                f"Database integrity check failed during startup recovery: {integrity}"
            )
            raise IncompatibleSchemaError(msg)

        # 2. Verify schema readiness
        self._db.schema.initialize()
        self._db.schema.verify_schema()

        # 3. Prune expired or stale leases
        pruned_leases = self._db.leases.prune_expired()

        report = {
            "status": "reconciled",
            "integrity": integrity,
            "pruned_expired_leases": pruned_leases,
            "reconciled_at_utc": datetime.now(UTC).isoformat(),
        }

        logger.info(
            "Host persistence recovery complete",
            extra={
                "report": report,
                "fr_id": "FR-HOST-PERSISTENCE-RESTART-RECOVERY",
            },
        )
        return report


# ============================================================================
# Scoped Capability Facade
# ============================================================================


class PersistenceAccess:
    """Scoped capability facade restricting domain callers to an authorized scope."""

    def __init__(
        self,
        db: DatabaseManager,
        *,
        scope: str,
        owner_id: str,
    ) -> None:
        """Initialize PersistenceAccess facade with database and scope.

        Args:
            db: Central host DatabaseManager.
            scope: Bound tenant or namespace scope.
            owner_id: Unique identifier of domain owner.
        """
        validate_identifier(scope, "scope")
        validate_identifier(owner_id, "owner_id")
        self._db = db
        self.scope = scope
        self.owner_id = owner_id

    def get_repository[T: BaseModel](
        self,
        entity_type: str,
        model_cls: type[T],
    ) -> TypedRepository[T]:
        """Create a TypedRepository bound strictly to caller scope."""
        return TypedRepository(
            self._db,
            entity_type=entity_type,
            model_cls=model_cls,
            scope=self.scope,
        )

    def acquire_lease(
        self,
        lease_key: str,
        *,
        ttl_seconds: float = 30.0,
        metadata: dict[str, Any] | None = None,
    ) -> LeaseRecord:
        """Acquire a lease bound to owner and scope."""
        scoped_key = f"{self.scope}:{lease_key}"
        return self._db.leases.acquire(
            scoped_key,
            self.owner_id,
            ttl_seconds=ttl_seconds,
            scope=self.scope,
            metadata=metadata,
        )

    def renew_lease(self, lease_key: str, *, ttl_seconds: float = 30.0) -> LeaseRecord:
        """Renew a held lease."""
        scoped_key = f"{self.scope}:{lease_key}"
        return self._db.leases.renew(scoped_key, self.owner_id, ttl_seconds=ttl_seconds)

    def release_lease(self, lease_key: str) -> bool:
        """Release a held lease."""
        scoped_key = f"{self.scope}:{lease_key}"
        return self._db.leases.release(scoped_key, self.owner_id)


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
        validator: Callable[[str, str, Any], None] | None = None,
    ) -> None:
        """Initialize SettingsStore with an authoritative database file path or manager.

        Args:
            db_path: Optional path to the SQLite database file or ':memory:'.
            busy_timeout: Timeout in seconds for SQLite lock waits.
            db: Optional preexisting DatabaseManager instance.
            validator: Optional callback validating setting value constraints.
        """
        self._db: DatabaseManager = db or DatabaseManager(
            db_path, busy_timeout=busy_timeout
        )
        self._busy_timeout: float = busy_timeout
        self._validator: Callable[[str, str, Any], None] | None = validator

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

    def read_all_scoped(self) -> tuple[int, dict[str, dict[str, Any]]]:
        """Read all scoped settings records grouped by scope, plus revision number."""
        if not self._db.is_memory and not self._db.database_path.exists():
            return 1, {}

        with self._db.connection(query_only=True) as conn:
            try:
                rows = conn.execute(
                    """
                    SELECT scope, key, value_json, schema_version, updated_at_utc
                    FROM host_settings
                    ORDER BY scope ASC, key ASC
                    """
                ).fetchall()
            except sqlite3.OperationalError:
                return 1, {}

        revision = 1
        values: dict[str, dict[str, Any]] = {}
        for row in rows:
            scope = str(row["scope"])
            key = str(row["key"])
            try:
                val = json.loads(row["value_json"])
            except (ValueError, TypeError) as exc:
                logger.debug(
                    "FR-HOST-SETTINGS-LOAD: Skipping corrupt row (%s)",
                    exc,
                    extra={"fr_id": "FR-HOST-SETTINGS-LOAD"},
                )
                continue

            if scope == "_system" and key == "revision":
                if isinstance(val, int):
                    revision = val
                continue

            if scope not in values:
                values[scope] = {}
            values[scope][key] = val

        return revision, values

    def get_snapshot(self) -> HostSettingsSnapshot:
        """Return full host settings snapshot including revision and values."""
        rev, vals = self.read_all_scoped()
        return HostSettingsSnapshot(revision=rev, values=vals)

    def update_settings(
        self,
        scope: str,
        values: dict[str, Any],
        *,
        expected_revision: int | None = None,
    ) -> HostSettingsSnapshot:
        """Convenience method to update settings within a single scope."""
        return self.update_batch({scope: values}, expected_revision=expected_revision)

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
                if self._validator is not None:
                    self._validator(scope, key, val)
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
    ) -> HostSettingsSnapshot:
        """Atomically update multiple scoped settings with optimistic locking."""
        if not changes:
            return self.get_snapshot()

        validated_items = self._validate_batch_changes(changes)

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
        return self.get_snapshot()

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
# Authoritative Job Store
# ============================================================================


class JobStore:
    """Authoritative SQLite persistence manager for compute job records.

    Provides transactional, parameterized CRUD operations against the `host_jobs`
    table and startup reconciliation for interrupted jobs.
    """

    def __init__(
        self,
        db_path: Path | str | None = None,
        *,
        busy_timeout: float = _BUSY_TIMEOUT_SECONDS,
        db: DatabaseManager | None = None,
        record_factory: Callable[[Mapping[str, Any]], Any] | None = None,
    ) -> None:
        """Initialize JobStore with a database path or manager.

        Args:
            db_path: Optional path to SQLite file or ':memory:'.
            busy_timeout: Lock timeout in seconds.
            db: Optional preexisting DatabaseManager instance.
            record_factory: Optional deserialization factory from mapping to
                domain record.
        """
        self._db: DatabaseManager = db or DatabaseManager(
            db_path, busy_timeout=busy_timeout
        )
        self._busy_timeout: float = busy_timeout
        self._record_factory: Callable[[Mapping[str, Any]], Any] | None = record_factory

    @property
    def db_path(self) -> Path | str:
        """Return the resolved database path or ':memory:'."""
        return ":memory:" if self._db.is_memory else self._db.database_path

    @property
    def db(self) -> DatabaseManager:
        """Return the underlying DatabaseManager instance."""
        return self._db

    def initialize(self) -> None:
        """Ensure host_jobs schema and indexes exist."""
        self._db.schema.initialize()

    def upsert_job(self, record: Any) -> None:
        """Insert or replace a job record.

        Args:
            record: Job record model instance to persist.
        """
        self.initialize()
        budget_attr = getattr(record, "budget", {})
        budget_dict = (
            asdict(budget_attr)
            if is_dataclass(budget_attr) and not isinstance(budget_attr, type)
            else (
                budget_attr.model_dump(mode="json")
                if hasattr(budget_attr, "model_dump")
                else getattr(budget_attr, "__dict__", {})
            )
        )
        budget_json = json.dumps(budget_dict)
        child_ids = getattr(record, "child_job_ids", [])
        child_json = json.dumps(child_ids)

        with self._db.transaction() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO host_jobs (
                    job_id, owner, kind, status, progress, accepted, rejected,
                    message, attempt_id, max_retries, retry_count, dedup_key,
                    parent_job_id, child_job_ids_json, budget_json, submitted_at_utc,
                    started_at_utc, finished_at_utc, error_message, error_location
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                );
                """,
                (
                    str(record.job_id),
                    str(record.owner),
                    str(record.kind),
                    str(record.status),
                    float(record.progress),
                    int(record.accepted),
                    int(record.rejected),
                    str(record.message),
                    int(record.attempt_id),
                    int(record.max_retries),
                    int(record.retry_count),
                    record.dedup_key,
                    record.parent_job_id,
                    child_json,
                    budget_json,
                    str(record.submitted_at_utc),
                    record.started_at_utc,
                    record.finished_at_utc,
                    record.error_message,
                    record.error_location,
                ),
            )

    def get_job(self, job_id: str) -> Any | None:
        """Query job record by job_id.

        Args:
            job_id: Task identifier string.

        Returns:
            Job record instance if found, None otherwise.
        """
        self.initialize()
        with self._db.connection() as conn:
            row = conn.execute(
                "SELECT * FROM host_jobs WHERE job_id = ?;", (job_id,)
            ).fetchone()
            if row is None:
                return None
            return self._row_to_record(row)

    def list_jobs(
        self,
        owner: str | None = None,
        status: Any | None = None,
        limit: int = 100,
    ) -> list[Any]:
        """List job records matching optional filters."""
        self.initialize()
        params: list[Any] = []
        if owner is not None and status is not None:
            query = (
                "SELECT * FROM host_jobs WHERE owner = ? AND status = ? "
                "ORDER BY submitted_at_utc DESC LIMIT ?;"
            )
            params = [owner, str(status), limit]
        elif owner is not None:
            query = (
                "SELECT * FROM host_jobs WHERE owner = ? "
                "ORDER BY submitted_at_utc DESC LIMIT ?;"
            )
            params = [owner, limit]
        elif status is not None:
            query = (
                "SELECT * FROM host_jobs WHERE status = ? "
                "ORDER BY submitted_at_utc DESC LIMIT ?;"
            )
            params = [str(status), limit]
        else:
            query = "SELECT * FROM host_jobs ORDER BY submitted_at_utc DESC LIMIT ?;"
            params = [limit]

        with self._db.connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_record(r) for r in rows]

    def reconcile_on_startup(self) -> int:
        """Reconcile uncompleted jobs from previous runs to INTERRUPTED state."""
        self.initialize()
        now_utc = datetime.now(UTC).isoformat()
        with self._db.transaction() as conn:
            cols = {
                r["name"]
                for r in conn.execute("PRAGMA table_info(host_jobs)").fetchall()
            }
            if "status" not in cols:
                return 0
            cursor = conn.execute(
                """
                UPDATE host_jobs
                SET status = 'interrupted',
                    finished_at_utc = ?,
                    error_message = ?
                WHERE status IN ('queued', 'running', 'cancellation_requested');
                """,
                (now_utc, "Host restarted while job was in-flight."),
            )
            count = cursor.rowcount

        if count > 0:
            logger.info(
                "Startup reconciliation: marked %d orphaned jobs as INTERRUPTED",
                count,
                extra={
                    "reconciled_count": count,
                    "requirement": "FR-HOST-JOBS-RESTART-RECONCILIATION",
                },
            )
        return count

    def _row_to_record(self, row: Mapping[str, Any]) -> Any:
        """Convert SQLite row to typed JobRecord model."""
        if self._record_factory is not None:
            return self._record_factory(row)

        from app.host.jobs import Budget, JobRecord, JobStatus

        row_dict = dict(row)
        raw_budget = row_dict.get("budget_json", "{}")
        budget_data = json.loads(raw_budget) if raw_budget else {}
        if not isinstance(budget_data, dict):
            budget_data = {}

        raw_children = row_dict.get("child_job_ids_json", "[]")
        child_ids = json.loads(raw_children) if raw_children else []
        if not isinstance(child_ids, list):
            child_ids = []
        return JobRecord(
            job_id=str(row_dict["job_id"]),
            owner=str(row_dict["owner"]),
            kind=str(row_dict["kind"]),
            status=JobStatus(row_dict["status"]),
            progress=float(row_dict["progress"]),
            accepted=int(row_dict["accepted"]),
            rejected=int(row_dict["rejected"]),
            message=str(row_dict["message"]),
            attempt_id=int(row_dict["attempt_id"]),
            max_retries=int(row_dict["max_retries"]),
            retry_count=int(row_dict["retry_count"]),
            dedup_key=row_dict["dedup_key"],
            parent_job_id=row_dict["parent_job_id"],
            child_job_ids=child_ids,
            budget=Budget(**budget_data),
            submitted_at_utc=str(row_dict["submitted_at_utc"]),
            started_at_utc=row_dict["started_at_utc"],
            finished_at_utc=row_dict["finished_at_utc"],
            error_message=row_dict["error_message"],
            error_location=row_dict["error_location"],
        )


# ============================================================================
# Datamgr Entities Persistence (Instruments, Sessions, Datasets)
# ============================================================================


class InstrumentPersistence:
    """Authoritative host persistence operations for datamgr_instruments."""

    def __init__(self, db: DatabaseManager) -> None:
        """Initialize with parent DatabaseManager."""
        self._db = db

    def create(self, record: dict[str, Any]) -> int:
        """Insert a new instrument record and return its generated ID."""
        now_ts = now_utc_iso()
        record_copy = dict(record)
        if not record_copy.get("created_at_utc"):
            record_copy["created_at_utc"] = now_ts
        if not record_copy.get("updated_at_utc"):
            record_copy["updated_at_utc"] = now_ts
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
        values = []
        for col in columns:
            val = record_copy.get(col)
            if val is None:
                if col in ("broker_id", "decimals", "swap_3day_day"):
                    val = 0
                elif col in (
                    "tick_size",
                    "tick_step",
                    "tick_value_in_money",
                    "point_value",
                    "default_spread",
                    "default_slippage",
                    "min_volume",
                    "max_volume",
                    "lot_step",
                    "margin_rate",
                    "swap_long",
                    "swap_short",
                ):
                    val = 0.0
                else:
                    val = ""
            values.append(val)
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
            record_copy.get("symbol"),
            last_id,
            extra={"fr_id": "FR-HOST-PERSISTENCE-INSTRUMENTS"},
        )
        return int(last_id)

    def get_by_symbol(self, symbol: str) -> dict[str, Any] | None:
        """Retrieve instrument record by symbol name."""
        sql = "SELECT * FROM datamgr_instruments WHERE symbol = ?;"
        with self._db.connection(query_only=True) as conn:
            cur = conn.cursor()
            cur.execute(sql, (symbol,))
            row = cur.fetchone()
            if row is not None:
                return dict(row)
        return None

    def list_instruments(
        self,
        connection: str | None = None,
        data_type: str | None = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """List instruments with optional connection or data_type filter."""
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
        if not updates:
            return True
        updates_copy = dict(updates)
        updates_copy["updated_at_utc"] = now_utc_iso()
        updates_copy.pop("id", None)
        updates_copy.pop("symbol", None)
        for k in updates_copy:
            validate_identifier(k, "column")
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
        sql = "SELECT COUNT(*) FROM datamgr_instruments;"
        with self._db.connection(query_only=True) as conn:
            cur = conn.cursor()
            cur.execute(sql)
            row = cur.fetchone()
            return int(row[0]) if row else 0


class SessionPersistence:
    """Authoritative host persistence operations for datamgr_sessions."""

    def __init__(self, db: DatabaseManager) -> None:
        """Initialize with parent DatabaseManager."""
        self._db = db

    def create(self, record: dict[str, Any]) -> int:
        """Insert a new session definition and return its generated ID."""
        values = [
            record.get("name", ""),
            record.get("description", ""),
            record.get("timezone", "UTC"),
            record.get("windows_json", "[]"),
            record.get("holidays_json", "[]"),
            int(record.get("is_default", 0)),
        ]
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
        return int(last_id)

    def get_by_name(self, name: str) -> dict[str, Any] | None:
        """Retrieve session record by name."""
        sql = "SELECT * FROM datamgr_sessions WHERE name = ?;"
        with self._db.connection(query_only=True) as conn:
            cur = conn.cursor()
            cur.execute(sql, (name,))
            row = cur.fetchone()
            if row is not None:
                return dict(row)
        return None

    def list_sessions(self, limit: int = 1000, offset: int = 0) -> list[dict[str, Any]]:
        """List sessions in ascending name order."""
        sql = "SELECT * FROM datamgr_sessions ORDER BY name ASC LIMIT ? OFFSET ?;"
        with self._db.connection(query_only=True) as conn:
            cur = conn.cursor()
            cur.execute(sql, (limit, offset))
            return [dict(r) for r in cur.fetchall()]

    def update(self, name: str, updates: dict[str, Any]) -> bool:
        """Update fields for a session by name."""
        if not updates:
            return True
        updates_copy = dict(updates)
        updates_copy.pop("id", None)
        updates_copy.pop("name", None)
        for k in updates_copy:
            validate_identifier(k, "column")
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
        sql = "SELECT COUNT(*) FROM datamgr_sessions;"
        with self._db.connection(query_only=True) as conn:
            cur = conn.cursor()
            cur.execute(sql)
            row = cur.fetchone()
            return int(row[0]) if row else 0


class DatasetPersistence:
    """Authoritative host persistence operations for datamgr_datasets."""

    def __init__(self, db: DatabaseManager) -> None:
        """Initialize with parent DatabaseManager."""
        self._db = db

    def save(self, record: dict[str, Any]) -> str:
        """Upsert a dataset metadata record."""
        now_ts = now_utc_iso()
        record_copy = dict(record)
        dataset_id = str(record_copy.get("id") or f"dataset-{uuid.uuid4().hex[:12]}")
        record_copy["id"] = dataset_id
        if not record_copy.get("created_at"):
            record_copy["created_at"] = now_ts
        record_copy["updated_at"] = now_ts
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
        values = []
        for col in columns:
            val = record_copy.get(col)
            if val is None:
                if col == "bars":
                    val = 0
                elif col == "schema_version":
                    val = 1
                elif col == "quality_score":
                    val = 1.0
                else:
                    val = ""
            values.append(val)
        sql = (
            "INSERT INTO datamgr_datasets ("
            "id, source, symbol, underlying, instrument, timeframe, "
            "broker, broker_name, timezone, category, date_from, date_to, "
            "bars, created_at, updated_at, path, data_kind, quality_score, "
            "lineage_json, schema_version"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(id) DO UPDATE SET "
            "bars = excluded.bars, "
            "date_from = excluded.date_from, "
            "date_to = excluded.date_to, "
            "updated_at = excluded.updated_at, "
            "path = excluded.path, "
            "quality_score = excluded.quality_score, "
            "lineage_json = excluded.lineage_json;"
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
        sql = "SELECT COUNT(*) FROM datamgr_datasets;"
        with self._db.connection(query_only=True) as conn:
            cur = conn.cursor()
            cur.execute(sql)
            row = cur.fetchone()
            return int(row[0]) if row else 0


# ============================================================================
# REST Transport Projection
# ============================================================================


class PersistenceRouterService:
    """Internal service adapter translating HTTP requests to persistence actions."""

    def __init__(self, db: DatabaseManager) -> None:
        self._db = db

    def get_status(self, request: Request) -> Response:
        """Get database operational metrics snapshot."""
        req_id = request.headers.get("x-request-id")
        status_rec = self._db.get_status()
        resp = ApiResponse.success(
            data=status_rec.model_dump(mode="json"),
            message="Database status retrieved successfully.",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    def get_schema(self, request: Request) -> Response:
        """Get schema migration ledger records."""
        req_id = request.headers.get("x-request-id")
        migrations = self._db.schema.list_migrations()
        resp = ApiResponse.success(
            data=[m.model_dump(mode="json") for m in migrations],
            message="Schema migrations retrieved successfully.",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    def check_integrity_endpoint(self, request: Request) -> Response:
        """Run physical SQLite database integrity verification."""
        req_id = request.headers.get("x-request-id")
        res = self._db.check_integrity()
        resp = ApiResponse.success(
            data={"integrity": res, "integrity_check": res},
            message=f"Database integrity verified: {res}",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    def list_leases(self, request: Request) -> Response:
        """List currently active cooperative leases."""
        req_id = request.headers.get("x-request-id")
        leases = self._db.leases.list_active()
        resp = ApiResponse.success(
            data=[lease.model_dump(mode="json") for lease in leases],
            message="Active leases retrieved successfully.",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    def acquire_lease_endpoint(
        self,
        request: Request,
        req: AcquireLeaseRequest,
    ) -> Response:
        """Acquire a cooperative worker lease."""
        req_id = request.headers.get("x-request-id")
        try:
            lease = self._db.leases.acquire(
                req.lease_key,
                req.holder_id,
                ttl_seconds=req.ttl_seconds,
                scope=req.scope,
                metadata=req.metadata,
            )
            resp = ApiResponse.success(
                data=lease.model_dump(mode="json"),
                message=f"Lease {req.lease_key} acquired successfully.",
                request_id=req_id,
            )
            return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())
        except StorageBusyError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(exc),
            ) from exc

    def renew_lease_endpoint(
        self,
        request: Request,
        req: RenewLeaseRequest,
    ) -> Response:
        """Renew a held cooperative lease."""
        req_id = request.headers.get("x-request-id")
        try:
            lease = self._db.leases.renew(
                req.lease_key,
                req.holder_id,
                ttl_seconds=req.ttl_seconds,
            )
            resp = ApiResponse.success(
                data=lease.model_dump(mode="json"),
                message=f"Lease {req.lease_key} renewed successfully.",
                request_id=req_id,
            )
            return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())
        except LeaseExpiredError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            ) from exc

    def release_lease_endpoint(
        self,
        request: Request,
        req: ReleaseLeaseRequest,
    ) -> Response:
        """Release a held cooperative lease."""
        req_id = request.headers.get("x-request-id")
        released = self._db.leases.release(req.lease_key, req.holder_id)
        resp = ApiResponse.success(
            data={"released": released},
            message=f"Lease {req.lease_key} released: {released}",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    def reconcile_endpoint(self, request: Request) -> Response:
        """Trigger restart recovery reconciliation."""
        req_id = request.headers.get("x-request-id")
        report = self._db.recovery.reconcile_on_startup()
        resp = ApiResponse.success(
            data=report,
            message="Recovery reconciliation completed.",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())


def create_persistence_router(db: DatabaseManager) -> APIRouter:
    """Create and configure FastAPI APIRouter exposing persistence endpoints.

    Args:
        db: Central host DatabaseManager instance.

    Returns:
        Configured FastAPI APIRouter.
    """
    service = PersistenceRouterService(db)
    router = APIRouter(prefix="/persistence", tags=["persistence"])

    router.add_api_route(
        "/status",
        service.get_status,
        methods=["GET"],
        summary="Query database status and health",
    )
    router.add_api_route(
        "/schema",
        service.get_schema,
        methods=["GET"],
        summary="List applied schema migrations",
    )
    router.add_api_route(
        "/schema/migrations",
        service.get_schema,
        methods=["GET"],
        summary="List applied schema migrations alias",
    )
    router.add_api_route(
        "/integrity-check",
        service.check_integrity_endpoint,
        methods=["POST"],
        summary="Execute PRAGMA integrity_check",
    )
    router.add_api_route(
        "/leases",
        service.list_leases,
        methods=["GET"],
        summary="List active cooperative leases",
    )
    router.add_api_route(
        "/leases/acquire",
        service.acquire_lease_endpoint,
        methods=["POST"],
        summary="Acquire a cooperative lease",
    )
    router.add_api_route(
        "/leases/renew",
        service.renew_lease_endpoint,
        methods=["POST"],
        summary="Renew an active lease",
    )
    router.add_api_route(
        "/leases/release",
        service.release_lease_endpoint,
        methods=["POST"],
        summary="Release an active lease",
    )
    router.add_api_route(
        "/recovery/reconcile",
        service.reconcile_endpoint,
        methods=["POST"],
        summary="Trigger restart recovery reconciliation",
    )

    logger.debug(
        "Persistence REST router initialized",
        extra={"fr_id": "FR-HOST-PERSISTENCE-REST-PROJECTION"},
    )
    return router


# ============================================================================
# CLI Diagnostics Entrypoint
# ============================================================================


def main() -> int:
    """CLI diagnostics entrypoint for database inspection and integrity validation.

    Returns:
        Process exit code (0 for success, non-zero for failure).
    """
    parser = argparse.ArgumentParser(
        description="HaruQuantAI Host Persistence Authority Tool"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Inspect database operational status and schema version",
    )
    parser.add_argument(
        "--integrity-check",
        action="store_true",
        help="Run physical database integrity verification",
    )
    parser.add_argument(
        "--reconcile",
        action="store_true",
        help="Execute startup recovery reconciliation",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=Path("data/database/haruquantai.db"),
        help="Target SQLite database path (default: data/database/haruquantai.db)",
    )

    args = parser.parse_args()
    db = DatabaseManager(args.db)
    exit_code = 0

    if args.status:
        try:
            stat = db.get_status()
            logger.info(
                "Database status output",
                extra={"status": stat.model_dump(mode="json")},
            )
            print(f"Database: {stat.database_path}")
            print(f"Connected: {stat.is_connected}")
            print(f"Journal: {stat.journal_mode}")
            print(f"Schema Version: {stat.schema_version}")
            print(f"Tables: {stat.table_count}")
            print(f"Integrity: {stat.integrity_status}")
            exit_code = 0 if stat.is_connected and stat.integrity_status == "ok" else 1
        except Exception as exc:
            logger.exception(
                "Error checking database status",
                extra={"error": str(exc)},
            )
            exit_code = 2
    elif args.integrity_check:
        try:
            result = db.check_integrity()
            print(f"Integrity check: {result}")
            exit_code = 0 if result == "ok" else 1
        except Exception as exc:
            logger.exception(
                "Error verifying integrity",
                extra={"error": str(exc)},
            )
            exit_code = 2
    elif args.reconcile:
        try:
            report = db.recovery.reconcile_on_startup()
            print(f"Reconciliation: {report['status']}")
            print(f"Pruned Leases: {report['pruned_expired_leases']}")
            exit_code = 0
        except Exception as exc:
            logger.exception(
                "Error running reconciliation",
                extra={"error": str(exc)},
            )
            exit_code = 2
    else:
        parser.print_help()

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
