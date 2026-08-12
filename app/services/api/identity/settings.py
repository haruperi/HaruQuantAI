"""Versioned UI/API-owned user and system settings persistence."""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.services.api.identity.errors import IdentityError
from app.services.api.identity.persistence import (
    create_settings_record,
    read_settings_record,
    update_settings_record,
)
from app.services.api.identity.system_settings import (
    get_system_settings_manifest,
    system_settings_require_restart,
    validate_system_settings,
)
from app.utils import canonical_json, is_sensitive_key, utc_now

_MAX_USER_SETTINGS = 32
_MAX_SYSTEM_SETTINGS = len(get_system_settings_manifest())
_MAX_SETTING_KEY_LENGTH = 64
_MAX_SETTING_VALUE_LENGTH = 256
_GLOBAL_SETTINGS_SUBJECT = "global"

type SettingsScope = Literal["system", "user"]


class SettingsRecord(BaseModel):
    """Bounded secret-free settings for one user or the global system scope."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    scope: SettingsScope
    subject_id: str
    user_id: str | None
    settings: Mapping[str, str]
    version: int
    created_at: datetime
    updated_at: datetime
    updated_by: str
    restart_required: bool = False

    @field_validator("settings", mode="before")
    @classmethod
    def _validate_settings(cls, value: object) -> Mapping[str, str]:
        """Validate bounded string-only settings without secret-like keys.

        Args:
            value: Candidate settings mapping.

        Returns:
            Validated settings mapping.

        Raises:
            TypeError: If settings are not a mapping of strings.
            ValueError: If settings are unsafe or unbounded.
        """
        if not isinstance(value, Mapping):
            raise TypeError("settings must be a mapping")
        if len(value) > max(_MAX_USER_SETTINGS, _MAX_SYSTEM_SETTINGS):
            raise ValueError("settings exceed maximum entries")
        result: dict[str, str] = {}
        for key, item in value.items():
            if not isinstance(key, str) or not isinstance(item, str):
                raise TypeError("settings keys and values must be strings")
            if (
                is_sensitive_key(key)
                or len(key) > _MAX_SETTING_KEY_LENGTH
                or len(item) > _MAX_SETTING_VALUE_LENGTH
            ):
                raise ValueError("settings contain an unsafe or oversized value")
            result[key] = item
        return result

    @model_validator(mode="after")
    def _validate_scoped_settings(self) -> SettingsRecord:
        """Apply the exact validator owned by the selected settings scope.

        Returns:
            Validated scoped record.

        Raises:
            ValueError: If user settings exceed their bounded entry count.
            IdentityError: If system settings are not manifest-approved.
        """
        if self.scope == "system":
            validate_system_settings(self.settings)
        elif len(self.settings) > _MAX_USER_SETTINGS:
            raise ValueError("user settings exceed maximum entries")
        return self


def _get_settings(
    scope: SettingsScope,
    subject_id: str,
    *,
    request_id: str,
) -> SettingsRecord:
    """Read one scoped settings document.

    Args:
        scope: Settings authority scope, system or user.
        subject_id: Global or authenticated-user settings subject.
        request_id: Canonical operation request identifier.

    Returns:
        Persisted record or an empty version-zero record.
    """
    rows = read_settings_record(scope, subject_id, request_id=request_id)
    if not rows:
        observed_at = utc_now()
        return SettingsRecord(
            scope=scope,
            subject_id=subject_id,
            user_id=subject_id if scope == "user" else None,
            settings={},
            version=0,
            created_at=observed_at,
            updated_at=observed_at,
            updated_by=subject_id,
        )
    row = rows[0]
    return SettingsRecord(
        scope=scope,
        subject_id=subject_id,
        user_id=subject_id if scope == "user" else None,
        settings=json.loads(str(row["settings_json"])),
        version=int(str(row["version"])),
        created_at=datetime.fromisoformat(str(row["created_at"])),
        updated_at=datetime.fromisoformat(str(row["updated_at"])),
        updated_by=str(row["updated_by"]),
    )


def get_user_settings(user_id: str, *, request_id: str) -> SettingsRecord:
    """Read one authenticated user's current settings.

    Args:
        user_id: Authenticated settings owner.
        request_id: Canonical operation request identifier.

    Returns:
        Persisted user settings or an empty version-zero record.
    """
    return _get_settings("user", user_id, request_id=request_id)


def get_system_settings(*, request_id: str) -> SettingsRecord:
    """Read the global non-secret system settings.

    Args:
        request_id: Canonical operation request identifier.

    Returns:
        Persisted system settings or an empty version-zero record.
    """
    return _get_settings(
        "system",
        _GLOBAL_SETTINGS_SUBJECT,
        request_id=request_id,
    )


def _update_settings(
    *,
    scope: SettingsScope,
    subject_id: str,
    actor_id: str,
    settings: Mapping[str, str],
    expected_version: int,
    request_id: str,
) -> SettingsRecord:
    """Replace one scoped settings document with optimistic locking.

    Args:
        scope: Settings authority scope, system or user.
        subject_id: Global or authenticated-user settings subject.
        actor_id: Authenticated actor responsible for the write.
        settings: Complete bounded settings document.
        expected_version: Current record version observed by the caller.
        request_id: Canonical operation request identifier.

    Returns:
        Updated scoped settings record.

    Raises:
        IdentityError: If the version conflicts or persistence fails.
        ValueError: If the actor identity is malformed.
    """
    if not actor_id or actor_id != actor_id.strip():
        raise ValueError("actor_id must be non-empty and trimmed")
    observed_at = utc_now()
    current = _get_settings(scope, subject_id, request_id=request_id)
    if current.version != expected_version:
        raise IdentityError("SETTINGS_VERSION_CONFLICT")
    validated_settings = (
        validate_system_settings(settings) if scope == "system" else settings
    )
    restart_required = scope == "system" and system_settings_require_restart(
        current.settings,
        validated_settings,
    )
    validated = SettingsRecord(
        scope=scope,
        subject_id=subject_id,
        user_id=subject_id if scope == "user" else None,
        settings=validated_settings,
        version=expected_version + 1,
        created_at=current.created_at if current.version else observed_at,
        updated_at=observed_at,
        updated_by=actor_id,
        restart_required=restart_required,
    )
    serialized = canonical_json(dict(validated.settings))
    if expected_version == 0:
        affected_rows = create_settings_record(
            scope=scope,
            subject_id=subject_id,
            settings_json=serialized,
            version=validated.version,
            created_at=validated.created_at.isoformat(),
            updated_at=validated.updated_at.isoformat(),
            updated_by=actor_id,
            request_id=request_id,
        )
    else:
        affected_rows = update_settings_record(
            scope=scope,
            subject_id=subject_id,
            settings_json=serialized,
            version=validated.version,
            updated_at=validated.updated_at.isoformat(),
            updated_by=actor_id,
            expected_version=expected_version,
            request_id=request_id,
        )
    if affected_rows != 1:
        raise IdentityError("SETTINGS_VERSION_CONFLICT")
    return validated


def update_user_settings(
    user_id: str,
    settings: Mapping[str, str],
    *,
    expected_version: int,
    request_id: str,
) -> SettingsRecord:
    """Replace one user's settings with optimistic version enforcement.

    Args:
        user_id: Authenticated settings owner.
        settings: Complete bounded presentation settings.
        expected_version: Current record version observed by the caller.
        request_id: Canonical operation request identifier.

    Returns:
        Updated user settings record.

    Raises:
        IdentityError: If the version conflicts or persistence fails.
    """
    return _update_settings(
        scope="user",
        subject_id=user_id,
        actor_id=user_id,
        settings=settings,
        expected_version=expected_version,
        request_id=request_id,
    )


def update_system_settings(
    settings: Mapping[str, str],
    *,
    actor_id: str,
    expected_version: int,
    request_id: str,
) -> SettingsRecord:
    """Replace global non-secret system settings with optimistic locking.

    Args:
        settings: Complete bounded system-settings document.
        actor_id: Authenticated administrator responsible for the write.
        expected_version: Current global settings version observed by the caller.
        request_id: Canonical operation request identifier.

    Returns:
        Updated global system settings.

    Raises:
        IdentityError: If the version conflicts or persistence fails.
        ValueError: If the actor identity is malformed.
    """
    return _update_settings(
        scope="system",
        subject_id=_GLOBAL_SETTINGS_SUBJECT,
        actor_id=actor_id,
        settings=settings,
        expected_version=expected_version,
        request_id=request_id,
    )


__all__ = (
    "SettingsRecord",
    "get_system_settings",
    "get_user_settings",
    "update_system_settings",
    "update_user_settings",
)
