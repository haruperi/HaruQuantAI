"""FEAT-BRK-13: exercise local Dukascopy tick-to-bar aggregation signature."""

import asyncio
from datetime import UTC, datetime

from _support import config, show, unavailable_capabilities
from app.services.brokers import BrokerId, DukascopyBrokerAdapter


async def main() -> None:
    """Call bounded local midpoint aggregation without provider network traffic."""
    adapter = DukascopyBrokerAdapter(
        config(BrokerId.DUKASCOPY), unavailable_capabilities()
    )
    show(
        "bars",
        await adapter.get_historical_bars(
            "EURUSD",
            "M1",
            datetime(2026, 1, 1, tzinfo=UTC),
            datetime(2026, 1, 1, 0, 5, tzinfo=UTC),
            limit=5,
        ),
    )


if __name__ == "__main__":
    asyncio.run(main())
