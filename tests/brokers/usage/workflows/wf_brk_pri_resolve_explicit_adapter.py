"""WF-BRK-PRI: resolve explicit independent broker adapters."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.brokers import (
    create_broker_adapter,
    disconnect_broker,
    get_broker_id,
    get_broker_value_field,
    get_registered_brokers,
    is_broker_connected,
)
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
    connection_config = config("mt5")
    assert get_broker_value_field(connection_config, "broker_id") == get_broker_id(
        "mt5"
    )

    # Stage 2 — Lazily resolve only the selected registered provider.
    _stage(2)
    first_result = create_broker_adapter(get_broker_id("mt5"), connection_config)
    require_success("First adapter resolution", first_result)

    # Stage 3 — Return new independent disconnected adapters.
    _stage(3)
    second_result = create_broker_adapter(get_broker_id("mt5"), connection_config)
    require_success("Second adapter resolution", second_result)
    first_adapter = get_broker_value_field(first_result, "data")
    second_adapter = get_broker_value_field(second_result, "data")
    assert first_adapter is not None
    assert second_adapter is not None
    assert first_adapter is not second_adapter
    require_error(
        "First disconnected state",
        await is_broker_connected(first_adapter),
        "BROKER_CONNECTION_LOST",
        "BROKER_NOT_CONNECTED",
    )
    require_error(
        "Second disconnected state",
        await is_broker_connected(second_adapter),
        "BROKER_CONNECTION_LOST",
        "BROKER_NOT_CONNECTED",
    )

    # Stage 4 — Expose registered broker IDs without fallback selection.
    _stage(4)
    response = get_registered_brokers()
    assert get_broker_value_field(response, "status") == "success"
    registered = get_broker_value_field(response, "data")
    assert registered is not None
    mt5_id = get_broker_id("mt5")
    assert mt5_id in registered
    print(
        "Registered broker IDs:",
        tuple(get_broker_value_field(item, "value") for item in registered),
    )
    require_success("First cleanup", await disconnect_broker(first_adapter))
    require_success("Second cleanup", await disconnect_broker(second_adapter))
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
