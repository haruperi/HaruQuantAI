"""Authoritative host SQLite persistence manager and transactional settings store.

Description:
    This module provides the authoritative persistence layer and SQLite database
    management for the HaruQuantAI host platform. It establishes transactional CRUD
    access to the host SQLite repository located at `data/database/haruquantai.db`.
    All database operations strictly adhere to safe connection-per-operation
    lifecycles, enabling write serialization with `BEGIN IMMEDIATE` transactions,
    enforcing foreign key constraints, and managing busy wait timeouts. Callers
    interact through typed data structures and bounded operations that safeguard
    host integrity without leaking raw SQL, sensitive values, or internal paths.

Purpose:
    FEAT-HOST-PERSISTENCE: Authoritative database access and transactional data
    storage for host services.

Key Capabilities:
    - FR-HOST-SETTINGS-READ: Query scoped host settings with pagination and key lookups.
      Associated: `SettingsStore.read_settings()`
      Logging: Emits DEBUG telemetry with scope and result counts upon read.
    - FR-HOST-SETTINGS-UPDATE: Atomically update scoped settings via batch upserts.
      Associated: `SettingsStore.update_settings()`
      Logging: Emits INFO telemetry with scope and changed record counts upon commit.

Python API Usage:
    ```python
    from pathlib import Path
    from app.host.persistance import SettingsStore

    store = SettingsStore(Path("data/database/haruquantai.db"))
    store.initialize()

    # Update scoped settings
    store.update_settings("system", {"theme": "dark", "refresh_rate": 60})

    # Read scoped settings
    page = store.read_settings("system", limit=50)
    for record in page.items:
        print(record.key, record.value)
    ```

CLI Usage:
    Persistence operations are invoked internally by host services and CLI commands:
    ```bash
    uv run python -m app.cli
    ```
"""

from __future__ import annotations

import contextlib
import copy
import json
import re
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from app.host.logging import get_logger

if TYPE_CHECKING:
    from collections.abc import Generator

__all__ = [
    "DEFAULT_DATABASE_PATH",
    "MAX_BATCH_SIZE",
    "MAX_IDENTIFIER_LENGTH",
    "MAX_JSON_DEPTH",
    "MAX_PAYLOAD_BYTES",
    "MAX_READ_LIMIT",
    "MAX_VALUE_BYTES",
    "SCHEMA_VERSION",
    "CorruptDataError",
    "IncompatibleSchemaError",
    "PersistenceError",
    "SettingRecord",
    "SettingsPage",
    "SettingsStore",
    "StorageBusyError",
    "ValidationError",
]

logger = get_logger(__name__)

MAX_IDENTIFIER_LENGTH: int = 128
IDENTIFIER_PATTERN: re.Pattern[str] = re.compile(r"^[A-Za-z0-9_.:-]+$")
MAX_BATCH_SIZE: int = 100
MAX_PAYLOAD_BYTES: int = 1024 * 1024  # 1 MiB
MAX_VALUE_BYTES: int = 64 * 1024  # 64 KiB
MAX_JSON_DEPTH: int = 16
MAX_READ_LIMIT: int = 1000
DEFAULT_READ_LIMIT: int = 100
BUSY_TIMEOUT_SECONDS: float = 5.0
SCHEMA_VERSION: int = 1

DEFAULT_DATABASE_PATH: Path = (
    Path(__file__).resolve().parents[2] / "data" / "database" / "haruquantai.db"
)


class PersistenceError(Exception):
    """Base exception for all host persistence and database errors."""


class ValidationError(PersistenceError):
    """Raised when an identifier, batch, or value violates schema or size bounds."""


class IncompatibleSchemaError(PersistenceError):
    """Raised when the database schema does not match required table definitions."""


class StorageBusyError(PersistenceError):
    """Raised when SQLite locks or transactions time out under concurrent contention."""


class CorruptDataError(PersistenceError):
    """Raised when persisted data fails validation, deserialization, or size checks."""


@dataclass(frozen=True, slots=True)
class SettingRecord:
    """Immutable record representing a persisted scoped setting.

    Attributes:
        scope: Scoped namespace identifier.
        key: Setting identifier within the scope.
        value: Decoded JSON setting value.
        schema_version: Schema version of the record.
        updated_at_utc: ISO 8601 UTC timestamp of the last write.
    """

    scope: str
    key: str
    value: Any
    schema_version: int
    updated_at_utc: str


@dataclass(frozen=True, slots=True)
class SettingsPage:
    """Keyset-paginated collection of setting records.

    Attributes:
        items: List of setting records in the current page.
        next_key: Key cursor for retrieving the subsequent page, or None.
    """

    items: list[SettingRecord]
    next_key: str | None


def validate_identifier(value: str, field_name: str) -> None:
    """Validate that an identifier string satisfies format and length constraints.

    Args:
        value: Identifier string to check.
        field_name: Descriptive name of the identifier field for errors.

    Raises:
        ValidationError: If the identifier is empty, exceeds maximum length, or
            contains illegal characters.
    """
    if not value:
        raise ValidationError(f"{field_name} must not be empty")
    if len(value) > MAX_IDENTIFIER_LENGTH:
        raise ValidationError(
            f"{field_name} length {len(value)} exceeds maximum of "
            f"{MAX_IDENTIFIER_LENGTH} characters"
        )
    if not IDENTIFIER_PATTERN.match(value):
        raise ValidationError(
            f"{field_name} '{value}' contains invalid characters; must match "
            f"alphanumeric, underscore, dot, colon, or hyphen"
        )


def validate_json_depth(obj: Any, depth: int = 1) -> None:
    """Recursively validate that JSON object nesting does not exceed safe limits.

    Args:
        obj: Python data structure to inspect.
        depth: Current nesting depth level.

    Raises:
        ValidationError: If nesting depth exceeds MAX_JSON_DEPTH.
    """
    if depth > MAX_JSON_DEPTH:
        raise ValidationError(
            f"JSON structure exceeds maximum nesting depth of {MAX_JSON_DEPTH}"
        )
    if isinstance(obj, dict):
        for val in obj.values():
            validate_json_depth(val, depth + 1)
    elif isinstance(obj, list):
        for item in obj:
            validate_json_depth(item, depth + 1)


def canonical_json(obj: Any) -> str:
    """Serialize a Python object to canonical sorted-key JSON string.

    Args:
        obj: Object to serialize.

    Returns:
        Compact, sorted JSON string representation.

    Raises:
        ValidationError: If serialization fails, contains non-finite numbers, or
            exceeds maximum allowed value byte size.
    """
    validate_json_depth(obj)
    try:
        encoded = json.dumps(
            obj,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        msg = "Setting value is not serializable to strict JSON"
        raise ValidationError(msg) from exc

    raw_bytes = encoded.encode("utf-8")
    if len(raw_bytes) > MAX_VALUE_BYTES:
        raise ValidationError(
            f"Serialized setting value of {len(raw_bytes)} bytes exceeds maximum "
            f"limit of {MAX_VALUE_BYTES} bytes"
        )
    return encoded


def now_utc_iso() -> str:
    """Return current UTC timestamp in ISO 8601 format with microsecond precision.

    Returns:
        ISO formatted UTC timestamp string.
    """
    return datetime.now(UTC).isoformat()


class SettingsStore:
    """Authoritative SQLite persistence manager for scoped host settings.

    Provides transactional, parameterized CRUD operations against the `host_settings`
    table with strict connection lifecycles, concurrency serialization, and
    isolated storage paths.
    """

    def __init__(
        self,
        db_path: Path | str | None = None,
        *,
        busy_timeout: float = BUSY_TIMEOUT_SECONDS,
    ) -> None:
        """Initialize SettingsStore with an authoritative database file path.

        Args:
            db_path: Optional path to the SQLite database file. Defaults to
                the repository root `data/database/haruquantai.db`.
            busy_timeout: Timeout in seconds for SQLite lock waits.
        """
        self._db_path: Path = (
            Path(db_path).resolve() if db_path is not None else DEFAULT_DATABASE_PATH
        )
        self._busy_timeout: float = busy_timeout

    @property
    def db_path(self) -> Path:
        """Return the resolved database file path."""
        return self._db_path

    @contextmanager
    def _connect(self, *, query_only: bool = False) -> Generator[sqlite3.Connection]:
        """Context manager creating a configured SQLite connection.

        Args:
            query_only: If True, opens connection in read-only query mode.

        Yields:
            Configured sqlite3.Connection instance with row factory and timeouts.

        Raises:
            StorageBusyError: If the connection attempt times out under lock contention.
            PersistenceError: If opening or configuring the connection fails.
        """
        if not query_only:
            self._db_path.parent.mkdir(parents=True, exist_ok=True)

        uri = (
            f"file:{self._db_path.as_posix()}?mode=ro"
            if query_only
            else f"file:{self._db_path.as_posix()}"
        )
        try:
            conn = sqlite3.connect(
                uri,
                timeout=self._busy_timeout,
                uri=True,
                autocommit=True,
            )
        except sqlite3.OperationalError as exc:
            if "busy" in str(exc).lower() or "locked" in str(exc).lower():
                raise StorageBusyError(
                    "Database connection timed out under lock"
                ) from exc
            raise PersistenceError("Failed to open database connection") from exc

        conn.row_factory = sqlite3.Row
        try:
            conn.execute(f"PRAGMA busy_timeout = {int(self._busy_timeout * 1000)}")
            conn.execute("PRAGMA foreign_keys = ON")
            if query_only:
                conn.execute("PRAGMA query_only = ON")
            yield conn
        finally:
            conn.close()

    def initialize(self) -> None:
        """Verify existing database schema or create required table transactionally.

        Raises:
            IncompatibleSchemaError: If the existing table schema is incompatible.
            PersistenceError: If table creation or schema verification fails.
        """
        with self._connect(query_only=False) as conn:
            try:
                row = conn.execute(
                    "SELECT sql FROM sqlite_master WHERE type = 'table' "
                    "AND name = 'host_settings'"
                ).fetchone()

                if row is None:
                    self._create_settings_table(conn)
                    logger.info(
                        "Initialized new host_settings table",
                        extra={"db_path": str(self._db_path)},
                    )
                    return

                self._verify_existing_schema(conn)
            except sqlite3.OperationalError as exc:
                if "busy" in str(exc).lower() or "locked" in str(exc).lower():
                    raise StorageBusyError(
                        "Database is busy during schema initialization"
                    ) from exc
                raise PersistenceError("Failed to initialize database schema") from exc

    def _create_settings_table(self, conn: sqlite3.Connection) -> None:
        """Create the host_settings table inside an immediate transaction.

        Args:
            conn: Active SQLite connection.
        """
        conn.execute("BEGIN IMMEDIATE")
        conn.execute(
            """
            CREATE TABLE host_settings (
                scope TEXT NOT NULL,
                key TEXT NOT NULL,
                value_json TEXT NOT NULL,
                schema_version INTEGER NOT NULL DEFAULT 1,
                updated_at_utc TEXT NOT NULL,
                PRIMARY KEY (scope, key)
            )
            """
        )
        conn.execute("COMMIT")

    def _verify_existing_schema(self, conn: sqlite3.Connection) -> None:
        """Verify columns and constraints of existing host_settings table.

        Args:
            conn: Active SQLite connection.

        Raises:
            IncompatibleSchemaError: If any column definition or constraint mismatches.
        """
        info_rows = conn.execute("PRAGMA table_info(host_settings)").fetchall()
        cols: dict[str, sqlite3.Row] = {r["name"]: r for r in info_rows}
        required: dict[str, tuple[str, int, int]] = {
            "scope": ("TEXT", 1, 1),
            "key": ("TEXT", 1, 2),
            "value_json": ("TEXT", 1, 0),
            "schema_version": ("INTEGER", 1, 0),
            "updated_at_utc": ("TEXT", 1, 0),
        }

        for col_name, (expected_type, notnull, pk) in required.items():
            if col_name not in cols:
                raise IncompatibleSchemaError(
                    f"Missing required column '{col_name}' in host_settings"
                )
            col = cols[col_name]
            if (
                col["type"].upper() != expected_type
                or col["notnull"] != notnull
                or col["pk"] != pk
            ):
                raise IncompatibleSchemaError(
                    f"Incompatible column definition for '{col_name}' in host_settings"
                )

    def read_settings(
        self,
        scope: str,
        *,
        key: str | None = None,
        after_key: str | None = None,
        limit: int = DEFAULT_READ_LIMIT,
    ) -> SettingsPage:
        """Query scoped host settings with pagination and optional single key lookup.

        Args:
            scope: Scoped namespace identifier.
            key: Optional exact key to query.
            after_key: Optional cursor for keyset pagination.
            limit: Maximum number of records to return (1 to 1000).

        Returns:
            SettingsPage containing matching SettingRecord items and next_key cursor.

        Raises:
            ValidationError: If scope, key, or pagination arguments are invalid.
            CorruptDataError: If stored rows contain invalid JSON or unsupported schema.
            StorageBusyError: If query times out under concurrent database lock.
            PersistenceError: If reading settings fails.
        """
        validate_identifier(scope, "scope")
        if key is not None:
            validate_identifier(key, "key")
        if after_key is not None:
            validate_identifier(after_key, "after_key")
        if not (1 <= limit <= MAX_READ_LIMIT):
            raise ValidationError(
                f"limit must be between 1 and {MAX_READ_LIMIT}, got {limit}"
            )

        if not self._db_path.exists():
            logger.debug(
                "Database file does not exist; returning empty settings page",
                extra={
                    "scope": scope,
                    "count": 0,
                    "requirement": "FR-HOST-SETTINGS-READ",
                },
            )
            return SettingsPage(items=[], next_key=None)

        with self._connect(query_only=True) as conn:
            try:
                if key is not None:
                    return self._read_single_key(conn, scope, key)
                return self._read_paginated_keys(conn, scope, after_key, limit)
            except sqlite3.OperationalError as exc:
                if "busy" in str(exc).lower() or "locked" in str(exc).lower():
                    raise StorageBusyError(
                        "Database is busy while reading settings"
                    ) from exc
                raise PersistenceError("Failed to query host settings") from exc

    def _read_single_key(
        self, conn: sqlite3.Connection, scope: str, key: str
    ) -> SettingsPage:
        """Read a single key from host_settings.

        Args:
            conn: Active SQLite connection.
            scope: Scoped namespace identifier.
            key: Setting key to fetch.

        Returns:
            SettingsPage containing either one SettingRecord or empty list.
        """
        row = conn.execute(
            """
            SELECT scope, key, value_json, schema_version, updated_at_utc
            FROM host_settings
            WHERE scope = ? AND key = ?
            """,
            (scope, key),
        ).fetchone()
        if row is None:
            logger.debug(
                "Setting key not found in scope",
                extra={
                    "scope": scope,
                    "count": 0,
                    "requirement": "FR-HOST-SETTINGS-READ",
                },
            )
            return SettingsPage(items=[], next_key=None)

        record = self._row_to_record(row)
        logger.debug(
            "Successfully read scoped setting key",
            extra={
                "scope": scope,
                "count": 1,
                "requirement": "FR-HOST-SETTINGS-READ",
            },
        )
        return SettingsPage(items=[record], next_key=None)

    def _read_paginated_keys(
        self,
        conn: sqlite3.Connection,
        scope: str,
        after_key: str | None,
        limit: int,
    ) -> SettingsPage:
        """Read a keyset-paginated slice of settings.

        Args:
            conn: Active SQLite connection.
            scope: Scoped namespace identifier.
            after_key: Cursor key or None.
            limit: Maximum items to return.

        Returns:
            SettingsPage containing up to limit items and optional next_key cursor.
        """
        if after_key is not None:
            rows = conn.execute(
                """
                SELECT scope, key, value_json, schema_version, updated_at_utc
                FROM host_settings
                WHERE scope = ? AND key > ?
                ORDER BY key ASC
                LIMIT ?
                """,
                (scope, after_key, limit + 1),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT scope, key, value_json, schema_version, updated_at_utc
                FROM host_settings
                WHERE scope = ?
                ORDER BY key ASC
                LIMIT ?
                """,
                (scope, limit + 1),
            ).fetchall()

        has_more = len(rows) > limit
        display_rows = rows[:limit] if has_more else rows
        next_cursor = display_rows[-1]["key"] if has_more else None

        records = [self._row_to_record(r) for r in display_rows]
        logger.debug(
            "Successfully read scoped settings page",
            extra={
                "scope": scope,
                "count": len(records),
                "requirement": "FR-HOST-SETTINGS-READ",
            },
        )
        return SettingsPage(items=records, next_key=next_cursor)

    def _validate_batch_input(
        self, scope: str, values: dict[str, Any]
    ) -> list[tuple[str, Any, str]]:
        """Validate batch input keys and serialize values to canonical JSON.

        Args:
            scope: Scoped namespace identifier.
            values: Mapping of keys to Python values.

        Returns:
            List of (key, original_value, canonical_json_string) tuples.

        Raises:
            ValidationError: If any identifier, limit, or payload size is invalid.
        """
        validate_identifier(scope, "scope")
        if len(values) > MAX_BATCH_SIZE:
            raise ValidationError(
                f"Batch size of {len(values)} exceeds maximum limit of "
                f"{MAX_BATCH_SIZE} settings"
            )

        validated: list[tuple[str, Any, str]] = []
        total_payload_bytes = 0
        for k, v in values.items():
            validate_identifier(k, "key")
            encoded_json = canonical_json(v)
            total_payload_bytes += len(encoded_json.encode("utf-8"))
            validated.append((k, v, encoded_json))

        if total_payload_bytes > MAX_PAYLOAD_BYTES:
            raise ValidationError(
                f"Total batch payload size {total_payload_bytes} exceeds maximum "
                f"limit of {MAX_PAYLOAD_BYTES} bytes"
            )
        return validated

    def update_settings(
        self, scope: str, values: dict[str, Any]
    ) -> list[SettingRecord]:
        """Atomically update or insert scoped settings within a transaction.

        Validates all keys and values, detects existing unchanged values to preserve
        timestamps, and applies all changes in a serialized `BEGIN IMMEDIATE`
        transaction.

        Args:
            scope: Scoped namespace identifier.
            values: Mapping of setting keys to serializable Python values.

        Returns:
            List of SettingRecord instances for settings that were modified or inserted.

        Raises:
            ValidationError: If scope, keys, batch limits, or values violate
                constraints.
            IncompatibleSchemaError: If table is missing or has unsupported
                schema versions.
            StorageBusyError: If transaction acquisition times out under
                contention.
            PersistenceError: If atomic upsert fails.
        """
        if not values:
            validate_identifier(scope, "scope")
            return []

        validated_items = self._validate_batch_input(scope, values)

        with self._connect(query_only=False) as conn:
            try:
                conn.execute("BEGIN IMMEDIATE")
                self._check_table_exists(conn)
                changed_records = self._apply_batch_upsert(conn, scope, validated_items)
                conn.execute("COMMIT")
            except sqlite3.OperationalError as exc:
                with contextlib.suppress(sqlite3.Error):
                    conn.execute("ROLLBACK")
                if "busy" in str(exc).lower() or "locked" in str(exc).lower():
                    raise StorageBusyError(
                        "Database is busy during atomic settings update"
                    ) from exc
                raise PersistenceError("Failed to update scoped settings") from exc
            except Exception:
                with contextlib.suppress(sqlite3.Error):
                    conn.execute("ROLLBACK")
                raise

        logger.info(
            "Atomically updated scoped settings batch",
            extra={
                "scope": scope,
                "changed_count": len(changed_records),
                "requirement": "FR-HOST-SETTINGS-UPDATE",
            },
        )
        return changed_records

    def _check_table_exists(self, conn: sqlite3.Connection) -> None:
        """Verify that the host_settings table exists in the connected database.

        Args:
            conn: Active SQLite connection.

        Raises:
            IncompatibleSchemaError: If table does not exist.
        """
        row = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' "
            "AND name = 'host_settings'"
        ).fetchone()
        if row is None:
            raise IncompatibleSchemaError(
                "Table 'host_settings' does not exist in target database"
            )

    def _apply_batch_upsert(
        self,
        conn: sqlite3.Connection,
        scope: str,
        validated_items: list[tuple[str, Any, str]],
    ) -> list[SettingRecord]:
        """Apply batch upsert operations within an active write transaction.

        Args:
            conn: Active SQLite connection inside a transaction.
            scope: Scoped namespace identifier.
            validated_items: Pre-validated list of (key, value, canonical_json).

        Returns:
            List of SettingRecord instances for settings that changed.

        Raises:
            IncompatibleSchemaError: If an existing row has an unsupported
                schema version.
        """
        now_ts = now_utc_iso()
        changed: list[SettingRecord] = []

        for key, val, raw_json in validated_items:
            existing = conn.execute(
                """
                SELECT value_json, schema_version, updated_at_utc
                FROM host_settings
                WHERE scope = ? AND key = ?
                """,
                (scope, key),
            ).fetchone()

            if existing is not None:
                if existing["schema_version"] != SCHEMA_VERSION:
                    raise IncompatibleSchemaError(
                        f"Unsupported schema version {existing['schema_version']} "
                        f"for key '{key}'"
                    )
                if existing["value_json"] == raw_json:
                    continue

            conn.execute(
                """
                INSERT INTO host_settings (
                    scope, key, value_json, schema_version, updated_at_utc
                )
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(scope, key) DO UPDATE SET
                    value_json = excluded.value_json,
                    schema_version = excluded.schema_version,
                    updated_at_utc = excluded.updated_at_utc
                """,
                (scope, key, raw_json, SCHEMA_VERSION, now_ts),
            )
            changed.append(
                SettingRecord(
                    scope=scope,
                    key=key,
                    value=copy.deepcopy(val),
                    schema_version=SCHEMA_VERSION,
                    updated_at_utc=now_ts,
                )
            )
        return changed

    @staticmethod
    def _row_to_record(row: sqlite3.Row) -> SettingRecord:
        """Convert an SQLite row to an immutable SettingRecord instance.

        Args:
            row: SQLite Row from the `host_settings` table.

        Returns:
            SettingRecord instance with decoded JSON value.

        Raises:
            CorruptDataError: If deserialization fails or schema version is unsupported.
        """
        if row["schema_version"] != SCHEMA_VERSION:
            raise CorruptDataError(
                f"Unsupported schema version {row['schema_version']} for key "
                f"'{row['key']}'"
            )
        try:
            value = json.loads(row["value_json"])
        except (ValueError, TypeError) as exc:
            raise CorruptDataError(
                f"Corrupt JSON payload in row for key '{row['key']}'"
            ) from exc

        return SettingRecord(
            scope=row["scope"],
            key=row["key"],
            value=value,
            schema_version=row["schema_version"],
            updated_at_utc=row["updated_at_utc"],
        )
