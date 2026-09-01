"""WF-ANLT-PRI: build a canonical performance report end to end."""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from app.kernel.identity import generate_id
from app.services.analytics import (
    adapt_trading_result,
    build_performance_report,
    calculate_grouped_evidence,
)
from tests.analytics.usage.workflows._support import examples

WORKFLOW_ID = "WF-ANLT-PRI"
STAGES = (
    "Accept a versioned closed-trade ledger plus initial balance and currency.",
    "Adapt the approved source to canonical TradingResult without silent field loss.",
    "Calculate only catalog-approved grouped metric evidence.",
    "Build sections, warnings, lineage, finite validation, and reproducibility hashes.",
    "Return PerformanceReport v1 or AnalyticsValidationError without writes.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Run the documented input-to-output workflow."""
    # Stage 1 — INPUT BOUNDARY: Trading/Simulation supplies a versioned closed ledger.
    _stage(1)
    source, config = examples._source(), examples._configured()
    print("Input:", source["schema_id"], len(source["closed_trades"]))
    # Stage 2: Adapt through the public receiver boundary.
    _stage(2)
    result = examples.unwrap(
        adapt_trading_result(
            source,
            source_contract="simulation.result",
            initial_balance=Decimal(1000),
            account_currency="USD",
            config=config,
        )
    )
    print("Adapted:", result.schema_id, len(result.trades))
    # Stage 3: Calculate approved grouped evidence.
    _stage(3)
    sections = examples.unwrap(calculate_grouped_evidence(result, config=config))
    print("Metric sections:", tuple(section.section_key for section in sections))
    # Stage 4: Compose the canonical report.
    _stage(4)
    report = examples.unwrap(
        build_performance_report(
            source,
            source_contract="simulation.result",
            request_id=generate_id("req"),
            correlation_id=generate_id("cor"),
            created_at=examples.NOW,
            initial_balance=Decimal(1000),
            account_currency="USD",
            config=config,
        )
    )
    print("Report sections:", len(report.sections), "hash:", report.hashes.report_hash)
    # Stage 5 — OUTPUT BOUNDARY: Return PerformanceReport v1; Analytics writes nothing.
    _stage(5)
    print("Output:", type(report).__name__, report.schema_id)


if __name__ == "__main__":
    main()
