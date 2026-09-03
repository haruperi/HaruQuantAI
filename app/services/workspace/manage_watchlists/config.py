"""Strict configuration for the manage-watchlists feature.

Purpose:
    Parse and validate the bounded configuration accepted by
    FEAT-WS-MANAGE_WATCHLISTS.

Key capabilities:
    * Reject unknown configuration keys deterministically.
    * Bound the database location and default-account identity.

Python API usage:
    config = ManageWatchlistsConfig.from_dict({"database_path": "x.db"})

CLI usage:
    uv run python -m app.services.workspace.manage_watchlists.manage_watchlists
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

_ALLOWED_CONFIG_KEYS = frozenset(
    {"database_path", "auto_migrate", "default_account_id"}
)


@dataclass(frozen=True, slots=True)
class ManageWatchlistsConfig:
    """Runtime configuration for the manage-watchlists feature.

    Attributes:
        database_path: SQLite database file; None uses a private
            in-memory database (tests and ephemeral runs).
        auto_migrate: Create/verify the schema on mount.
        default_account_id: The standalone local account every operation
            applies to until the identity boundary (gap G2) is ratified.
    """

    database_path: str | None = None
    auto_migrate: bool = True
    default_account_id: str = "local"


def from_dict(data: dict[str, Any] | None) -> ManageWatchlistsConfig:
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
        return ManageWatchlistsConfig()
    unknown = set(data) - _ALLOWED_CONFIG_KEYS
    if unknown:
        message = "Unknown manage-watchlists configuration keys: " + ", ".join(
            sorted(unknown)
        )
        raise ValueError(message)
    database_path = data.get("database_path")
    if database_path is not None and not isinstance(database_path, str):
        message = "database_path must be a string"
        raise TypeError(message)
    auto_migrate = data.get("auto_migrate")
    if auto_migrate is not None and not isinstance(auto_migrate, bool):
        message = "auto_migrate must be a boolean"
        raise TypeError(message)
    default_account_id = data.get("default_account_id")
    if default_account_id is not None and (
        not isinstance(default_account_id, str) or not default_account_id.strip()
    ):
        message = "default_account_id must be a non-empty string"
        raise TypeError(message)
    return ManageWatchlistsConfig(
        database_path=database_path,
        auto_migrate=True if auto_migrate is None else auto_migrate,
        default_account_id=(
            default_account_id if default_account_id is not None else "local"
        ),
    )
