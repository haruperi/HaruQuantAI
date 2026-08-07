"""Stage-labelled usage for WF-AGT-002 evidence interpretation."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from tests.agentic.usage.workflows._runner import run_workflow_usage


def main() -> None:
    """Run the deterministic-evidence interpretation stage."""
    run_workflow_usage("WF-AGT-002", ("08_interpretation.py",))


if __name__ == "__main__":
    main()
