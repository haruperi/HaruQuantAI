"""Standalone Automation Mode Policy feature evidence."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.strategy import (
    ensure_strategy_storage,
    evaluate_automation_mode,
    list_automation_policies,
    persist_automation_policy,
)

_REQUEST = "req-00000000-0000-4000-8000-000000000099"
_CORRELATION = "cor-00000000-0000-4000-8000-000000000099"


def _emit(requirement: str, value: object) -> None:
    """Print exactly one success message and its genuine produced value."""
    print(f"Success: {requirement}")
    print(value)


def _persist_demonstration() -> None:
    """Exercise production automation-policy persistence and listing when enabled."""
    if os.environ.get("RUN_STRATEGY_STATEFUL_USAGE") != "1":
        return
    ensure_strategy_storage(_REQUEST)
    persisted = persist_automation_policy(
        strategy_id="trend",
        strategy_version="1.0.0",
        mode="SUPERVISED",
        request_id=_REQUEST,
        correlation_id=_CORRELATION,
    )
    _emit("FEAT-STR-18 persistence", persisted["record_hash"])
    _emit(
        "FEAT-STR-18 automation policy list",
        list_automation_policies(request_id=_REQUEST),
    )


def fr_str_078() -> None:
    _emit(
        "FR-STR-078",
        evaluate_automation_mode(
            "OFF",
            risk_interlock=False,
            trading_interlock=False,
            route="SIM",
            environment="PAPER",
        ),
    )


def fr_str_079() -> None:
    _emit(
        "FR-STR-079",
        evaluate_automation_mode(
            "AUTOMATED",
            risk_interlock=True,
            trading_interlock=True,
            route="SIM",
            environment="PAPER",
        ),
    )


def main() -> None:
    """Run every Automation Mode Policy requirement example."""
    for number in (78, 79):
        globals()[f"fr_str_{number:03d}"]()
    _persist_demonstration()


if __name__ == "__main__":
    main()
