"""Strict configuration for durable job management."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ManageJobsConfig:
    """Configuration for the job store and observer queues."""

    database_path: str = ":memory:"
    callback_queue_capacity: int = 128


def from_dict(data: dict[str, Any] | None) -> ManageJobsConfig:
    """Parse strict feature configuration.

    Returns:
        Validated job configuration.

    Raises:
        TypeError: If a setting has the wrong type or range.
        ValueError: If an unknown setting is present.
    """
    values = dict(data or {})
    unknown = set(values) - {"database_path", "callback_queue_capacity"}
    if unknown:
        message = f"Unknown manage-jobs configuration keys: {sorted(unknown)}"
        raise ValueError(message)
    path = values.get("database_path", ":memory:")
    capacity = values.get("callback_queue_capacity", 128)
    if not isinstance(path, str) or not path:
        raise TypeError("database_path must be a non-empty string")
    if not isinstance(capacity, int) or isinstance(capacity, bool) or capacity <= 0:
        raise TypeError("callback_queue_capacity must be a positive integer")
    return ManageJobsConfig(path, capacity)
