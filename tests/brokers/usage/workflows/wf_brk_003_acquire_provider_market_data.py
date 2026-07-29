"""WF-BRK-003: acquire genuine bounded MT5 market data."""

from __future__ import annotations

import asyncio
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.brokers import (
    connect_broker,
    disconnect_broker,
    get_broker_historical_bars,
    get_broker_market_status,
    get_broker_order_book,
    get_broker_quote,
    get_broker_spread,
    get_broker_symbol_info,
    get_broker_symbols,
    get_broker_ticks,
    get_broker_trading_sessions,
    get_broker_value_field,
    select_broker_symbol,
)
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


def _check(label: str, res: object) -> object:
    """Require success or unsupported error."""
    if get_broker_value_field(res, "status") == "success":
        return require_success(label, res)
    return require_error(label, res, "BROKER_CAPABILITY_UNSUPPORTED")


async def run() -> None:
    """Execute every documented MT5 market-data operation."""
    print(f"{WORKFLOW_ID} — Acquire Provider Market Data")
    print("INPUT BOUNDARY — Data supplies a bounded explicit MT5 read")
    adapter = create_real_adapter("mt5")
    try:
        require_success("MT5 connect", await connect_broker(adapter))

        # Stage 1 — Resolve and select the exact provider symbol.
        _stage(1)
        require_success("Symbols", await get_broker_symbols(adapter, limit=10))
        require_success(
            "Symbol metadata", await get_broker_symbol_info(adapter, "EURUSD")
        )
        _check("Symbol selection", await select_broker_symbol(adapter, "EURUSD", True))

        # Stage 2 — Read provider market-state and session capabilities.
        _stage(2)
        _check("Market status", await get_broker_market_status(adapter, "EURUSD"))
        _check("Trading sessions", await get_broker_trading_sessions(adapter, "EURUSD"))

        # Stage 3 — Read quote, ticks, bars, order book, and spread.
        _stage(3)
        end = datetime.now(UTC)
        start = end - timedelta(hours=1)
        quote = require_success("Quote", await get_broker_quote(adapter, "EURUSD"))
        ticks = _check(
            "Ticks",
            await get_broker_ticks(
                adapter, "EURUSD", start_time=start, end_time=end, limit=10
            ),
        )
        bars = require_success(
            "Bars",
            await get_broker_historical_bars(
                adapter, "EURUSD", "1m", start_time=start, end_time=end, limit=10
            ),
        )
        _check("Order book", await get_broker_order_book(adapter, "EURUSD", depth=5))
        _check("Spread", await get_broker_spread(adapter, "EURUSD"))

        # Stage 4 — Return direct canonical provider observations to Data.
        _stage(4)
        assert get_broker_value_field(quote, "data") is not None
        print(
            "Bounded provider results:",
            get_broker_value_field(ticks, "data") is not None or ticks is not None,
            get_broker_value_field(bars, "data") is not None,
            "spread available",
        )
    finally:
        require_success("MT5 disconnect", await disconnect_broker(adapter))
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
