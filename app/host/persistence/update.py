# ruff: noqa: INP001
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
    - FR-HOST-PERSISTENCE-UPDATE-BY-PK: Atomic record update targeting table PK.
      Associated: `update_row_by_pk()`, `update_host_setting()`,
      `update_host_session_status()`, `update_host_job()`, `update_datamgr_broker()`,
      `update_datamgr_dataset()`, `update_datamgr_instrument()`
      Logging: DEBUG emitted on successful update with affected row count; WARNING
      when no rows matched; ERROR on constraint or execution failure.

Python API Usage:
    ```python
    from app.host.persistence.create import get_connection
    from app.host.persistence.update import update_host_setting, update_row_by_pk

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

import logging
import sqlite3
from collections.abc import Mapping
from typing import Any

from app.host.persistence.create import (
    TABLE_PRIMARY_KEYS,
    PersistenceError,
    current_utc_iso,
)

logger = logging.getLogger(__name__)

UPDATE_FR = "FR-HOST-PERSISTENCE-UPDATE-BY-PK"


def update_row_by_pk(
    conn: sqlite3.Connection,
    table: str,
    pk_values: Mapping[str, Any],
    updates: Mapping[str, Any],
) -> int:
    """Update a row identified by its primary key with given column updates.

    Args:
        conn: Open SQLite connection.
        table: Target table name.
        pk_values: Mapping of primary key column names to target values.
        updates: Mapping of column names to update values.

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
        with conn:
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


def update_host_session_status(
    conn: sqlite3.Connection,
    session_id: str,
    status: str,
    *,
    revoked_at_utc: str | None = None,
) -> bool:
    """Update status and optional revocation timestamp of a host session."""
    updates: dict[str, Any] = {"status": status}
    if revoked_at_utc is not None:
        updates["revoked_at_utc"] = revoked_at_utc
    affected = update_row_by_pk(
        conn, "host_session", {"session_id": session_id}, updates
    )
    return affected > 0


def update_host_job(
    conn: sqlite3.Connection,
    job_id: str,
    updates: Mapping[str, Any],
) -> bool:
    """Update attributes of a host job."""
    affected = update_row_by_pk(conn, "host_jobs", {"job_id": job_id}, updates)
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


def update_host_entity(
    conn: sqlite3.Connection,
    entity_id: str,
    entity_type: str,
    payload: str,
    revision: int,
    *,
    updated_at_utc: str | None = None,
) -> bool:
    """Update payload and revision of a host entity."""
    updates = {
        "payload": payload,
        "revision": revision,
        "updated_at_utc": updated_at_utc or current_utc_iso(),
    }
    affected = update_row_by_pk(
        conn,
        "host_entities",
        {"entity_id": entity_id, "entity_type": entity_type},
        updates,
    )
    return affected > 0


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
    conn: sqlite3.Connection,
    symbol: str,
    updates: Mapping[str, Any],
) -> bool:
    """Update fields of a datamgr instrument identified by symbol."""
    from app.host.persistence.read import get_datamgr_instrument

    current = get_datamgr_instrument(conn, symbol)
    if current is None:
        logger.warning(
            "%s: instrument '%s' not found for update",
            UPDATE_FR,
            symbol,
            extra={"fr_id": UPDATE_FR, "symbol": symbol},
        )
        return False
    affected = update_row_by_pk(
        conn, "datamgr_instruments", {"id": current["id"]}, updates
    )
    return affected > 0


def update_datamgr_session(
    conn: sqlite3.Connection,
    session_id: int,
    updates: Mapping[str, Any],
) -> bool:
    """Update trading session schedule or configuration."""
    affected = update_row_by_pk(conn, "datamgr_sessions", {"id": session_id}, updates)
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
