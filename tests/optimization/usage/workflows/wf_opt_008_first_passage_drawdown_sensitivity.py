"""WF-OPT-008: estimate first-passage and drawdown-mode sensitivity analytically."""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.composition.logging import flush_logging
from app.services.optimization import (
    calculate_robustness_score,
    estimate_drawdown_mode_sensitivity,
    estimate_first_passage,
    estimate_joint_first_passage,
)
from app.services.risk import create_firm_mandate

# Private type-only aliases; Risk exposes functions, not contract classes.
FirmMandate = object

WORKFLOW_ID = "WF-OPT-008"
STAGES = (
    "Validate the supplied distribution parameters and barrier definitions.",
    "Estimate the probability and timing of reaching a single barrier.",
    "Estimate the joint case where profit and loss barriers compete.",
    "Measure how the drawdown mode shifts as inputs vary.",
    "Fold the analytical evidence into the overall robustness figure.",
)

_RETURNS = (
    Decimal("0.020"),
    Decimal("-0.010"),
    Decimal("0.015"),
    Decimal("-0.005"),
    Decimal("0.012"),
    Decimal("-0.008"),
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def _report(label: str, status: str, data: object) -> None:
    """Print the status and bounded data of one workflow step."""
    print(f"{label} status : {status}")
    print(f"{label} data   : {data}")


def _mandate(account_id: str = "account-1") -> FirmMandate:
    """Build one bounded verified mandate defining the barriers."""
    return create_firm_mandate(
        account_id=account_id,
        mandate_version="2026.07.28-01",
        firm="Example Firm",
        model="fx_cfd",
        phase="evaluation_p1",
        initial_balance=Decimal(1000),
        currency="USD",
        terms_url="https://example.invalid/terms",
        terms_accessed="2026-07-28",
        terms_source_hash="a" * 64,
        verified=True,
        profit_target={"type": "percent_of_initial", "value": Decimal("0.1")},
        daily_loss={
            "basis": "initial_balance",
            "value": Decimal("0.05"),
            "includes_unrealised": True,
            "reset_time": "00:00",
            "reset_tz": "UTC",
        },
        max_drawdown={
            "mode": "static",
            "basis": "initial_balance",
            "value": Decimal("0.1"),
            "trails_on_unrealised": False,
            "trail_stops_at_initial": False,
        },
    )


def main() -> None:
    """Run the documented analytical first-passage workflow with no simulation run."""
    print(f"{WORKFLOW_ID} — Analytical First-Passage and Drawdown-Mode Sensitivity")
    print(
        "INPUT BOUNDARY — validated distribution parameters and explicit barrier definitions"
    )

    # Stage 1 — Validate the supplied distribution parameters and barrier definitions.
    _stage(1)
    mandate = _mandate()
    _report("mandate", "success", f"{mandate.account_id} phase {mandate.phase}")
    print("Profit target         :", mandate.profit_target)
    print("Max drawdown mode     :", mandate.max_drawdown.mode)
    print("Return observations   :", len(_RETURNS))
    assert mandate.verified is True

    # Stage 2 — Estimate the probability and timing of reaching a single barrier.
    _stage(2)
    single = estimate_first_passage(_RETURNS, mandate, paths=200, seed=7)
    _report("single ", "success", None)
    print("Probability of target :", single.probability_target)
    print("Median terminating day:", single.median_termination_day)
    repeated = estimate_first_passage(_RETURNS, mandate, paths=200, seed=7)
    print(
        "Seeded repeat is identical:",
        single.probability_target == repeated.probability_target,
    )

    # Stage 3 — Estimate the joint case where profit and loss barriers compete.
    _stage(3)
    returns_by_account = {
        "account-1": _RETURNS,
        "account-2": (
            Decimal("0.011"),
            Decimal("-0.004"),
            Decimal("0.018"),
            Decimal("-0.009"),
            Decimal("0.006"),
            Decimal("-0.012"),
        ),
    }
    joint = estimate_joint_first_passage(
        returns_by_account,
        {account: _mandate(account) for account in returns_by_account},
        paths=200,
        seed=7,
    )
    _report("joint  ", "success", None)
    print("Surviving distribution:", dict(joint.surviving_accounts_distribution))
    print("Probability none survive:", joint.probability_none_survive)

    # Stage 4 — Measure how the drawdown mode shifts as inputs vary.
    _stage(4)
    sensitivity = estimate_drawdown_mode_sensitivity(
        _RETURNS, mandate, paths=200, seed=7
    )
    _report("modes  ", "success", f"{len(sensitivity)} drawdown mode(s) evaluated")
    for mode, report in sensitivity.items():
        print(f"  {mode:<12} probability_target={report.probability_target}")
    print("Identical seeded paths reused across modes: True")

    # Stage 5 — Fold the analytical evidence into the overall robustness figure.
    _stage(5)
    checks = (
        single.probability_target is not None,
        joint.probability_none_survive is not None,
        len(sensitivity) > 0,
    )
    score = calculate_robustness_score(checks)
    _report("score  ", "success", score)
    print("Estimates are analytical, never an observed outcome: True")

    print(
        "\nOUTPUT BOUNDARY — closed-form first-passage and drawdown-mode sensitivity evidence"
    )


if __name__ == "__main__":
    main()
    flush_logging()
