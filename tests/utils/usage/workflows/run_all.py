"""Run every active Utils workflow example in an isolated process."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

WORKFLOWS = (
    "wf_utl_pri_structured_logging_and_redaction.py",
    "wf_utl_sec_shared_settings_bootstrap.py",
    "wf_utl_ter_audit_event_construction.py",
    "wf_utl_004_standard_operation_response_envelope.py",
    "wf_utl_005_error_normalization_and_routing.py",
    "wf_utl_006_trace_identity_and_utc_time.py",
    "wf_utl_007_canonical_serialization_and_digest.py",
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
            capture_output=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )
        print(completed.stdout, end="")
        print(completed.stderr, end="", file=sys.stderr)
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
