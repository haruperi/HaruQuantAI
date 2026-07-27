"""WF-SIM-006: reject raw strategy code at the public boundary."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.simulator import SimulationError, validate_run_inputs
from tests.simulator.unit.test_validate import _valid_payload

WORKFLOW_ID = "WF-SIM-006"
STAGES = (
    "Receive raw code, filesystem path, or an unapproved strategy reference.",
    "Validate reference-only run material at the public boundary.",
    "Return SIM_ARBITRARY_CODE_REJECTED before import, network, or engine creation.",
)


# fmt: off
def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}")
# fmt: on


def main() -> None:
    """Execute the documented security-rejection workflow."""
    print(f"{WORKFLOW_ID} — Registered-Strategy Security Rejection")
    print("INPUT BOUNDARY — unapproved raw strategy source")

    # Stage 1 — Receive raw code, filesystem path, or an unapproved strategy reference.
    _stage(1)
    payload = _valid_payload() | {"source_code": "import os"}

    # Stage 2 — Validate reference-only run material at the public boundary.
    _stage(2)
    try:
        validate_run_inputs(payload)
    except SimulationError as error:
        rejected = error
    else:
        raise AssertionError("raw strategy code unexpectedly passed validation")

    # Stage 3 — Return SIM_ARBITRARY_CODE_REJECTED before import, network, or engine creation.
    _stage(3)
    assert rejected.code == "SIM_ARBITRARY_CODE_REJECTED"
    print("OUTPUT BOUNDARY — typed SimulationError:", rejected.code)


if __name__ == "__main__":
    main()
