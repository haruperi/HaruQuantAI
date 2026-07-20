import subprocess
import sys
from pathlib import Path

import pytest

_USAGE_DIRECTORY = Path(__file__).parents[1] / "usage"
_EXPECTED_OUTPUT = {
    "01_contracts.py": "AuditEvent:",
    "02_errors.py": "Routed error event:",
    "03_identity.py": "Stable artifact ID:",
    "04_time.py": "is_fresh': True",
    "05_serialization.py": "Canonical JSON:",
    "06_security.py": "Redaction policy: protected credential allowlist rejected",
    "07_settings.py": "Active settings:",
    "08_logging.py": "Logging verification:",
}


@pytest.mark.parametrize(("filename", "expected"), _EXPECTED_OUTPUT.items())
def test_usage_script_executes_real_work(filename: str, expected: str) -> None:
    import os

    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[3])
    completed = subprocess.run(  # noqa: S603 - fixed local scripts and interpreter.
        [sys.executable, str(_USAGE_DIRECTORY / filename)],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    assert completed.returncode == 0, completed.stderr
    assert expected in completed.stdout
