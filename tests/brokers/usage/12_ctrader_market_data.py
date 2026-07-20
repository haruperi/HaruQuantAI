"""FEAT-BRK-12: exercise bounded cTrader market-data signatures."""

import asyncio
from datetime import UTC, datetime

from _support import config, show, unavailable_capabilities
from app.services.brokers import BrokerId, CTraderBrokerAdapter


async def main() -> None:
    """Call every FEAT-BRK-12 operation with exact provider-native identity."""
    adapter = CTraderBrokerAdapter(config(BrokerId.CTRADER), unavailable_capabilities())
    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 1, 2, tzinfo=UTC)
    show("symbols", await adapter.get_symbols(query="EUR", limit=10))
    show("symbol", await adapter.get_symbol_info("EURUSD"))
    show("quote", await adapter.get_quote("EURUSD"))
    show("spread", await adapter.get_spread("EURUSD"))
    show("ticks", await adapter.get_ticks("EURUSD", start, end, limit=10))
    show(
        "bars",
        await adapter.get_historical_bars("EURUSD", "M1", start, end, limit=10),
    )


if __name__ == "__main__":
    asyncio.run(main())
