"""Strict configuration for external indicator-series import."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ImportIndicatorsConfig:
    """Trusted configuration for indicator imports."""

    @classmethod
    def from_dict(cls, values: dict[str, object]) -> ImportIndicatorsConfig:
        """Reject unsupported configuration.

        Args:
            values: Raw feature configuration.

        Returns:
            Empty trusted configuration.

        Raises:
            ValueError: If any configuration key is supplied.
        """
        if values:
            raise ValueError(f"unknown config keys: {sorted(values)}")
        return cls()
