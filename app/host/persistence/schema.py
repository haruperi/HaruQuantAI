"""Database schema management and migrations for host persistence subsystem.

Description:
    Authoritative manager for SQLite database table creation, schema verification,
    and migration execution across versions. Ensures strict column presence and
    compatibility across host and workspace domains.

Purpose:
    FEAT-HOST-PERSISTENCE: Schema migrations, version assertions, and DDL.

Key Capabilities:
    - FR-HOST-PERSISTENCE-SCHEMA-VERIFICATION: Create and inspect storage schemas.
      Associated: `SchemaManager.initialize()`, `SchemaManager.verify_schema()`,
        `SchemaManager.drop_obsolete_sessions()`, `_migrate_datamgr_tables()`,
        `_migrate_host_jobs()`
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
from typing import TYPE_CHECKING

from app.host.logging import get_logger
from app.host.persistence.engine import _CURRENT_SCHEMA_VERSION
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


def _migrate_datamgr_tables(conn: sqlite3.Connection) -> None:
    """Ensure column compatibility and safe migrations for workspace tables."""
    inst_table_info = conn.execute("PRAGMA table_info(datamgr_instruments);").fetchall()
    inst_cols = {r["name"] for r in inst_table_info}
    if inst_cols:
        for col, col_def in (
            ("min_distance", "REAL NOT NULL DEFAULT 0.0"),
            ("order_size_multiplier", "REAL NOT NULL DEFAULT 1.0"),
            ("order_size_step", "REAL NOT NULL DEFAULT 0.0"),
            ("cot", "TEXT DEFAULT NULL"),
        ):
            if col not in inst_cols:
                conn.execute(
                    f"ALTER TABLE datamgr_instruments ADD COLUMN {col} {col_def};"
                )

    sess_table_info = conn.execute("PRAGMA table_info(datamgr_sessions);").fetchall()
    sess_cols = {r["name"] for r in sess_table_info}
    if sess_cols and "broker_id" not in sess_cols:
        conn.execute(
            "ALTER TABLE datamgr_sessions ADD COLUMN "
            "broker_id INTEGER NOT NULL DEFAULT -1;"
        )

    # Clean up obsolete legacy market data tables that carry incompatible foreign keys
    for table_name in (
        "source_partitions",
        "source_datasets",
        "market_files",
        "market_ingestions",
    ):
        conn.execute(f"DROP TABLE IF EXISTS {table_name};")


def _migrate_host_jobs(conn: sqlite3.Connection) -> None:
    """Ensure host_jobs table exists, migrates schemas, and creates indexes."""
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
    if "group_id" in cols:
        conn.execute(
            """
            CREATE TABLE host_jobs_v2 (
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
            );
            """
        )
        common_cols = [c for c in required_cols if c in cols]
        cols_to_copy = ["job_id", *common_cols]
        cols_str = ", ".join(cols_to_copy)
        conn.execute(
            f"INSERT OR IGNORE INTO host_jobs_v2 ({cols_str}) "  # noqa: S608
            f"SELECT {cols_str} FROM host_jobs;"
        )
        conn.execute("DROP TABLE host_jobs;")
        conn.execute("ALTER TABLE host_jobs_v2 RENAME TO host_jobs;")
        table_info = conn.execute("PRAGMA table_info(host_jobs);").fetchall()
        cols = {r["name"] for r in table_info}

    for col_name, col_def in required_cols.items():
        if col_name not in cols:
            conn.execute(f"ALTER TABLE host_jobs ADD COLUMN {col_name} {col_def};")

    conn.execute("CREATE INDEX IF NOT EXISTS idx_host_jobs_owner ON host_jobs(owner);")
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_host_jobs_status ON host_jobs(status);"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_host_jobs_dedup ON host_jobs(dedup_key);"
    )


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
            _migrate_host_jobs(conn)

            # Datamgr market data control tables
            conn.execute(
                """
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
            )
            _migrate_datamgr_tables(conn)
            conn.execute(
                """
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
            # Ensure columns and backward-compatibility for datamgr_stock_group
            group_table_info = conn.execute(
                "PRAGMA table_info(datamgr_stock_group);"
            ).fetchall()
            group_cols = {r["name"] for r in group_table_info}
            if group_cols and "description" not in group_cols:
                conn.execute(
                    "ALTER TABLE datamgr_stock_group ADD COLUMN "
                    "description TEXT DEFAULT '';"
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
            conn.execute(
                """
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
            )
            # Ensure columns and backward-compatibility for datamgr_broker
            broker_table_info = conn.execute(
                "PRAGMA table_info(datamgr_broker);"
            ).fetchall()
            broker_cols = {r["name"] for r in broker_table_info}
            if broker_cols:
                if "created_at_utc" not in broker_cols:
                    conn.execute(
                        "ALTER TABLE datamgr_broker ADD COLUMN "
                        "created_at_utc TEXT NOT NULL DEFAULT '';"
                    )
                if "updated_at_utc" not in broker_cols:
                    conn.execute(
                        "ALTER TABLE datamgr_broker ADD COLUMN "
                        "updated_at_utc TEXT NOT NULL DEFAULT '';"
                    )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS datamgr_broker_stock (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT NOT NULL,
                    broker_id INTEGER NOT NULL,
                    FOREIGN KEY(broker_id) REFERENCES datamgr_broker(id)
                        ON DELETE CASCADE
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS datamgr_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp_utc TEXT NOT NULL,
                    action TEXT NOT NULL,
                    message TEXT NOT NULL,
                    symbol TEXT,
                    details TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL DEFAULT
                        (strftime('%Y-%m-%d %H:%M:%f', 'now'))
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
        self._db.brokers.ensure_defaults()
        self._db.baskets.ensure_defaults()
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
