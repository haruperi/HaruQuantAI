"""Host configuration settings manager and dot-accessible configuration interface.

Description:
    Provides the central configuration settings container, dot-accessible access
    interface, validation engine, and settings management for HaruQuantAI host
    operations. All persistent database operations, schemas, and transactions are
    delegated exclusively to the central host persistence authority
    (app.host.persistence.SettingsStore). This module maintains zero direct SQLite
    connections, ensuring single-source-of-truth database management across the
    platform. Exposes a module-level `settings` singleton with lazy-loading
    semantics (zero disk I/O at import time) and a FastAPI REST projection router
    providing `/settings` inspection and atomic modification.

Purpose:
    FEAT-HOST-SETTINGS: Host configuration settings management, schema validation,
    authoritative persistence delegation, and dot-accessible navigation.

Key Capabilities:
    - FR-HOST-SETTINGS-SCHEMA: Host settings table schema constraint verification
      delegated to host persistence authority.
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
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any, override

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from app.host.logging import get_logger
from app.host.persistence import (
    DEFAULT_DATABASE_PATH,
    CorruptDataError,
    HostSettingsSnapshot,
    IncompatibleSchemaError,
    PersistenceError,
    RevisionConflictError,
    SettingRecord,
    SettingsPage,
    StorageBusyError,
    ValidationError,
    canonical_json,
    validate_identifier,
)
from app.host.persistence import (
    SettingsStore as _PersistenceSettingsStore,
)

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
    "canonical_json",
    "create_settings_router",
    "settings",
    "validate_configuration_values",
    "validate_identifier",
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

_MISSING = object()


class SettingsUpdateRequest(BaseModel):
    """Request envelope for updating host settings with optimistic locking."""

    model_config = ConfigDict(extra="forbid")

    expected_revision: int = Field(
        ..., ge=0, description="Expected settings revision before write"
    )
    changes: dict[str, dict[str, Any]] = Field(
        ..., description="Scoped changes mapping: scope -> {key: value}"
    )


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


class SettingsStore(_PersistenceSettingsStore):
    """Authoritative host settings persistence store delegating to app.host.persistence.

    Maintains 100% backward compatibility for existing callers and test suites while
    ensuring that all SQLite connections and transactions are exclusively managed by
    the host persistence engine.
    """

    def __init__(
        self,
        db_path: Path | str | None = None,
        *,
        busy_timeout: float = BUSY_TIMEOUT_SECONDS,
        validator: Callable[[str, str, Any], None] | None = None,
    ) -> None:
        """Initialize SettingsStore delegating to app.host.persistence.

        Args:
            db_path: Optional path to the SQLite database file or ':memory:'.
            busy_timeout: Timeout in seconds for SQLite lock waits.
            validator: Optional callback validating setting value constraints.
        """
        super().__init__(
            db_path=db_path,
            busy_timeout=busy_timeout,
            validator=validator or validate_configuration_values,
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
            except PersistenceError as exc:
                logger.warning(
                    "FR-HOST-SETTINGS-LOAD: Database initialization skipped (%s)",
                    exc,
                    extra={"fr_id": "FR-HOST-SETTINGS-LOAD"},
                )
        else:
            with contextlib.suppress(PersistenceError):
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
