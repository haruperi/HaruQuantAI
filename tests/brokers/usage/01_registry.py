"""FEAT-BRK-01: discover providers, capabilities, and construct an adapter."""

from _support import config
from app.services.brokers import (
    BrokerId,
    create_broker_adapter,
    get_broker_capability_catalogue,
    get_registered_brokers,
)


def main() -> None:
    """Exercise every FEAT-BRK-01 public operation."""
    registered = get_registered_brokers()
    catalogue = get_broker_capability_catalogue()
    created = create_broker_adapter(BrokerId.YAHOO, config(BrokerId.YAHOO))
    print("registered", len(registered))
    print("catalogue", len(catalogue))
    print("factory", created.status)


if __name__ == "__main__":
    main()
