"""Integration evidence for Agentic feature usage programs."""

import subprocess
import sys
from pathlib import Path


def test_feature_usage_registry_and_execution() -> None:
    """Every registered feature has one successful two-record program."""
    usage_root = Path("tests/agentic/usage/features")
    programs = sorted(usage_root.glob("[0-9][0-9]_*.py"))
    assert [path.name[:2] for path in programs] == [
        f"{number:02d}" for number in range(1, 23)
    ]

    for number, program in enumerate(programs, start=1):
        completed = subprocess.run(  # noqa: S603 - fixed local usage programs only.
            [sys.executable, str(program)],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert completed.returncode == 0, completed.stderr
        lines = completed.stdout.splitlines()
        assert len(lines) == 2
        assert lines[0] == f"SUCCESS: FEAT-AGT-{number:02d} usage completed"
        assert '"actual_data":' in lines[1]
        assert completed.stderr == ""
