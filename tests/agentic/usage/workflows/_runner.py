"""Shared execution support for Agentic workflow usage programs."""

from __future__ import annotations

import contextlib
import io
import json
import runpy
from pathlib import Path


def run_workflow_usage(workflow_id: str, feature_programs: tuple[str, ...]) -> None:
    """Execute feature stages and emit one bounded workflow result.

    Args:
        workflow_id: Active workflow registry identity.
        feature_programs: Ordered feature-program filenames forming the stages.
    """
    feature_root = Path(__file__).resolve().parents[1] / "features"
    stages: list[dict[str, object]] = []
    for stage, filename in enumerate(feature_programs, start=1):
        namespace = runpy.run_path(str(feature_root / filename), run_name="usage_stage")
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            namespace["main"]()
        stages.append(
            {
                "stage": stage,
                "feature_program": filename,
                "actual_data": tuple(
                    line for line in captured.getvalue().splitlines() if line
                ),
            }
        )
    print(f"SUCCESS: {workflow_id} workflow usage completed")
    print(json.dumps({"workflow_id": workflow_id, "stages": stages}))


__all__ = ("run_workflow_usage",)
