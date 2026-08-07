"""Stage-labelled usage for WF-AGT-012 tool permission approval."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from tests.agentic.usage.workflows._runner import run_workflow_usage


def main() -> None:
    """Run permission and approval stages."""
    run_workflow_usage("WF-AGT-012", ("05_permissions.py",))


if __name__ == "__main__":
    main()
