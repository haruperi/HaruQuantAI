"""Post-bootstrap composition of database-backed runtime configuration."""

from __future__ import annotations

import base64
import binascii
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, TypedDict

from app.composition.config import load_broker_provider_settings, load_settings
from app.composition.logging import configure_logging, get_logger
from app.kernel.identity import derive_stable_id
from app.services.api.identity import (
    get_system_settings,
    resolve_credential_reference,
)

if TYPE_CHECKING:
    from app.services.api.widgets.settings.bootstrap import ApiSettings

logger = get_logger(__name__)
_CREDENTIAL_KEY_BYTES = 32
_LOG_LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})
_PROVIDER_SETTING_FIELDS = MappingProxyType(
    {
        "MT5_ENABLED": "mt5_enabled",
        "MT5_TERMINAL_PATH": "mt5_terminal_path",
        "CTRADER_ENABLED": "ctrader_enabled",
        "BINANCE_ENABLED": "binance_enabled",
        "DUKASCOPY_ENABLED": "dukascopy_enabled",
        "YAHOO_ENABLED": "yahoo_enabled",
    }
)

# Data source identifier -> `BrokerProviderSettings` enabled-flag attribute.
# Mirrors Data's own provider capability keys (`app/services/data/sources/
# composition.py::_PROVIDER_CAPABILITIES`) so a source only enters Data's
# `data_provider_sources` allowlist once its DB-backed `*_ENABLED` flag is on.
_DATA_SOURCE_ENABLED_FIELDS = MappingProxyType(
    {
        "mt5": "mt5_enabled",
        "ctrader": "ctrader_enabled",
        "binance_spot": "binance_enabled",
        "dukascopy": "dukascopy_enabled",
        "yahoo": "yahoo_enabled",
    }
)


@dataclass(frozen=True, slots=True)
class _RuntimeSettingsSnapshot:
    """Internal immutable post-bootstrap configuration snapshot."""

    values: Mapping[str, str]
    version: int


class _Mt5SnapshotGatewayConfig(TypedDict):
    """Typed in-memory configuration passed to the Brokers listener."""

    host: str
    port: int
    auth_token: str
    source_id: str
    interval_seconds: int
    symbols: tuple[str, ...]
    log_snapshots: bool


def build_credential_key_set(settings: ApiSettings) -> Mapping[str, bytes]:
    """Decode the externally provisioned credential-encryption key.

    Args:
        settings: Validated bootstrap API settings.

    Returns:
        Immutable active key mapping, or an empty mapping when not provisioned.

    Raises:
        ValueError: If provisioned key material is malformed or not 256 bits.
    """
    if settings.credential_encryption_key is None:
        return MappingProxyType({})
    if settings.active_credential_key_id is None:
        raise ValueError("active credential key ID is required")
    encoded = settings.credential_encryption_key.get_secret_value()
    try:
        key = base64.b64decode(
            encoded.encode("ascii"),
            altchars=b"-_",
            validate=True,
        )
    except (binascii.Error, UnicodeEncodeError) as error:
        raise ValueError("credential encryption key must be URL-safe base64") from error
    if len(key) != _CREDENTIAL_KEY_BYTES:
        raise ValueError("credential encryption key must decode to exactly 32 bytes")
    return MappingProxyType({settings.active_credential_key_id: key})


def load_runtime_settings_snapshot(*, request_id: str) -> object:
    """Load the validated global settings record after storage initialization.

    Args:
        request_id: Canonical startup request identifier.

    Returns:
        Internal immutable runtime settings snapshot.
    """
    logger.info("Loading database-backed system settings snapshot")
    record = get_system_settings(request_id=request_id)
    return _RuntimeSettingsSnapshot(
        values=MappingProxyType(dict(record.settings)),
        version=record.version,
    )


def activate_runtime_logging(snapshot: object) -> None:
    """Activate the validated database-backed logging level.

    The API composition root calls this only after migrations and the global
    settings snapshot are available. Utils remains responsible for logging
    mechanics and has no persistence dependency.

    Args:
        snapshot: Snapshot created by ``load_runtime_settings_snapshot``.

    Raises:
        TypeError: If the snapshot did not originate from this module.
        ValueError: If the persisted logging level is invalid.
        ConfigurationError: If the logging sinks cannot be configured.
    """
    level = get_runtime_setting(snapshot, "LOG_LEVEL", "INFO")
    if level not in _LOG_LEVELS:
        raise ValueError("LOG_LEVEL_INVALID")
    logging_settings = load_settings({"LOG_LEVEL": level}, {}).logging
    configure_logging(logging_settings)
    logger.info("Activated database-backed logging configuration")


def build_runtime_provider_settings(snapshot: object) -> object:
    """Build opaque provider settings from the global runtime snapshot.

    Args:
        snapshot: Snapshot created by ``load_runtime_settings_snapshot``.

    Returns:
        Immutable provider settings validated by the Utils public boundary.

    Raises:
        TypeError: If the snapshot did not originate from this module.
        ConfigurationError: If a persisted provider value is invalid.
    """
    if not isinstance(snapshot, _RuntimeSettingsSnapshot):
        raise TypeError("runtime settings snapshot is invalid")
    explicit_values = {
        field: snapshot.values[key]
        for key, field in _PROVIDER_SETTING_FIELDS.items()
        if key in snapshot.values
    }
    return load_broker_provider_settings(explicit_values)


def build_runtime_data_provider_sources(provider_settings: object) -> tuple[str, ...]:
    """Derive the Data provider-source allowlist from enabled broker flags.

    Completes the composition-root wiring so a Data source composes only once
    its DB-backed platform flag (``MT5_ENABLED``, etc.) is enabled, matching
    the same settings the System Settings UI edits.

    Args:
        provider_settings: Immutable provider settings from
            ``build_runtime_provider_settings``.

    Returns:
        Sorted source identifiers whose platform flag is enabled.
    """
    return tuple(
        sorted(
            source_id
            for source_id, field in _DATA_SOURCE_ENABLED_FIELDS.items()
            if getattr(provider_settings, field, False)
        )
    )


def get_runtime_setting(
    snapshot: object,
    key: str,
    default: str | None = None,
) -> str | None:
    """Read one value from an opaque runtime snapshot.

    Args:
        snapshot: Snapshot created by ``load_runtime_settings_snapshot``.
        key: Canonical system setting key.
        default: Value returned when the setting is absent.

    Returns:
        Persisted value or the supplied default.

    Raises:
        TypeError: If the snapshot did not originate from this module.
    """
    if not isinstance(snapshot, _RuntimeSettingsSnapshot):
        raise TypeError("runtime settings snapshot is invalid")
    return snapshot.values.get(key, default)


def build_runtime_mt5_snapshot_gateway_config(
    snapshot: object,
    *,
    key_set: Mapping[str, bytes],
    request_id: str,
) -> _Mt5SnapshotGatewayConfig | None:
    """Build the authenticated MT5 snapshot listener configuration.

    Args:
        snapshot: Snapshot created by ``load_runtime_settings_snapshot``.
        key_set: Externally provisioned credential-decryption keys.
        request_id: Canonical startup request identifier.

    Returns:
        Validated configuration values, or ``None`` when not configured.

    Raises:
        IdentityError: If encrypted credential resolution fails.
        TypeError: If the runtime snapshot is invalid.
        ValueError: If persisted bootstrap-symbol configuration is invalid.
    """
    if not isinstance(snapshot, _RuntimeSettingsSnapshot):
        raise TypeError("runtime settings snapshot is invalid")
    required = {
        "host": snapshot.values.get("MT5_SNAPSHOT_HOST"),
        "port": snapshot.values.get("MT5_SNAPSHOT_PORT"),
        "interval_seconds": snapshot.values.get("MT5_SNAPSHOT_INTERVAL_SECONDS"),
        "source_id": snapshot.values.get("MT5_SNAPSHOT_SOURCE_ID"),
        "symbols": snapshot.values.get("MT5_SNAPSHOT_SYMBOLS"),
    }
    if not any(required.values()):
        return None
    if any(value is None for value in required.values()):
        raise ValueError("MT5 snapshot gateway settings are incomplete")
    symbols = tuple(symbol.strip() for symbol in str(required["symbols"]).split(","))
    if not symbols or any(not symbol for symbol in symbols):
        raise ValueError("MT5 snapshot symbols are invalid")
    reference_id = derive_stable_id(
        "id",
        "api-credential:system:mt5_snapshot_bridge",
    )
    material = resolve_credential_reference(
        f"secret://{reference_id}",
        owner_id="system",
        key_set=key_set,
        request_id=request_id,
    )
    token = material.get("auth_token")
    if token is None:
        raise ValueError("MT5 snapshot credential is incomplete")
    return _Mt5SnapshotGatewayConfig(
        host=str(required["host"]),
        port=int(str(required["port"])),
        auth_token=token.get_secret_value(),
        source_id=str(required["source_id"]),
        interval_seconds=int(str(required["interval_seconds"])),
        symbols=symbols,
        log_snapshots=snapshot.values.get(
            "MT5_SNAPSHOT_LOG_SNAPSHOTS",
            "false",
        )
        == "true",
    )


__all__ = (
    "activate_runtime_logging",
    "build_credential_key_set",
    "build_runtime_data_provider_sources",
    "build_runtime_mt5_snapshot_gateway_config",
    "build_runtime_provider_settings",
    "get_runtime_setting",
    "load_runtime_settings_snapshot",
)
