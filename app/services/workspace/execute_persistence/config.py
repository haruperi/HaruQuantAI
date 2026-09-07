"""Strict configuration for bounded persistence execution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

_ALLOWED_CONFIG_KEYS = frozenset(
    {
        "busy_timeout_seconds",
        "max_export_limit",
        "max_statements_per_tx",
    }
)
MIN_BUSY_TIMEOUT_SECONDS = 0.1
MAX_BUSY_TIMEOUT_SECONDS = 60.0
MIN_EXPORT_LIMIT = 1
MAX_EXPORT_LIMIT = 10_000
MIN_STATEMENTS_PER_TX = 1
MAX_STATEMENTS_PER_TX = 1_000


@dataclass(frozen=True, slots=True)
class ExecutePersistenceConfig:
    """Bounded runtime policy for persistence operations."""

    busy_timeout_seconds: float = 5.0
    max_export_limit: int = 1000
    max_statements_per_tx: int = 100


def from_dict(
    data: dict[str, Any] | None,
) -> ExecutePersistenceConfig:
    """Parse configuration and reject unknown, wrong-type, or unbounded values.

    Args:
        data: Raw configuration mapping or None.

    Returns:
        Validated immutable configuration.

    Raises:
        TypeError: If a value has the wrong type.
        ValueError: If a key is unknown or a value exceeds safe bounds.
    """
    if not data:
        return ExecutePersistenceConfig()
    unknown = set(data) - _ALLOWED_CONFIG_KEYS
    if unknown:
        raise ValueError(
            "Unknown execute-persistence configuration keys: "
            + ", ".join(sorted(unknown))
        )
    defaults = ExecutePersistenceConfig()
    busy_timeout = data.get("busy_timeout_seconds", defaults.busy_timeout_seconds)
    max_export = data.get("max_export_limit", defaults.max_export_limit)
    max_statements = data.get("max_statements_per_tx", defaults.max_statements_per_tx)

    if not isinstance(busy_timeout, int | float) or isinstance(busy_timeout, bool):
        raise TypeError("busy_timeout_seconds must be numeric")
    if not isinstance(max_export, int) or isinstance(max_export, bool):
        raise TypeError("max_export_limit must be an integer")
    if not isinstance(max_statements, int) or isinstance(max_statements, bool):
        raise TypeError("max_statements_per_tx must be an integer")

    if not MIN_BUSY_TIMEOUT_SECONDS <= float(busy_timeout) <= MAX_BUSY_TIMEOUT_SECONDS:
        msg = (
            f"busy_timeout_seconds must be between "
            f"{MIN_BUSY_TIMEOUT_SECONDS} and {MAX_BUSY_TIMEOUT_SECONDS}"
        )
        raise ValueError(msg)
    if not MIN_EXPORT_LIMIT <= max_export <= MAX_EXPORT_LIMIT:
        msg = (
            f"max_export_limit must be between "
            f"{MIN_EXPORT_LIMIT} and {MAX_EXPORT_LIMIT}"
        )
        raise ValueError(msg)
    if not MIN_STATEMENTS_PER_TX <= max_statements <= MAX_STATEMENTS_PER_TX:
        msg = (
            f"max_statements_per_tx must be between "
            f"{MIN_STATEMENTS_PER_TX} and {MAX_STATEMENTS_PER_TX}"
        )
        raise ValueError(msg)

    return ExecutePersistenceConfig(
        busy_timeout_seconds=float(busy_timeout),
        max_export_limit=max_export,
        max_statements_per_tx=max_statements,
    )
