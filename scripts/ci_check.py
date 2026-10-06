"""Qualify retained tooling and the frontend before pushing the reset baseline.

Description:
    The pre-push hook invokes this module to validate retained Python tooling and
    the React frontend. `main()` resolves npm and runs checks in sequence,
    preserving child diagnostics and stopping at the first failure. Deleted
    application and test directories are outside this reset baseline.

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
      Logging: ERROR identifies the blocking check; INFO confirms all six pass.

Python API Usage:
    ```python
    import logging
    from scripts.ci_check import main

    logging.basicConfig(level=logging.INFO)
    exit_code = main()
    ```

CLI Usage:
    ```bash
    uv run python scripts/ci_check.py
    ```
"""

from __future__ import annotations

import logging
import shutil
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def main() -> int:
    """Run bounded checks in order, returning the first failing exit status."""
    root = Path(__file__).resolve().parents[1]
    npm = shutil.which("npm")
    if npm is None:
        logger.error("FR-DEV-RESOLVE-NPM: npm launcher not found")
        return 1
    logger.info("FR-DEV-RESOLVE-NPM: npm launcher resolved")
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
        (npm, "--prefix", "ui", "run", "typecheck"),
        (npm, "--prefix", "ui", "run", "test"),
        (npm, "--prefix", "ui", "run", "build"),
    )
    for command in commands:
        logger.info("FR-DEV-RUN-CHECKS: running %s", " ".join(command))
        try:
            result = subprocess.run(command, cwd=root, check=False)
        except OSError as error:
            # Log only errno; exception text can contain sensitive environment data.
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
    logger.info("FR-DEV-QUALIFICATION-RESULT: all six checks passed")
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    raise SystemExit(main())
