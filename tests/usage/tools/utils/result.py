"""
Usage example for tools.utils.result.

Run from the project root:

    python tests/usage/tools/utils/result.py
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.utils import blocked_result
from tools.utils import error_result
from tools.utils import success_result


def validate_symbol(symbol: str, request_id: str) -> dict:
    """Demonstrate returning a structured validation result."""

    if not symbol.strip():
        return error_result(
            "Symbol validation failed.",
            code="INVALID_INPUT",
            details="symbol cannot be empty.",
            request_id=request_id,
            workflow_id="usage-result-workflow-001",
            source="tests.usage.tools.utils.result",
        )

    return success_result(
        "Symbol validation passed.",
        data={"symbol": symbol.upper()},
        request_id=request_id,
        workflow_id="usage-result-workflow-001",
        source="tests.usage.tools.utils.result",
        metadata={"stage": "validation"},
    )


def check_policy(can_continue: bool, request_id: str) -> dict:
    """Demonstrate returning a blocked result from a policy check."""

    if not can_continue:
        return blocked_result(
            "Operation blocked by policy.",
            details="The workflow cannot continue without valid evidence.",
            request_id=request_id,
            workflow_id="usage-result-workflow-001",
            source="tests.usage.tools.utils.result",
        )

    return success_result(
        "Policy check passed.",
        data={"allowed": True},
        request_id=request_id,
        workflow_id="usage-result-workflow-001",
        source="tests.usage.tools.utils.result",
    )


if __name__ == "__main__":
    request_id = "usage-result-001"

    validation = validate_symbol("EURUSD", request_id=request_id)
    if validation["status"] == "success":
        print(validation["data"])
    else:
        print(validation["error"])

    policy = check_policy(can_continue=False, request_id=request_id)
    if policy["status"] == "blocked":
        print(policy["error"])
