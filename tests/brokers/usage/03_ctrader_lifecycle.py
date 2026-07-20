"""FEAT-BRK-03: exercise the cTrader lifecycle surface."""

import asyncio

from _support import config, show, unavailable_capabilities
from app.services.brokers import BrokerId, CTraderBrokerAdapter


async def main() -> None:
    """Call every FEAT-BRK-03 operation without opening a provider session."""
    adapter = CTraderBrokerAdapter(config(BrokerId.CTRADER), unavailable_capabilities())
    show("connect", await adapter.connect())
    show("disconnect", await adapter.disconnect())


if __name__ == "__main__":
    asyncio.run(main())
