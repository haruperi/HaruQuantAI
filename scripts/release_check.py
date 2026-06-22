#!/usr/bin/env python
"""Release validation runner for HaruQuantAI.

Ensures all CI checks pass before allowing release processes to run.
"""

import subprocess
import sys
from pathlib import Path


def main() -> None:
    """Run release safety check gates."""
    print("========================================")
    print("Starting Pre-Release Safety Checks...")
    print("========================================\n")

    # Run the quality gates script
    script_dir = Path(__file__).resolve().parent
    ci_script = script_dir / "ci_check.py"

    print("Verifying codebase health via CI script...")
    result = subprocess.run(
        ["uv", "run", "python", str(ci_script)],
        capture_output=False,
        check=False,
    )

    if result.returncode != 0:
        print("\n========================================")
        print("[CRITICAL] Code quality check failed! Release blocked.")
        print("========================================\n")
        sys.exit(result.returncode)

    print("\n========================================")
    print("[SUCCESS] All pre-release checks passed! Ready for release.")
    print("========================================\n")
    sys.exit(0)


if __name__ == "__main__":
    main()
