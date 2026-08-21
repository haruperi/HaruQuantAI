"""Configuration validation for Mock Broker Feed."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

_ALLOWED_CONFIG_KEYS = frozenset({"base_price"})


@dataclass(frozen=True, slots=True)
class MockFeedConfig:
    """Configuration for deterministic synthetic bar generation."""

    base_price: float = 1.1000

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> MockFeedConfig:
        """Parse and validate a strict mock-feed configuration mapping.

        Returns:
            Validated mock-feed configuration.

        Raises:
            ValueError: If a field is unknown or invalid.
        """
        if not data:
            return cls()
        unknown = set(data) - _ALLOWED_CONFIG_KEYS
        if unknown:
            raise ValueError(
                "Unknown Mock Feed configuration keys: " + ", ".join(sorted(unknown))
            )
        base_price = float(data.get("base_price", 1.1000))
        if base_price <= 0:
            msg = f"base_price must be positive, got {base_price}"
            raise ValueError(msg)
        return cls(base_price=base_price)
