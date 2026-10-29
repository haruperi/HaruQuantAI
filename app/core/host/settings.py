"""Lazy stored settings, accessed exclusively through HostPersistence.

Use `settings.application.app_general.theme` or `settings.app_general.theme`.
Reads use a cached, detached snapshot; reload() explicitly refreshes it.
save_settings() replaces complete stored JSON records atomically and returns the
new revision. No defaults, schema migrations, or missing records are synthesized.
Snapshots are internal configuration containers, including stored credentials.
Legacy unquoted text is read as a string; new saves always encode valid JSON.
"""

from __future__ import annotations

import copy
import json
import math
import threading
from collections.abc import Iterator, Mapping, Sequence
from datetime import UTC, datetime
from typing import Any, override

from app.core.host.logging import get_logger
from app.core.host.persistence import HostPersistence
from app.core.lib.responses import ErrorCode

__all__ = [
    "RevisionConflictError",
    "SettingsDataError",
    "SettingsManager",
    "SettingsPersistenceError",
    "settings",
]

logger = get_logger(__name__)
_TABLE = "host_settings"
_MARKERS = frozenset({("_system", "revision"), ("host", "__revision__")})
_MAX_BATCH = 1000
_MAX_REVISION = 2**63 - 1


class RevisionConflictError(RuntimeError):
    """The supplied settings revision is stale; reload before retrying."""

    def __init__(self, *, expected_revision: int, current_revision: int) -> None:
        self.expected_revision = expected_revision
        self.current_revision = current_revision
        super().__init__(
            f"Settings revision conflict: expected {expected_revision}, "
            f"current {current_revision}"
        )


class SettingsPersistenceError(RuntimeError):
    """A persistence response rejected a settings operation."""

    def __init__(self, response: Mapping[str, Any]) -> None:
        error = response["error"]
        self.code = ErrorCode(error["code"])
        self.retryable: bool = error["retryable"]
        super().__init__("Settings persistence operation failed")


class SettingsDataError(ValueError):
    """Stored settings contain invalid JSON or revision metadata."""


def _unwrap(response: dict[str, Any]) -> dict[str, Any]:
    if not response["success"]:
        raise SettingsPersistenceError(response)
    data: dict[str, Any] = response["data"]
    return data


def _revision(value: object) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= _MAX_REVISION
    ):
        raise SettingsDataError(
            "Settings revisions must be non-negative SQLite integers"
        )
    return value


def _json_value(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("Setting object keys must be strings")
            _json_value(item)
    elif isinstance(value, list):
        for item in value:
            _json_value(item)
    elif (
        value is not None
        and not isinstance(value, (str, bool, int))
        and (not isinstance(value, float) or not math.isfinite(value))
    ):
        raise ValueError("Setting values must be finite JSON values")


def _encode(value: Any) -> str:
    _json_value(value)
    return json.dumps(value, allow_nan=False, sort_keys=True, separators=(",", ":"))


def _decode(raw: Any) -> Any:
    try:
        value = _parse_stored_value(raw)
        _json_value(value)
        return value
    except (TypeError, ValueError, RecursionError) as error:
        raise SettingsDataError("Stored setting is not valid finite JSON") from error


def _parse_stored_value(raw: Any) -> Any:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Older settings writers stored plain strings (for example UI themes).
        # Do not turn malformed structured JSON into apparently valid text.
        if isinstance(raw, str) and not raw.lstrip().startswith(("{", "[", '"')):
            return raw
        raise


class _SettingsNode(Mapping[str, Any]):
    """Read-only mapping and attribute view; mutable leaf values are copied."""

    __slots__ = ("_values",)

    def __init__(self, values: dict[str, Any]) -> None:
        self._values = copy.deepcopy(values)

    @override
    def __getitem__(self, key: str) -> Any:
        return _view(self._values[key])

    def __getattr__(self, key: str) -> Any:
        try:
            return self[key]
        except KeyError:
            raise AttributeError("Stored setting does not exist") from None

    @override
    def __iter__(self) -> Iterator[str]:
        return iter(self._values)

    @override
    def __len__(self) -> int:
        return len(self._values)

    @override
    def __repr__(self) -> str:
        return f"SettingsNode({len(self)} stored keys)"


def _view(value: Any) -> Any:
    return _SettingsNode(value) if isinstance(value, dict) else copy.deepcopy(value)


def _read_all(
    gateway: HostPersistence,
) -> tuple[dict[str, dict[str, Any]], int, list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    cursor = None
    while True:
        data = _unwrap(
            gateway.read_records(_TABLE, pagination="cursor", cursor=cursor, limit=1000)
        )
        rows.extend(data["records"])
        cursor = data["pagination"]["next_cursor"]
        if cursor is None:
            break
    values: dict[str, dict[str, Any]] = {}
    revision = 0
    for row in rows:
        scope, key = row["scope"], row["key"]
        value = _decode(row["value_json"])
        revision = max(revision, _revision(row["schema_version"]))
        if (scope, key) in _MARKERS:
            revision = max(revision, _revision(value))
        elif scope != "_system":
            values.setdefault(scope, {})[key] = value
    return values, revision, rows


def _prepare_updates(
    updates: Mapping[str, Mapping[str, Any]],
) -> dict[tuple[str, str], str]:
    if not isinstance(updates, Mapping) or not updates:
        raise ValueError("Updates must contain at least one stored scope")
    prepared = {}
    for scope, items in updates.items():
        if not isinstance(scope, str) or not scope or scope == "_system":
            raise ValueError("A non-system settings scope is required")
        if not isinstance(items, Mapping) or not items:
            raise ValueError("Each update scope must contain settings records")
        for key, value in items.items():
            if not isinstance(key, str) or not key or (scope, key) in _MARKERS:
                raise ValueError("A non-system setting key is required")
            prepared[scope, key] = _encode(value)
    if len(prepared) > _MAX_BATCH:
        raise ValueError("A batch may update at most 1000 settings records")
    return prepared


class SettingsManager:
    """Thread-safe lazy settings cache with optimistic, atomic database writes.

    Pass a gateway for testing or a separate database. Constructing this manager
    or importing the global instance performs no database access. A read failure
    leaves the previous cache intact and is never treated as empty configuration.
    Getter dictionaries and nodes are detached; edits require save_settings().
    """

    def __init__(self, persistence: HostPersistence | None = None) -> None:
        self._persistence = persistence
        self._lock = threading.RLock()
        self._loaded = False
        self._data: dict[str, dict[str, Any]] = {}
        self._revision = 0

    def _gateway(self) -> HostPersistence:
        if self._persistence is None:
            self._persistence = HostPersistence()
        return self._persistence

    def _ensure_loaded(self) -> None:
        if not self._loaded:
            self.reload()

    def reload(self) -> None:
        """Load all settings and their revision from one database transaction."""
        with self._lock:
            with self._gateway().transaction() as tx:
                values, revision, _ = _read_all(tx)
            self._data, self._revision, self._loaded = values, revision, True
            logger.info(
                "Settings loaded; scopes=%d; revision=%d", len(values), revision
            )

    @property
    def revision(self) -> int:
        """Revision of the cached snapshot; reload() detects external changes."""
        with self._lock:
            self._ensure_loaded()
            return self._revision

    def _scope(self, scope: str) -> dict[str, Any]:
        if scope in self._data:
            return self._data[scope]
        group = self._data.get("application", {}).get(scope)
        if isinstance(group, dict):
            return group
        raise KeyError(scope)

    def get_scope(self, scope: str) -> dict[str, Any]:
        """Return a detached stored scope or application group; missing raises."""
        with self._lock:
            self._ensure_loaded()
            return copy.deepcopy(self._scope(scope))

    def get(self, scope: str, key: str | None = None, default: Any = None) -> Any:
        """Read a value, using an explicit fallback only for this call."""
        with self._lock:
            self._ensure_loaded()
            try:
                values = self._scope(scope)
                value = values if key is None else values[key]
            except KeyError:
                return copy.deepcopy(default)
            logger.debug("Stored setting accessed")
            return _view(value)

    def __getitem__(self, scope: str) -> _SettingsNode:
        """Return a stored scope as a mapping with nested attribute access."""
        return _SettingsNode(self.get_scope(scope))

    def __getattr__(self, scope: str) -> Any:
        """Allow settings.host.port and application-group shortcuts."""
        if scope.startswith("_"):
            raise AttributeError(scope)
        try:
            return self[scope]
        except KeyError:
            raise AttributeError("Stored settings scope does not exist") from None

    def as_dict(self) -> dict[str, dict[str, Any]]:
        """Return only stored values, excluding internal revision markers."""
        with self._lock:
            self._ensure_loaded()
            return copy.deepcopy(self._data)

    def get_snapshot(self, *, scopes: Sequence[str] | None = None) -> dict[str, Any]:
        """Return detached cached values and revision, optionally selecting scopes.

        Missing scopes are omitted; no defaults are injected. Use reload() first
        when a fresh snapshot is needed. Scopes refer to stored database scopes.
        """
        with self._lock:
            self._ensure_loaded()
            if isinstance(scopes, str):
                raise TypeError("scopes must be a sequence of scope names")
            values = (
                self._data
                if scopes is None
                else {
                    scope: self._data[scope] for scope in scopes if scope in self._data
                }
            )
            return {"revision": self._revision, "values": copy.deepcopy(values)}

    def save_settings(
        self, updates: Mapping[str, Mapping[str, Any]], *, expected_revision: int
    ) -> int:
        """Replace existing records in one transaction, then refresh the cache.

        Use {scope: {key: complete_json_value}}. Nested objects are replaced,
        not patched. Missing records raise KeyError. Stale revisions raise
        RevisionConflictError. No-op batches preserve the revision and timestamps.
        The maximum stored row version and internal revision markers form the
        global revision; changed rows and existing markers advance it together.
        """
        prepared = _prepare_updates(updates)
        expected = _revision(expected_revision)
        with self._lock:
            with self._gateway().transaction() as tx:
                values, current, rows = _read_all(tx)
                _check_expected(expected, current)
                indexed = {(row["scope"], row["key"]): row for row in rows}
                changed = _changed_rows(prepared, indexed)
                revision = _revision(current + 1) if changed else current
                if changed:
                    timestamp = datetime.now(UTC).isoformat(timespec="microseconds")
                    for (scope, key), raw in changed.items():
                        _write_record(tx, indexed[scope, key], raw, revision, timestamp)
                        values[scope][key] = _decode(raw)
                    for identity in _MARKERS.intersection(indexed):
                        _write_record(
                            tx, indexed[identity], str(revision), revision, timestamp
                        )
            # Never publish provisional values before commit succeeds.
            self._data, self._revision, self._loaded = values, revision, True
            logger.info(
                "Settings batch committed; records=%d; revision=%d",
                len(changed),
                revision,
            )
            return revision


def _check_expected(expected: int, current: int) -> None:
    if expected != current:
        logger.warning(
            "Settings revision conflict; expected=%d; current=%d", expected, current
        )
        raise RevisionConflictError(
            expected_revision=expected, current_revision=current
        )


def _changed_rows(
    prepared: dict[tuple[str, str], str], indexed: dict[tuple[str, str], dict[str, Any]]
) -> dict[tuple[str, str], str]:
    changed = {}
    for identity, raw in prepared.items():
        if identity not in indexed:
            raise KeyError("Settings updates must target existing stored records")
        if raw != _encode(_decode(indexed[identity]["value_json"])):
            changed[identity] = raw
    return changed


def _write_record(
    gateway: HostPersistence,
    row: dict[str, Any],
    raw: str,
    revision: int,
    timestamp: str,
) -> None:
    _unwrap(
        gateway.update_record(
            _TABLE,
            {
                "value_json": raw,
                "schema_version": revision,
                "updated_at_utc": timestamp,
            },
            filters={
                "scope": row["scope"],
                "key": row["key"],
                "schema_version": row["schema_version"],
                "value_json": row["value_json"],
            },
        )
    )


settings = SettingsManager()


if __name__ == "__main__":
    """Demonstrate reading host settings via persistence read layer."""
    print(f"Found username: {settings.user_access.username}")
