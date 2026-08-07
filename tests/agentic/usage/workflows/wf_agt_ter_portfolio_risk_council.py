"""Stage-labelled usage for WF-AGT-TER portfolio and risk council."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from tests.agentic.usage.workflows._runner import run_workflow_usage


def main() -> None:
    """Run portfolio and risk advisory stages."""
    run_workflow_usage("WF-AGT-TER", ("19_advisory.py", "22_public_api.py"))


if __name__ == "__main__":
    main()
