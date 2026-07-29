"""WF-BRK-PRI: resolve explicit independent broker adapters."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.brokers import (
    create_broker_adapter,
    get_registered_brokers,
)
from app.services.brokers.contracts import BrokerErrorCode, BrokerId
from tests.brokers.usage._support import config, require_error, require_success

WORKFLOW_ID = "WF-BRK-PRI"
STAGES = (
    "Validate exact broker ID and connection-config correspondence.",
    "Lazily resolve only the selected registered provider.",
    "Return new independent disconnected adapters.",
    "Expose registered broker IDs without fallback selection.",
)


async def run() -> None:
    """Execute explicit MT5 adapter resolution."""
    print(f"{WORKFLOW_ID} — Resolve Explicit Adapter")
    print("INPUT BOUNDARY — explicit MT5 broker ID and immutable demo config")

    # Stage 1 — Validate exact broker ID and connection-config correspondence.
    _stage(1)
    connection_config = config(BrokerId.MT5)
    assert connection_config.broker_id == BrokerId.MT5

    # Stage 2 — Lazily resolve only the selected registered provider.
    _stage(2)
    first_result = create_broker_adapter(BrokerId.MT5, connection_config)
    require_success("First adapter resolution", first_result)

    # Stage 3 — Return new independent disconnected adapters.
    _stage(3)
    second_result = create_broker_adapter(BrokerId.MT5, connection_config)
    require_success("Second adapter resolution", second_result)
    assert first_result.data is not None
    assert second_result.data is not None
    assert first_result.data is not second_result.data
    require_error(
        "First disconnected state",
        await first_result.data.is_connected(),
        BrokerErrorCode.BROKER_CONNECTION_LOST,
    )
    require_error(
        "Second disconnected state",
        await second_result.data.is_connected(),
        BrokerErrorCode.BROKER_CONNECTION_LOST,
    )

    # Stage 4 — Expose registered broker IDs without fallback selection.
    _stage(4)
    response = get_registered_brokers()
    assert response.status == "success"
    assert response.data is not None
    registered = response.data
    assert BrokerId.MT5 in registered
    print("Registered broker IDs:", tuple(item.value for item in registered))
    require_success("First cleanup", await first_result.data.disconnect())
    require_success("Second cleanup", await second_result.data.disconnect())
    print("OUTPUT BOUNDARY — two independent disconnected BrokerAdapter values")


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Run the workflow."""
    import asyncio

    asyncio.run(run())


if __name__ == "__main__":
    main()
