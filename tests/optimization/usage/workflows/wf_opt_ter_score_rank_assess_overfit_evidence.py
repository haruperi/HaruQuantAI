"""WF-OPT-TER: score, rank, and assess overfit evidence."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.optimization.scoring import (
    ObjectiveName,
    assess_overfit_evidence,
    calculate_candidate_score,
    calculate_deflated_sharpe,
    count_nominal_trials,
    rank_candidates,
)
from tests.analytics._support import _report

WORKFLOW_ID = "WF-OPT-TER"
STAGES = (
    "Receive Analytics-owned candidate and trade evidence.",
    "Calculate the enabled objective score only.",
    "Calculate Deflated Sharpe and unique nominal-trial evidence.",
    "Rank candidates with deterministic tie breaking.",
    "Assess IS/OOS degradation and return caveated overfit evidence.",
)


# fmt: off
def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}")
# fmt: on


def main() -> None:
    """Execute the documented scoring workflow."""
    print(f"{WORKFLOW_ID} — Score, Rank, and Assess Overfit Evidence")
    print("INPUT BOUNDARY — supplied Analytics performance evidence")

    # Stage 1 — Receive Analytics-owned candidate and trade evidence.
    _stage(1)
    report, _ = _report()

    # Stage 2 — Calculate the enabled objective score only.
    _stage(2)
    score = calculate_candidate_score(
        report,
        candidate_hash="a" * 64,
        objective=ObjectiveName.NET_PNL,
        enabled_objectives=frozenset({ObjectiveName.NET_PNL}),
    )

    # Stage 3 — Calculate Deflated Sharpe and unique nominal-trial evidence.
    _stage(3)
    trials = count_nominal_trials(("a" * 64, "b" * 64))
    dsr = calculate_deflated_sharpe(
        sharpe=1.0,
        variance=0.2,
        skewness=0.0,
        kurtosis=3.0,
        sample_count=100,
        nominal_trials=trials,
    )

    # Stage 4 — Rank candidates with deterministic tie breaking.
    _stage(4)
    ranked = rank_candidates((score,))

    # Stage 5 — Assess IS/OOS degradation and return caveated overfit evidence.
    _stage(5)
    assessment = assess_overfit_evidence(
        in_sample=ranked[0],
        out_of_sample=ranked[0],
        nominal_trials=trials,
        deflated_sharpe=dsr,
        minimum_trade_count=1,
    )
    print(
        "OUTPUT BOUNDARY — ranked scores, DSR, overfit evidence:",
        ranked[0].value,
        dsr,
        assessment["trade_count_adequate"],
    )


if __name__ == "__main__":
    main()
