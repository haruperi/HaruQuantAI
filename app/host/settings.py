"""Host settings retrieval, cached access and validated updates.

Description:
    HostSettings calls persistence.SettingsStore directly to retrieve and update
    host_settings records. A small internal wrapper provides scoped dot access
    such as settings.user_access.username and dictionary access. Construction is
    lazy; reads use a local cache, updates refresh it, and reload() observes other
    writers. Constructor overrides affect the in-memory view only; snapshots
    describe persisted values. Database handles, SQL, schemas and storage checks
    belong to persistence. HTTP REST projections belong in app.api.settings; this
    module provides pure business logic and persistence coordination. Filesystem
    inspection belongs to diagnostics. Session supplies the access dependency and
    owns authentication/provisioning. Configuration preferences include
    data_frame_guard (warn/stop/off) and cleanup_interval_mins (0 means never).
    These are validated storage contracts; engine execution and Java runtime
    effects belong to their capability owners. The catalogue maps nested
    application records to legacy dotted scopes and stores explicit saves only in
    existing application group JSON. Consolidation is an explicit backed-up
    operation, never a startup migration. Secret replacement is write-only;
    account password policy/routes stay in session. Do not add another store
    wrapper or filesystem probes here.

Purpose:
    FEAT-HOST-SETTINGS: Retrieve configuration and validate/update it through the
    single database authority, with convenient scoped access.

Key Capabilities:
    - FR-HOST-SETTINGS-LOAD: Load settings and rebuild the local access cache.
      Associated: `HostSettings.reload()`, `_cache_snapshot()`
      Logging: INFO counts/revision; WARNING unavailable initialization; ERROR
        incompatible/corrupt storage without payload values.
    - FR-HOST-SETTINGS-DOT-ACCESS: Retrieve scoped settings and nested values.
      Associated: `HostSettings._resolve()`, `_SettingsNode`
      Logging: DEBUG key access without setting values.
    - FR-HOST-SETTINGS-VALIDATION: Validate configuration before database writes.
      Associated: `validate_configuration_values()`, `HostSettings.update()`
      Logging: WARNING rejected configuration constraints.
    - FR-HOST-SETTINGS-CONSOLIDATION: Explicitly consolidate redundant settings.
      Associated: `consolidate_settings()`
      Logging: INFO dry-run/apply and affected row count, without values.
    - FR-HOST-SETTINGS-UPDATE: Delegate atomic changes and refresh cached values.
      Associated: `HostSettings.update()`
      Logging: INFO revision on completion; persistence logs writes/conflicts.

Python API Usage:
    ```python
    from app.host.settings import settings

    username = settings.user_access.username
    snapshot = settings.update(
        {"user_access": {"username": "user"}},
        expected_revision=settings.revision,
    )
    settings.reload()  # Observe updates made by another writer.
    ```

CLI Usage:
    Settings management is accessed through Python APIs and app.api REST routes:
    ```bash
    uv run python -m app.main
    ```
"""

from __future__ import annotations

import math
from collections.abc import Iterator
from pathlib import Path
from typing import Any, override

from pydantic import BaseModel

from app.host.logging import get_logger
from app.host.persistence import (
    CorruptDataError,
    IncompatibleSchemaError,
    PersistenceError,
    SettingRecord,
    ValidationError,
)
from app.host.persistence import SettingsStore as _SettingsStore

__all__ = [
    "HostSettings",
    "HostSettingsSnapshot",
    "settings",
    "validate_configuration_values",
]

logger = get_logger(__name__)

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

_MISSING = object()


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


def _validate_configuration_contract(scope: str, key: str, value: Any) -> None:
    """Check typed UI preference contracts without applying runtime policy."""
    boolean_keys: dict[str, tuple[str, ...]] = {
        "config.global": ("sounds_off", "advanced_file_chooser", "show_control_orders"),
        "config.cpu": ("high_priority", "thread_affinity"),
        "config.performance": (
            "compute_pips_metrics",
            "compute_pcts_metrics",
            "compute_separate_metrics",
        ),
        "config.memory": (
            "automatic_memory",
            "dont_store_pending_orders",
            "memory_cleanup",
        ),
        "config.databanks": ("sync_databanks_after_task_done", "store_chart_data"),
        "config.optimizations": ("dont_store_op_3d_charts_data",),
        "config.troubleshooting": (
            "gpu_accelerated",
            "memory_protection",
            "debug_level_active",
        ),
    }
    valid = True
    if key in boolean_keys.get(scope, ()):
        valid = isinstance(value, bool)
    elif (scope, key) == ("config.global", "data_frame_guard"):
        valid = isinstance(value, str) and value in ("warn", "stop", "off")
    elif (scope, key) == ("config.global", "default_result_to_display"):
        valid = isinstance(value, str) and value in ("Portfolio", "Main")
    elif (scope, key) == ("config.memory", "gc_type"):
        valid = isinstance(value, str) and value in ("ParallelGC", "G1GC", "Automatic")
    elif (scope, key) == ("config.memory", "cleanup_interval_mins"):
        valid = type(value) is int and value in (0, 5, 15, 30, 60)
    elif (scope, key) == ("config.databanks", "databank_sync_interval_mins"):
        valid = value is None or (type(value) is int and value in (0, 5, 10, 15, 60))
    if not valid:
        logger.warning(
            "FR-HOST-SETTINGS-VALIDATION: Rejected configuration contract.",
            extra={"scope": scope, "key": key, "fr_id": "FR-HOST-SETTINGS-VALIDATION"},
        )
        raise ValidationError(f"Unsupported value for {scope}.{key}")


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
    _validate_configuration_contract(scope, key, value)


class HostSettingsSnapshot(BaseModel):
    """Point-in-time snapshot of the entire host settings dictionary."""

    revision: int
    values: dict[str, dict[str, Any]]


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
    load, cache, structure, and provide default fallback configuration records
    across all defined scopes.
    """

    def __init__(
        self,
        db_path: Path | str | None = None,
        *,
        host: str | None = None,
        port: int | None = None,
        debug: bool | None = None,
        data_dir: Path | str | None = None,
        title: str | None = None,
        version: str | None = None,
        api_prefix: str | None = None,
        reference_cohort: str | None = None,
        timeout_graceful_shutdown: int | None = None,
        auto_load: bool = False,
    ) -> None:
        """Initialize HostSettings with optional database path and overrides.

        Args:
            db_path: Optional path to SQLite database. Defaults to repository store.
            host: Optional host IP override.
            port: Optional host port override.
            debug: Optional debug mode override.
            data_dir: Optional workspace runtime data directory override.
            title: Optional application title override.
            version: Optional application version override.
            api_prefix: Optional REST API route prefix override.
            reference_cohort: Optional reference cohort identifier override.
            timeout_graceful_shutdown: Optional graceful shutdown timeout
                override in seconds.
            auto_load: Whether to load settings immediately upon construction.
        """
        super().__init__()
        self._override_host: str | None = host
        self._override_port: int | None = port
        self._override_debug: bool | None = debug
        self._override_data_dir: Path | None = (
            Path(data_dir) if data_dir is not None else None
        )
        self._override_title: str | None = title
        self._override_version: str | None = version
        self._override_api_prefix: str | None = api_prefix
        self._override_reference_cohort: str | None = reference_cohort
        self._override_timeout_graceful_shutdown: int | None = (
            int(timeout_graceful_shutdown)
            if timeout_graceful_shutdown is not None
            else None
        )

        resolved_db: Path | None = None
        if db_path is not None:
            resolved_db = Path(db_path)
        elif self._override_data_dir is not None:
            resolved_db = self._override_data_dir / "database" / "haruquantai.db"
        self._store = _SettingsStore(db_path=resolved_db)
        self._revision: int = 1
        self._loaded: bool = False
        if auto_load:
            self.reload()

    @property
    def db_path(self) -> Path:
        """Return filesystem path to underlying SQLite database."""
        return self._store.db_path

    @property
    def revision(self) -> int:
        """Return current cached revision number."""
        self._ensure_loaded()
        return self._revision

    @property
    def host(self) -> str:
        """Return configured bind IP address."""
        if self._override_host is not None:
            return self._override_host
        self._ensure_loaded()
        raw = self.get("app_general")
        return str(raw.get("host", "127.0.0.1")) if hasattr(raw, "get") else "127.0.0.1"

    @property
    def port(self) -> int:
        """Return configured backend bind port number."""
        if self._override_port is not None:
            return self._override_port
        self._ensure_loaded()
        raw = self.get("app_general")
        return int(raw.get("backend_port", 8000)) if hasattr(raw, "get") else 8000

    @property
    def debug(self) -> bool:
        """Return True if debug diagnostics are active."""
        if self._override_debug is not None:
            return self._override_debug
        self._ensure_loaded()
        raw = self.get("config_troubleshooting")
        return (
            bool(raw.get("debug_level_active", False)) if hasattr(raw, "get") else False
        )

    @property
    def data_dir(self) -> Path | None:
        """Return configured workspace data directory."""
        if self._override_data_dir is not None:
            return self._override_data_dir
        self._ensure_loaded()
        raw = self.get("workspace_paths")
        path_str = raw.get("data_dir") if hasattr(raw, "get") else None
        return Path(path_str) if path_str is not None else None

    @property
    def api_prefix(self) -> str:
        """Return REST API route prefix."""
        if self._override_api_prefix is not None:
            return self._override_api_prefix
        self._ensure_loaded()
        raw = self.get("host_runtime")
        return (
            str(raw.get("api_prefix", "/api/v1")) if hasattr(raw, "get") else "/api/v1"
        )

    @property
    def title(self) -> str:
        """Return platform application title."""
        if self._override_title is not None:
            return self._override_title
        self._ensure_loaded()
        raw = self.get("host_runtime")
        return (
            str(raw.get("title", "HaruQuantAI Host"))
            if hasattr(raw, "get")
            else "HaruQuantAI Host"
        )

    @property
    def version(self) -> str:
        """Return platform application version."""
        if self._override_version is not None:
            return self._override_version
        self._ensure_loaded()
        raw = self.get("host_runtime")
        return str(raw.get("version", "2.1.0")) if hasattr(raw, "get") else "2.1.0"

    @property
    def reference_cohort(self) -> str:
        """Return platform reference cohort identifier."""
        if self._override_reference_cohort is not None:
            return self._override_reference_cohort
        self._ensure_loaded()
        raw = self.get("host_runtime")
        return (
            str(raw.get("reference_cohort", "SQX145 Dev 1"))
            if hasattr(raw, "get")
            else "SQX145 Dev 1"
        )

    @property
    def timeout_graceful_shutdown(self) -> int:
        """Return configured timeout in seconds for server graceful shutdown."""
        if self._override_timeout_graceful_shutdown is not None:
            return self._override_timeout_graceful_shutdown
        self._ensure_loaded()
        raw = self.get("app_general")
        try:
            val = (
                int(raw.get("timeout_graceful_shutdown", 2))
                if hasattr(raw, "get")
                else 2
            )
            return max(1, val)
        except ValueError, TypeError:
            return 2

    def _ensure_loaded(self) -> None:
        """Ensure settings are loaded from disk if not yet loaded."""
        if not self._loaded:
            self.reload()

    def _initialize_store(self) -> None:
        """Initialize storage, logging tolerated failures and surfacing corruption."""
        try:
            self._store.initialize()
        except IncompatibleSchemaError, CorruptDataError:
            logger.error(  # noqa: TRY400 - Do not log potentially secret exception text.
                "Settings storage is incompatible or corrupt",
                extra={"fr_id": "FR-HOST-SETTINGS-LOAD"},
            )
            raise
        except PersistenceError as exc:
            logger.warning(
                "Settings storage initialization unavailable",
                extra={
                    "error_type": type(exc).__name__,
                    "fr_id": "FR-HOST-SETTINGS-LOAD",
                },
            )

    def _apply_runtime_overrides(self, merged: dict[str, dict[str, Any]]) -> None:
        """Apply explicit constructor overrides onto loaded configuration dictionary."""
        if self._override_host is not None:
            merged.setdefault("app_general", {})["host"] = self._override_host
        if self._override_port is not None:
            merged.setdefault("app_general", {})["backend_port"] = self._override_port
        if self._override_debug is not None:
            merged.setdefault("config_troubleshooting", {})["debug_level_active"] = (
                self._override_debug
            )
        if self._override_data_dir is not None:
            merged.setdefault("workspace_paths", {})["data_dir"] = str(
                self._override_data_dir
            )
        if self._override_title is not None:
            merged.setdefault("host_runtime", {})["title"] = self._override_title
        if self._override_version is not None:
            merged.setdefault("host_runtime", {})["version"] = self._override_version
        if self._override_api_prefix is not None:
            merged.setdefault("host_runtime", {})["api_prefix"] = (
                self._override_api_prefix
            )
        if self._override_reference_cohort is not None:
            merged.setdefault("host_runtime", {})["reference_cohort"] = (
                self._override_reference_cohort
            )

    @staticmethod
    def _snapshot(revision: int, records: list[SettingRecord]) -> HostSettingsSnapshot:
        """Group persisted records without including runtime overrides."""
        values: dict[str, dict[str, Any]] = {}
        for record in records:
            values.setdefault(record.scope, {})[record.key] = record.value
        return HostSettingsSnapshot(revision=revision, values=values)

    def _cache_snapshot(self, snapshot: HostSettingsSnapshot) -> None:
        """Build the access cache and apply in-memory constructor overrides."""
        merged = effective_settings_values(snapshot.values)
        self._apply_runtime_overrides(merged)
        for scope, group in SETTINGS_GROUPS.items():
            if group in merged:
                merged[scope].update(merged[group])
        data: dict[str, Any] = {}
        total_keys = 0
        for scope, values in merged.items():
            scope_node = _SettingsNode(values)
            for key in values:
                value = scope_node[key]
                data[key.replace(".", "_")] = value
                data[key] = value
                total_keys += 1
            data[scope.replace(".", "_")] = scope_node
            data[scope] = scope_node
        self._raw = {}
        self._data = data
        self._revision = snapshot.revision
        self._loaded = True
        logger.info(
            "FR-HOST-SETTINGS-LOAD: Loaded %d records in %d scopes. Revision: %d",
            total_keys,
            len(merged),
            self._revision,
            extra={
                "count": total_keys,
                "revision": self._revision,
                "fr_id": "FR-HOST-SETTINGS-LOAD",
            },
        )

    def reload(self) -> None:
        """Reload persisted settings and rebuild the local access cache."""
        self._initialize_store()
        revision, records = self._store.read_all()
        self._cache_snapshot(self._snapshot(revision, records))

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
        for scope, values in changes.items():
            if not isinstance(values, dict):
                raise ValidationError(
                    f"Scope changes for '{scope}' must be a dictionary"
                )
            for key, value in values.items():
                validate_configuration_values(scope, key, value)
        self._ensure_loaded()
        current = self.get_snapshot()
        changes = _synchronized_changes(current.values, changes)
        if expected_revision is None:
            expected_revision = current.revision
        revision, records = self._store.update_batch(
            changes, expected_revision=expected_revision
        )
        snapshot = self._snapshot(revision, records)
        self._cache_snapshot(snapshot)
        logger.info(
            "Host settings update completed",
            extra={"revision": revision, "fr_id": "FR-HOST-SETTINGS-UPDATE"},
        )
        return snapshot

    def get_snapshot(self) -> HostSettingsSnapshot:
        """Read a persisted snapshot without in-memory runtime overrides."""
        self._ensure_loaded()
        revision, records = self._store.read_all()
        return self._snapshot(revision, records)

    @override
    def __iter__(self) -> Iterator[str]:
        """Load settings before iterating cached keys."""
        self._ensure_loaded()
        return super().__iter__()

    @override
    def __len__(self) -> int:
        """Load settings before counting cached keys."""
        self._ensure_loaded()
        return super().__len__()

    def __bool__(self) -> bool:
        """Keep an explicit settings instance selectable without loading storage."""
        return True

    @override
    def as_dict(self) -> dict[str, Any]:
        """Load settings before returning their dictionary representation."""
        self._ensure_loaded()
        return super().as_dict()

    @override
    def __repr__(self) -> str:
        """Return developer representation of HostSettings."""
        return (
            f"HostSettings(db_path={self.db_path!r}, revision={self._revision}, "
            f"loaded_keys={len(self._data)})"
        )


# Convenient global singleton; construction performs no database I/O.
settings = HostSettings()


SETTINGS_FIELDS: dict[str, dict[str, str]] = {
    "app_general": {
        "theme": "str",
        "language": "str",
        "auto_save_interval_s": "int",
        "header_custom_text": "str",
        "confirm_on_exit": "bool",
        "host": "str",
        "backend_port": "int",
        "frontend_port": "int",
        "gpu_accelerated": "bool",
        "zoom": "int",
    },
    "calibration_indicators": {
        "QQE.RSIPeriod": "list",
        "QQE.sF": "list",
        "QQE.Value1": "str",
    },
    "config_agents": {
        "active_provider": "str",
        "gemini.api_key": "str",
        "gemini.use_vertex_ai": "bool",
        "gemini.model": "str",
        "gemini.fast_model": "str",
        "gemini.premium_model": "str",
        "gemini.fallback_model": "str",
        "gemini.temperature": "float",
        "gemini.max_tokens": "int",
        "openai.api_key": "str",
        "openai.base_url": "str",
        "openai.model": "str",
        "openai.temperature": "float",
        "openai.max_tokens": "int",
        "ollama.base_url": "str",
        "ollama.model": "str",
        "ollama.temperature": "float",
        "ollama.timeout_seconds": "int",
        "system_prompt_preset": "str",
        "agent_timeout_seconds": "int",
    },
    "config_cpu": {"core_usage": "str", "custom_cores": "int", "high_priority": "bool"},
    "config_ctrader": {
        "enabled": "bool",
        "client_id": "str",
        "client_secret": "str",
        "access_token": "str",
        "refresh_token": "str",
        "redirect_url": "str",
        "environment": "str",
        "account_id": "str",
        "gateway_host": "str",
        "gateway_port": "int",
    },
    "config_databanks": {
        "databank_sync_interval_mins": "int",
        "store_chart_data": "bool",
        "sync_databanks_after_task_done": "bool",
    },
    "config_global": {
        "advanced_file_chooser": "bool",
        "default_result_to_display": "str",
        "footer_custom_text": "str",
        "show_control_orders": "bool",
        "sounds_off": "bool",
    },
    "config_memory": {
        "automatic_memory": "bool",
        "cleanup_interval_mins": "int",
        "dont_store_pending_orders": "bool",
        "gc_type": "str",
        "memory_cleanup": "bool",
        "memory_limit_gb": "int",
    },
    "config_metatrader5": {
        "enabled": "bool",
        "terminal_path": "str",
        "account_id": "int",
        "password": "str",
        "server": "str",
        "environment": "str",
        "timeout_ms": "int",
        "portable": "bool",
        "use_ticks": "bool",
    },
    "config_optimizations": {"dont_store_op_3d_charts_data": "bool"},
    "config_performance": {
        "compute_pcts_metrics": "bool",
        "compute_pips_metrics": "bool",
        "compute_separate_metrics": "bool",
    },
    "config_troubleshooting": {
        "debug_level_active": "bool",
        "gpu_accelerated": "bool",
        "memory_protection": "bool",
    },
    "connect_mcp": {
        "enabled": "bool",
        "host": "str",
        "port": "int",
        "transport": "str",
        "auth_token": "str",
        "allowed_tools": "list",
        "max_context_items": "int",
    },
    "engine_backtest": {
        "max_threads": "int",
        "memory_limit_mb": "int",
        "enable_caching": "bool",
        "precision_mode": "str",
        "benchmark_time_per_tick_ms": "float",
        "dont_store_pending_orders": "bool",
        "dont_store_op3d_charts": "bool",
        "compute_separate_metrics": "bool",
        "compute_pcts_metrics": "bool",
        "compute_pips_metrics": "bool",
        "source_code_constants_params": "bool",
    },
    "notify_desktop": {
        "enabled": "bool",
        "sound_enabled": "bool",
        "duration_seconds": "int",
        "min_priority": "str",
    },
    "notify_email": {
        "enabled": "bool",
        "smtp_server": "str",
        "smtp_port": "int",
        "use_ssl": "bool",
        "use_tls": "bool",
        "username": "str",
        "password": "str",
        "from_address": "str",
        "recipient_addresses": "list",
    },
    "notify_telegram": {
        "enabled": "bool",
        "bot_token": "str",
        "chat_id": "str",
        "parse_mode": "str",
        "disable_notification": "bool",
    },
    "user_access": {
        "username": "str",
        "password_hash": "str",
        "password_salt": "str",
        "require_auth": "bool",
        "session_timeout_mins": "int",
        "allow_remember_me": "bool",
    },
    "workspace_paths": {
        "configs_dir": "str",
        "projects_dir": "str",
        "strategies_dir": "str",
        "data_dir": "str",
    },
}
SETTINGS_FIELDS["config_global"]["data_frame_guard"] = "str"
SETTINGS_FIELDS["config_cpu"]["thread_affinity"] = "bool"
SETTINGS_FIELDS["app_general"]["zoom"] = "float"
SETTINGS_FIELDS["config_memory"]["memory_limit_gb"] = "float"
SETTINGS_FIELDS["connect_remote"] = {"allow": "bool", "require_password": "bool"}
SETTINGS_GROUPS: dict[str, str] = {
    "app.general": "app_general",
    "config.global": "config_global",
    "config.cpu": "config_cpu",
    "config.performance": "config_performance",
    "config.memory": "config_memory",
    "config.databanks": "config_databanks",
    "config.optimizations": "config_optimizations",
    "config.troubleshooting": "config_troubleshooting",
    "config.metatrader5": "config_metatrader5",
    "config.ctrader": "config_ctrader",
    "config.agents": "config_agents",
    "notify.desktop": "notify_desktop",
    "notify.email": "notify_email",
    "notify.telegram": "notify_telegram",
    "connect.mcp": "connect_mcp",
    "connect.remote": "connect_remote",
    "engine.backtest": "engine_backtest",
    "workspace.paths": "workspace_paths",
    "calibration.indicators": "calibration_indicators",
}
_READ_ONLY_FIELDS: set[tuple[str, str]] = {("app_general", "language")}
_FIELD_DEFAULTS: dict[str, Any] = {
    "theme": "dark",
    "language": "en",
    "zoom": 1,
    "core_usage": "all_except_one",
    "custom_cores": 1,
    "memory_limit_gb": 10,
    "gc_type": "ParallelGC",
    "cleanup_interval_mins": 15,
    "databank_sync_interval_mins": 15,
    "default_result_to_display": "Portfolio",
    "data_frame_guard": "warn",
    "compute_separate_metrics": True,
    "dont_store_pending_orders": True,
    "dont_store_op_3d_charts_data": True,
    "gpu_accelerated": True,
    "memory_protection": True,
    "smtp_port": 587,
    "use_tls": True,
    "backend_port": 8000,
    "frontend_port": 3000,
    "port": 8001,
    "gateway_port": 5035,
    "timeout_ms": 60000,
    "environment": "demo",
    "duration_seconds": 5,
    "min_priority": "info",
    "parse_mode": "HTML",
    "session_timeout_mins": 1440,
    "agent_timeout_seconds": 60,
    "timeout_seconds": 60,
    "max_tokens": 4096,
    "max_threads": 1,
    "memory_limit_mb": 1024,
    "auto_save_interval_s": 60,
    "max_context_items": 100,
    "precision_mode": "normal",
    "transport": "stdio",
    "temperature": 0.7,
    "active_provider": "openai",
    "QQE.RSIPeriod": [14],
    "QQE.sF": [5],
    "require_auth": True,
    "allow_remember_me": True,
}
_FIELD_OPTIONS: dict[str, list[str]] = {
    "theme": ["dark", "light"],
    "core_usage": ["single", "all_except_one", "custom", "all"],
    "gc_type": ["ParallelGC", "G1GC", "Automatic"],
    "default_result_to_display": ["Portfolio", "Main"],
    "data_frame_guard": ["warn", "stop", "off"],
    "environment": ["demo", "live"],
    "active_provider": ["gemini", "openai", "ollama"],
    "min_priority": ["normal", "debug", "info", "warning", "error", "critical"],
    "parse_mode": ["", "HTML", "Markdown", "MarkdownV2"],
    "transport": ["stdio", "sse", "http"],
}


def _is_secret(field: str) -> bool:
    """Identify secret/verifier leaves without reading or displaying their values."""
    return field.rsplit(".", maxsplit=1)[-1] in {
        "password",
        "password_hash",
        "password_salt",
        "client_secret",
        "access_token",
        "refresh_token",
        "auth_token",
        "bot_token",
        "api_key",
    }


def _field_value(row: dict[str, Any], field: str, default: Any) -> Any:
    """Resolve nested provider leaves, preserving literal dotted indicator keys."""
    if field in row:
        return row[field]
    node: Any = row
    for key in field.split("."):
        if not isinstance(node, dict) or key not in node:
            return default
        node = node[key]
    return node


def _set_field(row: dict[str, Any], field: str, value: Any) -> None:
    """Merge a catalogue leaf without replacing sibling settings or secrets."""
    if field.startswith("QQE."):
        row[field] = value
        return
    parts = field.split(".")
    node = row
    for key in parts[:-1]:
        existing = node.get(key)
        node[key] = dict(existing) if isinstance(existing, dict) else {}
        node = node[key]
    node[parts[-1]] = value


def effective_settings_values(
    values: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Expose in-memory aliases backed only by canonical application JSON rows."""
    merged = {scope: dict(row) for scope, row in values.items()}
    application = values.get("application", {})
    for scope, group in SETTINGS_GROUPS.items():
        base = (
            application.get("app_general", {}).get("remote_access", {})
            if group == "connect_remote"
            else application.get(group, {})
        )
        row = dict(base) if isinstance(base, dict) else {}
        merged[scope] = row
        merged[group] = row
    merged["user_access"] = dict(application.get("user_access", {}))
    return merged


def _merge_fields(base: dict[str, Any], fields: dict[str, Any]) -> dict[str, Any]:
    """Merge explicit JSON leaves without discarding untouched nested siblings."""
    result = dict(base)
    for field, value in fields.items():
        if isinstance(value, dict) and isinstance(result.get(field), dict):
            result[field] = _merge_fields(result[field], value)
        else:
            _set_field(result, field, value)
    return result


def _canonical_aliases(changes: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Route old header aliases to the canonical general JSON field."""
    result = {scope: dict(fields) for scope, fields in changes.items()}
    for scope in ("config.global", "config_global"):
        fields = result.get(scope, {})
        if "header_custom_text" in fields:
            header = fields.pop("header_custom_text")
            result.setdefault("app.general", {}).setdefault(
                "header_custom_text", header
            )
            if not fields:
                del result[scope]
    return result


def _synchronized_changes(
    values: dict[str, dict[str, Any]], changes: dict[str, dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    """Translate aliases into updates of existing group JSON, without mirrors."""
    changes = _canonical_aliases(changes)
    application = values.get("application", {})
    result: dict[str, dict[str, Any]] = {}
    groups = set(SETTINGS_GROUPS.values()) | {"user_access"}
    for scope, fields in changes.items():
        group = SETTINGS_GROUPS.get(scope, scope if scope in groups else None)
        if scope == "application":
            for name, payload in fields.items():
                if not isinstance(payload, dict):
                    raise ValidationError("Application group must be a JSON object.")
                prior = result.setdefault("application", {}).get(
                    name, application.get(name, {})
                )
                result["application"][name] = _merge_fields(prior, payload)
            continue
        if group is None:
            result[scope] = dict(fields)
            continue
        destination = "app_general" if group == "connect_remote" else group
        if application and destination not in application and group != "user_access":
            raise ValidationError("Canonical settings group is unavailable.")
        prior = result.setdefault("application", {}).get(
            destination, application.get(destination, {})
        )
        payload = {"remote_access": fields} if group == "connect_remote" else fields
        result["application"][destination] = _merge_fields(prior, payload)
    return result


def consolidate_settings(
    target: HostSettings,
    *,
    apply: bool = False,
    allowed_deletions: tuple[tuple[str, str], ...] | None = None,
) -> dict[str, Any]:
    """Explicitly consolidate duplicate rows; dry-run returns names/counts only."""
    snapshot = target.get_snapshot()
    values = snapshot.values
    application = values.get("application", {})
    changes: dict[str, Any] = {}
    deletions: list[tuple[str, str]] = []
    for scope, group in SETTINGS_GROUPS.items():
        for field, value in values.get(scope, {}).items():
            if field not in SETTINGS_FIELDS[group] and not (
                scope == "config.global" and field == "header_custom_text"
            ):
                continue
            destination = (
                "app_general"
                if group == "connect_remote" or field == "header_custom_text"
                else group
            )
            if destination not in application:
                raise ValidationError("Consolidation destination is unavailable.")
            row = changes.get(destination, application[destination])
            payload = (
                {"remote_access": {field: value}}
                if group == "connect_remote"
                else {field: value}
            )
            changes[destination] = _merge_fields(row, payload)
            deletions.append((scope, field))
    _consolidate_account(values, application, changes, deletions)
    global_row = dict(
        changes.get("config_global", application.get("config_global", {}))
    )
    if "header_custom_text" in global_row:
        app_row = dict(changes.get("app_general", application.get("app_general", {})))
        if "app_general" not in application:
            raise ValidationError("Canonical general settings are unavailable.")
        app_row.setdefault("header_custom_text", global_row.pop("header_custom_text"))
        changes["app_general"] = app_row
        changes["config_global"] = global_row
    if allowed_deletions is not None and set(deletions) != set(allowed_deletions):
        raise ValidationError("Consolidation row targets differ from approval.")
    report: dict[str, Any] = {
        "revision": snapshot.revision,
        "updated_groups": sorted(changes),
        "deleted_rows": [
            {"scope": scope, "key": key} for scope, key in sorted(deletions)
        ],
        "applied": False,
    }
    if apply and (changes or deletions):
        revision, _ = _SettingsStore(target.db_path).update_batch(
            {"application": changes},
            deletions=tuple(deletions),
            expected_revision=snapshot.revision,
        )
        target.reload()
        report.update(revision=revision, applied=True)
    logger.info(
        "Settings consolidation inspected%s",
        " and applied" if report["applied"] else "",
        extra={"fr_id": "FR-HOST-SETTINGS-UPDATE", "row_count": len(deletions)},
    )
    return report


def _consolidate_account(
    values: dict[str, dict[str, Any]],
    application: dict[str, Any],
    changes: dict[str, Any],
    deletions: list[tuple[str, str]],
) -> None:
    """Preserve the working credentials or abort before any consolidation writes."""
    from app.host.session import password_verifier_salt

    account = values.get("user_access", {})
    if account:
        if (
            set(account) != {"username", "password_hash"}
            or not isinstance(account.get("username"), str)
            or not account["username"].strip()
        ):
            raise ValidationError("Incomplete account consolidation source.")
        try:
            salt = password_verifier_salt(account["password_hash"])
        except ValueError, TypeError, AttributeError:
            raise ValidationError("Unsupported account verifier.") from None
        if "user_access" not in application:
            raise ValidationError("Canonical account destination is unavailable.")
        changes["user_access"] = _merge_fields(
            application["user_access"], {**account, "password_salt": salt}
        )
        deletions.extend(("user_access", key) for key in account)


def _default_field(field: str, kind: str) -> Any:
    """Return explicit UI defaults for absent catalogue leaves only."""
    leaf = field.rsplit(".", maxsplit=1)[-1]
    if field in _FIELD_DEFAULTS:
        return _FIELD_DEFAULTS[field]
    if leaf in _FIELD_DEFAULTS:
        return _FIELD_DEFAULTS[leaf]
    empty_list: list[Any] = []
    defaults: dict[str, Any] = {
        "bool": False,
        "int": 0,
        "float": 0.0,
        "str": "",
        "list": empty_list,
    }
    return defaults[kind]


MAX_SETTING_STRING = 4096
MAX_SETTING_LIST = 256
MAX_LIST_STRING = 1024
MAX_SETTING_NUMBER = 1_000_000_000
MAX_TEMPERATURE = 2


def _valid_field_type(field: str, kind: str | None, value: Any) -> bool:
    """Check bounded primitive/list types without coercing unknown values."""
    if kind == "bool":
        return isinstance(value, bool)
    if kind == "int":
        return type(value) is int or (
            field == "databank_sync_interval_mins" and value is None
        )
    if kind == "float":
        return type(value) in (int, float) and math.isfinite(value)
    if kind == "str":
        return isinstance(value, str) and len(value) <= MAX_SETTING_STRING
    if kind != "list" or not isinstance(value, list) or len(value) > MAX_SETTING_LIST:
        return False
    return all(
        (type(item) in (int, float) and math.isfinite(item))
        if field.startswith("QQE.")
        else (isinstance(item, str) and len(item) <= MAX_LIST_STRING)
        for item in value
    )


def _valid_number_range(field: str, kind: str | None, value: Any) -> bool:
    """Check catalogue numeric limits following successful type validation."""
    if kind not in ("int", "float") or value is None:
        return True
    if not 0 <= value <= MAX_SETTING_NUMBER:
        return False
    if field.endswith("port"):
        return bool(MIN_PORT <= value <= MAX_PORT)
    if field.rsplit(".", maxsplit=1)[-1] in (
        "duration_seconds",
        "timeout_ms",
        "agent_timeout_seconds",
        "timeout_seconds",
        "max_tokens",
        "max_threads",
        "max_context_items",
    ):
        return bool(value >= 1)
    if field.endswith("temperature"):
        return bool(value <= MAX_TEMPERATURE)
    return True


def _validate_catalogue_field(
    group: str, field: str, value: Any, *, secrets: bool
) -> None:
    """Reject unknown/protected leaves and unsupported values without secret logs."""
    kind = SETTINGS_FIELDS.get(group, {}).get(field)
    options = _FIELD_OPTIONS.get(field)
    valid = (
        kind is not None
        and (group, field) not in _READ_ONLY_FIELDS
        and _is_secret(field) == secrets
        and group != "user_access"
        and _valid_field_type(field, kind, value)
        and _valid_number_range(field, kind, value)
        and (not options or value in options)
    )
    if not valid:
        logger.warning(
            "Settings catalogue validation rejected",
            extra={"fr_id": "FR-HOST-SETTINGS-VALIDATION"},
        )
        raise ValidationError("Unsupported or protected settings field/value.")
    scope = next(
        (scope for scope, name in SETTINGS_GROUPS.items() if name == group), group
    )
    validate_configuration_values(scope, field, value)


def _leaf_field_names(row: dict[str, Any], prefix: str = "") -> Iterator[str]:
    """Enumerate field names only; never project unknown values."""
    for key, value in row.items():
        name = prefix + key
        if isinstance(value, dict):
            yield from _leaf_field_names(value, name + ".")
        else:
            yield name


def _unknown_settings_metadata(
    values: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Cover unsupported rows and extra nested leaves with safe read-only metadata."""
    unknown: list[dict[str, Any]] = []
    for scope, row in values.items():
        group = SETTINGS_GROUPS.get(scope, scope)
        if scope == "application":
            for name, value in row.items():
                schema = SETTINGS_FIELDS.get(name)
                keys: list[str] = []
                if isinstance(value, dict):
                    keys = list(_leaf_field_names(value))
                extras = [
                    key
                    for key in keys
                    if (schema is None or key not in schema)
                    and not (
                        name == "app_general"
                        and key.startswith("remote_access.")
                        and key.split(".", 1)[1] in SETTINGS_FIELDS["connect_remote"]
                    )
                ]
                if schema is None and not extras:
                    extras = [""]
                unknown.extend(
                    {
                        "scope": "application",
                        "key": name + ("." + key if key else ""),
                        "reason": "Unsupported metadata; value withheld.",
                    }
                    for key in extras
                )
        elif group in SETTINGS_FIELDS:
            unknown.extend(
                {
                    "scope": scope,
                    "key": key,
                    "reason": "Unsupported metadata; value withheld.",
                }
                for key in _leaf_field_names(row)
                if key not in SETTINGS_FIELDS[group]
            )
        elif scope not in ("user_access", "host"):
            unknown.extend(
                {
                    "scope": scope,
                    "key": key,
                    "reason": "Unsupported metadata; value withheld.",
                }
                for key in row
            )
    return unknown


def settings_catalogue(snapshot: HostSettingsSnapshot) -> dict[str, Any]:
    """Project a complete field inventory with values or secret-presence metadata."""
    effective = effective_settings_values(snapshot.values)
    fields: list[dict[str, Any]] = []
    for scope, group in SETTINGS_GROUPS.items():
        row = effective.get(scope, {})
        for field, kind in SETTINGS_FIELDS[group].items():
            value = _field_value(row, field, _default_field(field, kind))
            secret = _is_secret(field)
            entry: dict[str, Any] = {
                "scope": scope,
                "group": group,
                "key": field,
                "kind": kind,
                "label": field.replace("_", " ").replace(".", " / ").capitalize(),
                "secret": secret,
                "readonly": (group, field) in _READ_ONLY_FIELDS,
                "options": _FIELD_OPTIONS.get(field, []),
                "effect": "Saved preference; runtime effects depend on its capability.",
            }
            if secret:
                entry["configured"] = bool(value)
            else:
                entry["value"] = value
            fields.append(entry)
    application = snapshot.values.get("application", {})
    for field, kind in SETTINGS_FIELDS["user_access"].items():
        legacy = application.get("user_access", {})
        fields.append(
            {
                "scope": "application",
                "group": "user_access",
                "key": field,
                "kind": kind,
                "label": field.replace("_", " "),
                "secret": _is_secret(field),
                "readonly": True,
                "effect": "Account metadata; use the session-owned User access form.",
                **(
                    {"configured": bool(_field_value(legacy, field, ""))}
                    if _is_secret(field)
                    else {
                        "value": _field_value(
                            legacy, field, _default_field(field, kind)
                        )
                    }
                ),
            }
        )
    fields.append(
        {
            "scope": "host",
            "group": "runtime",
            "key": "__revision__",
            "kind": "int",
            "label": "Settings revision",
            "value": snapshot.revision,
            "readonly": True,
            "secret": False,
        }
    )
    unknown = _unknown_settings_metadata(snapshot.values)
    logger.debug(
        "Settings catalogue projected", extra={"fr_id": "FR-HOST-SETTINGS-LOAD"}
    )
    return {"revision": snapshot.revision, "fields": fields, "unknown": unknown}
