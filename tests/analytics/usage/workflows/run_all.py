"""Execute every active Analytics workflow usage program."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

WORKFLOWS = (
    "wf_anlt_pri_build_canonical_performance_report.py",
    "wf_anlt_ter_calculate_grouped_analytics_evidence.py",
    "wf_anlt_003_benchmark_relative_analysis.py",
    "wf_anlt_005_build_dashboard_payload.py",
    "wf_anlt_sec_adapt_upstream_result.py",
    "wf_anlt_007_run_statistical_validation.py",
    "wf_anlt_008_serialize_hash_report.py",
    "wf_anlt_009_build_portfolio_performance_report.py",
    "wf_anlt_010_compare_performance_reports.py",
    "wf_anlt_013_build_portfolio_allocation_evidence.py",
    "wf_anlt_014_measure_reconciled_portfolio_rebalance.py",
)


def main() -> None:
    """Import and execute all workflow programs in registry order."""
    package = "tests.analytics.usage.workflows"
    for filename in WORKFLOWS:
        importlib.import_module(f"{package}.{filename[:-3]}").main()
    print(f"\nAnalytics workflows completed: {len(WORKFLOWS)}/{len(WORKFLOWS)}")


if __name__ == "__main__":
    main()
