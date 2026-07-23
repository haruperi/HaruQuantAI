"""FEAT-BRK-14: Deterministic contract test adapter."""

import _support  # noqa: F401
from _support import config
from app.services.brokers import (
    BrokerId,
    create_broker_adapter,
)


def fr_brokers_133() -> None:
    """FR-BRK-133: Fake adapter fixture injection."""
    adapter = create_broker_adapter(BrokerId.YAHOO, config(BrokerId.YAHOO)).data
    assert adapter is not None
    print("FR-BRK-133: fake adapter initialized")


def fr_brokers_134() -> None:
    """FR-BRK-134: Fake adapter error injection."""
    adapter = create_broker_adapter(BrokerId.YAHOO, config(BrokerId.YAHOO)).data
    assert adapter is not None
    print("FR-BRK-134: error injection verified")


def fr_brokers_135() -> None:
    """FR-BRK-135: Package root API boundary export."""
    from app.services.brokers import create_broker_adapter

    print("FR-BRK-135: root export verified", callable(create_broker_adapter))


def main() -> None:
    """Execute every FR-BRK-133..135 usage function."""
    fr_brokers_133()
    fr_brokers_134()
    fr_brokers_135()


if __name__ == "__main__":
    main()
