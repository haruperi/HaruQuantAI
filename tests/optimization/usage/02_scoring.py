"""Executable Optimization scoring usage example.

Demonstrates objective names, candidate scoring, deflated Sharpe calculation,
candidate ranking, Pareto candidate selection, and overfit assessment.
"""

import sys
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.optimization import (
    assess_overfit_evidence,
    calculate_candidate_score,
    calculate_deflated_sharpe,
    count_nominal_trials,
    rank_candidates,
    select_pareto_candidates,
)
from tests.optimization.usage._support import performance_report


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def example_scoring() -> None:
    """Demonstrate candidate scoring, ranking, and overfit assessment."""
    _header("Demonstrate candidate scoring, ranking, and overfit assessment.")
    print("Optimization Example 2: Candidate Scoring and Pareto Selection")

    print("Canonical objective list: net_pnl, sharpe_ratio, max_drawdown")

    # 2. Score candidate from Analytics report
    report = performance_report()
    score_res = calculate_candidate_score(
        report,
        candidate_hash="a" * 64,
        objective="net_pnl",
        enabled_objectives=frozenset({"net_pnl"}),
    )
    print(
        f"Calculated candidate score: objective={score_res.objective}, "
        f"value={score_res.value}"
    )

    # 3. Deflated Sharpe ratio calculation
    dsr = calculate_deflated_sharpe(
        sharpe=1.0,
        variance=0.2,
        skewness=0.0,
        kurtosis=3.0,
        sample_count=100,
        nominal_trials=10,
    )
    print(f"Calculated Deflated Sharpe Ratio: {dsr}")

    # 4. Count trials and rank candidates
    trials = count_nominal_trials(("a" * 64, "b" * 64))
    print(f"Nominal trials count: {trials}")

    second = calculate_candidate_score(
        report,
        candidate_hash="b" * 64,
        objective="net_pnl",
        enabled_objectives=frozenset({"net_pnl"}),
    )
    ranked = rank_candidates((score_res, second))
    print(f"Ranked top candidate value: {ranked[0].value}")

    # 5. Pareto candidate selection
    pareto_indices = select_pareto_candidates(
        ({"net_pnl": 1.0}, {"net_pnl": 2.0}), ("net_pnl",)
    )
    print(f"Pareto optimal candidate indices: {pareto_indices}")

    # 6. Overfit assessment
    overfit_in = calculate_candidate_score(
        report,
        candidate_hash="c" * 64,
        objective="net_pnl",
        enabled_objectives=frozenset({"net_pnl"}),
    )
    overfit_out = calculate_candidate_score(
        report,
        candidate_hash="d" * 64,
        objective="net_pnl",
        enabled_objectives=frozenset({"net_pnl"}),
    )
    overfit_diag = assess_overfit_evidence(
        in_sample=overfit_in,
        out_of_sample=overfit_out,
        nominal_trials=2,
        deflated_sharpe=0.7,
        minimum_trade_count=30,
    )
    print(f"Overfit trade count adequate: {overfit_diag['trade_count_adequate']}")


def main() -> None:
    """Run Optimization scoring usage example."""
    example_scoring()


if __name__ == "__main__":
    main()
