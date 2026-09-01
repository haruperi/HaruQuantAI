"""Strict configuration for volume-profile source preparation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PrepareProfilesConfig:
    """Parameter-free trusted feature configuration."""

    @classmethod
    def from_dict(cls, values: dict[str, object]) -> PrepareProfilesConfig:
        """Reject unknown configuration keys.

        Args:
            values: Raw feature configuration.

        Returns:
            Frozen configuration instance.

        Raises:
            ValueError: If any key is supplied.
        """
        if values:
            raise ValueError(f"unknown config keys: {sorted(values)}")
        return cls()
