"""Host configuration settings manager and transactional SQLite persistence layer.

Description:
    Provides the central configuration settings container, dot-accessible access
    interface, validation engine, and authoritative SQLite persistence store for
    HaruQuantAI host operations. All settings are persistently maintained in
    `data/database/haruquantai.db` inside the `host_settings` table using
    `BEGIN IMMEDIATE` serialized write transactions, busy timeout controls,
    and optimistic concurrency revision checks (`expected_revision`). Exposes a
    module-level `settings` singleton with lazy-loading semantics (zero disk I/O
    at import time) and a FastAPI REST projection router providing `/settings`
    inspection and atomic modification.

Purpose:
    FEAT-HOST-SETTINGS: Host configuration settings management, schema validation,
    transactional SQLite persistence, and dot-accessible navigation.

Key Capabilities:
    - FR-HOST-SETTINGS-SCHEMA: Transactional SQLite `host_settings` table
      initialization and schema constraint verification.
      Logging: Emits INFO on table creation; DEBUG on verification.
    - FR-HOST-SETTINGS-LOAD: Query and parse scoped configuration records into
      memory.
      Logging: Emits INFO on loading records with item count and discovered
      scopes.
    - FR-HOST-SETTINGS-DOT-ACCESS: Recursive dot-notation and dictionary-style
      attribute navigation.
      Logging: Emits DEBUG when accessing setting attributes or namespaces.
    - FR-HOST-SETTINGS-VALIDATION: Validate type, range, finite values, and
      credentials.
      Logging: Emits WARNING with reason when validation rejects a payload.
    - FR-HOST-SETTINGS-UPDATE: Atomic batch upsert with monotonic revision and
      conflict detection.
      Logging: Emits INFO on committed batch with changed count and updated
      revision.
    - FR-HOST-SETTINGS-PATH-VALIDATION: Validate configured workspace filesystem
      paths.
      Logging: Emits INFO when path exists; WARNING when path is absent.
    - FR-HOST-SETTINGS-PROJECTION: FastAPI REST endpoints for settings snapshot
      and updates.
      Logging: Emits DEBUG on query; INFO on settings updates.

Python API Usage:
    ```python
    from app.host.settings import settings

    # Access scoped setting via normalized dot-notation
    theme = settings.app_general.theme
    cores = settings.config_cpu.custom_cores

    # Dict-style access and fallback default
    port = settings.get("bound_port", 8080)

    # Validate workspace directories
    path_statuses = settings.validate_workspace_paths()
    ```

CLI Usage:
    Inspect and verify settings via the diagnostic CLI:
    ```bash
    uv run python -m app.cli
    ```
"""

from __future__ import annotations

import contextlib
import json
import math
import re
import sqlite3
from collections.abc import Generator, Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, override

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from app.host.logging import get_logger

__all__ = [
    "DEFAULT_DATABASE_PATH",
    "MAX_BATCH_SIZE",
    "MAX_IDENTIFIER_LENGTH",
    "MAX_JSON_DEPTH",
    "MAX_MEMORY_GB",
    "MAX_PAYLOAD_BYTES",
    "MAX_PORT",
    "MAX_READ_LIMIT",
    "MAX_TEXT_LENGTH",
    "MAX_VALUE_BYTES",
    "MAX_ZOOM",
    "MIN_CUSTOM_CORES",
    "MIN_MEMORY_GB",
    "MIN_PORT",
    "MIN_ZOOM",
    "SCHEMA_VERSION",
    "VALID_CORE_MODES",
    "VALID_THEMES",
    "AppSettings",
    "CorruptDataError",
    "HostSettings",
    "HostSettingsSnapshot",
    "IncompatibleSchemaError",
    "PersistenceError",
    "RevisionConflictError",
    "SettingRecord",
    "SettingsManager",
    "SettingsPage",
    "SettingsStore",
    "SettingsUpdateRequest",
    "StorageBusyError",
    "ValidationError",
    "create_settings_router",
    "settings",
    "validate_configuration_values",
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

MIN_ZOOM: float = 0.7
MAX_ZOOM: float = 1.8
MIN_CUSTOM_CORES: int = 1
MIN_MEMORY_GB: float = 2.0
MAX_MEMORY_GB: float = 1024.0
MAX_TEXT_LENGTH: int = 30
MIN_PORT: int = 1
MAX_PORT: int = 65535
VALID_THEMES: tuple[str, ...] = ("dark", "light")
VALID_CORE_MODES: tuple[str, ...] = (
    "single",
    "reserve-one",
    "all_except_one",
    "custom",
    "maximum",
    "all",
)

DEFAULT_DATABASE_PATH: Path = (
    Path(__file__).resolve().parents[2] / "data" / "database" / "haruquantai.db"
)

_MISSING = object()

# Default seed configuration records matching UI schema contracts
DEFAULT_SETTINGS_SEED: dict[str, dict[str, Any]] = {
    "app.general": {
        "theme": "dark",
        "language": "en",
        "zoom": 1.0,
        "gpu_accelerated": True,
    },
    "config.global": {
        "theme": "dark",
        "language": "en",
        "sounds_off": False,
        "advanced_file_chooser": True,
        "show_control_orders": False,
        "header_custom_text": "",
        "footer_custom_text": "",
        "default_result_to_display": "Portfolio",
    },
    "config.cpu": {
        "core_usage": "all_except_one",
        "custom_cores": 7,
        "high_priority": False,
        "thread_affinity": False,
    },
    "config.performance": {
        "compute_pips_metrics": False,
        "compute_pcts_metrics": False,
        "compute_separate_metrics": True,
    },
    "config.memory": {
        "gc_type": "ParallelGC",
        "automatic_memory": False,
        "memory_limit_gb": 10,
        "dont_store_pending_orders": True,
        "memory_cleanup": False,
        "cleanup_interval_mins": 15,
    },
    "config.databanks": {
        "databank_sync_interval_mins": 15,
        "sync_databanks_after_task_done": True,
        "store_chart_data": False,
    },
    "config.optimizations": {
        "dont_store_op_3d_charts_data": True,
    },
    "config.troubleshooting": {
        "gpu_accelerated": True,
        "memory_protection": True,
        "debug_level_active": False,
    },
    "connect.remote": {
        "allow": False,
        "require_password": False,
    },
    "notify.email": {
        "smtp_server": "",
        "smtp_port": 587,
        "use_ssl": False,
        "use_tls": True,
        "username": "",
        "from_address": "",
    },
    "workspace_paths": {
        "configs_dir": "data/configs",
        "data_dir": "data",
        "projects_dir": "data/projects",
        "strategies_dir": "data/strategies",
    },
}


class PersistenceError(Exception):
    """Base exception for all host settings and database errors."""


class ValidationError(PersistenceError):
    """Raised when an identifier, batch, or setting value violates constraints."""


class IncompatibleSchemaError(PersistenceError):
    """Raised when the database schema does not match required table definitions."""


class StorageBusyError(PersistenceError):
    """Raised when SQLite locks or transactions time out under concurrent contention."""


class CorruptDataError(PersistenceError):
    """Raised when persisted data fails validation, deserialization, or size checks."""


class RevisionConflictError(PersistenceError):
    """Raised when an update request expected_revision conflicts with current state."""


class SettingRecord(BaseModel):
    """Immutable record representing a persisted scoped setting."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    scope: str = Field(..., description="Scoped namespace identifier")
    key: str = Field(..., description="Setting key identifier")
    value: Any = Field(..., description="Decoded setting value")
    schema_version: int = Field(default=1, description="Schema version of record")
    updated_at_utc: str = Field(..., description="ISO 8601 UTC update timestamp")


class SettingsPage(BaseModel):
    """Keyset-paginated collection of setting records."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    items: list[SettingRecord] = Field(default_factory=list)
    next_key: str | None = Field(default=None)


class HostSettingsSnapshot(BaseModel):
    """Snapshot envelope of host settings with monotonic revision number."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    revision: int = Field(..., ge=0, description="Monotonic revision counter")
    values: dict[str, dict[str, Any]] = Field(
        default_factory=dict, description="Scoped settings mapping"
    )


class SettingsUpdateRequest(BaseModel):
    """Request envelope for updating host settings with optimistic locking."""

    model_config = ConfigDict(extra="forbid")

    expected_revision: int = Field(
        ..., ge=0, description="Expected settings revision before write"
    )
    changes: dict[str, dict[str, Any]] = Field(
        ..., description="Scoped changes mapping: scope -> {key: value}"
    )


def validate_identifier(value: str, field_name: str) -> None:
    """Validate that an identifier satisfies character and length limits.

    Args:
        value: Identifier string to check.
        field_name: Descriptive name of the identifier field.

    Raises:
        ValidationError: If identifier is empty, oversized, or contains illegal chars.
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
    """Recursively validate that JSON nesting does not exceed safe bounds.

    Args:
        obj: Object structure to inspect.
        depth: Current nesting depth level.

    Raises:
        ValidationError: If depth exceeds MAX_JSON_DEPTH.
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
        Compact, sorted JSON string.

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
        raise ValidationError(
            "Setting value is not serializable to strict JSON"
        ) from exc

    raw_bytes = encoded.encode("utf-8")
    if len(raw_bytes) > MAX_VALUE_BYTES:
        raise ValidationError(
            f"Serialized setting value of {len(raw_bytes)} bytes exceeds maximum "
            f"limit of {MAX_VALUE_BYTES} bytes"
        )
    return encoded


def now_utc_iso() -> str:
    """Return current UTC timestamp in ISO 8601 format."""
    return datetime.now(UTC).isoformat()


def _validate_finite_number(scope: str, key: str, value: Any) -> None:
    """Validate that numeric values are finite and not NaN or Infinity."""
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        logger.warning(
            "FR-HOST-SETTINGS-VALIDATION: Rejected non-finite float value.",
            extra={"scope": scope, "key": key, "fr_id": "FR-HOST-SETTINGS-VALIDATION"},
        )
        raise ValidationError(f"Setting '{scope}.{key}' cannot be NaN or Infinity")


def _validate_numeric_limits(scope: str, key: str, value: Any) -> None:
    """Validate numeric ranges for zoom, cores, memory, and ports."""
    if key == "zoom" and (
        not isinstance(value, (int, float))
        or not (MIN_ZOOM <= float(value) <= MAX_ZOOM)
        or math.isnan(float(value))
    ):
        logger.warning(
            "FR-HOST-SETTINGS-VALIDATION: Invalid zoom level %s",
            value,
            extra={
                "scope": scope,
                "key": key,
                "fr_id": "FR-HOST-SETTINGS-VALIDATION",
            },
        )
        raise ValidationError(
            f"Zoom level must be a finite number between {MIN_ZOOM} and {MAX_ZOOM}"
        )

    if key == "custom_cores" and (
        not isinstance(value, int)
        or isinstance(value, bool)
        or value < MIN_CUSTOM_CORES
    ):
        logger.warning(
            "FR-HOST-SETTINGS-VALIDATION: Invalid custom_cores %s",
            value,
            extra={
                "scope": scope,
                "key": key,
                "fr_id": "FR-HOST-SETTINGS-VALIDATION",
            },
        )
        raise ValidationError(
            f"Custom cores must be a positive integer >= {MIN_CUSTOM_CORES}"
        )

    if key == "memory_limit_gb" and (
        not isinstance(value, (int, float))
        or not (MIN_MEMORY_GB <= float(value) <= MAX_MEMORY_GB)
    ):
        logger.warning(
            "FR-HOST-SETTINGS-VALIDATION: Invalid memory_limit_gb %s",
            value,
            extra={
                "scope": scope,
                "key": key,
                "fr_id": "FR-HOST-SETTINGS-VALIDATION",
            },
        )
        raise ValidationError(
            f"Memory limit GB must be a finite number between {MIN_MEMORY_GB} "
            f"and {MAX_MEMORY_GB}"
        )

    if key == "smtp_port":
        port_num: int | None = None
        if isinstance(value, int) and not isinstance(value, bool):
            port_num = value
        elif isinstance(value, str) and value.isdigit():
            port_num = int(value)
        if port_num is None or not (MIN_PORT <= port_num <= MAX_PORT):
            logger.warning(
                "FR-HOST-SETTINGS-VALIDATION: Invalid SMTP port %s",
                value,
                extra={
                    "scope": scope,
                    "key": key,
                    "fr_id": "FR-HOST-SETTINGS-VALIDATION",
                },
            )
            raise ValidationError(
                f"SMTP port must be an integer between {MIN_PORT} and {MAX_PORT}"
            )


def _validate_string_limits(scope: str, key: str, value: Any) -> None:
    """Validate string constraints for headers, themes, and modes."""
    if key in ("header_custom_text", "footer_custom_text") and (
        not isinstance(value, str) or len(value) > MAX_TEXT_LENGTH
    ):
        logger.warning(
            "FR-HOST-SETTINGS-VALIDATION: Header/footer text exceeds limit.",
            extra={
                "scope": scope,
                "key": key,
                "fr_id": "FR-HOST-SETTINGS-VALIDATION",
            },
        )
        raise ValidationError(
            f"{key} must be a string of at most {MAX_TEXT_LENGTH} characters"
        )

    if key == "theme" and value not in VALID_THEMES:
        logger.warning(
            "FR-HOST-SETTINGS-VALIDATION: Invalid theme %s",
            value,
            extra={"scope": scope, "key": key, "fr_id": "FR-HOST-SETTINGS-VALIDATION"},
        )
        raise ValidationError(f"Theme must be one of {VALID_THEMES}")

    if key == "core_usage" and value not in VALID_CORE_MODES:
        logger.warning(
            "FR-HOST-SETTINGS-VALIDATION: Invalid core_usage mode %s",
            value,
            extra={"scope": scope, "key": key, "fr_id": "FR-HOST-SETTINGS-VALIDATION"},
        )
        raise ValidationError(f"Unsupported core_usage mode '{value}'")


def validate_configuration_values(scope: str, key: str, value: Any) -> None:
    """Validate specific setting constraints according to ratified rules.

    Args:
        scope: Scoped namespace identifier.
        key: Setting key within the scope.
        value: Candidate setting value to validate.

    Raises:
        ValidationError: If any constraint is violated.
    """
    _validate_finite_number(scope, key, value)
    _validate_numeric_limits(scope, key, value)
    _validate_string_limits(scope, key, value)


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
                    self._seed_default_settings(conn)
                    logger.info(
                        "FR-HOST-SETTINGS-SCHEMA: Initialized host_settings table.",
                        extra={
                            "db_path": str(self._db_path),
                            "fr_id": "FR-HOST-SETTINGS-SCHEMA",
                        },
                    )
                    return

                self._verify_existing_schema(conn)
                self._ensure_revision_exists(conn)
                logger.debug(
                    "FR-HOST-SETTINGS-SCHEMA: Verified host_settings schema.",
                    extra={"fr_id": "FR-HOST-SETTINGS-SCHEMA"},
                )
            except sqlite3.OperationalError as exc:
                if "busy" in str(exc).lower() or "locked" in str(exc).lower():
                    raise StorageBusyError(
                        "Database is busy during schema initialization"
                    ) from exc
                raise PersistenceError("Failed to initialize database schema") from exc

    def _create_settings_table(self, conn: sqlite3.Connection) -> None:
        """Create the host_settings table inside an immediate transaction."""
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

    def _ensure_revision_exists(self, conn: sqlite3.Connection) -> None:
        """Ensure the internal _system:revision key exists in host_settings."""
        row = conn.execute(
            "SELECT value_json FROM host_settings "
            "WHERE scope = '_system' AND key = 'revision'"
        ).fetchone()
        if row is None:
            now_ts = now_utc_iso()
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(
                """
                INSERT OR IGNORE INTO host_settings (
                    scope, key, value_json, schema_version, updated_at_utc
                )
                VALUES ('_system', 'revision', '1', ?, ?)
                """,
                (SCHEMA_VERSION, now_ts),
            )
            conn.execute("COMMIT")

    def _seed_default_settings(self, conn: sqlite3.Connection) -> None:
        """Seed initial default configuration records into empty host_settings table."""
        now_ts = now_utc_iso()
        conn.execute("BEGIN IMMEDIATE")
        conn.execute(
            """
            INSERT OR REPLACE INTO host_settings (
                scope, key, value_json, schema_version, updated_at_utc
            )
            VALUES ('_system', 'revision', '1', ?, ?)
            """,
            (SCHEMA_VERSION, now_ts),
        )
        for scope, keyvals in DEFAULT_SETTINGS_SEED.items():
            for key, val in keyvals.items():
                encoded = canonical_json(val)
                conn.execute(
                    """
                    INSERT OR REPLACE INTO host_settings (
                        scope, key, value_json, schema_version, updated_at_utc
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (scope, key, encoded, SCHEMA_VERSION, now_ts),
                )
        conn.execute("COMMIT")

    def get_revision(self) -> int:
        """Query current monotonic revision counter."""
        if not self._db_path.exists():
            return 1
        with self._connect(query_only=True) as conn:
            try:
                row = conn.execute(
                    "SELECT value_json FROM host_settings "
                    "WHERE scope = '_system' AND key = 'revision'"
                ).fetchone()
                if row is not None:
                    return int(json.loads(row["value_json"]))
            except (sqlite3.Error, ValueError, TypeError) as exc:
                logger.debug(
                    "FR-HOST-SETTINGS-LOAD: Revision query fallback (%s)",
                    exc,
                    extra={"fr_id": "FR-HOST-SETTINGS-LOAD"},
                )
        return 1

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
                    "requirement": "FR-HOST-SETTINGS-LOAD",
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
        """Read a single key from host_settings."""
        row = conn.execute(
            """
            SELECT scope, key, value_json, schema_version, updated_at_utc
            FROM host_settings
            WHERE scope = ? AND key = ?
            """,
            (scope, key),
        ).fetchone()
        if row is None:
            return SettingsPage(items=[], next_key=None)

        record = self._row_to_record(row)
        return SettingsPage(items=[record], next_key=None)

    def _read_paginated_keys(
        self,
        conn: sqlite3.Connection,
        scope: str,
        after_key: str | None,
        limit: int,
    ) -> SettingsPage:
        """Read a keyset-paginated slice of settings."""
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
        return SettingsPage(items=records, next_key=next_cursor)

    def read_all_scoped(self) -> tuple[int, dict[str, dict[str, Any]]]:
        """Read all scoped settings records grouped by scope, plus the revision number.

        Returns:
            Tuple of (revision: int, values: dict[scope, dict[key, value]]).
        """
        if not self._db_path.exists():
            return 1, {}

        with self._connect(query_only=True) as conn:
            try:
                rows = conn.execute(
                    """
                    SELECT scope, key, value_json, schema_version, updated_at_utc
                    FROM host_settings
                    ORDER BY scope ASC, key ASC
                    """
                ).fetchall()
            except sqlite3.OperationalError:
                return 1, {}

        revision = 1
        values: dict[str, dict[str, Any]] = {}
        for row in rows:
            scope = str(row["scope"])
            key = str(row["key"])
            try:
                val = json.loads(row["value_json"])
            except (ValueError, TypeError) as exc:
                logger.debug(
                    "FR-HOST-SETTINGS-LOAD: Skipping corrupt row (%s)",
                    exc,
                    extra={"fr_id": "FR-HOST-SETTINGS-LOAD"},
                )
                continue

            if scope == "_system" and key == "revision":
                if isinstance(val, int):
                    revision = val
                continue

            if scope not in values:
                values[scope] = {}
            values[scope][key] = val

        return revision, values

    def get_snapshot(self) -> HostSettingsSnapshot:
        """Return full host settings snapshot including revision and values."""
        rev, vals = self.read_all_scoped()
        return HostSettingsSnapshot(revision=rev, values=vals)

    def update_settings(
        self,
        scope: str,
        values: dict[str, Any],
        *,
        expected_revision: int | None = None,
    ) -> HostSettingsSnapshot:
        """Convenience method to update settings within a single scope."""
        return self.update_batch({scope: values}, expected_revision=expected_revision)

    def _validate_batch_changes(
        self, changes: dict[str, dict[str, Any]]
    ) -> list[tuple[str, str, Any, str]]:
        """Validate all items in a batch update mapping."""
        total_items = 0
        validated_items: list[tuple[str, str, Any, str]] = []
        for scope, scope_changes in changes.items():
            validate_identifier(scope, "scope")
            if not isinstance(scope_changes, dict):
                raise ValidationError(
                    f"Scope changes for '{scope}' must be a dictionary"
                )
            for key, val in scope_changes.items():
                validate_identifier(key, "key")
                validate_configuration_values(scope, key, val)
                encoded = canonical_json(val)
                validated_items.append((scope, key, val, encoded))
                total_items += 1

        if total_items > MAX_BATCH_SIZE:
            raise ValidationError(
                f"Total batch items {total_items} exceeds limit {MAX_BATCH_SIZE}"
            )
        return validated_items

    def _check_revision_match(
        self, expected_revision: int | None, current_revision: int
    ) -> None:
        """Verify that expected revision matches current revision."""
        if expected_revision is not None and expected_revision != current_revision:
            logger.warning(
                "FR-HOST-SETTINGS-UPDATE: Revision conflict. Current: %d, Expected: %d",
                current_revision,
                expected_revision,
                extra={"fr_id": "FR-HOST-SETTINGS-UPDATE"},
            )
            raise RevisionConflictError(
                f"Settings revision conflict: expected {expected_revision}, "
                f"but current is {current_revision}"
            )

    def update_batch(
        self,
        changes: dict[str, dict[str, Any]],
        *,
        expected_revision: int | None = None,
    ) -> HostSettingsSnapshot:
        """Atomically update multiple scoped settings batches with optimistic locking.

        Args:
            changes: Mapping of scope string to dictionary of key-value changes.
            expected_revision: Optional expected revision number. If mismatched,
                raises RevisionConflictError.

        Returns:
            Updated HostSettingsSnapshot.

        Raises:
            RevisionConflictError: If expected_revision does not match current revision.
            ValidationError: If any scope, key, limit, or value violates rules.
            PersistenceError: On database execution failure.
        """
        if not changes:
            return self.get_snapshot()

        validated_items = self._validate_batch_changes(changes)

        with self._connect(query_only=False) as conn:
            try:
                conn.execute("BEGIN IMMEDIATE")
                self._check_table_exists(conn)

                rev_row = conn.execute(
                    "SELECT value_json FROM host_settings "
                    "WHERE scope = '_system' AND key = 'revision'"
                ).fetchone()
                current_revision = (
                    int(json.loads(rev_row["value_json"])) if rev_row is not None else 1
                )

                self._check_revision_match(expected_revision, current_revision)

                now_ts = now_utc_iso()
                changed_count = 0
                for scope, key, _val, raw_json in validated_items:
                    existing = conn.execute(
                        "SELECT value_json FROM host_settings "
                        "WHERE scope = ? AND key = ?",
                        (scope, key),
                    ).fetchone()
                    if existing is not None and existing["value_json"] == raw_json:
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
                    changed_count += 1

                new_revision = (
                    current_revision + 1 if changed_count > 0 else current_revision
                )
                if changed_count > 0:
                    conn.execute(
                        """
                        INSERT INTO host_settings (
                            scope, key, value_json, schema_version, updated_at_utc
                        )
                        VALUES ('_system', 'revision', ?, ?, ?)
                        ON CONFLICT(scope, key) DO UPDATE SET
                            value_json = excluded.value_json,
                            schema_version = excluded.schema_version,
                            updated_at_utc = excluded.updated_at_utc
                        """,
                        (json.dumps(new_revision), SCHEMA_VERSION, now_ts),
                    )

                conn.execute("COMMIT")
            except RevisionConflictError:
                with contextlib.suppress(sqlite3.Error):
                    conn.execute("ROLLBACK")
                raise
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
            "FR-HOST-SETTINGS-UPDATE: Atomically updated %d setting(s). Revision: %d",
            changed_count,
            new_revision,
            extra={
                "changed_count": changed_count,
                "revision": new_revision,
                "fr_id": "FR-HOST-SETTINGS-UPDATE",
            },
        )
        return self.get_snapshot()

    def _check_table_exists(self, conn: sqlite3.Connection) -> None:
        """Verify that the host_settings table exists."""
        row = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' "
            "AND name = 'host_settings'"
        ).fetchone()
        if row is None:
            raise IncompatibleSchemaError(
                "Table 'host_settings' does not exist in target database"
            )

    @staticmethod
    def _row_to_record(row: sqlite3.Row) -> SettingRecord:
        """Convert SQLite Row to SettingRecord."""
        if row["schema_version"] != SCHEMA_VERSION:
            raise CorruptDataError(
                f"Unsupported schema version {row['schema_version']} "
                f"for key '{row['key']}'"
            )
        try:
            value = json.loads(row["value_json"])
        except (ValueError, TypeError) as exc:
            raise CorruptDataError(
                f"Corrupt JSON payload in row for key '{row['key']}'"
            ) from exc

        return SettingRecord(
            scope=str(row["scope"]),
            key=str(row["key"]),
            value=value,
            schema_version=int(row["schema_version"]),
            updated_at_utc=str(row["updated_at_utc"]),
        )


class _SettingsNode:
    """Recursive wrapper providing dot-attribute and dictionary-style access.

    Converts dictionary keys containing dots (e.g. `app.general`) into valid
    Python attribute identifiers (`app_general`) while retaining exact key
    lookups via dictionary indexing.
    """

    def __init__(self, data: dict[str, Any] | Any = None) -> None:
        """Initialize _SettingsNode with raw dictionary or primitive value.

        Args:
            data: Raw dictionary or primitive value to wrap.
        """
        self._raw: dict[str, Any] = {}
        self._data: dict[str, Any] = {}
        if isinstance(data, dict):
            self._raw = data
            for key, val in data.items():
                clean_key = str(key).replace(".", "_")
                wrapped = self.wrap(val)
                self._data[clean_key] = wrapped
                if clean_key != str(key):
                    self._data[str(key)] = wrapped
        elif data is not None:
            self._raw = {"value": data}
            self._data = {"value": self.wrap(data)}

    @classmethod
    def wrap(cls, value: Any) -> Any:
        """Recursively wrap nested dictionaries and list elements.

        Args:
            value: Object to inspect and wrap.

        Returns:
            Wrapped _SettingsNode, list of wrapped elements, or raw primitive.
        """
        if isinstance(value, dict):
            return _SettingsNode(value)
        if isinstance(value, list):
            return [cls.wrap(item) for item in value]
        return value

    def _resolve(self, name: str) -> Any:
        """Resolve value by key or normalized identifier."""
        if name in self._data:
            return self._data[name]
        clean_name = name.replace(".", "_")
        if clean_name in self._data:
            return self._data[clean_name]
        return _MISSING

    def _attribute_not_found(self, name: str) -> AttributeError:
        """Construct exception for missing attribute access."""
        return AttributeError(f"Setting attribute '{name}' not found")

    def _key_not_found(self, name: str) -> KeyError:
        """Construct exception for missing key indexing."""
        return KeyError(f"Setting key '{name}' not found")

    def __getattr__(self, name: str) -> Any:
        """Retrieve setting attribute via dot-notation."""
        if name.startswith("_"):
            return super().__getattribute__(name)
        val = self._resolve(name)
        if val is not _MISSING:
            return val
        raise self._attribute_not_found(name)

    def __getitem__(self, name: str) -> Any:
        """Retrieve setting value via dictionary indexing."""
        val = self._resolve(name)
        if val is not _MISSING:
            return val
        raise self._key_not_found(name)

    def get(self, name: str, default: Any = None) -> Any:
        """Retrieve setting value with fallback default."""
        val = self._resolve(name)
        return val if val is not _MISSING else default

    def __contains__(self, name: object) -> bool:
        """Check whether key or normalized attribute exists in node."""
        if not isinstance(name, str):
            return False
        return bool(self._resolve(name) is not _MISSING)

    def __iter__(self) -> Iterator[str]:
        """Iterate over canonical raw keys or indexed data keys."""
        return iter(self._raw or self._data)

    def __len__(self) -> int:
        """Return number of settings in node."""
        return len(self._raw or self._data)

    def as_dict(self) -> dict[str, Any]:
        """Return the underlying un-wrapped dictionary representation."""
        if self._raw:
            return self._raw
        result: dict[str, Any] = {}
        for k, v in self._data.items():
            if isinstance(v, _SettingsNode):
                result[k] = v.as_dict()
            else:
                result[k] = v
        return result

    @override
    def __repr__(self) -> str:
        """Return developer representation of wrapped node."""
        return f"_SettingsNode({self._raw!r})"


class HostSettings(_SettingsNode):
    """Authoritative host settings manager providing dot-access configuration.

    Inherits recursive dot-access and dictionary indexing from `_SettingsNode`.
    Connects to the authoritative SQLite persistence store (`SettingsStore`) to
    load, cache, and structure configuration records across all defined scopes.
    """

    def __init__(
        self,
        db_path: Path | str | None = None,
        *,
        auto_load: bool = True,
    ) -> None:
        """Initialize HostSettings with optional database path.

        Args:
            db_path: Optional path to SQLite database. Defaults to repository store.
            auto_load: Whether to load settings immediately upon construction.
        """
        super().__init__()
        self._store = SettingsStore(db_path=Path(db_path) if db_path else None)
        self._scopes: dict[str, _SettingsNode] = {}
        self._revision: int = 1
        self._loaded: bool = False
        if auto_load:
            self.reload()

    @property
    def db_path(self) -> Path:
        """Return filesystem path to underlying SQLite database."""
        return self._store.db_path

    @property
    def store(self) -> SettingsStore:
        """Return underlying SettingsStore instance."""
        return self._store

    @property
    def revision(self) -> int:
        """Return current cached revision number."""
        self._ensure_loaded()
        return self._revision

    def _ensure_loaded(self) -> None:
        """Ensure settings are loaded from disk if not yet loaded."""
        if not self._loaded:
            self.reload()

    def reload(self) -> None:
        """Query host database and reload all scoped settings into memory."""
        self._data.clear()
        self._raw.clear()
        self._scopes.clear()

        # Auto-initialize store if database file absent or table not created
        if not self._store.db_path.exists():
            try:
                self._store.initialize()
            except (sqlite3.Error, PersistenceError) as exc:
                logger.warning(
                    "FR-HOST-SETTINGS-LOAD: Database initialization skipped (%s)",
                    exc,
                    extra={"fr_id": "FR-HOST-SETTINGS-LOAD"},
                )
        else:
            with contextlib.suppress(sqlite3.Error, PersistenceError):
                self._store.initialize()

        rev, scoped_vals = self._store.read_all_scoped()
        self._revision = rev

        total_keys = 0
        for scope, keyvals in scoped_vals.items():
            scope_dict: dict[str, Any] = {}
            clean_scope = scope.replace(".", "_")

            for key, val in keyvals.items():
                wrapped = self.wrap(val)
                clean_key = key.replace(".", "_")

                self._data[clean_key] = wrapped
                if clean_key != key:
                    self._data[key] = wrapped

                scope_dict[clean_key] = wrapped
                if clean_key != key:
                    scope_dict[key] = wrapped
                total_keys += 1

            scope_node = _SettingsNode(scope_dict)
            self._scopes[clean_scope] = scope_node
            self._data[clean_scope] = scope_node
            if clean_scope != scope:
                self._scopes[scope] = scope_node
                self._data[scope] = scope_node

        self._loaded = True
        logger.info(
            "FR-HOST-SETTINGS-LOAD: Loaded %d records in %d scopes. Revision: %d",
            total_keys,
            len(scoped_vals),
            self._revision,
            extra={
                "scopes": list(scoped_vals.keys()),
                "count": total_keys,
                "revision": self._revision,
                "fr_id": "FR-HOST-SETTINGS-LOAD",
            },
        )

    @override
    def _resolve(self, name: str) -> Any:
        """Resolve setting by attribute or scope namespace with debug telemetry.

        Args:
            name: Key or scope attribute name.

        Returns:
            Resolved setting value, _SettingsNode scope, or `_MISSING`.
        """
        self._ensure_loaded()
        val = super()._resolve(name)
        if val is not _MISSING:
            logger.debug(
                "FR-HOST-SETTINGS-DOT-ACCESS: Accessed setting attribute '%s'",
                name,
                extra={"key": name, "fr_id": "FR-HOST-SETTINGS-DOT-ACCESS"},
            )
            return val

        if name in self._scopes:
            logger.debug(
                "FR-HOST-SETTINGS-DOT-ACCESS: Accessed scope namespace '%s'",
                name,
                extra={"scope": name, "fr_id": "FR-HOST-SETTINGS-DOT-ACCESS"},
            )
            return self._scopes[name]

        clean_name = name.replace(".", "_")
        if clean_name in self._scopes:
            logger.debug(
                "FR-HOST-SETTINGS-DOT-ACCESS: Accessed scope namespace '%s'",
                clean_name,
                extra={"scope": clean_name, "fr_id": "FR-HOST-SETTINGS-DOT-ACCESS"},
            )
            return self._scopes[clean_name]

        return _MISSING

    @override
    def _attribute_not_found(self, name: str) -> AttributeError:
        """Construct exception for missing attribute in HostSettings."""
        return AttributeError(f"HostSettings has no setting or scope '{name}'")

    @override
    def _key_not_found(self, name: str) -> KeyError:
        """Construct exception for missing key indexing in HostSettings."""
        return KeyError(f"HostSettings has no setting or scope '{name}'")

    def items(self) -> list[tuple[str, Any]]:
        """Return list of (key, value) pairs."""
        self._ensure_loaded()
        return list(self._data.items())

    def update(
        self,
        changes: dict[str, dict[str, Any]],
        *,
        expected_revision: int | None = None,
    ) -> HostSettingsSnapshot:
        """Update settings in the persistence store and reload into memory.

        Args:
            changes: Scoped mapping of changes.
            expected_revision: Expected current revision for conflict check.

        Returns:
            Updated HostSettingsSnapshot.
        """
        snapshot = self._store.update_batch(
            changes, expected_revision=expected_revision
        )
        self.reload()
        return snapshot

    def get_snapshot(self) -> HostSettingsSnapshot:
        """Return current snapshot with revision and values."""
        self._ensure_loaded()
        return self._store.get_snapshot()

    def validate_workspace_paths(self) -> dict[str, bool]:
        """Validate configured workspace directories on disk.

        Returns:
            Mapping of directory name to existence boolean.
        """
        self._ensure_loaded()
        workspace_paths = self.get("workspace_paths")
        paths_to_validate: dict[str, Path] = {}

        if isinstance(workspace_paths, (_SettingsNode, dict)):
            paths_to_validate = {
                "Configs": Path(
                    str(workspace_paths.get("configs_dir", "data/configs"))
                ),
                "Data": Path(str(workspace_paths.get("data_dir", "data"))),
                "Projects": Path(
                    str(workspace_paths.get("projects_dir", "data/projects"))
                ),
                "Strategies": Path(
                    str(workspace_paths.get("strategies_dir", "data/strategies"))
                ),
            }
        else:
            paths_to_validate = {
                "Configs": Path("data/configs"),
                "Data": Path("data"),
                "Projects": Path("data/projects"),
                "Strategies": Path("data/strategies"),
            }

        results: dict[str, bool] = {}
        for dir_name, path in paths_to_validate.items():
            exists = path.exists()
            results[dir_name] = exists
            if exists:
                logger.info(
                    "FR-HOST-SETTINGS-PATH-VALIDATION: Directory '%s' exists.",
                    dir_name,
                    extra={
                        "directory_name": dir_name,
                        "fr_id": "FR-HOST-SETTINGS-PATH-VALIDATION",
                    },
                )
            else:
                logger.warning(
                    "FR-HOST-SETTINGS-PATH-VALIDATION: Directory '%s' absent.",
                    dir_name,
                    extra={
                        "directory_name": dir_name,
                        "fr_id": "FR-HOST-SETTINGS-PATH-VALIDATION",
                    },
                )

        return results

    @override
    def __repr__(self) -> str:
        """Return developer representation of HostSettings."""
        return (
            f"HostSettings(db_path={self.db_path!r}, revision={self._revision}, "
            f"loaded_keys={len(self._data)})"
        )


# Aliases for domain conventions
AppSettings = HostSettings
SettingsManager = HostSettings


def _extract_put_payload(body: Any) -> tuple[int, dict[str, dict[str, Any]]]:
    """Validate and extract expected revision and changes from PUT body."""
    if not isinstance(body, dict):
        raise ValidationError("Request body must be a JSON object")
    expected_rev = body.get("expected_revision")
    if not isinstance(expected_rev, int) or expected_rev < 0:
        raise ValidationError("expected_revision must be a non-negative integer")
    changes = body.get("changes")
    if not isinstance(changes, dict):
        raise ValidationError("changes must be a dictionary of scoped settings")
    return expected_rev, changes


def create_settings_router(
    settings_instance: HostSettings | None = None,
) -> APIRouter:
    """Create FastAPI APIRouter exposing host settings REST projections.

    Args:
        settings_instance: HostSettings instance to expose. Defaults to
            global singleton.

    Returns:
        Configured FastAPI APIRouter.
    """
    router = APIRouter()
    target_settings = settings_instance or settings

    @router.get("/settings")
    async def get_settings_endpoint() -> JSONResponse:
        """Retrieve current shell settings and preferences snapshot."""
        logger.debug(
            "FR-HOST-SETTINGS-PROJECTION: Handling GET /settings query.",
            extra={"fr_id": "FR-HOST-SETTINGS-PROJECTION"},
        )
        snapshot = target_settings.get_snapshot()
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "success", "data": snapshot.model_dump()},
        )

    @router.put("/settings")
    async def put_settings_endpoint(request: Request) -> JSONResponse:
        """Atomically update host settings with revision check."""
        try:
            body = await request.json()
        except ValueError, TypeError, json.JSONDecodeError:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "status": "error",
                    "error": {
                        "code": "INVALID_JSON",
                        "message": "Malformed JSON payload in request body",
                    },
                },
            )

        try:
            expected_rev, changes = _extract_put_payload(body)
            snapshot = target_settings.update(changes, expected_revision=expected_rev)
            logger.info(
                "FR-HOST-SETTINGS-PROJECTION: Updated settings to revision %d.",
                snapshot.revision,
                extra={
                    "fr_id": "FR-HOST-SETTINGS-PROJECTION",
                    "revision": snapshot.revision,
                },
            )
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"status": "success", "data": snapshot.model_dump()},
            )
        except RevisionConflictError as exc:
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={
                    "status": "error",
                    "error": {
                        "code": "REVISION_CONFLICT",
                        "message": str(exc),
                        "current_revision": target_settings.revision,
                    },
                },
            )
        except ValidationError as exc:
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                content={
                    "status": "error",
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": str(exc),
                    },
                },
            )

    @router.get("/settings/paths/validate")
    async def validate_paths_endpoint() -> JSONResponse:
        """Validate configured workspace directories on disk."""
        statuses = target_settings.validate_workspace_paths()
        all_valid = all(statuses.values())
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "data": {
                    "paths": statuses,
                    "all_valid": all_valid,
                },
            },
        )

    return router


# Export convenient global singleton with lazy loading (no I/O on import)
settings = HostSettings(auto_load=False)
