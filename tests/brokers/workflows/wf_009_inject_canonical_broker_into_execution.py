"""WF-BRK-009: inject canonical broker protocol into execution."""

import _bootstrap  # noqa: F401
from app.services.brokers import (
    BrokerAdapter,
    BrokerId,
    TradeExecutionProvider,
    create_broker_adapter,
)
from wf_support import build_mt5_connection_config


def main() -> None:
    """Show caller-facing canonical protocol boundaries."""
    created = create_broker_adapter(BrokerId.MT5, build_mt5_connection_config())
    if created.data is None:
        print("WF-BRK-009: adapter creation failed")
        return

    adapter = created.data
    print("WF-BRK-009: broker adapter", isinstance(adapter, BrokerAdapter))
    print(
        "WF-BRK-009: trade execution protocol",
        isinstance(adapter, TradeExecutionProvider),
    )

    public_members = {name for name in dir(adapter) if not name.startswith("_")}
    forbidden = {"mt5", "MetaTrader5", "terminal", "sdk", "client"}
    print("WF-BRK-009: forbids native symbols", not (forbidden & public_members))


if __name__ == "__main__":
    main()
