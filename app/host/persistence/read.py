"""Read and query operations for operational database tables.

Description:
    Provides parameterized query and fetch operations for all 25 operational
    database tables in HaruQuantAI. Supports point lookups by single or composite
    primary keys, filtered listing with ordering and pagination bounds, row
    counting, and domain-specific read helpers. All queries execute through
    parameterized statements with non-silent requirement logging.

Purpose:
    FEAT-HOST-PERSISTENCE: Host platform and workspace isolated SQLite persistence.

Key Capabilities:
    - FR-HOST-PERSISTENCE-READ-BY-PK: Query single row by table primary key.
      Associated: `read_row_by_pk()`, `read_entity()`, and 25 domain-specific
      get helpers.
      Logging: DEBUG emitted on row lookup and match; WARNING when not found.
    - FR-HOST-PERSISTENCE-LIST: Query records with filters, ordering, and limits
      or cursor pagination.
      Associated: `read_rows()`, `read_records()`, and 25 domain-specific
      list helpers.
      Logging: DEBUG emitted on query execution; INFO on non-empty results.
    - FR-HOST-PERSISTENCE-COUNT: Count rows matching optional filter criteria.
      Associated: `count_rows()`
      Logging: DEBUG emitted on row count calculation.

Python API Usage:
    ```python
    from app.host.persistence.create import get_connection
    from app.host.persistence.read import get_host_setting, read_records, read_rows

    conn = get_connection("data/database/haruquantai.db")
    setting = get_host_setting(conn, "system", "theme")
    jobs = read_rows(conn, "host_jobs", where={"status": "completed"}, limit=10)
    records = read_records(conn, "host_jobs", cursor_col="job_id", limit=10)
    ```

CLI Usage:
    ```bash
    uv run python -c "from app.host.persistence.create import get_connection"
    ```
"""

from __future__ import annotations

import sqlite3
from collections.abc import Generator, Mapping
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from app.host.logging import get_logger
from app.host.persistence.create import (
    TABLE_PRIMARY_KEYS,
    PersistenceError,
    get_connection,
)

logger = get_logger(__name__)

READ_PK_FR = "FR-HOST-PERSISTENCE-READ-BY-PK"
LIST_FR = "FR-HOST-PERSISTENCE-LIST"
COUNT_FR = "FR-HOST-PERSISTENCE-COUNT"

ORDER_BY_PARTS_MAX = 2


@contextmanager
def resolve_connection(
    conn: sqlite3.Connection | Path | str | None = None,
) -> Generator[sqlite3.Connection]:
    """Yield active connection or deterministically manage a connection.

    Args:
        conn: Optional existing open SQLite connection or database filesystem path.
            If None, opens default connection via get_connection() and closes it
            deterministically on block exit.

    Yields:
        sqlite3.Connection ready for execution.
    """
    if isinstance(conn, sqlite3.Connection):
        yield conn
    elif conn is not None:
        file_conn = get_connection(conn)
        try:
            yield file_conn
        finally:
            file_conn.close()
    else:
        auto_conn = get_connection()
        try:
            yield auto_conn
        finally:
            auto_conn.close()


def _build_where_clause(
    where: Mapping[str, Any] | None,
) -> tuple[str, list[Any]]:
    """Build parameterized WHERE clause from filter mapping."""
    if not where:
        return ("", [])
    clauses: list[str] = []
    params: list[Any] = []
    for col, val in where.items():
        if val is None:
            clauses.append(f'"{col}" IS NULL')
        else:
            clauses.append(f'"{col}" = ?')
            params.append(val)
    return (f" WHERE {' AND '.join(clauses)}", params)


def _build_order_clause(order_by: str | None) -> str:
    """Validate and format ORDER BY clause."""
    if not order_by:
        return ""
    parts = order_by.strip().split()
    if len(parts) in (1, ORDER_BY_PARTS_MAX) and parts[0].replace("_", "").isalnum():
        direction = (
            parts[1].upper()
            if len(parts) == ORDER_BY_PARTS_MAX and parts[1].upper() in ("ASC", "DESC")
            else "ASC"
        )
        return f' ORDER BY "{parts[0]}" {direction}'
    raise PersistenceError(f"Invalid order_by clause: '{order_by}'")


def _build_limit_clause(limit: int | None, offset: int | None) -> str:
    """Validate and format LIMIT and OFFSET clause."""
    if limit is None:
        return ""
    if limit < 0:
        raise PersistenceError("Limit must be a non-negative integer.")
    limit_sql = f" LIMIT {limit}"
    if offset is not None:
        if offset < 0:
            raise PersistenceError("Offset must be a non-negative integer.")
        limit_sql += f" OFFSET {offset}"
    return limit_sql


def read_row_by_pk(
    conn: sqlite3.Connection,
    table: str,
    pk_values: Mapping[str, Any],
) -> dict[str, Any] | None:
    """Read a single row by its primary key.

    Args:
        conn: Open SQLite connection.
        table: Target table name.
        pk_values: Mapping of primary key column names to target values.

    Returns:
        Row dictionary if found, None if no row matches.

    Raises:
        PersistenceError: If table is unapproved or primary key specification is
            incomplete.
    """
    if table not in TABLE_PRIMARY_KEYS:
        logger.error(
            "%s: rejected read for unapproved table %s",
            READ_PK_FR,
            table,
            extra={"fr_id": READ_PK_FR, "table": table},
        )
        raise PersistenceError(f"Table '{table}' is not in approved table catalogue.")

    expected_pks = TABLE_PRIMARY_KEYS[table]
    missing_pks = [pk for pk in expected_pks if pk not in pk_values]
    if missing_pks:
        logger.error(
            "%s: missing primary key columns %s for table %s",
            READ_PK_FR,
            missing_pks,
            table,
            extra={"fr_id": READ_PK_FR, "table": table},
        )
        raise PersistenceError(
            f"Missing primary key columns for '{table}': {missing_pks}"
        )

    where_clauses = [f'"{pk}" = ?' for pk in expected_pks]
    sql = f'SELECT * FROM "{table}" WHERE {" AND ".join(where_clauses)} LIMIT 1'  # noqa: S608
    params = [pk_values[pk] for pk in expected_pks]

    logger.debug(
        "%s: querying %s by pk %s",
        READ_PK_FR,
        table,
        pk_values,
        extra={"fr_id": READ_PK_FR, "table": table},
    )
    try:
        cursor = conn.execute(sql, params)
        row = cursor.fetchone()
    except sqlite3.Error as err:
        logger.exception(
            "%s: query failed on %s",
            READ_PK_FR,
            table,
            extra={"fr_id": READ_PK_FR, "table": table, "error": str(err)},
        )
        raise PersistenceError(f"Query on '{table}' failed: {err}") from err

    if row is None:
        logger.debug(
            "%s: row not found in %s for pk %s",
            READ_PK_FR,
            table,
            pk_values,
            extra={"fr_id": READ_PK_FR, "table": table},
        )
        return None

    logger.debug(
        "%s: retrieved row from %s for pk %s",
        READ_PK_FR,
        table,
        pk_values,
        extra={"fr_id": READ_PK_FR, "table": table},
    )
    return dict(row)


read_record = read_row_by_pk


def read_entity(
    conn: sqlite3.Connection,
    entity_id: str,
    entity_type: str,
) -> dict[str, Any] | None:
    """Read a single host entity by composite key (canonical HostPersistence).

    Args:
        conn: Open SQLite connection.
        entity_id: Target entity identifier.
        entity_type: Target entity domain type.

    Returns:
        Entity row dictionary if found, None otherwise.
    """
    return read_row_by_pk(
        conn, "host_entities", {"entity_id": entity_id, "entity_type": entity_type}
    )


def read_rows(
    conn: sqlite3.Connection,
    table: str,
    *,
    where: Mapping[str, Any] | None = None,
    order_by: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> list[dict[str, Any]]:
    """Query rows from an approved table with optional filters, order, and limits.

    Args:
        conn: Open SQLite connection.
        table: Target table name.
        where: Optional dictionary of column names to filter values.
        order_by: Optional order by clause (column name or column name with ASC/DESC).
        limit: Optional maximum number of rows to return.
        offset: Optional offset pagination count.

    Returns:
        List of row dictionaries matching the query.

    Raises:
        PersistenceError: If table is unapproved or query fails.
    """
    if table not in TABLE_PRIMARY_KEYS:
        logger.error(
            "%s: rejected list for unapproved table %s",
            LIST_FR,
            table,
            extra={"fr_id": LIST_FR, "table": table},
        )
        raise PersistenceError(f"Table '{table}' is not in approved table catalogue.")

    where_sql, params = _build_where_clause(where)
    order_sql = _build_order_clause(order_by)
    limit_sql = _build_limit_clause(limit, offset)

    sql = f'SELECT * FROM "{table}"{where_sql}{order_sql}{limit_sql}'  # noqa: S608
    logger.debug(
        "%s: querying %s with filters=%s",
        LIST_FR,
        table,
        where,
        extra={"fr_id": LIST_FR, "table": table},
    )
    try:
        cursor = conn.execute(sql, params)
        rows = cursor.fetchall()
    except sqlite3.Error as err:
        logger.exception(
            "%s: list failed on %s",
            LIST_FR,
            table,
            extra={"fr_id": LIST_FR, "table": table, "error": str(err)},
        )
        raise PersistenceError(f"Query on '{table}' failed: {err}") from err

    result = [dict(row) for row in rows]
    logger.debug(
        "%s: returned %s rows from %s",
        LIST_FR,
        len(result),
        table,
        extra={"fr_id": LIST_FR, "table": table, "count": len(result)},
    )
    return result


def read_records(
    conn: sqlite3.Connection,
    table: str,
    *,
    where: Mapping[str, Any] | None = None,
    order_by: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
    cursor_col: str | None = None,
    after_cursor: Any = None,
) -> list[dict[str, Any]]:
    """Query rows from an approved table with filtering and cursor pagination.

    Canonical HostPersistence read query supporting cursor or offset pagination.

    Args:
        conn: Open SQLite connection.
        table: Target table name in approved catalogue.
        where: Optional dictionary of column names to equality filter values.
        order_by: Optional order by clause (e.g. 'id ASC', 'timestamp_utc DESC').
        limit: Optional maximum rows to return.
        offset: Optional offset pagination count.
        cursor_col: Optional column name for deterministic cursor pagination.
        after_cursor: Optional cursor value to fetch strictly after.

    Returns:
        List of row dictionaries matching the query.

    Raises:
        PersistenceError: If table is unapproved or query fails.
    """
    if table not in TABLE_PRIMARY_KEYS:
        logger.error(
            "%s: rejected read_records for unapproved table %s",
            LIST_FR,
            table,
            extra={"fr_id": LIST_FR, "table": table},
        )
        raise PersistenceError(f"Table '{table}' is not in approved table catalogue.")

    effective_order = order_by
    cursor_clause = ""
    cursor_params: list[Any] = []
    if cursor_col is not None:
        clean_col = cursor_col.strip().strip('"')
        if not clean_col.replace("_", "").isalnum():
            raise PersistenceError(f"Invalid cursor column name: '{cursor_col}'")
        col_cursor = conn.execute(f'PRAGMA table_info("{table}")')
        valid_cols = {row[1] for row in col_cursor.fetchall()}
        if clean_col not in valid_cols:
            raise PersistenceError(
                f"Invalid cursor column '{cursor_col}' for table '{table}'."
            )
        if after_cursor is not None:
            cursor_clause = f'"{clean_col}" > ?'
            cursor_params = [after_cursor]
            if effective_order is None:
                effective_order = f"{clean_col} ASC"

    where_sql, params = _build_where_clause(where)
    if cursor_clause:
        if where_sql:
            where_sql = f"{where_sql} AND {cursor_clause}"
            params.extend(cursor_params)
        else:
            where_sql = f" WHERE {cursor_clause}"
            params = cursor_params

    order_sql = _build_order_clause(effective_order)
    limit_sql = _build_limit_clause(limit, offset)

    sql = f'SELECT * FROM "{table}"{where_sql}{order_sql}{limit_sql}'  # noqa: S608
    logger.debug(
        "%s: read_records from %s (filters=%s, cursor=%s)",
        LIST_FR,
        table,
        where,
        after_cursor,
        extra={"fr_id": LIST_FR, "table": table},
    )
    try:
        cursor = conn.execute(sql, params)
        rows = cursor.fetchall()
    except sqlite3.Error as err:
        logger.exception(
            "%s: read_records failed on %s",
            LIST_FR,
            table,
            extra={"fr_id": LIST_FR, "table": table, "error": str(err)},
        )
        raise PersistenceError(f"Query on '{table}' failed: {err}") from err

    result = [dict(row) for row in rows]
    logger.debug(
        "%s: read_records returned %s rows from %s",
        LIST_FR,
        len(result),
        table,
        extra={"fr_id": LIST_FR, "table": table, "count": len(result)},
    )
    return result


def count_rows(
    conn: sqlite3.Connection,
    table: str,
    *,
    where: Mapping[str, Any] | None = None,
) -> int:
    """Count records matching filter in an approved table.

    Args:
        conn: Open SQLite connection.
        table: Target table name.
        where: Optional dictionary of column names to filter values.

    Returns:
        Integer count of matching rows.

    Raises:
        PersistenceError: If table is unapproved or query fails.
    """
    if table not in TABLE_PRIMARY_KEYS:
        logger.error(
            "%s: rejected count for unapproved table %s",
            COUNT_FR,
            table,
            extra={"fr_id": COUNT_FR, "table": table},
        )
        raise PersistenceError(f"Table '{table}' is not in approved table catalogue.")

    where_sql, params = _build_where_clause(where)
    sql = f'SELECT COUNT(*) FROM "{table}"{where_sql}'  # noqa: S608
    try:
        cursor = conn.execute(sql, params)
        count = int(cursor.fetchone()[0])
    except sqlite3.Error as err:
        logger.exception(
            "%s: count failed on %s",
            COUNT_FR,
            table,
            extra={"fr_id": COUNT_FR, "table": table, "error": str(err)},
        )
        raise PersistenceError(f"Count on '{table}' failed: {err}") from err

    logger.debug(
        "%s: counted %s rows in %s",
        COUNT_FR,
        count,
        table,
        extra={"fr_id": COUNT_FR, "table": table, "count": count},
    )
    return count


def get_host_setting(
    conn_or_scope: sqlite3.Connection | str,
    scope_or_key: str,
    key_opt: str | None = None,
) -> dict[str, Any] | None:
    """Get host setting by composite key (scope, key).

    Supports both (conn, scope, key) and (scope, key) calling signatures.
    """
    if isinstance(conn_or_scope, sqlite3.Connection):
        active_conn = conn_or_scope
        scope = scope_or_key
        key = key_opt or ""
        return read_row_by_pk(
            active_conn, "host_settings", {"scope": scope, "key": key}
        )
    with resolve_connection() as active_conn:
        return read_row_by_pk(
            active_conn, "host_settings", {"scope": conn_or_scope, "key": scope_or_key}
        )


def list_host_settings(
    conn: sqlite3.Connection | None = None,
    *,
    scope: str | None = None,
) -> list[dict[str, Any]]:
    """List host settings, optionally filtered by scope.

    Args:
        conn: Optional SQLite connection. If omitted, opens and closes default
            connection.
        scope: Optional scope string filter.

    Returns:
        List of setting row dictionaries.
    """
    with resolve_connection(conn) as active_conn:
        where = {"scope": scope} if scope is not None else None
        return read_rows(active_conn, "host_settings", where=where, order_by="key ASC")


def get_host_session(
    conn_or_session_id: sqlite3.Connection | Path | str | None = None,
    session_id: str | None = None,
    *,
    conn: sqlite3.Connection | Path | str | None = None,
) -> dict[str, Any] | None:
    """Get host session record by session ID."""
    active_conn = conn
    target_id = session_id
    if isinstance(conn_or_session_id, (sqlite3.Connection, Path)):
        active_conn = conn_or_session_id
    elif isinstance(conn_or_session_id, str):
        if session_id is None:
            target_id = conn_or_session_id
        else:
            active_conn = conn_or_session_id

    if target_id is None:
        raise PersistenceError("session_id must be provided to get_host_session")

    with resolve_connection(active_conn) as c:
        return read_row_by_pk(c, "host_session", {"session_id": target_id})


def get_host_session_by_token_hash(
    conn_or_token_hash: sqlite3.Connection | Path | str | None = None,
    token_hash: str | None = None,
    *,
    conn: sqlite3.Connection | Path | str | None = None,
) -> dict[str, Any] | None:
    """Get host session record by token hash."""
    active_conn = conn
    target_hash = token_hash
    if isinstance(conn_or_token_hash, (sqlite3.Connection, Path)):
        active_conn = conn_or_token_hash
    elif isinstance(conn_or_token_hash, str):
        if token_hash is None:
            target_hash = conn_or_token_hash
        else:
            active_conn = conn_or_token_hash

    if target_hash is None:
        raise PersistenceError(
            "token_hash must be provided to get_host_session_by_token_hash"
        )

    with resolve_connection(active_conn) as c:
        results = read_rows(
            c, "host_session", where={"token_hash": target_hash}, limit=1
        )
        return results[0] if results else None


def get_host_job(
    conn_or_job_id: sqlite3.Connection | Path | str | None = None,
    job_id: str | None = None,
    *,
    conn: sqlite3.Connection | Path | str | None = None,
) -> dict[str, Any] | None:
    """Get host job record by job ID."""
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
        raise PersistenceError("job_id must be provided to get_host_job")

    with resolve_connection(active_conn) as c:
        return read_row_by_pk(c, "host_jobs", {"job_id": target_id})


def list_host_jobs(
    conn: sqlite3.Connection | Path | str | None = None,
    *,
    status: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """List host jobs ordered by submitted timestamp descending.

    Args:
        conn: Optional SQLite connection or path. If omitted, opens and closes
            default connection.
        status: Optional status string filter.
        limit: Maximum rows to return.

    Returns:
        List of job row dictionaries.
    """
    with resolve_connection(conn) as active_conn:
        where = {"status": status} if status is not None else None
        return read_rows(
            active_conn,
            "host_jobs",
            where=where,
            order_by="submitted_at_utc DESC",
            limit=limit,
        )


def get_host_job_attempts(
    conn_or_job_id: sqlite3.Connection | Path | str | None = None,
    job_id: str | None = None,
    *,
    conn: sqlite3.Connection | Path | str | None = None,
) -> list[dict[str, Any]]:
    """Get all attempts for a given job ID ordered by sequence."""
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
        raise PersistenceError("job_id must be provided to get_host_job_attempts")

    with resolve_connection(active_conn) as c:
        return read_rows(
            c,
            "host_job_attempts",
            where={"job_id": target_id},
            order_by="sequence ASC",
        )


def get_host_job_events(
    conn_or_job_id: sqlite3.Connection | Path | str | None = None,
    job_id: str | None = None,
    *,
    conn: sqlite3.Connection | Path | str | None = None,
) -> list[dict[str, Any]]:
    """Get all events for a given job ID ordered by creation timestamp."""
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
        raise PersistenceError("job_id must be provided to get_host_job_events")

    with resolve_connection(active_conn) as c:
        return read_rows(
            c,
            "host_job_events",
            where={"job_id": target_id},
            order_by="created_at_utc ASC",
        )


def get_host_entity(
    conn: sqlite3.Connection,
    entity_id: str,
    entity_type: str,
) -> dict[str, Any] | None:
    """Get host entity by entity_id and entity_type."""
    return read_row_by_pk(
        conn, "host_entities", {"entity_id": entity_id, "entity_type": entity_type}
    )


def get_host_lease(
    conn: sqlite3.Connection,
    lease_key: str,
) -> dict[str, Any] | None:
    """Get host lease by lease key."""
    return read_row_by_pk(conn, "host_leases", {"lease_key": lease_key})


def get_host_grid_node(
    conn: sqlite3.Connection,
    node_id: str,
) -> dict[str, Any] | None:
    """Get host grid node by node ID."""
    return read_row_by_pk(conn, "host_grid_nodes", {"node_id": node_id})


def get_datamgr_broker(
    conn: sqlite3.Connection,
    broker_id: int,
) -> dict[str, Any] | None:
    """Get datamgr broker by integer ID."""
    return read_row_by_pk(conn, "datamgr_broker", {"id": broker_id})


def get_datamgr_broker_by_name(
    conn: sqlite3.Connection,
    name: str,
) -> dict[str, Any] | None:
    """Get datamgr broker by unique name."""
    results = read_rows(conn, "datamgr_broker", where={"name": name}, limit=1)
    return results[0] if results else None


def get_datamgr_dataset(
    conn: sqlite3.Connection,
    dataset_id: str,
) -> dict[str, Any] | None:
    """Get datamgr dataset by dataset ID."""
    return read_row_by_pk(conn, "datamgr_datasets", {"id": dataset_id})


def get_datamgr_instrument(
    conn: sqlite3.Connection | Path | str | None = None,
    symbol: str = "",
) -> dict[str, Any] | None:
    """Get datamgr instrument by symbol."""
    with resolve_connection(conn) as active_conn:
        results = read_rows(
            active_conn, "datamgr_instruments", where={"symbol": symbol}, limit=1
        )
    return results[0] if results else None


def list_datamgr_instruments(
    conn: sqlite3.Connection | Path | str | None = None,
    *,
    broker_id: int | None = None,
) -> list[dict[str, Any]]:
    """List datamgr instruments, optionally filtered by broker_id.

    Args:
        conn: Optional SQLite connection. If omitted, opens and closes default
            connection.
        broker_id: Optional broker ID integer filter.

    Returns:
        List of instrument row dictionaries.
    """
    with resolve_connection(conn) as active_conn:
        where = {"broker_id": broker_id} if broker_id is not None else None
        return read_rows(
            active_conn, "datamgr_instruments", where=where, order_by="symbol ASC"
        )


def get_datamgr_quality_report(
    conn: sqlite3.Connection,
    report_id: str,
) -> dict[str, Any] | None:
    """Get quality report by report ID."""
    return read_row_by_pk(conn, "datamgr_quality", {"report_id": report_id})


def get_datamgr_session(
    conn: sqlite3.Connection | Path | str | None = None,
    name_or_id: str | int = "",
) -> dict[str, Any] | None:
    """Get datamgr session by unique name or ID."""
    with resolve_connection(conn) as active_conn:
        if isinstance(name_or_id, int):
            return read_row_by_pk(active_conn, "datamgr_sessions", {"id": name_or_id})
        if isinstance(name_or_id, str) and name_or_id.isdigit():
            by_id = read_row_by_pk(
                active_conn, "datamgr_sessions", {"id": int(name_or_id)}
            )
            if by_id is not None:
                return by_id
        rows = read_rows(
            active_conn, "datamgr_sessions", where={"name": name_or_id}, limit=1
        )
        return rows[0] if rows else None


def list_datamgr_sessions(
    conn: sqlite3.Connection | Path | str | None = None,
    *,
    broker_id: int | None = None,
) -> list[dict[str, Any]]:
    """List datamgr sessions, optionally filtered by broker_id."""
    with resolve_connection(conn) as active_conn:
        where = (
            {"broker_id": broker_id}
            if broker_id is not None and broker_id >= 0
            else None
        )
        return read_rows(
            active_conn, "datamgr_sessions", where=where, order_by="name ASC"
        )


def get_mt5_command(
    conn: sqlite3.Connection,
    command_id: str,
) -> dict[str, Any] | None:
    """Get MT5 command by command ID."""
    return read_row_by_pk(conn, "mt5_commands", {"command_id": command_id})


def get_schema_migrations(
    conn: sqlite3.Connection | None = None,
) -> list[dict[str, Any]]:
    """Get applied schema migrations ordered by version ascending.

    Args:
        conn: Optional SQLite connection. If omitted, opens and closes default
            connection.

    Returns:
        List of migration row dictionaries.
    """
    with resolve_connection(conn) as active_conn:
        return read_rows(active_conn, "schema_migrations", order_by="version ASC")


def count_database_tables(
    conn: sqlite3.Connection | Path | str | None = None,
) -> int:
    """Count non-system user tables in the database.

    Args:
        conn: Optional SQLite connection or database path. If omitted,
            resolves the canonical default host database.

    Returns:
        Number of user tables in the database.
    """
    with resolve_connection(conn) as active_conn:
        cursor = active_conn.execute(
            "SELECT COUNT(*) FROM sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%';"
        )
        return int(cursor.fetchone()[0])


def list_datamgr_brokers(
    conn: sqlite3.Connection | None = None,
) -> list[dict[str, Any]]:
    """List all datamgr brokers ordered by name."""
    with resolve_connection(conn) as active_conn:
        return read_rows(active_conn, "datamgr_broker", order_by="name ASC")


def get_datamgr_broker_stock(
    conn: sqlite3.Connection,
    stock_id: int,
) -> dict[str, Any] | None:
    """Get datamgr broker stock mapping by ID."""
    return read_row_by_pk(conn, "datamgr_broker_stock", {"ID": stock_id})


def list_datamgr_broker_stocks(
    conn: sqlite3.Connection,
    *,
    broker_id: int | None = None,
) -> list[dict[str, Any]]:
    """List datamgr broker stocks, optionally filtered by broker ID."""
    where = {"BROKER_ID": broker_id} if broker_id is not None else None
    return read_rows(conn, "datamgr_broker_stock", where=where, order_by="ID ASC")


def get_datamgr_commodity(
    conn: sqlite3.Connection,
    commodity_id: int,
) -> dict[str, Any] | None:
    """Get commodity record by ID."""
    return read_row_by_pk(conn, "datamgr_commodities", {"id": commodity_id})


def list_datamgr_commodities(
    conn: sqlite3.Connection,
    *,
    exchange: str | None = None,
) -> list[dict[str, Any]]:
    """List commodity records, optionally filtered by exchange."""
    where = {"exchange": exchange} if exchange is not None else None
    return read_rows(conn, "datamgr_commodities", where=where, order_by="code ASC")


def get_datamgr_crypto_catalog(
    conn: sqlite3.Connection,
    exchange: str,
    symbol: str,
) -> dict[str, Any] | None:
    """Get crypto catalog entry by exchange and symbol."""
    return read_row_by_pk(
        conn, "datamgr_crypto_catalog", {"exchange": exchange, "symbol": symbol}
    )


def list_datamgr_crypto_catalog(
    conn: sqlite3.Connection,
    *,
    exchange: str | None = None,
) -> list[dict[str, Any]]:
    """List crypto catalog entries, optionally filtered by exchange."""
    where = {"exchange": exchange} if exchange is not None else None
    return read_rows(conn, "datamgr_crypto_catalog", where=where, order_by="symbol ASC")


list_datamgr_crypto_catalogs = list_datamgr_crypto_catalog


def list_datamgr_datasets(
    conn: sqlite3.Connection,
    *,
    broker: str | None = None,
) -> list[dict[str, Any]]:
    """List datamgr datasets, optionally filtered by broker."""
    where = {"broker": broker} if broker is not None else None
    return read_rows(conn, "datamgr_datasets", where=where, order_by="id ASC")


def get_datamgr_log(
    conn: sqlite3.Connection,
    log_id: int,
) -> dict[str, Any] | None:
    """Get datamgr log record by ID."""
    return read_row_by_pk(conn, "datamgr_logs", {"id": log_id})


def list_datamgr_logs(
    conn: sqlite3.Connection,
    *,
    symbol: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """List datamgr logs ordered by ID descending."""
    where = {"symbol": symbol} if symbol is not None else None
    return read_rows(conn, "datamgr_logs", where=where, order_by="id DESC", limit=limit)


def get_datamgr_operation_log(
    conn: sqlite3.Connection,
    op_id: int,
) -> dict[str, Any] | None:
    """Get datamgr operation log record by ID."""
    return read_row_by_pk(conn, "datamgr_operation_log", {"id": op_id})


def list_datamgr_operation_logs(
    conn: sqlite3.Connection,
    *,
    symbol: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """List datamgr operation logs ordered by ID descending."""
    where = {"symbol": symbol} if symbol is not None else None
    return read_rows(
        conn, "datamgr_operation_log", where=where, order_by="id DESC", limit=limit
    )


def list_datamgr_quality_reports(
    conn: sqlite3.Connection,
    *,
    dataset_id: str | None = None,
) -> list[dict[str, Any]]:
    """List quality reports ordered by evaluation time descending."""
    where = {"dataset_id": dataset_id} if dataset_id is not None else None
    return read_rows(
        conn, "datamgr_quality", where=where, order_by="evaluated_at_utc DESC"
    )


def get_datamgr_stock(
    conn: sqlite3.Connection,
    stock_id: int,
) -> dict[str, Any] | None:
    """Get datamgr stock by ID."""
    return read_row_by_pk(conn, "datamgr_stock", {"ID": stock_id})


def list_datamgr_stocks(
    conn: sqlite3.Connection,
    *,
    basket_id: int | None = None,
) -> list[dict[str, Any]]:
    """List datamgr stocks, optionally filtered by basket ID."""
    where = {"BASKET_ID": basket_id} if basket_id is not None else None
    return read_rows(conn, "datamgr_stock", where=where, order_by="ID ASC")


def get_datamgr_stock_group(
    conn: sqlite3.Connection,
    group_id: int,
) -> dict[str, Any] | None:
    """Get datamgr stock group by ID."""
    return read_row_by_pk(conn, "datamgr_stock_group", {"ID": group_id})


def list_datamgr_stock_groups(
    conn: sqlite3.Connection,
) -> list[dict[str, Any]]:
    """List datamgr stock groups ordered by name."""
    return read_rows(conn, "datamgr_stock_group", order_by="NAME ASC")


def get_datamgr_ticker(
    conn: sqlite3.Connection,
    ticker_id: int,
) -> dict[str, Any] | None:
    """Get datamgr ticker by ID."""
    return read_row_by_pk(conn, "datamgr_tickers", {"id": ticker_id})


def list_datamgr_tickers(
    conn: sqlite3.Connection,
    *,
    exchange: str | None = None,
) -> list[dict[str, Any]]:
    """List datamgr tickers, optionally filtered by exchange."""
    where = {"exchange": exchange} if exchange is not None else None
    return read_rows(conn, "datamgr_tickers", where=where, order_by="ticker ASC")


def list_host_entities(
    conn: sqlite3.Connection,
    *,
    entity_type: str | None = None,
    scope: str | None = None,
) -> list[dict[str, Any]]:
    """List host entities, optionally filtered by entity_type or scope."""
    where: dict[str, Any] = {}
    if entity_type is not None:
        where["entity_type"] = entity_type
    if scope is not None:
        where["scope"] = scope
    return read_rows(
        conn,
        "host_entities",
        where=where or None,
        order_by="created_at_utc DESC",
    )


def get_host_grid_lease(
    conn: sqlite3.Connection,
    lease_id: str,
) -> dict[str, Any] | None:
    """Get grid lease by lease ID."""
    return read_row_by_pk(conn, "host_grid_leases", {"lease_id": lease_id})


def list_host_grid_leases(
    conn: sqlite3.Connection,
    *,
    node_id: str | None = None,
    state: str | None = None,
) -> list[dict[str, Any]]:
    """List grid leases, optionally filtered by node_id or state."""
    where: dict[str, Any] = {}
    if node_id is not None:
        where["node_id"] = node_id
    if state is not None:
        where["state"] = state
    return read_rows(
        conn,
        "host_grid_leases",
        where=where or None,
        order_by="leased_at_utc DESC",
    )


def list_host_grid_nodes(
    conn: sqlite3.Connection,
    *,
    state: str | None = None,
) -> list[dict[str, Any]]:
    """List grid compute nodes, optionally filtered by state."""
    where = {"state": state} if state is not None else None
    return read_rows(conn, "host_grid_nodes", where=where, order_by="node_id ASC")


def get_host_job_attempt(
    conn: sqlite3.Connection,
    attempt_id: str,
) -> dict[str, Any] | None:
    """Get host job attempt by attempt ID."""
    return read_row_by_pk(conn, "host_job_attempts", {"attempt_id": attempt_id})


list_host_job_attempts = get_host_job_attempts


def get_host_job_event(
    conn: sqlite3.Connection,
    event_id: str,
) -> dict[str, Any] | None:
    """Get host job event by event ID."""
    return read_row_by_pk(conn, "host_job_events", {"event_id": event_id})


list_host_job_events = get_host_job_events


def list_host_leases(
    conn: sqlite3.Connection,
    *,
    scope: str | None = None,
) -> list[dict[str, Any]]:
    """List host leases, optionally filtered by scope."""
    where = {"scope": scope} if scope is not None else None
    return read_rows(conn, "host_leases", where=where, order_by="acquired_at_utc DESC")


def list_host_sessions(
    conn: sqlite3.Connection,
    *,
    status: str | None = None,
) -> list[dict[str, Any]]:
    """List host sessions, optionally filtered by status."""
    where = {"status": status} if status is not None else None
    return read_rows(conn, "host_session", where=where, order_by="created_at_utc DESC")


def list_mt5_commands(
    conn: sqlite3.Connection,
    *,
    status: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """List MT5 commands, optionally filtered by status."""
    where = {"status": status} if status is not None else None
    return read_rows(
        conn, "mt5_commands", where=where, order_by="created_at DESC", limit=limit
    )


def get_mt5_event(
    conn: sqlite3.Connection,
    event_id: int,
) -> dict[str, Any] | None:
    """Get MT5 event by event ID."""
    return read_row_by_pk(conn, "mt5_events", {"event_id": event_id})


def list_mt5_events(
    conn: sqlite3.Connection,
    *,
    command_id: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """List MT5 events, optionally filtered by command ID."""
    where = {"command_id": command_id} if command_id is not None else None
    return read_rows(
        conn, "mt5_events", where=where, order_by="received_at DESC", limit=limit
    )


def get_schema_migration(
    conn: sqlite3.Connection,
    version: int,
) -> dict[str, Any] | None:
    """Get applied schema migration by version integer."""
    return read_row_by_pk(conn, "schema_migrations", {"version": version})


list_schema_migrations = get_schema_migrations
