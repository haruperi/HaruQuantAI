"""Database schema management and migrations for host persistence subsystem.

Description:
    Authoritative manager for SQLite database table creation, schema verification,
    and migration execution across versions. Sole owner of table/index DDL and
    shape checks across the host and workspace domains.

Purpose:
    FEAT-HOST-PERSISTENCE: Schema migrations, version assertions, and DDL.

Key Capabilities:
    - FR-HOST-PERSISTENCE-SCHEMA-VERIFICATION: Create and inspect storage schemas.
      Associated: `SchemaManager.initialize()`, `SchemaManager.verify_schema()`,
        `SchemaManager.drop_obsolete_sessions()`, `ensure_settings_schema()`,
        `ensure_host_session_schema()`, `validate_settings_schema()`
      Logging: INFO initialization; ERROR incompatible required tables/version.

Python API Usage:
    ```python
    from app.host.persistence.engine import DatabaseManager
    from app.host.persistence.schema import SchemaManager

    db = DatabaseManager(":memory:")
    schema = SchemaManager(db)
    schema.initialize()
    schema.verify_schema()
    ```

CLI Usage:
    No direct CLI for schema management. Diagnostics runs integrity checks:
    ```bash
    uv run python -m app.host.diagnostics --integrity-check
    ```
"""

from __future__ import annotations

import re
import sqlite3
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from app.host.logging import get_logger
from app.host.persistence.errors import (
    CorruptDataError,
    IncompatibleSchemaError,
    RevisionConflictError,
    ValidationError,
)
from app.host.persistence.models import MigrationRecord

if TYPE_CHECKING:
    from app.host.persistence.engine import DatabaseManager

logger = get_logger(__name__)

CURRENT_SCHEMA_VERSION: int = 1
INITIAL_MIGRATION_NAME: str = "initial_host_control_tables"
V1_CANONICAL_CHECKSUM: str = "v1_canonical_hash"

CORE_REQUIRED_TABLES: frozenset[str] = frozenset(
    {
        "schema_migrations",
        "host_entities",
        "host_leases",
        "host_settings",
        "host_jobs",
        "datamgr_instruments",
        "datamgr_sessions",
        "datamgr_datasets",
        "datamgr_stock_group",
        "datamgr_stock",
        "datamgr_broker",
        "datamgr_broker_stock",
        "datamgr_logs",
    }
)

SCHEMA_MIGRATIONS_DDL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    applied_at_utc TEXT NOT NULL,
    checksum TEXT NOT NULL
);
"""

HOST_ENTITIES_DDL = """
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
CREATE INDEX IF NOT EXISTS idx_host_entities_scope
ON host_entities (scope, entity_type);
"""

HOST_LEASES_DDL = """
CREATE TABLE IF NOT EXISTS host_leases (
    lease_key TEXT PRIMARY KEY,
    holder_id TEXT NOT NULL,
    scope TEXT NOT NULL,
    acquired_at_utc TEXT NOT NULL,
    expires_at_utc TEXT NOT NULL,
    metadata TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_host_leases_expiry
ON host_leases (expires_at_utc);
"""

HOST_SETTINGS_DDL = """
CREATE TABLE IF NOT EXISTS host_settings (
    scope TEXT NOT NULL,
    key TEXT NOT NULL,
    value_json TEXT NOT NULL,
    schema_version INTEGER NOT NULL DEFAULT 1,
    updated_at_utc TEXT NOT NULL,
    PRIMARY KEY (scope, key)
);
"""

HOST_JOBS_DDL = """
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
CREATE INDEX IF NOT EXISTS idx_host_jobs_owner ON host_jobs(owner);
CREATE INDEX IF NOT EXISTS idx_host_jobs_status ON host_jobs(status);
CREATE INDEX IF NOT EXISTS idx_host_jobs_dedup ON host_jobs(dedup_key);
"""

DATAMGR_INSTRUMENTS_DDL = """
CREATE TABLE IF NOT EXISTS datamgr_instruments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL UNIQUE,
    connection TEXT DEFAULT '',
    broker_id INTEGER DEFAULT -1,
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
    min_distance REAL NOT NULL DEFAULT 0.0,
    order_size_multiplier REAL NOT NULL DEFAULT 1.0,
    order_size_step REAL NOT NULL DEFAULT 0.0,
    cot TEXT DEFAULT NULL,
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL
);
"""

DATAMGR_SESSIONS_DDL = """
CREATE TABLE IF NOT EXISTS datamgr_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    broker_id INTEGER NOT NULL DEFAULT -1,
    description TEXT DEFAULT '',
    timezone TEXT NOT NULL DEFAULT 'UTC',
    windows_json TEXT NOT NULL DEFAULT '[]',
    holidays_json TEXT NOT NULL DEFAULT '[]',
    is_default INTEGER NOT NULL DEFAULT 0
);
"""

DATAMGR_DATASETS_DDL = """
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

DATAMGR_STOCK_GROUP_DDL = """
CREATE TABLE IF NOT EXISTS datamgr_stock_group (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    system INTEGER NOT NULL DEFAULT 0,
    description TEXT DEFAULT ''
);
"""

DATAMGR_STOCK_DDL = """
CREATE TABLE IF NOT EXISTS datamgr_stock (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    basket_id INTEGER NOT NULL,
    date_from TEXT NOT NULL,
    date_to TEXT,
    FOREIGN KEY(basket_id) REFERENCES datamgr_stock_group(id)
);
"""

DATAMGR_BROKER_DDL = """
CREATE TABLE IF NOT EXISTS datamgr_broker (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    is_system INTEGER NOT NULL DEFAULT 0,
    description TEXT DEFAULT '',
    server_timezone TEXT DEFAULT 'UTC',
    postfix TEXT DEFAULT '',
    enabled INTEGER NOT NULL DEFAULT 1,
    mt_use INTEGER NOT NULL DEFAULT 0,
    stockpicker_use INTEGER NOT NULL DEFAULT 0,
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL
);
"""

DATAMGR_BROKER_STOCK_DDL = """
CREATE TABLE IF NOT EXISTS datamgr_broker_stock (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    broker_id INTEGER NOT NULL,
    FOREIGN KEY(broker_id) REFERENCES datamgr_broker(id) ON DELETE CASCADE
);
"""

DATAMGR_LOGS_DDL = """
CREATE TABLE IF NOT EXISTS datamgr_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp_utc TEXT NOT NULL,
    action TEXT NOT NULL,
    message TEXT NOT NULL,
    symbol TEXT,
    details TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now'))
);
"""

HOST_SESSION_DDL = """
CREATE TABLE IF NOT EXISTS host_session (
    session_id TEXT PRIMARY KEY,
    token_hash TEXT NOT NULL UNIQUE,
    username TEXT NOT NULL,
    peer_id TEXT NOT NULL,
    created_at_utc TEXT NOT NULL,
    expires_at_utc TEXT NOT NULL,
    revoked_at_utc TEXT,
    status TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_host_session_status ON host_session(status);
CREATE INDEX IF NOT EXISTS idx_host_session_peer_id ON host_session(peer_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_host_session_token_hash
    ON host_session(token_hash);
"""


def validate_settings_schema(conn: sqlite3.Connection) -> None:
    """Validate host_settings table structure and constraints without mutation."""
    info_rows = conn.execute("PRAGMA table_info(host_settings);").fetchall()
    if not info_rows:
        raise IncompatibleSchemaError("Missing required table: host_settings")

    cols: dict[str, Any] = {str(r["name"]).lower(): r for r in info_rows}
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
                f"Missing required column in host_settings: {col_name}"
            )
        col = cols[col_name]
        if str(col["type"]).upper() != expected_type:
            raise IncompatibleSchemaError(
                f"Column {col_name} has invalid type: expected {expected_type}, "
                f"got {col['type']}"
            )
        if col["notnull"] != notnull:
            raise IncompatibleSchemaError(
                f"Column {col_name} NOT NULL constraint mismatch: "
                f"expected {notnull}, got {col['notnull']}"
            )
        if col["pk"] != pk:
            raise IncompatibleSchemaError(
                f"Column {col_name} PK position mismatch: "
                f"expected {pk}, got {col['pk']}"
            )


def ensure_settings_schema(conn: sqlite3.Connection) -> None:
    """Ensure host_settings table exists and is structurally compatible."""
    table_row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'host_settings';"
    ).fetchone()
    if table_row is None:
        conn.execute(HOST_SETTINGS_DDL)
        return

    validate_settings_schema(conn)


def ensure_host_session_schema(conn: sqlite3.Connection) -> None:
    """Ensure host_session table and indexes exist and are compatible."""
    table_row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'host_session';"
    ).fetchone()
    if table_row is None:
        conn.executescript(HOST_SESSION_DDL)
        return

    columns = conn.execute("PRAGMA table_info(host_session);").fetchall()
    shape = [
        (str(r["name"]).lower(), str(r["type"]).upper(), r["notnull"], r["pk"])
        for r in columns
    ]
    expected_shape = [
        ("session_id", "TEXT", 0, 1),
        ("token_hash", "TEXT", 1, 0),
        ("username", "TEXT", 1, 0),
        ("peer_id", "TEXT", 1, 0),
        ("created_at_utc", "TEXT", 1, 0),
        ("expires_at_utc", "TEXT", 1, 0),
        ("revoked_at_utc", "TEXT", 0, 0),
        ("status", "TEXT", 1, 0),
    ]
    if shape != expected_shape:
        raise IncompatibleSchemaError("Host session schema differs")

    idx_rows = conn.execute("PRAGMA index_list(host_session);").fetchall()
    has_non_partial_token_unique = False
    for idx in idx_rows:
        idx_dict = dict(idx)
        idx_name = str(idx_dict["name"])
        is_unique = bool(idx_dict.get("unique", 0))
        is_partial = bool(idx_dict.get("partial", 0))

        idx_info = conn.execute(f"PRAGMA index_info({idx_name});").fetchall()
        col_names = [str(r["name"]).lower() for r in idx_info]

        if idx_name == "idx_host_session_token_hash" and is_partial:
            raise IncompatibleSchemaError(
                f"Incompatible index {idx_name}: "
                "partial unique index on token_hash is not permitted"
            )

        if is_unique and not is_partial and col_names == ["token_hash"]:
            has_non_partial_token_unique = True

    if not has_non_partial_token_unique:
        raise IncompatibleSchemaError(
            "Host session missing non-partial unique index on token_hash"
        )

    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_host_session_status ON host_session(status);"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_host_session_peer_id ON host_session(peer_id);"
    )
    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_host_session_token_hash "
        "ON host_session(token_hash);"
    )


def _check_unique_targets(
    conn: sqlite3.Connection,
    table_name: str,
    actual_pk: tuple[str, ...],
    unique_targets: tuple[tuple[str, ...], ...],
) -> None:
    idx_rows = conn.execute(f"PRAGMA index_list({table_name});").fetchall()
    table_unique_targets: set[tuple[str, ...]] = set()

    if actual_pk:
        table_unique_targets.add(actual_pk)

    for idx in idx_rows:
        idx_dict = dict(idx)
        if bool(idx_dict.get("unique", 0)) and not bool(idx_dict.get("partial", 0)):
            info_rows = conn.execute(
                f"PRAGMA index_info({idx_dict['name']});"
            ).fetchall()
            target_cols = tuple(str(r["name"]).lower() for r in info_rows)
            if target_cols:
                table_unique_targets.add(target_cols)

    for target in unique_targets:
        target_lower = tuple(c.lower() for c in target)
        if target_lower not in table_unique_targets:
            raise IncompatibleSchemaError(
                f"Table {table_name} missing non-partial UNIQUE constraint "
                f"or index on {target}"
            )


def _check_foreign_keys(
    conn: sqlite3.Connection,
    table_name: str,
    foreign_keys: tuple[tuple[str, str, str], ...],
) -> None:
    fks = conn.execute(f"PRAGMA foreign_key_list({table_name});").fetchall()
    actual_fks = {
        (
            str(r["from"]).lower(),
            str(r["table"]).lower(),
            str(r["to"]).lower() if r["to"] else "id",
        )
        for r in fks
    }
    for from_col, ref_table, ref_col in foreign_keys:
        expected = (from_col.lower(), ref_table.lower(), ref_col.lower())
        if expected not in actual_fks:
            raise IncompatibleSchemaError(
                f"Table {table_name} missing foreign key {from_col} -> "
                f"{ref_table}({ref_col})"
            )


def _get_column_affinity(col_type: str) -> str:
    upper = col_type.upper()
    if "INT" in upper or "LONG" in upper or "BOOLEAN" in upper:
        return "INTEGER"
    if "CHAR" in upper or "CLOB" in upper or "TEXT" in upper:
        return "TEXT"
    if "BLOB" in upper:
        return "BLOB"
    if "REAL" in upper or "FLOA" in upper or "DOUB" in upper:
        return "REAL"
    return "NUMERIC"


def _check_column_specs(
    table_name: str,
    cols: dict[str, Any],
    column_specs: dict[str, dict[str, Any]],
) -> None:
    for col_name, spec in column_specs.items():
        col_lower = col_name.lower()
        if col_lower not in cols:
            raise IncompatibleSchemaError(
                f"Missing required column in {table_name}: {col_name}"
            )
        col_row = cols[col_lower]
        col_type = str(col_row["type"]).upper()

        if "affinity" in spec:
            allowed_affinities = spec["affinity"]
            affinity = _get_column_affinity(col_type)
            if affinity not in allowed_affinities:
                raise IncompatibleSchemaError(
                    f"Column {table_name}.{col_name} type '{col_type}' has affinity "
                    f"'{affinity}', expected one of {allowed_affinities}"
                )

        if (
            spec.get("notnull") is True
            and col_row["notnull"] == 0
            and col_row["pk"] == 0
        ):
            raise IncompatibleSchemaError(
                f"Column {table_name}.{col_name} must be NOT NULL"
            )


def _check_columns(
    conn: sqlite3.Connection,
    table_name: str,
    required_cols: tuple[str, ...],
    *,
    exact_pk: tuple[str, ...] | None = None,
    unique_targets: tuple[tuple[str, ...], ...] | None = None,
    foreign_keys: tuple[tuple[str, str, str], ...] | None = None,
    column_specs: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    rows = conn.execute(f"PRAGMA table_info({table_name});").fetchall()
    cols = {str(r["name"]).lower(): r for r in rows}
    for col in required_cols:
        col_lower = col.lower()
        if col_lower not in cols:
            raise IncompatibleSchemaError(
                f"Missing required column in {table_name}: {col}"
            )

    actual_pk = tuple(
        str(r["name"]).lower()
        for r in sorted([r for r in rows if r["pk"] > 0], key=lambda r: r["pk"])
    )

    if exact_pk is not None and actual_pk != tuple(c.lower() for c in exact_pk):
        raise IncompatibleSchemaError(
            f"Table {table_name} primary key mismatch: "
            f"expected {exact_pk}, got {actual_pk}"
        )

    if unique_targets is not None:
        _check_unique_targets(conn, table_name, actual_pk, unique_targets)

    if foreign_keys is not None:
        _check_foreign_keys(conn, table_name, foreign_keys)

    if column_specs is not None:
        _check_column_specs(table_name, cols, column_specs)

    return cols


def _verify_host_shapes(conn: sqlite3.Connection) -> None:
    validate_settings_schema(conn)

    jobs_cols = _check_columns(
        conn,
        "host_jobs",
        (
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
        ),
        exact_pk=("job_id",),
        column_specs={
            "owner": {"affinity": ("TEXT",), "notnull": True},
            "kind": {"affinity": ("TEXT",), "notnull": True},
            "status": {"affinity": ("TEXT",), "notnull": True},
            "progress": {"affinity": ("REAL", "NUMERIC"), "notnull": True},
            "child_job_ids_json": {"affinity": ("TEXT",), "notnull": True},
            "budget_json": {"affinity": ("TEXT",), "notnull": True},
        },
    )
    if "group_id" in jobs_cols:
        raise IncompatibleSchemaError(
            "Legacy host_jobs schema with group_id requires manual migration"
        )

    _check_columns(
        conn,
        "host_entities",
        (
            "entity_id",
            "entity_type",
            "scope",
            "payload",
            "revision",
            "created_at_utc",
            "updated_at_utc",
        ),
        exact_pk=("entity_id", "entity_type"),
        column_specs={
            "payload": {"affinity": ("TEXT",), "notnull": True},
            "revision": {"affinity": ("INTEGER",), "notnull": True},
        },
    )

    _check_columns(
        conn,
        "host_leases",
        (
            "lease_key",
            "holder_id",
            "scope",
            "acquired_at_utc",
            "expires_at_utc",
            "metadata",
        ),
        exact_pk=("lease_key",),
        column_specs={
            "holder_id": {"affinity": ("TEXT",), "notnull": True},
            "scope": {"affinity": ("TEXT",), "notnull": True},
            "metadata": {"affinity": ("TEXT",), "notnull": True},
        },
    )


def _verify_datamgr_shapes(conn: sqlite3.Connection) -> None:
    _check_columns(
        conn,
        "datamgr_datasets",
        (
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
        ),
        exact_pk=("id",),
        column_specs={
            "bars": {"affinity": ("INTEGER",), "notnull": True},
            "source": {"affinity": ("TEXT",), "notnull": True},
            "symbol": {"affinity": ("TEXT",), "notnull": True},
            "path": {"affinity": ("TEXT",), "notnull": True},
            "schema_version": {"affinity": ("INTEGER",), "notnull": True},
        },
    )
    _check_columns(
        conn,
        "datamgr_instruments",
        (
            "id",
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
            "min_distance",
            "order_size_multiplier",
            "order_size_step",
            "cot",
            "created_at_utc",
            "updated_at_utc",
        ),
        exact_pk=("id",),
        unique_targets=(("symbol",),),
        column_specs={
            "symbol": {"affinity": ("TEXT",), "notnull": True},
            "tick_size": {"affinity": ("REAL", "NUMERIC"), "notnull": True},
            "decimals": {"affinity": ("INTEGER",), "notnull": True},
        },
    )
    sg_cols = _check_columns(
        conn,
        "datamgr_stock_group",
        ("id", "name", "system"),
        exact_pk=("id",),
        unique_targets=(("name",),),
        column_specs={
            "name": {"affinity": ("TEXT",), "notnull": True},
            "system": {"affinity": ("INTEGER",), "notnull": True},
        },
    )
    if "description" not in sg_cols and "desc" not in sg_cols:
        raise IncompatibleSchemaError(
            "Missing description column in datamgr_stock_group"
        )
    _check_columns(
        conn,
        "datamgr_stock",
        ("id", "ticker", "basket_id", "date_from", "date_to"),
        exact_pk=("id",),
        foreign_keys=(("basket_id", "datamgr_stock_group", "id"),),
        column_specs={
            "basket_id": {"affinity": ("INTEGER",), "notnull": True},
            "ticker": {"affinity": ("TEXT",), "notnull": True},
            "date_from": {"affinity": ("INTEGER", "TEXT", "NUMERIC"), "notnull": True},
        },
    )
    _check_columns(
        conn,
        "datamgr_broker",
        (
            "id",
            "name",
            "is_system",
            "description",
            "server_timezone",
            "postfix",
            "enabled",
            "mt_use",
            "stockpicker_use",
            "created_at_utc",
            "updated_at_utc",
        ),
        exact_pk=("id",),
        unique_targets=(("name",),),
        column_specs={
            "name": {"affinity": ("TEXT",), "notnull": True},
            "is_system": {"affinity": ("INTEGER",), "notnull": True},
        },
    )
    _check_columns(
        conn,
        "datamgr_broker_stock",
        ("id", "ticker", "broker_id"),
        exact_pk=("id",),
        foreign_keys=(("broker_id", "datamgr_broker", "id"),),
        column_specs={
            "broker_id": {"affinity": ("INTEGER",), "notnull": True},
            "ticker": {"affinity": ("TEXT",), "notnull": True},
        },
    )
    _check_columns(
        conn,
        "datamgr_sessions",
        (
            "id",
            "name",
            "broker_id",
            "description",
            "timezone",
            "windows_json",
            "holidays_json",
            "is_default",
        ),
        exact_pk=("id",),
        unique_targets=(("name",),),
        column_specs={
            "name": {"affinity": ("TEXT",), "notnull": True},
            "timezone": {"affinity": ("TEXT",), "notnull": True},
            "windows_json": {"affinity": ("TEXT",), "notnull": True},
            "holidays_json": {"affinity": ("TEXT",), "notnull": True},
            "is_default": {"affinity": ("INTEGER",), "notnull": True},
        },
    )
    _check_columns(
        conn,
        "datamgr_logs",
        (
            "id",
            "timestamp_utc",
            "action",
            "message",
            "symbol",
            "details",
            "created_at",
        ),
        exact_pk=("id",),
    )
    _check_columns(
        conn,
        "schema_migrations",
        ("version", "name", "applied_at_utc", "checksum"),
        exact_pk=("version",),
    )


def _verify_core_shapes(conn: sqlite3.Connection) -> None:
    """Verify column definitions and constraints for core tables."""
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    existing_tables = {row[0] for row in cur.fetchall()}

    missing = CORE_REQUIRED_TABLES - existing_tables
    if missing:
        raise IncompatibleSchemaError(
            f"Incompatible database schema: missing required tables {sorted(missing)}"
        )

    _verify_host_shapes(conn)
    _verify_datamgr_shapes(conn)


def _create_fresh_core_tables(
    conn: sqlite3.Connection, existing_tables: set[str]
) -> None:
    """Execute canonical DDL for all core tables in a single transaction."""
    conn.execute(SCHEMA_MIGRATIONS_DDL)
    conn.executescript(HOST_ENTITIES_DDL)
    conn.executescript(HOST_LEASES_DDL)
    if "host_settings" not in existing_tables:
        conn.execute(HOST_SETTINGS_DDL)
    conn.executescript(HOST_JOBS_DDL)
    conn.execute(DATAMGR_INSTRUMENTS_DDL)
    conn.execute(DATAMGR_SESSIONS_DDL)
    conn.execute(DATAMGR_DATASETS_DDL)
    conn.execute(DATAMGR_STOCK_GROUP_DDL)
    conn.execute(DATAMGR_STOCK_DDL)
    conn.execute(DATAMGR_BROKER_DDL)
    conn.execute(DATAMGR_BROKER_STOCK_DDL)
    conn.execute(DATAMGR_LOGS_DDL)


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
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
            existing_tables = {row[0] for row in cur.fetchall()}

            # Case A: Ledger exists -> inspect and verify without mutating schema
            if "schema_migrations" in existing_tables:
                cur.execute("SELECT MAX(version) FROM schema_migrations;")
                row = cur.fetchone()
                current_ver = row[0] if row and row[0] is not None else 0
                if current_ver > CURRENT_SCHEMA_VERSION:
                    msg = (
                        f"Unsupported future database schema version {current_ver}; "
                        f"maximum supported version is {CURRENT_SCHEMA_VERSION}"
                    )
                    logger.error(
                        msg,
                        extra={"fr_id": "FR-HOST-PERSISTENCE-SCHEMA-VERIFICATION"},
                    )
                    raise IncompatibleSchemaError(msg)
                if current_ver < CURRENT_SCHEMA_VERSION:
                    msg = (
                        f"Outdated database schema version {current_ver}; "
                        f"expected at least {CURRENT_SCHEMA_VERSION}"
                    )
                    logger.error(
                        msg,
                        extra={"fr_id": "FR-HOST-PERSISTENCE-SCHEMA-VERIFICATION"},
                    )
                    raise IncompatibleSchemaError(msg)

                # Verify all core tables and their operational shapes
                _verify_core_shapes(conn)
                logger.info(
                    "Host database schema verified (existing version %d)",
                    current_ver,
                    extra={
                        "version": current_ver,
                        "fr_id": "FR-HOST-PERSISTENCE-SCHEMA-VERIFICATION",
                    },
                )
            else:
                # Case B: Ledger does NOT exist
                # Check if any owned core tables exist without a ledger
                owned_core_tables = CORE_REQUIRED_TABLES - {
                    "schema_migrations",
                    "host_settings",
                }
                overlap = owned_core_tables & existing_tables
                if overlap:
                    msg = (
                        f"Existing database contains core tables {sorted(overlap)} "
                        "without schema_migrations ledger; manual migration required"
                    )
                    logger.error(
                        msg,
                        extra={"fr_id": "FR-HOST-PERSISTENCE-SCHEMA-VERIFICATION"},
                    )
                    raise IncompatibleSchemaError(msg)

                # If host_settings exists standalone, verify it before creating rest
                if "host_settings" in existing_tables:
                    validate_settings_schema(conn)

                # If host_session exists standalone, verify it
                if "host_session" in existing_tables:
                    ensure_host_session_schema(conn)

                # Fresh core creation: execute canonical DDL in this transaction
                _create_fresh_core_tables(conn, existing_tables)

                # Validate the complete created/adopted core schema BEFORE inserting
                # migration 1 and committing!
                _verify_core_shapes(conn)

                # Record initial migration 1
                now_str = datetime.now(UTC).isoformat()
                conn.execute(
                    """
                    INSERT INTO schema_migrations (
                        version, name, applied_at_utc, checksum
                    ) VALUES (?, ?, ?, ?);
                    """,
                    (
                        CURRENT_SCHEMA_VERSION,
                        INITIAL_MIGRATION_NAME,
                        now_str,
                        V1_CANONICAL_CHECKSUM,
                    ),
                )
                logger.info(
                    "Host database schema initialized",
                    extra={
                        "version": CURRENT_SCHEMA_VERSION,
                        "fr_id": "FR-HOST-PERSISTENCE-SCHEMA-VERIFICATION",
                    },
                )

        self._initialized = True
        logger.info(
            "Host database schema initialized",
            extra={
                "version": CURRENT_SCHEMA_VERSION,
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
        """Verify core tables exist, version is supported, and shapes match.

        Returns:
            True if schema is valid.

        Raises:
            IncompatibleSchemaError: If required tables are missing or schema
                is corrupt.
        """
        with self._db.connection(query_only=True) as conn:
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
            existing_tables = {row[0] for row in cur.fetchall()}

            missing = CORE_REQUIRED_TABLES - existing_tables
            if missing:
                msg = (
                    f"Incompatible database schema: missing required tables "
                    f"{sorted(missing)}"
                )
                logger.error(
                    msg,
                    extra={"fr_id": "FR-HOST-PERSISTENCE-SCHEMA-VERIFICATION"},
                )
                raise IncompatibleSchemaError(msg)

            cur.execute("SELECT MAX(version) FROM schema_migrations;")
            row = cur.fetchone()
            current_ver = row[0] if row and row[0] is not None else 0
            if current_ver < CURRENT_SCHEMA_VERSION:
                msg = (
                    f"Outdated database schema version {current_ver}; "
                    f"expected at least {CURRENT_SCHEMA_VERSION}"
                )
                logger.error(
                    msg,
                    extra={"fr_id": "FR-HOST-PERSISTENCE-SCHEMA-VERIFICATION"},
                )
                raise IncompatibleSchemaError(msg)
            if current_ver > CURRENT_SCHEMA_VERSION:
                msg = (
                    f"Unsupported future database schema version {current_ver}; "
                    f"maximum supported version is {CURRENT_SCHEMA_VERSION}"
                )
                logger.error(
                    msg,
                    extra={"fr_id": "FR-HOST-PERSISTENCE-SCHEMA-VERIFICATION"},
                )
                raise IncompatibleSchemaError(msg)

            _verify_core_shapes(conn)

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
