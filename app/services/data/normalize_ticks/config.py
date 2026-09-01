"""Strict configuration for tick normalization."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class NormalizeTicksConfig:
    """Trusted configuration for deterministic tick normalization."""

    @classmethod
    def from_dict(cls, values: dict[str, object]) -> NormalizeTicksConfig:
        """Reject all unknown configuration because the feature is parameter-free.

        Args:
            values: Raw feature configuration.

        Returns:
            Frozen configuration instance.

        Raises:
            ValueError: If any configuration key is supplied.
        """
        if values:
            raise ValueError(f"unknown config keys: {sorted(values)}")
        return cls()
