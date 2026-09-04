"""Strict configuration for the system settings feature.

Purpose:
    Parse and validate the bounded configuration accepted by
    FEAT-WS-ADMINISTER_SETTINGS.

Key capabilities:
    * Reject unknown configuration keys deterministically.
    * Carry the shared workspace database path.

Python API usage:
    config = AdministerSettingsConfig.from_dict({})
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

_ALLOWED_CONFIG_KEYS = frozenset({"database_path"})

_DEFAULT_DATABASE_PATH = (
    Path(__file__).resolve().parents[4] / "data" / "database" / "haruquantai.db"
)


def from_dict(data: dict[str, Any] | None) -> AdministerSettingsConfig:
    """Build a configuration from a mapping, rejecting unknown keys.

    Args:
        data: Configuration mapping or None for defaults.

    Returns:
        Parsed immutable configuration.

    Raises:
        ValueError: If an unknown key is present.
        TypeError: If a value has an unexpected type.
    """
    if not data:
        return AdministerSettingsConfig()
    unknown = set(data) - _ALLOWED_CONFIG_KEYS
    if unknown:
        message = "Unknown administer-settings configuration keys: " + ", ".join(
            sorted(unknown)
        )
        raise ValueError(message)
    database_path = data.get("database_path")
    if database_path is not None and not isinstance(database_path, str | Path):
        message = "database_path must be a string or Path"
        raise TypeError(message)
    return AdministerSettingsConfig(
        database_path=(
            Path(database_path) if database_path is not None else _DEFAULT_DATABASE_PATH
        ),
    )


@dataclass(frozen=True, slots=True)
class AdministerSettingsConfig:
    """Runtime configuration for the system settings feature.

    Attributes:
        database_path: Shared workspace SQLite database path holding the
            ``settings`` and ``settings_history`` tables.
    """

    database_path: Path | None = None
