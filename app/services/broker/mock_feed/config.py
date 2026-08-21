"""Configuration validation for Mock Broker Feed."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class MockFeedConfig:
    """Configuration options for mock broker feed.

    Satisfies:
        FR-BROKER-VALIDATE_FEED_CONFIG: Validates base price and spread constraints.

    Attributes:
        base_price: Base price level for synthetic bar generation.
        spread: Simulated bid-ask spread offset.
    """

    base_price: float = 1.1000
    spread: float = 0.0002

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> MockFeedConfig:
        """Parse and validate configuration dictionary.

        Args:
            data: Raw dictionary from application configuration.

        Returns:
            Validated MockFeedConfig instance.

        Raises:
            ValueError: If values are out of allowable bounds.
        """
        if not data:
            return cls()

        base = float(data.get("base_price", 1.1000))
        spread = float(data.get("spread", 0.0002))

        if base <= 0:
            msg = f"base_price must be positive, got {base}"
            raise ValueError(msg)
        if spread < 0:
            msg = f"spread cannot be negative, got {spread}"
            raise ValueError(msg)

        return cls(base_price=base, spread=spread)
