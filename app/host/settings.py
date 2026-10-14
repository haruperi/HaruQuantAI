# ruff: noqa: INP001
"""Host settings reader, revision tracker, and atomic batch configuration manager.

Description:
    Reads and updates operational and application settings in the database
    through the persistence layer (app.host.persistence.read and
    app.host.persistence.update) and packages them into an accessible container
    for the rest of the host platform and workspaces. Supports atomic batch
    updates with optimistic revision conflict checking. Exports a single lazy
    settings instance.

Purpose:
    FEAT-HOST-SETTINGS: Host settings reader and configuration packaging.

Key Capabilities:
    - FR-HOST-SETTINGS-LOAD: Read settings from database and package for app.
      Associated: `settings`
      Logging: INFO on settings load with scope count; DEBUG on setting access.
    - FR-HOST-SETTINGS-BATCH-UPDATE: Persist atomic multi-scope settings updates
      with optimistic revision conflict verification and cache refresh.
      Associated: `settings.update_batch()`, `RevisionConflictError`
      Logging: INFO emitted on committed batch settings update; WARNING emitted
      on revision conflict.

Python API Usage:
    ```python
    from app.host.settings import settings

    user = settings.user_access.username
    ```

CLI Usage:
    ```bash
    uv run python -m app.host.settings
    ```
"""

from __future__ import annotations

import json
import threading
from collections.abc import Mapping
from typing import Any

from app.host.logging import get_logger
from app.host.persistence.read import list_host_settings
from app.host.persistence.update import (
    RevisionConflictError,
    batch_save_host_settings,
)

__all__ = ["RevisionConflictError", "settings"]

logger = get_logger(__name__)

LOAD_FR = "FR-HOST-SETTINGS-LOAD"
BATCH_UPDATE_FR = "FR-HOST-SETTINGS-BATCH-UPDATE"


class _SettingsNode:
    """Recursive read-only node supporting nested dot and dictionary access."""

    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data

    def __getattr__(self, name: str) -> Any:
        if name in self._data:
            val = self._data[name]
            if isinstance(val, dict):
                return _SettingsNode(val)
            return val
        raise AttributeError(f"Setting key '{name}' not found")

    def __getitem__(self, key: str) -> Any:
        val = self._data[key]
        if isinstance(val, dict):
            return _SettingsNode(val)
        return val

    def get(self, key: str, default: Any = None) -> Any:
        val = self._data.get(key, default)
        if isinstance(val, dict):
            return _SettingsNode(val)
        return val

    def as_dict(self) -> dict[str, Any]:
        return self._data

    def __contains__(self, key: object) -> bool:
        return key in self._data

    def __len__(self) -> int:
        return len(self._data)


class _HostSettings:
    """Lazy settings container providing nested dot-access and atomic batch updates."""

    def __init__(self, data: dict[str, dict[str, Any]] | None = None) -> None:
        self._revision: int = 0
        self._lock = threading.RLock()
        self._default_conn: Any = None
        if data is not None:
            self._data = data
            self._loaded = True
        else:
            self._data = {}
            self._loaded = False

    def _ensure_loaded(self) -> None:
        if not self._loaded:
            self.reload()

    @property
    def revision(self) -> int:
        """Return current monotonic settings revision."""
        self._ensure_loaded()
        return self._revision

    def reload(self, conn: Any = None) -> None:
        """Reload settings and current revision from database."""
        with self._lock:
            self._data, self._revision = _read_settings_with_revision(
                conn=conn if conn is not None else self._default_conn
            )
            if conn is not None:
                self._default_conn = conn
            self._loaded = True

    def update_batch(
        self,
        updates: Mapping[str, Mapping[str, Any]],
        *,
        expected_revision: int | None = None,
        conn: Any = None,
    ) -> int:
        """Atomically persist batch settings updates with revision conflict checking."""
        with self._lock:
            target_conn = conn if conn is not None else self._default_conn
            new_rev = batch_save_host_settings(
                updates,
                expected_revision=expected_revision,
                conn=target_conn,
            )
            self.reload(conn=target_conn)
        logger.info(
            "%s: refreshed host settings after atomic batch update (revision=%d)",
            BATCH_UPDATE_FR,
            self._revision,
            extra={"fr_id": BATCH_UPDATE_FR, "revision": self._revision},
        )
        return new_rev

    def get(self, scope: str, key: str | None = None, default: Any = None) -> Any:
        """Retrieve setting value by scope and optional key with fallback default."""
        self._ensure_loaded()
        if key is None:
            if scope in self._data:
                val = self._data[scope]
                return _SettingsNode(val) if isinstance(val, dict) else val
            for sub in self._data.values():
                if isinstance(sub, dict) and scope in sub:
                    val = sub[scope]
                    return _SettingsNode(val) if isinstance(val, dict) else val
            return default

        scope_data = self.get_scope(scope)
        val = scope_data.get(key, default)
        logger.debug("%s: accessed %s.%s", LOAD_FR, scope, key)
        return val

    def get_scope(self, scope: str) -> dict[str, Any]:
        """Return all key-value settings within a scope."""
        self._ensure_loaded()
        if scope in self._data and isinstance(self._data[scope], dict):
            return dict(self._data[scope])
        for sub in self._data.values():
            if isinstance(sub, dict) and scope in sub and isinstance(sub[scope], dict):
                return dict(sub[scope])
        return {}

    def as_dict(self) -> dict[str, dict[str, Any]]:
        """Return raw nested dictionary of all loaded settings."""
        self._ensure_loaded()
        return self._data

    def __getattr__(self, name: str) -> Any:
        """Support scoped dot-access (e.g. settings.user_access.username)."""
        self._ensure_loaded()
        if name in self._data:
            val = self._data[name]
            return _SettingsNode(val) if isinstance(val, dict) else val
        for sub in self._data.values():
            if isinstance(sub, dict) and name in sub:
                val = sub[name]
                return _SettingsNode(val) if isinstance(val, dict) else val
        raise AttributeError(f"Setting scope '{name}' not found in loaded settings")

    def __getitem__(self, scope: str) -> Any:
        """Support dictionary indexing by scope."""
        self._ensure_loaded()
        if scope in self._data:
            val = self._data[scope]
            return _SettingsNode(val) if isinstance(val, dict) else val
        for sub in self._data.values():
            if isinstance(sub, dict) and scope in sub:
                val = sub[scope]
                return _SettingsNode(val) if isinstance(val, dict) else val
        raise KeyError(scope)

    def __contains__(self, scope: object) -> bool:
        """Check whether scope exists in loaded settings."""
        self._ensure_loaded()
        if scope in self._data:
            return True
        return any(
            isinstance(sub, dict) and scope in sub for sub in self._data.values()
        )

    def __len__(self) -> int:
        """Return number of configured scopes."""
        self._ensure_loaded()
        return len(self._data)


def _read_settings_with_revision(
    conn: Any = None,
) -> tuple[dict[str, dict[str, Any]], int]:
    """Read all host settings and maximum revision from persistence read layer."""
    try:
        rows = list_host_settings(conn=conn)
    except Exception as err:
        logger.warning(
            "%s: could not read host settings from database: %s",
            LOAD_FR,
            err,
            extra={"fr_id": LOAD_FR, "error": str(err)},
        )
        raise

    data: dict[str, dict[str, Any]] = {}
    max_rev = 0
    for row in rows:
        scope = str(row["scope"])
        key = str(row["key"])
        val_str = row["value_json"]
        rev = int(row.get("schema_version", 1) or 1)
        max_rev = max(max_rev, rev)
        try:
            val = json.loads(val_str)
        except json.JSONDecodeError, TypeError:
            val = val_str
        data.setdefault(scope, {})[key] = val

    logger.info(
        "%s: read host settings from database (scopes=%d, revision=%d)",
        LOAD_FR,
        len(data),
        max_rev,
        extra={"fr_id": LOAD_FR, "scopes": len(data), "revision": max_rev},
    )
    return data, max_rev


def _read_settings(conn: Any = None) -> dict[str, dict[str, Any]]:
    """Read all host settings from the database via persistence read layer."""
    data, _ = _read_settings_with_revision(conn=conn)
    return data


settings = _HostSettings()


def main() -> None:
    """Demonstrate reading host settings via persistence read layer."""
    print("Accessing global host settings...")
    user = settings.user_access.username
    print(f"Username: {user}")


if __name__ == "__main__":
    main()
