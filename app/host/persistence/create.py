"""Database connection, table schema creation, and row insertion operations.

Description:
    Provides the isolated SQLite persistence creation foundation for the host
    platform and data workspaces. Manages database connection lifecycle with
    write-ahead logging (WAL mode), busy timeout handling, and foreign key
    enforcement targeting data/database/haruquantai.db or isolated test stores.
    Owns idempotent DDL schema creation across all 25 operational tables and
    parameterized record insertion operations.

Purpose:
    FEAT-HOST-PERSISTENCE: Host platform and workspace isolated SQLite persistence.

Key Capabilities:
    - FR-HOST-PERSISTENCE-CONNECT: Initialize database connection in WAL mode.
      Associated: `get_connection()`
      Logging: DEBUG emitted on connection opening; ERROR on connection failure.
    - FR-HOST-PERSISTENCE-CREATE-SCHEMA: Create all 25 operational database tables
      or ensure individual table schemas idempotently.
      Associated: `create_schema()`, `ensure_table_schema()`
      Logging: INFO emitted on schema creation completion; ERROR on DDL failure.
    - FR-HOST-PERSISTENCE-INSERT: Insert records into database tables.
      Associated: `insert_row()`, `create_record()`, `create_entity()`,
      and 25 domain-specific typed creation helpers.
      Logging: DEBUG emitted on successful insert; ERROR on constraint or validation
      failure.

Python API Usage:
    ```python
    from app.host.persistence.create import (
        create_record,
        create_schema,
        get_connection,
        insert_row,
    )

    conn = get_connection("data/database/haruquantai.db")
    create_schema(conn)
    row_id = insert_row(
        conn, "host_settings", {"scope": "sys", "key": "k", "value_json": "{}"}
    )
    ```

CLI Usage:
    ```bash
    uv run python -c "from app.host.persistence.create import get_connection"
    ```
"""

from __future__ import annotations

import sqlite3
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.host.logging import get_logger

logger = get_logger(__name__)

CONNECT_FR = "FR-HOST-PERSISTENCE-CONNECT"
CREATE_SCHEMA_FR = "FR-HOST-PERSISTENCE-CREATE-SCHEMA"
INSERT_FR = "FR-HOST-PERSISTENCE-INSERT"

DEFAULT_DB_PATH: Path = Path("data/database/haruquantai.db")

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
    "host_grid_leases": """CREATE TABLE IF NOT EXISTS "host_grid_leases" (
    lease_id TEXT PRIMARY KEY,
    node_id TEXT NOT NULL REFERENCES "host_grid_nodes"(node_id),
    job_id TEXT NOT NULL REFERENCES "host_jobs"(job_id),
    leased_at_utc TEXT NOT NULL,
    expires_at_utc TEXT NOT NULL,
    state TEXT NOT NULL
)""",
    "host_grid_nodes": """CREATE TABLE IF NOT EXISTS "host_grid_nodes" (
    node_id TEXT PRIMARY KEY,
    host TEXT NOT NULL,
    port INTEGER NOT NULL,
    cores INTEGER NOT NULL,
    memory_mb INTEGER NOT NULL,
    state TEXT NOT NULL,
    last_heartbeat_utc TEXT NOT NULL
)""",
    "host_job_attempts": """CREATE TABLE IF NOT EXISTS "host_job_attempts" (
    attempt_id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL REFERENCES "host_jobs"(job_id),
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

SCHEMA_DDL: tuple[str, ...] = tuple(TABLE_DDL_MAP.values())
PERSISTENCE_TABLES: tuple[str, ...] = tuple(TABLE_DDL_MAP.keys())


class PersistenceError(Exception):
    """Base exception for persistence failures."""


def current_utc_iso() -> str:
    """Return formatted current UTC timestamp in ISO 8601."""
    return datetime.now(UTC).isoformat()


def get_connection(db_path: Path | str | None = None) -> sqlite3.Connection:
    """Connect to SQLite database with WAL mode and foreign key enforcement.

    Args:
        db_path: Path to SQLite database file or None to use default.

    Returns:
        sqlite3.Connection configured with WAL journal mode and Row factory.

    Raises:
        PersistenceError: When connection or configuration fails.
    """
    target = DEFAULT_DB_PATH if db_path is None else Path(db_path)
    logger.debug(
        "%s: opening connection to %s",
        CONNECT_FR,
        target,
        extra={"fr_id": CONNECT_FR, "path": str(target)},
    )
    try:
        if str(target) != ":memory:":
            target.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(target)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.execute("PRAGMA busy_timeout = 5000;")
        conn.execute("PRAGMA foreign_keys = ON;")
    except (sqlite3.Error, OSError, ValueError) as err:
        logger.exception(
            "%s: connection failed to %s",
            CONNECT_FR,
            target,
            extra={"fr_id": CONNECT_FR, "error": str(err)},
        )
        raise PersistenceError(f"Database connection failed: {err}") from err

    logger.debug(
        "%s: connection established in WAL mode",
        CONNECT_FR,
        extra={"fr_id": CONNECT_FR},
    )
    return conn


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


def create_schema(conn: sqlite3.Connection) -> None:
    """Idempotently create all 25 operational database tables.

    Args:
        conn: Open SQLite connection.

    Raises:
        PersistenceError: When table creation fails.
    """
    logger.debug(
        "%s: starting schema initialization",
        CREATE_SCHEMA_FR,
        extra={"fr_id": CREATE_SCHEMA_FR},
    )
    try:
        with conn:
            for ddl in SCHEMA_DDL:
                conn.execute(ddl)
    except sqlite3.Error as err:
        logger.exception(
            "%s: schema creation failed",
            CREATE_SCHEMA_FR,
            extra={"fr_id": CREATE_SCHEMA_FR, "error": str(err)},
        )
        raise PersistenceError(f"Schema creation failed: {err}") from err

    logger.info(
        "%s: successfully ensured 25 operational tables",
        CREATE_SCHEMA_FR,
        extra={"fr_id": CREATE_SCHEMA_FR, "table_count": len(SCHEMA_DDL)},
    )


def ensure_table_schema(conn: sqlite3.Connection, table: str) -> None:
    """Ensure a specific table exists by executing its canonical DDL statement.

    Args:
        conn: Open SQLite connection.
        table: Target table name from TABLE_DDL_MAP.

    Raises:
        PersistenceError: When table is unapproved or DDL execution fails.
    """
    if table not in TABLE_DDL_MAP:
        logger.error(
            "%s: rejected schema creation for unapproved table %s",
            CREATE_SCHEMA_FR,
            table,
            extra={"fr_id": CREATE_SCHEMA_FR, "table": table},
        )
        raise PersistenceError(
            f"Table '{table}' is not an approved operational persistence table."
        )

    try:
        conn.execute(TABLE_DDL_MAP[table])
    except sqlite3.Error as err:
        logger.exception(
            "%s: failed ensuring table schema for %s",
            CREATE_SCHEMA_FR,
            table,
            extra={"fr_id": CREATE_SCHEMA_FR, "table": table, "error": str(err)},
        )
        raise PersistenceError(f"Ensuring schema for '{table}' failed: {err}") from err


def insert_row(
    conn: sqlite3.Connection,
    table: str,
    data: Mapping[str, Any],
    *,
    commit: bool = True,
) -> Any:
    """Insert a record into an allowed database table.

    Args:
        conn: Open SQLite connection.
        table: Target table name.
        data: Mapping of column names to values.
        commit: Whether to commit the transaction immediately (default True).

    Returns:
        The lastrowid integer or the table primary key value from data.

    Raises:
        PersistenceError: If table is invalid, data is empty, or execution fails.
    """
    if table not in TABLE_PRIMARY_KEYS:
        logger.error(
            "%s: rejected insert into unapproved table %s",
            INSERT_FR,
            table,
            extra={"fr_id": INSERT_FR, "table": table},
        )
        raise PersistenceError(f"Table '{table}' is not in approved table catalogue.")

    if not data:
        logger.error(
            "%s: rejected insert with empty data mapping for table %s",
            INSERT_FR,
            table,
            extra={"fr_id": INSERT_FR, "table": table},
        )
        raise PersistenceError("Insert data dictionary cannot be empty.")

    columns = list(data.keys())
    placeholders = ", ".join("?" for _ in columns)
    quoted_cols = ", ".join(f'"{col}"' for col in columns)
    sql = f'INSERT INTO "{table}" ({quoted_cols}) VALUES ({placeholders})'  # noqa: S608
    values = [data[col] for col in columns]

    logger.debug(
        "%s: inserting into %s (cols=%s)",
        INSERT_FR,
        table,
        columns,
        extra={"fr_id": INSERT_FR, "table": table},
    )
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
            INSERT_FR,
            table,
            extra={"fr_id": INSERT_FR, "table": table, "error": str(err)},
        )
        raise PersistenceError(f"Insert into '{table}' failed: {err}") from err

    logger.debug(
        "%s: inserted into %s (lastrowid=%s)",
        INSERT_FR,
        table,
        last_id,
        extra={"fr_id": INSERT_FR, "table": table, "lastrowid": last_id},
    )
    pk_cols = TABLE_PRIMARY_KEYS[table]
    if len(pk_cols) == 1 and pk_cols[0] in data:
        return data[pk_cols[0]]
    if len(pk_cols) > 1 and all(k in data for k in pk_cols):
        return tuple(data[k] for k in pk_cols)
    return last_id


def create_record(
    conn: sqlite3.Connection,
    table: str,
    data: Mapping[str, Any],
    *,
    commit: bool = True,
) -> Any:
    """Insert a single record into an approved database table.

    Args:
        conn: Open SQLite connection.
        table: Target table name.
        data: Mapping of column names to values.
        commit: Whether to commit the transaction immediately (default True).

    Returns:
        The table primary key value or lastrowid of the inserted record.

    Raises:
        PersistenceError: When validation or insertion fails.
    """
    if table not in TABLE_PRIMARY_KEYS:
        raise PersistenceError(f"Table '{table}' is not in approved table catalogue.")

    if table not in TABLE_AUTOINCREMENT_PK_TABLES:
        missing_pks = [pk for pk in TABLE_PRIMARY_KEYS[table] if pk not in data]
        if missing_pks:
            raise PersistenceError(
                f"Missing required primary key column(s) {missing_pks} "
                f"for table '{table}'."
            )

    try:
        return insert_row(conn, table, data, commit=commit)
    except PersistenceError as err:
        raise PersistenceError(f"Failed to create record in '{table}': {err}") from err


def create_entity(
    conn: sqlite3.Connection,
    entity_id: str,
    entity_type: str,
    scope: str,
    payload: str,
    *,
    revision: int = 1,
    created_at_utc: str | None = None,
    updated_at_utc: str | None = None,
) -> tuple[str, str]:
    """Insert a host entity record (canonical HostPersistence).

    Args:
        conn: Open SQLite connection.
        entity_id: Unique entity ID.
        entity_type: Entity classification.
        scope: Entity visibility or domain scope.
        payload: Entity payload JSON or text.
        revision: Initial optimistic revision counter (default 1).
        created_at_utc: Creation timestamp or current UTC.
        updated_at_utc: Update timestamp or current UTC.

    Returns:
        Composite primary key (entity_id, entity_type).
    """
    now_iso = current_utc_iso()
    data = {
        "entity_id": entity_id,
        "entity_type": entity_type,
        "scope": scope,
        "payload": payload,
        "revision": revision,
        "created_at_utc": created_at_utc or now_iso,
        "updated_at_utc": updated_at_utc or now_iso,
    }
    insert_row(conn, "host_entities", data)
    return (entity_id, entity_type)


create_host_entity = create_entity


def create_host_setting(
    conn: sqlite3.Connection,
    scope: str,
    key: str,
    value_json: str,
    *,
    schema_version: int = 1,
    updated_at_utc: str | None = None,
) -> tuple[str, str]:
    """Insert a host setting row."""
    data = {
        "scope": scope,
        "key": key,
        "value_json": value_json,
        "schema_version": schema_version,
        "updated_at_utc": updated_at_utc or current_utc_iso(),
    }
    insert_row(conn, "host_settings", data)
    return (scope, key)


def create_host_session(
    conn: sqlite3.Connection,
    session_id: str,
    token_hash: str,
    username: str,
    peer_id: str,
    *,
    created_at_utc: str,
    expires_at_utc: str,
    status: str,
    revoked_at_utc: str | None = None,
) -> str:
    """Insert a host session record."""
    data = {
        "session_id": session_id,
        "token_hash": token_hash,
        "username": username,
        "peer_id": peer_id,
        "created_at_utc": created_at_utc,
        "expires_at_utc": expires_at_utc,
        "revoked_at_utc": revoked_at_utc,
        "status": status,
    }
    insert_row(conn, "host_session", data)
    return session_id


def create_host_job(
    conn: sqlite3.Connection,
    job_id: str,
    *,
    owner: str = "default",
    kind: str = "compute",
    status: str = "completed",
    progress: float = 0.0,
    accepted: int = 0,
    rejected: int = 0,
    message: str = "",
    attempt_id: int = 1,
    max_retries: int = 0,
    retry_count: int = 0,
    dedup_key: str | None = None,
    parent_job_id: str | None = None,
    child_job_ids_json: str = "[]",
    budget_json: str = "{}",
    submitted_at_utc: str = "",
    started_at_utc: str | None = None,
    finished_at_utc: str | None = None,
    error_message: str | None = None,
    error_location: str | None = None,
) -> str:
    """Insert a host job record."""
    data = {
        "job_id": job_id,
        "owner": owner,
        "kind": kind,
        "status": status,
        "progress": progress,
        "accepted": accepted,
        "rejected": rejected,
        "message": message,
        "attempt_id": attempt_id,
        "max_retries": max_retries,
        "retry_count": retry_count,
        "dedup_key": dedup_key,
        "parent_job_id": parent_job_id,
        "child_job_ids_json": child_job_ids_json,
        "budget_json": budget_json,
        "submitted_at_utc": submitted_at_utc or current_utc_iso(),
        "started_at_utc": started_at_utc,
        "finished_at_utc": finished_at_utc,
        "error_message": error_message,
        "error_location": error_location,
    }
    insert_row(conn, "host_jobs", data)
    return job_id


def create_datamgr_broker(
    conn: sqlite3.Connection,
    name: str,
    *,
    created_at_utc: str,
    updated_at_utc: str,
    is_system: int = 0,
    description: str = "",
    stockpicker_use: int = 0,
    mt_use: int = 0,
    server_timezone: str = "UTC",
    postfix: str = "",
    enabled: int = 1,
    clock_policy_json: str = "{}",
    clock_policy_revision: int = 0,
) -> int:
    """Insert a datamgr_broker record."""
    data = {
        "name": name,
        "is_system": is_system,
        "description": description,
        "stockpicker_use": stockpicker_use,
        "mt_use": mt_use,
        "server_timezone": server_timezone,
        "postfix": postfix,
        "enabled": enabled,
        "created_at_utc": created_at_utc,
        "updated_at_utc": updated_at_utc,
        "clock_policy_json": clock_policy_json,
        "clock_policy_revision": clock_policy_revision,
    }
    res = insert_row(conn, "datamgr_broker", data)
    return int(res)


def create_datamgr_dataset(
    conn: sqlite3.Connection,
    dataset_id: str,
    *,
    source: str,
    symbol: str,
    underlying: str,
    instrument: str,
    timeframe: str,
    broker: str,
    broker_name: str,
    timezone_name: str,
    category: str,
    date_from: str,
    date_to: str,
    created_at: str,
    updated_at: str,
    bars: int = 0,
    path: str = "",
    data_kind: str = "bars",
    quality_score: float = 1.0,
    lineage_json: str = "{}",
    schema_version: int = 1,
) -> str:
    """Insert a datamgr_datasets record."""
    data = {
        "id": dataset_id,
        "source": source,
        "symbol": symbol,
        "underlying": underlying,
        "instrument": instrument,
        "timeframe": timeframe,
        "broker": broker,
        "broker_name": broker_name,
        "timezone": timezone_name,
        "category": category,
        "date_from": date_from,
        "date_to": date_to,
        "bars": bars,
        "created_at": created_at,
        "updated_at": updated_at,
        "path": path,
        "data_kind": data_kind,
        "quality_score": quality_score,
        "lineage_json": lineage_json,
        "schema_version": schema_version,
    }
    insert_row(conn, "datamgr_datasets", data)
    return dataset_id


def create_datamgr_instrument(
    conn: sqlite3.Connection | Path | str | None = None,
    symbol: str = "",
    *,
    created_at_utc: str | None = None,
    updated_at_utc: str | None = None,
    connection: str = "",
    broker_id: int = 0,
    description: str = "",
    tick_size: float = 0.00001,
    tick_step: float = 0.00001,
    tick_value_in_money: float = 10.0,
    point_value: float = 100000.0,
    decimals: int = 5,
    default_spread: float = 0.0001,
    default_slippage: float = 0.0,
    min_volume: float = 0.01,
    max_volume: float = 100.0,
    lot_step: float = 0.01,
    margin_rate: float = 0.05,
    swap_long: float = 0.0,
    swap_short: float = 0.0,
    swap_3day_day: int = 3,
    commissions: str = "0.0",
    data_type: str = "Forex",
    alias: str = "",
    exchange: str = "",
    country: str = "",
    sector: str = "",
    min_distance: float = 0.0,
    order_size_multiplier: float = 1.0,
    order_size_step: float = 0.0,
    cot: str | None = None,
) -> int:
    """Insert a datamgr_instruments record."""
    from datetime import UTC, datetime

    from app.host.persistence.read import resolve_connection

    now_iso = datetime.now(UTC).isoformat()
    data = {
        "symbol": symbol,
        "connection": connection,
        "broker_id": broker_id,
        "description": description,
        "tick_size": tick_size,
        "tick_step": tick_step,
        "tick_value_in_money": tick_value_in_money,
        "point_value": point_value,
        "decimals": decimals,
        "default_spread": default_spread,
        "default_slippage": default_slippage,
        "min_volume": min_volume,
        "max_volume": max_volume,
        "lot_step": lot_step,
        "margin_rate": margin_rate,
        "swap_long": swap_long,
        "swap_short": swap_short,
        "swap_3day_day": swap_3day_day,
        "commissions": commissions,
        "data_type": data_type,
        "alias": alias,
        "exchange": exchange,
        "country": country,
        "sector": sector,
        "created_at_utc": created_at_utc or now_iso,
        "updated_at_utc": updated_at_utc or now_iso,
        "min_distance": min_distance,
        "order_size_multiplier": order_size_multiplier,
        "order_size_step": order_size_step,
        "cot": cot,
    }
    with resolve_connection(conn) as active_conn:
        res = insert_row(active_conn, "datamgr_instruments", data)
    return int(res)


def create_datamgr_session(
    conn: sqlite3.Connection | Path | str | None = None,
    name: str = "",
    *,
    description: str = "",
    timezone_name: str = "UTC",
    windows_json: str = "[]",
    holidays_json: str = "[]",
    is_default: int = 0,
    broker_id: int = -1,
) -> int:
    """Insert a datamgr_sessions record."""
    from app.host.persistence.read import resolve_connection

    data = {
        "name": name,
        "description": description,
        "timezone": timezone_name,
        "windows_json": windows_json,
        "holidays_json": holidays_json,
        "is_default": is_default,
        "broker_id": broker_id,
    }
    with resolve_connection(conn) as active_conn:
        res = insert_row(active_conn, "datamgr_sessions", data)
    return int(res)


def create_mt5_command(
    conn: sqlite3.Connection,
    command_id: str,
    *,
    object_id: str,
    class_name: str,
    method_name: str,
    args_json: str,
    requires_arm: int,
    created_at: float,
    status: str,
    session_id: str | None = None,
    sent_at: float | None = None,
    acknowledged_at: float | None = None,
    resolved_at: float | None = None,
    native_request_id: str | None = None,
    value_json: str | None = None,
    meta_json: str | None = None,
    error_json: str | None = None,
) -> str:
    """Insert an mt5_commands record."""
    data = {
        "command_id": command_id,
        "session_id": session_id,
        "object_id": object_id,
        "class_name": class_name,
        "method_name": method_name,
        "args_json": args_json,
        "requires_arm": requires_arm,
        "created_at": created_at,
        "sent_at": sent_at,
        "acknowledged_at": acknowledged_at,
        "resolved_at": resolved_at,
        "status": status,
        "native_request_id": native_request_id,
        "value_json": value_json,
        "meta_json": meta_json,
        "error_json": error_json,
    }
    insert_row(conn, "mt5_commands", data)
    return command_id


def create_mt5_event(
    conn: sqlite3.Connection,
    event_type: str,
    payload_json: str,
    received_at: float,
    *,
    session_id: str | None = None,
    command_id: str | None = None,
    native_request_id: str | None = None,
) -> int:
    """Insert an mt5_events record."""
    data = {
        "session_id": session_id,
        "command_id": command_id,
        "native_request_id": native_request_id,
        "event_type": event_type,
        "payload_json": payload_json,
        "received_at": received_at,
    }
    res = insert_row(conn, "mt5_events", data)
    return int(res)


def create_datamgr_broker_stock(
    conn: sqlite3.Connection,
    ticker: str,
    broker_id: int,
) -> int:
    """Insert a datamgr_broker_stock record."""
    data = {
        "TICKER": ticker,
        "BROKER_ID": broker_id,
    }
    res = insert_row(conn, "datamgr_broker_stock", data)
    return int(res)


def create_datamgr_commodity(
    conn: sqlite3.Connection,
    code: str,
    *,
    commodity_id: int | None = None,
    name: str | None = None,
    point_value: float | None = None,
    tick_step: float | None = None,
    tick_size: float | None = None,
    order_size_multi: float | None = None,
    order_size_step: float | None = None,
    exchange: str | None = None,
) -> int:
    """Insert a datamgr_commodities record."""
    data: dict[str, Any] = {"code": code}
    if commodity_id is not None:
        data["id"] = commodity_id
    if name is not None:
        data["name"] = name
    if point_value is not None:
        data["point_value"] = point_value
    if tick_step is not None:
        data["tick_step"] = tick_step
    if tick_size is not None:
        data["tick_size"] = tick_size
    if order_size_multi is not None:
        data["order_size_multi"] = order_size_multi
    if order_size_step is not None:
        data["order_size_step"] = order_size_step
    if exchange is not None:
        data["exchange"] = exchange
    res = insert_row(conn, "datamgr_commodities", data)
    return int(res)


def create_datamgr_crypto_catalog(
    conn: sqlite3.Connection,
    exchange: str,
    symbol: str,
    *,
    point_value: float = 1.0,
    tick_size: float = 1e-8,
    tick_step: float = 1e-8,
    default_spread: float = 0.0,
    default_slippage: float = 0.0,
    date_from: str | None = None,
    price_precision: int = 8,
    name: str | None = None,
    updated_at: str | None = None,
) -> tuple[str, str]:
    """Insert a datamgr_crypto_catalog record."""
    data: dict[str, Any] = {
        "exchange": exchange,
        "symbol": symbol,
        "point_value": point_value,
        "tick_size": tick_size,
        "tick_step": tick_step,
        "default_spread": default_spread,
        "default_slippage": default_slippage,
        "date_from": date_from,
        "price_precision": price_precision,
        "name": name,
        "updated_at": updated_at or current_utc_iso(),
    }
    insert_row(conn, "datamgr_crypto_catalog", data)
    return (exchange, symbol)


def create_datamgr_log(
    conn: sqlite3.Connection,
    timestamp_utc: str,
    action: str,
    message: str,
    *,
    symbol: str | None = None,
    details: str = "{}",
    created_at: str | None = None,
) -> int:
    """Insert a datamgr_logs record."""
    data: dict[str, Any] = {
        "timestamp_utc": timestamp_utc,
        "action": action,
        "message": message,
        "symbol": symbol,
        "details": details,
    }
    if created_at is not None:
        data["created_at"] = created_at
    res = insert_row(conn, "datamgr_logs", data)
    return int(res)


def create_datamgr_operation_log(
    conn: sqlite3.Connection,
    timestamp_utc: str,
    symbol: str,
    operation: str,
    *,
    status: str,
    message: str,
) -> int:
    """Insert a datamgr_operation_log record."""
    data = {
        "timestamp_utc": timestamp_utc,
        "symbol": symbol,
        "operation": operation,
        "status": status,
        "message": message,
    }
    res = insert_row(conn, "datamgr_operation_log", data)
    return int(res)


def create_datamgr_quality_report(
    conn: sqlite3.Connection,
    report_id: str,
    dataset_id: str,
    quality_score: float,
    total_records: int,
    *,
    anomalies_json: str = "[]",
    anomaly_counts_json: str = "{}",
    evaluated_at_utc: str | None = None,
) -> str:
    """Insert a datamgr_quality record."""
    data = {
        "report_id": report_id,
        "dataset_id": dataset_id,
        "quality_score": quality_score,
        "total_records": total_records,
        "anomalies_json": anomalies_json,
        "anomaly_counts_json": anomaly_counts_json,
        "evaluated_at_utc": evaluated_at_utc or current_utc_iso(),
    }
    insert_row(conn, "datamgr_quality", data)
    return report_id


def create_datamgr_stock(
    conn: sqlite3.Connection,
    ticker: str,
    basket_id: int,
    date_from: int,
    *,
    date_to: int | None = None,
) -> int:
    """Insert a datamgr_stock record."""
    data: dict[str, Any] = {
        "TICKER": ticker,
        "BASKET_ID": basket_id,
        "DATE_FROM": date_from,
        "DATE_TO": date_to,
    }
    res = insert_row(conn, "datamgr_stock", data)
    return int(res)


def create_datamgr_stock_group(
    conn: sqlite3.Connection,
    name: str,
    system: bool = False,
    *,
    desc: str | None = None,
    description: str = "",
) -> int:
    """Insert a datamgr_stock_group record."""
    data: dict[str, Any] = {
        "NAME": name,
        "SYSTEM": 1 if system else 0,
        "DESC": desc,
        "description": description,
    }
    res = insert_row(conn, "datamgr_stock_group", data)
    return int(res)


def create_datamgr_ticker(
    conn: sqlite3.Connection,
    ticker: str,
    *,
    name: str | None = None,
    commodity_code: str | None = None,
    exchange: str | None = None,
    timeframe: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> int:
    """Insert a datamgr_tickers record."""
    data: dict[str, Any] = {
        "ticker": ticker,
        "name": name,
        "commodity_code": commodity_code,
        "exchange": exchange,
        "timeframe": timeframe,
        "date_from": date_from,
        "date_to": date_to,
    }
    res = insert_row(conn, "datamgr_tickers", data)
    return int(res)


def create_host_grid_lease(
    conn: sqlite3.Connection,
    lease_id: str,
    node_id: str,
    job_id: str,
    *,
    leased_at_utc: str | None = None,
    expires_at_utc: str | None = None,
    state: str = "active",
) -> str:
    """Insert a host_grid_leases record."""
    now_iso = current_utc_iso()
    data = {
        "lease_id": lease_id,
        "node_id": node_id,
        "job_id": job_id,
        "leased_at_utc": leased_at_utc or now_iso,
        "expires_at_utc": expires_at_utc or now_iso,
        "state": state,
    }
    insert_row(conn, "host_grid_leases", data)
    return lease_id


def create_host_grid_node(
    conn: sqlite3.Connection,
    node_id: str,
    host: str,
    port: int,
    *,
    cores: int,
    memory_mb: int,
    state: str = "online",
    last_heartbeat_utc: str | None = None,
) -> str:
    """Insert a host_grid_nodes record."""
    data = {
        "node_id": node_id,
        "host": host,
        "port": port,
        "cores": cores,
        "memory_mb": memory_mb,
        "state": state,
        "last_heartbeat_utc": last_heartbeat_utc or current_utc_iso(),
    }
    insert_row(conn, "host_grid_nodes", data)
    return node_id


def create_host_job_attempt(
    conn: sqlite3.Connection,
    attempt_id: str,
    job_id: str,
    worker_id: str,
    sequence: int,
    *,
    state: str = "running",
    heartbeat_at_utc: str | None = None,
    checkpoint_json: str | None = None,
    created_at_utc: str | None = None,
    completed_at_utc: str | None = None,
) -> str:
    """Insert a host_job_attempts record."""
    data = {
        "attempt_id": attempt_id,
        "job_id": job_id,
        "worker_id": worker_id,
        "sequence": sequence,
        "state": state,
        "heartbeat_at_utc": heartbeat_at_utc,
        "checkpoint_json": checkpoint_json,
        "created_at_utc": created_at_utc or current_utc_iso(),
        "completed_at_utc": completed_at_utc,
    }
    insert_row(conn, "host_job_attempts", data)
    return attempt_id


def create_host_job_event(
    conn: sqlite3.Connection,
    event_id: str,
    job_id: str,
    to_state: str,
    *,
    attempt_id: str | None = None,
    from_state: str | None = None,
    details_json: str = "{}",
    created_at_utc: str | None = None,
) -> str:
    """Insert a host_job_events record."""
    data = {
        "event_id": event_id,
        "job_id": job_id,
        "attempt_id": attempt_id,
        "from_state": from_state,
        "to_state": to_state,
        "details_json": details_json,
        "created_at_utc": created_at_utc or current_utc_iso(),
    }
    insert_row(conn, "host_job_events", data)
    return event_id


def create_host_lease(
    conn: sqlite3.Connection,
    lease_key: str,
    holder_id: str,
    scope: str,
    *,
    acquired_at_utc: str | None = None,
    expires_at_utc: str | None = None,
    metadata: str = "{}",
) -> str:
    """Insert a host_leases record."""
    now_iso = current_utc_iso()
    data = {
        "lease_key": lease_key,
        "holder_id": holder_id,
        "scope": scope,
        "acquired_at_utc": acquired_at_utc or now_iso,
        "expires_at_utc": expires_at_utc or now_iso,
        "metadata": metadata,
    }
    insert_row(conn, "host_leases", data)
    return lease_key


def create_schema_migration(
    conn: sqlite3.Connection,
    version: int,
    name: str,
    *,
    applied_at_utc: str | None = None,
    checksum: str = "",
) -> int:
    """Insert a schema_migrations record."""
    data = {
        "version": version,
        "name": name,
        "applied_at_utc": applied_at_utc or current_utc_iso(),
        "checksum": checksum,
    }
    res = insert_row(conn, "schema_migrations", data)
    return int(res)
