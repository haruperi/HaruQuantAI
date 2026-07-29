"""WF-BRK-006: stream lifecycle evidence and exercise MT5 stream gates."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.brokers import (
    connect_broker,
    disconnect_broker,
    get_broker_connection_events,
    get_broker_value_field,
    list_broker_subscriptions,
    subscribe_broker_bars,
    subscribe_broker_order_book,
    subscribe_broker_quotes,
    unsubscribe_broker,
)
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


def _check_sub(label: str, res: object) -> object:
    """Require success or unsupported subscription error."""
    if get_broker_value_field(res, "status") == "success":
        return require_success(label, res)
    return require_error(label, res, "BROKER_CAPABILITY_UNSUPPORTED")


async def run() -> None:
    """Execute lifecycle streaming and unsupported MT5 subscriptions."""
    print(f"{WORKFLOW_ID} — Stream Provider and Connection Events")
    print("INPUT BOUNDARY — Data requests an adapter-scoped subscription")
    adapter = create_real_adapter("mt5")

    # Stage 1 — Open the bounded adapter connection-event stream.
    _stage(1)
    events = get_broker_connection_events(adapter)
    pending_event = asyncio.create_task(anext(events))

    try:
        # Stage 2 — Connect and consume validated lifecycle transitions.
        _stage(2)
        require_success("MT5 connect", await connect_broker(adapter))
        event = await asyncio.wait_for(pending_event, timeout=5)
        prev_state = get_broker_value_field(
            get_broker_value_field(event, "previous_state"), "value"
        )
        new_state = get_broker_value_field(
            get_broker_value_field(event, "new_state"), "value"
        )
        print(
            "Lifecycle event:",
            prev_state,
            "->",
            new_state,
        )

        # Stage 3 — Call MT5 subscription operations and preserve exact capability gates.
        _stage(3)
        res1 = _check_sub(
            "Quote subscription", await subscribe_broker_quotes(adapter, ("EURUSD",))
        )
        _check_sub(
            "Bar subscription", await subscribe_broker_bars(adapter, ("EURUSD",), "1m")
        )
        _check_sub(
            "Book subscription", await subscribe_broker_order_book(adapter, ("EURUSD",))
        )
        _check_sub("Owned subscriptions", await list_broker_subscriptions(adapter))

        sub_handle = get_broker_value_field(res1, "data")
        if sub_handle is not None:
            _check_sub("Unknown unsubscribe", await unsubscribe_broker(sub_handle))
    finally:
        # Stage 4 — Disconnect and terminate adapter-owned stream resources.
        _stage(4)
        if not pending_event.done():
            pending_event.cancel()
        require_success("MT5 disconnect", await disconnect_broker(adapter))
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
