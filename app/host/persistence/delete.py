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
    - FR-HOST-PERSISTENCE-DELETE-BY-PK: Delete record targeting table primary key
      with foreign-key reference guards.
      Associated: `delete_row_by_pk()`, `delete_record()`, `delete_entity()`,
      and 25 domain-specific delete helpers.
      Logging: DEBUG emitted on successful deletion with affected row count; WARNING
      when no rows matched; ERROR on constraint or execution failure.
    - FR-HOST-PERSISTENCE-DELETE-WHERE: Delete records matching filter criteria.
      Associated: `delete_rows()`
      Logging: DEBUG emitted on deletion with affected row count; ERROR on failure.

Python API Usage:
    ```python
    from app.host.persistence.create import get_connection
    from app.host.persistence.delete import (
        delete_entity,
        delete_host_setting,
        delete_record,
        delete_row_by_pk,
    )

    conn = get_connection("data/database/haruquantai.db")
    deleted = delete_host_setting(conn, "system", "theme")
    count = delete_record(conn, "host_jobs", {"job_id": "j-1"})
    ```

CLI Usage:
    ```bash
    uv run python -c "from app.host.persistence.create import get_connection"
    ```
"""

from __future__ import annotations

import sqlite3
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from app.host.logging import get_logger
from app.host.persistence.create import TABLE_PRIMARY_KEYS, PersistenceError
from app.host.persistence.read import resolve_connection

logger = get_logger(__name__)

DELETE_PK_FR = "FR-HOST-PERSISTENCE-DELETE-BY-PK"
DELETE_WHERE_FR = "FR-HOST-PERSISTENCE-DELETE-WHERE"

TABLE_FOREIGN_KEY_GUARDS: dict[str, list[tuple[str, str, str]]] = {
    "datamgr_broker": [("datamgr_broker_stock", "BROKER_ID", "id")],
    "datamgr_stock_group": [("datamgr_stock", "BASKET_ID", "ID")],
    "host_jobs": [
        ("host_grid_leases", "job_id", "job_id"),
        ("host_job_attempts", "job_id", "job_id"),
    ],
    "host_grid_nodes": [("host_grid_leases", "node_id", "node_id")],
}


def delete_row_by_pk(
    conn: sqlite3.Connection,
    table: str,
    pk_values: Mapping[str, Any],
    *,
    commit: bool = True,
) -> int:
    """Delete a row identified by its primary key.

    Args:
        conn: Open SQLite connection.
        table: Target table name.
        pk_values: Mapping of primary key column names to target values.
        commit: Whether to commit the transaction immediately (default True).

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

    if table in TABLE_FOREIGN_KEY_GUARDS:
        for child_table, child_fk_col, parent_pk_col in TABLE_FOREIGN_KEY_GUARDS[table]:
            if parent_pk_col in pk_values:
                parent_val = pk_values[parent_pk_col]
                cursor = conn.execute(
                    f'SELECT COUNT(*) FROM "{child_table}" WHERE "{child_fk_col}" = ?',  # noqa: S608
                    (parent_val,),
                )
                child_count = int(cursor.fetchone()[0])
                if child_count > 0:
                    logger.error(
                        "%s: delete blocked by foreign key guard on %s "
                        "(dependent rows in %s: %d)",
                        DELETE_PK_FR,
                        table,
                        child_table,
                        child_count,
                        extra={
                            "fr_id": DELETE_PK_FR,
                            "table": table,
                            "child_table": child_table,
                            "count": child_count,
                        },
                    )
                    raise PersistenceError(
                        f"Deletion blocked for '{table}': {child_count} dependent "
                        f"row(s) exist in '{child_table}'."
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


def delete_record(
    conn: sqlite3.Connection,
    table: str,
    pk_values: Mapping[str, Any],
    *,
    commit: bool = True,
) -> int:
    """Delete a single record with foreign-key reference guards.

    Canonical HostPersistence delete function.

    Args:
        conn: Open SQLite connection.
        table: Target table name.
        pk_values: Mapping of primary key columns to values.
        commit: Whether to commit the transaction immediately (default True).

    Returns:
        Number of rows deleted (0 or 1).

    Raises:
        PersistenceError: When dependent foreign key child rows exist,
            table is unapproved, pk_values is empty, or delete fails.
    """
    if table not in TABLE_PRIMARY_KEYS:
        raise PersistenceError(f"Table '{table}' is not in approved table catalogue.")
    if not pk_values:
        raise PersistenceError(
            f"delete_record requires non-empty pk_values for table '{table}'."
        )

    return delete_row_by_pk(conn, table, pk_values, commit=commit)


def delete_entity(
    conn: sqlite3.Connection,
    entity_id: str,
    entity_type: str,
) -> bool:
    """Delete a persistent host entity by composite key (canonical HostPersistence).

    Args:
        conn: Open SQLite connection.
        entity_id: Target entity identifier.
        entity_type: Target entity domain type.

    Returns:
        True if the entity was deleted, False otherwise.
    """
    deleted = delete_record(
        conn,
        "host_entities",
        {"entity_id": entity_id, "entity_type": entity_type},
    )
    return deleted > 0


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
    conn_or_job_id: sqlite3.Connection | Path | str | None = None,
    job_id: str | None = None,
    *,
    conn: sqlite3.Connection | Path | str | None = None,
) -> bool:
    """Delete a host job by job ID."""
    active_conn = conn
    target_id = job_id

    if isinstance(conn_or_job_id, (sqlite3.Connection, Path)):
        active_conn = conn_or_job_id
    elif isinstance(conn_or_job_id, str):
        if job_id is None:
            target_id = conn_or_job_id
        else:
            active_conn = conn_or_job_id

    if target_id is None:
        raise PersistenceError("job_id must be provided to delete_host_job")

    with resolve_connection(active_conn) as c:
        deleted = delete_row_by_pk(c, "host_jobs", {"job_id": target_id})
        return deleted > 0


def delete_host_entity(
    conn: sqlite3.Connection,
    entity_id: str,
    entity_type: str,
) -> bool:
    """Delete a host entity by composite key (entity_id, entity_type)."""
    return delete_entity(conn, entity_id, entity_type)


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
    conn: sqlite3.Connection | Path | str | None = None,
    symbol: str = "",
) -> bool:
    """Delete a datamgr instrument identified by symbol."""
    from app.host.persistence.read import get_datamgr_instrument

    with resolve_connection(conn) as active_conn:
        current = get_datamgr_instrument(active_conn, symbol)
        if current is None:
            logger.warning(
                "%s: instrument '%s' not found for delete",
                DELETE_PK_FR,
                symbol,
                extra={"fr_id": DELETE_PK_FR, "symbol": symbol},
            )
            return False
        deleted = delete_row_by_pk(
            active_conn, "datamgr_instruments", {"id": current["id"]}
        )
    return deleted > 0


def delete_datamgr_session(
    conn: sqlite3.Connection | Path | str | None = None,
    name_or_id: str | int = "",
) -> bool:
    """Delete a datamgr session identified by name or ID."""
    from app.host.persistence.read import get_datamgr_session

    with resolve_connection(conn) as active_conn:
        current = get_datamgr_session(active_conn, name_or_id)
        if current is None:
            logger.warning(
                "%s: session '%s' not found for delete",
                DELETE_PK_FR,
                name_or_id,
                extra={"fr_id": DELETE_PK_FR, "session": name_or_id},
            )
            return False
        deleted = delete_row_by_pk(
            active_conn, "datamgr_sessions", {"id": current["id"]}
        )
    return deleted > 0


def delete_mt5_command(
    conn: sqlite3.Connection,
    command_id: str,
) -> bool:
    """Delete an MT5 command by command ID."""
    deleted = delete_row_by_pk(conn, "mt5_commands", {"command_id": command_id})
    return deleted > 0


def delete_datamgr_broker_stock(
    conn: sqlite3.Connection,
    stock_id: int,
) -> bool:
    """Delete a datamgr broker stock record by ID."""
    deleted = delete_row_by_pk(conn, "datamgr_broker_stock", {"ID": stock_id})
    return deleted > 0


def delete_datamgr_commodity(
    conn: sqlite3.Connection,
    commodity_id: int,
) -> bool:
    """Delete a commodity record by ID."""
    deleted = delete_row_by_pk(conn, "datamgr_commodities", {"id": commodity_id})
    return deleted > 0


def delete_datamgr_crypto_catalog(
    conn: sqlite3.Connection,
    exchange: str,
    symbol: str,
) -> bool:
    """Delete a crypto catalog entry by exchange and symbol."""
    deleted = delete_row_by_pk(
        conn,
        "datamgr_crypto_catalog",
        {"exchange": exchange, "symbol": symbol},
    )
    return deleted > 0


def delete_datamgr_log(
    conn: sqlite3.Connection,
    log_id: int,
) -> bool:
    """Delete a datamgr log record by ID."""
    deleted = delete_row_by_pk(conn, "datamgr_logs", {"id": log_id})
    return deleted > 0


def delete_datamgr_operation_log(
    conn: sqlite3.Connection,
    op_id: int,
) -> bool:
    """Delete a datamgr operation log record by ID."""
    deleted = delete_row_by_pk(conn, "datamgr_operation_log", {"id": op_id})
    return deleted > 0


def delete_datamgr_quality_report(
    conn: sqlite3.Connection,
    report_id: str,
) -> bool:
    """Delete a quality report by report ID."""
    deleted = delete_row_by_pk(conn, "datamgr_quality", {"report_id": report_id})
    return deleted > 0


def delete_datamgr_stock(
    conn: sqlite3.Connection,
    stock_id: int,
) -> bool:
    """Delete a datamgr stock by ID."""
    deleted = delete_row_by_pk(conn, "datamgr_stock", {"ID": stock_id})
    return deleted > 0


def delete_datamgr_stock_group(
    conn: sqlite3.Connection,
    group_id: int,
) -> bool:
    """Delete a datamgr stock group by ID with foreign key protection."""
    deleted = delete_record(conn, "datamgr_stock_group", {"ID": group_id})
    return deleted > 0


def delete_datamgr_ticker(
    conn: sqlite3.Connection,
    ticker_id: int,
) -> bool:
    """Delete a datamgr ticker by ID."""
    deleted = delete_row_by_pk(conn, "datamgr_tickers", {"id": ticker_id})
    return deleted > 0


def delete_host_grid_lease(
    conn: sqlite3.Connection,
    lease_id: str,
) -> bool:
    """Delete a grid lease by lease ID."""
    deleted = delete_row_by_pk(conn, "host_grid_leases", {"lease_id": lease_id})
    return deleted > 0


def delete_host_job_attempt(
    conn: sqlite3.Connection,
    attempt_id: str,
) -> bool:
    """Delete a host job attempt by attempt ID."""
    deleted = delete_row_by_pk(conn, "host_job_attempts", {"attempt_id": attempt_id})
    return deleted > 0


def delete_host_job_event(
    conn: sqlite3.Connection,
    event_id: str,
) -> bool:
    """Delete a host job event by event ID."""
    deleted = delete_row_by_pk(conn, "host_job_events", {"event_id": event_id})
    return deleted > 0


def delete_mt5_event(
    conn: sqlite3.Connection,
    event_id: int,
) -> bool:
    """Delete an MT5 event by event ID."""
    deleted = delete_row_by_pk(conn, "mt5_events", {"event_id": event_id})
    return deleted > 0


def delete_schema_migration(
    conn: sqlite3.Connection,
    version: int,
) -> bool:
    """Delete a schema migration record by version integer."""
    deleted = delete_row_by_pk(conn, "schema_migrations", {"version": version})
    return deleted > 0
