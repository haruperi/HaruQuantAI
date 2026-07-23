"""WF-BRK-005: read account and execution state."""

import asyncio

import _bootstrap  # noqa: F401
from app.services.brokers import BrokerId, BrokerPositionFilter, create_broker_adapter
from wf_support import build_mt5_connection_config, print_result


async def _run() -> None:
    """Show a disconnected read boundary for account state."""
    created = create_broker_adapter(BrokerId.MT5, build_mt5_connection_config())
    if created.data is None:
        print("WF-BRK-005: adapter creation failed")
        print_result("WF-BRK-005", created)
        return

    adapter = created.data
    account_info = await adapter.get_account_info()
    print_result("WF-BRK-005: get_account_info", account_info)

    positions = await adapter.get_positions(BrokerPositionFilter(), limit=10)
    print_result("WF-BRK-005: get_positions", positions)

    orders = await adapter.get_orders(limit=5)
    print_result("WF-BRK-005: get_orders", orders)


def main() -> None:
    """Execute WF-BRK-005 demonstration."""
    asyncio.run(_run())


if __name__ == "__main__":
    main()
