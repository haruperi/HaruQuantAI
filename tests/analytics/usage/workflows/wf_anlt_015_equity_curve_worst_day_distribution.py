"""WF-ANLT-015: show calculated worst-day loss distribution evidence."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from decimal import Decimal

from app.services.analytics import (
    build_worst_day_distribution,
    create_closed_trade_ledger,
    get_analytics_value_field,
)
from tests.analytics.usage.workflows._support import examples

WORKFLOW_ID = "WF-ANLT-015"
STAGES = ("Build observed closed-trade equity data.", "Calculate loss distribution.")


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(f"{'=' * 88}\nStage {number}/{len(STAGES)}\n{'=' * 88}")


def main() -> None:
    """Execute the documented Analytics-only part of the workflow."""
    # Stage 1: INPUT BOUNDARY -- observed closed-trade facts.
    _stage(1)
    result, _ = examples._configured_result()
    ledger = create_closed_trade_ledger(
        daily_pnl=(Decimal(-15), Decimal(8), Decimal(-4))
    )
    distribution = examples.unwrap(
        build_worst_day_distribution(
            ledger, percentiles=(Decimal("0.5"), Decimal("0.95"))
        )
    )
    # Stage 2: OUTPUT BOUNDARY -- calculated distribution evidence.
    _stage(2)
    print("Daily curve:", get_analytics_value_field(result, "daily_equity_curve"))
    print("Worst-day distribution:", distribution)
    print(
        "Barrier analysis: unavailable; no verified Optimization first-passage input."
    )


if __name__ == "__main__":
    main()
