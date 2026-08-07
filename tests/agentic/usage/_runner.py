"""Output normalization for standalone Agentic usage programs."""

from __future__ import annotations

import contextlib
import io
import json
from collections.abc import Callable


def run_feature_usage(feature_id: str, operation: Callable[[], None]) -> None:
    """Run one feature example and emit exactly two bounded output records.

    Args:
        feature_id: Registered feature identity demonstrated by the program.
        operation: Complete usage demonstration to execute.
    """
    captured = io.StringIO()
    with contextlib.redirect_stdout(captured):
        operation()
    actual_data = tuple(line for line in captured.getvalue().splitlines() if line)
    print(f"SUCCESS: {feature_id} usage completed")
    print(json.dumps({"feature_id": feature_id, "actual_data": actual_data}))


__all__ = ("run_feature_usage",)
