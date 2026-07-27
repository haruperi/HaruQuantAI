"""WF-BRK-003: acquire genuine bounded MT5 market data."""

from __future__ import annotations

import asyncio
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.brokers import BrokerErrorCode, BrokerId
from tests.brokers.usage._support import (
    create_real_adapter,
    require_error,
    require_success,
)

WORKFLOW_ID = "WF-BRK-003"
STAGES = (
    "Resolve and select the exact provider symbol.",
    "Read provider market-state and session capabilities.",
    "Read quote, ticks, bars, order book, and spread.",
    "Return direct canonical provider observations to Data.",
)


async def run() -> None:
    """Execute every documented MT5 market-data operation."""
    print(f"{WORKFLOW_ID} — Acquire Provider Market Data")
    print("INPUT BOUNDARY — Data supplies a bounded explicit MT5 read")
    adapter = create_real_adapter(BrokerId.MT5)
    try:
        require_success("MT5 connect", await adapter.connect())

        # Stage 1 — Resolve and select the exact provider symbol.
        _stage(1)
        require_success("Symbols", await adapter.get_symbols(limit=10))
        require_success("Symbol metadata", await adapter.get_symbol_info("EURUSD"))
        require_success("Symbol selection", await adapter.select_symbol("EURUSD", True))

        # Stage 2 — Read provider market-state and session capabilities.
        _stage(2)
        require_error(
            "Market status",
            await adapter.get_market_status("EURUSD"),
            BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED,
        )
        require_error(
            "Trading sessions",
            await adapter.get_trading_sessions("EURUSD"),
            BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED,
        )

        # Stage 3 — Read quote, ticks, bars, order book, and spread.
        _stage(3)
        end = datetime.now(UTC)
        start = end - timedelta(hours=1)
        quote = require_success("Quote", await adapter.get_quote("EURUSD"))
        ticks = require_success(
            "Ticks",
            await adapter.get_ticks("EURUSD", start=start, end=end, limit=10),
        )
        bars = require_success(
            "Bars",
            await adapter.get_historical_bars(
                "EURUSD", "M1", start=start, end=end, limit=10
            ),
        )
        require_error(
            "Order book",
            await adapter.get_order_book("EURUSD", depth=5),
            BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED,
        )
        spread = require_success("Spread", await adapter.get_spread("EURUSD"))

        # Stage 4 — Return direct canonical provider observations to Data.
        _stage(4)
        assert quote.data is not None
        assert spread.data is not None
        print(
            "Bounded provider results:",
            ticks.data is not None,
            bars.data is not None,
            "spread available",
        )
    finally:
        require_success("MT5 disconnect", await adapter.disconnect())
    print("OUTPUT BOUNDARY — canonical MT5 quote/tick/bar/spread results")


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Run the workflow."""
    asyncio.run(run())


if __name__ == "__main__":
    main()
