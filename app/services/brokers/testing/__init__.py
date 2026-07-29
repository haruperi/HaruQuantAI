"""Testing utilities and fake adapter for the Brokers domain."""

from typing import Any

from app.services.brokers.testing.fake import FakeBrokerAdapter


def create_fake_broker_adapter(*args: Any, **kwargs: Any) -> FakeBrokerAdapter:
    """Create a new deterministic fake broker adapter instance for testing.

    Args:
        *args: Positional arguments for FakeBrokerAdapter constructor.
        **kwargs: Keyword arguments for FakeBrokerAdapter constructor.

    Returns:
        A new FakeBrokerAdapter instance.
    """
    return FakeBrokerAdapter(*args, **kwargs)


__all__: list[str] = ["FakeBrokerAdapter", "create_fake_broker_adapter"]
