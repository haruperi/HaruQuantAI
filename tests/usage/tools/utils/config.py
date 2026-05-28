"""
Usage example for tools.utils.config.

Run from the project root:

    python tests/usage/tools/utils/config.py
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.utils import get_settings, is_production


def main() -> None:
    """Load and consume non-secret HaruQuant runtime settings."""

    settings = get_settings()

    if is_production():
        environment_note = "Production safeguards should be enabled."
    else:
        environment_note = "Development/local safeguards are active."

    print(
        {
            "environment": settings.environment,
            "app_name": settings.app_name,
            "log_level": settings.log_level,
            "note": environment_note,
        }
    )


if __name__ == "__main__":
    main()
