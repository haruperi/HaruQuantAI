"""Strict configuration for deterministic bar aggregation."""

from __future__ import annotations

from dataclasses import dataclass

_ALLOWED_KEYS = frozenset({"max_output_bars"})


@dataclass(frozen=True, slots=True)
class AggregateBarsConfig:
    """Trusted bounds for one aggregation request."""

    max_output_bars: int = 500_000

    @classmethod
    def from_dict(cls, values: dict[str, object]) -> AggregateBarsConfig:
        """Validate and normalize aggregation bounds.

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
        raw = values.get("max_output_bars", 500_000)
        if not isinstance(raw, int) or isinstance(raw, bool) or not 1 <= raw <= 2_000_000:
            raise ValueError("max_output_bars must be an integer in [1, 2000000]")
        return cls(max_output_bars=raw)
