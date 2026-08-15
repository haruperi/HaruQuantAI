"""WF-TRD-TER: enforce kill switch and bounded emergency controls."""

from __future__ import annotations

import asyncio
import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from app.services.trading import cancel_all_orders, resume_strategy
from tests.trading.usage.workflows._support import examples

WORKFLOW_ID = "WF-TRD-TER"
STAGES = (
    "Accept Risk-owned kill hierarchy, policy verdict, approval evidence, and control request.",
    "Block new action admission when any applicable scope is active or unknown.",
    "Apply the same gates to bounded emergency cancel/close controls.",
    "Preserve every successful, skipped, failed, and uncertain child outcome.",
    "Return blocked/partial control evidence without blindly retrying or closing fills.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


async def run() -> None:
    """Run the documented safe control workflow."""
    # Stage 1 — INPUT BOUNDARY: Risk state and governed control request enter Trading.
    _stage(1)
    request = examples.trading_request(action="resume_strategy")
    states = list(examples.inactive_kill_switch_hierarchy(request))
    states[0] = states[0].model_copy(update={"state": "active"})
    deps = replace(
        examples.trading_dependencies(
            action_policy=examples.action_policy("resume_strategy")
        ),
        kill_switch_state_source=lambda _item: tuple(states),
    )
    print("Input kill state:", states[0].state)
    # Stage 2: Active state blocks new admission.
    _stage(2)
    blocked = await resume_strategy(request, deps)
    assert blocked.error is not None
    print("Blocked:", blocked.error.code, blocked.error.details)
    # Stage 3: Emergency control uses governed Simulation authority.
    _stage(3)
    emergency = examples.emergency_dependencies("cancel_all_orders")
    # Stage 4: Preserve partial/uncertain children.
    _stage(4)
    outcome = await cancel_all_orders(
        examples.trading_request(action="cancel_all_orders"), emergency
    )
    print("Emergency status:", outcome.status)
    # Stage 5 — OUTPUT BOUNDARY: Return explicit blocked/partial evidence.
    _stage(5)
    print("Output:", type(outcome).__name__, outcome.status)


def main() -> None:
    """Run the workflow."""
    asyncio.run(run())


if __name__ == "__main__":
    main()
