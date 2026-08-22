"""Configuration validation for Historical Bars."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

VALID_TIMEFRAMES: frozenset[str] = frozenset(
    {"M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1", "MN1"}
)
_ALLOWED_CONFIG_KEYS = frozenset({"default_timeframe"})


@dataclass(frozen=True, slots=True)
class HistoricalBarsConfig:
    """Configuration options for historical-bar retrieval."""

    default_timeframe: str = "M1"

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> HistoricalBarsConfig:
        """Parse and validate a strict historical-bars configuration mapping.

        Returns:
            Validated historical-bars configuration.

        Raises:
            ValueError: If a field is unknown or invalid.
        """
        if not data:
            return cls()
        unknown = set(data) - _ALLOWED_CONFIG_KEYS
        if unknown:
            raise ValueError(
                "Unknown Historical Bars configuration keys: "
                + ", ".join(sorted(unknown))
            )
        timeframe = str(data.get("default_timeframe", "M1")).upper()
        if timeframe not in VALID_TIMEFRAMES:
            msg = (
                f"Unsupported default_timeframe: '{timeframe}'. "
                f"Allowed: {sorted(VALID_TIMEFRAMES)}"
            )
            raise ValueError(msg)
        return cls(default_timeframe=timeframe)
