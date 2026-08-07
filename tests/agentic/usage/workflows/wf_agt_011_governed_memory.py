"""Stage-labelled usage for WF-AGT-011 governed memory."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from tests.agentic.usage.workflows._runner import run_workflow_usage


def main() -> None:
    """Run context and governed-memory stages."""
    run_workflow_usage("WF-AGT-011", ("06_context_memory.py",))


if __name__ == "__main__":
    main()
