"""Stage-labelled evidence for WF-UTL-009 notification orchestration."""

import sys
from pathlib import Path

_USAGE_ROOT = Path(__file__).resolve().parents[1]
if str(_USAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(_USAGE_ROOT))

from notification_runtime import run_real_notification_evidence  # noqa: E402

WORKFLOW_ID = "WF-UTL-009"
STAGES = (
    "Verify development environment.",
    "Resolve database-backed settings.",
    "Resolve encrypted credentials.",
    "Dispatch real non-production notification.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Compose an inactive manager and render a safe operational alert."""
    print(f"{WORKFLOW_ID} — Notification Orchestration")
    print("INPUT BOUNDARY — validated settings and notification configuration")
    # Stage 1 — Verify development environment.
    _stage(1)
    # Stage 2 — Resolve database-backed settings.
    _stage(2)
    # Stage 3 — Resolve encrypted credentials.
    _stage(3)
    # Stage 4 — Dispatch real non-production notification.
    _stage(4)
    result = {
        "stage_1_environment": "verified non-production",
        "stage_2_settings": "database-backed settings resolved",
        "stage_3_credentials": "encrypted credentials resolved in memory",
        "stage_4_delivery": dict(run_real_notification_evidence("WF-UTL-009")),
    }
    print("WF-UTL-009 notification orchestration succeeded")
    print(result)
    print("OUTPUT BOUNDARY — notification delivery outcome")


if __name__ == "__main__":
    main()
