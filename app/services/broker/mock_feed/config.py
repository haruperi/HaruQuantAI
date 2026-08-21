"""Configuration validation for Mock Broker Feed."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class MockFeedConfig:
    """Configuration options for deterministic synthetic market data."""

    base_price: float = 1.1000

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> MockFeedConfig:
        """Parse and validate configuration dictionary."""
        if not data:
            return cls()
        base_price = float(data.get("base_price", 1.1000))
        if base_price <= 0:
            msg = f"base_price must be positive, got {base_price}"
            raise ValueError(msg)
        return cls(base_price=base_price)
