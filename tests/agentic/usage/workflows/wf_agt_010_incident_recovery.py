"""Stage-labelled usage for WF-AGT-010 incident recovery."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from tests.agentic.usage.workflows._runner import run_workflow_usage


def main() -> None:
    """Run operations and operator containment stages."""
    run_workflow_usage("WF-AGT-010", ("21_operations.py", "22_public_api.py"))


if __name__ == "__main__":
    main()
