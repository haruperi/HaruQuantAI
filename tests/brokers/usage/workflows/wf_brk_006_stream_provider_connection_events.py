"""WF-BRK-006: stream lifecycle evidence and exercise MT5 stream gates."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.brokers.contracts import BrokerErrorCode, BrokerId
from tests.brokers.usage._support import (
    create_real_adapter,
    require_error,
    require_success,
)

WORKFLOW_ID = "WF-BRK-006"
STAGES = (
    "Open the bounded adapter connection-event stream.",
    "Connect and consume validated lifecycle transitions.",
    "Call MT5 subscription operations and preserve exact capability gates.",
    "Disconnect and terminate adapter-owned stream resources.",
)


async def run() -> None:
    """Execute lifecycle streaming and unsupported MT5 subscriptions."""
    print(f"{WORKFLOW_ID} — Stream Provider and Connection Events")
    print("INPUT BOUNDARY — Data requests an adapter-scoped subscription")
    adapter = create_real_adapter(BrokerId.MT5)

    # Stage 1 — Open the bounded adapter connection-event stream.
    _stage(1)
    events = adapter.connection_events()
    pending_event = asyncio.create_task(anext(events))

    try:
        # Stage 2 — Connect and consume validated lifecycle transitions.
        _stage(2)
        require_success("MT5 connect", await adapter.connect())
        event = await asyncio.wait_for(pending_event, timeout=5)
        print(
            "Lifecycle event:",
            event.previous_state.value,
            "->",
            event.new_state.value,
        )

        # Stage 3 — Call MT5 subscription operations and preserve exact capability gates.
        _stage(3)
        require_error(
            "Quote subscription",
            await adapter.subscribe_quotes(("EURUSD",)),
            BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED,
        )
        require_error(
            "Bar subscription",
            await adapter.subscribe_bars(("EURUSD",), "M1"),
            BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED,
        )
        require_error(
            "Book subscription",
            await adapter.subscribe_order_book(("EURUSD",)),
            BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED,
        )
        require_error(
            "Owned subscriptions",
            await adapter.list_subscriptions(),
            BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED,
        )
        require_error(
            "Unknown unsubscribe",
            await adapter.unsubscribe("workflow-subscription"),
            BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED,
        )
    finally:
        # Stage 4 — Disconnect and terminate adapter-owned stream resources.
        _stage(4)
        if not pending_event.done():
            pending_event.cancel()
        require_success("MT5 disconnect", await adapter.disconnect())
        await events.aclose()
    print(
        "OUTPUT BOUNDARY — lifecycle event plus exact MT5 stream-unavailable evidence"
    )


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
