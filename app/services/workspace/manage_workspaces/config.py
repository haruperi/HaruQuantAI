"""Strict configuration for workspace management."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

_ALLOWED_CONFIG_KEYS = frozenset(
    {
        "auto_migrate",
        "busy_timeout_seconds",
        "staged_grace_period_seconds",
        "max_manifest_files",
        "max_backup_bytes",
    }
)
MIN_BUSY_TIMEOUT_SECONDS = 0.1
MAX_BUSY_TIMEOUT_SECONDS = 60.0
MAX_STAGED_GRACE_SECONDS = 31_536_000.0
MAX_MANIFEST_FILES = 100_000
MAX_BACKUP_BYTES = 1024**4


@dataclass(frozen=True, slots=True)
class ManageWorkspacesConfig:
    """Bounded runtime policy for workspace lifecycle operations."""

    auto_migrate: bool = True
    busy_timeout_seconds: float = 5.0
    staged_grace_period_seconds: float = 86400.0
    max_manifest_files: int = 10_000
    max_backup_bytes: int = 10 * 1024 * 1024 * 1024


def from_dict(  # noqa: C901 - one strict parser owns all five bounded keys.
    data: dict[str, Any] | None,
) -> ManageWorkspacesConfig:
    """Parse configuration and reject unknown, wrong-type, or unsafe values.

    Returns:
        A validated immutable configuration.

    Raises:
        TypeError: If a value has the wrong exact type.
        ValueError: If a key is unknown or a value exceeds its safe bound.
    """
    if not data:
        return ManageWorkspacesConfig()
    unknown = set(data) - _ALLOWED_CONFIG_KEYS
    if unknown:
        raise ValueError(
            "Unknown manage-workspaces configuration keys: "
            + ", ".join(sorted(unknown))
        )
    defaults = ManageWorkspacesConfig()
    auto_migrate = data.get("auto_migrate", defaults.auto_migrate)
    busy_timeout = data.get("busy_timeout_seconds", defaults.busy_timeout_seconds)
    grace = data.get(
        "staged_grace_period_seconds", defaults.staged_grace_period_seconds
    )
    max_files = data.get("max_manifest_files", defaults.max_manifest_files)
    max_bytes = data.get("max_backup_bytes", defaults.max_backup_bytes)
    if not isinstance(auto_migrate, bool):
        raise TypeError("auto_migrate must be a boolean")
    if not isinstance(busy_timeout, int | float) or isinstance(busy_timeout, bool):
        raise TypeError("busy_timeout_seconds must be numeric")
    if not isinstance(grace, int | float) or isinstance(grace, bool):
        raise TypeError("staged_grace_period_seconds must be numeric")
    if not isinstance(max_files, int) or isinstance(max_files, bool):
        raise TypeError("max_manifest_files must be an integer")
    if not isinstance(max_bytes, int) or isinstance(max_bytes, bool):
        raise TypeError("max_backup_bytes must be an integer")
    if not MIN_BUSY_TIMEOUT_SECONDS <= float(busy_timeout) <= MAX_BUSY_TIMEOUT_SECONDS:
        raise ValueError("busy_timeout_seconds must be between 0.1 and 60")
    if not 0.0 <= float(grace) <= MAX_STAGED_GRACE_SECONDS:
        raise ValueError("staged_grace_period_seconds must be between 0 and 31536000")
    if not 1 <= max_files <= MAX_MANIFEST_FILES:
        raise ValueError("max_manifest_files must be between 1 and 100000")
    if not 1 <= max_bytes <= MAX_BACKUP_BYTES:
        raise ValueError("max_backup_bytes must be between 1 and 1099511627776")
    return ManageWorkspacesConfig(
        auto_migrate=auto_migrate,
        busy_timeout_seconds=float(busy_timeout),
        staged_grace_period_seconds=float(grace),
        max_manifest_files=max_files,
        max_backup_bytes=max_bytes,
    )
