"""WF-TRD-009: perform bounded safe live shutdown."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from tests.trading.usage.workflows._support import examples

WORKFLOW_ID = "WF-TRD-009"
STAGES = (
    "Accept operator/runtime stop request for a configured LiveSession.",
    "Stop new admission and mark/drain in-flight work within budget.",
    "Flush execution evidence.",
    "Attempt final authority reconciliation and preserve every incomplete step.",
    "Return structured shutdown result with unresolved work.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


async def run() -> None:
    """Run the documented lifecycle."""
    # Stage 1 — INPUT BOUNDARY: Operator/runtime owns stop trigger.
    _stage(1)

    async def failed() -> bool:
        return False

    session = examples.live_session(flush_evidence=failed)
    await session.start(examples.live_config(), examples.live_evidence())
    print("Session started:", session.started)
    # Stage 2: LiveSession.stop immediately stops admission/drains.
    _stage(2)
    # Stage 3: The injected flush deliberately reports incomplete.
    _stage(3)
    print("Flush expected:", False)
    # Stage 4: Stop performs reconciliation and retains failures.
    _stage(4)
    outcome = await session.stop()
    print("Unresolved:", outcome.data["unresolved_steps"])
    # Stage 5 — OUTPUT BOUNDARY: Return structured partial shutdown truth.
    _stage(5)
    print("Output:", type(outcome).__name__, outcome.status)


def main() -> None:
    """Run the workflow."""
    asyncio.run(run())


if __name__ == "__main__":
    main()
