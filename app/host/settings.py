"""Runtime Host Configuration and Optimistic Concurrency Settings Store.

Description:
    This module manages immutable runtime host settings and persisted system
    preferences. It exists to guarantee schema-validated, type-safe configuration,
    prevent sensitive credential leakage (passwords, TLS private keys) during
    serialization, enforce optimistic concurrency control via monotonic revision
    counters, and broadcast configuration change events. Externally, it participates
    in three key workflows: (1) The application entrypoint (`app.main`) calls
    `load_settings()` to merge CLI options, environment variables, and persisted boot
    records into an immutable `HostSettings` instance; (2) `BootstrapCoordinator`
    validates database schemas and initial settings snapshots during host boot; and
    (3) Workspaces and frontend clients access public preferences via `SettingsAccess`
    and HTTP endpoints (`/api/v1/settings`), issuing transactional patches that
    publish notifications over `app.host.events`. Internally, `HostSettings` enforces
    network and TLS constraints; helper functions (`_valid_setting`, `_public`) sanitize
    and project public fields while protecting private workspace partitions; and
    `SettingsStore` coordinates atomic compare-and-set updates and isolated private
    record persistence.

Purpose:
    FEAT-HOST-SETTINGS: Typed Runtime Configuration and CAS Settings Store.
    Provides immutable runtime configuration models, optimistic concurrency
    preference updates, sensitive field masking, and event-driven preference
    change broadcast.

Key Capabilities:
    - FR-HOST-SETTINGS-CONFIG-VALIDATION: Runtime Host Configuration Validation
      Associated: `HostSettings.validate_network()`, `load_settings()`
      Logging: Emits debug log when runtime configuration successfully validates
      against network, port, and TLS pairing constraints.
    - FR-HOST-SETTINGS-SCHEMA-PROJECTION: Public Settings Schema Projection & Masking
      Associated: `SettingsStore.snapshot()`, `_public()`, `_public_record()`
      Logging: Emits debug log on public settings snapshot generation with revision
      number, stripping unprojected or private fields.
    - FR-HOST-SETTINGS-TRANSACTIONAL-PATCH: Atomic CAS Patch & Event Broadcast
      Associated: `SettingsStore.patch()`
      Logging: Emits info log when settings patch commits successfully with
      incremented revision and broadcasts updates on the settings event channel.
    - FR-HOST-SETTINGS-PRIVATE-STORAGE: Partition-Isolated Private Record Persistence
      Associated: `SettingsStore.get_private()`, `SettingsStore.set_private()`
      Logging: Emits info log when an owner-scoped private configuration record is
      upserted into storage.
    - FR-HOST-SETTINGS-TERMINAL-SELECTION: Credential-Free Global Terminal Read
      Associated: `SettingsStore.mt5_terminal_configuration()`
      Logging: Emits info on successful global terminal configuration reads;
      verification checks that credentials and paths are absent from logs.

Python API Usage:
    ```python
    from pathlib import Path
    from app.host.events import EventBus
    from app.host.settings import HostSettings, SettingsStore, load_settings

    # 1. Load immutable runtime configuration
    config: HostSettings = load_settings({"port": 8080})

    # 2. Instantiate persistent settings store
    store = SettingsStore(Path("data/database/haruquantai.db"))

    # 3. Read public settings snapshot
    snapshot = store.snapshot()
    rev = snapshot["revision"]

    # 4. Atomically patch preferences with revision guard
    bus = EventBus()
    updated = store.patch(
        {"app.general": {"theme": "dark"}},
        expected_revision=rev,
        bus=bus,
    )
    ```

CLI Usage:
    Settings are configured via CLI arguments and environment variables passed
    to the main entrypoint:
    ```bash
    # Configure via CLI flags
    uv run python -m app.main --host 127.0.0.1 --port 8080 --data-dir ./data

    # Configure via environment variables
    export HARU_HOST="127.0.0.1"
    export HARU_PORT="8080"
    uv run python -m app.main
    ```
"""

import ipaddress
import json
import math
import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Self

from pydantic import Field, SecretStr, model_validator

from app.host.contracts import Document
from app.host.events import SETTINGS_CHANNEL, EventBus
from app.host.logging import get_logger
from app.host.network import SourceCredentials
from app.persistence.host import (
    HostPersistenceConflictError,
    HostPersistenceValueError,
    HostSettingRecord,
    HostStore,
    patch_settings,
    read_settings,
    settings_snapshot,
    utc_now_iso,
)

logger = get_logger(__name__)


class SettingsError(ValueError):
    """The public settings projection is malformed or unsupported."""


class SettingsConflictError(SettingsError):
    """A concurrent writer changed the expected revision."""


@dataclass(frozen=True)
class MT5TerminalConfiguration:
    """Credential-free terminal selection owned by global host settings."""

    enabled: bool
    terminal_path: str
    portable: bool = False


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
        "benchmark_time_per_tick_ms": "number",
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
    "config.metatrader5": {
        "enabled": "bool",
        "terminal_path": "str",
        "account_id": "str_or_int",
        "password": "str",  # pragma: allowlist secret
        "server": "str",
        "environment": "str",
        "timeout_ms": "int",
        "portable": "bool",
        "use_ticks": "bool",
    },
    "config.ctrader": {
        "enabled": "bool",
        "client_id": "str",
        "client_secret": "str",  # pragma: allowlist secret
        "access_token": "str",
        "refresh_token": "str",
        "redirect_url": "str",
        "environment": "str",
        "account_id": "str_or_int",
        "gateway_host": "str",
        "gateway_port": "int",
    },
    "config.agents": {
        "active_provider": "str",
        "gemini": "dict",
        "openai": "dict",
        "ollama": "dict",
        "system_prompt_preset": "str",
        "agent_timeout_seconds": "int",
    },
    "workspace.paths": {
        "configs_dir": "str",
        "projects_dir": "str",
        "strategies_dir": "str",
        "customdata_dir": "str",
    },
    "engine.backtest": {
        "max_threads": "int",
        "memory_limit_mb": "int",
        "enable_caching": "bool",
        "precision_mode": "str",
        "benchmark_time_per_tick_ms": "number",
        "dont_store_pending_orders": "bool",
        "dont_store_op3d_charts": "bool",
        "compute_separate_metrics": "bool",
        "compute_pcts_metrics": "bool",
        "compute_pips_metrics": "bool",
        "source_code_constants_params": "bool",
    },
    "notify.email": {
        "enabled": "bool",
        "smtp_server": "str",
        "smtp_port": "int",
        "use_ssl": "bool",
        "use_tls": "bool",
        "username": "str",
        "from_address": "str",
    },
    "notify.telegram": {
        "enabled": "bool",
        "chat_id": "str",
        "parse_mode": "str",
        "disable_notification": "bool",
    },
    "notify.desktop": {
        "enabled": "bool",
        "sound_enabled": "bool",
        "duration_seconds": "int",
        "min_priority": "str",
    },
    "connect.remote": {
        "allow": "bool",
        "require_password": "bool",  # pragma: allowlist secret
    },
    "connect.mcp": {
        "enabled": "bool",
        "host": "str",
        "port": "int",
        "transport": "str",
        "allowed_tools": "list",
        "max_context_items": "int",
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
    "active_provider": ("gemini", "openai", "ollama"),
    "environment": ("demo", "live", "real"),
    "precision_mode": ("high", "standard", "low"),
    "transport": ("sse", "stdio", "websocket", "http"),
    "min_priority": ("low", "normal", "high", "critical"),
    "parse_mode": ("HTML", "Markdown", "MarkdownV2"),
}
FIELD_RANGES: dict[str, tuple[float, float]] = {
    "zoom": (0.7, 1.8),
    "custom_cores": (1, 1024),
    "memory_limit_gb": (2, 1024),
    "smtp_port": (1, 65535),
    "gateway_port": (1, 65535),
    "port": (1, 65535),
    "timeout_ms": (1000, 300000),
    "agent_timeout_seconds": (10, 3600),
    "max_threads": (1, 256),
    "memory_limit_mb": (256, 1048576),
    "duration_seconds": (1, 60),
    "max_context_items": (1, 1000),
}
TITLE_FIELDS = frozenset(("header_custom_text", "footer_custom_text"))
MAX_TITLE_LENGTH = 30


def _valid_field(value: Any, kind: str) -> bool:
    """Check primitive field types without treating booleans as numbers.

    Numbers must be finite. Intervals accept None or nonnegative integers; narrower
    allowed-value restrictions are applied by _valid_setting.

    Args:
        value: Candidate decoded JSON value.
        kind: Schema kind: str, bool, int, number, interval, list, dict, or str_or_int.

    Returns:
        True for matching values; unknown kinds return False.
    """
    validators: dict[str, Callable[[Any], bool]] = {
        "str": lambda v: isinstance(v, str),
        "bool": lambda v: type(v) is bool,
        "int": lambda v: type(v) is int,
        "number": lambda v: type(v) in (int, float) and math.isfinite(v),
        "interval": lambda v: v is None or (type(v) is int and v >= 0),
        "list": lambda v: isinstance(v, list),
        "dict": lambda v: isinstance(v, dict),
        "str_or_int": lambda v: (
            (isinstance(v, str) or type(v) is int) and type(v) is not bool
        ),
    }
    check = validators.get(kind)
    return check(value) if check is not None else False


def _valid_setting(key: str, field: str, value: Any) -> bool:
    """Apply type, choice, range, and title-length rules to a public field.

    Args:
        key: Known PUBLIC_FIELDS record key.
        field: Candidate field name in that record.
        value: Proposed decoded JSON value.

    Returns:
        Whether the field exists and satisfies all applicable constraints.

    Raises:
        KeyError: key is not a registered public record.
    """
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
    """Decode a JSON settings object with a domain-specific error.

    Args:
        value_json: Serialized object to decode.

    Returns:
        Decoded object without field-level validation.

    Raises:
        SettingsError: JSON is malformed or its root is not an object.
    """
    try:
        value = json.loads(value_json)
    except (TypeError, json.JSONDecodeError) as error:
        raise SettingsError("Malformed host settings value") from error
    if not isinstance(value, dict):
        raise SettingsError("Host settings record must be an object")
    return value


def _public_record(key: str, value: dict[str, Any]) -> dict[str, Any]:
    """Validate known fields and omit everything outside the public projection.

    Args:
        key: Registered public record key.
        value: Decoded record that may include private fields.

    Returns:
        Fresh mapping containing only present public fields.

    Raises:
        SettingsError: A present public field violates its constraints.
        KeyError: key is not registered.
    """
    fields = PUBLIC_FIELDS[key]
    for field, field_value in value.items():
        if field in fields and not _valid_setting(key, field, field_value):
            raise SettingsError("Invalid host settings field")
    return {field: value[field] for field in fields if field in value}


def _validate_values(values: dict[str, Any]) -> None:
    """Check public records while leaving unknown private records untouched.

    Used inside the persistence transaction; it does not mutate or sanitize the
    stored mapping. Private values remain available to their owner.

    Args:
        values: Merged storage records keyed by setting name.

    Raises:
        SettingsError: A known record is not an object or contains invalid public
            fields.
    """
    for key, value in values.items():
        if key in PUBLIC_FIELDS:
            if not isinstance(value, dict):
                raise SettingsError("Malformed settings record")
            _public_record(key, value)


def _public(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Build a safe wire snapshot from an internal storage snapshot.

    Args:
        snapshot: Internal mapping containing revision and values.

    Returns:
        Same revision with validated, public-only records and fields.

    Raises:
        SettingsError: Known stored fields are malformed.
    """
    values = snapshot["values"]
    _validate_values(values)
    return {
        "revision": snapshot["revision"],
        "values": {
            key: _public_record(key, value)
            for key, value in values.items()
            if key in PUBLIC_FIELDS
        },
    }


class HostSettings(Document):
    """Validated immutable runtime configuration passed to host components.

    Construction validates values but does not inspect TLS files or create paths.
    Password and private-key fields are excluded from model dumps and repr. Zero
    workers requests automatic sizing; session_seconds is a lifetime in seconds.
    Collection fields roots and origins are supplied through records or overrides.
    """

    host: str = "127.0.0.1"
    port: int = Field(default=8000, ge=1, le=65535)
    data_dir: Path = Path("data")
    password: SecretStr | None = Field(default=None, exclude=True, repr=False)
    source_credentials: tuple[SourceCredentials, ...] = Field(
        default=(), exclude=True, repr=False
    )
    workers: int = Field(default=0, ge=0, le=61)
    ui_dist: Path = Path("app/ui/dist")
    installation_root: Path | None = None
    roots: tuple[Path, ...] = (
        Path("app/workspace"),
        Path("app/plugin"),
        Path("app/plugins"),
    )
    open_browser: bool = False
    certificate: Path | None = None
    private_key: Path | None = Field(default=None, exclude=True, repr=False)
    origins: tuple[str, ...] = ("http://localhost:3000", "http://127.0.0.1:3000")
    session_seconds: int = Field(default=3600, ge=1, le=86400)

    @model_validator(mode="after")
    def validate_network(self) -> Self:
        """Enforce literal bind addresses and remote-host credentials.

        This is a Pydantic after-validator. It checks configuration relationships, not
        certificate contents, file accessibility, or stored operator credentials.

        Returns:
            This validated settings instance.

        Raises:
            ValueError: The address is invalid, TLS files are unpaired, a password is
                empty, or remote binding lacks password/TLS.
        """
        address = ipaddress.ip_address(self.host)
        if bool(self.certificate) != bool(self.private_key):
            raise ValueError("Both certificate and private key are required")
        if not address.is_loopback and not (self.password and self.certificate):
            raise ValueError("Remote binding requires password and TLS")
        if self.password is not None and not self.password.get_secret_value():
            raise ValueError("Password must not be empty")
        return self

    @property
    def database_path(self) -> Path:
        """Derive the unified database location without filesystem access.

        Returns:
            data_dir/database/haruquantai.db; existence is not checked.
        """
        return self.data_dir / "database" / "haruquantai.db"

    @property
    def log_dir(self) -> Path:
        """Derive the host log directory without creating it.

        Returns:
            The logs child of the configured data directory.
        """
        return self.data_dir / "logs"


def load_settings(
    overrides: Mapping[str, Any] | None = None,
    *,
    environment: Mapping[str, str] | None = None,
) -> HostSettings:
    """Load a validated configuration without creating or migrating storage.

    Persisted password, private_key, and data_dir fields are forbidden. HARU_ROOTS
    and HARU_ORIGINS are not parsed as collection overrides. A missing database
    uses defaults and external overrides only.

    Args:
        overrides: Explicit field values, normally parsed CLI options; omitted values
            retain lower-precedence settings.
        environment: Environment mapping for deterministic callers; None reads
            os.environ.

    Returns:
        Frozen HostSettings with the selected data root.

    Raises:
        ValueError: Persisted JSON/version or the merged runtime configuration is
            invalid.
        HostPersistenceSchemaError: An existing settings database cannot be safely read.
    """
    env = os.environ if environment is None else environment
    explicit = dict(overrides or {})
    root = Path(explicit.get("data_dir", env.get("HARU_DATA_DIR", "data")))
    values: dict[str, Any] = {}
    path = root / "database" / "haruquantai.db"
    if path.exists():
        for record in read_settings(path):
            if record.scope == "host" and record.key == "runtime":
                if record.schema_version != 1:
                    raise ValueError("Unsupported runtime settings version")
                raw = json.loads(record.value_json)
                if not isinstance(raw, dict) or any(
                    k in raw
                    for k in (
                        "password",
                        "private_key",
                        "data_dir",
                        "source_credentials",
                    )
                ):
                    raise ValueError("Invalid persisted runtime configuration")
                values.update(raw)
    for name in HostSettings.model_fields:
        key = "HARU_" + name.upper()
        if key in env and name not in ("roots", "origins"):
            values[name] = (
                json.loads(env[key]) if name == "source_credentials" else env[key]
            )
    values.update(explicit)
    values["data_dir"] = root
    result = HostSettings.model_validate(values)
    logger.info("Runtime configuration validated")
    return result


class SettingsStore:
    """Read and patch public preferences through a prepared database capability.

    The instance retains only a path. Each operation opens its own short-lived
    persistence connection; no migration or connection lifecycle lives here.
    """

    def __init__(self, path: Path) -> None:
        """Retain the prepared storage location without opening it.

        Args:
            path: Unified database whose schema is initialized by the host.
        """
        self.path = path

    def snapshot(self) -> dict[str, Any]:
        """Load and validate one public settings snapshot.

        Storage access failures propagate. This method does not fill absent preference
        fields with defaults or write corrections back to the database.

        Returns:
            Mapping with integer revision and public values, excluding private records.

        Raises:
            SettingsError: Stored JSON, version, revision, or public field values are
                invalid.
        """
        try:
            snap = _public(settings_snapshot(self.path))
            logger.info(
                "Settings snapshot loaded: revision=%d",
                snap["revision"],
            )
            return snap
        except (ValueError, HostPersistenceValueError) as error:
            raise SettingsError("Malformed host settings") from error

    def mt5_terminal_configuration(self) -> MT5TerminalConfiguration:
        """Read current global terminal selection without exposing credentials.

        Raises:
            SettingsError: The saved record is absent or malformed.
        """
        record = HostStore(self.path).get_setting("application", "config.metatrader5")
        if record is None:
            raise SettingsError("MT5 global settings are missing")
        if record.schema_version != 1:
            raise SettingsError("Unsupported MT5 global settings version")
        value = _decode_record(record.value_json)
        enabled = value.get("enabled")
        terminal_path = value.get("terminal_path")
        portable = value.get("portable", False)
        if (
            type(enabled) is not bool
            or not isinstance(terminal_path, str)
            or type(portable) is not bool
        ):
            raise SettingsError("Invalid MT5 global terminal settings")
        logger.info("MT5 global terminal configuration read")
        return MT5TerminalConfiguration(enabled, terminal_path, portable)

    def patch(
        self,
        changes: dict[str, Any],
        expected_revision: int,
        *,
        bus: EventBus | None = None,
    ) -> dict[str, Any]:
        """Validate a field patch and publish its public result after commit.

        Persistence preserves unmodified private fields and rolls back validation
        failures. If event publication raises after commit, storage remains committed;
        the caller should reload rather than assuming rollback.

        Args:
            changes: Nonempty mapping of known records to nonempty public-field updates.
            expected_revision: Nonnegative integer revision from a previous snapshot.
            bus: Optional host event bus for a settings.changed notification.

        Returns:
            Committed public snapshot with its incremented revision.

        Raises:
            SettingsError: Patch structure, fields, or merged public values are invalid.
            SettingsConflictError: Another writer changed the expected revision.
        """
        if not changes or type(expected_revision) is not int or expected_revision < 0:
            raise SettingsError("Expected nonempty changes and revision")
        for key, fields in changes.items():
            if key not in PUBLIC_FIELDS or not isinstance(fields, dict) or not fields:
                raise SettingsError("Unknown or empty settings record")
            for field, value in fields.items():
                if not _valid_setting(key, field, value):
                    raise SettingsError("Unknown or invalid settings field")
        try:
            saved = _public(
                patch_settings(self.path, changes, expected_revision, _validate_values)
            )
        except HostPersistenceConflictError as error:
            raise SettingsConflictError("Settings changed; reload and retry") from error
        logger.info("Settings update published")
        if bus is not None:
            bus.publish(SETTINGS_CHANNEL, saved["values"])
        return saved

    def get_private(self, owner: str, key: str) -> dict[str, Any] | None:
        """Read an owner-scoped private settings record without public projection."""
        store = HostStore(self.path)
        record = store.get_setting(owner, key)
        if record is None:
            return None
        try:
            val = json.loads(record.value_json)
            return val if isinstance(val, dict) else None
        except TypeError, json.JSONDecodeError:
            return None

    def set_private(self, owner: str, key: str, value: dict[str, Any]) -> None:
        """Insert or replace an owner-scoped private settings record."""
        if not isinstance(value, dict):
            raise TypeError("Private settings record must be a dict")
        store = HostStore(self.path)
        store.upsert_setting(
            HostSettingRecord(
                scope=owner,
                key=key,
                value_json=json.dumps(value, allow_nan=False),
                schema_version=1,
                updated_at_utc=utc_now_iso(),
            )
        )
        logger.info("Private setting updated: owner=%s key=%s", owner, key)
