"""Host configuration settings manager and dot-accessible access interface.

Description:
    Provides the central configuration settings container and dot-accessible
    interface for HaruQuantAI host operations. Wraps the authoritative SQLite
    persistence store (`SettingsStore`) to query, parse, and structure scoped
    application and host configuration records into memory. Exposes a module-level
    `settings` singleton allowing application modules, diagnostic utilities, and
    user entrypoints to navigate configuration values cleanly via dot-access
    (e.g., `settings.app_general.theme` or `settings.user_access.username`) or
    dictionary indexing, without direct coupling to low-level persistence tables.

Purpose:
    FEAT-HOST-SETTINGS: Host configuration settings management and dot-accessible
    access.

Key Capabilities:
    - FR-HOST-SETTINGS-LOAD: Query and parse scoped configuration records into memory.
      Associated: `HostSettings.reload()`, `HostSettings.__init__()`
      Logging: Emits INFO upon loading settings from database with count of items.
    - FR-HOST-SETTINGS-DOT-ACCESS: Provide recursive dot and dict attribute navigation.
      Associated: `_SettingsNode.__getattr__()`, `HostSettings.__getattr__()`
      Logging: Emits DEBUG when accessing setting attributes or namespaces.

Python API Usage:
    ```python
    from app.host.settings import settings

    # Access top-level normalized setting
    general = settings.app_general
    theme = settings.app_general.theme

    # Access nested configuration values
    gemini_model = settings.config_agents.gemini.model

    # Dict-style access and get with default
    port = settings.get("bound_port", 8080)
    ```

CLI Usage:
    Inspect and verify settings via the diagnostic CLI:
    ```bash
    uv run python -m app.cli
    ```
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from pathlib import Path
from typing import Any, override

from app.host.logging import get_logger
from app.host.persistance import SettingsStore

__all__ = ["HostSettings", "settings"]

logger = get_logger(__name__)

_MISSING = object()


class _SettingsNode:
    """Recursive wrapper providing dot-attribute and dictionary-style access.

    Converts dictionary keys containing dots (e.g. `QQE.RSIPeriod`) into valid
    Python attribute identifiers (`QQE_RSIPeriod`) while retaining exact key
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
        """Resolve value by key or normalized identifier.

        Args:
            name: Key or attribute identifier.

        Returns:
            Matched value if present, otherwise `_MISSING`.
        """
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
        """Retrieve setting attribute via dot-notation.

        Args:
            name: Attribute name.

        Returns:
            Wrapped setting value.

        Raises:
            AttributeError: If attribute does not exist.
        """
        if name.startswith("_"):
            return super().__getattribute__(name)
        val = self._resolve(name)
        if val is not _MISSING:
            return val
        raise self._attribute_not_found(name)

    def __getitem__(self, name: str) -> Any:
        """Retrieve setting value via dictionary indexing.

        Args:
            name: Key identifier.

        Returns:
            Wrapped setting value.

        Raises:
            KeyError: If key is not found.
        """
        val = self._resolve(name)
        if val is not _MISSING:
            return val
        raise self._key_not_found(name)

    def get(self, name: str, default: Any = None) -> Any:
        """Retrieve setting value with fallback default.

        Args:
            name: Key or attribute identifier.
            default: Fallback value if identifier is absent.

        Returns:
            Matched value or default.
        """
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
        if auto_load:
            self.reload()

    @property
    def db_path(self) -> Path:
        """Return filesystem path to underlying SQLite database."""
        return self._store.db_path

    def _discover_scopes(self) -> list[str]:
        """Discover distinct scopes present in host_settings table.

        Returns:
            List of scope strings.
        """
        if not self._store.db_path.exists():
            return []
        conn: sqlite3.Connection | None = None
        try:
            conn = sqlite3.connect(
                f"file:{self._store.db_path}?mode=ro",
                uri=True,
                timeout=5.0,
                autocommit=True,
            )
            cursor = conn.execute(
                "SELECT DISTINCT scope FROM host_settings ORDER BY scope"
            )
            return [str(row[0]) for row in cursor.fetchall()]
        except sqlite3.OperationalError:
            return ["application", "host"]
        finally:
            if conn is not None:
                conn.close()

    def reload(self) -> None:
        """Query host database and reload all scoped settings into memory."""
        self._data.clear()
        self._raw.clear()
        self._scopes.clear()

        if not self._store.db_path.exists():
            logger.info(
                "Host database absent at %s; settings initialized empty",
                self._store.db_path,
                extra={"requirement": "FR-HOST-SETTINGS-LOAD", "count": 0},
            )
            return

        scopes = self._discover_scopes()
        loaded_count = 0

        for scope in scopes:
            page = self._store.read_settings(scope=scope, limit=1000)
            scope_dict: dict[str, Any] = {}
            for record in page.items:
                wrapped = self.wrap(record.value)
                clean_key = record.key.replace(".", "_")

                # Populate top-level data
                self._data[clean_key] = wrapped
                if clean_key != record.key:
                    self._data[record.key] = wrapped

                # Populate scope container
                scope_dict[clean_key] = wrapped
                if clean_key != record.key:
                    scope_dict[record.key] = wrapped

                loaded_count += 1

            scope_node = _SettingsNode(scope_dict)
            clean_scope = scope.replace(".", "_")
            self._scopes[clean_scope] = scope_node
            if clean_scope != scope:
                self._scopes[scope] = scope_node

        logger.info(
            "Loaded %d host settings from database",
            loaded_count,
            extra={
                "scopes": list(self._scopes.keys()),
                "count": loaded_count,
                "requirement": "FR-HOST-SETTINGS-LOAD",
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
        val = super()._resolve(name)
        if val is not _MISSING:
            logger.debug(
                "Accessed setting attribute '%s'",
                name,
                extra={"key": name, "requirement": "FR-HOST-SETTINGS-DOT-ACCESS"},
            )
            return val

        if name in self._scopes:
            logger.debug(
                "Accessed scope namespace '%s'",
                name,
                extra={"scope": name, "requirement": "FR-HOST-SETTINGS-DOT-ACCESS"},
            )
            return self._scopes[name]

        clean_name = name.replace(".", "_")
        if clean_name in self._scopes:
            logger.debug(
                "Accessed scope namespace '%s'",
                clean_name,
                extra={
                    "scope": clean_name,
                    "requirement": "FR-HOST-SETTINGS-DOT-ACCESS",
                },
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
        return list(self._data.items())

    def update(self, scope: str, values: dict[str, Any]) -> None:
        """Update settings in the persistence store and reload into memory.

        Args:
            scope: Scoped namespace identifier.
            values: Mapping of keys to serializable values.
        """
        self._store.update_settings(scope, values)
        self.reload()

    @override
    def __repr__(self) -> str:
        """Return developer representation of HostSettings."""
        return f"HostSettings(db_path={self.db_path!r}, loaded_keys={len(self._data)})"


# Export convenient global singleton
settings = HostSettings()
