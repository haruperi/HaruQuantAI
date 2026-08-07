"""Stage-labelled usage for WF-AGT-SEC artifact promotion."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from tests.agentic.usage.workflows._runner import run_workflow_usage


def main() -> None:
    """Run evaluation, lifecycle, and operator-control stages."""
    run_workflow_usage(
        "WF-AGT-SEC",
        ("17_evaluation.py", "18_lifecycle.py", "22_public_api.py"),
    )


if __name__ == "__main__":
    main()
