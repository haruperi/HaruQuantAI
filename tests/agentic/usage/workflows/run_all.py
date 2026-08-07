"""Run every active Agentic workflow usage program."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> None:
    """Execute every stage-labelled workflow program in registry order."""
    root = Path(__file__).resolve().parent
    programs = sorted(root.glob("wf_agt_*.py"))
    for program in programs:
        completed = subprocess.run(  # noqa: S603 - fixed local interpreter and files.
            [sys.executable, str(program)],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if completed.returncode != 0:
            raise RuntimeError(f"{program.name} failed: {completed.stderr}")
        print(completed.stdout.strip())


if __name__ == "__main__":
    main()
