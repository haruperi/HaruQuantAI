import subprocess
import sys
from pathlib import Path

import pytest

_USAGE_DIRECTORY = Path(__file__).parents[1] / "usage" / "features"
_EXPECTED_OUTPUT = {
    "01_contracts.py": "Data -> principal_id='service-demo'",
    "02_errors.py": "Data -> routed_code='INTERNAL_ERROR'",
    "03_identity.py": "Data -> validated_workflow_id=",
    "04_time.py": "Data -> age_seconds=1, is_fresh=True",
    "05_serialization.py": "Data -> canonical_digest=",
    "06_security.py": "Data -> truncated=False, redacted_paths=",
    "07_settings.py": "Data -> environment='test', runtime_profile='research'",
    "08_logging.py": "Data -> non_empty_log_files=",
    "09_standard_responses.py": "Data -> immutable_mapping_keys=",
    "features.py": "Data -> full_domain_pipeline_status='completed'",
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
