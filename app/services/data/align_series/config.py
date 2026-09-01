"""Strict configuration for point-in-time series alignment."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AlignSeriesConfig:
    """Trusted configuration for external-series alignment."""

    @classmethod
    def from_dict(cls, values: dict[str, object]) -> AlignSeriesConfig:
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
