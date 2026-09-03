"""Configuration for Bar Aggregation and Timeframes feature."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BarAggregationConfig:
    """Runtime configuration for Bar Aggregation and Timeframes feature.

    Attributes:
        max_bars_per_request: Maximum allowed number of source bars per
            aggregation request.
        default_timezone: Default timezone string for bucket alignment
            when unspecified.
        allow_custom_timeframes: Whether non-standard custom timeframes
            are enabled.
    """

    max_bars_per_request: int = 100_000
    default_timezone: str = "UTC"
    allow_custom_timeframes: bool = True

    def __post_init__(self) -> None:
        """Validate configuration settings.

        Raises:
            ValueError: If settings are out of valid bounds.
        """
        if self.max_bars_per_request <= 0:
            msg = "max_bars_per_request must be a positive integer"
            raise ValueError(msg)
        if not self.default_timezone or not isinstance(self.default_timezone, str):
            msg = "default_timezone must be a non-empty string"
            raise ValueError(msg)
