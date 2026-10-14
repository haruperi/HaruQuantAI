# ruff: noqa: INP001
"""Delete operations for operational database tables.

Description:
    Provides parameterized delete operations for database tables in HaruQuantAI.
    Ensures safe, bounded record removal by targeting rows strictly through
    primary keys or explicit non-empty condition mappings. Foreign key constraints
    are enforced under WAL mode. Non-silent structured logging records every
    deletion with affected counts.

Purpose:
    FEAT-HOST-PERSISTENCE: Host platform and workspace isolated SQLite persistence.

Key Capabilities:
    - FR-HOST-PERSISTENCE-DELETE-BY-PK: Delete record targeting table primary key.
      Associated: `delete_row_by_pk()`, `delete_host_setting()`,
      `delete_host_session()`, `delete_host_job()`, `delete_datamgr_broker()`,
      `delete_datamgr_dataset()`, `delete_datamgr_instrument()`
      Logging: DEBUG emitted on successful deletion with affected row count; WARNING
      when no rows matched; ERROR on constraint or execution failure.
    - FR-HOST-PERSISTENCE-DELETE-WHERE: Delete records matching filter criteria.
      Associated: `delete_rows()`
      Logging: DEBUG emitted on deletion with affected row count; ERROR on failure.

Python API Usage:
    ```python
    from app.host.persistence.create import get_connection
    from app.host.persistence.delete import delete_host_setting, delete_row_by_pk

    conn = get_connection("data/database/haruquantai.db")
    deleted = delete_host_setting(conn, "system", "theme")
    count = delete_row_by_pk(conn, "host_jobs", {"job_id": "j-1"})
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

from app.host.persistence.create import TABLE_PRIMARY_KEYS, PersistenceError

logger = logging.getLogger(__name__)

DELETE_PK_FR = "FR-HOST-PERSISTENCE-DELETE-BY-PK"
DELETE_WHERE_FR = "FR-HOST-PERSISTENCE-DELETE-WHERE"


def delete_row_by_pk(
    conn: sqlite3.Connection,
    table: str,
    pk_values: Mapping[str, Any],
) -> int:
    """Delete a row identified by its primary key.

    Args:
        conn: Open SQLite connection.
        table: Target table name.
        pk_values: Mapping of primary key column names to target values.

    Returns:
        Number of rows deleted (0 or 1).

    Raises:
        PersistenceError: If table is unapproved, primary key is incomplete,
            or execution fails.
    """
    if table not in TABLE_PRIMARY_KEYS:
        logger.error(
            "%s: rejected delete for unapproved table %s",
            DELETE_PK_FR,
            table,
            extra={"fr_id": DELETE_PK_FR, "table": table},
        )
        raise PersistenceError(f"Table '{table}' is not in approved table catalogue.")

    expected_pks = TABLE_PRIMARY_KEYS[table]
    missing_pks = [pk for pk in expected_pks if pk not in pk_values]
    if missing_pks:
        logger.error(
            "%s: missing primary key columns %s for delete on %s",
            DELETE_PK_FR,
            missing_pks,
            table,
            extra={"fr_id": DELETE_PK_FR, "table": table},
        )
        raise PersistenceError(
            f"Missing primary key columns for '{table}': {missing_pks}"
        )

    where_clauses = [f'"{pk}" = ?' for pk in expected_pks]
    where_str = " AND ".join(where_clauses)
    sql = f'DELETE FROM "{table}" WHERE {where_str}'  # noqa: S608
    params = [pk_values[pk] for pk in expected_pks]

    logger.debug(
        "%s: deleting from %s for pk %s",
        DELETE_PK_FR,
        table,
        pk_values,
        extra={"fr_id": DELETE_PK_FR, "table": table},
    )
    try:
        with conn:
            cursor = conn.execute(sql, params)
            deleted = cursor.rowcount
    except sqlite3.Error as err:
        logger.exception(
            "%s: delete failed on %s",
            DELETE_PK_FR,
            table,
            extra={"fr_id": DELETE_PK_FR, "table": table, "error": str(err)},
        )
        raise PersistenceError(f"Delete on '{table}' failed: {err}") from err

    if deleted == 0:
        logger.warning(
            "%s: delete on %s matched 0 rows for pk %s",
            DELETE_PK_FR,
            table,
            pk_values,
            extra={"fr_id": DELETE_PK_FR, "table": table, "deleted": 0},
        )
    else:
        logger.debug(
            "%s: delete on %s succeeded (deleted=%s)",
            DELETE_PK_FR,
            table,
            deleted,
            extra={"fr_id": DELETE_PK_FR, "table": table, "deleted": deleted},
        )
    return deleted


def delete_rows(
    conn: sqlite3.Connection,
    table: str,
    where: Mapping[str, Any],
) -> int:
    """Delete rows matching filter criteria from an approved table.

    Args:
        conn: Open SQLite connection.
        table: Target table name.
        where: Non-empty mapping of column names to filter values.

    Returns:
        Number of rows deleted.

    Raises:
        PersistenceError: If table is unapproved, where mapping is empty,
            or execution fails.
    """
    if table not in TABLE_PRIMARY_KEYS:
        logger.error(
            "%s: rejected delete for unapproved table %s",
            DELETE_WHERE_FR,
            table,
            extra={"fr_id": DELETE_WHERE_FR, "table": table},
        )
        raise PersistenceError(f"Table '{table}' is not in approved table catalogue.")

    if not where:
        logger.error(
            "%s: rejected unbounded delete with empty where mapping for %s",
            DELETE_WHERE_FR,
            table,
            extra={"fr_id": DELETE_WHERE_FR, "table": table},
        )
        raise PersistenceError("Delete requires non-empty where filter mapping.")

    clauses: list[str] = []
    params: list[Any] = []
    for col, val in where.items():
        if val is None:
            clauses.append(f'"{col}" IS NULL')
        else:
            clauses.append(f'"{col}" = ?')
            params.append(val)

    where_str = " AND ".join(clauses)
    sql = f'DELETE FROM "{table}" WHERE {where_str}'  # noqa: S608
    logger.debug(
        "%s: deleting from %s with filter %s",
        DELETE_WHERE_FR,
        table,
        where,
        extra={"fr_id": DELETE_WHERE_FR, "table": table},
    )
    try:
        with conn:
            cursor = conn.execute(sql, params)
            deleted = cursor.rowcount
    except sqlite3.Error as err:
        logger.exception(
            "%s: delete failed on %s",
            DELETE_WHERE_FR,
            table,
            extra={"fr_id": DELETE_WHERE_FR, "table": table, "error": str(err)},
        )
        raise PersistenceError(f"Delete on '{table}' failed: {err}") from err

    logger.debug(
        "%s: deleted %s rows from %s",
        DELETE_WHERE_FR,
        deleted,
        table,
        extra={"fr_id": DELETE_WHERE_FR, "table": table, "deleted": deleted},
    )
    return deleted


def delete_host_setting(
    conn: sqlite3.Connection,
    scope: str,
    key: str,
) -> bool:
    """Delete a host setting by its composite key (scope, key)."""
    deleted = delete_row_by_pk(conn, "host_settings", {"scope": scope, "key": key})
    return deleted > 0


def delete_host_session(
    conn: sqlite3.Connection,
    session_id: str,
) -> bool:
    """Delete a host session record by session ID."""
    deleted = delete_row_by_pk(conn, "host_session", {"session_id": session_id})
    return deleted > 0


def delete_host_job(
    conn: sqlite3.Connection,
    job_id: str,
) -> bool:
    """Delete a host job by job ID."""
    deleted = delete_row_by_pk(conn, "host_jobs", {"job_id": job_id})
    return deleted > 0


def delete_host_entity(
    conn: sqlite3.Connection,
    entity_id: str,
    entity_type: str,
) -> bool:
    """Delete a host entity by composite key (entity_id, entity_type)."""
    deleted = delete_row_by_pk(
        conn,
        "host_entities",
        {"entity_id": entity_id, "entity_type": entity_type},
    )
    return deleted > 0


def delete_host_lease(
    conn: sqlite3.Connection,
    lease_key: str,
) -> bool:
    """Delete a host lease by lease key."""
    deleted = delete_row_by_pk(conn, "host_leases", {"lease_key": lease_key})
    return deleted > 0


def delete_host_grid_node(
    conn: sqlite3.Connection,
    node_id: str,
) -> bool:
    """Delete a host grid node by node ID."""
    deleted = delete_row_by_pk(conn, "host_grid_nodes", {"node_id": node_id})
    return deleted > 0


def delete_datamgr_broker(
    conn: sqlite3.Connection,
    broker_id: int,
) -> bool:
    """Delete a datamgr broker by integer ID."""
    deleted = delete_row_by_pk(conn, "datamgr_broker", {"id": broker_id})
    return deleted > 0


def delete_datamgr_dataset(
    conn: sqlite3.Connection,
    dataset_id: str,
) -> bool:
    """Delete a datamgr dataset by dataset ID."""
    deleted = delete_row_by_pk(conn, "datamgr_datasets", {"id": dataset_id})
    return deleted > 0


def delete_datamgr_instrument(
    conn: sqlite3.Connection,
    symbol: str,
) -> bool:
    """Delete a datamgr instrument identified by symbol."""
    from app.host.persistence.read import get_datamgr_instrument

    current = get_datamgr_instrument(conn, symbol)
    if current is None:
        logger.warning(
            "%s: instrument '%s' not found for delete",
            DELETE_PK_FR,
            symbol,
            extra={"fr_id": DELETE_PK_FR, "symbol": symbol},
        )
        return False
    deleted = delete_row_by_pk(conn, "datamgr_instruments", {"id": current["id"]})
    return deleted > 0


def delete_datamgr_session(
    conn: sqlite3.Connection,
    session_id: int,
) -> bool:
    """Delete a trading session by ID."""
    deleted = delete_row_by_pk(conn, "datamgr_sessions", {"id": session_id})
    return deleted > 0


def delete_mt5_command(
    conn: sqlite3.Connection,
    command_id: str,
) -> bool:
    """Delete an MT5 command by command ID."""
    deleted = delete_row_by_pk(conn, "mt5_commands", {"command_id": command_id})
    return deleted > 0
