"""WF-BRK-009: inject only the canonical BrokerAdapter protocol."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.brokers import BrokerAdapter, BrokerId
from tests.brokers.usage._support import create_real_adapter, require_success

WORKFLOW_ID = "WF-BRK-009"
STAGES = (
    "Resolve a genuine MT5 adapter at the composition root.",
    "Inject only the canonical BrokerAdapter capability.",
    "Execute through the provider-neutral protocol.",
    "Return canonical evidence and release the adapter.",
)


async def _execution_consumer(adapter: BrokerAdapter) -> None:
    """Represent a Trading consumer that knows only the canonical protocol."""
    require_success("Injected status", await adapter.get_connection_status())
    require_success("Injected quote", await adapter.get_quote("EURUSD"))


async def run() -> None:
    """Execute canonical protocol injection."""
    print(f"{WORKFLOW_ID} — Inject Canonical Broker into Execution")
    print("INPUT BOUNDARY — composition root resolves MT5 demo configuration")

    # Stage 1 — Resolve a genuine MT5 adapter at the composition root.
    _stage(1)
    adapter = create_real_adapter(BrokerId.MT5)
    try:
        require_success("MT5 connect", await adapter.connect())

        # Stage 2 — Inject only the canonical BrokerAdapter capability.
        _stage(2)
        injected: BrokerAdapter = adapter
        assert injected.schema_id == "brokers.adapter.v1"

        # Stage 3 — Execute through the provider-neutral protocol.
        _stage(3)
        await _execution_consumer(injected)
    finally:
        # Stage 4 — Return canonical evidence and release the adapter.
        _stage(4)
        require_success("MT5 disconnect", await adapter.disconnect())
    print("OUTPUT BOUNDARY — Trading consumed BrokerAdapter, not a native SDK")


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
