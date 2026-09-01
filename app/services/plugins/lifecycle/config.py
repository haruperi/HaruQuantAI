"""Strict configuration for the Plugin Lifecycle feature."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

_ALLOWED_CONFIG_KEYS = frozenset({"database_path"})


@dataclass(frozen=True, slots=True)
class PluginLifecycleConfig:
    """Explicit database binding for lifecycle-owned durable state."""

    database_path: Path

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> PluginLifecycleConfig:
        """Parse the complete lifecycle configuration without filesystem access.

        Args:
            data: Raw feature configuration mapping.

        Returns:
            A validated immutable lifecycle configuration.

        Raises:
            TypeError: If ``database_path`` is not a string.
            ValueError: If the mapping is missing, malformed, or incomplete.
        """
        if data is None:
            raise ValueError("Plugin Lifecycle configuration requires database_path")

        unknown = set(data) - _ALLOWED_CONFIG_KEYS
        if unknown:
            raise ValueError(
                "Unknown Plugin Lifecycle configuration keys: "
                + ", ".join(sorted(unknown))
            )

        database_path = data.get("database_path")
        if not isinstance(database_path, str):
            raise TypeError("database_path must be a non-blank string")
        if not database_path.strip():
            raise ValueError("database_path must be a non-blank string")

        return cls(database_path=Path(database_path))
