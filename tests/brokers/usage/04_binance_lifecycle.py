"""FEAT-BRK-04: exercise the Binance Spot lifecycle surface."""

import asyncio

from _support import config, show, unavailable_capabilities
from app.services.brokers import BinanceBrokerAdapter, BrokerId


async def main() -> None:
    """Call every FEAT-BRK-04 operation without opening a provider session."""
    adapter = BinanceBrokerAdapter(
        config(BrokerId.BINANCE_SPOT), unavailable_capabilities()
    )
    show("connect", await adapter.connect())
    show("disconnect", await adapter.disconnect())


if __name__ == "__main__":
    asyncio.run(main())
