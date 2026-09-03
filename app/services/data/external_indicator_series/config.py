"""Configuration for External Indicator Series feature."""

from __future__ import annotations

import re
import zoneinfo
from dataclasses import dataclass

_VALID_MISSING_POLICIES: frozenset[str] = frozenset(
    {"FORWARD_FILL", "ZERO_FILL", "REJECT", "NAN", "NONE"}
)

_IANA_AREAS: frozenset[str] = frozenset(
    {
        "Africa",
        "America",
        "Antarctica",
        "Arctic",
        "Asia",
        "Atlantic",
        "Australia",
        "Brazil",
        "Canada",
        "Chile",
        "Etc",
        "Europe",
        "Indian",
        "Mexico",
        "Pacific",
        "US",
    }
)


def _validate_timezone(name: str) -> None:
    """Validate that name is a recognized IANA timezone or valid fallback.

    Args:
        name: Timezone identifier string.

    Raises:
        ValueError: If name is not a valid timezone identifier.
    """
    if not name or not isinstance(name, str):
        msg = "Timezone identifier must be a non-empty string"
        raise ValueError(msg)
    if name in ("UTC", "GMT", "Etc/UTC", "Etc/GMT"):
        return
    try:
        zoneinfo.ZoneInfo(name)
        return
    except (
        zoneinfo.ZoneInfoNotFoundError,
        ModuleNotFoundError,
        ValueError,
        OSError,
        KeyError,
    ):
        area, _, rest = name.partition("/")
        if (
            area in _IANA_AREAS
            and rest
            and re.fullmatch(r"[A-Za-z0-9_+-]+(/[A-Za-z0-9_+-]+)*", rest)
        ):
            return
    msg = f"default_timezone '{name}' is not a valid IANA timezone"
    raise ValueError(msg)


@dataclass(frozen=True)
class ExternalIndicatorSeriesConfig:
    """Runtime configuration for External Indicator Series feature.

    Attributes:
        default_timezone: Default IANA timezone name for imported series
            timestamps.
        max_points_per_series: Maximum allowable points per imported
            indicator series.
        require_deterministic_reimport: Whether reimport must yield
            deterministic version hashes.
        allow_future_timestamps: Whether timestamps past decision point are
            permitted.
        default_missing_policy: Default missing-value alignment policy
            strategy.
    """

    default_timezone: str = "UTC"
    max_points_per_series: int = 1_000_000
    require_deterministic_reimport: bool = True
    allow_future_timestamps: bool = False
    default_missing_policy: str = "FORWARD_FILL"

    def __post_init__(self) -> None:
        """Validate configuration parameters.

        Raises:
            ValueError: If configuration values are out of bounds or invalid.
        """
        if self.max_points_per_series <= 0:
            msg = "max_points_per_series must be a positive integer"
            raise ValueError(msg)

        _validate_timezone(self.default_timezone)

        if self.default_missing_policy not in _VALID_MISSING_POLICIES:
            valid = sorted(_VALID_MISSING_POLICIES)
            msg = f"default_missing_policy must be one of {valid}"
            raise ValueError(msg)
