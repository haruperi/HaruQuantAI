"""WF-TRD-014: run a neutral paper/live evaluation cycle without mutation."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from app.services.trading import run_live_evaluation_cycle
from tests.trading.usage.workflows._support import examples

WORKFLOW_ID = "WF-TRD-014"
STAGES = (
    "Accept live/paper market update or scheduled trigger with immutable trace evidence.",
    "Read Data market/account/context evidence in documented order.",
    "Calculate Indicators and request Strategy decision.",
    "End normally on neutral Strategy output without calling Risk or execution.",
    "Return success envelope with mutation_performed=False.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


async def run() -> None:
    """Run the documented neutral workflow."""
    # Stage 1 — INPUT BOUNDARY: Runtime supplies scheduled evaluation trace evidence.
    _stage(1)
    deps, calls = examples.evaluation_dependencies(None)
    evidence = examples.evaluation_evidence()
    print("Input request:", evidence["request_id"])
    # Stage 2: Orchestrator reads Data boundaries.
    _stage(2)
    # Stage 3: It then invokes Indicators and Strategy.
    _stage(3)
    outcome = await run_live_evaluation_cycle(deps, evidence)
    print("Calls:", calls)
    # Stage 4: Neutral ends before Risk and dispatch.
    _stage(4)
    print(
        "Risk called:", "risk" in calls, "mutation:", outcome.data["mutation_performed"]
    )
    # Stage 5 — OUTPUT BOUNDARY: Return normal no-mutation success.
    _stage(5)
    print("Output:", type(outcome).__name__, outcome.status)


def main() -> None:
    """Run the workflow."""
    asyncio.run(run())


if __name__ == "__main__":
    main()
