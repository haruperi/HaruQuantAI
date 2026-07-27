"""WF-BRK-008: handle a genuine MT5 unsupported capability."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))


from app.services.brokers import BrokerCapabilityId, BrokerErrorCode, BrokerId
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
    adapter = create_real_adapter(BrokerId.MT5)
    try:
        # Stage 1 — Connect and inspect the runtime capability declaration.
        _stage(1)
        require_success("MT5 connect", await adapter.connect())
        supported = require_success(
            "Order-book capability",
            await adapter.supports(BrokerCapabilityId.GET_ORDER_BOOK),
        )
        assert supported.data is False

        # Stage 2 — Call one unavailable canonical operation.
        _stage(2)
        result = await adapter.get_order_book("EURUSD", depth=5)

        # Stage 3 — Return deterministic unsupported evidence without an SDK call.
        _stage(3)
        require_error(
            "Unsupported order book",
            result,
            BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED,
        )
    finally:
        require_success("MT5 disconnect", await adapter.disconnect())
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
