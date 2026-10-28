"""The host's SQLite access gateway; no other host module should open the database.

CRUD calls return StandardResponse dictionaries. Writes are atomic and bounded
to 1,000 records. Filters are ANDed; mappings mean equality (None means IS NULL).
Use RecordFilter for comparisons or IN. Identifiers come from the live schema;
values are always bound parameters. No caller-supplied SQL is accepted.
"""

# Dynamic SQL below contains schema-validated, quoted identifiers and fixed
# operators only. All caller values are bound separately.
# ruff: noqa: S608

from __future__ import annotations

import base64
import math
import sqlite3
import threading
import time
from collections.abc import Callable, Generator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from app.host.logging import get_logger
from app.host.response import (
    ErrorCode,
    ResponseMetadata,
    StandardError,
    StandardResponse,
)

logger = get_logger(__name__)

type SQLiteValue = str | int | float | bytes | None
type Filters = Mapping[str, SQLiteValue] | Sequence[RecordFilter] | None
_MAX_RECORDS = 1000
_DEFAULT_PATH = Path(__file__).resolve().parents[2] / "data/database/haruquantai.db"
_OPERATORS = {
    "eq": "=",
    "ne": "!=",
    "lt": "<",
    "lte": "<=",
    "gt": ">",
    "gte": ">=",
    "like": "LIKE",
}


@dataclass(frozen=True, slots=True)
class RecordFilter:
    """One AND predicate: eq/ne/lt/lte/gt/gte/like/in/not_in.

    IN values must be a list or tuple of non-null SQLite values. Use eq/ne with
    None for IS NULL/IS NOT NULL. LIKE follows SQLite's standard wildcard rules.
    """

    column: str
    operator: str
    value: SQLiteValue | Sequence[SQLiteValue]


class PersistenceTransactionError(RuntimeError):
    """A grouped transaction was rolled back because a CRUD operation failed."""


class _OperationError(Exception):
    def __init__(self, code: ErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class _Table:
    name: str
    columns: tuple[str, ...]
    writable: tuple[str, ...]
    primary_key: tuple[str, ...]


def _quote(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _value(value: Any) -> SQLiteValue:
    if value is None or isinstance(value, (str, bytes, int)):
        if isinstance(value, int) and not -(2**63) <= value < 2**63:
            raise ValueError("Integer exceeds SQLite's signed 64-bit range")
        return value
    if isinstance(value, float) and math.isfinite(value):
        return value
    raise ValueError("Values must be SQLite scalars; encode JSON explicitly as text")


def _record(row: sqlite3.Row) -> dict[str, Any]:
    # Arbitrary BLOBs cannot be UTF-8 decoded by the JSON response serializer.
    return {
        key: {"$binary": base64.b64encode(value).decode("ascii")}
        if isinstance(value, bytes)
        else value
        for key, value in dict(row).items()
    }


class HostPersistence:
    """Central SQLite WAL persistence and transaction gateway.

    Each call opens and closes its own connection, making a gateway safe to share
    across threads. Connections enforce foreign keys and use a bounded busy wait.
    The default existing database is never silently created or migrated.

    transaction() yields a thread-bound gateway for grouping CRUD calls. Its
    successful responses are provisional until context exit commits the group.
    Any failed call makes the entire group rollback-only, even if ignored.
    """

    def __init__(
        self, database_path: str | Path = _DEFAULT_PATH, *, timeout: float = 5.0
    ) -> None:
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("timeout must be finite and positive")
        self.database_path = Path(database_path).resolve()
        self.timeout = timeout
        self._connection: sqlite3.Connection | None = None
        self._owner: int | None = None
        self._rollback_only = False
        self._closed = False

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.database_path.as_uri() + "?mode=rw",
            uri=True,
            timeout=self.timeout,
            isolation_level=None,
        )
        try:
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            mode = connection.execute("PRAGMA journal_mode").fetchone()[0]
            if mode.lower() != "wal":
                mode = connection.execute("PRAGMA journal_mode = WAL").fetchone()[0]
            if mode.lower() != "wal":
                raise _OperationError(ErrorCode.UNAVAILABLE, "WAL mode is unavailable")  # noqa: TRY301
            return connection
        except BaseException:
            connection.close()
            raise

    def ensure_code_editor_schema(self) -> dict[str, Any]:
        """Install additive editor session and indicator configuration storage."""

        def action(connection: sqlite3.Connection) -> dict[str, Any]:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS code_editor_state ("
                "id TEXT PRIMARY KEY, payload TEXT NOT NULL)"
            )
            return {"affected_rows": 0, "records": []}

        return self._run("code_editor.schema", write=True, action=action)

    def ensure_custom_data_schema(self) -> dict[str, Any]:
        """Install additive Data Manager custom-indicator tables atomically.

        Called explicitly by CustomData operations; never creates a database file.
        Existing definitions, observations and unrelated tables remain untouched.
        """
        statements = (
            (
                "CREATE TABLE IF NOT EXISTS datamgr_custom ("
                "id TEXT PRIMARY KEY, name TEXT NOT NULL COLLATE NOCASE UNIQUE, "
                "data_type TEXT NOT NULL, timeframe TEXT NOT NULL, "
                "values_json TEXT NOT NULL, "
                "system INTEGER NOT NULL DEFAULT 0, updated_at TEXT NOT NULL)"
            ),
            (
                "CREATE TABLE IF NOT EXISTS datamgr_custom_values ("
                "indicator_id TEXT NOT NULL REFERENCES datamgr_custom(id) "
                "ON DELETE CASCADE, "
                "timestamp TEXT NOT NULL, values_json TEXT NOT NULL, "
                "PRIMARY KEY(indicator_id, timestamp))"
            ),
            (
                "CREATE TABLE IF NOT EXISTS datamgr_custom_formats ("
                "name TEXT PRIMARY KEY COLLATE NOCASE, config_json TEXT NOT NULL)"
            ),
        )

        def action(connection: sqlite3.Connection) -> dict[str, Any]:
            for statement in statements:
                connection.execute(statement)
            return {"affected_rows": 0, "records": []}

        return self._run("custom_data.schema", write=True, action=action)

    def ensure_datasets_schema(self) -> dict[str, Any]:
        """Install additive Data Manager dataset catalog tables atomically."""
        statements = (
            (
                "CREATE TABLE IF NOT EXISTS datamgr_datasets ("
                "id TEXT PRIMARY KEY, source TEXT NOT NULL, symbol TEXT NOT NULL, "
                "underlying TEXT NOT NULL, "
                "timeframe TEXT NOT NULL, broker TEXT NOT NULL, "
                "timezone TEXT NOT NULL, "
                "category TEXT NOT NULL, date_from TEXT NOT NULL, "
                "date_to TEXT NOT NULL, bars INTEGER NOT NULL DEFAULT 0, "
                "created_at TEXT NOT NULL, updated_at TEXT NOT NULL, "
                "path TEXT NOT NULL DEFAULT '', "
                "data_kind TEXT NOT NULL DEFAULT 'bars', "
                "quality_score REAL NOT NULL DEFAULT 1.0, "
                "lineage_json TEXT NOT NULL DEFAULT '{}', "
                "schema_version INTEGER NOT NULL DEFAULT 1)"
            ),
        )

        def action(connection: sqlite3.Connection) -> dict[str, Any]:
            for statement in statements:
                connection.execute(statement)

            existing = {
                r[1] for r in connection.execute("PRAGMA table_info(datamgr_datasets)")
            }
            for column in ("symbol_definition_id", "session_id"):
                if column not in existing:
                    connection.execute(
                        f"ALTER TABLE datamgr_datasets ADD COLUMN {column} INTEGER"
                    )

            # Drop obsolete duplicate columns if present in existing databases
            cursor = connection.execute("PRAGMA table_info(datamgr_datasets)")
            existing_cols = {row[1] for row in cursor.fetchall()}
            if "instrument" in existing_cols:
                connection.execute(
                    "ALTER TABLE datamgr_datasets DROP COLUMN instrument"
                )
            if "broker_name" in existing_cols:
                connection.execute(
                    "ALTER TABLE datamgr_datasets DROP COLUMN broker_name"
                )

            # Migrate numeric broker IDs in datamgr_datasets to canonical broker names
            tables = {
                r[0]
                for r in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
            if "datamgr_broker" in tables:
                brokers = connection.execute(
                    "SELECT id, name FROM datamgr_broker"
                ).fetchall()
                for b_id, b_name in brokers:
                    clean = str(b_name).strip()
                    if clean.startswith("[[") and clean.endswith("]]"):
                        clean = clean[2:-2].strip()
                    connection.execute(
                        "UPDATE datamgr_datasets SET broker = ? WHERE broker = ?",
                        (clean, str(b_id)),
                    )
            return {"affected_rows": 0, "records": []}

        return self._run("datasets.schema", write=True, action=action)

    def ensure_broker_cost_schema(self) -> dict[str, Any]:
        """Add inherited profile costs without replacing existing catalog tables."""

        def action(connection: sqlite3.Connection) -> dict[str, Any]:
            columns = {
                row[1]
                for row in connection.execute("PRAGMA table_info(datamgr_broker)")
            }
            if columns:
                for column in ("spread_model_json", "commission_model_json"):
                    if column not in columns:
                        connection.execute(
                            f"ALTER TABLE datamgr_broker ADD COLUMN {column} "
                            'TEXT NOT NULL DEFAULT \'{"model":"inherit"}\''
                        )
            return {"affected_rows": 0, "records": []}

        return self._run("brokers.cost_schema", write=True, action=action)

    def _check_scope(self) -> None:
        if self._closed:
            raise _OperationError(ErrorCode.CONFLICT, "Transaction scope is closed")
        if self._owner is not None and self._owner != threading.get_ident():
            raise _OperationError(
                ErrorCode.CONFLICT, "Transaction belongs to another thread"
            )
        if self._rollback_only:
            raise _OperationError(ErrorCode.CONFLICT, "Transaction is rollback-only")

    @contextmanager
    def transaction(self) -> Generator[HostPersistence]:
        """Group operations atomically using `with gateway.transaction() as tx`.

        Use tx for all calls in the group. Nested groups are rejected. Connection
        and commit failures propagate; CRUD failures trigger an exception at exit.
        """
        self._check_scope()
        if self._connection is not None:
            raise PersistenceTransactionError("Nested transactions are not supported")
        connection = self._connect()
        scoped = HostPersistence(self.database_path, timeout=self.timeout)
        scoped._connection = connection
        scoped._owner = threading.get_ident()
        try:
            connection.execute("BEGIN IMMEDIATE")
            logger.debug("Persistence transaction started")
            yield scoped
            if scoped._rollback_only:
                raise PersistenceTransactionError(  # noqa: TRY301
                    "A failed operation rolled back the transaction"
                )
            connection.commit()
            logger.debug("Persistence transaction committed")
        except BaseException as error:
            connection.rollback()
            logger.warning(
                "Persistence transaction rolled back; cause=%s", type(error).__name__
            )
            raise
        finally:
            scoped._closed = True
            connection.close()

    @contextmanager
    def _session(self, *, write: bool) -> Generator[sqlite3.Connection]:
        self._check_scope()
        if self._connection is not None:
            yield self._connection
            return
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE" if write else "BEGIN")
            yield connection
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _run(
        self,
        operation: str,
        *,
        write: bool,
        action: Callable[[sqlite3.Connection], dict[str, Any]],
    ) -> dict[str, Any]:
        start = time.perf_counter()
        try:
            with self._session(write=write) as connection:
                data = action(connection)
                effects = (
                    ("Database records changed",)
                    if write and data["affected_rows"]
                    else ()
                )
                # Serialize before commit so serialization errors cannot hide a write.
                response = StandardResponse.success(
                    message="Operation completed",
                    data=data,
                    metadata=ResponseMetadata(
                        operation=operation,
                        duration_ms=(time.perf_counter() - start) * 1000,
                        side_effects=effects,
                        extensions={"provisional": self._connection is not None},
                    ),
                )
            response["metadata"]["duration_ms"] = (time.perf_counter() - start) * 1000
            logger.debug(
                "Persistence operation=%s completed; duration_ms=%.3f; provisional=%s",
                operation,
                response["metadata"]["duration_ms"],
                self._connection is not None,
            )
            return response
        except (_OperationError, ValueError, TypeError, sqlite3.Error) as error:
            if self._connection is not None:
                self._rollback_only = True
            code, message, retryable = _classify_error(error)
            log_failure = (
                logger.error
                if code == ErrorCode.UNAVAILABLE and not retryable
                else logger.warning
            )
            log_failure(
                "Persistence operation=%s failed; code=%s; retryable=%s; cause=%s",
                operation,
                code.value,
                retryable,
                type(error).__name__,
            )
            return StandardResponse.failure(
                message=message,
                error=StandardError(code=code, message=message, retryable=retryable),
                metadata=ResponseMetadata(
                    operation=operation,
                    duration_ms=(time.perf_counter() - start) * 1000,
                ),
            )

    @staticmethod
    def _table(connection: sqlite3.Connection, name: str) -> _Table:
        if not isinstance(name, str) or name.lower().startswith("sqlite_"):
            raise ValueError("A user table name is required")
        found = connection.execute(
            "SELECT name FROM main.sqlite_schema WHERE type = 'table' AND name = ?",
            (name,),
        ).fetchone()
        if found is None:
            raise _OperationError(ErrorCode.NOT_FOUND, "Table does not exist")
        columns = connection.execute(
            f"PRAGMA main.table_xinfo({_quote(name)})"
        ).fetchall()
        return _Table(
            name=name,
            columns=tuple(row["name"] for row in columns),
            writable=tuple(row["name"] for row in columns if row["hidden"] == 0),
            primary_key=tuple(
                row["name"]
                for row in sorted(columns, key=lambda item: item["pk"])
                if row["pk"]
            ),
        )

    @staticmethod
    def _column(table: _Table, column: str, *, writable: bool = False) -> str:
        if column not in (table.writable if writable else table.columns):
            raise ValueError("Unknown or non-writable column")
        return _quote(column)

    def _where(self, table: _Table, filters: Filters) -> tuple[str, list[SQLiteValue]]:
        predicates = (
            [RecordFilter(key, "eq", value) for key, value in filters.items()]
            if isinstance(filters, Mapping)
            else list(filters or ())
        )
        clauses: list[str] = []
        parameters: list[SQLiteValue] = []
        for predicate in predicates:
            if not isinstance(predicate, RecordFilter):
                raise TypeError("Filters must be a mapping or RecordFilter sequence")
            column = self._column(table, predicate.column)
            operator, value = predicate.operator, predicate.value
            if operator in ("in", "not_in"):
                if not isinstance(value, (list, tuple)) or len(value) > _MAX_RECORDS:
                    raise ValueError("IN filters require up to 1000 values")
                if any(item is None for item in value):
                    raise ValueError("Use eq/ne for NULL comparisons")
                parameters.extend(_value(item) for item in value)
                placeholders = ", ".join("?" for _ in value)
                sql_operator = "IN" if operator == "in" else "NOT IN"
                clauses.append(f"{column} {sql_operator} ({placeholders})")
            elif operator in ("eq", "ne") and value is None:
                clauses.append(f"{column} IS {'NOT ' if operator == 'ne' else ''}NULL")
            elif operator in _OPERATORS and value is not None:
                clauses.append(f"{column} {_OPERATORS[operator]} ?")
                parameters.append(_value(value))
            else:
                raise ValueError("Unsupported filter operator or NULL comparison")
        return " AND ".join(clauses), parameters

    def create_records(
        self,
        table: str,
        values: Mapping[str, SQLiteValue] | Sequence[Mapping[str, SQLiteValue]],
    ) -> dict[str, Any]:
        """Insert one mapping or up to 1000 mappings atomically, returning rows.

        Rows may contain different columns; omitted columns use database defaults.
        An empty mapping inserts DEFAULT VALUES. An empty batch is rejected.
        """

        def action(connection: sqlite3.Connection) -> dict[str, Any]:
            schema = self._table(connection, table)
            rows = [values] if isinstance(values, Mapping) else list(values)
            if not 1 <= len(rows) <= _MAX_RECORDS:
                raise ValueError("Insert requires between 1 and 1000 records")
            records = []
            for row in rows:
                if not isinstance(row, Mapping):
                    raise TypeError("Each record must be a mapping")
                columns = [self._column(schema, key, writable=True) for key in row]
                parameters = [_value(value) for value in row.values()]
                clause = (
                    f"({', '.join(columns)}) VALUES ({', '.join('?' for _ in row)})"
                    if row
                    else "DEFAULT VALUES"
                )
                result = connection.execute(
                    f"INSERT INTO {_quote(table)} {clause} RETURNING *", parameters
                ).fetchone()
                if result is not None:
                    records.append(_record(result))
            return {"affected_rows": len(records), "records": records}

        return self._run("create_records", write=True, action=action)

    def read_records(
        self,
        table: str,
        *,
        filters: Filters = None,
        columns: Sequence[str] | None = None,
        limit: int = 100,
        offset: int = 0,
        pagination: Literal["offset", "cursor"] = "offset",
        cursor: Mapping[str, SQLiteValue] | None = None,
        order_by: Sequence[str] | None = None,
        descending: bool = False,
    ) -> dict[str, Any]:
        """Read a bounded page with AND filters and validated column ordering.

        Cursor mode orders by the full primary key and returns next_cursor as a
        key mapping. Reuse it with the same table, filters, and direction. Nullable
        keys containing NULL require offset mode. Offset mode defaults to primary
        key order (all columns if no key). Pages are separate snapshot reads.
        BLOB cells are represented as {"$binary": "base64..."} in JSON output.
        """

        def action(connection: sqlite3.Connection) -> dict[str, Any]:
            schema = self._table(connection, table)
            _check_pagination(limit, offset, pagination, cursor)
            if not isinstance(descending, bool):
                raise TypeError("descending must be a bool")
            selected = tuple(columns) if columns is not None else schema.columns
            ordering = (
                tuple(order_by)
                if order_by is not None
                else schema.primary_key or schema.columns
            )
            if (
                not selected
                or not ordering
                or isinstance(columns, str)
                or isinstance(order_by, str)
            ):
                raise ValueError("Columns and ordering must be non-empty sequences")
            for column in (*selected, *ordering):
                self._column(schema, column)
            where, parameters = self._where(schema, filters)
            if pagination == "cursor":
                if not schema.primary_key or ordering != schema.primary_key:
                    raise ValueError("Cursor pagination requires primary key ordering")
                self._cursor_guard(connection, schema, where, parameters)
                if cursor is not None:
                    if set(cursor) != set(ordering) or any(
                        value is None for value in cursor.values()
                    ):
                        raise ValueError(
                            "Cursor must contain all non-null primary key values"
                        )
                    keys = ", ".join(_quote(key) for key in ordering)
                    marks = ", ".join("?" for _ in ordering)
                    # SQLite row comparisons also work for one-column keys.
                    comparison = "<" if descending else ">"
                    clause = f"({keys}) {comparison} ({marks})"
                    where = f"{where} AND {clause}" if where else clause
                    parameters.extend(_value(cursor[key]) for key in ordering)
            query_columns = tuple(dict.fromkeys((*selected, *ordering)))
            projection = ", ".join(_quote(column) for column in query_columns)
            direction = "DESC" if descending else "ASC"
            order = ", ".join(f"{_quote(column)} {direction}" for column in ordering)
            query = f"SELECT {projection} FROM {_quote(table)}"
            if where:
                query += f" WHERE {where}"
            query += f" ORDER BY {order} LIMIT ? OFFSET ?"
            rows = connection.execute(
                query, [*parameters, limit + 1, offset]
            ).fetchall()
            has_more = len(rows) > limit
            page = rows[:limit]
            converted = [_record(row) for row in page]
            next_cursor = (
                {key: converted[-1][key] for key in ordering}
                if pagination == "cursor" and has_more
                else None
            )
            _check_cursor_values(next_cursor)
            return {
                "records": [{key: row[key] for key in selected} for row in converted],
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "has_more": has_more,
                    "next_offset": offset + limit
                    if pagination == "offset" and has_more
                    else None,
                    "next_cursor": next_cursor,
                },
            }

        return self._run("read_records", write=False, action=action)

    @staticmethod
    def _cursor_guard(
        connection: sqlite3.Connection,
        schema: _Table,
        where: str,
        parameters: list[SQLiteValue],
    ) -> None:
        nulls = " OR ".join(f"{_quote(key)} IS NULL" for key in schema.primary_key)
        clause = f"({where}) AND ({nulls})" if where else nulls
        if connection.execute(
            f"SELECT 1 FROM {_quote(schema.name)} WHERE {clause} LIMIT 1", parameters
        ).fetchone():
            raise ValueError("NULL primary keys require offset pagination")

    def update_record(
        self, table: str, values: Mapping[str, SQLiteValue], *, filters: Filters
    ) -> dict[str, Any]:
        """Update exactly one matching row; ambiguous matches fail atomically."""

        def action(connection: sqlite3.Connection) -> dict[str, Any]:
            schema = self._table(connection, table)
            if not isinstance(values, Mapping) or not values:
                raise ValueError("Update values must be a non-empty mapping")
            where, parameters = self._where(schema, filters)
            self._check_targets(connection, schema, where, parameters, maximum=1)
            assignments = ", ".join(
                f"{self._column(schema, key, writable=True)} = ?" for key in values
            )
            rows = connection.execute(
                f"UPDATE {_quote(table)} SET {assignments} WHERE {where} RETURNING *",
                [*(_value(value) for value in values.values()), *parameters],
            ).fetchall()
            return {
                "affected_rows": len(rows),
                "records": [_record(row) for row in rows],
            }

        return self._run("update_record", write=True, action=action)

    @staticmethod
    def _check_targets(
        connection: sqlite3.Connection,
        schema: _Table,
        where: str,
        parameters: list[SQLiteValue],
        *,
        maximum: int,
    ) -> None:
        if not where:
            raise ValueError("Writes require non-empty filters")
        rows = connection.execute(
            f"SELECT 1 FROM {_quote(schema.name)} WHERE {where} LIMIT ?",
            [*parameters, maximum + 1],
        ).fetchall()
        if not rows:
            raise _OperationError(ErrorCode.NOT_FOUND, "No matching records")
        if len(rows) > maximum:
            raise _OperationError(
                ErrorCode.CONFLICT, "Too many records match the write filters"
            )

    def delete_record(self, table: str, *, filters: Filters) -> dict[str, Any]:
        """Delete up to 1000 filtered rows, refusing all inbound FK references.

        Guards apply even to CASCADE and SET NULL relationships. Only declared
        foreign keys can be discovered; application-only relationships are unknown.
        """

        def action(connection: sqlite3.Connection) -> dict[str, Any]:
            schema = self._table(connection, table)
            where, parameters = self._where(schema, filters)
            self._check_targets(
                connection, schema, where, parameters, maximum=_MAX_RECORDS
            )
            self._guard_references(connection, schema, where, parameters)
            rows = connection.execute(
                f"DELETE FROM {_quote(table)} WHERE {where} RETURNING *", parameters
            ).fetchall()
            return {
                "affected_rows": len(rows),
                "records": [_record(row) for row in rows],
            }

        return self._run("delete_record", write=True, action=action)

    def _guard_references(
        self,
        connection: sqlite3.Connection,
        parent: _Table,
        where: str,
        parameters: list[SQLiteValue],
    ) -> None:
        tables = connection.execute(
            "SELECT name FROM main.sqlite_schema WHERE type = 'table' "
            "AND substr(name, 1, 7) != 'sqlite_'"
        ).fetchall()
        for table in tables:
            child = table["name"]
            groups: dict[int, list[sqlite3.Row]] = {}
            for key in connection.execute(
                f"PRAGMA main.foreign_key_list({_quote(child)})"
            ):
                if key["table"].casefold() == parent.name.casefold():
                    groups.setdefault(key["id"], []).append(key)
            for keys in groups.values():
                keys.sort(key=lambda key: key["seq"])
                joins = []
                for index, key in enumerate(keys):
                    if key["to"] is None and index >= len(parent.primary_key):
                        raise _OperationError(
                            ErrorCode.CONFLICT, "Invalid foreign key schema"
                        )
                    target = key["to"] or parent.primary_key[index]
                    joins.append(f"p.{_quote(target)} = c.{_quote(key['from'])}")
                # A subquery keeps unqualified caller filter columns unambiguous.
                query = (
                    f"SELECT 1 FROM (SELECT * FROM {_quote(parent.name)} "
                    f"WHERE {where}) AS p "
                    f"JOIN {_quote(child)} AS c ON {' AND '.join(joins)} LIMIT 1"
                )
                if connection.execute(query, parameters).fetchone():
                    raise _OperationError(
                        ErrorCode.CONFLICT, "Records are referenced by a foreign key"
                    )


def _check_cursor_values(cursor: Mapping[str, Any] | None) -> None:
    if cursor and any(isinstance(value, dict) for value in cursor.values()):
        raise ValueError("BLOB primary keys require offset pagination")


def _check_pagination(
    limit: int, offset: int, pagination: str, cursor: Mapping[str, SQLiteValue] | None
) -> None:
    if (
        isinstance(limit, bool)
        or not isinstance(limit, int)
        or not 1 <= limit <= _MAX_RECORDS
    ):
        raise ValueError("limit must be between 1 and 1000")
    if (
        isinstance(offset, bool)
        or not isinstance(offset, int)
        or not 0 <= offset < 2**63
    ):
        raise ValueError("offset must be a non-negative SQLite integer")
    if pagination not in ("offset", "cursor"):
        raise ValueError("pagination must be offset or cursor")
    if pagination == "cursor" and offset:
        raise ValueError("Cursor pagination cannot use an offset")
    if cursor is not None and (
        pagination != "cursor" or not isinstance(cursor, Mapping)
    ):
        raise ValueError("cursor requires cursor pagination and a key mapping")


def _classify_error(error: Exception) -> tuple[ErrorCode, str, bool]:
    if isinstance(error, _OperationError):
        return error.code, str(error), False
    if isinstance(error, (TypeError, ValueError)):
        return ErrorCode.VALIDATION, "Invalid persistence arguments", False
    if isinstance(error, sqlite3.IntegrityError):
        return ErrorCode.CONFLICT, "Database constraint rejected the operation", False
    code = getattr(error, "sqlite_errorcode", 0) & 0xFF
    if code in (sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED):
        return ErrorCode.UNAVAILABLE, "Database is busy; retry the operation", True
    return ErrorCode.UNAVAILABLE, "Database operation could not be completed", False
