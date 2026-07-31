"""Executable Trading reporting usage example.

Demonstrates FEAT-TRD-09 building trading execution evidence reports.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.trading import build_trading_report
from tests.trading.unit.actions.test_dependencies import request
from tests.trading.unit.reporting.test_evidence import ReportStore


def _feature_header(title: str) -> None:
    """Print the feature header banner."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type name and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


def fr_trd_049() -> None:
    """FR-TRD-049: Stage 3 — Emit registered ExecutionEvidenceReport v1 by packaging stored facts."""
    _header("Stage 3: Report Generation - Build Execution Evidence Report (FR-TRD-049)")
    req = request(action="sync_positions")
    outcome = build_trading_report(req, ReportStore())
    print(_format_result(outcome))
    print(
        f"Data -> status='{outcome.status}', schema_id='{outcome.data.schema_id if outcome.data else None}'"
    )


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-TRD-09 — reporting/ — Immutable Execution Evidence\n\n"
        "Purpose: Package officially stored receipts, trade record costs, readiness, reconciliation, and incidents into immutable execution evidence reports.\n\n"
        "Module flow:\n"
        "-> Stage 1: Report request parameter binding and scope definition\n"
        "-> Stage 2: Stored report evidence loading via TradingStateStore\n"
        "-> Stage 3: ExecutionEvidenceReport v1 contract construction and response packaging"
    )

    # Stage 3: Report generation
    fr_trd_049()


if __name__ == "__main__":
    main()
