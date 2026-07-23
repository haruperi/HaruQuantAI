"""Bounded short-lived SQLite transaction execution."""

from __future__ import annotations

import math
import sqlite3
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn

from app.services.data._settings import DataSettings, get_data_settings
from app.services.data.contracts import DataError
from app.services.data.persistence.contracts import (
    ResultScalar,
    TransactionRequest,
    TransactionResult,
)
from app.utils import logger

_SQLITE_URL_PREFIX = "sqlite:///"
_SQLITE_PRIMARY_CODE_MASK = 0xFF
_DISALLOWED_SQL_ACTIONS = frozenset(
    {
        sqlite3.SQLITE_ATTACH,
        sqlite3.SQLITE_DETACH,
        sqlite3.SQLITE_TRANSACTION,
    }
)


@dataclass(frozen=True, slots=True)
class _DatabaseConfig:
    """Validated call-time SQLite configuration."""

    database_path: Path
    busy_timeout_seconds: float


def _error(code: str, request_id: str, stage: str) -> DataError:
    """Build one redacted database-boundary error."""
    logger.debug("Running DATA function: _error")
    return DataError(
        code,
        safe_details={"operation": "execute_transaction", "stage": stage},
        request_id=request_id,
    )


def _parse_database_config(settings: DataSettings) -> _DatabaseConfig:
    """Parse Data-owned database configuration or raise a safe local error."""
    logger.debug("Running DATA function: _parse_database_config")
    database_url = settings.database_url
    data_directory = settings.data_dir
    busy_timeout_seconds = settings.sqlite_busy_timeout_seconds
    if database_url is None or data_directory is None or busy_timeout_seconds is None:
        raise ValueError("required database settings are missing")
    if not database_url.startswith(_SQLITE_URL_PREFIX):
        raise ValueError("unsupported database URL")
    relative_value = database_url.removeprefix(_SQLITE_URL_PREFIX)
    if not relative_value or relative_value == ":memory:" or "?" in relative_value:
        raise ValueError("database URL must contain a relative file path")
    relative_path = Path(relative_value)
    if relative_path.is_absolute() or relative_path.drive:
        raise ValueError("database path must be relative")
    data_directory = data_directory.expanduser().resolve()
    if not data_directory.is_dir():
        raise ValueError("DATA_DIR must be an existing directory")
    database_path = (data_directory / relative_path).resolve()
    if not database_path.is_relative_to(data_directory):
        raise ValueError("database path escapes DATA_DIR")
    if not database_path.parent.is_dir():
        raise ValueError("database parent directory must already exist")
    if not math.isfinite(busy_timeout_seconds) or busy_timeout_seconds <= 0:
        raise ValueError("busy timeout must be finite and positive")
    return _DatabaseConfig(
        database_path=database_path,
        busy_timeout_seconds=busy_timeout_seconds,
    )


def _load_database_config(settings: DataSettings, request_id: str) -> _DatabaseConfig:
    """Resolve and map call-time database configuration failures."""
    logger.debug("Running DATA function: _load_database_config")
    try:
        return _parse_database_config(settings)
    except OSError, ValueError:
        raise _error("DB_CONNECTION_ERROR", request_id, "configuration") from None


def _open_connection(config: _DatabaseConfig, request_id: str) -> sqlite3.Connection:
    """Open one configured short-lived PEP 249 transaction connection."""
    logger.debug("Running DATA function: _open_connection")
    try:
        return sqlite3.connect(
            config.database_path,
            timeout=config.busy_timeout_seconds,
            autocommit=False,
        )
    except sqlite3.Error:
        raise _error("DB_CONNECTION_ERROR", request_id, "connection") from None


def _is_lock_conflict(error: sqlite3.OperationalError) -> bool:
    """Return whether an operational error is SQLite busy/locked evidence."""
    logger.debug("Running DATA function: _is_lock_conflict")
    error_code = getattr(error, "sqlite_errorcode", None)
    if not isinstance(error_code, int):
        return False
    primary_code = error_code & _SQLITE_PRIMARY_CODE_MASK
    return primary_code in {sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED}


def _authorize_sql(
    action_code: int,
    _arg1: str | None,
    _arg2: str | None,
    _database_name: str | None,
    _trigger_name: str | None,
) -> int:
    """Deny caller transaction control and cross-database attachment."""
    logger.debug("Running DATA function: _authorize_sql")
    if action_code in _DISALLOWED_SQL_ACTIONS:
        return sqlite3.SQLITE_DENY
    return sqlite3.SQLITE_OK


def _normalize_result_value(value: object, request_id: str) -> ResultScalar:
    """Validate one SQLite value against the public result scalar contract."""
    logger.debug("Running DATA function: _normalize_result_value")
    if value is None or isinstance(value, bool | int | str):
        return value
    if isinstance(value, float) and math.isfinite(value):
        return value
    raise _error("DATABASE_ERROR", request_id, "result_value")


def _collect_rows(
    cursor: sqlite3.Cursor,
    rows: list[Mapping[str, ResultScalar]],
    max_rows: int,
    request_id: str,
) -> None:
    """Append one ordered result set without exceeding its caller bound."""
    logger.debug("Running DATA function: _collect_rows")
    if cursor.description is None:
        return
    columns = tuple(str(description[0]) for description in cursor.description)
    if len(set(columns)) != len(columns):
        raise _error("DATABASE_ERROR", request_id, "result_columns")
    remaining = max_rows - len(rows)
    result_rows = cursor.fetchmany(remaining + 1)
    if len(result_rows) > remaining:
        raise _error("DATABASE_ERROR", request_id, "result_bound")
    for result_row in result_rows:
        normalized = tuple(
            _normalize_result_value(value, request_id) for value in result_row
        )
        rows.append(dict(zip(columns, normalized, strict=True)))


def _execute_plan(
    connection: sqlite3.Connection, request: TransactionRequest
) -> tuple[tuple[Mapping[str, ResultScalar], ...], int]:
    """Execute every caller statement in order under one open transaction."""
    logger.debug("Running DATA function: _execute_plan")
    rows: list[Mapping[str, ResultScalar]] = []
    affected_rows = 0
    connection.set_authorizer(_authorize_sql)
    try:
        for statement, parameters in zip(
            request.plan.statements,
            request.plan.parameter_sets,
            strict=True,
        ):
            cursor = connection.execute(statement, parameters)
            _collect_rows(cursor, rows, request.plan.max_rows, request.request_id)
            if cursor.rowcount > 0:
                affected_rows += cursor.rowcount
    finally:
        connection.set_authorizer(None)
    return tuple(rows), affected_rows


def _rollback_and_raise(
    connection: sqlite3.Connection,
    error: DataError,
    request_id: str,
) -> NoReturn:
    """Roll back once, replacing the failure only when rollback itself fails."""
    logger.debug("Running DATA function: _rollback_and_raise")
    try:
        connection.rollback()
    except sqlite3.Error:
        raise _error("DB_WRITE_FAILED", request_id, "rollback") from None
    raise error


def execute_transaction(request: TransactionRequest) -> TransactionResult:
    """Execute a bounded statement plan atomically on a short-lived connection.

    Args:
        request: Immutable statement plan, row bound, and request identifier.

    Returns:
        Normalized rows and affected-row evidence after a successful commit.

    Raises:
        DataError: If configuration, connection, execution, result validation,
            commit, or rollback fails. Raw SQL and exception details are omitted.
    """
    logger.debug("Running DATA function: execute_transaction")
    try:
        settings = get_data_settings()
    except ValueError:
        raise _error(
            "DB_CONNECTION_ERROR", request.request_id, "configuration"
        ) from None
    config = _load_database_config(settings, request.request_id)
    connection = _open_connection(config, request.request_id)
    try:
        try:
            rows, affected_rows = _execute_plan(connection, request)
        except DataError as error:
            _rollback_and_raise(connection, error, request.request_id)
        except sqlite3.IntegrityError:
            _rollback_and_raise(
                connection,
                _error("DB_WRITE_FAILED", request.request_id, "execution"),
                request.request_id,
            )
        except sqlite3.OperationalError as error:
            code = (
                "CONCURRENT_WRITE_LOCKED"
                if _is_lock_conflict(error)
                else "DATABASE_ERROR"
            )
            _rollback_and_raise(
                connection,
                _error(code, request.request_id, "execution"),
                request.request_id,
            )
        except sqlite3.DatabaseError:
            _rollback_and_raise(
                connection,
                _error("DATABASE_ERROR", request.request_id, "execution"),
                request.request_id,
            )
        try:
            connection.commit()
        except sqlite3.OperationalError as error:
            code = (
                "CONCURRENT_WRITE_LOCKED"
                if _is_lock_conflict(error)
                else "DB_WRITE_FAILED"
            )
            _rollback_and_raise(
                connection,
                _error(code, request.request_id, "commit"),
                request.request_id,
            )
        except sqlite3.Error:
            _rollback_and_raise(
                connection,
                _error("DB_WRITE_FAILED", request.request_id, "commit"),
                request.request_id,
            )
        return TransactionResult(
            rows=rows,
            affected_rows=affected_rows,
            committed=True,
            request_id=request.request_id,
        )
    finally:
        try:
            connection.close()
        except sqlite3.Error:
            raise _error("DATABASE_ERROR", request.request_id, "close") from None


__all__ = ["execute_transaction"]
