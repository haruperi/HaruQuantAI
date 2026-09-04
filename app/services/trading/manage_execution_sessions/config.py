"""Strict configuration for the execution sessions feature.

Purpose:
    Parse and validate the bounded configuration accepted by
    FEAT-TRD-MANAGE_EXECUTION_SESSIONS.

Key capabilities:
    * Reject unknown configuration keys deterministically.
    * Carry the trading database path.

Python API usage:
    config = ManageExecutionSessionsConfig.from_dict({})
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

_ALLOWED_CONFIG_KEYS = frozenset({"database_path"})

_DEFAULT_DATABASE_PATH = (
    Path(__file__).resolve().parents[4] / "data" / "database" / "haruquantai.db"
)


def from_dict(data: dict[str, Any] | None) -> ManageExecutionSessionsConfig:
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
        return ManageExecutionSessionsConfig()
    unknown = set(data) - _ALLOWED_CONFIG_KEYS
    if unknown:
        message = "Unknown manage-execution-sessions configuration keys: " + ", ".join(
            sorted(unknown)
        )
        raise ValueError(message)
    database_path = data.get("database_path")
    if database_path is not None and not isinstance(database_path, str | Path):
        message = "database_path must be a string or Path"
        raise TypeError(message)
    return ManageExecutionSessionsConfig(
        database_path=(
            Path(database_path) if database_path is not None else _DEFAULT_DATABASE_PATH
        ),
    )


@dataclass(frozen=True, slots=True)
class ManageExecutionSessionsConfig:
    """Immutable runtime configuration for the execution sessions manager."""

    database_path: Path | str = _DEFAULT_DATABASE_PATH

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> ManageExecutionSessionsConfig:
        """Parse configuration mapping with strict key validation.

        Args:
            data: Raw configuration mapping.

        Returns:
            Validated ManageExecutionSessionsConfig instance.
        """
        return from_dict(data)
