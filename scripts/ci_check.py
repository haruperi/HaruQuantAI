"""Qualify retained tooling, Stage 0 (`P00`) references, and the React frontend.

Description:
    The pre-push hook invokes this module to validate Python reference tooling
    and the React frontend. `main()` resolves npm and runs checks in sequence,
    preserving child diagnostics and stopping at the first failure. Reference
    tests use temporary files, and offline evidence checks never require an SQX
    installation or database connection.

Purpose:
    FEAT-DEV-QUALIFICATION: Qualify the current repository before publication.
    Keep the mandatory Git hook active while the application is rebuilt.

Key Capabilities:
    - FR-DEV-RESOLVE-NPM: Resolve the platform-specific npm launcher.
      Associated: `main()`
      Logging: INFO records resolution; ERROR records a missing executable.
    - FR-DEV-RUN-CHECKS: Run tooling and frontend checks without silent steps.
      Associated: `main()`
      Logging: INFO records each command and success; ERROR records launch
      failures or nonzero exit codes. Events identify command and exit status.
    - FR-DEV-QUALIFICATION-RESULT: Stop on failure or report full success.
      Associated: `main()`
      Logging: ERROR identifies the blocking check; INFO confirms all checks pass.

Python API Usage:
    ```python
    from app.host.logging import setup_logging, shutdown_logging
    from scripts.ci_check import main

    setup_logging()
    try:
        exit_code = main()
    finally:
        shutdown_logging()
    ```

CLI Usage:
    ```bash
    uv run python scripts/ci_check.py
    ```
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.host.logging import get_logger, setup_logging, shutdown_logging

logger = get_logger(__name__)


def main() -> int:
    """Run bounded checks in order, returning the first failing exit status."""
    root = Path(__file__).resolve().parents[1]
    npm = shutil.which("npm")
    if npm is None:
        logger.error("FR-DEV-RESOLVE-NPM: npm launcher not found")
        return 1
    logger.info("FR-DEV-RESOLVE-NPM: npm launcher resolved")
    audit = root / ".agents/logs/reference-qualification"
    try:
        audit.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        logger.error(  # noqa: TRY400
            "FR-DEV-QUALIFICATION-RESULT: audit directory unavailable (errno=%s)",
            error.errno,
        )
        return 1
    tests = (
        "tests/unit/test_reference_manifest.py",
        "tests/unit/test_reference_fixtures.py",
        "tests/unit/test_reference_validation.py",
    )
    commands = (
        (sys.executable, "-m", "ruff", "check", "scripts"),
        (sys.executable, "-m", "ruff", "format", "--check", "scripts"),
        (
            sys.executable,
            "-m",
            "mypy",
            "--explicit-package-bases",
            "scripts",
        ),
        (sys.executable, "scripts/check_architecture.py"),
        (sys.executable, "-m", "ruff", "check", "tests"),
        (sys.executable, "-m", "ruff", "format", "--check", "tests"),
        (
            sys.executable,
            "-m",
            "mypy",
            "--strict",
            "--explicit-package-bases",
            "tests/reference",
            "tests/unit",
        ),
        (sys.executable, "-m", "tests.reference.validate"),
        (
            sys.executable,
            "-m",
            "pytest",
            *tests,
            "--cov=tests.reference",
            "--cov-config=tests/reference/coverage.toml",
            "--cov-branch",
            "--cov-fail-under=80",
            "--cov-report=term-missing",
            "--cov-report=json:.agents/logs/reference-qualification/coverage.json",
        ),
        (npm, "--prefix", "ui", "run", "typecheck"),
        (npm, "--prefix", "ui", "run", "test"),
        (npm, "--prefix", "ui", "run", "build"),
    )
    for command in commands:
        logger.info("FR-DEV-RUN-CHECKS: running %s", " ".join(command))
        try:
            result = subprocess.run(command, cwd=root, check=False)
        except OSError as error:
            logger.error(  # noqa: TRY400
                "FR-DEV-RUN-CHECKS: launch failed for %s (errno=%s)",
                " ".join(command),
                error.errno,
            )
            return 1
        if result.returncode:
            logger.error(
                "FR-DEV-QUALIFICATION-RESULT: failed %s (exit=%s)",
                " ".join(command),
                result.returncode,
            )
            return result.returncode
        logger.info("FR-DEV-RUN-CHECKS: passed %s (exit=0)", " ".join(command))
    logger.info("FR-DEV-QUALIFICATION-RESULT: all checks passed")
    return 0


if __name__ == "__main__":
    setup_logging()
    try:
        raise SystemExit(main())
    finally:
        shutdown_logging()
