# ruff: noqa: INP001
"""SQLite WAL persistence layer, parameterized CRUD, and atomic batch transactions.

Description:
    Provides the centralized HostPersistence engine for HaruQuantAI. Manages
    connection lifecycles in write-ahead logging (WAL) mode, idempotently provisions
    the 25 operational database tables, enforces primary key validations and
    foreign-key reference guards, supports deterministic cursor pagination,
    implements compare-and-set (CAS) optimistic revision concurrency, and guarantees
    all-or-nothing rollback for atomic multi-row batch write transactions.

Purpose:
    FEAT-HOST-PERSISTENCE: Core SQLite WAL persistence and transaction gateway.

Key Capabilities:
    - FR-HOST-PERSISTENCE-CREATE: Create rows/entities (create_record() -> INFO).
    - FR-HOST-PERSISTENCE-READ: Query rows with cursor (read_records() -> DEBUG).
    - FR-HOST-PERSISTENCE-UPDATE: Update rows with CAS (update_record() -> INFO).
    - FR-HOST-PERSISTENCE-DELETE: Delete rows with FK guards (delete_record() -> INFO).
    - FR-HOST-PERSISTENCE-BATCH: Atomic multi-row batch writes (apply_batch() -> INFO).

Python API Usage:
    ```python
    from app.host.persistence import HostPersistence

    records = HostPersistence.read_records("host_settings", where={"scope": "ui"})
    ```

CLI Usage:
    ```bash
    uv run python -m app.host.persistence
    ```
"""

from __future__ import annotations

import sqlite3
import sys
import tempfile
import threading
from collections.abc import Generator, Mapping, Sequence
from contextlib import contextmanager, nullcontext
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, NamedTuple

from app.host._schema import (
    PERSISTENCE_TABLES,
    SCHEMA_DDL,
    TABLE_AUTOINCREMENT_PK_TABLES,
    TABLE_DDL_MAP,
    TABLE_FOREIGN_KEY_GUARDS,
    TABLE_PRIMARY_KEYS,
)
from app.host.logging import get_logger

__all__ = ["HostPersistence", "HostPersistenceCLI"]

logger = get_logger(__name__)

CREATE_FR = "FR-HOST-PERSISTENCE-CREATE"
READ_FR = "FR-HOST-PERSISTENCE-READ"
UPDATE_FR = "FR-HOST-PERSISTENCE-UPDATE"
DELETE_FR = "FR-HOST-PERSISTENCE-DELETE"
BATCH_FR = "FR-HOST-PERSISTENCE-BATCH"

DEFAULT_DB_PATH: Path = Path("data/database/haruquantai.db")


class _PersistenceError(RuntimeError):
    """Base error for host persistence and transaction failures."""


class _RevisionConflictError(_PersistenceError):
    """Raised when an optimistic revision expectation fails."""

    def __init__(
        self,
        message: str = "Revision conflict detected during update",
        expected_revision: int | None = None,
        current_revision: int | None = None,
        *,
        expected: int | None = None,
        current: int | None = None,
    ) -> None:
        exp = expected_revision if expected_revision is not None else expected
        cur = current_revision if current_revision is not None else current
        self.expected = self.expected_revision = exp
        self.current = self.current_revision = cur
        super().__init__(message)


class _BatchOperation(NamedTuple):
    """Single operation descriptor inside an atomic batch transaction."""

    op_type: str
    table: str
    data: Mapping[str, Any] | None = None
    pk_values: Mapping[str, Any] | None = None
    expected_revision: int | None = None
    revision_col: str = "revision"


class _BatchResult(NamedTuple):
    """Result summary of an applied atomic batch transaction."""

    total_operations: int
    affected_rows: int
    details: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        """Convert result into serializable dictionary."""
        return {**self._asdict(), "details": list(self.details)}


def _current_utc_iso() -> str:
    """Return formatted ISO-8601 UTC timestamp."""
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


class HostPersistence:
    """Centralized SQLite WAL persistence and transaction gateway."""

    DEFAULT_DB_PATH = DEFAULT_DB_PATH
    PERSISTENCE_TABLES = PERSISTENCE_TABLES
    TABLE_PRIMARY_KEYS = TABLE_PRIMARY_KEYS
    TABLE_AUTOINCREMENT_PK_TABLES = TABLE_AUTOINCREMENT_PK_TABLES
    TABLE_FOREIGN_KEY_GUARDS = TABLE_FOREIGN_KEY_GUARDS
    TABLE_DDL_MAP = TABLE_DDL_MAP
    SCHEMA_DDL = SCHEMA_DDL
    Error = _PersistenceError
    RevisionConflictError = _RevisionConflictError
    BatchOperation = _BatchOperation
    BatchResult = _BatchResult
    _local = threading.local()

    @classmethod
    def _require_table(cls, table: str) -> tuple[str, ...]:
        """Validate table is in approved catalogue and return its primary key tuple."""
        if table not in cls.TABLE_PRIMARY_KEYS:
            raise _PersistenceError(
                f"Table '{table}' is not in approved table catalogue."
            )
        return cls.TABLE_PRIMARY_KEYS[table]

    @classmethod
    def _get_connection(cls, *, timeout: float = 30.0) -> sqlite3.Connection:
        """Create and configure a SQLite connection in WAL mode."""
        resolved = Path(cls.DEFAULT_DB_PATH)
        is_new_file = str(resolved) != ":memory:" and not resolved.exists()
        if str(resolved) != ":memory:":
            resolved.parent.mkdir(parents=True, exist_ok=True)
        try:
            conn = sqlite3.connect(
                str(resolved), timeout=timeout, check_same_thread=False
            )
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = NORMAL")
            conn.execute("PRAGMA foreign_keys = ON")
            if is_new_file:
                with conn:
                    for ddl in cls.SCHEMA_DDL:
                        conn.execute(ddl)
        except (sqlite3.Error, OSError, ValueError) as err:
            extra = {"fr_id": CREATE_FR, "error": str(err)}
            logger.exception(
                "%s: connection failed to %s", CREATE_FR, resolved, extra=extra
            )
            raise _PersistenceError(f"Database connection failed: {err}") from err
        return conn

    @classmethod
    def _ensure_table_schema(cls, conn: sqlite3.Connection, table: str) -> None:
        """Ensure a specific table exists by executing its canonical DDL statement."""
        if table not in cls.TABLE_DDL_MAP:
            extra = {"fr_id": CREATE_FR, "table": table}
            logger.error(
                "%s: rejected schema creation for unapproved table %s",
                CREATE_FR,
                table,
                extra=extra,
            )
            raise _PersistenceError(
                f"Table '{table}' is not an approved operational persistence table."
            )
        try:
            conn.execute(cls.TABLE_DDL_MAP[table])
        except sqlite3.Error as err:
            extra_err = {"fr_id": CREATE_FR, "table": table, "error": str(err)}
            logger.exception(
                "%s: failed ensuring table schema for %s",
                CREATE_FR,
                table,
                extra=extra_err,
            )
            raise _PersistenceError(
                f"Ensuring schema for '{table}' failed: {err}"
            ) from err

    @classmethod
    @contextmanager
    def _resolve_connection(cls) -> Generator[sqlite3.Connection]:
        """Resolve an active thread-local batch connection or open a temporary one."""
        active_conn: sqlite3.Connection | None = getattr(cls._local, "conn", None)
        if active_conn is not None:
            yield active_conn
        else:
            c = cls._get_connection()
            try:
                yield c
            finally:
                c.close()

    @staticmethod
    def _build_where(where: Mapping[str, Any] | None) -> tuple[str, list[Any]]:
        """Construct parameterized WHERE clause from dictionary mapping."""
        if not where:
            return "", []
        clauses: list[str] = []
        params: list[Any] = []
        for col, val in where.items():
            clean_col = col.strip().strip('"')
            if not clean_col.replace("_", "").isalnum():
                raise _PersistenceError(f"Invalid column name in filter: '{col}'")
            if val is None:
                clauses.append(f'"{clean_col}" IS NULL')
            else:
                clauses.append(f'"{clean_col}" = ?')
                params.append(val)
        return " WHERE " + " AND ".join(clauses), params

    @classmethod
    def _insert_row(
        cls,
        conn: sqlite3.Connection,
        table: str,
        data: Mapping[str, Any],
        *,
        commit: bool = True,
    ) -> Any:
        """Insert a row into table."""
        pk_cols = cls._require_table(table)
        if not data:
            raise _PersistenceError("Insert data dictionary cannot be empty.")

        columns = list(data.keys())
        placeholders = ", ".join("?" for _ in columns)
        quoted_cols = ", ".join(f'"{col}"' for col in columns)
        sql = f'INSERT INTO "{table}" ({quoted_cols}) VALUES ({placeholders})'  # noqa: S608
        values = [data[col] for col in columns]

        try:
            with conn if commit else nullcontext():
                last_id = conn.execute(sql, values).lastrowid
        except sqlite3.Error as err:
            extra = {"fr_id": CREATE_FR, "table": table, "error": str(err)}
            logger.exception("%s: insert failed on %s", CREATE_FR, table, extra=extra)
            raise _PersistenceError(f"Insert into '{table}' failed: {err}") from err

        if len(pk_cols) == 1 and pk_cols[0] in data:
            return data[pk_cols[0]]
        if len(pk_cols) > 1 and all(k in data for k in pk_cols):
            return tuple(data[k] for k in pk_cols)
        return last_id

    @classmethod
    def _update_row_by_pk(
        cls,
        conn: sqlite3.Connection,
        table: str,
        pk_values: Mapping[str, Any],
        updates: Mapping[str, Any],
        *,
        commit: bool = True,
    ) -> int:
        """Update a row by primary key."""
        expected_pks = cls._require_table(table)
        if not updates:
            raise _PersistenceError("Updates mapping cannot be empty.")
        missing_pks = [pk for pk in expected_pks if pk not in pk_values]
        if missing_pks:
            raise _PersistenceError(
                f"Missing primary key columns for '{table}': {missing_pks}"
            )

        set_str = ", ".join(f'"{col}" = ?' for col in updates)
        where_str = " AND ".join(f'"{pk}" = ?' for pk in expected_pks)
        sql = f'UPDATE "{table}" SET {set_str} WHERE {where_str}'  # noqa: S608
        params = list(updates.values()) + [pk_values[pk] for pk in expected_pks]

        try:
            with conn if commit else nullcontext():
                return conn.execute(sql, params).rowcount
        except sqlite3.Error as err:
            extra = {"fr_id": UPDATE_FR, "table": table, "error": str(err)}
            logger.exception("%s: update failed on %s", UPDATE_FR, table, extra=extra)
            raise _PersistenceError(f"Update on '{table}' failed: {err}") from err

    @classmethod
    def _delete_row_by_pk(
        cls,
        conn: sqlite3.Connection,
        table: str,
        pk_values: Mapping[str, Any],
        *,
        check_references: bool = True,
        commit: bool = True,
    ) -> int:
        """Delete a row by primary key with foreign key guards."""
        expected_pks = cls._require_table(table)
        missing_pks = [pk for pk in expected_pks if pk not in pk_values]
        if missing_pks:
            raise _PersistenceError(
                f"Missing primary key columns for '{table}': {missing_pks}"
            )

        if check_references and table in cls.TABLE_FOREIGN_KEY_GUARDS:
            for child_tbl, fk_col, pk_col in cls.TABLE_FOREIGN_KEY_GUARDS[table]:
                if pk_col in pk_values:
                    cls._ensure_table_schema(conn, child_tbl)
                    query = f'SELECT COUNT(*) FROM "{child_tbl}" WHERE "{fk_col}" = ?'  # noqa: S608
                    cnt = int(conn.execute(query, (pk_values[pk_col],)).fetchone()[0])
                    if cnt > 0:
                        extra = {
                            "fr_id": DELETE_FR,
                            "table": table,
                            "child_table": child_tbl,
                            "count": cnt,
                        }
                        msg = (
                            "%s: delete blocked by foreign key guard on %s "
                            "(dependent rows in %s: %d)"
                        )
                        logger.error(msg, DELETE_FR, table, child_tbl, cnt, extra=extra)
                        raise _PersistenceError(
                            f"Deletion blocked for '{table}': {cnt} dependent "
                            f"row(s) exist in '{child_tbl}'."
                        )

        where_str = " AND ".join(f'"{pk}" = ?' for pk in expected_pks)
        sql = f'DELETE FROM "{table}" WHERE {where_str}'  # noqa: S608
        params = [pk_values[pk] for pk in expected_pks]

        try:
            with conn if commit else nullcontext():
                return conn.execute(sql, params).rowcount
        except sqlite3.Error as err:
            extra = {"fr_id": DELETE_FR, "table": table, "error": str(err)}
            logger.exception("%s: delete failed on %s", DELETE_FR, table, extra=extra)
            raise _PersistenceError(f"Delete on '{table}' failed: {err}") from err

    @classmethod
    def _delete_rows(
        cls, conn: sqlite3.Connection, table: str, where: Mapping[str, Any]
    ) -> int:
        """Delete multiple rows matching filter criteria."""
        cls._require_table(table)
        if not where:
            raise _PersistenceError("Delete requires non-empty where filter mapping.")
        where_sql, params = cls._build_where(where)
        sql = f'DELETE FROM "{table}"{where_sql}'  # noqa: S608
        try:
            with conn:
                return conn.execute(sql, params).rowcount
        except sqlite3.Error as err:
            raise _PersistenceError(f"Delete rows on '{table}' failed: {err}") from err

    @classmethod
    def create_record(
        cls, table: str, data: Mapping[str, Any], *, commit: bool = True
    ) -> Any:
        """Insert a single record into an approved database table (canonical)."""
        pk_cols = cls._require_table(table)
        if table not in cls.TABLE_AUTOINCREMENT_PK_TABLES:
            missing_pks = [pk for pk in pk_cols if pk not in data]
            if missing_pks:
                raise _PersistenceError(
                    f"Missing required primary key column(s) {missing_pks} "
                    f"for table '{table}'."
                )

        with cls._resolve_connection() as c:
            cls._ensure_table_schema(c, table)
            try:
                pk_val = cls._insert_row(c, table, data, commit=commit)
                extra = {"fr_id": CREATE_FR, "table": table, "key": str(pk_val)}
                logger.info(
                    "%s: created record in %s (key=%s)",
                    CREATE_FR,
                    table,
                    pk_val,
                    extra=extra,
                )
                return pk_val
            except _PersistenceError as err:
                raise _PersistenceError(
                    f"Failed to create record in '{table}': {err}"
                ) from err

    @classmethod
    def create_entity(
        cls,
        entity_id: str,
        entity_type: str,
        scope: str,
        payload: str,
        *,
        revision: int = 1,
        created_at_utc: str | None = None,
        updated_at_utc: str | None = None,
        commit: bool = True,
    ) -> tuple[str, str]:
        """Insert a host entity record (canonical HostPersistence)."""
        now_iso = _current_utc_iso()
        data = {
            "entity_id": entity_id,
            "entity_type": entity_type,
            "scope": scope,
            "payload": payload,
            "revision": revision,
            "created_at_utc": created_at_utc or now_iso,
            "updated_at_utc": updated_at_utc or now_iso,
        }
        res = cls.create_record("host_entities", data, commit=commit)
        if isinstance(res, tuple):
            return (str(res[0]), str(res[1]))
        return (entity_id, entity_type)

    @classmethod
    def _resolve_cursor(
        cls,
        c: sqlite3.Connection,
        table: str,
        cursor_col: str | None,
        after_cursor: Any,
        order_by: str | None,
    ) -> tuple[str, list[Any], str | None]:
        """Resolve cursor column, where clause fragment, and ordering."""
        if cursor_col is None:
            return "", [], order_by
        clean_col = cursor_col.strip().strip('"')
        if not clean_col.replace("_", "").isalnum():
            raise _PersistenceError(f"Invalid cursor column name: '{cursor_col}'")
        valid_cols = {
            row[1] for row in c.execute(f'PRAGMA table_info("{table}")').fetchall()
        }
        if clean_col not in valid_cols:
            raise _PersistenceError(
                f"Invalid cursor column '{cursor_col}' for table '{table}'."
            )
        if after_cursor is None:
            return "", [], order_by
        return f'"{clean_col}" > ?', [after_cursor], order_by or f"{clean_col} ASC"

    @staticmethod
    def _build_limit_offset(limit: int | None, offset: int | None) -> str:
        """Construct SQL limit/offset fragment."""
        if limit is None:
            return ""
        return (
            f" LIMIT {limit} OFFSET {offset}"
            if offset is not None
            else f" LIMIT {limit}"
        )

    @classmethod
    def read_records(
        cls,
        table: str,
        *,
        pk_values: Mapping[str, Any] | None = None,
        where: Mapping[str, Any] | None = None,
        order_by: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        cursor_col: str | None = None,
        after_cursor: Any = None,
    ) -> list[dict[str, Any]]:
        """Query rows with filtering and pagination (canonical)."""
        if table not in cls.TABLE_PRIMARY_KEYS:
            extra = {"fr_id": READ_FR, "table": table}
            logger.error(
                "%s: rejected read_records for unapproved table %s",
                READ_FR,
                table,
                extra=extra,
            )
            raise _PersistenceError(
                f"Table '{table}' is not in approved table catalogue."
            )

        with cls._resolve_connection() as c:
            cls._ensure_table_schema(c, table)
            combined_where: dict[str, Any] = {**(pk_values or {}), **(where or {})}
            cursor_clause, c_params, eff_order = cls._resolve_cursor(
                c, table, cursor_col, after_cursor, order_by
            )
            where_sql, params = cls._build_where(combined_where)
            if cursor_clause:
                where_sql = (
                    f"{where_sql} AND {cursor_clause}"
                    if where_sql
                    else f" WHERE {cursor_clause}"
                )
                params.extend(c_params)

            order_sql = f" ORDER BY {eff_order}" if eff_order else ""
            limit_sql = cls._build_limit_offset(limit, offset)
            sql = f'SELECT * FROM "{table}"{where_sql}{order_sql}{limit_sql}'  # noqa: S608

            try:
                rows = [dict(r) for r in c.execute(sql, params).fetchall()]
            except sqlite3.Error as err:
                extra_err = {"fr_id": READ_FR, "table": table, "error": str(err)}
                logger.exception(
                    "%s: read_records failed on %s", READ_FR, table, extra=extra_err
                )
                raise _PersistenceError(f"Query on '{table}' failed: {err}") from err

            extra_ok = {"fr_id": READ_FR, "table": table, "count": len(rows)}
            logger.debug(
                "%s: read_records returned %d rows from %s",
                READ_FR,
                len(rows),
                table,
                extra=extra_ok,
            )
            return rows

    @classmethod
    def read_entity(cls, entity_id: str, entity_type: str) -> dict[str, Any] | None:
        """Retrieve an entity by composite key (canonical HostPersistence)."""
        rows = cls.read_records(
            "host_entities",
            pk_values={"entity_id": entity_id, "entity_type": entity_type},
            limit=1,
        )
        return rows[0] if rows else None

    @classmethod
    def update_record(
        cls,
        table: str,
        pk_values: Mapping[str, Any],
        updates: Mapping[str, Any],
        *,
        expected_revision: int | None = None,
        revision_col: str = "revision",
        upsert: bool = False,
        commit: bool = True,
    ) -> int:
        """Update a row with revision verification or upsert (canonical)."""
        cls._require_table(table)
        if not pk_values:
            raise _PersistenceError(
                f"update_record requires non-empty pk_values for table '{table}'."
            )
        if not updates and not upsert:
            raise _PersistenceError(
                f"update_record requires non-empty update_values for table '{table}'."
            )

        with cls._resolve_connection() as c:
            cls._ensure_table_schema(c, table)
            prev_conn = getattr(cls._local, "conn", None)
            cls._local.conn = c
            try:
                if expected_revision is not None:
                    cols = {
                        row[1]
                        for row in c.execute(f'PRAGMA table_info("{table}")').fetchall()
                    }
                    if revision_col not in cols:
                        raise _PersistenceError(
                            f"Table '{table}' does not contain "
                            f"revision column '{revision_col}'."
                        )
                    existing_rows = cls.read_records(
                        table, pk_values=pk_values, limit=1
                    )
                    if existing_rows:
                        curr_rev = existing_rows[0].get(revision_col)
                        if curr_rev is not None and int(curr_rev) != expected_revision:
                            cur = int(curr_rev)
                            extra = {
                                "fr_id": UPDATE_FR,
                                "table": table,
                                "expected_revision": expected_revision,
                                "current_revision": cur,
                            }
                            msg = (
                                "%s: revision conflict on %s (expected=%d, current=%d)"
                            )
                            logger.warning(
                                msg,
                                UPDATE_FR,
                                table,
                                expected_revision,
                                cur,
                                extra=extra,
                            )
                            raise _RevisionConflictError(
                                expected_revision=expected_revision,
                                current_revision=cur,
                            )

                if upsert and not cls.read_records(table, pk_values=pk_values, limit=1):
                    cls._insert_row(c, table, {**pk_values, **updates}, commit=commit)
                    return 1

                affected = cls._update_row_by_pk(
                    c, table, pk_values, updates, commit=commit
                )
            finally:
                cls._local.conn = prev_conn

            extra_ok = {"fr_id": UPDATE_FR, "table": table, "affected": affected}
            logger.info(
                "%s: updated record in %s (affected=%d)",
                UPDATE_FR,
                table,
                affected,
                extra=extra_ok,
            )
            return affected

    @classmethod
    def update_entity(
        cls,
        entity_id: str,
        entity_type: str,
        payload: str,
        *,
        expected_revision: int | None = None,
        revision: int | None = None,
        updated_at_utc: str | None = None,
        commit: bool = True,
    ) -> int:
        """Update an entity with optimistic CAS revision verification (canonical)."""
        now_iso = _current_utc_iso()
        with cls._resolve_connection() as c:
            prev_conn = getattr(cls._local, "conn", None)
            cls._local.conn = c
            try:
                existing = cls.read_entity(entity_id, entity_type)
                if existing is None:
                    return 0
                curr_rev = int(existing.get("revision", 1))
                if expected_revision is not None and curr_rev != expected_revision:
                    raise _RevisionConflictError(
                        f"Entity '{entity_id}' revision conflict: "
                        f"expected {expected_revision}, found {curr_rev}",
                        expected_revision=expected_revision,
                        current_revision=curr_rev,
                    )
                updates = {
                    "payload": payload,
                    "revision": revision if revision is not None else curr_rev + 1,
                    "updated_at_utc": updated_at_utc or now_iso,
                }
                return cls.update_record(
                    "host_entities",
                    pk_values={"entity_id": entity_id, "entity_type": entity_type},
                    updates=updates,
                    commit=commit,
                )
            finally:
                cls._local.conn = prev_conn

    @classmethod
    def delete_record(
        cls,
        table: str,
        pk_values: Mapping[str, Any] | None = None,
        *,
        where: Mapping[str, Any] | None = None,
        check_references: bool = True,
        commit: bool = True,
    ) -> int:
        """Delete records with foreign key reference guards (canonical)."""
        cls._require_table(table)
        if not pk_values and not where:
            raise _PersistenceError(
                f"delete_record requires non-empty pk_values or where filter "
                f"for table '{table}'."
            )

        with cls._resolve_connection() as c:
            cls._ensure_table_schema(c, table)
            if pk_values:
                deleted = cls._delete_row_by_pk(
                    c,
                    table,
                    pk_values,
                    check_references=check_references,
                    commit=commit,
                )
            elif where is not None:
                deleted = cls._delete_rows(c, table, where)
            else:
                raise _PersistenceError(
                    f"Deletion requires non-empty criteria on '{table}'."
                )

            extra = {"fr_id": DELETE_FR, "table": table, "deleted": deleted}
            logger.info(
                "%s: deleted record(s) from %s (deleted=%d)",
                DELETE_FR,
                table,
                deleted,
                extra=extra,
            )
            return deleted

    @classmethod
    def delete_entity(
        cls, entity_id: str, entity_type: str, *, commit: bool = True
    ) -> bool:
        """Delete an entity by composite key (canonical HostPersistence)."""
        pk = {"entity_id": entity_id, "entity_type": entity_type}
        return cls.delete_record("host_entities", pk_values=pk, commit=commit) > 0

    @classmethod
    def _batch_op_create(
        cls, active_c: sqlite3.Connection, idx: int, op: _BatchOperation
    ) -> tuple[int, dict[str, Any]]:
        """Execute single batch create/insert operation."""
        if not op.data:
            raise _PersistenceError(
                f"Create operation at index {idx} on '{op.table}' "
                "requires non-empty data."
            )
        pk_res = cls._insert_row(active_c, op.table, op.data, commit=False)
        res = {"index": idx, "op": op.op_type.lower(), "table": op.table}
        return 1, {**res, "status": "created", "key": pk_res}

    @classmethod
    def _batch_op_update(
        cls, idx: int, op: _BatchOperation
    ) -> tuple[int, dict[str, Any]]:
        """Execute single batch update operation."""
        if not op.pk_values or not op.data:
            raise _PersistenceError(
                f"Update operation at index {idx} on '{op.table}' requires both "
                "pk_values and data."
            )
        aff = cls.update_record(
            op.table,
            op.pk_values,
            op.data,
            expected_revision=op.expected_revision,
            revision_col=op.revision_col,
            commit=False,
        )
        res = {"index": idx, "op": op.op_type.lower(), "table": op.table}
        return aff, {**res, "status": "updated", "affected": aff}

    @classmethod
    def _batch_op_delete(
        cls, idx: int, op: _BatchOperation
    ) -> tuple[int, dict[str, Any]]:
        """Execute single batch delete operation."""
        if not op.pk_values:
            raise _PersistenceError(
                f"Delete operation at index {idx} on '{op.table}' requires pk_values."
            )
        aff = cls.delete_record(op.table, op.pk_values, commit=False)
        res = {"index": idx, "op": op.op_type.lower(), "table": op.table}
        return aff, {**res, "status": "deleted", "affected": aff}

    @classmethod
    def _batch_op_upsert(
        cls, active_c: sqlite3.Connection, idx: int, op: _BatchOperation
    ) -> tuple[int, dict[str, Any]]:
        """Execute single batch upsert operation."""
        if not op.data:
            raise _PersistenceError(
                f"Upsert operation at index {idx} on '{op.table}' "
                "requires non-empty data."
            )
        pk_cols = cls.TABLE_PRIMARY_KEYS[op.table]
        target_pk = op.pk_values or {
            col: op.data[col] for col in pk_cols if col in op.data
        }
        if len(target_pk) != len(pk_cols):
            raise _PersistenceError(
                f"Upsert operation at index {idx} on '{op.table}' "
                "requires complete primary key specification."
            )
        res = {"index": idx, "op": "upsert", "table": op.table}
        if cls.read_records(op.table, pk_values=target_pk, limit=1):
            aff = cls.update_record(
                op.table,
                target_pk,
                op.data,
                expected_revision=op.expected_revision,
                revision_col=op.revision_col,
                commit=False,
            )
            return aff, {**res, "status": "updated", "affected": aff}
        pk_res = cls._insert_row(active_c, op.table, op.data, commit=False)
        return 1, {**res, "status": "inserted", "key": pk_res}

    @classmethod
    def _execute_batch_op(
        cls, active_c: sqlite3.Connection, idx: int, op: _BatchOperation
    ) -> tuple[int, dict[str, Any]]:
        """Dispatch a single batch operation to its typed handler."""
        op_type = op.op_type.lower()
        if op.table not in cls.TABLE_PRIMARY_KEYS:
            raise _PersistenceError(
                f"Table '{op.table}' at batch index {idx} is not in approved table set."
            )
        cls._ensure_table_schema(active_c, op.table)
        if op_type in ("create", "insert"):
            return cls._batch_op_create(active_c, idx, op)
        if op_type == "update":
            return cls._batch_op_update(idx, op)
        if op_type == "delete":
            return cls._batch_op_delete(idx, op)
        if op_type == "upsert":
            return cls._batch_op_upsert(active_c, idx, op)
        raise _PersistenceError(
            f"Unsupported batch operation '{op.op_type}' at index {idx}."
        )

    @classmethod
    def _reject_active_tx(cls) -> None:
        """Raise PersistenceError when a caller transaction is already active."""
        logger.error(
            "%s: caller transaction already active", BATCH_FR, extra={"fr_id": BATCH_FR}
        )
        raise _PersistenceError(
            "Batch operations require an idle connection with no active transaction."
        )

    @staticmethod
    def _check_settings_revision(c: sqlite3.Connection, expected: int) -> None:
        row = c.execute(
            "SELECT COALESCE(MAX(schema_version), 0) FROM host_settings"
        ).fetchone()
        current = int(row[0])
        if current != expected:
            raise _RevisionConflictError(
                expected_revision=expected, current_revision=current
            )

    @classmethod
    def apply_batch(
        cls,
        operations: Sequence[_BatchOperation],
        *,
        expected_settings_revision: int | None = None,
        revoke_active_sessions: bool = False,
    ) -> _BatchResult:
        """Execute atomic batch writes with rollback (canonical)."""
        if getattr(cls._local, "conn", None) is not None:
            cls._reject_active_tx()
        if (
            not operations
            and expected_settings_revision is None
            and not revoke_active_sessions
        ):
            return _BatchResult(total_operations=0, affected_rows=0, details=[])

        with cls._resolve_connection() as c:
            if c.in_transaction:
                cls._reject_active_tx()

            extra_start = {"fr_id": BATCH_FR, "operations_count": len(operations)}
            logger.debug(
                "%s: beginning atomic batch transaction with %d operations",
                BATCH_FR,
                len(operations),
                extra=extra_start,
            )
            details: list[dict[str, Any]] = []
            total_affected = 0
            cls._local.conn = c
            c.execute("BEGIN IMMEDIATE")
            try:
                if expected_settings_revision is not None:
                    cls._check_settings_revision(c, expected_settings_revision)
                for idx, op in enumerate(operations):
                    aff, detail = cls._execute_batch_op(c, idx, op)
                    total_affected += aff
                    details.append(detail)
                if revoke_active_sessions:
                    c.execute(
                        "UPDATE host_session SET status='REVOKED', revoked_at_utc=? "
                        "WHERE status='ACTIVE'",
                        (datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S"),),
                    )
                c.commit()
            except Exception as err:
                c.rollback()
                extra_err = {"fr_id": BATCH_FR, "error": str(err)}
                logger.exception(
                    "%s: batch transaction failed, rolled back completely",
                    BATCH_FR,
                    extra=extra_err,
                )
                if isinstance(err, _RevisionConflictError):
                    raise
                raise _PersistenceError(f"Batch transaction failed: {err}") from err
            finally:
                cls._local.conn = None

            extra_ok = {
                "fr_id": BATCH_FR,
                "total_operations": len(operations),
                "affected_rows": total_affected,
            }
            logger.info(
                "%s: committed atomic batch transaction with %d operations "
                "(%d affected rows)",
                BATCH_FR,
                len(operations),
                total_affected,
                extra=extra_ok,
            )
            return _BatchResult(
                total_operations=len(operations),
                affected_rows=total_affected,
                details=details,
            )


class HostPersistenceCLI:
    """Command-line interface formatter and demo runner for HostPersistence."""

    @staticmethod
    def format_output(result: Mapping[str, Any]) -> str:
        """Format batch result dictionary for CLI display."""
        t = result.get("total_operations", 0)
        a, d = result.get("affected_rows", 0), result.get("details", [])
        return f"total_operations: {t}\naffected_rows: {a}\ndetails: {d}"

    @classmethod
    def run_cli(cls, argv: Sequence[str] | None = None) -> int:
        """Run CLI diagnostic demonstration for HostPersistence."""
        _ = argv
        prev_db = HostPersistence.DEFAULT_DB_PATH
        with tempfile.TemporaryDirectory(
            prefix="hqai_persistence_cli_", ignore_cleanup_errors=True
        ) as tmp_dir:
            HostPersistence.DEFAULT_DB_PATH = Path(tmp_dir) / "demo.db"
            try:
                now = _current_utc_iso()
                pk = {"scope": "sys", "key": "demo_key"}
                ops = [
                    _BatchOperation(
                        "create",
                        "host_settings",
                        {**pk, "value_json": '{"active": true}', "updated_at_utc": now},
                    ),
                    _BatchOperation(
                        "update",
                        "host_settings",
                        {"value_json": '{"active": false}'},
                        pk,
                    ),
                ]
                res = HostPersistence.apply_batch(ops)
                sys.stdout.write(cls.format_output(res.to_dict()) + "\n")
                return 0
            finally:
                HostPersistence.DEFAULT_DB_PATH = prev_db


if __name__ == "__main__":
    raise SystemExit(HostPersistenceCLI.run_cli(sys.argv[1:]))
