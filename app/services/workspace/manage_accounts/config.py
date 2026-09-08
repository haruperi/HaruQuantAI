"""Strict configuration for the account registry feature.

Purpose:
    Parse and validate the bounded configuration accepted by
    FEAT-WS-MANAGE_ACCOUNTS.

Key capabilities:
    * Reject unknown configuration keys deterministically.
    * Carry the shared workspace database path.

Python API usage:
    config = ManageAccountsConfig.from_dict({})
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

_ALLOWED_CONFIG_KEYS = frozenset({"database_path"})

_DEFAULT_DATABASE_PATH = (
    Path(__file__).resolve().parents[4] / "data" / "database" / "haruquantai.db"
)


def from_dict(data: dict[str, Any] | None) -> ManageAccountsConfig:
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
        return ManageAccountsConfig()
    unknown = set(data) - _ALLOWED_CONFIG_KEYS
    if unknown:
        message = "Unknown manage-accounts configuration keys: " + ", ".join(
            sorted(unknown)
        )
        raise ValueError(message)
    database_path = data.get("database_path")
    if database_path is not None and not isinstance(database_path, str | Path):
        message = "database_path must be a string or Path"
        raise TypeError(message)
    return ManageAccountsConfig(
        database_path=(
            Path(database_path) if database_path is not None else _DEFAULT_DATABASE_PATH
        ),
    )


@dataclass(frozen=True, slots=True)
class ManageAccountsConfig:
    """Runtime configuration for the account registry feature.

    Attributes:
        database_path: Shared workspace SQLite database path holding the
            ``users`` and ``user_sessions`` tables.
    """

    database_path: Path = _DEFAULT_DATABASE_PATH

    def __post_init__(self) -> None:
        """Validate the compatibility path without granting raw-file access.

        Raises:
            TypeError: If ``database_path`` is not a Path.
            ValueError: If a database file is not the canonical database file.
        """
        if not isinstance(self.database_path, Path):
            raise TypeError("database_path must be a Path")
        if self.database_path.suffix and self.database_path.name != "haruquantai.db":
            raise ValueError(
                "database_path must name haruquantai.db or a database directory"
            )

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> ManageAccountsConfig:
        """Build a strict configuration from a mapping.

        Args:
            data: Configuration mapping or None.

        Returns:
            Validated immutable configuration.
        """
        return from_dict(data)

    @property
    def workspace_path(self) -> Path:
        """Return the canonical database path used by persistence.

        Returns:
            Central database path or directory.
        """
        return self.database_path
