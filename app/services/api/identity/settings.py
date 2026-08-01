"""Versioned UI/API-owned user settings persistence."""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.services.api.identity.accounts import IdentityError, _execute
from app.utils import canonical_json, is_sensitive_key, utc_now

_MAX_SETTINGS = 32
_MAX_SETTING_KEY_LENGTH = 64
_MAX_SETTING_VALUE_LENGTH = 256


class UserSettingsRecord(BaseModel):
    """Bounded secret-free user presentation settings."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    user_id: str
    settings: Mapping[str, str]
    version: int
    updated_at: datetime

    @field_validator("settings", mode="before")
    @classmethod
    def _validate_settings(cls, value: object) -> Mapping[str, str]:
        """Validate bounded string-only settings without secret-like keys.

        Returns:
            Validated settings mapping.

        Raises:
            TypeError: If settings are not a mapping.
            ValueError: If settings are unsafe or unbounded.
        """
        if not isinstance(value, Mapping):
            raise TypeError("settings must be a mapping")
        if len(value) > _MAX_SETTINGS:
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


def get_user_settings(user_id: str, *, request_id: str) -> UserSettingsRecord:
    """Read one user's current settings.

    Args:
        user_id: Authenticated settings owner.
        request_id: Canonical operation request identifier.

    Returns:
        Persisted record or an empty version-zero record.
    """
    result = _execute(
        (
            "SELECT settings_json, version, updated_at FROM api_user_settings "
            "WHERE user_id = ?",
        ),
        ((user_id,),),
        request_id=request_id,
    )
    rows = tuple(result.rows)
    if not rows:
        return UserSettingsRecord(
            user_id=user_id,
            settings={},
            version=0,
            updated_at=utc_now(),
        )
    row = rows[0]
    return UserSettingsRecord(
        user_id=user_id,
        settings=json.loads(str(row["settings_json"])),
        version=int(str(row["version"])),
        updated_at=datetime.fromisoformat(str(row["updated_at"])),
    )


def update_user_settings(
    user_id: str,
    settings: Mapping[str, str],
    *,
    expected_version: int,
    request_id: str,
) -> UserSettingsRecord:
    """Replace user settings with optimistic version enforcement.

    Args:
        user_id: Authenticated settings owner.
        settings: Complete bounded presentation settings.
        expected_version: Current record version observed by the caller.
        request_id: Canonical operation request identifier.

    Returns:
        Updated record.

    Raises:
        IdentityError: If the version conflicts or persistence fails.
    """
    validated = UserSettingsRecord(
        user_id=user_id,
        settings=settings,
        version=expected_version + 1,
        updated_at=utc_now(),
    )
    current = get_user_settings(user_id, request_id=request_id)
    if current.version != expected_version:
        raise IdentityError("SETTINGS_VERSION_CONFLICT")
    serialized = canonical_json(dict(validated.settings))
    if expected_version == 0:
        statement = (
            "INSERT INTO api_user_settings "
            "(user_id, settings_json, version, updated_at) VALUES (?, ?, ?, ?)"
        )
        parameters: tuple[object, ...] = (
            user_id,
            serialized,
            validated.version,
            validated.updated_at.isoformat(),
        )
    else:
        statement = (
            "UPDATE api_user_settings SET settings_json = ?, version = ?, "
            "updated_at = ? WHERE user_id = ? AND version = ?"
        )
        parameters = (
            serialized,
            validated.version,
            validated.updated_at.isoformat(),
            user_id,
            expected_version,
        )
    result = _execute(
        (statement,),
        (parameters,),
        request_id=request_id,
    )
    if int(result.affected_rows) != 1:
        raise IdentityError("SETTINGS_VERSION_CONFLICT")
    return validated


__all__ = ("UserSettingsRecord", "get_user_settings", "update_user_settings")
