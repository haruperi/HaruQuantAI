"""Executable Optimization execution usage example.

Demonstrates backtest execution adapter interface, execution request, error handling,
and candidate execution.
"""

import sys
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.analytics import get_analytics_value_field
from app.services.optimization import execute_candidate, get_optimization_value_field
from tests.optimization.usage._support import genuine_execution_bundle


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def example_execution() -> None:
    """Demonstrate candidate execution engine integration."""
    _header("Demonstrate candidate execution engine integration.")
    print("Optimization Example 4: Candidate Execution")

    dataset, req, adapter = genuine_execution_bundle()
    print(f"Execution request contract version: {req.contract_version}")
    print(
        f"Genuine input: {len(dataset.records)} MT5-derived {dataset.symbol} "
        f"ticks; first={dataset.records[0]}"
    )

    # Execute candidate
    res = execute_candidate(req, adapter, deterministic_only=True)
    report = get_optimization_value_field(res, "analytics_report")
    sections = get_analytics_value_field(report, "sections")
    pnl_section = next(section for section in sections if section.section_key == "pnl")
    print(
        "Real adapter execution evidence:",
        {
            "candidate_hash": res.candidate_hash,
            "simulation_run_id": res.simulation_run_id,
            "simulation_request_hash": res.simulation_request_hash,
            "analytics_report_id": get_analytics_value_field(report, "report_id"),
            "pnl_metrics": tuple(
                (metric.metric_key, metric.value) for metric in pnl_section.metrics
            ),
        },
    )


def main() -> None:
    """Run Optimization execution usage example."""
    example_execution()


if __name__ == "__main__":
    main()
