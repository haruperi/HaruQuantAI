"""Configuration for External Series Alignment feature."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExternalSeriesAlignmentConfig:
    """Runtime configuration for External Series Alignment feature.

    Attributes:
        max_series_points_per_request: Maximum allowed number of points per
            alignment request.
        default_timezone: Default timezone string when unspecified.
        default_max_age_seconds: Default maximum lookback age in seconds.
        default_missing_policy: Default missing value policy (NULL,
            CARRY_FORWARD, FAIL).
    """

    max_series_points_per_request: int = 100_000
    default_timezone: str = "UTC"
    default_max_age_seconds: int = 86_400
    default_missing_policy: str = "NULL"

    def __post_init__(self) -> None:
        """Validate configuration settings.

        Raises:
            ValueError: If settings are out of valid bounds.
        """
        if self.max_series_points_per_request <= 0:
            msg = "max_series_points_per_request must be a positive integer"
            raise ValueError(msg)
        if not self.default_timezone or not isinstance(self.default_timezone, str):
            msg = "default_timezone must be a non-empty string"
            raise ValueError(msg)
        if self.default_max_age_seconds <= 0:
            msg = "default_max_age_seconds must be a positive integer"
            raise ValueError(msg)
        if self.default_missing_policy not in ("NULL", "CARRY_FORWARD", "FAIL"):
            msg = "default_missing_policy must be one of: NULL, CARRY_FORWARD, FAIL"
            raise ValueError(msg)
