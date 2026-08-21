"""Configuration validation for Mock Broker Feed."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class MockFeedConfig:
    """Configuration options for mock broker feed.

    Satisfies:
        FR-BROKER-VALIDATE_FEED_CONFIG: Validates base price constraint.

    Attributes:
        base_price: Base price level for synthetic bar generation.
    """

    base_price: float = 1.1000

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> MockFeedConfig:
        """Parse and validate configuration dictionary.

        Args:
            data: Raw dictionary from application configuration.

        Returns:
            Validated MockFeedConfig instance.

        Raises:
            ValueError: If base_price is not positive.
        """
        if not data:
            return cls()

        base = float(data.get("base_price", 1.1000))
        if base <= 0:
            msg = f"base_price must be positive, got {base}"
            raise ValueError(msg)

        return cls(base_price=base)
