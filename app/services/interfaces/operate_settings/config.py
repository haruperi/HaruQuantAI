"""Strict configuration for the system settings gateway.

Purpose:
    Parse and validate the bounded configuration accepted by
    FEAT-IFACE-OPERATE_SETTINGS.

Key capabilities:
    * Reject unknown configuration keys deterministically.

Python API usage:
    config = from_dict({})

CLI usage:
    uv run python -m app.services.interfaces.operate_settings.gateway
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

_ALLOWED_CONFIG_KEYS: frozenset[str] = frozenset()


def from_dict(data: dict[str, Any] | None) -> OperateSettingsConfig:
    """Build a configuration from a mapping, rejecting unknown keys.

    Args:
        data: Configuration mapping or None for defaults.

    Returns:
        Parsed immutable configuration.

    Raises:
        ValueError: If an unknown key is present.
    """
    if not data:
        return OperateSettingsConfig()
    unknown = set(data) - _ALLOWED_CONFIG_KEYS
    if unknown:
        message = "Unknown operate-settings configuration keys: " + ", ".join(
            sorted(unknown)
        )
        raise ValueError(message)
    return OperateSettingsConfig()


@dataclass(frozen=True, slots=True)
class OperateSettingsConfig:
    """Runtime configuration for the settings gateway."""
