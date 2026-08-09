"""Executable Risk no-trade success-state usage example.

Demonstrates FEAT-RISK-17 classification of a rejected setup as a safe stand-down or failed gameplay.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.risk import (
    build_no_trade_outcome,
    classify_no_trade_outcome,
    parse_no_trade_outcome,
)
from tests.risk._support import unwrap_risk_response

NOW = datetime(2026, 7, 19, tzinfo=UTC)


def _feature_header(title: str) -> None:
    """Print the feature header banner."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type name and field/key signature."""
    if isinstance(obj, dict):
        return f"Output Result -> dict({', '.join(obj.keys())}) : dict"
    return f"Output Result -> {type(obj).__name__} : {type(obj).__name__}"


def fr_risk_085() -> None:
    """FR-RISK-085: Build and parse a bounded NoTradeOutcome v1 contract."""
    _header("No-Trade Contract - Build/Parse NoTradeOutcome v1 (FR-RISK-085)")
    print("SUCCESS: FR-RISK-085")
    built = build_no_trade_outcome(
        decision_id="decision-1",
        outcome_kind="safe_stand_down",
        failed_rule_ids=("kill_switch",),
        rationale="mandatory gate",
        evaluated_at=NOW,
    )
    parsed = parse_no_trade_outcome(built)
    print(_format_result(parsed))
    print(f"Data -> schema_id='{parsed['schema_id']}'")


def fr_risk_086() -> None:
    """FR-RISK-086: Classify a mandatory-gate-only rejection as a safe stand-down."""
    _header("No-Trade Classification - Safe Stand-Down (FR-RISK-086)")
    print("SUCCESS: FR-RISK-086")
    outcome = unwrap_risk_response(
        classify_no_trade_outcome(
            "decision-1", ["kill_switch", "drawdown_state"], now=NOW
        ),
        operation="classify_no_trade_outcome",
    )
    print(_format_result(outcome))
    print(f"Data -> outcome_kind='{outcome['outcome_kind']}'")


def fr_risk_087() -> None:
    """FR-RISK-087: Classify an avoidable execution mistake as failed gameplay."""
    _header("No-Trade Classification - Failed Gameplay (FR-RISK-087)")
    print("SUCCESS: FR-RISK-087")
    outcome = unwrap_risk_response(
        classify_no_trade_outcome(
            "decision-1", ["kill_switch", "stop_noise_distance"], now=NOW
        ),
        operation="classify_no_trade_outcome",
    )
    print(_format_result(outcome))
    print(f"Data -> outcome_kind='{outcome['outcome_kind']}'")


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-RISK-17 — no_trade_state/ — No-Trade Success State\n\n"
        "Purpose: Distinguish a safe stand-down from failed gameplay when mandatory "
        "gates reject a setup.\n\n"
        "Module flow:\n"
        "-> Build/parse the NoTradeOutcome v1 contract\n"
        "-> Classify mandatory-gate-only rejections as safe stand-downs\n"
        "-> Classify avoidable execution mistakes as failed gameplay"
    )
    fr_risk_085()
    fr_risk_086()
    fr_risk_087()


if __name__ == "__main__":
    main()
