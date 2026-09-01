"""Strict configuration for synthetic/scenario generation."""

from __future__ import annotations

from dataclasses import dataclass

_ALLOWED_KEYS = frozenset({"max_points"})


@dataclass(frozen=True, slots=True)
class GenerateScenariosConfig:
    """Trusted bounded generation configuration."""

    max_points: int = 100_000

    @classmethod
    def from_dict(cls, values: dict[str, object]) -> GenerateScenariosConfig:
        """Validate and normalize generation bounds.

        Args:
            values: Raw feature configuration.

        Returns:
            Frozen validated configuration.

        Raises:
            ValueError: If keys or bounds are invalid.
        """
        unknown = set(values) - _ALLOWED_KEYS
        if unknown:
            raise ValueError(f"unknown config keys: {sorted(unknown)}")
        raw = values.get("max_points", 100_000)
        if not isinstance(raw, int) or isinstance(raw, bool) or not 1 <= raw <= 1_000_000:
            raise ValueError("max_points must be an integer in [1, 1000000]")
        return cls(max_points=raw)
