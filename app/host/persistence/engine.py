"""Database connection and transaction engine for host persistence subsystem.

Description:
    Owns SQLite connection lifecycles, WAL configuration, transactional context
    managers, SQLite integrity validation, DuckDB analytical query routing, and
    instantiation of domain-specific stores. All handles and transaction contexts
    originate strictly within this engine.

Purpose:
    FEAT-HOST-PERSISTENCE: Exclusive transactional database access and connections.

Key Capabilities:
    - FR-HOST-PERSISTENCE-TRANSACTIONS: Atomic writes and connection ownership.
      Associated: `DatabaseManager.connection()`, `DatabaseManager.transaction()`
      Logging: DEBUG access/commit; WARNING rollback; ERROR contention.
    - FR-HOST-PERSISTENCE-ANALYTICAL-QUERY: Direct DuckDB analytical query execution.
      Associated: `query_duckdb()`, `DatabaseManager.query_duckdb()`
      Logging: DEBUG execution with query text.
    - FR-HOST-PERSISTENCE-INTEGRITY-CHECK: Query physical SQLite integrity.
      Associated: `DatabaseManager.check_integrity()`
      Logging: INFO clean result; ERROR detected corruption.

Python API Usage:
    ```python
    from app.host.persistence.engine import DatabaseManager, get_database_manager

    db = get_database_manager(":memory:")
    db.initialize()
    with db.transaction() as conn:
        conn.execute("SELECT 1;")
    ```

CLI Usage:
    No direct CLI entrypoint. Diagnostics provides external management:
    ```bash
    uv run python -m app.host.diagnostics --status
    uv run python -m app.host.diagnostics --integrity-check
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
from typing import TYPE_CHECKING, Any

from app.host.logging import get_logger
from app.host.persistence.errors import (
    PersistenceError,
    StorageBusyError,
    ValidationError,
)
from app.host.persistence.models import DatabaseStatus

if TYPE_CHECKING:
    from app.host.persistence.schema import SchemaManager
    from app.host.persistence.stores.baskets import BasketStore
    from app.host.persistence.stores.brokers import BrokerStore
    from app.host.persistence.stores.datasets import DatasetStore
    from app.host.persistence.stores.instruments import InstrumentStore
    from app.host.persistence.stores.jobs import LeaseStore
    from app.host.persistence.stores.logs import LogStore
    from app.host.persistence.stores.trading_sessions import SessionStore

logger = get_logger(__name__)

DEFAULT_DATABASE_PATH: Path = (
    Path(__file__).resolve().parents[3] / "data" / "database" / "haruquantai.db"
)
MAX_BATCH_SIZE: int = 100
MAX_READ_LIMIT: int = 1000
DEFAULT_READ_LIMIT: int = 50
SETTINGS_RECORD_SCHEMA_VERSION: int = 1
SCHEMA_VERSION: int = SETTINGS_RECORD_SCHEMA_VERSION  # Backward-compatibility alias

_MAX_IDENTIFIER_LENGTH: int = 128
_IDENTIFIER_PATTERN: re.Pattern[str] = re.compile(r"^[A-Za-z0-9_.:-]+$")
_MAX_PAYLOAD_BYTES: int = 1024 * 1024  # 1 MiB
_MAX_JSON_DEPTH: int = 16
_BUSY_TIMEOUT_MS: int = 5000
_BUSY_TIMEOUT_SECONDS: float = 5.0


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


class DatabaseManager:
    """Central host authority for SQLite database connections, WAL, and transactions."""

    schema: SchemaManager
    leases: LeaseStore
    instruments: InstrumentStore
    sessions: SessionStore
    datasets: DatasetStore
    baskets: BasketStore
    brokers: BrokerStore
    logs: LogStore

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

        self._init_stores()

    def _init_stores(self) -> None:
        from app.host.persistence.schema import SchemaManager
        from app.host.persistence.stores.baskets import BasketStore
        from app.host.persistence.stores.brokers import BrokerStore
        from app.host.persistence.stores.datasets import DatasetStore
        from app.host.persistence.stores.instruments import InstrumentStore
        from app.host.persistence.stores.jobs import LeaseStore
        from app.host.persistence.stores.logs import LogStore
        from app.host.persistence.stores.trading_sessions import SessionStore

        self.schema = SchemaManager(self)
        self.leases = LeaseStore(self)
        self.instruments = InstrumentStore(self)
        self.sessions = SessionStore(self)
        self.datasets = DatasetStore(self)
        self.baskets = BasketStore(self)
        self.brokers = BrokerStore(self)
        self.logs = LogStore(self)

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
