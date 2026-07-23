"""Executable Trading reporting usage example.

Demonstrates building trading execution evidence reports.
"""

import sys
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.trading.reporting import build_trading_report
from tests.trading.unit.actions.test_dependencies import request
from tests.trading.unit.reporting.test_evidence import ReportStore


def example_reporting() -> None:
    """Demonstrate Trading report generation."""
    print("=" * 80)
    print("Trading Example 9: Execution Evidence Report Generation")
    print("=" * 80)

    req = request(action="sync_positions")
    outcome = build_trading_report(req, ReportStore())
    print(f"Trading report outcome status: {outcome.status}")
    print(f"Report schema ID: {outcome.data['schema_id']}")


def main() -> None:
    """Run Trading reporting usage example."""
    example_reporting()


if __name__ == "__main__":
    main()
