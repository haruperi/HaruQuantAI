"""Executable Trading reporting usage example.

Demonstrates building trading execution evidence reports.
"""

import sys
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.trading import build_trading_report
from tests.trading.unit.actions.test_dependencies import request
from tests.trading.unit.reporting.test_evidence import ReportStore


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def example_reporting() -> None:
    """Demonstrate Trading report generation."""
    _header("Demonstrate Trading report generation.")
    print("Trading Example 9: Execution Evidence Report Generation")

    req = request(action="sync_positions")
    outcome = build_trading_report(req, ReportStore())
    print(f"Trading report outcome status: {outcome.status}")
    assert outcome.status == "success"
    report = outcome.data
    assert report is not None
    print(f"Report schema ID: {report.schema_id}")


def fr_trd_049() -> None:
    """FR-TRD-049: The system shall emit registered `ExecutionEvidenceReport v1` by packaging officially stored receipts, `TradeRecord` factual costs, readiness, reconciliation, incidents, warnings, and unresolved actions without calculating performance/TCA. `TradingStateStore.load_report_evidence` is the sole report query and returns exact stored JSON-safe facts for one scope."""
    _header(
        "FR-TRD-049: The system shall emit registered `ExecutionEvidenceReport v1` by packaging officially stored receipts, `TradeRecord` factual costs, readiness, reconciliation, incidents, warnings, and unresolved actions without calculating performance/TCA. `TradingStateStore.load_report_evidence` is the sole report query and returns exact stored JSON-safe facts for one scope."
    )
    example_reporting()


def main() -> None:
    """Run Trading reporting usage example."""
    example_reporting()


if __name__ == "__main__":
    main()
