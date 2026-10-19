# ruff: noqa: INP001
"""SQLite WAL persistence layer, parameterized CRUD, and atomic batch transactions.

Description:
    Provides the centralized HostPersistence engine for HaruQuantAI. Manages
    connection lifecycles in write-ahead logging (WAL) mode, idempotently provisions
    the 25 operational database tables, enforces primary key validations and
    foreign-key reference guards, supports deterministic cursor pagination,
    implements compare-and-set (CAS) optimistic revision concurrency, and guarantees
    all-or-nothing rollback for atomic multi-row batch write transactions.

Purpose:
    FEAT-HOST-PERSISTENCE: Core SQLite WAL persistence and transaction gateway.

Key Capabilities:
    - FR-HOST-PERSISTENCE-CREATE: Parameterized single-row and entity creation
      in SQLite WAL.
      Associated: `HostPersistence.create_record()`, `HostPersistence.create_entity()`
      Logging: INFO on successful record creation; DEBUG on query execution;
      ERROR on failure.
    - FR-HOST-PERSISTENCE-READ: Parameterized queries, filtering, and cursor pagination.
      Associated: `HostPersistence.read_records()`, `HostPersistence.read_entity()`
      Logging: DEBUG on query execution with row count; ERROR on unapproved table
      or failure.
    - FR-HOST-PERSISTENCE-UPDATE: Parameterized updates and optimistic revision
      compare-and-set.
      Associated: `HostPersistence.update_record()`, `HostPersistence.update_entity()`
      Logging: INFO on record modification; WARNING on revision conflict;
      ERROR on failure.
    - FR-HOST-PERSISTENCE-DELETE: Parameterized deletion with foreign-key reference
      guards.
      Associated: `HostPersistence.delete_record()`, `HostPersistence.delete_entity()`
      Logging: INFO on deletion; ERROR when blocked by foreign key reference guards.
    - FR-HOST-PERSISTENCE-BATCH: Atomic multi-row batch writes with all-or-nothing
      rollback.
      Associated: `HostPersistence.apply_batch()`
      Logging: INFO on committed atomic batch; ERROR on rollback.

Python API Usage:
    ```python
    from app.host.persistence import HostPersistence

    pk = HostPersistence.create_record(
        "host_settings",
        {
            "scope": "ui",
            "key": "theme",
            "value_json": '"dark"',
            "updated_at_utc": "2026-10-19T12:00:00Z",
        },
    )
    records = HostPersistence.read_records("host_settings", where={"scope": "ui"})
    HostPersistence.update_record(
        "host_settings",
        pk_values={"scope": "ui", "key": "theme"},
        updates={"value_json": '"light"'},
    )
    HostPersistence.delete_record(
        "host_settings", pk_values={"scope": "ui", "key": "theme"}
    )
    ```

CLI Usage:
    ```bash
    uv run python -m app.host.persistence
    ```
"""

from __future__ import annotations

import sqlite3
import sys
import tempfile
import threading
from collections.abc import Generator, Mapping, Sequence
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, NamedTuple

from app.host.logging import get_logger

__all__ = [
    "HostPersistence",
    "HostPersistenceCLI",
]

logger = get_logger(__name__)

CREATE_FR = "FR-HOST-PERSISTENCE-CREATE"
READ_FR = "FR-HOST-PERSISTENCE-READ"
UPDATE_FR = "FR-HOST-PERSISTENCE-UPDATE"
DELETE_FR = "FR-HOST-PERSISTENCE-DELETE"
BATCH_FR = "FR-HOST-PERSISTENCE-BATCH"

DEFAULT_DB_PATH: Path = Path("data/database/haruquantai.db")

PERSISTENCE_TABLES: tuple[str, ...] = (
    "datamgr_broker",
    "datamgr_broker_stock",
    "datamgr_commodities",
    "datamgr_crypto_catalog",
    "datamgr_datasets",
    "datamgr_instruments",
    "datamgr_logs",
    "datamgr_operation_log",
    "datamgr_quality",
    "datamgr_sessions",
    "datamgr_stock",
    "datamgr_stock_group",
    "datamgr_tickers",
    "host_entities",
    "host_grid_leases",
    "host_grid_nodes",
    "host_job_attempts",
    "host_job_events",
    "host_jobs",
    "host_leases",
    "host_session",
    "host_settings",
    "mt5_commands",
    "mt5_events",
    "schema_migrations",
)

TABLE_PRIMARY_KEYS: dict[str, tuple[str, ...]] = {
    "datamgr_broker": ("id",),
    "datamgr_broker_stock": ("ID",),
    "datamgr_commodities": ("id",),
    "datamgr_crypto_catalog": ("exchange", "symbol"),
    "datamgr_datasets": ("id",),
    "datamgr_instruments": ("id",),
    "datamgr_logs": ("id",),
    "datamgr_operation_log": ("id",),
    "datamgr_quality": ("report_id",),
    "datamgr_sessions": ("id",),
    "datamgr_stock": ("ID",),
    "datamgr_stock_group": ("ID",),
    "datamgr_tickers": ("id",),
    "host_entities": ("entity_id", "entity_type"),
    "host_grid_leases": ("lease_id",),
    "host_grid_nodes": ("node_id",),
    "host_job_attempts": ("attempt_id",),
    "host_job_events": ("event_id",),
    "host_jobs": ("job_id",),
    "host_leases": ("lease_key",),
    "host_session": ("session_id",),
    "host_settings": ("scope", "key"),
    "mt5_commands": ("command_id",),
    "mt5_events": ("event_id",),
    "schema_migrations": ("version",),
}

TABLE_AUTOINCREMENT_PK_TABLES: set[str] = {
    "datamgr_broker",
    "datamgr_broker_stock",
    "datamgr_commodities",
    "datamgr_instruments",
    "datamgr_logs",
    "datamgr_operation_log",
    "datamgr_sessions",
    "datamgr_stock",
    "datamgr_stock_group",
    "datamgr_tickers",
    "mt5_events",
}

TABLE_FOREIGN_KEY_GUARDS: dict[str, tuple[tuple[str, str, str], ...]] = {
    "datamgr_broker": (("datamgr_broker_stock", "BROKER_ID", "id"),),
    "datamgr_stock_group": (("datamgr_stock", "BASKET_ID", "ID"),),
    "host_jobs": (
        ("host_job_attempts", "job_id", "job_id"),
        ("host_grid_leases", "job_id", "job_id"),
    ),
    "host_grid_nodes": (("host_grid_leases", "node_id", "node_id"),),
}

TABLE_DDL_MAP: dict[str, str] = {
    "datamgr_broker": """CREATE TABLE IF NOT EXISTS "datamgr_broker" (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    is_system INTEGER NOT NULL DEFAULT 0,
    description TEXT DEFAULT '',
    stockpicker_use INTEGER DEFAULT 0,
    mt_use INTEGER DEFAULT 0,
    server_timezone TEXT DEFAULT 'UTC',
    postfix TEXT DEFAULT '',
    enabled INTEGER DEFAULT 1,
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL,
    clock_policy_json TEXT NOT NULL DEFAULT '{}',
    clock_policy_revision INTEGER NOT NULL DEFAULT 0
)""",
    "datamgr_broker_stock": """CREATE TABLE IF NOT EXISTS datamgr_broker_stock (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    TICKER VARCHAR(50) NOT NULL,
    BROKER_ID INTEGER NOT NULL,
    FOREIGN KEY(BROKER_ID) REFERENCES datamgr_broker(id)
)""",
    "datamgr_commodities": """CREATE TABLE IF NOT EXISTS "datamgr_commodities" (
    id INTEGER PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    name TEXT,
    point_value REAL,
    tick_step REAL,
    tick_size REAL,
    order_size_multi REAL,
    order_size_step REAL,
    exchange TEXT
)""",
    "datamgr_crypto_catalog": """CREATE TABLE IF NOT EXISTS "datamgr_crypto_catalog" (
    exchange TEXT NOT NULL,
    symbol TEXT NOT NULL,
    point_value REAL NOT NULL DEFAULT 1.0,
    tick_size REAL NOT NULL DEFAULT 1e-8,
    tick_step REAL NOT NULL DEFAULT 1e-8,
    default_spread REAL NOT NULL DEFAULT 0.0,
    default_slippage REAL NOT NULL DEFAULT 0.0,
    date_from TEXT,
    price_precision INTEGER NOT NULL DEFAULT 8,
    name TEXT,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (exchange, symbol)
)""",
    "datamgr_datasets": """CREATE TABLE IF NOT EXISTS "datamgr_datasets" (
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
)""",
    "datamgr_instruments": """CREATE TABLE IF NOT EXISTS "datamgr_instruments" (
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
    updated_at_utc TEXT NOT NULL,
    min_distance REAL NOT NULL DEFAULT 0.0,
    order_size_multiplier REAL NOT NULL DEFAULT 1.0,
    order_size_step REAL NOT NULL DEFAULT 0.0,
    cot TEXT DEFAULT NULL
)""",
    "datamgr_logs": """CREATE TABLE IF NOT EXISTS datamgr_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp_utc TEXT NOT NULL,
    action TEXT NOT NULL,
    message TEXT NOT NULL,
    symbol TEXT,
    details TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now'))
)""",
    "datamgr_operation_log": """CREATE TABLE IF NOT EXISTS datamgr_operation_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp_utc TEXT NOT NULL,
    symbol TEXT NOT NULL,
    operation TEXT NOT NULL,
    status TEXT NOT NULL,
    message TEXT NOT NULL
)""",
    "datamgr_quality": """CREATE TABLE IF NOT EXISTS "datamgr_quality" (
    report_id TEXT PRIMARY KEY,
    dataset_id TEXT NOT NULL,
    quality_score REAL NOT NULL,
    total_records INTEGER NOT NULL,
    anomalies_json TEXT NOT NULL DEFAULT '[]',
    anomaly_counts_json TEXT NOT NULL DEFAULT '{}',
    evaluated_at_utc TEXT NOT NULL
)""",
    "datamgr_sessions": """CREATE TABLE IF NOT EXISTS "datamgr_sessions" (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT DEFAULT '',
    timezone TEXT NOT NULL DEFAULT 'UTC',
    windows_json TEXT NOT NULL DEFAULT '[]',
    holidays_json TEXT NOT NULL DEFAULT '[]',
    is_default INTEGER NOT NULL DEFAULT 0,
    broker_id INTEGER NOT NULL DEFAULT -1
)""",
    "datamgr_stock": """CREATE TABLE IF NOT EXISTS datamgr_stock (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    TICKER VARCHAR(50) NOT NULL,
    BASKET_ID INTEGER NOT NULL,
    DATE_FROM LONG NOT NULL,
    DATE_TO LONG,
    FOREIGN KEY(BASKET_ID) REFERENCES datamgr_stock_group(ID)
)""",
    "datamgr_stock_group": """CREATE TABLE IF NOT EXISTS datamgr_stock_group (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    NAME VARCHAR(50) NOT NULL,
    SYSTEM BOOLEAN NOT NULL,
    DESC VARCHAR(250),
    description TEXT DEFAULT ''
)""",
    "datamgr_tickers": """CREATE TABLE IF NOT EXISTS "datamgr_tickers" (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    name TEXT,
    commodity_code TEXT,
    exchange TEXT,
    timeframe TEXT,
    date_from TEXT,
    date_to TEXT
)""",
    "host_entities": """CREATE TABLE IF NOT EXISTS host_entities (
    entity_id TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    scope TEXT NOT NULL,
    payload TEXT NOT NULL,
    revision INTEGER NOT NULL DEFAULT 1,
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL,
    PRIMARY KEY (entity_id, entity_type)
)""",
    "host_grid_leases": """CREATE TABLE IF NOT EXISTS host_grid_leases (
    lease_id TEXT PRIMARY KEY,
    node_id TEXT NOT NULL,
    job_id TEXT NOT NULL,
    leased_at_utc TEXT NOT NULL,
    expires_at_utc TEXT NOT NULL,
    state TEXT NOT NULL,
    FOREIGN KEY(node_id) REFERENCES host_grid_nodes(node_id),
    FOREIGN KEY(job_id) REFERENCES host_jobs(job_id)
)""",
    "host_grid_nodes": """CREATE TABLE IF NOT EXISTS host_grid_nodes (
    node_id TEXT PRIMARY KEY,
    address TEXT NOT NULL,
    port INTEGER NOT NULL,
    cores INTEGER NOT NULL,
    memory_mb INTEGER NOT NULL,
    state TEXT NOT NULL,
    last_heartbeat_utc TEXT NOT NULL
)""",
    "host_job_attempts": """CREATE TABLE IF NOT EXISTS "host_job_attempts" (
    attempt_id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    worker_id TEXT NOT NULL,
    sequence INTEGER NOT NULL,
    state TEXT NOT NULL,
    heartbeat_at_utc TEXT,
    checkpoint_json TEXT,
    created_at_utc TEXT NOT NULL,
    completed_at_utc TEXT
)""",
    "host_job_events": """CREATE TABLE IF NOT EXISTS "host_job_events" (
    event_id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    attempt_id TEXT,
    from_state TEXT,
    to_state TEXT NOT NULL,
    details_json TEXT NOT NULL,
    created_at_utc TEXT NOT NULL
)""",
    "host_jobs": """CREATE TABLE IF NOT EXISTS "host_jobs" (
    job_id TEXT PRIMARY KEY,
    owner TEXT NOT NULL DEFAULT 'default',
    kind TEXT NOT NULL DEFAULT 'compute',
    status TEXT NOT NULL DEFAULT 'completed',
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
)""",
    "host_leases": """CREATE TABLE IF NOT EXISTS host_leases (
    lease_key TEXT PRIMARY KEY,
    holder_id TEXT NOT NULL,
    scope TEXT NOT NULL,
    acquired_at_utc TEXT NOT NULL,
    expires_at_utc TEXT NOT NULL,
    metadata TEXT NOT NULL
)""",
    "host_session": """CREATE TABLE IF NOT EXISTS host_session (
    session_id TEXT PRIMARY KEY,
    token_hash TEXT NOT NULL UNIQUE,
    username TEXT NOT NULL,
    peer_id TEXT NOT NULL,
    created_at_utc TEXT NOT NULL,
    expires_at_utc TEXT NOT NULL,
    revoked_at_utc TEXT,
    status TEXT NOT NULL
)""",
    "host_settings": """CREATE TABLE IF NOT EXISTS "host_settings" (
    scope TEXT NOT NULL,
    key TEXT NOT NULL,
    value_json TEXT NOT NULL,
    schema_version INTEGER NOT NULL DEFAULT 1,
    updated_at_utc TEXT NOT NULL,
    PRIMARY KEY (scope, key)
)""",
    "mt5_commands": """CREATE TABLE IF NOT EXISTS mt5_commands (
    command_id TEXT PRIMARY KEY,
    session_id TEXT,
    object_id TEXT NOT NULL,
    class_name TEXT NOT NULL,
    method_name TEXT NOT NULL,
    args_json TEXT NOT NULL,
    requires_arm INTEGER NOT NULL,
    created_at REAL NOT NULL,
    sent_at REAL,
    acknowledged_at REAL,
    resolved_at REAL,
    status TEXT NOT NULL,
    native_request_id TEXT,
    value_json TEXT,
    meta_json TEXT,
    error_json TEXT
)""",
    "mt5_events": """CREATE TABLE IF NOT EXISTS mt5_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    command_id TEXT,
    native_request_id TEXT,
    event_type TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    received_at REAL NOT NULL
)""",
    "schema_migrations": """CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    applied_at_utc TEXT NOT NULL,
    checksum TEXT NOT NULL
)""",
}

SCHEMA_DDL: tuple[str, ...] = tuple(TABLE_DDL_MAP[t] for t in PERSISTENCE_TABLES)


class _PersistenceError(RuntimeError):
    """Base error for host persistence and transaction failures."""


class _RevisionConflictError(_PersistenceError):
    """Raised when an optimistic revision expectation fails."""

    def __init__(
        self,
        message: str = "Revision conflict detected during update",
        expected_revision: int | None = None,
        current_revision: int | None = None,
        *,
        expected: int | None = None,
        current: int | None = None,
    ) -> None:
        exp = expected_revision if expected_revision is not None else expected
        cur = current_revision if current_revision is not None else current
        self.expected: int | None = exp
        self.current: int | None = cur
        self.expected_revision: int | None = exp
        self.current_revision: int | None = cur
        super().__init__(message)


class _BatchOperation(NamedTuple):
    """Single operation descriptor inside an atomic batch transaction."""

    op_type: str
    table: str
    data: Mapping[str, Any] | None = None
    pk_values: Mapping[str, Any] | None = None
    expected_revision: int | None = None
    revision_col: str = "revision"


class _BatchResult(NamedTuple):
    """Result summary of an applied atomic batch transaction."""

    total_operations: int
    affected_rows: int
    details: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        """Convert result into serializable dictionary."""
        return {
            "total_operations": self.total_operations,
            "affected_rows": self.affected_rows,
            "details": list(self.details),
        }


def _current_utc_iso() -> str:
    """Return formatted ISO-8601 UTC timestamp."""
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


class HostPersistence:
    """Centralized SQLite WAL persistence and transaction gateway."""

    DEFAULT_DB_PATH: Path = DEFAULT_DB_PATH
    PERSISTENCE_TABLES: tuple[str, ...] = PERSISTENCE_TABLES
    TABLE_PRIMARY_KEYS: dict[str, tuple[str, ...]] = TABLE_PRIMARY_KEYS
    TABLE_AUTOINCREMENT_PK_TABLES: set[str] = TABLE_AUTOINCREMENT_PK_TABLES
    TABLE_FOREIGN_KEY_GUARDS: dict[str, tuple[tuple[str, str, str], ...]] = (
        TABLE_FOREIGN_KEY_GUARDS
    )
    TABLE_DDL_MAP: dict[str, str] = TABLE_DDL_MAP
    SCHEMA_DDL: tuple[str, ...] = SCHEMA_DDL
    Error = _PersistenceError
    RevisionConflictError = _RevisionConflictError
    BatchOperation = _BatchOperation
    BatchResult = _BatchResult
    _local = threading.local()

    # ------------------------------------------------------------------------
    # Connection Lifecycle & Schema Provisioning Helpers
    # ------------------------------------------------------------------------

    @classmethod
    def _get_connection(
        cls,
        *,
        timeout: float = 30.0,
    ) -> sqlite3.Connection:
        """Create and configure a SQLite connection in WAL mode."""
        resolved = Path(cls.DEFAULT_DB_PATH)
        is_new_file = str(resolved) != ":memory:" and not resolved.exists()
        if str(resolved) != ":memory:":
            resolved.parent.mkdir(parents=True, exist_ok=True)

        try:
            conn = sqlite3.connect(
                str(resolved),
                timeout=timeout,
                check_same_thread=False,
            )
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = NORMAL")
            conn.execute("PRAGMA foreign_keys = ON")
            if is_new_file:
                with conn:
                    for ddl in cls.SCHEMA_DDL:
                        conn.execute(ddl)
        except (sqlite3.Error, OSError, ValueError) as err:
            logger.exception(
                "%s: connection failed to %s",
                CREATE_FR,
                resolved,
                extra={"fr_id": CREATE_FR, "error": str(err)},
            )
            raise _PersistenceError(f"Database connection failed: {err}") from err

        return conn

    @classmethod
    def _ensure_table_schema(cls, conn: sqlite3.Connection, table: str) -> None:
        """Ensure a specific table exists by executing its canonical DDL statement."""
        if table not in cls.TABLE_DDL_MAP:
            logger.error(
                "%s: rejected schema creation for unapproved table %s",
                CREATE_FR,
                table,
                extra={"fr_id": CREATE_FR, "table": table},
            )
            raise _PersistenceError(
                f"Table '{table}' is not an approved operational persistence table."
            )

        try:
            conn.execute(cls.TABLE_DDL_MAP[table])
        except sqlite3.Error as err:
            logger.exception(
                "%s: failed ensuring table schema for %s",
                CREATE_FR,
                table,
                extra={"fr_id": CREATE_FR, "table": table, "error": str(err)},
            )
            raise _PersistenceError(
                f"Ensuring schema for '{table}' failed: {err}"
            ) from err

    @classmethod
    @contextmanager
    def _resolve_connection(cls) -> Generator[sqlite3.Connection]:
        """Resolve an active thread-local batch connection or open a temporary one."""
        active_conn: sqlite3.Connection | None = getattr(cls._local, "conn", None)
        if active_conn is not None:
            yield active_conn
        else:
            c = cls._get_connection()
            try:
                yield c
            finally:
                c.close()

    # ------------------------------------------------------------------------
    # Internal SQL Helpers
    # ------------------------------------------------------------------------

    @staticmethod
    def _build_where(
        where: Mapping[str, Any] | None,
    ) -> tuple[str, list[Any]]:
        """Construct parameterized WHERE clause from dictionary mapping."""
        if not where:
            return "", []
        clauses: list[str] = []
        params: list[Any] = []
        for col, val in where.items():
            clean_col = col.strip().strip('"')
            if not clean_col.replace("_", "").isalnum():
                raise _PersistenceError(f"Invalid column name in filter: '{col}'")
            if val is None:
                clauses.append(f'"{clean_col}" IS NULL')
            else:
                clauses.append(f'"{clean_col}" = ?')
                params.append(val)
        return " WHERE " + " AND ".join(clauses), params

    @classmethod
    def _insert_row(
        cls,
        conn: sqlite3.Connection,
        table: str,
        data: Mapping[str, Any],
        *,
        commit: bool = True,
    ) -> Any:
        """Insert a row into table."""
        if table not in cls.TABLE_PRIMARY_KEYS:
            raise _PersistenceError(
                f"Table '{table}' is not in approved table catalogue."
            )
        if not data:
            raise _PersistenceError("Insert data dictionary cannot be empty.")

        columns = list(data.keys())
        placeholders = ", ".join("?" for _ in columns)
        quoted_cols = ", ".join(f'"{col}"' for col in columns)
        sql = f'INSERT INTO "{table}" ({quoted_cols}) VALUES ({placeholders})'  # noqa: S608
        values = [data[col] for col in columns]

        try:
            if commit:
                with conn:
                    cursor = conn.execute(sql, values)
                    last_id = cursor.lastrowid
            else:
                cursor = conn.execute(sql, values)
                last_id = cursor.lastrowid
        except sqlite3.Error as err:
            logger.exception(
                "%s: insert failed on %s",
                CREATE_FR,
                table,
                extra={"fr_id": CREATE_FR, "table": table, "error": str(err)},
            )
            raise _PersistenceError(f"Insert into '{table}' failed: {err}") from err

        pk_cols = cls.TABLE_PRIMARY_KEYS[table]
        if len(pk_cols) == 1 and pk_cols[0] in data:
            return data[pk_cols[0]]
        if len(pk_cols) > 1 and all(k in data for k in pk_cols):
            return tuple(data[k] for k in pk_cols)
        return last_id

    @classmethod
    def _update_row_by_pk(
        cls,
        conn: sqlite3.Connection,
        table: str,
        pk_values: Mapping[str, Any],
        updates: Mapping[str, Any],
        *,
        commit: bool = True,
    ) -> int:
        """Update a row by primary key."""
        if table not in cls.TABLE_PRIMARY_KEYS:
            raise _PersistenceError(
                f"Table '{table}' is not in approved table catalogue."
            )
        if not updates:
            raise _PersistenceError("Updates mapping cannot be empty.")

        expected_pks = cls.TABLE_PRIMARY_KEYS[table]
        missing_pks = [pk for pk in expected_pks if pk not in pk_values]
        if missing_pks:
            raise _PersistenceError(
                f"Missing primary key columns for '{table}': {missing_pks}"
            )

        set_clauses = [f'"{col}" = ?' for col in updates]
        where_clauses = [f'"{pk}" = ?' for pk in expected_pks]
        set_str = ", ".join(set_clauses)
        where_str = " AND ".join(where_clauses)
        sql = f'UPDATE "{table}" SET {set_str} WHERE {where_str}'  # noqa: S608
        params = list(updates.values()) + [pk_values[pk] for pk in expected_pks]

        try:
            if commit:
                with conn:
                    cursor = conn.execute(sql, params)
                    affected = cursor.rowcount
            else:
                cursor = conn.execute(sql, params)
                affected = cursor.rowcount
        except sqlite3.Error as err:
            logger.exception(
                "%s: update failed on %s",
                UPDATE_FR,
                table,
                extra={"fr_id": UPDATE_FR, "table": table, "error": str(err)},
            )
            raise _PersistenceError(f"Update on '{table}' failed: {err}") from err

        return affected

    @classmethod
    def _delete_row_by_pk(
        cls,
        conn: sqlite3.Connection,
        table: str,
        pk_values: Mapping[str, Any],
        *,
        check_references: bool = True,
        commit: bool = True,
    ) -> int:
        """Delete a row by primary key with foreign key guards."""
        if table not in cls.TABLE_PRIMARY_KEYS:
            raise _PersistenceError(
                f"Table '{table}' is not in approved table catalogue."
            )

        expected_pks = cls.TABLE_PRIMARY_KEYS[table]
        missing_pks = [pk for pk in expected_pks if pk not in pk_values]
        if missing_pks:
            raise _PersistenceError(
                f"Missing primary key columns for '{table}': {missing_pks}"
            )

        if check_references and table in cls.TABLE_FOREIGN_KEY_GUARDS:
            guards = cls.TABLE_FOREIGN_KEY_GUARDS[table]
            for child_table, child_fk_col, parent_pk_col in guards:
                if parent_pk_col in pk_values:
                    cls._ensure_table_schema(conn, child_table)
                    parent_val = pk_values[parent_pk_col]
                    query = (
                        f'SELECT COUNT(*) FROM "{child_table}" '  # noqa: S608
                        f'WHERE "{child_fk_col}" = ?'
                    )
                    cursor = conn.execute(query, (parent_val,))
                    child_count = int(cursor.fetchone()[0])
                    if child_count > 0:
                        logger.error(
                            "%s: delete blocked by foreign key guard on %s "
                            "(dependent rows in %s: %d)",
                            DELETE_FR,
                            table,
                            child_table,
                            child_count,
                            extra={
                                "fr_id": DELETE_FR,
                                "table": table,
                                "child_table": child_table,
                                "count": child_count,
                            },
                        )
                        raise _PersistenceError(
                            f"Deletion blocked for '{table}': {child_count} dependent "
                            f"row(s) exist in '{child_table}'."
                        )

        where_clauses = [f'"{pk}" = ?' for pk in expected_pks]
        where_str = " AND ".join(where_clauses)
        sql = f'DELETE FROM "{table}" WHERE {where_str}'  # noqa: S608
        params = [pk_values[pk] for pk in expected_pks]

        try:
            if commit:
                with conn:
                    cursor = conn.execute(sql, params)
                    deleted = cursor.rowcount
            else:
                cursor = conn.execute(sql, params)
                deleted = cursor.rowcount
        except sqlite3.Error as err:
            logger.exception(
                "%s: delete failed on %s",
                DELETE_FR,
                table,
                extra={"fr_id": DELETE_FR, "table": table, "error": str(err)},
            )
            raise _PersistenceError(f"Delete on '{table}' failed: {err}") from err

        return deleted

    @classmethod
    def _delete_rows(
        cls,
        conn: sqlite3.Connection,
        table: str,
        where: Mapping[str, Any],
    ) -> int:
        """Delete multiple rows matching filter criteria."""
        if table not in cls.TABLE_PRIMARY_KEYS:
            raise _PersistenceError(
                f"Table '{table}' is not in approved table catalogue."
            )
        if not where:
            raise _PersistenceError("Delete requires non-empty where filter mapping.")

        where_sql, params = cls._build_where(where)
        sql = f'DELETE FROM "{table}"{where_sql}'  # noqa: S608
        try:
            with conn:
                cursor = conn.execute(sql, params)
                return cursor.rowcount
        except sqlite3.Error as err:
            raise _PersistenceError(f"Delete rows on '{table}' failed: {err}") from err

    # ------------------------------------------------------------------------
    # Canonical Public HostPersistence Operations
    # ------------------------------------------------------------------------

    @classmethod
    def create_record(
        cls,
        table: str,
        data: Mapping[str, Any],
        *,
        commit: bool = True,
    ) -> Any:
        """Insert a single record into an approved database table (canonical).

        Args:
            table: Target table name from approved catalog.
            data: Mapping of column names to values.
            commit: Whether to commit transaction immediately (default True).

        Returns:
            The primary key value or lastrowid of inserted row.

        Raises:
            PersistenceError: When validation or insertion fails.
        """
        if table not in cls.TABLE_PRIMARY_KEYS:
            raise _PersistenceError(
                f"Table '{table}' is not in approved table catalogue."
            )

        if table not in cls.TABLE_AUTOINCREMENT_PK_TABLES:
            missing_pks = [pk for pk in cls.TABLE_PRIMARY_KEYS[table] if pk not in data]
            if missing_pks:
                raise _PersistenceError(
                    f"Missing required primary key column(s) {missing_pks} "
                    f"for table '{table}'."
                )

        with cls._resolve_connection() as c:
            cls._ensure_table_schema(c, table)
            try:
                pk_val = cls._insert_row(c, table, data, commit=commit)
                logger.info(
                    "%s: created record in %s (key=%s)",
                    CREATE_FR,
                    table,
                    pk_val,
                    extra={"fr_id": CREATE_FR, "table": table, "key": str(pk_val)},
                )
                return pk_val
            except _PersistenceError as err:
                raise _PersistenceError(
                    f"Failed to create record in '{table}': {err}"
                ) from err

    @classmethod
    def create_entity(
        cls,
        entity_id: str,
        entity_type: str,
        scope: str,
        payload: str,
        *,
        revision: int = 1,
        created_at_utc: str | None = None,
        updated_at_utc: str | None = None,
        commit: bool = True,
    ) -> tuple[str, str]:
        """Insert a host entity record (canonical HostPersistence)."""
        now_iso = _current_utc_iso()
        data = {
            "entity_id": entity_id,
            "entity_type": entity_type,
            "scope": scope,
            "payload": payload,
            "revision": revision,
            "created_at_utc": created_at_utc or now_iso,
            "updated_at_utc": updated_at_utc or now_iso,
        }
        res = cls.create_record("host_entities", data, commit=commit)
        if isinstance(res, tuple):
            return (str(res[0]), str(res[1]))
        return (entity_id, entity_type)

    @classmethod
    def _resolve_cursor(
        cls,
        c: sqlite3.Connection,
        table: str,
        cursor_col: str | None,
        after_cursor: Any,
        order_by: str | None,
    ) -> tuple[str, list[Any], str | None]:
        """Resolve cursor column, where clause fragment, and ordering."""
        if cursor_col is None:
            return "", [], order_by
        clean_col = cursor_col.strip().strip('"')
        if not clean_col.replace("_", "").isalnum():
            raise _PersistenceError(f"Invalid cursor column name: '{cursor_col}'")
        col_cursor = c.execute(f'PRAGMA table_info("{table}")')
        valid_cols = {row[1] for row in col_cursor.fetchall()}
        if clean_col not in valid_cols:
            raise _PersistenceError(
                f"Invalid cursor column '{cursor_col}' for table '{table}'."
            )
        if after_cursor is None:
            return "", [], order_by
        eff_order = order_by or f"{clean_col} ASC"
        return f'"{clean_col}" > ?', [after_cursor], eff_order

    @staticmethod
    def _build_limit_offset(limit: int | None, offset: int | None) -> str:
        """Construct SQL limit/offset fragment."""
        if limit is None:
            return ""
        if offset is not None:
            return f" LIMIT {int(limit)} OFFSET {int(offset)}"
        return f" LIMIT {int(limit)}"

    @classmethod
    def read_records(
        cls,
        table: str,
        *,
        pk_values: Mapping[str, Any] | None = None,
        where: Mapping[str, Any] | None = None,
        order_by: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        cursor_col: str | None = None,
        after_cursor: Any = None,
    ) -> list[dict[str, Any]]:
        """Query rows with filtering and pagination (canonical)."""
        if table not in cls.TABLE_PRIMARY_KEYS:
            logger.error(
                "%s: rejected read_records for unapproved table %s",
                READ_FR,
                table,
                extra={"fr_id": READ_FR, "table": table},
            )
            raise _PersistenceError(
                f"Table '{table}' is not in approved table catalogue."
            )

        with cls._resolve_connection() as c:
            cls._ensure_table_schema(c, table)
            combined_where: dict[str, Any] = {}
            if pk_values:
                combined_where.update(pk_values)
            if where:
                combined_where.update(where)

            cursor_clause, c_params, eff_order = cls._resolve_cursor(
                c, table, cursor_col, after_cursor, order_by
            )
            where_sql, params = cls._build_where(combined_where)
            if cursor_clause:
                where_sql = (
                    f"{where_sql} AND {cursor_clause}"
                    if where_sql
                    else f" WHERE {cursor_clause}"
                )
                params.extend(c_params)

            order_sql = f" ORDER BY {eff_order}" if eff_order else ""
            limit_sql = cls._build_limit_offset(limit, offset)
            sql = f'SELECT * FROM "{table}"{where_sql}{order_sql}{limit_sql}'  # noqa: S608

            try:
                cursor = c.execute(sql, params)
                rows = [dict(r) for r in cursor.fetchall()]
            except sqlite3.Error as err:
                logger.exception(
                    "%s: read_records failed on %s",
                    READ_FR,
                    table,
                    extra={"fr_id": READ_FR, "table": table, "error": str(err)},
                )
                raise _PersistenceError(f"Query on '{table}' failed: {err}") from err

            logger.debug(
                "%s: read_records returned %d rows from %s",
                READ_FR,
                len(rows),
                table,
                extra={"fr_id": READ_FR, "table": table, "count": len(rows)},
            )
            return rows

    @classmethod
    def read_entity(
        cls,
        entity_id: str,
        entity_type: str,
    ) -> dict[str, Any] | None:
        """Retrieve an entity by composite key (canonical HostPersistence)."""
        rows = cls.read_records(
            "host_entities",
            pk_values={"entity_id": entity_id, "entity_type": entity_type},
            limit=1,
        )
        return rows[0] if rows else None

    @classmethod
    def update_record(
        cls,
        table: str,
        pk_values: Mapping[str, Any],
        updates: Mapping[str, Any],
        *,
        expected_revision: int | None = None,
        revision_col: str = "revision",
        upsert: bool = False,
        commit: bool = True,
    ) -> int:
        """Update a row with revision verification or upsert (canonical)."""
        if table not in cls.TABLE_PRIMARY_KEYS:
            raise _PersistenceError(
                f"Table '{table}' is not in approved table catalogue."
            )
        if not pk_values:
            raise _PersistenceError(
                f"update_record requires non-empty pk_values for table '{table}'."
            )
        if not updates and not upsert:
            raise _PersistenceError(
                f"update_record requires non-empty update_values for table '{table}'."
            )

        with cls._resolve_connection() as c:
            cls._ensure_table_schema(c, table)
            prev_conn = getattr(cls._local, "conn", None)
            cls._local.conn = c
            try:
                if expected_revision is not None:
                    cursor = c.execute(f'PRAGMA table_info("{table}")')
                    cols = {row[1] for row in cursor.fetchall()}
                    if revision_col not in cols:
                        raise _PersistenceError(
                            f"Table '{table}' does not contain "
                            f"revision column '{revision_col}'."
                        )
                    existing_rows = cls.read_records(
                        table, pk_values=pk_values, limit=1
                    )
                    if existing_rows:
                        curr_rev = existing_rows[0].get(revision_col)
                        if curr_rev is not None and int(curr_rev) != expected_revision:
                            logger.warning(
                                "%s: revision conflict on %s (expected=%d, current=%d)",
                                UPDATE_FR,
                                table,
                                expected_revision,
                                int(curr_rev),
                                extra={
                                    "fr_id": UPDATE_FR,
                                    "table": table,
                                    "expected_revision": expected_revision,
                                    "current_revision": int(curr_rev),
                                },
                            )
                            raise _RevisionConflictError(
                                expected_revision=expected_revision,
                                current_revision=int(curr_rev),
                            )

                if upsert:
                    existing_rows = cls.read_records(
                        table, pk_values=pk_values, limit=1
                    )
                    if not existing_rows:
                        combined_data = {**pk_values, **updates}
                        cls._insert_row(c, table, combined_data, commit=commit)
                        return 1

                affected = cls._update_row_by_pk(
                    c, table, pk_values, updates, commit=commit
                )
            finally:
                cls._local.conn = prev_conn

            logger.info(
                "%s: updated record in %s (affected=%d)",
                UPDATE_FR,
                table,
                affected,
                extra={"fr_id": UPDATE_FR, "table": table, "affected": affected},
            )
            return affected

    @classmethod
    def update_entity(
        cls,
        entity_id: str,
        entity_type: str,
        payload: str,
        *,
        expected_revision: int | None = None,
        revision: int | None = None,
        updated_at_utc: str | None = None,
        commit: bool = True,
    ) -> int:
        """Update an entity with optimistic CAS revision verification (canonical)."""
        now_iso = _current_utc_iso()
        with cls._resolve_connection() as c:
            prev_conn = getattr(cls._local, "conn", None)
            cls._local.conn = c
            try:
                existing = cls.read_entity(entity_id, entity_type)
                if existing is None:
                    return 0

                curr_rev = int(existing.get("revision", 1))
                if expected_revision is not None and curr_rev != expected_revision:
                    raise _RevisionConflictError(
                        f"Entity '{entity_id}' revision conflict: "
                        f"expected {expected_revision}, found {curr_rev}",
                        expected_revision=expected_revision,
                        current_revision=curr_rev,
                    )

                next_rev = revision if revision is not None else curr_rev + 1
                updates = {
                    "payload": payload,
                    "revision": next_rev,
                    "updated_at_utc": updated_at_utc or now_iso,
                }
                return cls.update_record(
                    "host_entities",
                    pk_values={"entity_id": entity_id, "entity_type": entity_type},
                    updates=updates,
                    commit=commit,
                )
            finally:
                cls._local.conn = prev_conn

    @classmethod
    def delete_record(
        cls,
        table: str,
        pk_values: Mapping[str, Any] | None = None,
        *,
        where: Mapping[str, Any] | None = None,
        check_references: bool = True,
        commit: bool = True,
    ) -> int:
        """Delete records with foreign key reference guards (canonical)."""
        if table not in cls.TABLE_PRIMARY_KEYS:
            raise _PersistenceError(
                f"Table '{table}' is not in approved table catalogue."
            )
        if not pk_values and not where:
            raise _PersistenceError(
                f"delete_record requires non-empty pk_values or where filter "
                f"for table '{table}'."
            )

        with cls._resolve_connection() as c:
            cls._ensure_table_schema(c, table)
            if pk_values:
                deleted = cls._delete_row_by_pk(
                    c,
                    table,
                    pk_values,
                    check_references=check_references,
                    commit=commit,
                )
            elif where is not None:
                deleted = cls._delete_rows(c, table, where)
            else:
                raise _PersistenceError(
                    f"Deletion requires non-empty criteria on '{table}'."
                )

            logger.info(
                "%s: deleted record(s) from %s (deleted=%d)",
                DELETE_FR,
                table,
                deleted,
                extra={"fr_id": DELETE_FR, "table": table, "deleted": deleted},
            )
            return deleted

    @classmethod
    def delete_entity(
        cls,
        entity_id: str,
        entity_type: str,
        *,
        commit: bool = True,
    ) -> bool:
        """Delete an entity by composite key (canonical HostPersistence)."""
        deleted = cls.delete_record(
            "host_entities",
            pk_values={"entity_id": entity_id, "entity_type": entity_type},
            commit=commit,
        )
        return deleted > 0

    @classmethod
    def _batch_op_create(
        cls, active_c: sqlite3.Connection, idx: int, op: _BatchOperation
    ) -> tuple[int, dict[str, Any]]:
        """Execute single batch create/insert operation."""
        if not op.data:
            raise _PersistenceError(
                f"Create operation at index {idx} on '{op.table}' "
                "requires non-empty data."
            )
        pk_res = cls._insert_row(active_c, op.table, op.data, commit=False)
        return 1, {
            "index": idx,
            "op": op.op_type.lower(),
            "table": op.table,
            "status": "created",
            "key": pk_res,
        }

    @classmethod
    def _batch_op_update(
        cls, idx: int, op: _BatchOperation
    ) -> tuple[int, dict[str, Any]]:
        """Execute single batch update operation."""
        if not op.pk_values or not op.data:
            raise _PersistenceError(
                f"Update operation at index {idx} on '{op.table}' requires both "
                "pk_values and data."
            )
        aff = cls.update_record(
            op.table,
            op.pk_values,
            op.data,
            expected_revision=op.expected_revision,
            revision_col=op.revision_col,
            commit=False,
        )
        return aff, {
            "index": idx,
            "op": op.op_type.lower(),
            "table": op.table,
            "status": "updated",
            "affected": aff,
        }

    @classmethod
    def _batch_op_delete(
        cls, idx: int, op: _BatchOperation
    ) -> tuple[int, dict[str, Any]]:
        """Execute single batch delete operation."""
        if not op.pk_values:
            raise _PersistenceError(
                f"Delete operation at index {idx} on '{op.table}' requires pk_values."
            )
        aff = cls.delete_record(op.table, op.pk_values, commit=False)
        return aff, {
            "index": idx,
            "op": op.op_type.lower(),
            "table": op.table,
            "status": "deleted",
            "affected": aff,
        }

    @classmethod
    def _batch_op_upsert(
        cls, active_c: sqlite3.Connection, idx: int, op: _BatchOperation
    ) -> tuple[int, dict[str, Any]]:
        """Execute single batch upsert operation."""
        if not op.data:
            raise _PersistenceError(
                f"Upsert operation at index {idx} on '{op.table}' "
                "requires non-empty data."
            )
        pk_cols = cls.TABLE_PRIMARY_KEYS[op.table]
        target_pk = op.pk_values or {
            col: op.data[col] for col in pk_cols if col in op.data
        }
        if len(target_pk) != len(pk_cols):
            raise _PersistenceError(
                f"Upsert operation at index {idx} on '{op.table}' "
                "requires complete primary key specification."
            )
        existing_rows = cls.read_records(op.table, pk_values=target_pk, limit=1)
        if existing_rows:
            aff = cls.update_record(
                op.table,
                target_pk,
                op.data,
                expected_revision=op.expected_revision,
                revision_col=op.revision_col,
                commit=False,
            )
            return aff, {
                "index": idx,
                "op": "upsert",
                "table": op.table,
                "status": "updated",
                "affected": aff,
            }
        pk_res = cls._insert_row(active_c, op.table, op.data, commit=False)
        return 1, {
            "index": idx,
            "op": "upsert",
            "table": op.table,
            "status": "inserted",
            "key": pk_res,
        }

    @classmethod
    def _execute_batch_op(
        cls, active_c: sqlite3.Connection, idx: int, op: _BatchOperation
    ) -> tuple[int, dict[str, Any]]:
        """Dispatch a single batch operation to its typed handler."""
        op_type = op.op_type.lower()
        if op.table not in cls.TABLE_PRIMARY_KEYS:
            raise _PersistenceError(
                f"Table '{op.table}' at batch index {idx} is not in approved table set."
            )
        cls._ensure_table_schema(active_c, op.table)
        if op_type in ("create", "insert"):
            return cls._batch_op_create(active_c, idx, op)
        if op_type == "update":
            return cls._batch_op_update(idx, op)
        if op_type == "delete":
            return cls._batch_op_delete(idx, op)
        if op_type == "upsert":
            return cls._batch_op_upsert(active_c, idx, op)
        raise _PersistenceError(
            f"Unsupported batch operation '{op.op_type}' at index {idx}."
        )

    @classmethod
    def apply_batch(
        cls,
        operations: Sequence[_BatchOperation],
    ) -> _BatchResult:
        """Execute atomic batch writes with rollback (canonical)."""
        if getattr(cls._local, "conn", None) is not None:
            logger.error(
                "%s: caller transaction already active",
                BATCH_FR,
                extra={"fr_id": BATCH_FR},
            )
            raise _PersistenceError(
                "Batch operations require an idle connection with no active "
                "transaction."
            )

        if not operations:
            return _BatchResult(total_operations=0, affected_rows=0, details=[])

        with cls._resolve_connection() as c:
            if c.in_transaction:
                logger.error(
                    "%s: caller transaction already active",
                    BATCH_FR,
                    extra={"fr_id": BATCH_FR},
                )
                raise _PersistenceError(
                    "Batch operations require an idle connection with no active "
                    "transaction."
                )

            logger.debug(
                "%s: beginning atomic batch transaction with %d operations",
                BATCH_FR,
                len(operations),
                extra={"fr_id": BATCH_FR, "operations_count": len(operations)},
            )

            details: list[dict[str, Any]] = []
            total_affected = 0

            cls._local.conn = c
            c.execute("BEGIN IMMEDIATE")
            try:
                for idx, op in enumerate(operations):
                    aff, detail = cls._execute_batch_op(c, idx, op)
                    total_affected += aff
                    details.append(detail)
                c.commit()
            except Exception as err:
                c.rollback()
                logger.exception(
                    "%s: batch transaction failed, rolled back completely",
                    BATCH_FR,
                    extra={"fr_id": BATCH_FR, "error": str(err)},
                )
                if isinstance(err, _RevisionConflictError):
                    raise
                raise _PersistenceError(f"Batch transaction failed: {err}") from err
            finally:
                cls._local.conn = None

            logger.info(
                "%s: committed atomic batch transaction with %d operations "
                "(%d affected rows)",
                BATCH_FR,
                len(operations),
                total_affected,
                extra={
                    "fr_id": BATCH_FR,
                    "total_operations": len(operations),
                    "affected_rows": total_affected,
                },
            )
            return _BatchResult(
                total_operations=len(operations),
                affected_rows=total_affected,
                details=details,
            )


class HostPersistenceCLI:
    """Command-line interface formatter and demo runner for HostPersistence."""

    @staticmethod
    def format_output(result: Mapping[str, Any]) -> str:
        """Format batch result dictionary for CLI display."""
        lines = [
            f"total_operations: {result.get('total_operations', 0)}",
            f"affected_rows: {result.get('affected_rows', 0)}",
            f"details: {result.get('details', [])}",
        ]
        return "\n".join(lines)

    @classmethod
    def run_cli(cls, argv: Sequence[str] | None = None) -> int:
        """Run CLI diagnostic demonstration for HostPersistence."""
        _ = argv
        prev_db = HostPersistence.DEFAULT_DB_PATH
        with tempfile.TemporaryDirectory(
            prefix="hqai_persistence_cli_",
            ignore_cleanup_errors=True,
        ) as tmp_dir:
            HostPersistence.DEFAULT_DB_PATH = Path(tmp_dir) / "demo.db"
            try:
                ops = [
                    _BatchOperation(
                        op_type="create",
                        table="host_settings",
                        data={
                            "scope": "sys",
                            "key": "demo_key",
                            "value_json": '{"active": true}',
                            "updated_at_utc": _current_utc_iso(),
                        },
                    ),
                    _BatchOperation(
                        op_type="update",
                        table="host_settings",
                        pk_values={"scope": "sys", "key": "demo_key"},
                        data={"value_json": '{"active": false}'},
                    ),
                ]
                res = HostPersistence.apply_batch(ops)
                output = cls.format_output(res.to_dict())
                sys.stdout.write(output + "\n")
                return 0
            finally:
                HostPersistence.DEFAULT_DB_PATH = prev_db


if __name__ == "__main__":
    raise SystemExit(HostPersistenceCLI.run_cli(sys.argv[1:]))
