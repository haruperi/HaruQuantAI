"""Stage-labelled usage for WF-AGT-004 bounded optimization."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from tests.agentic.usage.workflows._runner import run_workflow_usage


def main() -> None:
    """Run experiment and bounded-search stages."""
    run_workflow_usage("WF-AGT-004", ("14_experiments.py", "15_optimization.py"))


if __name__ == "__main__":
    main()
