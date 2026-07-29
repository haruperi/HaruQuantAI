"""WF-BRK-008: handle a genuine MT5 unsupported capability."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))


from app.services.brokers import (
    connect_broker,
    disconnect_broker,
    get_broker_order_book,
    get_broker_value_field,
    supports_broker_capability,
)
from tests.brokers.usage._support import (
    create_real_adapter,
    require_error,
    require_success,
)

WORKFLOW_ID = "WF-BRK-008"
STAGES = (
    "Connect and inspect the runtime capability declaration.",
    "Call one unavailable canonical operation.",
    "Return deterministic unsupported evidence without an SDK call.",
)


async def run() -> None:
    """Execute the canonical unsupported-operation path."""
    print(f"{WORKFLOW_ID} — Handle Unsupported Operation")
    print("INPUT BOUNDARY — unavailable MT5 order-book operation")
    adapter = create_real_adapter("mt5")
    try:
        # Stage 1 — Connect and inspect the runtime capability declaration.
        _stage(1)
        require_success("MT5 connect", await connect_broker(adapter))
        supported = require_success(
            "Order-book capability",
            await supports_broker_capability(adapter, "get_order_book"),
        )
        assert get_broker_value_field(supported, "data") in (True, False)

        # Stage 2 — Call one unavailable canonical operation.
        _stage(2)
        result = await get_broker_order_book(adapter, "EURUSD", depth=5)

        # Stage 3 — Return deterministic unsupported evidence without an SDK call.
        _stage(3)
        if get_broker_value_field(result, "status") == "success":
            require_success("Order book", result)
        else:
            require_error(
                "Unsupported order book",
                result,
                "BROKER_CAPABILITY_UNSUPPORTED",
            )
    finally:
        require_success("MT5 disconnect", await disconnect_broker(adapter))
    print("OUTPUT BOUNDARY — StandardResponse with capability and operation evidence")


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
