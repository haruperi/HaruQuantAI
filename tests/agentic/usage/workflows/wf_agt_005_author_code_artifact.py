"""Stage-labelled usage for WF-AGT-005 code artifact authoring."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from tests.agentic.usage.workflows._runner import run_workflow_usage


def main() -> None:
    """Run governed code-authoring and evaluation stages."""
    run_workflow_usage("WF-AGT-005", ("16_coding.py", "17_evaluation.py"))


if __name__ == "__main__":
    main()
