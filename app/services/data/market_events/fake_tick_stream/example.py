"""Executable usage example for deterministic fake tick stream provider."""

# ruff: noqa: E402
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[5]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from app.contracts.data.tick_stream.v1 import TickStreamRequestV1
from app.kernel.effects import EffectScope
from app.services.data.market_events.fake_tick_stream.plugin import (
    create_provider,
)


async def _run_example() -> None:
    """Execute fake tick stream provider usage demonstration."""
    scope = EffectScope()
    provider = create_provider(
        dependencies={},
        config={"symbol": "EURUSD", "buffer_size": 3},
        scope=scope,
    )
    req = TickStreamRequestV1(symbol="EURUSD", buffer_size=3)
    await provider.start(req)

    async for event in provider.events():
        output = {
            "sequence": event.sequence,
            "symbol": event.symbol,
            "bid": event.payload.get("bid"),
        }
        print(json.dumps(output))

    await provider.stop()
    scope.close()


def main() -> None:
    """Run deterministic fake tick stream demonstration."""
    asyncio.run(_run_example())


if __name__ == "__main__":
    main()
