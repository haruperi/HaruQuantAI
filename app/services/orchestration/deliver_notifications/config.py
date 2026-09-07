"""Strict configuration for notification delivery coordination."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class DeliverNotificationsConfig:
    """Configuration for durable notification receipts."""

    database_path: str = ":memory:"


def from_dict(data: dict[str, Any] | None) -> DeliverNotificationsConfig:
    """Parse strict feature configuration.

    Args:
        data: Raw configuration mapping or None.

    Returns:
        Validated notification configuration.

    Raises:
        TypeError: If database_path is not a non-empty string.
        ValueError: If an unknown setting is present.
    """
    values = dict(data or {})
    unknown = set(values) - {"database_path"}
    if unknown:
        message = f"Unknown deliver-notifications configuration keys: {sorted(unknown)}"
        raise ValueError(message)
    database_path = values.get("database_path", ":memory:")
    if not isinstance(database_path, str) or not database_path:
        raise TypeError("database_path must be a non-empty string")
    return DeliverNotificationsConfig(database_path=database_path)
