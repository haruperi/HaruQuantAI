import subprocess
import sys
from pathlib import Path

import pytest

_USAGE_DIRECTORY = Path(__file__).parents[1] / "usage"
_EXPECTED_OUTPUT = {
    "01_contracts.py": "AuditEvent:",
    "02_errors.py": "Routed event:",
    "03_identity.py": "Stable:",
    "04_time.py": "fresh: True",
    "05_serialization.py": "Canonical JSON:",
    "06_security.py": "authenticated decryption succeeded",
    "07_settings.py": "Constructed:",
    "08_logging.py": "Verified app.log, access.log, debug.log, and errors.log",
}


@pytest.mark.parametrize(("filename", "expected"), _EXPECTED_OUTPUT.items())
def test_usage_script_executes_real_work(filename: str, expected: str) -> None:
    completed = subprocess.run(  # noqa: S603 - fixed local scripts and interpreter.
        [sys.executable, str(_USAGE_DIRECTORY / filename)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert expected in completed.stdout
    if filename == "08_logging.py":
        standard_heading = completed.stdout.index(
            "1.1 Standard structured logging levels"
        )
        standard_record = completed.stdout.index(
            "This is a debug message containing developer details."
        )
        exception_heading = completed.stdout.index(
            "1.2 Logging exceptions with tracebacks"
        )
        assert standard_heading < standard_record < exception_heading
        assert (
            " | \033[36mDEBUG   \033[0m | __main__:example_standard_levels:"
            in completed.stdout
        )
        assert (
            " - \033[36mThis is a debug message containing developer details.\033[0m"
            in completed.stdout
        )
