"""Import-safety evidence for the Analytics package root."""

# ruff: noqa: INP001
import os
import subprocess
import sys
from pathlib import Path

from app.utils import logger

_ROOT = Path(__file__).resolve().parents[3]


def test_package_root_import_is_quiet_and_does_not_mutate_filesystem(
    tmp_path: Path,
) -> None:
    """A fresh Analytics import emits nothing and creates no local artifacts."""
    logger.info("Testing Analytics package-root import safety")
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        [sys.executable, "-c", "import app.services.analytics"],
        cwd=tmp_path,
        env={**environment, "PYTHONPATH": str(_ROOT)},
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0
    assert completed.stdout == ""
    assert completed.stderr == ""
    assert tuple(tmp_path.iterdir()) == ()
