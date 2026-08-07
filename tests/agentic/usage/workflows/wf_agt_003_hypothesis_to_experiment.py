"""Stage-labelled usage for WF-AGT-003 hypothesis to experiment."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from tests.agentic.usage.workflows._runner import run_workflow_usage


def main() -> None:
    """Run research, thesis, and experiment stages."""
    run_workflow_usage(
        "WF-AGT-003",
        ("09_fundamental.py", "13_thesis.py", "14_experiments.py"),
    )


if __name__ == "__main__":
    main()
