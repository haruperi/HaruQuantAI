"""Authoritative settings storage repository for host persistence subsystem.

Description:
    Provides transactional, parameterized CRUD operations against the `host_settings`
    table with strict connection lifecycles, concurrency serialization, workspace path
    validation, batch updates, and backup export/import capabilities.

Purpose:
    FEAT-HOST-PERSISTENCE: Scoped host settings persistence.

Key Capabilities:
    - FR-HOST-PERSISTENCE-SETTINGS: Setting reads, batch writes/deletes and backups.
      Associated: `SettingsStore.read_all()`, `SettingsStore.update_batch()`,
        `SettingsStore.backup_to()`, `SettingsStore.restore_from()`
      Logging: DEBUG reads; INFO changes; WARNING unavailable/corrupt data.

Python API Usage:
    ```python
    from app.host.persistence.stores.settings import SettingsStore

    store = SettingsStore(":memory:")
    store.initialize()
    store.update_batch("workspace", {"theme": "dark"})
    settings = store.read_all("workspace")
    ```

CLI Usage:
    No direct persistence CLI. Settings management is performed via diagnostics:
    ```bash
    uv run python -m app.host.diagnostics --status
    ```
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from app.host.logging import get_logger
from app.host.persistence.engine import (
    _BUSY_TIMEOUT_SECONDS,
    DEFAULT_READ_LIMIT,
    MAX_BATCH_SIZE,
    MAX_READ_LIMIT,
    SETTINGS_RECORD_SCHEMA_VERSION,
    DatabaseManager,
    canonical_json,
    now_utc_iso,
    validate_identifier,
)
from app.host.persistence.errors import (
    CorruptDataError,
    IncompatibleSchemaError,
    PersistenceError,
    RevisionConflictError,
    StorageBusyError,
    ValidationError,
)
from app.host.persistence.models import SettingRecord, SettingsPage
from app.host.persistence.schema import ensure_settings_schema

logger = get_logger(__name__)


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
        busy_timeout: float = _BUSY_TIMEOUT_SECONDS,
        db: DatabaseManager | None = None,
    ) -> None:
        """Initialize SettingsStore with an authoritative database file path or manager.

        Args:
            db_path: Optional path to the SQLite database file or ':memory:'.
            busy_timeout: Timeout in seconds for SQLite lock waits.
            db: Optional preexisting DatabaseManager instance.
        """
        self._db: DatabaseManager = db or DatabaseManager(
            db_path, busy_timeout=busy_timeout
        )
        self._busy_timeout: float = busy_timeout

    @property
    def db_path(self) -> Path:
        """Return the resolved database file path."""
        return self._db.database_path

    @property
    def db(self) -> DatabaseManager:
        """Return the underlying DatabaseManager instance."""
        return self._db

    def initialize(self) -> None:
        """Verify existing database schema or create required table transactionally.

        Raises:
            IncompatibleSchemaError: If the existing table schema is incompatible.
            PersistenceError: If table creation or schema verification fails.
        """
        logger.debug(
            "SettingsStore.initialize storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-SETTINGS"},
        )
        try:
            with self._db.transaction() as conn:
                ensure_settings_schema(conn)
                self._ensure_revision_exists(conn)
        except IncompatibleSchemaError, StorageBusyError:
            raise
        except sqlite3.OperationalError as exc:
            if "busy" in str(exc).lower() or "locked" in str(exc).lower():
                raise StorageBusyError(
                    "Database is busy during schema initialization"
                ) from exc
            raise PersistenceError("Failed to initialize database schema") from exc
        except Exception as exc:
            raise PersistenceError("Failed to initialize database schema") from exc

        logger.info(
            "FR-HOST-SETTINGS-SCHEMA: Initialized host_settings table.",
            extra={
                "db_path": str(self._db.database_path),
                "fr_id": "FR-HOST-SETTINGS-SCHEMA",
            },
        )

    def _ensure_revision_exists(self, conn: sqlite3.Connection) -> None:
        """Ensure the internal _system:revision key exists in host_settings."""
        row = conn.execute(
            "SELECT value_json FROM host_settings "
            "WHERE scope = '_system' AND key = 'revision'"
        ).fetchone()
        if row is None:
            now_ts = now_utc_iso()
            conn.execute(
                """
                INSERT OR IGNORE INTO host_settings (
                    scope, key, value_json, schema_version, updated_at_utc
                )
                VALUES ('_system', 'revision', '1', ?, ?)
                """,
                (SETTINGS_RECORD_SCHEMA_VERSION, now_ts),
            )

    def get_revision(self) -> int:
        """Query current monotonic revision counter."""
        logger.debug(
            "SettingsStore.get_revision storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-SETTINGS"},
        )
        if not self._db.is_memory and not self._db.database_path.exists():
            return 1
        with self._db.connection(query_only=True) as conn:
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
        """Query scoped host settings with pagination and optional single key lookup."""
        logger.debug(
            "SettingsStore.read_settings storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-SETTINGS"},
        )
        validate_identifier(scope, "scope")
        if key is not None:
            validate_identifier(key, "key")
        if after_key is not None:
            validate_identifier(after_key, "after_key")
        if not (1 <= limit <= MAX_READ_LIMIT):
            raise ValidationError(
                f"limit must be between 1 and {MAX_READ_LIMIT}, got {limit}"
            )

        if not self._db.is_memory and not self._db.database_path.exists():
            return SettingsPage(items=[], next_key=None)

        with self._db.connection(query_only=True) as conn:
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
        next_cursor = display_rows[-1]["key"] if has_more and display_rows else None

        records = [self._row_to_record(r) for r in display_rows]
        return SettingsPage(items=records, next_key=next_cursor)

    def read_all(self) -> tuple[int, list[SettingRecord]]:
        """Read configuration records and their global storage revision."""
        logger.debug(
            "SettingsStore.read_all storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-SETTINGS"},
        )
        if not self._db.is_memory and not self._db.database_path.exists():
            return 1, []
        with self._db.connection(query_only=True) as conn:
            try:
                rows = conn.execute(
                    "SELECT * FROM host_settings ORDER BY scope, key"
                ).fetchall()
            except sqlite3.OperationalError as exc:
                logger.warning(
                    "Settings storage read unavailable",
                    extra={
                        "error_type": type(exc).__name__,
                        "fr_id": "FR-HOST-PERSISTENCE-SETTINGS",
                    },
                )
                return 1, []
        revision = 1
        records: list[SettingRecord] = []
        for row in rows:
            if row["scope"] == "_system" and row["key"] == "revision":
                try:
                    revision = int(json.loads(row["value_json"]))
                except (ValueError, TypeError) as exc:
                    raise CorruptDataError("Corrupt settings revision") from exc
                continue
            try:
                records.append(self._row_to_record(row))
            except CorruptDataError:
                logger.warning(
                    "Skipping corrupt settings row",
                    extra={"fr_id": "FR-HOST-PERSISTENCE-SETTINGS"},
                )
        logger.debug(
            "Read settings records",
            extra={"count": len(records), "fr_id": "FR-HOST-PERSISTENCE-SETTINGS"},
        )
        return revision, records

    def _validate_batch_changes(
        self, changes: dict[str, dict[str, Any]]
    ) -> list[tuple[str, str, Any, str]]:
        """Validate all items in a batch update mapping."""
        total_items = sum(len(v) for v in changes.values() if isinstance(v, dict))
        if total_items > MAX_BATCH_SIZE:
            raise ValidationError(
                f"Total batch items {total_items} exceeds limit {MAX_BATCH_SIZE}"
            )

        validated_items: list[tuple[str, str, Any, str]] = []
        for scope, scope_changes in changes.items():
            validate_identifier(scope, "scope")
            if not isinstance(scope_changes, dict):
                raise ValidationError(
                    f"Scope changes for '{scope}' must be a dictionary"
                )
            for key, val in scope_changes.items():
                validate_identifier(key, "key")
                encoded = canonical_json(val)
                validated_items.append((scope, key, val, encoded))

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
        deletions: tuple[tuple[str, str], ...] = (),
    ) -> tuple[int, list[SettingRecord]]:
        """Atomically update multiple scoped settings with optimistic locking."""
        logger.debug(
            "SettingsStore.update_batch storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-SETTINGS"},
        )
        if not changes and not deletions:
            return self.read_all()

        validated_items = self._validate_batch_changes(changes)
        updates = {(scope, key) for scope, key, _, _ in validated_items}
        if len(deletions) > MAX_BATCH_SIZE or len(set(deletions)) != len(deletions):
            raise ValidationError("Invalid settings deletion batch.")
        for scope, key in deletions:
            validate_identifier(scope, "scope")
            validate_identifier(key, "key")
            if scope == "_system" or (scope, key) in updates:
                raise ValidationError("Protected or ambiguous settings deletion.")

        with self._db.transaction() as conn:
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
                    "SELECT value_json FROM host_settings WHERE scope = ? AND key = ?",
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
                    (scope, key, raw_json, SETTINGS_RECORD_SCHEMA_VERSION, now_ts),
                )
                changed_count += 1

            for scope, key in deletions:
                cursor = conn.execute(
                    "DELETE FROM host_settings WHERE scope = ? AND key = ?",
                    (scope, key),
                )
                changed_count += cursor.rowcount

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
                    (json.dumps(new_revision), SETTINGS_RECORD_SCHEMA_VERSION, now_ts),
                )

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
        return self.read_all()

    def backup_to(self, destination: Path) -> None:
        """Create a consistent SQLite backup without overwriting an existing file."""
        target = destination.resolve()
        if self._db.is_memory or not self.db_path.exists():
            raise ValidationError("Backup requires an existing file database.")
        if target == self.db_path.resolve() or target.exists():
            raise ValidationError("Backup destination must be a new file.")
        target.parent.mkdir(parents=True, exist_ok=True)
        # Exclusive creation closes the existence-check race before SQLite opens it.
        with target.open("xb"):
            pass
        try:
            with self._db.connection(query_only=True) as source:
                backup = sqlite3.connect(str(target), timeout=self._busy_timeout)
                try:
                    source.backup(backup)
                    if backup.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                        raise PersistenceError("Backup integrity verification failed.")
                finally:
                    backup.close()
        except sqlite3.Error as exc:
            logger.error(  # noqa: TRY400 - Never expose database exception payloads.
                "Settings database backup failed",
                extra={"fr_id": "FR-HOST-PERSISTENCE-SETTINGS"},
            )
            raise PersistenceError("Settings database backup failed.") from exc
        logger.info(
            "Settings database backup completed",
            extra={"fr_id": "FR-HOST-PERSISTENCE-SETTINGS"},
        )

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
        if row["schema_version"] != SETTINGS_RECORD_SCHEMA_VERSION:
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
