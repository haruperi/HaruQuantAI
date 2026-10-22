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

    records = HostPersistence.read_records("host_settings", {"scope": "ui"})
    ```

CLI Usage:
    ```bash
    uv run python -m app.host.persistence --verify
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
from typing import Any

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


def _current_utc_iso() -> str:
    """Return formatted ISO-8601 UTC timestamp."""
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _log(level: str, fr_id: str, msg: str, **extra: Any) -> None:
    """Emit structured requirement log entry via TelemetryLogger."""
    getattr(logger, level)("%s: %s", fr_id, msg, extra={"fr_id": fr_id, **extra})


def _row_res(
    table: str, key_cols: Mapping[str, Any], n: int, **kw: Any
) -> dict[str, Any]:
    """Build standard mutation result dictionary."""
    return {"table": table, "key_columns": dict(key_cols), "affected": n, **kw}


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
            _log("exception", CREATE_FR, f"connection failed to {resolved}")
            raise _PersistenceError(f"Database connection failed: {err}") from err
        return conn

    @classmethod
    def _ensure_table_schema(cls, conn: sqlite3.Connection, table: str) -> None:
        """Ensure a specific table exists by executing its canonical DDL statement."""
        if table not in cls.TABLE_DDL_MAP:
            _log("error", CREATE_FR, f"rejected schema creation for {table}")
            raise _PersistenceError(
                f"Table '{table}' is not an approved operational persistence table."
            )
        try:
            conn.execute(cls.TABLE_DDL_MAP[table])
            if table == "datamgr_instruments":
                present = {
                    str(row[1])
                    for row in conn.execute('PRAGMA table_info("datamgr_instruments")')
                }
                if "specification_meta" not in present:
                    raise _PersistenceError(
                        "Unsupported legacy instrument schema; grouped schema required."
                    )
        except sqlite3.Error as err:
            _log("exception", CREATE_FR, f"failed schema for {table}")
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
    def _build_where(filters: Mapping[str, Any] | None) -> tuple[str, list[Any]]:
        """Construct parameterized WHERE clause from dictionary mapping."""
        if not filters:
            return "", []
        clauses: list[str] = []
        params: list[Any] = []
        for col, val in filters.items():
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
        values: Mapping[str, Any],
        *,
        commit: bool = True,
    ) -> tuple[Any, dict[str, Any]]:
        """Insert a row into table and return (pk_val, pk_dict)."""
        pk_cols = cls._require_table(table)
        if not values:
            raise _PersistenceError("Insert values dictionary cannot be empty.")
        columns = list(values.keys())
        placeholders = ", ".join("?" for _ in columns)
        quoted_cols = ", ".join(f'"{col}"' for col in columns)
        sql = f'INSERT INTO "{table}" ({quoted_cols}) VALUES ({placeholders})'  # noqa: S608
        try:
            with conn if commit else nullcontext():
                last_id = conn.execute(sql, [values[c] for c in columns]).lastrowid
        except sqlite3.Error as err:
            _log("exception", CREATE_FR, f"insert failed on {table}")
            raise _PersistenceError(f"Insert into '{table}' failed: {err}") from err

        if len(pk_cols) == 1:
            col0 = pk_cols[0]
            pk_val = values.get(col0, last_id)
            return pk_val, {col0: pk_val}
        return tuple(values[k] for k in pk_cols), {k: values[k] for k in pk_cols}

    @classmethod
    def _update_row_by_pk(
        cls,
        conn: sqlite3.Connection,
        table: str,
        key_columns: Mapping[str, Any],
        updates: Mapping[str, Any],
        *,
        commit: bool = True,
    ) -> int:
        """Update a row by primary key."""
        expected_pks = cls._require_table(table)
        if not updates:
            raise _PersistenceError("Updates mapping cannot be empty.")
        missing_pks = [pk for pk in expected_pks if pk not in key_columns]
        if missing_pks:
            raise _PersistenceError(
                f"Missing primary key columns for '{table}': {missing_pks}"
            )
        set_str = ", ".join(f'"{col}" = ?' for col in updates)
        where_str = " AND ".join(f'"{pk}" = ?' for pk in expected_pks)
        sql = f'UPDATE "{table}" SET {set_str} WHERE {where_str}'  # noqa: S608
        params = list(updates.values()) + [key_columns[pk] for pk in expected_pks]
        try:
            with conn if commit else nullcontext():
                return conn.execute(sql, params).rowcount
        except sqlite3.Error as err:
            _log("exception", UPDATE_FR, f"update failed on {table}")
            raise _PersistenceError(f"Update on '{table}' failed: {err}") from err

    @classmethod
    def _delete_row_by_pk(
        cls,
        conn: sqlite3.Connection,
        table: str,
        key_columns: Mapping[str, Any],
        *,
        check_references: bool = True,
        commit: bool = True,
    ) -> int:
        """Delete a row by primary key with foreign key guards."""
        expected_pks = cls._require_table(table)
        missing_pks = [pk for pk in expected_pks if pk not in key_columns]
        if missing_pks:
            raise _PersistenceError(
                f"Missing primary key columns for '{table}': {missing_pks}"
            )
        if check_references and table in cls.TABLE_FOREIGN_KEY_GUARDS:
            for child_tbl, fk_col, pk_col in cls.TABLE_FOREIGN_KEY_GUARDS[table]:
                if pk_col in key_columns:
                    cls._ensure_table_schema(conn, child_tbl)
                    query = f'SELECT COUNT(*) FROM "{child_tbl}" WHERE "{fk_col}" = ?'  # noqa: S608
                    cnt = int(conn.execute(query, (key_columns[pk_col],)).fetchone()[0])
                    if cnt > 0:
                        _log(
                            "error",
                            DELETE_FR,
                            f"delete blocked by FK guard on {table} "
                            f"({child_tbl}: {cnt})",
                        )
                        raise _PersistenceError(
                            f"Deletion blocked for '{table}': {cnt} dependent "
                            f"row(s) exist in '{child_tbl}'."
                        )
        where_str = " AND ".join(f'"{pk}" = ?' for pk in expected_pks)
        sql = f'DELETE FROM "{table}" WHERE {where_str}'  # noqa: S608
        params = [key_columns[pk] for pk in expected_pks]
        try:
            with conn if commit else nullcontext():
                return conn.execute(sql, params).rowcount
        except sqlite3.Error as err:
            _log("exception", DELETE_FR, f"delete failed on {table}")
            raise _PersistenceError(f"Delete on '{table}' failed: {err}") from err

    @classmethod
    def _delete_rows(
        cls,
        conn: sqlite3.Connection,
        table: str,
        filters: Mapping[str, Any],
        *,
        commit: bool = True,
    ) -> int:
        """Delete multiple rows matching filter criteria."""
        cls._require_table(table)
        where_sql, params = cls._build_where(filters)
        sql = f'DELETE FROM "{table}"{where_sql}'  # noqa: S608
        try:
            with conn if commit else nullcontext():
                return conn.execute(sql, params).rowcount
        except sqlite3.Error as err:
            raise _PersistenceError(f"Delete rows on '{table}' failed: {err}") from err

    @classmethod
    def create_record(
        cls, table: str, values: Mapping[str, Any], *, commit: bool = True
    ) -> dict[str, Any]:
        """Insert a single record into an approved database table."""
        pk_cols = cls._require_table(table)
        if table not in cls.TABLE_AUTOINCREMENT_PK_TABLES:
            missing_pks = [pk for pk in pk_cols if pk not in values]
            if missing_pks:
                raise _PersistenceError(
                    f"Missing required primary key column(s) {missing_pks} "
                    f"for table '{table}'."
                )
        with cls._resolve_connection() as c:
            cls._ensure_table_schema(c, table)
            try:
                pk_val, pk_dict = cls._insert_row(c, table, values, commit=commit)
                _log(
                    "info",
                    CREATE_FR,
                    f"created record in {table} (key={pk_val})",
                    table=table,
                )
                rec = {**values, **pk_dict}
                return {
                    "table": table,
                    "key": pk_val,
                    "pk": pk_dict,
                    "record": rec,
                    "created": True,
                }
            except _PersistenceError as err:
                raise _PersistenceError(
                    f"Failed to create record in '{table}': {err}"
                ) from err

    @classmethod
    def create_entity(
        cls, entity: str, values: Mapping[str, Any], *, commit: bool = True
    ) -> dict[str, Any]:
        """Insert a domain entity record into host_entities."""
        entity_id = str(values.get("entity_id", "")).strip()
        if not entity_id:
            raise _PersistenceError(
                f"create_entity for '{entity}' requires non-empty 'entity_id'."
            )
        now_iso = _current_utc_iso()
        row = {
            "entity_id": entity_id,
            "entity_type": entity,
            "scope": str(values.get("scope", "global")),
            "payload": str(values.get("payload", "{}")),
            "revision": int(values.get("revision", 1)),
            "created_at_utc": str(values.get("created_at_utc") or now_iso),
            "updated_at_utc": str(values.get("updated_at_utc") or now_iso),
        }
        res = cls.create_record("host_entities", row, commit=commit)
        return {
            "entity": entity,
            "entity_id": entity_id,
            "scope": row["scope"],
            "revision": row["revision"],
            "record": res["record"],
            "created": True,
        }

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

    @classmethod
    def read_records(
        cls,
        table: str,
        filters: Mapping[str, Any] | None = None,
        *,
        limit: int = 100,
        offset: int = 0,
        order_by: str | None = None,
        cursor_col: str | None = None,
        after_cursor: Any = None,
    ) -> list[dict[str, Any]]:
        """Query rows with parameterized filtering and cursor/offset pagination."""
        if table not in cls.TABLE_PRIMARY_KEYS:
            _log("error", READ_FR, f"rejected read_records for {table}", table=table)
            raise _PersistenceError(
                f"Table '{table}' is not in approved table catalogue."
            )
        with cls._resolve_connection() as c:
            cls._ensure_table_schema(c, table)
            cursor_clause, c_params, eff_order = cls._resolve_cursor(
                c, table, cursor_col, after_cursor, order_by
            )
            where_sql, params = cls._build_where(filters)
            if cursor_clause:
                where_sql = (
                    f"{where_sql} AND {cursor_clause}"
                    if where_sql
                    else f" WHERE {cursor_clause}"
                )
                params.extend(c_params)
            order_sql = f" ORDER BY {eff_order}" if eff_order else ""
            limit_sql = f" LIMIT {limit} OFFSET {offset}" if limit > 0 else ""
            sql = f'SELECT * FROM "{table}"{where_sql}{order_sql}{limit_sql}'  # noqa: S608
            try:
                rows = [dict(r) for r in c.execute(sql, params).fetchall()]
            except sqlite3.Error as err:
                _log(
                    "exception",
                    READ_FR,
                    f"read_records failed on {table}",
                    error=str(err),
                )
                raise _PersistenceError(f"Query on '{table}' failed: {err}") from err
            _log(
                "debug", READ_FR, f"read_records returned {len(rows)} rows from {table}"
            )
            return rows

    @classmethod
    def read_entity(
        cls,
        entity: str,
        entity_id: str | None = None,
        filters: Mapping[str, Any] | None = None,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Query domain entity records by entity type, optional ID, and filters."""
        combined: dict[str, Any] = {"entity_type": entity, **(filters or {})}
        if entity_id is not None:
            combined["entity_id"] = entity_id
        return cls.read_records("host_entities", combined, limit=limit, offset=offset)

    @classmethod
    def update_record(
        cls,
        table: str,
        key_columns: Mapping[str, Any],
        updates: Mapping[str, Any],
        *,
        expected_revision: int | None = None,
        revision_col: str = "revision",
        upsert: bool = False,
        commit: bool = True,
    ) -> dict[str, Any]:
        """Update a row with optimistic revision CAS verification or upsert."""
        cls._require_table(table)
        if not key_columns:
            raise _PersistenceError(
                f"update_record requires non-empty key_columns for table '{table}'."
            )
        if not updates and not upsert:
            raise _PersistenceError(
                f"update_record requires non-empty updates for table '{table}'."
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
                    existing_rows = cls.read_records(table, key_columns, limit=1)
                    if existing_rows:
                        curr_rev = existing_rows[0].get(revision_col)
                        if curr_rev is not None and int(curr_rev) != expected_revision:
                            cur = int(curr_rev)
                            _log(
                                "warning",
                                UPDATE_FR,
                                f"revision conflict on {table} "
                                f"(expected={expected_revision}, current={cur})",
                            )
                            raise _RevisionConflictError(
                                expected_revision=expected_revision,
                                current_revision=cur,
                            )
                if upsert and not cls.read_records(table, key_columns, limit=1):
                    cls._insert_row(c, table, {**key_columns, **updates}, commit=commit)
                    return _row_res(table, key_columns, 1, updated=1, upserted=True)
                affected = cls._update_row_by_pk(
                    c, table, key_columns, updates, commit=commit
                )
            finally:
                cls._local.conn = prev_conn
            _log("info", UPDATE_FR, f"updated record in {table} (affected={affected})")
            return _row_res(
                table, key_columns, affected, updated=affected, upserted=False
            )

    @classmethod
    def update_entity(
        cls,
        entity: str,
        entity_id: str,
        updates: Mapping[str, Any],
        *,
        expected_revision: int | None = None,
        commit: bool = True,
    ) -> dict[str, Any]:
        """Update a domain entity with optimistic CAS revision verification."""
        now_iso = _current_utc_iso()
        with cls._resolve_connection() as c:
            prev_conn = getattr(cls._local, "conn", None)
            cls._local.conn = c
            try:
                rows = cls.read_entity(entity, entity_id, limit=1)
                if not rows:
                    return {
                        "entity": entity,
                        "entity_id": entity_id,
                        "affected": 0,
                        "updated": 0,
                        "revision": None,
                    }
                curr_rev = int(rows[0].get("revision", 1))
                if expected_revision is not None and curr_rev != expected_revision:
                    raise _RevisionConflictError(
                        f"Entity '{entity_id}' revision conflict: "
                        f"expected {expected_revision}, found {curr_rev}",
                        expected_revision=expected_revision,
                        current_revision=curr_rev,
                    )
                target_rev = (
                    int(updates["revision"])
                    if "revision" in updates and updates["revision"] is not None
                    else curr_rev + 1
                )
                row_upd: dict[str, Any] = {
                    "revision": target_rev,
                    "updated_at_utc": str(updates.get("updated_at_utc") or now_iso),
                    **{
                        k: str(updates[k]) for k in ("payload", "scope") if k in updates
                    },
                }
                pk = {"entity_id": entity_id, "entity_type": entity}
                res = cls.update_record("host_entities", pk, row_upd, commit=commit)
                return {
                    "entity": entity,
                    "entity_id": entity_id,
                    "affected": res["affected"],
                    "updated": res["updated"],
                    "revision": target_rev,
                }
            finally:
                cls._local.conn = prev_conn

    @classmethod
    def delete_record(
        cls,
        table: str,
        key_columns: Mapping[str, Any],
        *,
        check_references: bool = True,
        commit: bool = True,
    ) -> dict[str, Any]:
        """Delete records with foreign key reference guards."""
        expected_pks = cls._require_table(table)
        if not key_columns:
            raise _PersistenceError(
                f"delete_record requires non-empty key_columns for table '{table}'."
            )
        with cls._resolve_connection() as c:
            cls._ensure_table_schema(c, table)
            if all(pk in key_columns for pk in expected_pks):
                deleted = cls._delete_row_by_pk(
                    c,
                    table,
                    key_columns,
                    check_references=check_references,
                    commit=commit,
                )
            else:
                deleted = cls._delete_rows(c, table, key_columns, commit=commit)
            _log(
                "info", DELETE_FR, f"deleted record(s) from {table} (deleted={deleted})"
            )
            return _row_res(table, key_columns, deleted, deleted=deleted)

    @classmethod
    def delete_entity(
        cls, entity: str, entity_id: str, *, commit: bool = True
    ) -> dict[str, Any]:
        """Delete a domain entity by entity type and entity_id."""
        pk = {"entity_id": entity_id, "entity_type": entity}
        res = cls.delete_record("host_entities", pk, commit=commit)
        return {
            "entity": entity,
            "entity_id": entity_id,
            "deleted": res["deleted"],
            "affected": res["affected"],
        }

    @classmethod
    def _batch_upsert(
        cls,
        active_c: sqlite3.Connection,
        idx: int,
        table: str,
        op: Mapping[str, Any],
    ) -> tuple[int, dict[str, Any]]:
        """Execute a single batch upsert operation."""
        values = op.get("values") if "values" in op else op.get("updates")
        key_cols = op.get("key_columns")
        if not isinstance(values, Mapping) or not values:
            raise _PersistenceError(
                f"Upsert operation at index {idx} on '{table}' requires values."
            )
        pk_cols = cls.TABLE_PRIMARY_KEYS[table]
        target_pk = (
            dict(key_cols)
            if isinstance(key_cols, Mapping) and key_cols
            else {col: values[col] for col in pk_cols if col in values}
        )
        if len(target_pk) != len(pk_cols):
            raise _PersistenceError(
                f"Upsert operation at index {idx} on '{table}' "
                "requires complete primary key specification."
            )
        base = {"index": idx, "op": "upsert", "table": table}
        if cls.read_records(table, target_pk, limit=1):
            upd = cls.update_record(
                table,
                target_pk,
                values,
                expected_revision=op.get("expected_revision"),
                revision_col=str(op.get("revision_col", "revision")),
                commit=False,
            )
            aff = int(upd["affected"])
            return aff, {**base, "status": "updated", "affected": aff}
        pk_val, _ = cls._insert_row(active_c, table, values, commit=False)
        return 1, {**base, "status": "inserted", "key": pk_val}

    @classmethod
    def _execute_batch_op(
        cls, active_c: sqlite3.Connection, idx: int, op: Mapping[str, Any]
    ) -> tuple[int, dict[str, Any]]:
        """Dispatch a single batch mapping operation inside an active transaction."""
        op_type = str(op.get("op_type") or op.get("op") or "").lower()
        table = str(op.get("table") or "")
        if table not in cls.TABLE_PRIMARY_KEYS:
            raise _PersistenceError(
                f"Table '{table}' at batch index {idx} is not in approved table set."
            )
        cls._ensure_table_schema(active_c, table)
        values = op.get("values") if "values" in op else op.get("updates")
        key_cols = op.get("key_columns")
        base = {"index": idx, "op": op_type, "table": table}

        if op_type in ("create", "insert"):
            if not isinstance(values, Mapping) or not values:
                raise _PersistenceError(
                    f"Create operation at index {idx} on '{table}' requires values."
                )
            pk_val, _ = cls._insert_row(active_c, table, values, commit=False)
            return 1, {**base, "status": "created", "key": pk_val}
        if op_type == "update":
            if (
                not isinstance(key_cols, Mapping)
                or not key_cols
                or not isinstance(values, Mapping)
                or not values
            ):
                raise _PersistenceError(
                    f"Update operation at index {idx} on '{table}' requires "
                    "key_columns and values."
                )
            upd = cls.update_record(
                table,
                key_cols,
                values,
                expected_revision=op.get("expected_revision"),
                revision_col=str(op.get("revision_col", "revision")),
                commit=False,
            )
            aff = int(upd["affected"])
            return aff, {**base, "status": "updated", "affected": aff}
        if op_type == "delete":
            if not isinstance(key_cols, Mapping) or not key_cols:
                raise _PersistenceError(
                    f"Delete operation at index {idx} on '{table}' "
                    "requires key_columns."
                )
            d_res = cls.delete_record(table, key_cols, commit=False)
            aff = int(d_res["deleted"])
            return aff, {**base, "status": "deleted", "affected": aff}
        if op_type == "upsert":
            return cls._batch_upsert(active_c, idx, table, op)
        raise _PersistenceError(
            f"Unsupported batch operation '{op_type}' at index {idx}."
        )

    @classmethod
    def _reject_active_tx(cls) -> None:
        """Raise PersistenceError when a caller transaction is already active."""
        _log("error", BATCH_FR, "caller transaction already active")
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
        operations: Sequence[Mapping[str, Any]],
        *,
        expected_settings_revision: int | None = None,
        revoke_active_sessions: bool = False,
    ) -> dict[str, Any]:
        """Execute atomic multi-row batch writes with all-or-nothing rollback."""
        if getattr(cls._local, "conn", None) is not None:
            cls._reject_active_tx()
        if (
            not operations
            and expected_settings_revision is None
            and not revoke_active_sessions
        ):
            return {"total_operations": 0, "affected_rows": 0, "details": []}

        with cls._resolve_connection() as c:
            if c.in_transaction:
                cls._reject_active_tx()
            _log(
                "debug",
                BATCH_FR,
                f"beginning atomic batch transaction with {len(operations)} operations",
                operations_count=len(operations),
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
                _log(
                    "exception",
                    BATCH_FR,
                    "batch transaction failed, rolled back completely",
                    error=str(err),
                )
                if isinstance(err, _RevisionConflictError):
                    raise
                raise _PersistenceError(f"Batch transaction failed: {err}") from err
            finally:
                cls._local.conn = None

            _log(
                "info",
                BATCH_FR,
                f"committed atomic batch ({len(operations)} ops, "
                f"{total_affected} rows)",
                total_operations=len(operations),
                affected_rows=total_affected,
            )
            return {
                "total_operations": len(operations),
                "affected_rows": total_affected,
                "details": details,
            }


class HostPersistenceCLI:
    """Command-line interface formatter and verification runner for HostPersistence."""

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
                now, pk = _current_utc_iso(), {"scope": "sys", "key": "demo_key"}
                v1 = {**pk, "value_json": '{"active": true}', "updated_at_utc": now}
                v2 = {"value_json": '{"active": false}'}
                ops: list[Mapping[str, Any]] = [
                    {"op_type": "create", "table": "host_settings", "values": v1},
                    {
                        "op_type": "update",
                        "table": "host_settings",
                        "key_columns": pk,
                        "values": v2,
                    },
                ]
                res = HostPersistence.apply_batch(ops)
                sys.stdout.write(cls.format_output(res) + "\n")
                return 0
            finally:
                HostPersistence.DEFAULT_DB_PATH = prev_db


if __name__ == "__main__":
    raise SystemExit(HostPersistenceCLI.run_cli(sys.argv[1:]))
