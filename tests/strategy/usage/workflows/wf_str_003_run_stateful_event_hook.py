"""WF-STR-003: run one declared stateful event hook."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.strategy import run_event_strategy_hook
from tests.strategy.unit.test_event_runner import Evaluator
from tests.strategy.unit.test_models import (
    make_config,
    make_context,
    make_event,
    make_ref,
)

WORKFLOW_ID = "WF-STR-003"
STAGES = (
    "Accept a typed event, fixed context, and immutable execution evidence.",
    "Resolve the declared hook in stable priority order.",
    "Invoke the approved hash-bound event evaluator.",
    "Validate intents, diagnostics, and candidate local-state update atomically.",
    "Return the result and commit-eligible local state or structured failure.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Run the documented input-to-output workflow."""
    # Stage 1 — INPUT BOUNDARY: Runtime supplies a typed event and fixed evidence.
    _stage(1)
    event, context = make_event(), make_context()
    print("Input event:", event.event_type)

    # Stage 2: The manifest declares the allowed hook.
    _stage(2)
    ref = make_ref()
    print("Declared hooks:", ref.manifest.supported_hooks)

    # Stage 3: Run exactly one approved hook.
    _stage(3)
    outcome = run_event_strategy_hook(ref, make_config(), event, context, Evaluator())
    print("Hook status:", outcome.status)

    # Stage 4: Inspect the fully validated candidate update.
    _stage(4)
    update = outcome.data.local_state_update if outcome.data else None
    print("Candidate local state:", update)

    # Stage 5 — OUTPUT BOUNDARY: Return validated result or StandardResponse error.
    _stage(5)
    print("Output:", type(outcome).__name__, outcome.status)


if __name__ == "__main__":
    main()
