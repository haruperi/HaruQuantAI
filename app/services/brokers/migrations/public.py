"""Lazy public execution boundary for Brokers-owned migrations."""


def run_broker_migrations(request_id: str) -> object:
    """Apply the immutable Brokers migration manifest through Data.

    Args:
        request_id: Canonical startup request identifier.

    Returns:
        Data-owned standard migration response.
    """
    from app.services.brokers.migrations.definitions import (
        run_broker_migrations as _run_broker_migrations,
    )

    return _run_broker_migrations(request_id)


__all__ = ["run_broker_migrations"]
