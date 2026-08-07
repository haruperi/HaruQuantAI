"""Stage-labelled usage for WF-AGT-PRI firm research council."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from tests.agentic.usage.workflows._runner import run_workflow_usage


def main() -> None:
    """Run governance, context, deliberation, and public-boundary stages."""
    run_workflow_usage(
        "WF-AGT-PRI",
        (
            "02_governance.py",
            "06_context_memory.py",
            "07_deliberation.py",
            "22_public_api.py",
        ),
    )


if __name__ == "__main__":
    main()
