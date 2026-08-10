"""Lazy boundary for Brokers-owned immutable schema definitions."""

from __future__ import annotations

from collections.abc import Callable

from app.services.brokers.migrations.public import run_broker_migrations

BROKER_MIGRATIONS: tuple[object, ...]
BROKER_SCHEMA_VERSION: str
get_broker_migrations: Callable[[], tuple[object, ...]]


def __getattr__(name: str) -> object:
    """Load schema definitions only when explicitly requested.

    Args:
        name: Requested migration export.

    Returns:
        Requested immutable migration value or function.

    Raises:
        AttributeError: If the requested name is not a migration export.
    """
    if name not in {
        "BROKER_MIGRATIONS",
        "BROKER_SCHEMA_VERSION",
        "get_broker_migrations",
    }:
        raise AttributeError(name)
    from app.services.brokers.migrations import definitions

    return getattr(definitions, name)


__all__ = [
    "BROKER_MIGRATIONS",
    "BROKER_SCHEMA_VERSION",
    "get_broker_migrations",
    "run_broker_migrations",
]
