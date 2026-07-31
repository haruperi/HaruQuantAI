"""Executable Optimization scoring usage example.

Demonstrates FEAT-OPT-02 objective names, candidate scoring, deflated Sharpe calculation, candidate ranking, Pareto candidate selection, and overfit assessment.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.optimization import (
    assess_overfit_evidence,
    calculate_candidate_score,
    calculate_deflated_sharpe,
    count_nominal_trials,
    rank_candidates,
    select_pareto_candidates,
)
from tests.optimization.usage._support import performance_report


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


def fr_opt_006() -> None:
    """FR-OPT-006: Stage 1 — Objective Definition.

    The system shall support canonical objective definitions for scoring optimization candidates.
    """
    _header("Stage 1: Objective Definition - Canonical Objectives (FR-OPT-006)")
    objectives = ("net_pnl", "sharpe_ratio", "max_drawdown")
    print(_format_result(objectives))
    print(f"Data -> canonical_objectives={objectives}")


def fr_opt_007() -> None:
    """FR-OPT-007: Stage 2 — Candidate Score Calculation.

    The system shall calculate candidate scores from externally owned Analytics PerformanceReports.
    """
    _header("Stage 2: Score Calculation - Calculate Candidate Score (FR-OPT-007)")
    report = performance_report()
    score_res = calculate_candidate_score(
        report,
        candidate_hash="a" * 64,
        objective="net_pnl",
        enabled_objectives=frozenset({"net_pnl"}),
    )
    print(_format_result(score_res))
    print(f"Data -> objective='{score_res.objective}', value={score_res.value}")


def fr_opt_008() -> None:
    """FR-OPT-008: Stage 2 — Deflated Sharpe Ratio Calculation.

    The system shall calculate Deflated Sharpe Ratio evidence to adjust for multiple testing.
    """
    _header("Stage 2: Deflated Sharpe - Calculate Deflated Sharpe Ratio (FR-OPT-008)")
    dsr = calculate_deflated_sharpe(
        sharpe=1.0,
        variance=0.2,
        skewness=0.0,
        kurtosis=3.0,
        sample_count=100,
        nominal_trials=10,
    )
    print(_format_result(dsr))
    print(f"Data -> deflated_sharpe={dsr}")


def fr_opt_009() -> None:
    """FR-OPT-009: Stage 2 — Nominal Trial Counting.

    The system shall count nominal trials across candidate evaluations.
    """
    _header("Stage 2: Trial Counting - Count Nominal Trials (FR-OPT-009)")
    trials = count_nominal_trials(("a" * 64, "b" * 64))
    print(_format_result(trials))
    print(f"Data -> nominal_trials={trials}")


def fr_opt_010() -> None:
    """FR-OPT-010: Stage 3 — Candidate Ranking.

    The system shall deterministically rank candidate scores according to objective direction.
    """
    _header("Stage 3: Candidate Ranking - Rank Candidates (FR-OPT-010)")
    report = performance_report()
    s1 = calculate_candidate_score(
        report,
        candidate_hash="a" * 64,
        objective="net_pnl",
        enabled_objectives=frozenset({"net_pnl"}),
    )
    s2 = calculate_candidate_score(
        report,
        candidate_hash="b" * 64,
        objective="net_pnl",
        enabled_objectives=frozenset({"net_pnl"}),
    )
    ranked = rank_candidates((s1, s2))
    print(_format_result(ranked))
    print(f"Data -> top_candidate_value={ranked[0].value if ranked else None}")


def fr_opt_011() -> None:
    """FR-OPT-011: Stage 3 — Pareto Candidate Selection.

    The system shall select non-dominated Pareto candidate sets for multi-objective trade-offs.
    """
    _header("Stage 3: Pareto Selection - Select Pareto Candidates (FR-OPT-011)")
    pareto_indices = select_pareto_candidates(
        ({"net_pnl": 1.0}, {"net_pnl": 2.0}), ("net_pnl",)
    )
    print(_format_result(pareto_indices))
    print(f"Data -> pareto_indices={pareto_indices}")


def fr_opt_012() -> None:
    """FR-OPT-012: Stage 3 — Overfit Assessment.

    The system shall assess in-sample vs out-of-sample overfit evidence and trade count adequacy.
    """
    _header("Stage 3: Overfit Assessment - Assess Overfit Evidence (FR-OPT-012)")
    report = performance_report()
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
    print(_format_result(overfit_diag))
    print(
        f"Data -> trade_count_adequate={overfit_diag.get('trade_count_adequate') if isinstance(overfit_diag, dict) else None}"
    )


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-OPT-02 — scoring/ — Objectives, Ranking, and Overfit Evidence\n\n"
        "Purpose: Define canonical objectives, calculate candidate scores and Deflated Sharpe Ratios, rank candidates deterministically, select Pareto sets, and assess overfit evidence.\n\n"
        "Module flow:\n"
        "-> Stage 1: Objective definition input mapping\n"
        "-> Stage 2: Candidate score calculation, trial counting, and Deflated Sharpe evaluation\n"
        "-> Stage 3: Deterministic ranking, Pareto selection, and overfit evidence assessment"
    )

    # Stage 1: Objectives
    fr_opt_006()

    # Stage 2: Scoring, DSR & Trials
    fr_opt_007()
    fr_opt_008()
    fr_opt_009()

    # Stage 3: Ranking, Pareto & Overfit
    fr_opt_010()
    fr_opt_011()
    fr_opt_012()


if __name__ == "__main__":
    main()
