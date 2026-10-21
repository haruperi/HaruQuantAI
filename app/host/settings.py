# ruff: noqa: INP001
"""Host settings reader, revision tracker, atomic batch configuration.

Description:
    Reads and updates operational and application settings in the database
    through the persistence layer (app.host.persistence.read and
    app.host.persistence.update) and packages them into an accessible container
    for the rest of the host platform and workspaces. Supports atomic batch
    updates with optimistic revision conflict checking and stored-only projections.
    Exports a single lazy settings instance.

Purpose:
    FEAT-HOST-SETTINGS: Host settings reader, configuration packaging.

Key Capabilities:
    - FR-HOST-SETTINGS-LOAD: Read settings from database and package for app.
      Associated: `SettingsManager`, `settings`
      Logging: INFO on settings load with scope count; DEBUG on setting access.
    - FR-HOST-SETTINGS-BATCH-UPDATE: Persist atomic multi-scope settings updates
      with optimistic revision conflict verification and cache refresh.
      Associated: `SettingsManager.save_settings()`, `RevisionConflictError`
      Logging: INFO emitted on committed batch settings update; WARNING emitted
      on revision conflict.
    - FR-HOST-SETTINGS-LOAD: Project typed UI snapshots, catalogue metadata and
      safe account identity without exposing secrets. Associated: get_snapshot(),
      get_catalogue(), get_account(). Logging: DEBUG snapshot/account and INFO
      catalogue projection with fr_id.
    - FR-HOST-SETTINGS-BATCH-UPDATE: Validate and merge registered patches and
      account updates. Associated: save_changes(), save_account(). Logging: INFO
      after committed writes; persistence WARNING/ERROR on rejected transactions.

Python API Usage:
    ```python
    from app.host.settings import SettingsManager, settings

    user = settings.user_access.username
    snapshot = settings.get_snapshot()
    ```

CLI Usage:
    ```bash
    uv run python -m app.host.settings
    ```
"""

from __future__ import annotations

import copy
import json
import math
import threading
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Final

from app.host.logging import get_logger
from app.host.persistence import HostPersistence

RevisionConflictError = HostPersistence.RevisionConflictError

__all__ = [
    "RevisionConflictError",
    "SettingsManager",
    "settings",
]

logger = get_logger(__name__)

LOAD_FR = "FR-HOST-SETTINGS-LOAD"
BATCH_UPDATE_FR = "FR-HOST-SETTINGS-BATCH-UPDATE"
_MAX_LIST_ITEMS = 1000
_MAX_USERNAME_LENGTH = 128
_MIN_SESSION_MINS = 1440
_MAX_SESSION_MINS = 43200


@dataclass(frozen=True)
class _Field:
    group: str
    path: tuple[str, ...]
    kind: str
    readonly: bool = False
    options: tuple[str, ...] = ()
    minimum: float | None = None
    maximum: float | None = None

    @property
    def scope(self) -> str:
        return _GROUP_SCOPES[self.group]

    @property
    def record(self) -> str:
        return "app_general" if self.group == "connect_remote" else self.group

    @property
    def key(self) -> str:
        parts = self.path[1:] if self.group == "connect_remote" else self.path
        return ".".join(parts)

    @property
    def secret(self) -> bool:
        return self.path[-1] in _SECRET_KEYS

    @property
    def effect(self) -> str:
        if self.group in (
            "workspace_paths",
            "connect_mcp",
            "connect_remote",
            "config_troubleshooting",
        ) or self.key in ("host", "backend_port", "frontend_port", "gpu_accelerated"):
            return (
                "Saved configuration; requires the owning runtime capability or restart"
            )
        return "Saved configuration"


_SECRET_KEYS: Final = frozenset(
    {
        "password",
        "password_hash",
        "password_salt",
        "api_key",
        "client_secret",
        "access_token",
        "refresh_token",
        "auth_token",
        "bot_token",
    }
)
_GROUP_SCOPES: Final = {
    "app_general": "app.general",
    "config_global": "config.global",
    "config_cpu": "config.cpu",
    "config_performance": "config.performance",
    "config_memory": "config.memory",
    "config_databanks": "config.databanks",
    "config_optimizations": "config.optimizations",
    "config_troubleshooting": "config.troubleshooting",
    "connect_remote": "connect.remote",
    "connect_mcp": "connect.mcp",
    "notify_desktop": "notify.desktop",
    "notify_email": "notify.email",
    "notify_telegram": "notify.telegram",
    "config_metatrader5": "config.metatrader5",
    "config_ctrader": "config.ctrader",
    "config_agents": "config.agents",
    "workspace_paths": "workspace.paths",
    "engine_backtest": "engine.backtest",
    "calibration_indicators": "calibration.indicators",
    "user_access": "user.access",
}


def _build_fields() -> tuple[_Field, ...]:
    schema: dict[str, tuple[tuple[tuple[str, ...], str], ...]] = {
        "app_general": (
            (("theme",), "str"),
            (("language",), "str"),
            (("zoom",), "float"),
            (("auto_save_interval_s",), "int"),
            (("header_custom_text",), "str"),
            (("confirm_on_exit",), "bool"),
            (("host",), "str"),
            (("backend_port",), "int"),
            (("frontend_port",), "int"),
            (("gpu_accelerated",), "bool"),
        ),
        "config_global": (
            (("sounds_off",), "bool"),
            (("advanced_file_chooser",), "bool"),
            (("show_control_orders",), "bool"),
            (("footer_custom_text",), "str"),
            (("default_result_to_display",), "str"),
            (("data_frame_guard",), "str"),
        ),
        "config_cpu": (
            (("core_usage",), "str"),
            (("custom_cores",), "int"),
            (("high_priority",), "bool"),
            (("thread_affinity",), "bool"),
        ),
        "config_performance": (
            (("compute_pips_metrics",), "bool"),
            (("compute_pcts_metrics",), "bool"),
            (("compute_separate_metrics",), "bool"),
        ),
        "config_memory": (
            (("gc_type",), "str"),
            (("automatic_memory",), "bool"),
            (("memory_limit_gb",), "int"),
            (("dont_store_pending_orders",), "bool"),
            (("memory_cleanup",), "bool"),
            (("cleanup_interval_mins",), "int"),
        ),
        "config_databanks": (
            (("databank_sync_interval_mins",), "int"),
            (("sync_databanks_after_task_done",), "bool"),
            (("store_chart_data",), "bool"),
        ),
        "config_optimizations": ((("dont_store_op_3d_charts_data",), "bool"),),
        "config_troubleshooting": (
            (("gpu_accelerated",), "bool"),
            (("memory_protection",), "bool"),
            (("debug_level_active",), "bool"),
        ),
        "connect_remote": (
            (("allow",), "bool"),
            (("require_password",), "bool"),
            (("port",), "int"),
        ),
        "connect_mcp": (
            (("enabled",), "bool"),
            (("host",), "str"),
            (("port",), "int"),
            (("transport",), "str"),
            (("auth_token",), "str"),
            (("allowed_tools",), "list"),
            (("max_context_items",), "int"),
        ),
        "notify_desktop": (
            (("enabled",), "bool"),
            (("duration_seconds",), "int"),
            (("min_priority",), "str"),
            (("sound_enabled",), "bool"),
        ),
        "notify_email": (
            (("enabled",), "bool"),
            (("smtp_server",), "str"),
            (("smtp_port",), "int"),
            (("use_ssl",), "bool"),
            (("use_tls",), "bool"),
            (("username",), "str"),
            (("password",), "str"),
            (("from_address",), "str"),
            (("recipient_addresses",), "list"),
        ),
        "notify_telegram": (
            (("enabled",), "bool"),
            (("bot_token",), "str"),
            (("chat_id",), "str"),
            (("parse_mode",), "str"),
            (("disable_notification",), "bool"),
        ),
        "config_metatrader5": (
            (("enabled",), "bool"),
            (("terminal_path",), "str"),
            (("account_id",), "int"),
            (("password",), "str"),
            (("server",), "str"),
            (("environment",), "str"),
            (("timeout_ms",), "int"),
            (("portable",), "bool"),
            (("use_ticks",), "bool"),
        ),
        "config_ctrader": (
            (("enabled",), "bool"),
            (("account_id",), "str"),
            (("client_id",), "str"),
            (("client_secret",), "str"),
            (("access_token",), "str"),
            (("refresh_token",), "str"),
            (("environment",), "str"),
            (("gateway_host",), "str"),
            (("gateway_port",), "int"),
            (("redirect_url",), "str"),
        ),
        "config_agents": (
            (("active_provider",), "str"),
            (("agent_timeout_seconds",), "int"),
            (("system_prompt_preset",), "str"),
            (("openai", "api_key"), "str"),
            (("openai", "model"), "str"),
            (("openai", "base_url"), "str"),
            (("openai", "temperature"), "float"),
            (("openai", "max_tokens"), "int"),
            (("gemini", "api_key"), "str"),
            (("gemini", "model"), "str"),
            (("gemini", "base_url"), "str"),
            (("gemini", "use_vertex_ai"), "bool"),
            (("gemini", "fast_model"), "str"),
            (("gemini", "premium_model"), "str"),
            (("gemini", "fallback_model"), "str"),
            (("gemini", "temperature"), "float"),
            (("gemini", "max_tokens"), "int"),
            (("ollama", "model"), "str"),
            (("ollama", "base_url"), "str"),
            (("ollama", "temperature"), "float"),
            (("ollama", "timeout_seconds"), "int"),
        ),
        "workspace_paths": (
            (("configs_dir",), "str"),
            (("projects_dir",), "str"),
            (("strategies_dir",), "str"),
            (("data_dir",), "str"),
        ),
        "engine_backtest": (
            (("max_threads",), "int"),
            (("memory_limit_mb",), "int"),
            (("enable_caching",), "bool"),
            (("precision_mode",), "str"),
            (("benchmark_time_per_tick_ms",), "float"),
            (("dont_store_pending_orders",), "bool"),
            (("dont_store_op3d_charts",), "bool"),
            (("compute_separate_metrics",), "bool"),
            (("compute_pcts_metrics",), "bool"),
            (("compute_pips_metrics",), "bool"),
            (("source_code_constants_params",), "bool"),
        ),
        "calibration_indicators": (
            (("QQE.RSIPeriod",), "list"),
            (("QQE.sF",), "list"),
            (("QQE.Value1",), "str"),
        ),
        "user_access": (
            (("username",), "str"),
            (("password_hash",), "str"),
            (("password_salt",), "str"),
            (("session_timeout_mins",), "int"),
            (("allow_remember_me",), "bool"),
            (("require_auth",), "bool"),
        ),
    }
    options = {
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
        "core_usage": ("single", "all_except_one", "custom", "all"),
        "gc_type": ("ParallelGC", "G1GC", "Automatic"),
        "default_result_to_display": ("Portfolio", "Main"),
        "data_frame_guard": ("warn", "stop", "off"),
    }
    limits = {
        "zoom": (0.7, 1.8),
        "memory_limit_gb": (2, 1024),
        "duration_seconds": (0, 3600),
        "auto_save_interval_s": (1, 86400),
        "custom_cores": (1, 65536),
        "max_threads": (1, 65536),
        "max_context_items": (1, 100000),
        "agent_timeout_seconds": (1, 86400),
        "temperature": (0, 2),
        "max_tokens": (1, 1000000),
        "timeout_seconds": (1, 86400),
        "timeout_ms": (1, 3600000),
    }
    result = []
    for group, rules in schema.items():
        for path, kind in rules:
            key = path[-1]
            lo, hi = limits.get(key, (None, None))
            if key.endswith("port"):
                lo, hi = 1, 65535
            physical = ("remote_access", *path) if group == "connect_remote" else path
            result.append(
                _Field(
                    group,
                    physical,
                    kind,
                    readonly=group == "user_access",
                    options=options.get(key, ()),
                    minimum=lo,
                    maximum=hi,
                )
            )
    return tuple(result)


def _leaf_paths(value: Any, prefix: tuple[str, ...] = ()) -> list[tuple[str, ...]]:
    if not isinstance(value, dict):
        return [prefix]
    return [
        path
        for key, child in value.items()
        for path in _leaf_paths(child, (*prefix, key))
    ]


def _validate_field(field: _Field, value: Any) -> None:
    label = f"{field.scope}.{field.key}"
    valid = {
        "str": isinstance(value, str),
        "bool": type(value) is bool,
        "int": type(value) is int,
        "float": type(value) in (int, float),
        "list": isinstance(value, list),
    }[field.kind]
    if value is None and field.key == "databank_sync_interval_mins":
        return
    if not valid:
        raise ValueError(f"Invalid type for {label}")
    if (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and (
            not math.isfinite(value)
            or (field.minimum is not None and value < field.minimum)
            or (field.maximum is not None and value > field.maximum)
        )
    ):
        raise ValueError(f"Invalid range for {label}")
    if field.options and value not in field.options:
        raise ValueError(f"Unsupported option for {label}")
    if isinstance(value, str) and len(value) > (
        30 if field.key.endswith("custom_text") else 8192
    ):
        raise ValueError(f"Value too long for {label}")
    if field.key == "cleanup_interval_mins" and value not in (0, 5, 15, 30, 60):
        raise ValueError("Unsupported cleanup interval")
    if field.key == "databank_sync_interval_mins" and value not in (0, 5, 10, 15, 60):
        raise ValueError("Unsupported databank interval")
    if isinstance(value, list):
        _validate_list(field, value, label)


def _validate_list(field: _Field, value: list[Any], label: str) -> None:
    if len(value) > _MAX_LIST_ITEMS or any(
        type(x) not in (str, int, float) for x in value
    ):
        raise ValueError(f"Invalid list for {label}")
    if field.group == "calibration_indicators" and any(
        type(x) not in (int, float) for x in value
    ):
        raise ValueError(f"Expected numeric calibration list for {label}")
    if field.key in ("recipient_addresses", "allowed_tools") and any(
        not isinstance(x, str) for x in value
    ):
        raise ValueError(f"Expected text list for {label}")
    if any(isinstance(x, float) and not math.isfinite(x) for x in value):
        raise ValueError(f"Non-finite list value for {label}")


_FIELDS: Final = _build_fields()
_MISSING: Final = object()


class _SettingsNode:
    """Recursive read-only node supporting nested dot and dictionary access."""

    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data

    def __getattr__(self, name: str) -> Any:
        canonical = self._data.get("application", {}).get(name)
        if name in _GROUP_SCOPES and isinstance(canonical, dict):
            return _SettingsNode(copy.deepcopy(canonical))
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


class SettingsManager:
    """Lazy settings container with dot-access, atomic updates and stored values."""

    def __init__(self, data: dict[str, dict[str, Any]] | None = None) -> None:
        self._revision: int = 0
        self._lock = threading.RLock()
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

    def reload(self) -> None:
        """Reload settings and current revision from database."""
        with self._lock:
            self._data, self._revision = _read_settings_with_revision()
            self._loaded = True

    def set_in_memory(self, scope: str, key: str, value: Any) -> None:
        """Store a setting in memory without triggering database persistence."""
        with self._lock:
            self._data.setdefault(scope, {})[key] = value

    def save_settings(
        self,
        updates: Mapping[str, Mapping[str, Any]],
        *,
        expected_revision: int | None = None,
        revoke_sessions: bool = False,
    ) -> int:
        """Persist complete internal records with database-atomic revision checking."""
        with self._lock:
            self.reload()
            current = self._revision
            expected = current if expected_revision is None else expected_revision
            if current != expected:
                raise RevisionConflictError(
                    expected_revision=expected, current_revision=current
                )
            changed = {
                scope: {
                    key: val
                    for key, val in items.items()
                    if key not in self._data.get(scope, {})
                    or self._data[scope][key] != val
                }
                for scope, items in updates.items()
            }
            changed = {scope: items for scope, items in changed.items() if items}
            now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
            ops: list[Mapping[str, Any]] = []
            for scope, items in changed.items():
                for key, val in items.items():
                    ops.append(
                        {
                            "op_type": "upsert",
                            "table": "host_settings",
                            "key_columns": {"scope": scope, "key": key},
                            "values": {
                                "scope": scope,
                                "key": key,
                                "value_json": json.dumps(val, allow_nan=False),
                                "schema_version": current + 1,
                                "updated_at_utc": now,
                            },
                        }
                    )
            HostPersistence.apply_batch(
                ops,
                expected_settings_revision=expected,
                revoke_active_sessions=revoke_sessions,
            )
            self.reload()
            logger.info(
                "%s: committed settings update (revision=%d, groups=%d)",
                BATCH_UPDATE_FR,
                self._revision,
                len(changed),
                extra={"fr_id": BATCH_UPDATE_FR, "revision": self._revision},
            )
            return self._revision

    def get_snapshot(self) -> dict[str, Any]:
        """Project fresh registered non-secret settings under logical group IDs."""
        with self._lock:
            self.reload()
            values: dict[str, dict[str, Any]] = {}
            for field in _FIELDS:
                if not field.secret:
                    value = self._field_value(field)
                    if value is not _MISSING:
                        values.setdefault(field.scope, {})[field.key] = value
            logger.debug(
                "%s: projected safe snapshot", LOAD_FR, extra={"fr_id": LOAD_FR}
            )
            return {"revision": self._revision, "values": values}

    def get_catalogue(self) -> dict[str, Any]:
        """Return typed field metadata and configured-only secret projections."""
        with self._lock:
            self.reload()
            fields = []
            known: set[tuple[str, tuple[str, ...]]] = set()
            for field in _FIELDS:
                known.add((field.record, field.path))
                value = self._field_value(field)
                if value is _MISSING:
                    continue
                item: dict[str, Any] = {
                    "scope": field.scope,
                    "group": field.group,
                    "key": field.key,
                    "label": field.key.replace("_", " ")
                    .replace(".", " / ")
                    .capitalize(),
                    "kind": field.kind,
                    "readonly": field.readonly,
                    "secret": field.secret,
                    "effect": field.effect,
                }
                if field.options:
                    item["options"] = list(field.options)
                if field.minimum is not None:
                    item["minimum"] = field.minimum
                if field.maximum is not None:
                    item["maximum"] = field.maximum
                if field.secret:
                    item["configured"] = bool(value)
                else:
                    item["value"] = value
                fields.append(item)
            unknown: list[dict[str, str]] = []
            for group, value in self._data.get("application", {}).items():
                unknown.extend(
                    {
                        "scope": "application",
                        "key": f"{group}." + ".".join(path),
                        "reason": "Unregistered field; preserved read-only",
                    }
                    for path in _leaf_paths(value)
                    if (group, path) not in known
                )
            logger.info(
                "%s: projected field catalogue", LOAD_FR, extra={"fr_id": LOAD_FR}
            )
            return {"revision": self._revision, "fields": fields, "unknown": unknown}

    def _field_value(self, field: _Field) -> Any:
        value: Any = self._data.get("application", {}).get(field.record, {})
        for segment in field.path:
            if not isinstance(value, dict):
                raise ValueError(  # noqa: TRY004 - shared settings validation boundary
                    f"Stored settings path is not an object: {field.scope}"
                )
            if segment not in value:
                return _MISSING
            value = value[segment]
        _validate_field(field, value)
        return copy.deepcopy(value)

    def save_changes(
        self,
        changes: Mapping[str, Mapping[str, Any]],
        *,
        expected_revision: int,
        include_secrets: bool = False,
    ) -> dict[str, Any]:
        """Validate registered field patches and merge into canonical records."""
        with self._lock:
            self.reload()
            updates: dict[str, Any] = {}
            index = {(f.scope, f.key): f for f in _FIELDS}
            for scope, fields in changes.items():
                if not fields:
                    raise ValueError("A settings group patch cannot be empty")
                for key, value in fields.items():
                    field = index.get((scope, key))
                    if (
                        field is None
                        or field.readonly
                        or (field.secret and not include_secrets)
                    ):
                        raise ValueError(
                            "Unknown, protected or read-only settings field"
                        )
                    _validate_field(field, value)
                    group = updates.setdefault(
                        field.record,
                        copy.deepcopy(
                            self._data.get("application", {}).get(field.record, {})
                        ),
                    )
                    if not isinstance(group, dict):
                        raise TypeError("Stored settings group is not an object")
                    node = group
                    for part in field.path[:-1]:
                        if part not in node:
                            node[part] = {}
                        if not isinstance(node[part], dict):
                            raise TypeError("Stored settings path is not an object")
                        node = node[part]
                    node[field.path[-1]] = copy.deepcopy(value)
            before = self._revision
            revision = self.save_settings(
                {"application": updates}, expected_revision=expected_revision
            )
            result = self.get_snapshot()
            result["wrote"] = revision != before
            return result

    def get_account(self) -> dict[str, Any]:
        """Read safe account identity and session duration from canonical settings."""
        self.reload()
        account = self.get_scope("user_access")
        if "username" not in account or "session_timeout_mins" not in account:
            logger.warning(
                "%s: account is unconfigured", LOAD_FR, extra={"fr_id": LOAD_FR}
            )
            raise KeyError("Account identity and session duration are not configured")
        if (
            not isinstance(account["username"], str)
            or not account["username"].strip()
            or type(account["session_timeout_mins"]) is not int
            or not _MIN_SESSION_MINS
            <= account["session_timeout_mins"]
            <= _MAX_SESSION_MINS
        ):
            raise ValueError("Invalid stored account configuration")
        logger.debug("%s: projected account", LOAD_FR, extra={"fr_id": LOAD_FR})
        return {
            "revision": self._revision,
            "username": account["username"],
            "session_timeout_mins": account["session_timeout_mins"],
        }

    def save_account(
        self,
        username: str,
        duration: int,
        password_hash: str,
        *,
        expected_revision: int,
    ) -> int:
        """Commit account credentials and durable session revocation together."""
        with self._lock:
            self.reload()
            if (
                not username.strip()
                or len(username) > _MAX_USERNAME_LENGTH
                or not _MIN_SESSION_MINS <= duration <= _MAX_SESSION_MINS
            ):
                raise ValueError("Invalid account identity or session duration")
            self.get_account()
            account = copy.deepcopy(self.get_scope("user_access"))
            account.update(
                username=username.strip(),
                session_timeout_mins=duration,
                password_hash=password_hash,
            )
            return self.save_settings(
                {"application": {"user_access": account}},
                expected_revision=expected_revision,
                revoke_sessions=True,
            )

    def get(self, scope: str, key: str | None = None, default: Any = None) -> Any:
        """Retrieve setting value by scope and optional key with fallback default."""
        self._ensure_loaded()
        if key is None:
            canonical = self._data.get("application", {}).get(scope)
            if scope in _GROUP_SCOPES and isinstance(canonical, dict):
                return _SettingsNode(copy.deepcopy(canonical))
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
        canonical = self._data.get("application", {}).get(scope)
        if scope in _GROUP_SCOPES and isinstance(canonical, dict):
            return copy.deepcopy(canonical)
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
        canonical = self._data.get("application", {}).get(name)
        if name in _GROUP_SCOPES and isinstance(canonical, dict):
            return _SettingsNode(copy.deepcopy(canonical))
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
        canonical = self._data.get("application", {}).get(scope)
        if scope in _GROUP_SCOPES and isinstance(canonical, dict):
            return _SettingsNode(copy.deepcopy(canonical))
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


def _read_settings_with_revision() -> tuple[dict[str, dict[str, Any]], int]:
    """Read all host settings and maximum revision from persistence read layer."""
    try:
        rows = HostPersistence.read_records("host_settings")
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


def _read_settings() -> dict[str, dict[str, Any]]:
    """Read all host settings from the database via persistence read layer."""
    data, _ = _read_settings_with_revision()
    return data


settings = SettingsManager()


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
