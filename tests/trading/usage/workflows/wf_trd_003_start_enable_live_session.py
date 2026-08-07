"""WF-TRD-003: start a deterministic package-only paper session."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from app.services.trading import is_live_session_admission_enabled, start_live_session
from tests.trading.usage.workflows._support import examples

WORKFLOW_ID = "WF-TRD-003"
STAGES = (
    "Accept a virtual non-production session fixture.",
    "Read bounded virtual capability and readiness evidence.",
    "Construct the Trading lifecycle with injected authority sources.",
    "Start in paper mode and complete startup reconciliation.",
    "Return bounded session status without broker mutation.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


async def run() -> None:
    """Run the safe in-memory startup lifecycle."""
    # Stage 1 — INPUT BOUNDARY: deterministic in-memory session.
    _stage(1)
    session = examples.live_gate_session()
    print("Input: paper, virtual adapter")
    # Stage 2: expose only bounded readiness evidence.
    _stage(2)
    print("Evidence: capability=available, readiness=current")
    # Stage 3: injected sources are contained by the session fixture.
    _stage(3)
    print("Composed: package-only lifecycle")
    # Stage 4: start without live-mutation authority.
    _stage(4)
    runtime = {
        **examples.live_config(),
        "RUNTIME_PROFILE": "paper",
        "EXECUTION_ROUTE": "paper",
        "ALLOW_LIVE_MUTATIONS": False,
    }
    outcome = await start_live_session(session, runtime, examples.live_evidence())
    print(
        "Startup:",
        outcome.status,
        "admission:",
        is_live_session_admission_enabled(session),
    )
    # Stage 5 — OUTPUT BOUNDARY: no external account or credential data.
    _stage(5)
    print("Output:", outcome.status, "No broker mutation was transmitted")


def main() -> None:
    """Run the workflow."""
    asyncio.run(run())


if __name__ == "__main__":
    main()
