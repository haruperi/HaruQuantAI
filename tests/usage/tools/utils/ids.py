"""
Usage example for tools.utils.ids.

Run from the project root:

    python tests/usage/tools/utils/ids.py
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.utils import (
    is_request_id,
    is_tool_call_id,
    is_workflow_id,
    new_request_id,
    new_run_id,
    new_tool_call_id,
    new_workflow_id,
)


def build_trace_context() -> dict[str, str]:
    """Build a realistic trace context for a workflow step."""

    return {
        "request_id": new_request_id(),
        "workflow_id": new_workflow_id(),
        "run_id": new_run_id(),
        "tool_call_id": new_tool_call_id(),
    }


if __name__ == "__main__":
    trace_context = build_trace_context()

    if not is_request_id(trace_context["request_id"]):
        raise ValueError("Invalid request_id generated.")

    if not is_workflow_id(trace_context["workflow_id"]):
        raise ValueError("Invalid workflow_id generated.")

    if not is_tool_call_id(trace_context["tool_call_id"]):
        raise ValueError("Invalid tool_call_id generated.")

    print(trace_context)
