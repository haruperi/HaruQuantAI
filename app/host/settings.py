"""Host settings retrieval, cached access and validated updates.

Description:
    HostSettings calls persistence.SettingsStore directly to retrieve and update
    host_settings records. A small internal wrapper provides scoped dot access
    such as settings.user_access.username and dictionary access. Construction is
    lazy; reads use a local cache, updates refresh it, and reload() observes other
    writers. Constructor overrides affect the in-memory view only; snapshots
    describe persisted values. Database handles, SQL, schemas and storage checks
    belong to persistence. Settings HTTP access belongs here because it serves
    the same retrieval/update capability; filesystem inspection belongs to
    diagnostics. Do not add another store wrapper or filesystem probes here.

Purpose:
    FEAT-HOST-SETTINGS: Retrieve configuration and validate/update it through the
    single database authority, with convenient scoped access.

Key Capabilities:
    - FR-HOST-SETTINGS-PROJECTION: Expose settings reads and updates over HTTP.
      Associated: `create_settings_router()`
      Logging: DEBUG reads; INFO updates; delegated validation logs failures.
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
    Settings HTTP inspection is composed by bootstrap; this module has no CLI:
    ```bash
    uv run python -m app.main
    ```
"""

from __future__ import annotations

import json
import math
from collections.abc import Iterator
from pathlib import Path
from typing import Any, override

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.host.logging import get_logger
from app.host.persistence import (
    CorruptDataError,
    IncompatibleSchemaError,
    PersistenceError,
    RevisionConflictError,
    SettingRecord,
    ValidationError,
)
from app.host.persistence import SettingsStore as _SettingsStore

__all__ = [
    "HostSettings",
    "HostSettingsSnapshot",
    "create_settings_router",
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
        merged = {scope: dict(values) for scope, values in snapshot.values.items()}
        self._apply_runtime_overrides(merged)
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
    target_settings = settings_instance if settings_instance is not None else settings

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

    return router
