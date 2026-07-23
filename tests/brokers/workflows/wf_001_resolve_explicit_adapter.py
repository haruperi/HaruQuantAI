"""WF-BRK-001: resolve an explicit adapter instance."""

import _bootstrap  # noqa: F401
from app.services.brokers import BrokerId, create_broker_adapter
from wf_support import build_mt5_connection_config


def main() -> None:
    """Create two explicit MT5 adapters and show they are distinct."""
    config = build_mt5_connection_config()
    first = create_broker_adapter(BrokerId.MT5, config)
    second = create_broker_adapter(BrokerId.MT5, config)
    print("WF-BRK-001: create first", first.is_success)
    print("WF-BRK-001: create second", second.is_success)
    if first.data is None or second.data is None:
        return
    print("WF-BRK-001: independent instances", first.data is not second.data)


if __name__ == "__main__":
    main()
