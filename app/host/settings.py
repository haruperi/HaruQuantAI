"""Project stored settings into the host's explicitly public field schema.

SettingsStore delegates all SQL and revision updates to persistence. This layer
validates allowed records/fields and strips private values from responses/events.
A patch merges fields transactionally and publishes only after commit. These
settings describe host preferences; changing them does not implement missing
research engines or apply arbitrary runtime configuration changes.
"""

import json
import math
from pathlib import Path
from typing import Any

from app.host.events import SETTINGS_CHANNEL, EventBus
from app.host.logging import get_logger
from app.persistence.host import (
    HostPersistenceConflictError,
    HostPersistenceValueError,
    HostSettingRecord,
    HostStore,
    patch_settings,
    settings_snapshot,
    utc_now_iso,
)

logger = get_logger(__name__)


class SettingsError(ValueError):
    """The public settings projection is malformed or unsupported."""


class SettingsConflictError(SettingsError):
    """A concurrent writer changed the expected revision."""


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
    """Check primitive field types without treating booleans as numbers.

    Numbers must be finite. Intervals accept None or nonnegative integers; narrower
    allowed-value restrictions are applied by _valid_setting.

    Args:
        value: Candidate decoded JSON value.
        kind: Schema kind: str, bool, int, number, or interval.

    Returns:
        True for matching values; unknown kinds return False.
    """
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
            return _public(settings_snapshot(self.path))
        except (ValueError, HostPersistenceValueError) as error:
            raise SettingsError("Malformed host settings") from error

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
