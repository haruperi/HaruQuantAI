"""WF-BRK-003: acquire provider market data."""

import asyncio

import _bootstrap  # noqa: F401
from app.services.brokers import BrokerId, create_broker_adapter
from wf_support import (
    build_mt5_connection_config,
    print_connection_status,
    print_result,
)


async def _run() -> None:
    """Connect to MT5 (when possible) and request one quote."""
    created = create_broker_adapter(BrokerId.MT5, build_mt5_connection_config())
    if created.data is None:
        print("WF-BRK-003: adapter creation failed")
        print_result("WF-BRK-003", created)
        return

    adapter = created.data
    connect_result = await adapter.connect()
    print_result("WF-BRK-003: connect", connect_result)

    status = await adapter.get_connection_status()
    print_connection_status("WF-BRK-003: status", status)

    quote_result = await adapter.get_quote("EURUSD")
    print_result("WF-BRK-003: get_quote", quote_result)
    if quote_result.data is not None:
        print(
            "WF-BRK-003: quote ask/bid",
            quote_result.data.ask,
            quote_result.data.bid,
        )

    disconnect_result = await adapter.disconnect()
    print_result("WF-BRK-003: disconnect", disconnect_result)


def main() -> None:
    """Execute WF-BRK-003 demonstration."""
    asyncio.run(_run())


if __name__ == "__main__":
    main()
