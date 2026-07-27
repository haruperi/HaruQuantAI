"""Run every active Utils workflow example in an isolated process."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

WORKFLOWS = (
    "wf_utl_001_structured_logging_and_redaction.py",
    "wf_utl_002_shared_settings_bootstrap.py",
    "wf_utl_003_audit_event_construction.py",
)


def main() -> None:
    """Execute all Utils workflows and report every result."""
    directory = Path(__file__).resolve().parent
    failures: list[str] = []
    for filename in WORKFLOWS:
        print(f"\nRUNNING {filename}", flush=True)
        completed = subprocess.run(  # noqa: S603 - fixed local workflow scripts.
            [sys.executable, str(directory / filename)],
            check=False,
        )
        status = "PASS" if completed.returncode == 0 else "FAIL"
        print(f"{status} {filename}", flush=True)
        if completed.returncode:
            failures.append(filename)
    print(
        f"\nUtils workflows: {len(WORKFLOWS) - len(failures)} passed, {len(failures)} failed"
    )
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
