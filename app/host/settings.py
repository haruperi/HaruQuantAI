# ruff: noqa: INP001
"""Host settings reader, revision tracker, atomic batch configuration, and theming.

Description:
    Reads and updates operational and application settings in the database
    through the persistence layer (app.host.persistence.read and
    app.host.persistence.update) and packages them into an accessible container
    for the rest of the host platform and workspaces. Supports atomic batch
    updates with optimistic revision conflict checking, alongside Tailwind CSS
    and Dockview theme token management. Exports a single lazy settings instance.

Purpose:
    FEAT-HOST-SETTINGS: Host settings reader, configuration packaging, and theming.

Key Capabilities:
    - FR-HOST-SETTINGS-LOAD: Read settings from database and package for app.
      Associated: `HostSettings`, `settings`
      Logging: INFO on settings load with scope count; DEBUG on setting access.
    - FR-HOST-SETTINGS-BATCH-UPDATE: Persist atomic multi-scope settings updates
      with optimistic revision conflict verification and cache refresh.
      Associated: `HostSettings.update_batch()`, `RevisionConflictError`
      Logging: INFO emitted on committed batch settings update; WARNING emitted
      on revision conflict.
    - FR-HOST-SETTINGS-THEME-TOKENS: Provide Tailwind CSS and Dockview theme tokens
      and manage dark/light appearance state.
      Associated: `Theme.set_dark()`, `Theme.get_tokens()`, `Theme.set_light()`,
      `Theme.get_light_tokens()`
      Logging: INFO on theme mode switch; DEBUG on theme token retrieval.

Python API Usage:
    ```python
    from app.host.settings import HostSettings, Theme, settings

    user = settings.user_access.username
    tokens = settings.theme.set_dark()
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
from typing import Any, Final

from app.host.logging import get_logger
from app.host.persistence.read import list_host_settings
from app.host.persistence.update import (
    RevisionConflictError,
    batch_save_host_settings,
)

__all__ = [
    "HostSettings",
    "RevisionConflictError",
    "Theme",
    "settings",
]

logger = get_logger(__name__)

LOAD_FR = "FR-HOST-SETTINGS-LOAD"
BATCH_UPDATE_FR = "FR-HOST-SETTINGS-BATCH-UPDATE"
THEME_FR = "FR-HOST-SETTINGS-THEME-TOKENS"

DARK_THEME_TOKENS: Final[dict[str, Any]] = {
    "theme": "dark",
    "background": {
        "primary": "#0f172a",
        "secondary": "#1e293b",
        "surface": "#1e293b",
        "overlay": "rgba(15, 23, 42, 0.8)",
    },
    "text": {
        "primary": "#f8fafc",
        "secondary": "#94a3b8",
        "muted": "#64748b",
        "accent": "#38bdf8",
    },
    "border": {
        "default": "#334155",
        "contrast": "#475569",
    },
    "dockview": {
        "headers": "#1e293b",
        "panels": "#0f172a",
        "tab_active": "#334155",
        "tab_inactive": "#1e293b",
    },
    "chart": {
        "background": "#0f172a",
        "grid": "#1e293b",
        "text": "#94a3b8",
        "candle_up": "#22c55e",
        "candle_down": "#ef4444",
    },
    "typography": {
        "font_sans": "Inter, system-ui, sans-serif",
        "font_mono": "Fira Code, monospace",
        "size_base": "14px",
        "size_sm": "12px",
    },
}

LIGHT_THEME_TOKENS: Final[dict[str, Any]] = {
    "theme": "light",
    "background": {
        "primary": "#ffffff",
        "secondary": "#f8fafc",
        "surface": "#f1f5f9",
        "overlay": "rgba(255, 255, 255, 0.8)",
    },
    "text": {
        "primary": "#0f172a",
        "secondary": "#475569",
        "muted": "#94a3b8",
        "accent": "#0284c7",
    },
    "border": {
        "default": "#e2e8f0",
        "contrast": "#cbd5e1",
    },
    "dockview": {
        "headers": "#f1f5f9",
        "panels": "#ffffff",
        "tab_active": "#e2e8f0",
        "tab_inactive": "#f8fafc",
    },
    "chart": {
        "background": "#ffffff",
        "grid": "#f1f5f9",
        "text": "#475569",
        "candle_up": "#16a34a",
        "candle_down": "#dc2626",
    },
    "typography": {
        "font_sans": "Inter, system-ui, sans-serif",
        "font_mono": "Fira Code, monospace",
        "size_base": "14px",
        "size_sm": "12px",
    },
}


class Theme:
    """Tailwind CSS and Dockview appearance state and design token manager."""

    def __init__(self, host_settings: HostSettings | None = None) -> None:
        """Initialize Theme manager with an optional host settings container."""
        self._settings = host_settings

    @property
    def current_theme(self) -> str:
        """Return the current active theme identifier ('dark' or 'light')."""
        if self._settings is not None:
            try:
                theme_val = self._settings.get("ui", "theme", default=None)
                if theme_val in ("dark", "light"):
                    return str(theme_val)
            except (KeyError, AttributeError, ValueError) as err:
                logger.debug(
                    "%s: Could not inspect current theme from settings: %s",
                    THEME_FR,
                    err,
                    extra={"fr_id": THEME_FR},
                )
        return "dark"

    def set_dark(self) -> dict[str, Any]:
        """Apply dark theme state and return dark theme tokens."""
        if self._settings is not None:
            try:
                self._settings.update_batch({"ui": {"theme": "dark"}})
            except (RuntimeError, ValueError) as err:
                logger.warning(
                    "%s: Persisting dark theme failed, caching in memory: %s",
                    THEME_FR,
                    err,
                    extra={"fr_id": THEME_FR},
                )
                self._settings.set_in_memory("ui", "theme", "dark")
        tokens = self.get_tokens()
        logger.info(
            "%s: Set theme to 'dark' with %d token groups.",
            THEME_FR,
            len(tokens),
            extra={"fr_id": THEME_FR, "theme": "dark"},
        )
        return tokens

    def get_tokens(self) -> dict[str, Any]:
        """Return dark mode color variables, background shades, and tokens."""
        logger.debug(
            "%s: Retrieved dark theme tokens.", THEME_FR, extra={"fr_id": THEME_FR}
        )
        return dict(DARK_THEME_TOKENS)

    def set_light(self) -> dict[str, Any]:
        """Apply light theme state and return light theme tokens."""
        if self._settings is not None:
            try:
                self._settings.update_batch({"ui": {"theme": "light"}})
            except (RuntimeError, ValueError) as err:
                logger.warning(
                    "%s: Persisting light theme failed, caching in memory: %s",
                    THEME_FR,
                    err,
                    extra={"fr_id": THEME_FR},
                )
                self._settings.set_in_memory("ui", "theme", "light")
        tokens = self.get_light_tokens()
        logger.info(
            "%s: Set theme to 'light' with %d token groups.",
            THEME_FR,
            len(tokens),
            extra={"fr_id": THEME_FR, "theme": "light"},
        )
        return tokens

    def get_light_tokens(self) -> dict[str, Any]:
        """Return light mode color variables, clean white/gray, and borders."""
        logger.debug(
            "%s: Retrieved light theme tokens.", THEME_FR, extra={"fr_id": THEME_FR}
        )
        return dict(LIGHT_THEME_TOKENS)


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


class HostSettings:
    """Lazy settings container with dot-access, atomic updates, and theming."""

    def __init__(self, data: dict[str, dict[str, Any]] | None = None) -> None:
        self._revision: int = 0
        self._lock = threading.RLock()
        self._default_conn: Any = None
        self.theme: Theme = Theme(self)
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

    def set_in_memory(self, scope: str, key: str, value: Any) -> None:
        """Store a setting in memory without triggering database persistence."""
        with self._lock:
            self._data.setdefault(scope, {})[key] = value

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
    except (RuntimeError, ValueError) as err:
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


settings = HostSettings()


def main() -> None:
    """Demonstrate reading host settings via persistence read layer."""
    logger.info("Accessing global host settings via settings CLI...")
    try:
        user = settings.user_access.username
        logger.info("Found username: %s", user)
    except (AttributeError, KeyError, RuntimeError) as err:
        logger.info("Settings read test completed: %s", err)


if __name__ == "__main__":
    main()
