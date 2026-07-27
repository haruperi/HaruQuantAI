"""Run every active Brokers workflow example in an isolated process."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

WORKFLOWS = (
    "wf_brk_001_resolve_explicit_adapter.py",
    "wf_brk_002_connect_authenticate_provider_session.py",
    "wf_brk_003_acquire_provider_market_data.py",
    "wf_brk_004_submit_one_broker_mutation.py",
    "wf_brk_005_read_account_execution_state.py",
    "wf_brk_006_stream_provider_connection_events.py",
    "wf_brk_007_correlate_ctrader_response.py",
    "wf_brk_008_handle_unsupported_operation.py",
    "wf_brk_009_inject_canonical_broker_execution.py",
)


def main() -> None:
    """Execute all Broker workflows and report every result."""
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
        f"\nBroker workflows: {len(WORKFLOWS) - len(failures)} passed, "
        f"{len(failures)} failed"
    )
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
