"""FEAT-BRK-05: exercise the Dukascopy lifecycle surface."""

import asyncio

from _support import config, show, unavailable_capabilities
from app.services.brokers import BrokerId, DukascopyBrokerAdapter


async def main() -> None:
    """Call every FEAT-BRK-05 operation without provider network traffic."""
    adapter = DukascopyBrokerAdapter(
        config(BrokerId.DUKASCOPY), unavailable_capabilities()
    )
    show("connect", await adapter.connect())
    show("disconnect", await adapter.disconnect())


if __name__ == "__main__":
    asyncio.run(main())
