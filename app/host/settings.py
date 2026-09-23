"""Transactional, host-owned settings in the application SQLite database."""

from __future__ import annotations

import json
import math
import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from starlette.requests import Request
from starlette.responses import JSONResponse

from app.host.envelope import error_payload, success_payload
from app.host.events import SETTINGS_CHANNEL
from app.host.http import envelope_response, read_json_body, request_id_of

DEFAULT_DATABASE_PATH = Path("data/database/haruquantai.db")
REVISION_KEY = "__revision__"
SCHEMA_VERSION = 1
APPLICATION_SCOPE = "application"
HOST_SCOPE = "host"

# Only these non-secret shell preference fields may cross the settings API.
# The remaining scoped records, including credential fields, stay in SQLite.
PUBLIC_FIELDS: dict[str, dict[str, str]] = {
    "app.general": {
        "theme": "str",
        "language": "str",
        "zoom": "number",
        "gpu_accelerated": "bool",
    },
    "config.global": {
        "sounds_off": "bool",
        "advanced_file_chooser": "bool",
        "show_control_orders": "bool",
        "header_custom_text": "str",
        "footer_custom_text": "str",
        "default_result_to_display": "str",
        "language": "str",
        "theme": "str",
    },
    "config.cpu": {
        "core_usage": "str",
        "custom_cores": "int",
        "high_priority": "bool",
        "thread_affinity": "bool",
    },
    "config.performance": {
        "compute_pips_metrics": "bool",
        "compute_pcts_metrics": "bool",
        "compute_separate_metrics": "bool",
    },
    "config.memory": {
        "gc_type": "str",
        "memory_limit_gb": "number",
        "dont_store_pending_orders": "bool",
        "memory_cleanup": "bool",
        "cleanup_interval_mins": "int",
        "automatic_memory": "bool",
    },
    "config.databanks": {
        "databank_sync_interval_mins": "interval",
        "sync_databanks_after_task_done": "bool",
        "store_chart_data": "bool",
    },
    "config.optimizations": {"dont_store_op_3d_charts_data": "bool"},
    "config.troubleshooting": {
        "gpu_accelerated": "bool",
        "memory_protection": "bool",
        "debug_level_active": "bool",
    },
    "notify.email": {
        "smtp_server": "str",
        "smtp_port": "int",
        "use_ssl": "bool",
        "use_tls": "bool",
        "username": "str",
        "from_address": "str",
    },
    "connect.remote": {
        "allow": "bool",
        "require_password": "bool",  # pragma: allowlist secret
    },
}

ALLOWED_VALUES: dict[str, tuple[Any, ...]] = {
    "theme": ("dark", "light"),
    "language": (
        "en",
        "cs",
        "zh-CN",
        "zh-TW",
        "fr",
        "de",
        "id",
        "it",
        "pl",
        "pt",
        "ru",
        "es",
    ),
    "default_result_to_display": ("Main", "Portfolio"),
    "core_usage": ("single", "all_except_one", "custom", "all"),
    "gc_type": ("ParallelGC", "G1GC", "Automatic"),
    "cleanup_interval_mins": (5, 15, 30, 60),
    "databank_sync_interval_mins": (None, 0, 5, 10, 15, 60),
}
FIELD_RANGES: dict[str, tuple[float, float]] = {
    "zoom": (0.7, 1.8),
    "custom_cores": (1, 1024),
    "memory_limit_gb": (2, 1024),
    "smtp_port": (1, 65535),
}
TITLE_FIELDS = frozenset(("header_custom_text", "footer_custom_text"))
MAX_TITLE_LENGTH = 30


def _valid_field(value: Any, kind: str) -> bool:
    if kind == "str":
        return isinstance(value, str)
    if kind == "bool":
        return type(value) is bool
    if kind == "int":
        return type(value) is int
    if kind == "number":
        return type(value) in (int, float) and math.isfinite(value)
    if kind == "interval":
        return value is None or (type(value) is int and value >= 0)
    return False


def _valid_setting(key: str, field: str, value: Any) -> bool:
    kind = PUBLIC_FIELDS[key].get(field)
    if kind is None or not _valid_field(value, kind):
        return False
    allowed = ALLOWED_VALUES.get(field)
    if allowed is not None and value not in allowed:
        return False
    bounds = FIELD_RANGES.get(field)
    if bounds is not None and not bounds[0] <= value <= bounds[1]:
        return False
    return field not in TITLE_FIELDS or len(value) <= MAX_TITLE_LENGTH


def _decode_record(value_json: str) -> dict[str, Any]:
    try:
        value = json.loads(value_json)
    except (TypeError, json.JSONDecodeError) as error:
        raise SettingsError("Malformed host settings value") from error
    if not isinstance(value, dict):
        raise SettingsError("Host settings record must be an object")
    return value


def _public_record(key: str, value: dict[str, Any]) -> dict[str, Any]:
    fields = PUBLIC_FIELDS[key]
    for field, field_value in value.items():
        if field in fields and not _valid_setting(key, field, field_value):
            raise SettingsError("Invalid host settings field")
    return {field: value[field] for field in fields if field in value}


def _update_record(
    connection: sqlite3.Connection, key: str, updates: dict[str, Any], timestamp: str
) -> None:
    row = connection.execute(
        "SELECT value_json, schema_version FROM host_settings WHERE scope=? AND key=?",
        (APPLICATION_SCOPE, key),
    ).fetchone()
    if row is None:
        value: dict[str, Any] = {}
    else:
        if row[1] != SCHEMA_VERSION:
            raise SettingsError("Unsupported host settings schema version")
        value = _decode_record(row[0])
    value.update(updates)
    try:
        value_json = json.dumps(value, allow_nan=False, sort_keys=True)
    except (TypeError, ValueError) as error:
        raise SettingsError("Settings must be JSON values") from error
    connection.execute(
        "INSERT INTO host_settings "
        "(scope, key, value_json, schema_version, updated_at_utc) "
        "VALUES (?, ?, ?, ?, ?) ON CONFLICT(scope, key) DO UPDATE SET "
        "value_json=excluded.value_json, "
        "schema_version=excluded.schema_version, "
        "updated_at_utc=excluded.updated_at_utc",
        (APPLICATION_SCOPE, key, value_json, SCHEMA_VERSION, timestamp),
    )


def _validate_changes(changes: dict[str, Any]) -> None:
    if not changes:
        raise SettingsError("Settings change must not be empty")
    for key, fields in changes.items():
        if key not in PUBLIC_FIELDS or not isinstance(fields, dict) or not fields:
            raise SettingsError("Unknown or empty settings record")
        for field, value in fields.items():
            if not _valid_setting(key, field, value):
                raise SettingsError("Unknown or invalid settings field")


class SettingsError(Exception):
    """Settings database has an invalid schema or value."""


class SettingsConflictError(SettingsError):
    """The caller attempted to replace a newer settings revision."""


def _now() -> str:
    return datetime.now(tz=UTC).isoformat()


class SettingsStore:
    """Read and atomically update host settings without touching other owners."""

    def __init__(self, path: Path) -> None:
        """Open the database and initialize the host-owned settings table."""
        self._path = path
        self._prepare()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._path, timeout=5.0, isolation_level=None)
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 5000")
        return connection

    def _prepare(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with closing(self._connect()) as connection, connection:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute(
                    "CREATE TABLE IF NOT EXISTS host_settings ("
                    "scope TEXT NOT NULL, key TEXT NOT NULL, "
                    "value_json TEXT NOT NULL, schema_version INTEGER NOT NULL, "
                    "updated_at_utc TEXT NOT NULL, PRIMARY KEY (scope, key))"
                )
                columns = [
                    (row[1], row[3], row[5])
                    for row in connection.execute("PRAGMA table_info(host_settings)")
                ]
                if columns != [
                    ("scope", 1, 1),
                    ("key", 1, 2),
                    ("value_json", 1, 0),
                    ("schema_version", 1, 0),
                    ("updated_at_utc", 1, 0),
                ]:
                    raise SettingsError("Incompatible host_settings schema")
                connection.execute(
                    "INSERT OR IGNORE INTO host_settings "
                    "(scope, key, value_json, schema_version, updated_at_utc) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (HOST_SCOPE, REVISION_KEY, "0", SCHEMA_VERSION, _now()),
                )
        except sqlite3.Error as error:
            raise SettingsError("Cannot initialize settings database") from error

    @staticmethod
    def _snapshot(connection: sqlite3.Connection) -> dict[str, Any]:
        values: dict[str, Any] = {}
        revision: int | None = None
        for scope, key, value_json, schema_version in connection.execute(
            "SELECT scope, key, value_json, schema_version FROM host_settings "
            "WHERE (scope=? AND key=?) OR scope=?",
            (HOST_SCOPE, REVISION_KEY, APPLICATION_SCOPE),
        ):
            if scope == APPLICATION_SCOPE and key not in PUBLIC_FIELDS:
                continue
            if schema_version != SCHEMA_VERSION:
                raise SettingsError("Unsupported host settings schema version")
            try:
                value = json.loads(value_json)
            except (TypeError, json.JSONDecodeError) as error:
                raise SettingsError("Malformed host settings value") from error
            if scope == HOST_SCOPE and key == REVISION_KEY:
                if type(value) is not int or value < 0:
                    raise SettingsError("Invalid settings revision")
                revision = value
            else:
                if not isinstance(value, dict):
                    raise SettingsError("Host settings record must be an object")
                values[key] = _public_record(key, value)
        if revision is None:
            raise SettingsError("Missing settings revision")
        return {"revision": revision, "values": values}

    def snapshot(self) -> dict[str, Any]:
        """Return a consistent revision and settings object."""
        try:
            with closing(self._connect()) as connection:
                return self._snapshot(connection)
        except sqlite3.Error as error:
            raise SettingsError("Cannot read host settings") from error

    def get_all(self) -> dict[str, Any]:
        """Return only user-visible settings values."""
        return cast("dict[str, Any]", self.snapshot()["values"])

    def patch(
        self, changes: dict[str, Any], expected_revision: int, *, bus: Any = None
    ) -> dict[str, Any]:
        """Commit safe field updates to scoped records at one revision."""
        _validate_changes(changes)
        try:
            with closing(self._connect()) as connection:
                connection.execute("BEGIN IMMEDIATE")
                try:
                    current = self._snapshot(connection)
                    if current["revision"] != expected_revision:
                        raise SettingsConflictError(
                            "Settings changed; reload and retry"
                        )
                    timestamp = _now()
                    for key, updates in changes.items():
                        _update_record(connection, key, updates, timestamp)
                    revision = current["revision"] + 1
                    connection.execute(
                        "UPDATE host_settings SET value_json=?, updated_at_utc=? "
                        "WHERE scope=? AND key=?",
                        (str(revision), timestamp, HOST_SCOPE, REVISION_KEY),
                    )
                    saved = self._snapshot(connection)
                    connection.execute("COMMIT")
                except SettingsError, sqlite3.Error:
                    connection.execute("ROLLBACK")
                    raise
        except sqlite3.Error as error:
            raise SettingsError("Cannot save host settings") from error
        if bus is not None:
            bus.publish(SETTINGS_CHANNEL, saved["values"])
        return saved


async def get_settings(request: Request) -> JSONResponse:
    """Handle authenticated ``GET /api/v1/settings``."""
    request_id = request_id_of(request)
    store: SettingsStore = request.app.state.services.settings
    return envelope_response(request_id, success_payload(request_id, store.snapshot()))


async def put_settings(request: Request) -> JSONResponse:
    """Handle conditional ``PUT /api/v1/settings``."""
    body = await read_json_body(request)
    request_id = request_id_of(request)
    revision = body.get("expected_revision")
    changes = body.get("changes")
    if type(revision) is not int or revision < 0 or not isinstance(changes, dict):
        return envelope_response(
            request_id,
            error_payload(
                request_id, "INVALID_SETTINGS", "Expected revision and changes"
            ),
            400,
        )
    store: SettingsStore = request.app.state.services.settings
    try:
        saved = store.patch(changes, revision, bus=request.app.state.services.events)
    except SettingsConflictError:
        return envelope_response(
            request_id,
            error_payload(
                request_id, "SETTINGS_CONFLICT", "Settings changed; reload and retry"
            ),
            409,
        )
    except SettingsError:
        return envelope_response(
            request_id,
            error_payload(request_id, "INVALID_SETTINGS", "Invalid settings value"),
            400,
        )
    return envelope_response(request_id, success_payload(request_id, saved))
