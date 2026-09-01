"""Strict configuration for plugin development compatibility."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class DevelopmentCompatibilityConfig:
    """Empty, explicit configuration schema for the feature."""

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> DevelopmentCompatibilityConfig:
        """Validate the feature's intentionally empty configuration schema.

        Args:
            data: Raw configuration mapping, if configured.

        Returns:
            A validated empty configuration instance.

        Raises:
            TypeError: If configuration is not a mapping.
            ValueError: If any configuration key is supplied.
        """
        if data is None:
            return cls()
        if not isinstance(data, dict):
            raise TypeError("Development Compatibility configuration must be a mapping")
        if data:
            joined = ", ".join(sorted(str(key) for key in data))
            raise ValueError(
                "Development Compatibility accepts no configuration keys: " + joined
            )
        return cls()
