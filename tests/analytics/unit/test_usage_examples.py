"""Coverage wrapper for analytics usage examples."""

from __future__ import annotations

import runpy
from pathlib import Path


def test_analytics_usage_examples_run() -> None:
    """Execute the documented analytics usage examples under pytest coverage."""
    project_root = Path(__file__).resolve().parents[3]
    usage_file = project_root / "tests" / "analytics" / "usage" / "06_analytics.py"

    runpy.run_path(str(usage_file), run_name="__main__")
