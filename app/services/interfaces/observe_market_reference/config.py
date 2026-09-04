"""Configuration model for the market reference gateway."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def from_dict(data: dict[str, Any] | None) -> ObserveMarketReferenceConfig:
    """Build a configuration from a mapping, rejecting unknown keys.

    Args:
        data: Configuration mapping or None for defaults.

    Returns:
        Parsed immutable configuration.

    Raises:
        ValueError: If an unknown key is present.
    """
    if not data:
        return ObserveMarketReferenceConfig()
    unknown = set(data)
    if unknown:
        message = "Unknown observe-market-reference configuration keys: " + ", ".join(
            sorted(unknown)
        )
        raise ValueError(message)
    return ObserveMarketReferenceConfig()


@dataclass(frozen=True, slots=True)
class ObserveMarketReferenceConfig:
    """Runtime configuration for FEAT-IFACE-OBSERVE_MARKET_REFERENCE."""
