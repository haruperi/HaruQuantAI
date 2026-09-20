"""Transactional SQLite persistence feature for the Workspace domain.

Purpose:
    Provides durable storage, parameterized SQL execution, and transactional
    invariants for application settings, durable job states, worker attempts,
    audit events, and distributed grid nodes under namespace `workspace.v1`.

Key capabilities:
    * WAL-mode SQLite metadata management with bounded busy timeout.
    * Atomic compare-and-swap job state mutations and append-only audit events.
    * Scoped key-value settings storage with JSON serialization.
    * Remote worker grid node registration and time-bounded lease reconciliation.

Python API usage:
    persistence = ctx.require(WORKSPACE_PERSISTENCE)
    persistence.execute_mutation("INSERT INTO workspace_settings ...", params)

CLI usage:
    uv run python -m tests.examples.01_workspace
"""

from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, override
from uuid import uuid4

from app.contracts.workspace import (
    WORKSPACE_PERSISTENCE,
)
from app.contracts.workspace import (
    WorkspacePersistenceService as IWorkspacePersistenceService,
)
from app.kernel.feature import FeatureSpec
from app.kernel.logging import get_logger

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext

logger = get_logger(__name__)

_SCHEMA_SQL: str = """
CREATE TABLE IF NOT EXISTS workspace_settings (
    scope TEXT NOT NULL,
    key TEXT NOT NULL,
    value_json TEXT NOT NULL,
    schema_version INTEGER NOT NULL DEFAULT 1,
    updated_at_utc TEXT NOT NULL,
    PRIMARY KEY (scope, key)
);

CREATE TABLE IF NOT EXISTS workspace_jobs (
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
);

CREATE INDEX IF NOT EXISTS idx_workspace_jobs_state ON workspace_jobs(state);
CREATE INDEX IF NOT EXISTS idx_workspace_jobs_group ON workspace_jobs(group_id);

CREATE TABLE IF NOT EXISTS workspace_job_attempts (
    attempt_id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL REFERENCES workspace_jobs(job_id),
    worker_id TEXT NOT NULL,
    sequence INTEGER NOT NULL,
    state TEXT NOT NULL,
    heartbeat_at_utc TEXT,
    checkpoint_json TEXT,
    created_at_utc TEXT NOT NULL,
    completed_at_utc TEXT
);

CREATE INDEX IF NOT EXISTS idx_workspace_attempts_job ON workspace_job_attempts(job_id);

CREATE TABLE IF NOT EXISTS workspace_job_events (
    event_id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    attempt_id TEXT,
    from_state TEXT,
    to_state TEXT NOT NULL,
    details_json TEXT NOT NULL,
    created_at_utc TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_workspace_events_job ON workspace_job_events(job_id);

CREATE TABLE IF NOT EXISTS workspace_grid_nodes (
    node_id TEXT PRIMARY KEY,
    host TEXT NOT NULL,
    port INTEGER NOT NULL,
    cores INTEGER NOT NULL,
    memory_mb INTEGER NOT NULL,
    state TEXT NOT NULL,
    last_heartbeat_utc TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS workspace_grid_leases (
    lease_id TEXT PRIMARY KEY,
    node_id TEXT NOT NULL REFERENCES workspace_grid_nodes(node_id),
    job_id TEXT NOT NULL REFERENCES workspace_jobs(job_id),
    leased_at_utc TEXT NOT NULL,
    expires_at_utc TEXT NOT NULL,
    state TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_workspace_leases_node ON workspace_grid_leases(node_id);
CREATE INDEX IF NOT EXISTS idx_workspace_leases_job ON workspace_grid_leases(job_id);
"""


DEFAULT_DB_PATH: str = "data/database/haruquantai.db"
SCHEMA_VERSION: int = 1


def get_default_db_path() -> str:
    """Resolve default database path with environment override."""
    return os.environ.get("HARUQUANTAI_DB_PATH", DEFAULT_DB_PATH)


@dataclass(frozen=True, slots=True)
class WorkspacePersistenceConfig:
    """Runtime configuration for workspace domain SQLite persistence."""

    db_path: str = ""
    busy_timeout_ms: int = 5000
    wal_mode: bool = True

    def __post_init__(self) -> None:
        """Validate database parameters."""
        resolved = self.db_path or get_default_db_path()
        object.__setattr__(self, "db_path", resolved)
        if self.busy_timeout_ms < 0:
            msg = f"busy_timeout_ms must be non-negative; got {self.busy_timeout_ms}"
            raise ValueError(msg)
        if not self.db_path or not self.db_path.strip():
            msg = "db_path cannot be empty"
            raise ValueError(msg)


class WorkspacePersistenceService(IWorkspacePersistenceService):
    """Implement transactional SQLite operations for the workspace domain."""

    def __init__(self, config: WorkspacePersistenceConfig) -> None:
        """Initialize SQLite database, set pragmas, and run schema DDL.

        Args:
            config: Persistence runtime options.
        """
        self._config = config
        if config.db_path != ":memory:":
            db_dir = Path(config.db_path).parent
            db_dir.mkdir(parents=True, exist_ok=True)

        self._conn = sqlite3.connect(
            config.db_path,
            check_same_thread=False,
            autocommit=True,
        )
        self._conn.row_factory = sqlite3.Row

        # Apply robust SQLite pragmas
        cursor = self._conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute(f"PRAGMA busy_timeout = {config.busy_timeout_ms};")
        if config.wal_mode and config.db_path != ":memory:":
            cursor.execute("PRAGMA journal_mode = WAL;")
        cursor.execute(f"PRAGMA user_version = {SCHEMA_VERSION};")
        cursor.close()

        # Initialize schema tables
        self.execute_script(_SCHEMA_SQL)
        logger.info(
            "workspace_persistence_initialized",
            db_path=config.db_path,
            wal_mode=config.wal_mode,
        )

    def execute_query(
        self, sql: str, params: tuple[Any, ...] = ()
    ) -> list[tuple[Any, ...]]:
        """Execute a read-only SQL query and return rows.

        Args:
            sql: Parameterized SQL string.
            params: Parameters tuple.

        Returns:
            List of row tuples.
        """
        cursor = self._conn.cursor()
        try:
            cursor.execute(sql, params)
            return cursor.fetchall()
        finally:
            cursor.close()

    def execute_mutation(self, sql: str, params: tuple[Any, ...] = ()) -> int:
        """Execute an atomic mutating SQL statement in a transaction.

        Args:
            sql: Parameterized SQL statement.
            params: Parameters tuple.

        Returns:
            Number of affected rows.
        """
        cursor = self._conn.cursor()
        try:
            with self._conn:
                cursor.execute(sql, params)
                return cursor.rowcount
        finally:
            cursor.close()

    def execute_script(self, script: str) -> None:
        """Execute a multi-statement SQL script transactionally.

        Args:
            script: SQL script string.
        """
        cursor = self._conn.cursor()
        try:
            with self._conn:
                cursor.executescript(script)
        finally:
            cursor.close()

    # -----------------------------------------------------------------------
    # Schema & Metadata
    # -----------------------------------------------------------------------
    @override
    def get_schema_version(self) -> int:
        """Return the PRAGMA user_version persisted in the database."""
        cursor = self._conn.cursor()
        try:
            cursor.execute("PRAGMA user_version;")
            row = cursor.fetchone()
            return int(row[0]) if row else 0
        finally:
            cursor.close()

    # -----------------------------------------------------------------------
    # Settings Operations (FIP-14 PERSIST)
    # -----------------------------------------------------------------------
    @override
    def load_all_settings(self) -> list[tuple[str, str, str, int, str]]:
        """Load all persisted settings records."""
        cursor = self._conn.cursor()
        try:
            cursor.execute(
                "SELECT scope, key, value_json, schema_version, updated_at_utc "
                "FROM workspace_settings ORDER BY scope, key;"
            )
            return [(r[0], r[1], r[2], int(r[3]), r[4]) for r in cursor.fetchall()]
        finally:
            cursor.close()

    @override
    def save_setting(
        self,
        scope: str,
        key: str,
        value_json: str,
        schema_version: int,
        updated_at_utc: str,
    ) -> None:
        """Upsert a setting entry inside a transaction."""
        sql = """
        INSERT INTO workspace_settings (
            scope, key, value_json, schema_version, updated_at_utc
        ) VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(scope, key) DO UPDATE SET
            value_json = excluded.value_json,
            schema_version = excluded.schema_version,
            updated_at_utc = excluded.updated_at_utc;
        """
        cursor = self._conn.cursor()
        try:
            with self._conn:
                cursor.execute(
                    sql,
                    (scope, key, value_json, schema_version, updated_at_utc),
                )
        finally:
            cursor.close()

    @override
    def delete_setting(self, scope: str, key: str) -> bool:
        """Delete a setting entry."""
        sql = "DELETE FROM workspace_settings WHERE scope = ? AND key = ?;"
        cursor = self._conn.cursor()
        try:
            with self._conn:
                cursor.execute(sql, (scope, key))
                return cursor.rowcount > 0
        finally:
            cursor.close()

    # -----------------------------------------------------------------------
    # Jobs Operations (FIP-14 PERSIST, FIP-21 COMP)
    # -----------------------------------------------------------------------
    @override
    def insert_job(
        self,
        *,
        job_id: str,
        group_id: str | None,
        operation: str,
        state: str,
        priority: int,
        resource_class: str,
        config_hash: str,
        payload_json: str,
        created_at_utc: str,
        event_id: str,
        event_details_json: str,
    ) -> None:
        """Register a new job in the durable ledger and append initial audit event."""
        job_sql = """
        INSERT INTO workspace_jobs (
            job_id, group_id, operation, state, priority,
            resource_class, config_hash, payload_json,
            progress_percent, progress_message, created_at_utc
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0.0, '', ?);
        """
        event_sql = """
        INSERT INTO workspace_job_events (
            event_id, job_id, attempt_id, from_state,
            to_state, details_json, created_at_utc
        ) VALUES (?, ?, NULL, NULL, ?, ?, ?);
        """
        cursor = self._conn.cursor()
        try:
            with self._conn:
                cursor.execute(
                    job_sql,
                    (
                        job_id,
                        group_id,
                        operation,
                        state,
                        priority,
                        resource_class,
                        config_hash,
                        payload_json,
                        created_at_utc,
                    ),
                )
                cursor.execute(
                    event_sql,
                    (
                        event_id,
                        job_id,
                        state,
                        event_details_json,
                        created_at_utc,
                    ),
                )
        finally:
            cursor.close()

    @override
    def get_job_record(self, job_id: str) -> tuple[Any, ...] | None:
        """Retrieve durable job tuple by ID."""
        sql = """
        SELECT job_id, group_id, operation, state, priority,
               resource_class, config_hash, payload_json,
               progress_percent, progress_message, checkpoint_json,
               created_at_utc, started_at_utc, completed_at_utc, terminal_reason
        FROM workspace_jobs WHERE job_id = ?;
        """
        cursor = self._conn.cursor()
        try:
            cursor.execute(sql, (job_id,))
            row = cursor.fetchone()
            return tuple(row) if row else None
        finally:
            cursor.close()

    @override
    def transition_job_state_cas(
        self,
        *,
        job_id: str,
        expected_state: str | None,
        new_state: str,
        updated_at_utc: str,
        event_id: str,
        event_details_json: str,
        attempt_id: str | None = None,
        terminal_reason: str | None = None,
    ) -> bool:
        """Perform a single-statement atomic compare-and-swap transition."""
        is_terminal = terminal_reason is not None or new_state in (
            "succeeded",
            "failed",
            "cancelled",
            "interrupted",
        )
        reason = terminal_reason or new_state

        if expected_state is not None:
            if new_state == "running":
                upd_sql = """
                UPDATE workspace_jobs
                SET state = ?, started_at_utc = ?
                WHERE job_id = ? AND state = ?;
                """
                params: tuple[Any, ...] = (
                    new_state,
                    updated_at_utc,
                    job_id,
                    expected_state,
                )
            elif is_terminal:
                upd_sql = """
                UPDATE workspace_jobs
                SET state = ?, completed_at_utc = ?, terminal_reason = ?
                WHERE job_id = ? AND state = ?;
                """
                params = (
                    new_state,
                    updated_at_utc,
                    reason,
                    job_id,
                    expected_state,
                )
            else:
                upd_sql = """
                UPDATE workspace_jobs
                SET state = ?
                WHERE job_id = ? AND state = ?;
                """
                params = (new_state, job_id, expected_state)
        elif new_state == "running":
            upd_sql = """
            UPDATE workspace_jobs
            SET state = ?, started_at_utc = ?
            WHERE job_id = ?;
            """
            params = (new_state, updated_at_utc, job_id)
        elif is_terminal:
            upd_sql = """
            UPDATE workspace_jobs
            SET state = ?, completed_at_utc = ?, terminal_reason = ?
            WHERE job_id = ?;
            """
            params = (new_state, updated_at_utc, reason, job_id)
        else:
            upd_sql = """
            UPDATE workspace_jobs
            SET state = ?
            WHERE job_id = ?;
            """
            params = (new_state, job_id)

        event_sql = """
        INSERT INTO workspace_job_events (
            event_id, job_id, attempt_id, from_state,
            to_state, details_json, created_at_utc
        ) VALUES (?, ?, ?, ?, ?, ?, ?);
        """

        cursor = self._conn.cursor()
        try:
            with self._conn:
                cursor.execute(upd_sql, params)
                if cursor.rowcount != 1:
                    return False
                cursor.execute(
                    event_sql,
                    (
                        event_id,
                        job_id,
                        attempt_id,
                        expected_state,
                        new_state,
                        event_details_json,
                        updated_at_utc,
                    ),
                )
                return True
        finally:
            cursor.close()

    @override
    def update_job_progress(
        self,
        job_id: str,
        progress_percent: float,
        progress_message: str,
        checkpoint_json: str | None = None,
    ) -> bool:
        """Update job execution progress."""
        sql = """
        UPDATE workspace_jobs
        SET progress_percent = ?, progress_message = ?, checkpoint_json = ?
        WHERE job_id = ?;
        """
        cursor = self._conn.cursor()
        try:
            with self._conn:
                cursor.execute(
                    sql,
                    (progress_percent, progress_message, checkpoint_json, job_id),
                )
                return cursor.rowcount > 0
        finally:
            cursor.close()

    @override
    def create_job_attempt(
        self,
        *,
        attempt_id: str,
        job_id: str,
        worker_id: str,
        sequence: int,
        state: str,
        created_at_utc: str,
    ) -> None:
        """Record a new worker attempt for a job."""
        sql = """
        INSERT INTO workspace_job_attempts (
            attempt_id, job_id, worker_id, sequence, state,
            heartbeat_at_utc, checkpoint_json, created_at_utc, completed_at_utc
        ) VALUES (?, ?, ?, ?, ?, ?, NULL, ?, NULL);
        """
        cursor = self._conn.cursor()
        try:
            with self._conn:
                cursor.execute(
                    sql,
                    (
                        attempt_id,
                        job_id,
                        worker_id,
                        sequence,
                        state,
                        created_at_utc,
                        created_at_utc,
                    ),
                )
        finally:
            cursor.close()

    @override
    def update_attempt_heartbeat(self, attempt_id: str, heartbeat_at_utc: str) -> bool:
        """Record worker attempt heartbeat timestamp."""
        sql = """
        UPDATE workspace_job_attempts
        SET heartbeat_at_utc = ?
        WHERE attempt_id = ?;
        """
        cursor = self._conn.cursor()
        try:
            with self._conn:
                cursor.execute(sql, (heartbeat_at_utc, attempt_id))
                return cursor.rowcount > 0
        finally:
            cursor.close()

    @override
    def update_attempt_checkpoint(
        self, attempt_id: str, heartbeat_at_utc: str, checkpoint_json: str
    ) -> bool:
        """Update durable attempt checkpoint state."""
        sql = """
        UPDATE workspace_job_attempts
        SET heartbeat_at_utc = ?, checkpoint_json = ?
        WHERE attempt_id = ?;
        """
        cursor = self._conn.cursor()
        try:
            with self._conn:
                cursor.execute(sql, (heartbeat_at_utc, checkpoint_json, attempt_id))
                return cursor.rowcount > 0
        finally:
            cursor.close()

    @override
    def complete_job_attempt(
        self,
        *,
        attempt_id: str,
        state: str,
        completed_at_utc: str,
    ) -> bool:
        """Mark attempt as completed, failed, or cancelled."""
        sql = """
        UPDATE workspace_job_attempts
        SET state = ?, completed_at_utc = ?
        WHERE attempt_id = ?;
        """
        cursor = self._conn.cursor()
        try:
            with self._conn:
                cursor.execute(sql, (state, completed_at_utc, attempt_id))
                return cursor.rowcount > 0
        finally:
            cursor.close()

    @override
    def get_job_attempts(self, job_id: str) -> list[tuple[Any, ...]]:
        """Retrieve attempt history for a job ordered by sequence."""
        sql = """
        SELECT attempt_id, job_id, worker_id, sequence, state,
               heartbeat_at_utc, checkpoint_json, created_at_utc, completed_at_utc
        FROM workspace_job_attempts
        WHERE job_id = ?
        ORDER BY sequence ASC;
        """
        cursor = self._conn.cursor()
        try:
            cursor.execute(sql, (job_id,))
            return [tuple(r) for r in cursor.fetchall()]
        finally:
            cursor.close()

    @override
    def get_job_events(self, job_id: str) -> list[tuple[Any, ...]]:
        """Retrieve immutable audit events for a job."""
        sql = """
        SELECT event_id, job_id, attempt_id, from_state,
               to_state, details_json, created_at_utc
        FROM workspace_job_events
        WHERE job_id = ?
        ORDER BY created_at_utc ASC;
        """
        cursor = self._conn.cursor()
        try:
            cursor.execute(sql, (job_id,))
            return [tuple(r) for r in cursor.fetchall()]
        finally:
            cursor.close()

    @override
    def record_job_event(
        self,
        *,
        event_id: str,
        job_id: str,
        attempt_id: str | None,
        from_state: str | None,
        to_state: str,
        details_json: str,
        created_at_utc: str,
    ) -> None:
        """Record an immutable audit event for a job."""
        event_sql = """
        INSERT INTO workspace_job_events (
            event_id, job_id, attempt_id, from_state,
            to_state, details_json, created_at_utc
        ) VALUES (?, ?, ?, ?, ?, ?, ?);
        """
        cursor = self._conn.cursor()
        try:
            with self._conn:
                cursor.execute(
                    event_sql,
                    (
                        event_id,
                        job_id,
                        attempt_id,
                        from_state,
                        to_state,
                        details_json,
                        created_at_utc,
                    ),
                )
        finally:
            cursor.close()

    @override
    def recover_orphaned_jobs(
        self,
        *,
        running_states: tuple[str, ...],
        interrupted_state: str,
        interrupted_reason: str,
        now_utc: str,
    ) -> int:
        """Identify uncompleted jobs from previous runs and mark them interrupted."""
        cursor = self._conn.cursor()
        try:
            with self._conn:
                placeholders = ",".join("?" for _ in running_states)
                query_sql = f"""
                SELECT job_id, state
                FROM workspace_jobs
                WHERE state IN ({placeholders});
                """  # noqa: S608
                cursor.execute(query_sql, running_states)
                jobs = cursor.fetchall()
                if not jobs:
                    return 0

                count = len(jobs)
                for r in jobs:
                    job_id = str(r[0])
                    from_st = str(r[1])

                    # Transition job
                    cursor.execute(
                        """
                        UPDATE workspace_jobs
                        SET state = ?, completed_at_utc = ?, terminal_reason = ?
                        WHERE job_id = ?;
                        """,
                        (interrupted_state, now_utc, interrupted_reason, job_id),
                    )
                    # Mark active attempts as interrupted
                    cursor.execute(
                        """
                        UPDATE workspace_job_attempts
                        SET state = ?, completed_at_utc = ?
                        WHERE job_id = ? AND state = 'running';
                        """,
                        (interrupted_state, now_utc, job_id),
                    )
                    # Record audit event
                    cursor.execute(
                        """
                        INSERT INTO workspace_job_events (
                            event_id, job_id, attempt_id, from_state,
                            to_state, details_json, created_at_utc
                        ) VALUES (?, ?, NULL, ?, ?, ?, ?);
                        """,
                        (
                            str(uuid4()),
                            job_id,
                            from_st,
                            interrupted_state,
                            json.dumps(
                                {
                                    "reason": interrupted_reason,
                                    "recovered": True,
                                }
                            ),
                            now_utc,
                        ),
                    )
                return count
        finally:
            cursor.close()

    # -----------------------------------------------------------------------
    # Grid Operations (FIP-14 PERSIST)
    # -----------------------------------------------------------------------
    @override
    def upsert_grid_node(
        self,
        *,
        node_id: str,
        host: str,
        port: int,
        cores: int,
        memory_mb: int,
        state: str,
        last_heartbeat_utc: str,
    ) -> None:
        """Register or update a remote worker node in the grid ledger."""
        sql = """
        INSERT INTO workspace_grid_nodes (
            node_id, host, port, cores, memory_mb, state, last_heartbeat_utc
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(node_id) DO UPDATE SET
            host = excluded.host,
            port = excluded.port,
            cores = excluded.cores,
            memory_mb = excluded.memory_mb,
            state = excluded.state,
            last_heartbeat_utc = excluded.last_heartbeat_utc;
        """
        cursor = self._conn.cursor()
        try:
            with self._conn:
                cursor.execute(
                    sql,
                    (
                        node_id,
                        host,
                        port,
                        cores,
                        memory_mb,
                        state,
                        last_heartbeat_utc,
                    ),
                )
        finally:
            cursor.close()

    @override
    def get_grid_nodes(self) -> list[tuple[Any, ...]]:
        """List all registered grid compute nodes."""
        sql = """
        SELECT node_id, host, port, cores, memory_mb, state, last_heartbeat_utc
        FROM workspace_grid_nodes
        ORDER BY node_id ASC;
        """
        cursor = self._conn.cursor()
        try:
            cursor.execute(sql)
            return [tuple(r) for r in cursor.fetchall()]
        finally:
            cursor.close()

    @override
    def get_grid_node(self, node_id: str) -> tuple[Any, ...] | None:
        """Retrieve a specific grid node."""
        sql = """
        SELECT node_id, host, port, cores, memory_mb, state, last_heartbeat_utc
        FROM workspace_grid_nodes WHERE node_id = ?;
        """
        cursor = self._conn.cursor()
        try:
            cursor.execute(sql, (node_id,))
            row = cursor.fetchone()
            return tuple(row) if row else None
        finally:
            cursor.close()

    @override
    def update_node_heartbeat(
        self, node_id: str, heartbeat_at_utc: str, state: str | None = None
    ) -> bool:
        """Record heartbeat and optionally update node status."""
        cursor = self._conn.cursor()
        try:
            with self._conn:
                if state is not None:
                    cursor.execute(
                        """
                        UPDATE workspace_grid_nodes
                        SET last_heartbeat_utc = ?, state = ?
                        WHERE node_id = ?;
                        """,
                        (heartbeat_at_utc, state, node_id),
                    )
                else:
                    cursor.execute(
                        """
                        UPDATE workspace_grid_nodes
                        SET last_heartbeat_utc = ?,
                            state = CASE
                                WHEN state = 'offline' THEN 'online'
                                ELSE state
                            END
                        WHERE node_id = ?;
                        """,
                        (heartbeat_at_utc, node_id),
                    )
                return cursor.rowcount > 0
        finally:
            cursor.close()

    @override
    def acquire_grid_lease(
        self,
        *,
        lease_id: str,
        node_id: str,
        job_id: str,
        acquired_at_utc: str,
        expires_at_utc: str,
        state: str,
        now_utc: str,
    ) -> bool:
        """Atomically check for conflicting active leases and insert new lease."""
        check_sql = """
        SELECT COUNT(*) FROM workspace_grid_leases
        WHERE job_id = ? AND state = 'active' AND expires_at_utc > ?;
        """
        ins_sql = """
        INSERT INTO workspace_grid_leases (
            lease_id, node_id, job_id, leased_at_utc, expires_at_utc, state
        ) VALUES (?, ?, ?, ?, ?, ?);
        """
        node_sql = "UPDATE workspace_grid_nodes SET state = 'busy' WHERE node_id = ?;"
        cursor = self._conn.cursor()
        try:
            with self._conn:
                cursor.execute(check_sql, (job_id, now_utc))
                row = cursor.fetchone()
                if row and row[0] > 0:
                    return False
                cursor.execute(
                    ins_sql,
                    (
                        lease_id,
                        node_id,
                        job_id,
                        acquired_at_utc,
                        expires_at_utc,
                        state,
                    ),
                )
                cursor.execute(node_sql, (node_id,))
                return True
        finally:
            cursor.close()

    @override
    def release_grid_lease(
        self, lease_id: str, completed_state: str, now_utc: str
    ) -> bool:
        """Mark lease as completed/released and restore node to online."""
        cursor = self._conn.cursor()
        try:
            with self._conn:
                cursor.execute(
                    "SELECT node_id FROM workspace_grid_leases WHERE lease_id = ?;",
                    (lease_id,),
                )
                row = cursor.fetchone()
                if not row:
                    return False
                node_id = row[0]
                cursor.execute(
                    "UPDATE workspace_grid_leases SET state = ? WHERE lease_id = ?;",
                    (completed_state, lease_id),
                )
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM workspace_grid_leases
                    WHERE node_id = ? AND state = 'active' AND expires_at_utc > ?;
                    """,
                    (node_id, now_utc),
                )
                active_row = cursor.fetchone()
                if active_row and active_row[0] == 0:
                    cursor.execute(
                        """
                        UPDATE workspace_grid_nodes
                        SET state = 'online'
                        WHERE node_id = ?;
                        """,
                        (node_id,),
                    )
                return True
        finally:
            cursor.close()

    @override
    def get_active_leases(self) -> list[tuple[Any, ...]]:
        """List all active leases."""
        sql = """
        SELECT lease_id, node_id, job_id, acquired_at_utc, expires_at_utc, state
        FROM workspace_grid_leases
        WHERE state = 'active';
        """
        cursor = self._conn.cursor()
        try:
            cursor.execute(sql)
            return [tuple(r) for r in cursor.fetchall()]
        finally:
            cursor.close()

    @override
    def reconcile_expired_leases(self, now_utc: str) -> list[tuple[str, str]]:
        """Mark expired leases and reconcile node statuses.

        Returns list of (lease_id, job_id).
        """
        cursor = self._conn.cursor()
        expired: list[tuple[str, str]] = []
        try:
            with self._conn:
                cursor.execute(
                    """
                    SELECT lease_id, node_id, job_id
                    FROM workspace_grid_leases
                    WHERE state = 'active' AND expires_at_utc <= ?;
                    """,
                    (now_utc,),
                )
                rows = cursor.fetchall()
                for lease_id, node_id, job_id in rows:
                    cursor.execute(
                        """
                        UPDATE workspace_grid_leases
                        SET state = 'expired'
                        WHERE lease_id = ?;
                        """,
                        (lease_id,),
                    )
                    cursor.execute(
                        """
                        SELECT COUNT(*) FROM workspace_grid_leases
                        WHERE node_id = ? AND state = 'active' AND expires_at_utc > ?;
                        """,
                        (node_id, now_utc),
                    )
                    active_row = cursor.fetchone()
                    if active_row and active_row[0] == 0:
                        cursor.execute(
                            """
                            UPDATE workspace_grid_nodes
                            SET state = 'online'
                            WHERE node_id = ?;
                            """,
                            (node_id,),
                        )
                    expired.append((str(lease_id), str(job_id)))
            return expired
        finally:
            cursor.close()

    @override
    def count_active_jobs(self) -> int:
        """Count the number of currently running jobs in the ledger."""
        cursor = self._conn.cursor()
        try:
            cursor.execute(
                "SELECT COUNT(*) FROM workspace_jobs WHERE state = 'running';"
            )
            row = cursor.fetchone()
            return int(row[0]) if row and row[0] is not None else 0
        finally:
            cursor.close()

    def close(self) -> None:
        """Commit pending work and close the SQLite connection."""
        try:
            self._conn.commit()
            self._conn.close()
            logger.info("workspace_persistence_closed", db_path=self._config.db_path)
        except sqlite3.Error as err:
            logger.warning("workspace_persistence_close_error", error=str(err))


SPEC: FeatureSpec = FeatureSpec(
    name="persistence.workspace",
    provides=frozenset({WORKSPACE_PERSISTENCE}),
    requires=frozenset(),
    optional=frozenset(),
    description="Transactional SQLite persistence for the workspace domain.",
)


class WorkspacePersistenceFeature:
    """Wire workspace persistence into the kernel composition lifecycle."""

    def __init__(self, config: WorkspacePersistenceConfig | None = None) -> None:
        """Initialize feature with optional configuration.

        Args:
            config: Optional persistence configuration.
        """
        self._config = config or WorkspacePersistenceConfig()

    @property
    def spec(self) -> FeatureSpec:
        """Return the immutable feature specification."""
        return SPEC

    async def start(self, context: FeatureContext) -> None:
        """Start the persistence service and publish its capability.

        Args:
            context: Lifecycle feature context.
        """
        service = WorkspacePersistenceService(self._config)
        context.on_close(service.close)
        context.provide(WORKSPACE_PERSISTENCE, service)


def feature() -> WorkspacePersistenceFeature:
    """Return an unmounted WorkspacePersistenceFeature instance.

    Returns:
        New feature instance.
    """
    return WorkspacePersistenceFeature()


__all__ = [
    "DEFAULT_DB_PATH",
    "SCHEMA_VERSION",
    "SPEC",
    "WorkspacePersistenceConfig",
    "WorkspacePersistenceFeature",
    "WorkspacePersistenceService",
    "feature",
    "get_default_db_path",
]
