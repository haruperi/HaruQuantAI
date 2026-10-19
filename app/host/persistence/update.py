"""Update operations for operational database tables.

Description:
    Provides parameterized update operations for database tables in HaruQuantAI.
    Ensures safe, atomic modifications by targeting rows strictly through primary
    keys or composite keys with non-silent requirement logging and error handling.
    Exposes both generic parameterized update primitives and explicit typed domain
    helpers.

Purpose:
    FEAT-HOST-PERSISTENCE: Host platform and workspace isolated SQLite persistence.

Key Capabilities:
    - FR-HOST-PERSISTENCE-UPDATE-BY-PK: Atomic record update targeting table PK
      with optional optimistic revision compare-and-set.
      Associated: `update_row_by_pk()`, `update_record()`, `update_entity()`,
      and 25 domain-specific update helpers.
      Logging: DEBUG emitted on successful update with affected row count; WARNING
      when no rows matched; ERROR on constraint or execution failure.
    - FR-HOST-PERSISTENCE-BATCH-SETTINGS-REVISION: Atomic batch settings upsert
      with optimistic revision conflict verification.
      Associated: `batch_save_host_settings()`, `RevisionConflictError`
      Logging: INFO emitted on committed batch settings update with new revision;
      WARNING emitted when revision conflict is detected.

Python API Usage:
    ```python
    from app.host.persistence.create import get_connection
    from app.host.persistence.update import (
        update_entity,
        update_host_setting,
        update_record,
        update_row_by_pk,
    )

    conn = get_connection("data/database/haruquantai.db")
    updated = update_host_setting(conn, "system", "theme", '{"theme": "dark"}')
    count = update_row_by_pk(
        conn, "host_jobs", {"job_id": "j-1"}, {"status": "completed"}
    )
    ```

CLI Usage:
    ```bash
    uv run python -c "from app.host.persistence.create import get_connection"
    ```
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from app.host.logging import get_logger
from app.host.persistence.create import (
    TABLE_PRIMARY_KEYS,
    PersistenceError,
    current_utc_iso,
    ensure_table_schema,
)
from app.host.persistence.read import resolve_connection

logger = get_logger(__name__)

UPDATE_FR = "FR-HOST-PERSISTENCE-UPDATE-BY-PK"
BATCH_SETTINGS_FR = "FR-HOST-PERSISTENCE-BATCH-SETTINGS-REVISION"
BATCH_SETTINGS_REVISION_FR = BATCH_SETTINGS_FR


class RevisionConflictError(PersistenceError):
    """Raised when an atomic settings batch update encounters a stale revision."""

    def __init__(self, expected_revision: int, current_revision: int) -> None:
        self.expected_revision = expected_revision
        self.current_revision = current_revision
        super().__init__(
            f"Settings revision conflict: expected revision {expected_revision}, "
            f"but current database revision is {current_revision}."
        )

    @property
    def expected(self) -> int:
        """Alias for expected_revision."""
        return self.expected_revision

    @property
    def current(self) -> int:
        """Alias for current_revision."""
        return self.current_revision


def update_row_by_pk(
    conn: sqlite3.Connection,
    table: str,
    pk_values: Mapping[str, Any],
    updates: Mapping[str, Any],
    *,
    commit: bool = True,
) -> int:
    """Update a row identified by its primary key with given column updates.

    Args:
        conn: Open SQLite connection.
        table: Target table name.
        pk_values: Mapping of primary key column names to target values.
        updates: Mapping of column names to update values.
        commit: Whether to commit the transaction immediately (default True).

    Returns:
        Number of rows updated (0 or 1).

    Raises:
        PersistenceError: If table is unapproved, primary key is incomplete,
            updates mapping is empty, or execution fails.
    """
    if table not in TABLE_PRIMARY_KEYS:
        logger.error(
            "%s: rejected update for unapproved table %s",
            UPDATE_FR,
            table,
            extra={"fr_id": UPDATE_FR, "table": table},
        )
        raise PersistenceError(f"Table '{table}' is not in approved table catalogue.")

    if not updates:
        logger.error(
            "%s: rejected update with empty values for table %s",
            UPDATE_FR,
            table,
            extra={"fr_id": UPDATE_FR, "table": table},
        )
        raise PersistenceError("Updates mapping cannot be empty.")

    expected_pks = TABLE_PRIMARY_KEYS[table]
    missing_pks = [pk for pk in expected_pks if pk not in pk_values]
    if missing_pks:
        logger.error(
            "%s: missing primary key columns %s for update on %s",
            UPDATE_FR,
            missing_pks,
            table,
            extra={"fr_id": UPDATE_FR, "table": table},
        )
        raise PersistenceError(
            f"Missing primary key columns for '{table}': {missing_pks}"
        )

    set_clauses = [f'"{col}" = ?' for col in updates]
    where_clauses = [f'"{pk}" = ?' for pk in expected_pks]
    set_str = ", ".join(set_clauses)
    where_str = " AND ".join(where_clauses)
    sql = f'UPDATE "{table}" SET {set_str} WHERE {where_str}'  # noqa: S608
    params = list(updates.values()) + [pk_values[pk] for pk in expected_pks]

    logger.debug(
        "%s: updating %s for pk %s (cols=%s)",
        UPDATE_FR,
        table,
        pk_values,
        list(updates.keys()),
        extra={"fr_id": UPDATE_FR, "table": table},
    )
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
        raise PersistenceError(f"Update on '{table}' failed: {err}") from err

    if affected == 0:
        logger.warning(
            "%s: update on %s matched 0 rows for pk %s",
            UPDATE_FR,
            table,
            pk_values,
            extra={"fr_id": UPDATE_FR, "table": table, "affected": 0},
        )
    else:
        logger.debug(
            "%s: update on %s succeeded (affected=%s)",
            UPDATE_FR,
            table,
            affected,
            extra={"fr_id": UPDATE_FR, "table": table, "affected": affected},
        )
    return affected


def update_record(
    conn: sqlite3.Connection,
    table: str,
    pk_values: Mapping[str, Any],
    updates: Mapping[str, Any],
    *,
    expected_revision: int | None = None,
    revision_col: str = "revision",
    commit: bool = True,
) -> int:
    """Update a row with optional optimistic revision verification.

    Canonical HostPersistence update function.

    Args:
        conn: Open SQLite connection.
        table: Target table name.
        pk_values: Mapping of primary key columns to values.
        updates: Mapping of column names to new values.
        expected_revision: Optional expected revision integer for CAS check.
        revision_col: Column name containing the revision (default 'revision').
        commit: Whether to commit the transaction immediately (default True).

    Returns:
        Number of rows updated (0 or 1).

    Raises:
        RevisionConflictError: When expected_revision does not match current state.
        PersistenceError: If table is unapproved or update fails.
    """
    if table not in TABLE_PRIMARY_KEYS:
        raise PersistenceError(f"Table '{table}' is not in approved table catalogue.")
    if not pk_values:
        raise PersistenceError(
            f"update_record requires non-empty pk_values for table '{table}'."
        )
    if not updates:
        raise PersistenceError(
            f"update_record requires non-empty update_values for table '{table}'."
        )

    if expected_revision is not None:
        cursor = conn.execute(f'PRAGMA table_info("{table}")')
        cols = {row[1] for row in cursor.fetchall()}
        if revision_col not in cols:
            raise PersistenceError(
                f"Table '{table}' does not contain revision column '{revision_col}'."
            )

        from app.host.persistence.read import read_row_by_pk

        current = read_row_by_pk(conn, table, pk_values)
        if current is not None:
            curr_rev = current.get(revision_col)
            if curr_rev is not None and int(curr_rev) != expected_revision:
                logger.warning(
                    "%s: update_record revision conflict on %s "
                    "(expected=%d, current=%d)",
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
                raise RevisionConflictError(
                    expected_revision=expected_revision,
                    current_revision=int(curr_rev),
                )

    return update_row_by_pk(conn, table, pk_values, updates, commit=commit)


def update_host_setting(
    conn: sqlite3.Connection,
    scope: str,
    key: str,
    value_json: str,
    *,
    schema_version: int | None = None,
    updated_at_utc: str | None = None,
) -> bool:
    """Update value and timestamp of a host setting."""
    updates: dict[str, Any] = {
        "value_json": value_json,
        "updated_at_utc": updated_at_utc or current_utc_iso(),
    }
    if schema_version is not None:
        updates["schema_version"] = schema_version
    affected = update_row_by_pk(
        conn, "host_settings", {"scope": scope, "key": key}, updates
    )
    return affected > 0


def _verify_settings_revision(expected_revision: int | None, current_rev: int) -> None:
    """Raise ``RevisionConflictError`` if ``expected_revision`` mismatches DB state."""
    if expected_revision is not None and expected_revision != current_rev:
        logger.warning(
            "%s: rejected batch settings save due to revision conflict "
            "(expected=%d, current=%d)",
            BATCH_SETTINGS_FR,
            expected_revision,
            current_rev,
            extra={
                "fr_id": BATCH_SETTINGS_FR,
                "expected_revision": expected_revision,
                "current_revision": current_rev,
            },
        )
        raise RevisionConflictError(
            expected_revision=expected_revision,
            current_revision=current_rev,
        )


def batch_save_host_settings(
    updates: Mapping[str, Mapping[str, Any]],
    *,
    expected_revision: int | None = None,
    conn: sqlite3.Connection | Path | str | None = None,
) -> int:
    """Atomically upsert settings after acquiring the SQLite writer reservation.

    Args:
        updates: Nested mapping of ``{scope: {key: value}}`` to persist.
        expected_revision: Optional revision expected by caller; raises
            ``RevisionConflictError`` if current DB revision differs.
        conn: Optional SQLite connection or database file path.

    Returns:
        Committed revision; an empty batch returns the unchanged revision.

    Raises:
        PersistenceError: Connection already has a transaction, or saving fails.
        RevisionConflictError: Expected revision differs from the locked snapshot.
    """
    with resolve_connection(conn) as active_conn:
        if active_conn.in_transaction:
            logger.error("%s: caller transaction is already active", BATCH_SETTINGS_FR)
            raise PersistenceError("Settings batches require an idle connection.")
        ensure_table_schema(active_conn, "host_settings")
        try:
            with active_conn:
                active_conn.execute("BEGIN IMMEDIATE")
                row = active_conn.execute(
                    "SELECT COALESCE(MAX(schema_version), 0) AS rev "
                    'FROM "host_settings"'
                ).fetchone()
                current_rev = int(row["rev"]) if row is not None else 0
                _verify_settings_revision(expected_revision, current_rev)

                next_rev = current_rev + int(any(updates.values()))
                now_iso = current_utc_iso()
                total_keys = 0
                for scope, scope_map in updates.items():
                    for key, raw_val in scope_map.items():
                        val_json = json.dumps(raw_val)
                        active_conn.execute(
                            'INSERT INTO "host_settings" '
                            "(scope, key, value_json, schema_version, updated_at_utc) "
                            "VALUES (?, ?, ?, ?, ?) "
                            "ON CONFLICT(scope, key) DO UPDATE SET "
                            "value_json = excluded.value_json, "
                            "schema_version = excluded.schema_version, "
                            "updated_at_utc = excluded.updated_at_utc",
                            (scope, key, val_json, next_rev, now_iso),
                        )
                        total_keys += 1

                if total_keys > 0:
                    active_conn.execute(
                        'UPDATE "host_settings" SET schema_version = ?',
                        (next_rev,),
                    )
        except (sqlite3.Error, TypeError, ValueError) as err:
            logger.exception(
                "%s: atomic batch settings save failed",
                BATCH_SETTINGS_FR,
                extra={"fr_id": BATCH_SETTINGS_FR, "error": str(err)},
            )
            raise PersistenceError(f"Batch settings save failed: {err}") from err

    logger.info(
        "%s: committed atomic batch settings update (keys=%d, revision=%d)",
        BATCH_SETTINGS_FR,
        total_keys,
        next_rev,
        extra={
            "fr_id": BATCH_SETTINGS_FR,
            "keys": total_keys,
            "revision": next_rev,
        },
    )
    return next_rev


def save_host_session(
    session_id: str,
    token_hash: str,
    username: str,
    peer_id: str,
    created_at_utc: str,
    *,
    expires_at_utc: str,
    status: str = "ACTIVE",
    revoked_at_utc: str | None = None,
    conn: sqlite3.Connection | Path | str | None = None,
) -> bool:
    """Save or upsert a host session record."""
    with resolve_connection(conn) as active_conn:
        ensure_table_schema(active_conn, "host_session")
        active_conn.execute(
            "INSERT INTO host_session "
            "(session_id, token_hash, username, peer_id, "
            "created_at_utc, expires_at_utc, revoked_at_utc, status) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(session_id) DO UPDATE SET "
            "status=excluded.status, "
            "revoked_at_utc=excluded.revoked_at_utc",
            (
                session_id,
                token_hash,
                username,
                peer_id,
                created_at_utc,
                expires_at_utc,
                revoked_at_utc,
                status,
            ),
        )
        active_conn.commit()
        return True


def update_host_session_status(
    conn_or_session_id: sqlite3.Connection | Path | str | None = None,
    session_id_or_status: str | None = None,
    status: str | None = None,
    *,
    revoked_at_utc: str | None = None,
    conn: sqlite3.Connection | Path | str | None = None,
) -> bool:
    """Update status and optional revocation timestamp of a host session."""
    active_conn = conn
    target_id: str | None = None
    target_status: str | None = status

    if isinstance(conn_or_session_id, (sqlite3.Connection, Path)):
        active_conn = conn_or_session_id
        target_id = session_id_or_status
    elif isinstance(conn_or_session_id, str):
        if status is None and session_id_or_status is not None:
            target_id = conn_or_session_id
            target_status = session_id_or_status
        else:
            active_conn = conn_or_session_id
            target_id = session_id_or_status

    if target_id is None or target_status is None:
        raise PersistenceError(
            "session_id and status must be provided to update_host_session_status"
        )

    updates: dict[str, Any] = {"status": target_status}
    if revoked_at_utc is not None:
        updates["revoked_at_utc"] = revoked_at_utc

    with resolve_connection(active_conn) as c:
        affected = update_row_by_pk(
            c, "host_session", {"session_id": target_id}, updates
        )
        return affected > 0


update_host_session = update_host_session_status


def save_host_job(
    job_id: str,
    *,
    owner: str = "default",
    kind: str = "compute",
    status: str = "QUEUED",
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
    submitted_at_utc: str | None = None,
    started_at_utc: str | None = None,
    finished_at_utc: str | None = None,
    error_message: str | None = None,
    error_location: str | None = None,
    conn: sqlite3.Connection | Path | str | None = None,
) -> bool:
    """Save or upsert a host job record."""
    with resolve_connection(conn) as active_conn:
        ensure_table_schema(active_conn, "host_jobs")
        effective_submitted = submitted_at_utc or current_utc_iso()
        active_conn.execute(
            'INSERT INTO "host_jobs" ('
            "job_id, owner, kind, status, progress, accepted, rejected, message, "
            "attempt_id, max_retries, retry_count, dedup_key, parent_job_id, "
            "child_job_ids_json, budget_json, submitted_at_utc, started_at_utc, "
            "finished_at_utc, error_message, error_location"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(job_id) DO UPDATE SET "
            "status=excluded.status, "
            "progress=excluded.progress, "
            "accepted=excluded.accepted, "
            "rejected=excluded.rejected, "
            "message=excluded.message, "
            "attempt_id=excluded.attempt_id, "
            "retry_count=excluded.retry_count, "
            "started_at_utc=excluded.started_at_utc, "
            "finished_at_utc=excluded.finished_at_utc, "
            "error_message=excluded.error_message, "
            "error_location=excluded.error_location",
            (
                job_id,
                owner,
                kind,
                status,
                progress,
                accepted,
                rejected,
                message,
                attempt_id,
                max_retries,
                retry_count,
                dedup_key,
                parent_job_id,
                child_job_ids_json,
                budget_json,
                effective_submitted,
                started_at_utc,
                finished_at_utc,
                error_message,
                error_location,
            ),
        )
        active_conn.commit()
        return True


def record_host_job_event(
    event_id: str,
    job_id: str,
    to_state: str,
    *,
    from_state: str | None = None,
    attempt_id: str | None = None,
    details_json: str = "{}",
    created_at_utc: str | None = None,
    conn: sqlite3.Connection | Path | str | None = None,
) -> bool:
    """Record a state transition event in host_job_events."""
    with resolve_connection(conn) as active_conn:
        ensure_table_schema(active_conn, "host_job_events")
        effective_created = created_at_utc or current_utc_iso()
        active_conn.execute(
            'INSERT OR REPLACE INTO "host_job_events" '
            "(event_id, job_id, attempt_id, from_state, to_state, "
            "details_json, created_at_utc) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                event_id,
                job_id,
                attempt_id,
                from_state,
                to_state,
                details_json,
                effective_created,
            ),
        )
        active_conn.commit()
        return True


def update_host_job(
    conn_or_job_id: sqlite3.Connection | Path | str | None = None,
    job_id_or_updates: str | Mapping[str, Any] | None = None,
    updates: Mapping[str, Any] | None = None,
    *,
    conn: sqlite3.Connection | Path | str | None = None,
) -> bool:
    """Update attributes of a host job."""
    active_conn = conn
    target_id: str | None = None
    target_updates: Mapping[str, Any] | None = updates

    if isinstance(conn_or_job_id, (sqlite3.Connection, Path)):
        active_conn = conn_or_job_id
        if isinstance(job_id_or_updates, str):
            target_id = job_id_or_updates
    elif isinstance(conn_or_job_id, str):
        if isinstance(job_id_or_updates, Mapping) and updates is None:
            target_id = conn_or_job_id
            target_updates = job_id_or_updates
        elif isinstance(job_id_or_updates, str):
            active_conn = conn_or_job_id
            target_id = job_id_or_updates

    if target_id is None or target_updates is None:
        raise PersistenceError("job_id and updates must be provided to update_host_job")

    with resolve_connection(active_conn) as c:
        affected = update_row_by_pk(
            c, "host_jobs", {"job_id": target_id}, target_updates
        )
        return affected > 0


def update_host_job_attempt(
    conn: sqlite3.Connection,
    attempt_id: str,
    updates: Mapping[str, Any],
) -> bool:
    """Update state or completion of a host job attempt."""
    affected = update_row_by_pk(
        conn, "host_job_attempts", {"attempt_id": attempt_id}, updates
    )
    return affected > 0


def update_entity(
    conn: sqlite3.Connection,
    entity_id: str,
    entity_type: str,
    payload: str,
    *,
    revision: int | None = None,
    expected_revision: int | None = None,
    updated_at_utc: str | None = None,
) -> bool:
    """Update payload and revision of a host entity with optimistic CAS.

    Canonical HostPersistence entity update function.

    Args:
        conn: Open SQLite connection.
        entity_id: Target entity identifier.
        entity_type: Target entity domain type.
        payload: New payload text or JSON string.
        revision: Explicit new revision integer, or None to auto-increment.
        expected_revision: Optional expected revision to compare-and-set.
        updated_at_utc: Optional update timestamp.

    Returns:
        True if the row was updated, False otherwise.

    Raises:
        RevisionConflictError: When expected_revision does not match current state.
        PersistenceError: When update fails.
    """
    from app.host.persistence.read import read_row_by_pk

    pk = {"entity_id": entity_id, "entity_type": entity_type}
    current = read_row_by_pk(conn, "host_entities", pk)
    if current is None:
        logger.warning(
            "%s: entity not found for update (%s, %s)",
            UPDATE_FR,
            entity_id,
            entity_type,
            extra={
                "fr_id": UPDATE_FR,
                "entity_id": entity_id,
                "entity_type": entity_type,
            },
        )
        return False

    current_rev = int(current["revision"])
    if expected_revision is not None and expected_revision != current_rev:
        logger.warning(
            "%s: entity revision conflict on (%s, %s) (expected=%d, current=%d)",
            UPDATE_FR,
            entity_id,
            entity_type,
            expected_revision,
            current_rev,
            extra={
                "fr_id": UPDATE_FR,
                "entity_id": entity_id,
                "entity_type": entity_type,
                "expected_revision": expected_revision,
                "current_revision": current_rev,
            },
        )
        raise RevisionConflictError(
            expected_revision=expected_revision,
            current_revision=current_rev,
        )

    next_rev = revision if revision is not None else (current_rev + 1)
    updates = {
        "payload": payload,
        "revision": next_rev,
        "updated_at_utc": updated_at_utc or current_utc_iso(),
    }
    affected = update_row_by_pk(conn, "host_entities", pk, updates)
    return affected > 0


def update_host_entity(
    conn: sqlite3.Connection,
    entity_id: str,
    entity_type: str,
    payload: str,
    revision: int | None = None,
    *,
    expected_revision: int | None = None,
    updated_at_utc: str | None = None,
) -> bool:
    """Update payload and revision of a host entity."""
    return update_entity(
        conn,
        entity_id,
        entity_type,
        payload,
        revision=revision,
        expected_revision=expected_revision,
        updated_at_utc=updated_at_utc,
    )


def update_host_grid_node_heartbeat(
    conn: sqlite3.Connection,
    node_id: str,
    state: str,
    heartbeat_at_utc: str,
) -> bool:
    """Update state and heartbeat timestamp for a grid compute node."""
    updates = {
        "state": state,
        "last_heartbeat_utc": heartbeat_at_utc,
    }
    affected = update_row_by_pk(conn, "host_grid_nodes", {"node_id": node_id}, updates)
    return affected > 0


def update_datamgr_broker(
    conn: sqlite3.Connection,
    broker_id: int,
    updates: Mapping[str, Any],
) -> bool:
    """Update fields of a datamgr broker."""
    affected = update_row_by_pk(conn, "datamgr_broker", {"id": broker_id}, updates)
    return affected > 0


def update_datamgr_dataset(
    conn: sqlite3.Connection,
    dataset_id: str,
    updates: Mapping[str, Any],
) -> bool:
    """Update fields of a datamgr dataset."""
    affected = update_row_by_pk(conn, "datamgr_datasets", {"id": dataset_id}, updates)
    return affected > 0


def update_datamgr_instrument(
    conn: sqlite3.Connection | Path | str | None = None,
    symbol: str = "",
    updates: Mapping[str, Any] | None = None,
) -> bool:
    """Update fields of a datamgr instrument identified by symbol."""
    from app.host.persistence.read import get_datamgr_instrument

    with resolve_connection(conn) as active_conn:
        current = get_datamgr_instrument(active_conn, symbol)
        if current is None:
            logger.warning(
                "%s: instrument '%s' not found for update",
                UPDATE_FR,
                symbol,
                extra={"fr_id": UPDATE_FR, "symbol": symbol},
            )
            return False
        affected = update_row_by_pk(
            active_conn, "datamgr_instruments", {"id": current["id"]}, updates or {}
        )
    return affected > 0


def update_datamgr_session(
    conn: sqlite3.Connection | Path | str | None = None,
    name_or_id: str | int = "",
    updates: Mapping[str, Any] | None = None,
) -> bool:
    """Update trading session schedule or configuration."""
    from app.host.persistence.read import get_datamgr_session

    with resolve_connection(conn) as active_conn:
        current = get_datamgr_session(active_conn, name_or_id)
        if current is None:
            logger.warning(
                "%s: session '%s' not found for update",
                UPDATE_FR,
                name_or_id,
                extra={"fr_id": UPDATE_FR, "session": name_or_id},
            )
            return False
        affected = update_row_by_pk(
            active_conn, "datamgr_sessions", {"id": current["id"]}, updates or {}
        )
    return affected > 0


def update_mt5_command(
    conn: sqlite3.Connection,
    command_id: str,
    status: str,
    *,
    resolved_at: float | None = None,
    value_json: str | None = None,
    error_json: str | None = None,
) -> bool:
    """Update execution status and results of an MT5 command."""
    updates: dict[str, Any] = {"status": status}
    if resolved_at is not None:
        updates["resolved_at"] = resolved_at
    if value_json is not None:
        updates["value_json"] = value_json
    if error_json is not None:
        updates["error_json"] = error_json
    affected = update_row_by_pk(
        conn, "mt5_commands", {"command_id": command_id}, updates
    )
    return affected > 0


def update_datamgr_broker_stock(
    conn: sqlite3.Connection,
    stock_id: int,
    updates: Mapping[str, Any],
) -> bool:
    """Update fields of a datamgr broker stock record."""
    affected = update_row_by_pk(conn, "datamgr_broker_stock", {"ID": stock_id}, updates)
    return affected > 0


def update_datamgr_commodity(
    conn: sqlite3.Connection,
    commodity_id: int,
    updates: Mapping[str, Any],
) -> bool:
    """Update fields of a commodity record."""
    affected = update_row_by_pk(
        conn, "datamgr_commodities", {"id": commodity_id}, updates
    )
    return affected > 0


def update_datamgr_crypto_catalog(
    conn: sqlite3.Connection,
    exchange: str,
    symbol: str,
    updates: Mapping[str, Any],
) -> bool:
    """Update fields of a crypto catalog entry."""
    affected = update_row_by_pk(
        conn,
        "datamgr_crypto_catalog",
        {"exchange": exchange, "symbol": symbol},
        updates,
    )
    return affected > 0


def update_datamgr_log(
    conn: sqlite3.Connection,
    log_id: int,
    updates: Mapping[str, Any],
) -> bool:
    """Update fields of a datamgr log record."""
    affected = update_row_by_pk(conn, "datamgr_logs", {"id": log_id}, updates)
    return affected > 0


def update_datamgr_operation_log(
    conn: sqlite3.Connection,
    op_id: int,
    updates: Mapping[str, Any],
) -> bool:
    """Update fields of a datamgr operation log record."""
    affected = update_row_by_pk(conn, "datamgr_operation_log", {"id": op_id}, updates)
    return affected > 0


def update_datamgr_quality_report(
    conn: sqlite3.Connection,
    report_id: str,
    updates: Mapping[str, Any],
) -> bool:
    """Update fields of a quality report."""
    affected = update_row_by_pk(
        conn, "datamgr_quality", {"report_id": report_id}, updates
    )
    return affected > 0


def update_datamgr_stock(
    conn: sqlite3.Connection,
    stock_id: int,
    updates: Mapping[str, Any],
) -> bool:
    """Update fields of a datamgr stock record."""
    affected = update_row_by_pk(conn, "datamgr_stock", {"ID": stock_id}, updates)
    return affected > 0


def update_datamgr_stock_group(
    conn: sqlite3.Connection,
    group_id: int,
    updates: Mapping[str, Any],
) -> bool:
    """Update fields of a datamgr stock group."""
    affected = update_row_by_pk(conn, "datamgr_stock_group", {"ID": group_id}, updates)
    return affected > 0


def update_datamgr_ticker(
    conn: sqlite3.Connection,
    ticker_id: int,
    updates: Mapping[str, Any],
) -> bool:
    """Update fields of a datamgr ticker."""
    affected = update_row_by_pk(conn, "datamgr_tickers", {"id": ticker_id}, updates)
    return affected > 0


def update_host_grid_lease(
    conn: sqlite3.Connection,
    lease_id: str,
    updates: Mapping[str, Any],
) -> bool:
    """Update fields of a grid lease."""
    affected = update_row_by_pk(
        conn, "host_grid_leases", {"lease_id": lease_id}, updates
    )
    return affected > 0


def update_host_grid_node(
    conn: sqlite3.Connection,
    node_id: str,
    updates: Mapping[str, Any],
) -> bool:
    """Update attributes of a grid node."""
    affected = update_row_by_pk(conn, "host_grid_nodes", {"node_id": node_id}, updates)
    return affected > 0


def update_host_job_event(
    conn: sqlite3.Connection,
    event_id: str,
    updates: Mapping[str, Any],
) -> bool:
    """Update attributes of a host job event."""
    affected = update_row_by_pk(
        conn, "host_job_events", {"event_id": event_id}, updates
    )
    return affected > 0


def update_host_lease(
    conn: sqlite3.Connection,
    lease_key: str,
    updates: Mapping[str, Any],
) -> bool:
    """Update attributes of a host lease."""
    affected = update_row_by_pk(conn, "host_leases", {"lease_key": lease_key}, updates)
    return affected > 0


def update_mt5_event(
    conn: sqlite3.Connection,
    event_id: int,
    updates: Mapping[str, Any],
) -> bool:
    """Update attributes of an MT5 event."""
    affected = update_row_by_pk(conn, "mt5_events", {"event_id": event_id}, updates)
    return affected > 0


def update_schema_migration(
    conn: sqlite3.Connection,
    version: int,
    updates: Mapping[str, Any],
) -> bool:
    """Update attributes of a schema migration."""
    affected = update_row_by_pk(
        conn, "schema_migrations", {"version": version}, updates
    )
    return affected > 0
