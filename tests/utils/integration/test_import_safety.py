"""Process-isolated import-safety proofs for the Utils logging boundary.

These integration proofs spawn fresh interpreters because import-time behavior
cannot be observed inside the shared pytest process. They provide the dynamic
evidence for FR-UTL-032 and the import-inert portion of FR-UTL-039.
"""

import os
import subprocess
import sys
from pathlib import Path


def test_import_registers_no_handlers() -> None:
    command = (
        "import logging; import app.utils; "
        "print(len(logging.getLogger('haruquant').handlers))"
    )
    completed = subprocess.run(  # noqa: S603 - fixed interpreter and source.
        [sys.executable, "-c", command],
        check=True,
        capture_output=True,
        text=True,
    )
    assert completed.stdout.strip() == "0"


def test_import_time_bound_log_does_not_activate_defaults(tmp_path: Path) -> None:
    probe = tmp_path / "lazy_logging_probe.py"
    probe.write_text(
        "from app.utils import get_logger\nget_logger('haruquant').info('import-time record')\n",
        encoding="utf-8",
    )
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join(
        filter(None, (str(tmp_path), environment.get("PYTHONPATH", "")))
    )
    command = (
        "import logging; import lazy_logging_probe; "
        "print(len(logging.getLogger('haruquant').handlers))"
    )

    completed = subprocess.run(  # noqa: S603 - fixed interpreter and source.
        [sys.executable, "-c", command],
        check=True,
        capture_output=True,
        text=True,
        cwd=Path(__file__).parents[3],
        env=environment,
    )

    assert completed.stdout.strip() == "0"
    assert not (tmp_path / "data" / "logs").exists()
