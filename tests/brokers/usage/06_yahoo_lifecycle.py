"""FEAT-BRK-06: exercise the Yahoo lifecycle surface."""

import asyncio

from _support import config, show, unavailable_capabilities
from app.services.brokers import BrokerId, YahooBrokerAdapter


async def main() -> None:
    """Call every FEAT-BRK-06 operation without provider network traffic."""
    adapter = YahooBrokerAdapter(config(BrokerId.YAHOO), unavailable_capabilities())
    show("connect", await adapter.connect())
    show("disconnect", await adapter.disconnect())


if __name__ == "__main__":
    asyncio.run(main())
