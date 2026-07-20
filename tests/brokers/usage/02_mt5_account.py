"""FEAT-BRK-02: exercise the MT5 lifecycle and account diagnostics surface."""

import asyncio

from _support import config, show, unavailable_capabilities
from app.services.brokers import BrokerId, MT5BrokerAdapter


async def main() -> None:
    """Call every FEAT-BRK-02 operation without opening a provider session."""
    adapter = MT5BrokerAdapter(config(BrokerId.MT5), unavailable_capabilities())
    show("connect", await adapter.connect())
    show("balances", await adapter.get_balances())
    show("permissions", await adapter.get_permissions())
    show("last-error", await adapter.get_last_error())
    show("disconnect", await adapter.disconnect())


if __name__ == "__main__":
    asyncio.run(main())
