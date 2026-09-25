"""CRUD operations for the host-owned tables of the unified SQLite database.

This module is the single home for every read and write against the
``host_*`` tables in ``data/database/haruquantai.db``. It owns no product,
plugin, scheduling, or presentation logic: callers compose these typed
primitives. Timestamps are UTC ISO-8601 strings and JSON documents are
validated and canonically re-encoded before storage. The module uses only
the Python standard library and performs no I/O at import time.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Generator
from contextlib import closing, contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, NoReturn

DEFAULT_DATABASE_PATH = Path("data") / "database" / "haruquantai.db"
ACTIVE_LEASE_STATE = "active"
EXPIRED_LEASE_STATE = "expired"

_CONNECT_TIMEOUT_S = 5.0
_BUSY_TIMEOUT_MS = 5000
_MIN_PROGRESS_PERCENT = 0.0
_MAX_PROGRESS_PERCENT = 100.0


class HostPersistenceError(Exception):
    """A host persistence operation failed."""


class HostPersistenceConflictError(HostPersistenceError):
    """A uniqueness, foreign-key, or compare-and-set expectation failed."""


class HostPersistenceSchemaError(HostPersistenceError):
    """The database is missing a host table or has a drifted shape."""


class HostPersistenceValueError(HostPersistenceError):
    """A caller supplied a malformed JSON document or out-of-range value."""


@dataclass(frozen=True, slots=True)
class HostSettingRecord:
    """One row of ``host_settings`` keyed by ``(scope, key)``."""

    scope: str
    key: str
    value_json: str
    schema_version: int
    updated_at_utc: str


@dataclass(frozen=True, slots=True)
class HostJobRecord:
    """One row of the durable ``host_jobs`` queue."""

    job_id: str
    group_id: str
    operation: str
    state: str
    priority: int = 0
    resource_class: str = ""
    config_hash: str = ""
    payload_json: str = "{}"
    progress_percent: float = 0.0
    progress_message: str = ""
    checkpoint_json: str | None = None
    created_at_utc: str = ""
    started_at_utc: str | None = None
    completed_at_utc: str | None = None
    terminal_reason: str | None = None


@dataclass(frozen=True, slots=True)
class HostJobAttemptRecord:
    """One execution attempt of a job in ``host_job_attempts``."""

    attempt_id: str
    job_id: str
    worker_id: str
    sequence: int
    state: str
    heartbeat_at_utc: str | None = None
    checkpoint_json: str | None = None
    created_at_utc: str = ""
    completed_at_utc: str | None = None


@dataclass(frozen=True, slots=True)
class HostJobEventRecord:
    """One append-only state transition event in ``host_job_events``."""

    event_id: str
    job_id: str
    to_state: str
    details_json: str
    created_at_utc: str
    attempt_id: str | None = None
    from_state: str | None = None


@dataclass(frozen=True, slots=True)
class HostGridNodeRecord:
    """One compute node registration in ``host_grid_nodes``."""

    node_id: str
    host: str
    port: int
    cores: int
    memory_mb: int
    state: str
    last_heartbeat_utc: str


@dataclass(frozen=True, slots=True)
class HostGridLeaseRecord:
    """One grid lease binding a job to a node in ``host_grid_leases``."""

    lease_id: str
    node_id: str
    job_id: str
    leased_at_utc: str
    expires_at_utc: str
    state: str


_SCHEMA_STATEMENTS: tuple[str, ...] = (
    """
    CREATE TABLE IF NOT EXISTS "host_settings" (
        scope TEXT NOT NULL,
        key TEXT NOT NULL,
        value_json TEXT NOT NULL,
        schema_version INTEGER NOT NULL DEFAULT 1,
        updated_at_utc TEXT NOT NULL,
        PRIMARY KEY (scope, key)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS "host_jobs" (
        job_id TEXT PRIMARY KEY,
        group_id TEXT NOT NULL,
        operation TEXT NOT NULL,
        state TEXT NOT NULL,
        priority INTEGER NOT NULL DEFAULT 0,
        resource_class TEXT NOT NULL,
        config_hash TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        progress_percent REAL NOT NULL DEFAULT 0.0,
        progress_message TEXT NOT NULL DEFAULT '',
        checkpoint_json TEXT,
        created_at_utc TEXT NOT NULL,
        started_at_utc TEXT,
        completed_at_utc TEXT,
        terminal_reason TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS "host_job_attempts" (
        attempt_id TEXT PRIMARY KEY,
        job_id TEXT NOT NULL REFERENCES "host_jobs"(job_id),
        worker_id TEXT NOT NULL,
        sequence INTEGER NOT NULL,
        state TEXT NOT NULL,
        heartbeat_at_utc TEXT,
        checkpoint_json TEXT,
        created_at_utc TEXT NOT NULL,
        completed_at_utc TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS "host_job_events" (
        event_id TEXT PRIMARY KEY,
        job_id TEXT NOT NULL,
        attempt_id TEXT,
        from_state TEXT,
        to_state TEXT NOT NULL,
        details_json TEXT NOT NULL,
        created_at_utc TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS "host_grid_nodes" (
        node_id TEXT PRIMARY KEY,
        host TEXT NOT NULL,
        port INTEGER NOT NULL,
        cores INTEGER NOT NULL,
        memory_mb INTEGER NOT NULL,
        state TEXT NOT NULL,
        last_heartbeat_utc TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS "host_grid_leases" (
        lease_id TEXT PRIMARY KEY,
        node_id TEXT NOT NULL REFERENCES "host_grid_nodes"(node_id),
        job_id TEXT NOT NULL REFERENCES "host_jobs"(job_id),
        leased_at_utc TEXT NOT NULL,
        expires_at_utc TEXT NOT NULL,
        state TEXT NOT NULL
    )
    """,
    'CREATE INDEX IF NOT EXISTS idx_workspace_jobs_state ON "host_jobs"(state)',
    'CREATE INDEX IF NOT EXISTS idx_workspace_jobs_group ON "host_jobs"(group_id)',
    (
        "CREATE INDEX IF NOT EXISTS idx_workspace_attempts_job "
        'ON "host_job_attempts"(job_id)'
    ),
    'CREATE INDEX IF NOT EXISTS idx_workspace_events_job ON "host_job_events"(job_id)',
    (
        "CREATE INDEX IF NOT EXISTS idx_workspace_leases_node "
        'ON "host_grid_leases"(node_id)'
    ),
    'CREATE INDEX IF NOT EXISTS idx_workspace_leases_job ON "host_grid_leases"(job_id)',
)

# (column name, declared type, NOT NULL flag, primary-key position) per table,
# captured from the live database schema on 2026-09-25.
_EXPECTED_COLUMNS: dict[str, tuple[tuple[str, str, int, int], ...]] = {
    "host_settings": (
        ("scope", "TEXT", 1, 1),
        ("key", "TEXT", 1, 2),
        ("value_json", "TEXT", 1, 0),
        ("schema_version", "INTEGER", 1, 0),
        ("updated_at_utc", "TEXT", 1, 0),
    ),
    "host_jobs": (
        ("job_id", "TEXT", 0, 1),
        ("group_id", "TEXT", 1, 0),
        ("operation", "TEXT", 1, 0),
        ("state", "TEXT", 1, 0),
        ("priority", "INTEGER", 1, 0),
        ("resource_class", "TEXT", 1, 0),
        ("config_hash", "TEXT", 1, 0),
        ("payload_json", "TEXT", 1, 0),
        ("progress_percent", "REAL", 1, 0),
        ("progress_message", "TEXT", 1, 0),
        ("checkpoint_json", "TEXT", 0, 0),
        ("created_at_utc", "TEXT", 1, 0),
        ("started_at_utc", "TEXT", 0, 0),
        ("completed_at_utc", "TEXT", 0, 0),
        ("terminal_reason", "TEXT", 0, 0),
    ),
    "host_job_attempts": (
        ("attempt_id", "TEXT", 0, 1),
        ("job_id", "TEXT", 1, 0),
        ("worker_id", "TEXT", 1, 0),
        ("sequence", "INTEGER", 1, 0),
        ("state", "TEXT", 1, 0),
        ("heartbeat_at_utc", "TEXT", 0, 0),
        ("checkpoint_json", "TEXT", 0, 0),
        ("created_at_utc", "TEXT", 1, 0),
        ("completed_at_utc", "TEXT", 0, 0),
    ),
    "host_job_events": (
        ("event_id", "TEXT", 0, 1),
        ("job_id", "TEXT", 1, 0),
        ("attempt_id", "TEXT", 0, 0),
        ("from_state", "TEXT", 0, 0),
        ("to_state", "TEXT", 1, 0),
        ("details_json", "TEXT", 1, 0),
        ("created_at_utc", "TEXT", 1, 0),
    ),
    "host_grid_nodes": (
        ("node_id", "TEXT", 0, 1),
        ("host", "TEXT", 1, 0),
        ("port", "INTEGER", 1, 0),
        ("cores", "INTEGER", 1, 0),
        ("memory_mb", "INTEGER", 1, 0),
        ("state", "TEXT", 1, 0),
        ("last_heartbeat_utc", "TEXT", 1, 0),
    ),
    "host_grid_leases": (
        ("lease_id", "TEXT", 0, 1),
        ("node_id", "TEXT", 1, 0),
        ("job_id", "TEXT", 1, 0),
        ("leased_at_utc", "TEXT", 1, 0),
        ("expires_at_utc", "TEXT", 1, 0),
        ("state", "TEXT", 1, 0),
    ),
}


def utc_now_iso() -> str:
    """Return the current UTC time in the stored ISO-8601 convention."""
    return datetime.now(tz=UTC).isoformat()


def _reject_constant(value: str) -> None:
    raise ValueError(f"Non-finite JSON constant {value}")


def _validated_json(text: str, *, require_object: bool = False) -> str:
    """Validate a JSON document and return it canonically re-encoded."""
    try:
        document: object = json.loads(text, parse_constant=_reject_constant)
    except (TypeError, ValueError) as error:
        raise HostPersistenceValueError("Malformed JSON document") from error
    if require_object and not isinstance(document, dict):
        raise HostPersistenceValueError("JSON document must be an object")
    return json.dumps(document, allow_nan=False, sort_keys=True)


def _validated_progress(percent: float) -> float:
    """Require a job progress percentage within the inclusive 0-100 range."""
    if not _MIN_PROGRESS_PERCENT <= percent <= _MAX_PROGRESS_PERCENT:
        raise HostPersistenceValueError("Progress percent must be within 0 and 100")
    return percent


@contextmanager
def _connect(path: Path) -> Generator[sqlite3.Connection]:
    """Open a short-lived autocommit connection with host pragmas applied."""
    connection = sqlite3.connect(path, timeout=_CONNECT_TIMEOUT_S, isolation_level=None)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(f"PRAGMA busy_timeout = {_BUSY_TIMEOUT_MS}")
        yield connection
    finally:
        connection.close()


@contextmanager
def _write_transaction(connection: sqlite3.Connection) -> Generator[None]:
    """Run a write inside BEGIN IMMEDIATE with rollback on any failure."""
    connection.execute("BEGIN IMMEDIATE")
    try:
        yield
    except BaseException:
        connection.execute("ROLLBACK")
        raise
    connection.execute("COMMIT")


def ensure_schema(path: Path) -> None:
    """Create the ratified host tables and indexes when they are absent.

    The statements are idempotent and never drop, alter, or rename anything,
    so this is safe to run against an existing database. Callers remain
    responsible for authorization over the target file.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with _connect(path) as connection, _write_transaction(connection):
        for statement in _SCHEMA_STATEMENTS:
            connection.execute(statement)
    verify_schema(path)


@contextmanager
def _readonly(path: Path) -> Generator[sqlite3.Connection]:
    """Open a short-lived read-only connection, failing closed on errors."""
    if not path.is_file():
        raise HostPersistenceSchemaError("Host database is missing")
    try:
        uri = f"{path.resolve().as_uri()}?mode=ro"
    except OSError, ValueError:
        raise HostPersistenceSchemaError("Cannot locate the host database") from None
    try:
        with closing(
            sqlite3.connect(uri, uri=True, timeout=_CONNECT_TIMEOUT_S)
        ) as connection:
            yield connection
    except sqlite3.Error:
        raise HostPersistenceSchemaError("Cannot inspect the host database") from None


def _verify_table(connection: sqlite3.Connection, table: str) -> None:
    """Fail closed unless one host table exists with the ratified shape."""
    actual = tuple(
        (str(row[1]), str(row[2]), int(row[3]), int(row[5]))
        for row in connection.execute(f"PRAGMA table_info({table})")
    )
    if not actual:
        raise HostPersistenceSchemaError(f"Host table {table} is missing")
    if actual != _EXPECTED_COLUMNS[table]:
        raise HostPersistenceSchemaError(
            f"Host table {table} has an incompatible shape"
        )


def verify_schema(path: Path) -> None:
    """Fail closed unless every host table exists with the ratified shape."""
    with _readonly(path) as connection:
        for table in _EXPECTED_COLUMNS:
            _verify_table(connection, table)


def read_settings(path: Path) -> list[HostSettingRecord]:
    """Read every host_settings record read-only from a compatible table.

    Unlike HostStore, this verifies only the host_settings shape, so boot
    works against databases that predate the other host tables. The file
    is never created or modified.
    """
    with _readonly(path) as connection:
        _verify_table(connection, "host_settings")
        rows = connection.execute(
            "SELECT scope, key, value_json, schema_version, updated_at_utc "
            "FROM host_settings ORDER BY scope, key"
        ).fetchall()
    return [_setting_record(row) for row in rows]


def _raise_for_integrity(error: sqlite3.IntegrityError, *, context: str) -> NoReturn:
    """Translate a constraint failure into a typed conflict error."""
    message = str(error)
    if "UNIQUE constraint failed" in message:
        raise HostPersistenceConflictError(f"{context} already exists") from error
    if "FOREIGN KEY constraint failed" in message:
        raise HostPersistenceConflictError(
            f"{context} references a missing record"
        ) from error
    raise HostPersistenceError(f"{context} violated a database constraint") from error


def _setting_record(row: Any) -> HostSettingRecord:
    """Map a host_settings row selected in canonical column order."""
    return HostSettingRecord(
        scope=row[0],
        key=row[1],
        value_json=row[2],
        schema_version=row[3],
        updated_at_utc=row[4],
    )


def _job_record(row: Any) -> HostJobRecord:
    """Map a host_jobs row selected in canonical column order."""
    return HostJobRecord(
        job_id=row[0],
        group_id=row[1],
        operation=row[2],
        state=row[3],
        priority=row[4],
        resource_class=row[5],
        config_hash=row[6],
        payload_json=row[7],
        progress_percent=row[8],
        progress_message=row[9],
        checkpoint_json=row[10],
        created_at_utc=row[11],
        started_at_utc=row[12],
        completed_at_utc=row[13],
        terminal_reason=row[14],
    )


def _attempt_record(row: Any) -> HostJobAttemptRecord:
    """Map a host_job_attempts row selected in canonical column order."""
    return HostJobAttemptRecord(
        attempt_id=row[0],
        job_id=row[1],
        worker_id=row[2],
        sequence=row[3],
        state=row[4],
        heartbeat_at_utc=row[5],
        checkpoint_json=row[6],
        created_at_utc=row[7],
        completed_at_utc=row[8],
    )


def _event_record(row: Any) -> HostJobEventRecord:
    """Map a host_job_events row selected in canonical column order."""
    return HostJobEventRecord(
        event_id=row[0],
        job_id=row[1],
        attempt_id=row[2],
        from_state=row[3],
        to_state=row[4],
        details_json=row[5],
        created_at_utc=row[6],
    )


def _node_record(row: Any) -> HostGridNodeRecord:
    """Map a host_grid_nodes row selected in canonical column order."""
    return HostGridNodeRecord(
        node_id=row[0],
        host=row[1],
        port=row[2],
        cores=row[3],
        memory_mb=row[4],
        state=row[5],
        last_heartbeat_utc=row[6],
    )


def _lease_record(row: Any) -> HostGridLeaseRecord:
    """Map a host_grid_leases row selected in canonical column order."""
    return HostGridLeaseRecord(
        lease_id=row[0],
        node_id=row[1],
        job_id=row[2],
        leased_at_utc=row[3],
        expires_at_utc=row[4],
        state=row[5],
    )


class HostStore:
    """CRUD access to the host-owned tables of the unified database.

    Every method opens a short-lived connection with foreign-key enforcement
    and a bounded busy timeout, so one store instance is safe to share across
    threads. Construction fails closed unless the database already carries
    the ratified host schema.
    """

    def __init__(self, path: Path) -> None:
        """Verify the schema and remember the database location."""
        verify_schema(path)
        self._path = path

    # -- host_settings ----------------------------------------------------

    def get_setting(self, scope: str, key: str) -> HostSettingRecord | None:
        """Return one settings record, or None when the key is absent."""
        with _connect(self._path) as connection:
            row = connection.execute(
                "SELECT scope, key, value_json, schema_version, updated_at_utc "
                "FROM host_settings WHERE scope=? AND key=?",
                (scope, key),
            ).fetchone()
        return None if row is None else _setting_record(row)

    def list_settings(self, *, scope: str | None = None) -> list[HostSettingRecord]:
        """Return settings ordered by (scope, key), optionally filtered."""
        with _connect(self._path) as connection:
            if scope is None:
                rows = connection.execute(
                    "SELECT scope, key, value_json, schema_version, updated_at_utc "
                    "FROM host_settings ORDER BY scope, key"
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT scope, key, value_json, schema_version, updated_at_utc "
                    "FROM host_settings WHERE scope=? ORDER BY scope, key",
                    (scope,),
                ).fetchall()
        return [_setting_record(row) for row in rows]

    def upsert_setting(self, record: HostSettingRecord) -> None:
        """Insert or replace one settings record transactionally.

        The value must be a JSON object; it is canonically re-encoded before
        storage so identical settings always produce identical bytes.
        """
        value_json = _validated_json(record.value_json, require_object=True)
        with _connect(self._path) as connection, _write_transaction(connection):
            connection.execute(
                "INSERT INTO host_settings "
                "(scope, key, value_json, schema_version, updated_at_utc) "
                "VALUES (?, ?, ?, ?, ?) ON CONFLICT(scope, key) DO UPDATE SET "
                "value_json=excluded.value_json, "
                "schema_version=excluded.schema_version, "
                "updated_at_utc=excluded.updated_at_utc",
                (
                    record.scope,
                    record.key,
                    value_json,
                    record.schema_version,
                    record.updated_at_utc,
                ),
            )

    def delete_setting(self, scope: str, key: str) -> bool:
        """Remove one settings record; return False when it is absent."""
        with _connect(self._path) as connection, _write_transaction(connection):
            cursor = connection.execute(
                "DELETE FROM host_settings WHERE scope=? AND key=?", (scope, key)
            )
            return cursor.rowcount > 0

    # -- host_jobs ---------------------------------------------------------

    def insert_job(self, record: HostJobRecord) -> None:
        """Insert one job; duplicates and unknown parents fail closed."""
        payload_json = _validated_json(record.payload_json)
        checkpoint_json = (
            None
            if record.checkpoint_json is None
            else _validated_json(record.checkpoint_json)
        )
        _validated_progress(record.progress_percent)
        with _connect(self._path) as connection, _write_transaction(connection):
            try:
                connection.execute(
                    "INSERT INTO host_jobs (job_id, group_id, operation, state, "
                    "priority, resource_class, config_hash, payload_json, "
                    "progress_percent, progress_message, checkpoint_json, "
                    "created_at_utc, started_at_utc, completed_at_utc, "
                    "terminal_reason) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, "
                    "?, ?, ?, ?)",
                    (
                        record.job_id,
                        record.group_id,
                        record.operation,
                        record.state,
                        record.priority,
                        record.resource_class,
                        record.config_hash,
                        payload_json,
                        record.progress_percent,
                        record.progress_message,
                        checkpoint_json,
                        record.created_at_utc,
                        record.started_at_utc,
                        record.completed_at_utc,
                        record.terminal_reason,
                    ),
                )
            except sqlite3.IntegrityError as error:
                _raise_for_integrity(error, context="Job")

    def get_job(self, job_id: str) -> HostJobRecord | None:
        """Return one job, or None when the identifier is absent."""
        with _connect(self._path) as connection:
            row = connection.execute(
                "SELECT job_id, group_id, operation, state, priority, "
                "resource_class, config_hash, payload_json, progress_percent, "
                "progress_message, checkpoint_json, created_at_utc, "
                "started_at_utc, completed_at_utc, terminal_reason "
                "FROM host_jobs WHERE job_id=?",
                (job_id,),
            ).fetchone()
        return None if row is None else _job_record(row)

    def list_jobs(
        self, *, state: str | None = None, group_id: str | None = None
    ) -> list[HostJobRecord]:
        """Return jobs highest-priority first, then oldest first.

        Optional state and group filters may be combined; both use the
        indexes created by ensure_schema.
        """
        with _connect(self._path) as connection:
            if state is None and group_id is None:
                rows = connection.execute(
                    "SELECT job_id, group_id, operation, state, priority, "
                    "resource_class, config_hash, payload_json, progress_percent, "
                    "progress_message, checkpoint_json, created_at_utc, "
                    "started_at_utc, completed_at_utc, terminal_reason "
                    "FROM host_jobs ORDER BY priority DESC, created_at_utc, job_id"
                ).fetchall()
            elif state is None:
                rows = connection.execute(
                    "SELECT job_id, group_id, operation, state, priority, "
                    "resource_class, config_hash, payload_json, progress_percent, "
                    "progress_message, checkpoint_json, created_at_utc, "
                    "started_at_utc, completed_at_utc, terminal_reason "
                    "FROM host_jobs WHERE group_id=? "
                    "ORDER BY priority DESC, created_at_utc, job_id",
                    (group_id,),
                ).fetchall()
            elif group_id is None:
                rows = connection.execute(
                    "SELECT job_id, group_id, operation, state, priority, "
                    "resource_class, config_hash, payload_json, progress_percent, "
                    "progress_message, checkpoint_json, created_at_utc, "
                    "started_at_utc, completed_at_utc, terminal_reason "
                    "FROM host_jobs WHERE state=? "
                    "ORDER BY priority DESC, created_at_utc, job_id",
                    (state,),
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT job_id, group_id, operation, state, priority, "
                    "resource_class, config_hash, payload_json, progress_percent, "
                    "progress_message, checkpoint_json, created_at_utc, "
                    "started_at_utc, completed_at_utc, terminal_reason "
                    "FROM host_jobs WHERE state=? AND group_id=? "
                    "ORDER BY priority DESC, created_at_utc, job_id",
                    (state, group_id),
                ).fetchall()
        return [_job_record(row) for row in rows]

    def update_job_progress(
        self, job_id: str, *, progress_percent: float, progress_message: str
    ) -> bool:
        """Update job progress; return False when the job is absent."""
        percent = _validated_progress(progress_percent)
        with _connect(self._path) as connection, _write_transaction(connection):
            cursor = connection.execute(
                "UPDATE host_jobs SET progress_percent=?, progress_message=? "
                "WHERE job_id=?",
                (percent, progress_message, job_id),
            )
            return cursor.rowcount > 0

    def update_job_checkpoint(self, job_id: str, *, checkpoint_json: str) -> bool:
        """Replace the job checkpoint; return False when the job is absent."""
        checkpoint = _validated_json(checkpoint_json)
        with _connect(self._path) as connection, _write_transaction(connection):
            cursor = connection.execute(
                "UPDATE host_jobs SET checkpoint_json=? WHERE job_id=?",
                (checkpoint, job_id),
            )
            return cursor.rowcount > 0

    def transition_job(
        self,
        job_id: str,
        *,
        from_state: str,
        to_state: str,
        started_at_utc: str | None = None,
        completed_at_utc: str | None = None,
        terminal_reason: str | None = None,
    ) -> HostJobRecord:
        """Atomically move a job between states on an expected state.

        The compare-and-set runs inside one immediate transaction, so a job
        whose state changed concurrently raises
        HostPersistenceConflictError instead of overwriting. Optional
        timestamps and terminal reason are filled in when supplied and
        otherwise keep their stored values.
        """
        with _connect(self._path) as connection, _write_transaction(connection):
            row = connection.execute(
                "SELECT job_id, group_id, operation, state, priority, "
                "resource_class, config_hash, payload_json, progress_percent, "
                "progress_message, checkpoint_json, created_at_utc, "
                "started_at_utc, completed_at_utc, terminal_reason "
                "FROM host_jobs WHERE job_id=?",
                (job_id,),
            ).fetchone()
            if row is None:
                raise HostPersistenceConflictError("Job does not exist")
            if row[3] != from_state:
                raise HostPersistenceConflictError("Job state changed concurrently")
            connection.execute(
                "UPDATE host_jobs SET state=?, "
                "started_at_utc=COALESCE(?, started_at_utc), "
                "completed_at_utc=COALESCE(?, completed_at_utc), "
                "terminal_reason=COALESCE(?, terminal_reason) WHERE job_id=?",
                (to_state, started_at_utc, completed_at_utc, terminal_reason, job_id),
            )
            return HostJobRecord(
                job_id=row[0],
                group_id=row[1],
                operation=row[2],
                state=to_state,
                priority=row[4],
                resource_class=row[5],
                config_hash=row[6],
                payload_json=row[7],
                progress_percent=row[8],
                progress_message=row[9],
                checkpoint_json=row[10],
                created_at_utc=row[11],
                started_at_utc=(
                    started_at_utc if started_at_utc is not None else row[12]
                ),
                completed_at_utc=(
                    completed_at_utc if completed_at_utc is not None else row[13]
                ),
                terminal_reason=(
                    terminal_reason if terminal_reason is not None else row[14]
                ),
            )

    def delete_job(self, job_id: str) -> bool:
        """Delete a job with its attempts, events, and leases atomically."""
        with _connect(self._path) as connection, _write_transaction(connection):
            row = connection.execute(
                "SELECT 1 FROM host_jobs WHERE job_id=?", (job_id,)
            ).fetchone()
            if row is None:
                return False
            connection.execute(
                "DELETE FROM host_job_attempts WHERE job_id=?", (job_id,)
            )
            connection.execute("DELETE FROM host_job_events WHERE job_id=?", (job_id,))
            connection.execute("DELETE FROM host_grid_leases WHERE job_id=?", (job_id,))
            connection.execute("DELETE FROM host_jobs WHERE job_id=?", (job_id,))
        return True

    # -- host_job_attempts --------------------------------------------------

    def create_attempt(self, record: HostJobAttemptRecord) -> None:
        """Insert one attempt for an existing job; conflicts fail closed."""
        checkpoint_json = (
            None
            if record.checkpoint_json is None
            else _validated_json(record.checkpoint_json)
        )
        with _connect(self._path) as connection, _write_transaction(connection):
            try:
                connection.execute(
                    "INSERT INTO host_job_attempts (attempt_id, job_id, worker_id, "
                    "sequence, state, heartbeat_at_utc, checkpoint_json, "
                    "created_at_utc, completed_at_utc) VALUES (?, ?, ?, ?, ?, ?, "
                    "?, ?, ?)",
                    (
                        record.attempt_id,
                        record.job_id,
                        record.worker_id,
                        record.sequence,
                        record.state,
                        record.heartbeat_at_utc,
                        checkpoint_json,
                        record.created_at_utc,
                        record.completed_at_utc,
                    ),
                )
            except sqlite3.IntegrityError as error:
                _raise_for_integrity(error, context="Job attempt")

    def get_attempt(self, attempt_id: str) -> HostJobAttemptRecord | None:
        """Return one attempt, or None when the identifier is absent."""
        with _connect(self._path) as connection:
            row = connection.execute(
                "SELECT attempt_id, job_id, worker_id, sequence, state, "
                "heartbeat_at_utc, checkpoint_json, created_at_utc, "
                "completed_at_utc FROM host_job_attempts WHERE attempt_id=?",
                (attempt_id,),
            ).fetchone()
        return None if row is None else _attempt_record(row)

    def list_attempts(self, job_id: str) -> list[HostJobAttemptRecord]:
        """Return a job's attempts ordered by ascending sequence."""
        with _connect(self._path) as connection:
            rows = connection.execute(
                "SELECT attempt_id, job_id, worker_id, sequence, state, "
                "heartbeat_at_utc, checkpoint_json, created_at_utc, "
                "completed_at_utc FROM host_job_attempts WHERE job_id=? "
                "ORDER BY sequence",
                (job_id,),
            ).fetchall()
        return [_attempt_record(row) for row in rows]

    def update_attempt_heartbeat(
        self, attempt_id: str, *, heartbeat_at_utc: str
    ) -> bool:
        """Stamp the attempt heartbeat; return False when it is absent."""
        with _connect(self._path) as connection, _write_transaction(connection):
            cursor = connection.execute(
                "UPDATE host_job_attempts SET heartbeat_at_utc=? WHERE attempt_id=?",
                (heartbeat_at_utc, attempt_id),
            )
            return cursor.rowcount > 0

    def update_attempt_checkpoint(
        self, attempt_id: str, *, checkpoint_json: str
    ) -> bool:
        """Replace the attempt checkpoint; return False when it is absent."""
        checkpoint = _validated_json(checkpoint_json)
        with _connect(self._path) as connection, _write_transaction(connection):
            cursor = connection.execute(
                "UPDATE host_job_attempts SET checkpoint_json=? WHERE attempt_id=?",
                (checkpoint, attempt_id),
            )
            return cursor.rowcount > 0

    def complete_attempt(
        self, attempt_id: str, *, state: str, completed_at_utc: str
    ) -> bool:
        """Record a terminal attempt state; return False when it is absent."""
        with _connect(self._path) as connection, _write_transaction(connection):
            cursor = connection.execute(
                "UPDATE host_job_attempts SET state=?, completed_at_utc=? "
                "WHERE attempt_id=?",
                (state, completed_at_utc, attempt_id),
            )
            return cursor.rowcount > 0

    # -- host_job_events ----------------------------------------------------

    def record_event(self, record: HostJobEventRecord) -> None:
        """Append one state-transition event with a validated payload."""
        details_json = _validated_json(record.details_json)
        with _connect(self._path) as connection, _write_transaction(connection):
            try:
                connection.execute(
                    "INSERT INTO host_job_events (event_id, job_id, attempt_id, "
                    "from_state, to_state, details_json, created_at_utc) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        record.event_id,
                        record.job_id,
                        record.attempt_id,
                        record.from_state,
                        record.to_state,
                        details_json,
                        record.created_at_utc,
                    ),
                )
            except sqlite3.IntegrityError as error:
                _raise_for_integrity(error, context="Job event")

    def list_events(self, job_id: str) -> list[HostJobEventRecord]:
        """Return a job's events ordered by creation time then identifier."""
        with _connect(self._path) as connection:
            rows = connection.execute(
                "SELECT event_id, job_id, attempt_id, from_state, to_state, "
                "details_json, created_at_utc FROM host_job_events "
                "WHERE job_id=? ORDER BY created_at_utc, event_id",
                (job_id,),
            ).fetchall()
        return [_event_record(row) for row in rows]

    # -- host_grid_nodes and host_grid_leases --------------------------------

    def upsert_node(self, record: HostGridNodeRecord) -> None:
        """Insert or refresh one grid node registration."""
        with _connect(self._path) as connection, _write_transaction(connection):
            connection.execute(
                "INSERT INTO host_grid_nodes (node_id, host, port, cores, "
                "memory_mb, state, last_heartbeat_utc) VALUES (?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(node_id) DO UPDATE SET host=excluded.host, "
                "port=excluded.port, cores=excluded.cores, "
                "memory_mb=excluded.memory_mb, state=excluded.state, "
                "last_heartbeat_utc=excluded.last_heartbeat_utc",
                (
                    record.node_id,
                    record.host,
                    record.port,
                    record.cores,
                    record.memory_mb,
                    record.state,
                    record.last_heartbeat_utc,
                ),
            )

    def get_node(self, node_id: str) -> HostGridNodeRecord | None:
        """Return one grid node, or None when the identifier is absent."""
        with _connect(self._path) as connection:
            row = connection.execute(
                "SELECT node_id, host, port, cores, memory_mb, state, "
                "last_heartbeat_utc FROM host_grid_nodes WHERE node_id=?",
                (node_id,),
            ).fetchone()
        return None if row is None else _node_record(row)

    def list_nodes(self) -> list[HostGridNodeRecord]:
        """Return every grid node ordered by identifier."""
        with _connect(self._path) as connection:
            rows = connection.execute(
                "SELECT node_id, host, port, cores, memory_mb, state, "
                "last_heartbeat_utc FROM host_grid_nodes ORDER BY node_id"
            ).fetchall()
        return [_node_record(row) for row in rows]

    def update_node_heartbeat(self, node_id: str, *, heartbeat_at_utc: str) -> bool:
        """Stamp the node heartbeat; return False when the node is absent."""
        with _connect(self._path) as connection, _write_transaction(connection):
            cursor = connection.execute(
                "UPDATE host_grid_nodes SET last_heartbeat_utc=? WHERE node_id=?",
                (heartbeat_at_utc, node_id),
            )
            return cursor.rowcount > 0

    def delete_node(self, node_id: str) -> bool:
        """Remove a node unless a lease still references it.

        An active lease fails with a precise conflict error; released or
        expired lease rows also block removal because they preserve history
        referencing the node. Deleting that history first is the caller's
        explicit decision.
        """
        with _connect(self._path) as connection, _write_transaction(connection):
            active = connection.execute(
                "SELECT 1 FROM host_grid_leases WHERE node_id=? AND state=? LIMIT 1",
                (node_id, ACTIVE_LEASE_STATE),
            ).fetchone()
            if active is not None:
                raise HostPersistenceConflictError("Node has an active grid lease")
            try:
                cursor = connection.execute(
                    "DELETE FROM host_grid_nodes WHERE node_id=?", (node_id,)
                )
            except sqlite3.IntegrityError as error:
                raise HostPersistenceConflictError(
                    "Node still has grid lease history"
                ) from error
            return cursor.rowcount > 0

    def insert_lease(self, record: HostGridLeaseRecord) -> None:
        """Insert one lease for an existing node and job; conflicts fail."""
        with _connect(self._path) as connection, _write_transaction(connection):
            try:
                connection.execute(
                    "INSERT INTO host_grid_leases (lease_id, node_id, job_id, "
                    "leased_at_utc, expires_at_utc, state) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        record.lease_id,
                        record.node_id,
                        record.job_id,
                        record.leased_at_utc,
                        record.expires_at_utc,
                        record.state,
                    ),
                )
            except sqlite3.IntegrityError as error:
                _raise_for_integrity(error, context="Grid lease")

    def get_lease(self, lease_id: str) -> HostGridLeaseRecord | None:
        """Return one lease, or None when the identifier is absent."""
        with _connect(self._path) as connection:
            row = connection.execute(
                "SELECT lease_id, node_id, job_id, leased_at_utc, expires_at_utc, "
                "state FROM host_grid_leases WHERE lease_id=?",
                (lease_id,),
            ).fetchone()
        return None if row is None else _lease_record(row)

    def list_leases(self, *, state: str | None = None) -> list[HostGridLeaseRecord]:
        """Return leases ordered by lease time, optionally by state."""
        with _connect(self._path) as connection:
            if state is None:
                rows = connection.execute(
                    "SELECT lease_id, node_id, job_id, leased_at_utc, "
                    "expires_at_utc, state FROM host_grid_leases "
                    "ORDER BY leased_at_utc, lease_id"
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT lease_id, node_id, job_id, leased_at_utc, "
                    "expires_at_utc, state FROM host_grid_leases WHERE state=? "
                    "ORDER BY leased_at_utc, lease_id",
                    (state,),
                ).fetchall()
        return [_lease_record(row) for row in rows]

    def release_lease(self, lease_id: str, *, state: str) -> bool:
        """Move a lease to a terminal state; return False when absent."""
        with _connect(self._path) as connection, _write_transaction(connection):
            cursor = connection.execute(
                "UPDATE host_grid_leases SET state=? WHERE lease_id=?",
                (state, lease_id),
            )
            return cursor.rowcount > 0

    def expire_leases(self, *, now_utc: str) -> list[HostGridLeaseRecord]:
        """Flip active leases whose expiry strictly passed to expired.

        Comparison is lexicographic over UTC ISO-8601 strings, matching the
        stored timestamp convention. A lease expiring exactly at now_utc
        stays active. The returned records reflect the pre-update rows.
        """
        with _connect(self._path) as connection, _write_transaction(connection):
            rows = connection.execute(
                "SELECT lease_id, node_id, job_id, leased_at_utc, expires_at_utc, "
                "state FROM host_grid_leases WHERE state=? AND expires_at_utc < ? "
                "ORDER BY expires_at_utc, lease_id",
                (ACTIVE_LEASE_STATE, now_utc),
            ).fetchall()
            connection.execute(
                "UPDATE host_grid_leases SET state=? WHERE state=? "
                "AND expires_at_utc < ?",
                (EXPIRED_LEASE_STATE, ACTIVE_LEASE_STATE, now_utc),
            )
        return [_lease_record(row) for row in rows]

    def delete_lease(self, lease_id: str) -> bool:
        """Remove one lease row; return False when it is absent."""
        with _connect(self._path) as connection, _write_transaction(connection):
            cursor = connection.execute(
                "DELETE FROM host_grid_leases WHERE lease_id=?", (lease_id,)
            )
            return cursor.rowcount > 0
