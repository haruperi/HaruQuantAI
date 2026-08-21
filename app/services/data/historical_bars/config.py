"""Configuration validation for Historical Bars feature."""

from dataclasses import dataclass
from typing import Any

VALID_TIMEFRAMES: frozenset[str] = frozenset(
    {"M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1", "MN1"}
)


@dataclass(frozen=True, slots=True)
class HistoricalBarsConfig:
    """Configuration options for historical bars retrieval.

    Satisfies:
        FR-DATA-VALIDATE_CONFIG: Validates default timeframe and caching parameters.

    Attributes:
        default_timeframe: Default fallback timeframe interval.
        cache_enabled: Whether to attempt local caching when cache capability exists.
    """

    default_timeframe: str = "M1"
    cache_enabled: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> HistoricalBarsConfig:
        """Parse and validate configuration dictionary.

        Args:
            data: Raw dictionary from application configuration.

        Returns:
            Validated HistoricalBarsConfig instance.

        Raises:
            ValueError: If timeframe is not supported.
        """
        if not data:
            return cls()

        tf = str(data.get("default_timeframe", "M1")).upper()
        if tf not in VALID_TIMEFRAMES:
            allowed = sorted(VALID_TIMEFRAMES)
            msg = f"Unsupported default_timeframe: '{tf}'. Allowed: {allowed}"
            raise ValueError(msg)

        cache_on = bool(data.get("cache_enabled", True))
        return cls(default_timeframe=tf, cache_enabled=cache_on)
