"""Strict configuration for the market data observation gateway.

Purpose:
    Parse and validate the bounded configuration accepted by
    FEAT-IFACE-OBSERVE_MARKET_DATA.

Key capabilities:
    * Reject unknown configuration keys deterministically.
    * Bound snapshot staleness detection and the served symbol filter.

Python API usage:
    config = ObserveMarketDataConfig.from_dict({"stale_after_seconds": 2.5})

CLI usage:
    uv run python -m app.services.interfaces.observe_market_data.gateway
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

_ALLOWED_CONFIG_KEYS = frozenset({"stale_after_seconds", "max_symbols"})
_MAX_SYMBOLS = 200


def _positive_float(key: str, value: object, default: float) -> float:
    """Normalize an optional positive float.

    Args:
        key: Configuration key name used in error messages.
        value: Raw configuration value or None.
        default: Value returned when the key is absent.

    Returns:
        Validated float.

    Raises:
        TypeError: If the value is not a real number.
        ValueError: If the value is not positive.
    """
    if value is None:
        return default
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        message = f"{key} must be a number"
        raise TypeError(message)
    parsed = float(value)
    if parsed <= 0:
        message = f"{key} must be a positive number"
        raise ValueError(message)
    return parsed


def _bounded_int(key: str, value: object, default: int) -> int:
    """Normalize an optional integer within [1, 200].

    Args:
        key: Configuration key name used in error messages.
        value: Raw configuration value or None.
        default: Value returned when the key is absent.

    Returns:
        Validated integer.

    Raises:
        TypeError: If the value is not an integer.
        ValueError: If the value is outside the permitted range.
    """
    if value is None:
        return default
    if isinstance(value, bool) or not isinstance(value, int):
        message = f"{key} must be an integer"
        raise TypeError(message)
    if not 1 <= value <= _MAX_SYMBOLS:
        message = f"{key} must be between 1 and {_MAX_SYMBOLS}"
        raise ValueError(message)
    return value


@dataclass(frozen=True, slots=True)
class ObserveMarketDataConfig:
    """Runtime configuration for the market observation gateway.

    Attributes:
        stale_after_seconds: Seconds without provider events after which
            snapshots are reported stale.
        max_symbols: Maximum accepted symbol-filter size per request.
    """

    stale_after_seconds: float = 5.0
    max_symbols: int = 50

    def __post_init__(self) -> None:
        """Validate configuration limits.

        Raises:
            ValueError: If any value is outside its documented bound.
        """
        if self.stale_after_seconds <= 0:
            message = "stale_after_seconds must be a positive number"
            raise ValueError(message)
        if not 1 <= self.max_symbols <= _MAX_SYMBOLS:
            message = f"max_symbols must be between 1 and {_MAX_SYMBOLS}"
            raise ValueError(message)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> ObserveMarketDataConfig:
        """Build a configuration from a mapping, rejecting unknown keys.

        Args:
            data: Configuration mapping or None for defaults.

        Returns:
            Parsed immutable configuration.

        Raises:
            ValueError: If an unknown key or an out-of-range value is present.
            TypeError: If a value has an unexpected type.
        """
        if not data:
            return cls()
        unknown = set(data) - _ALLOWED_CONFIG_KEYS
        if unknown:
            message = "Unknown observe-market-data configuration keys: " + ", ".join(
                sorted(unknown)
            )
            raise ValueError(message)
        defaults = cls()
        return cls(
            stale_after_seconds=_positive_float(
                "stale_after_seconds",
                data.get("stale_after_seconds"),
                defaults.stale_after_seconds,
            ),
            max_symbols=_bounded_int(
                "max_symbols",
                data.get("max_symbols"),
                defaults.max_symbols,
            ),
        )
