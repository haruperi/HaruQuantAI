"""Post-bootstrap composition of database-backed runtime configuration."""

from __future__ import annotations

import base64
import binascii
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING

from app.services.api.identity import get_system_settings
from app.utils import get_logger

if TYPE_CHECKING:
    from app.services.api._settings import ApiSettings

logger = get_logger(__name__)
_CREDENTIAL_KEY_BYTES = 32


@dataclass(frozen=True, slots=True)
class _RuntimeSettingsSnapshot:
    """Internal immutable post-bootstrap configuration snapshot."""

    values: Mapping[str, str]
    version: int


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


__all__ = (
    "build_credential_key_set",
    "get_runtime_setting",
    "load_runtime_settings_snapshot",
)
