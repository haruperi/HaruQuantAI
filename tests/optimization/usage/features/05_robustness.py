"""Executable Optimization robustness usage example.

Demonstrates FEAT-OPT-05 Monte Carlo simulations, execution stress testing, confidence interval calculation, probability of ruin, strategy robustness assessment, and first-passage drawdown sensitivity.
"""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.optimization import (
    apply_execution_cost_stress,
    assess_strategy_robustness,
    calculate_confidence_intervals,
    calculate_probability_of_ruin,
    create_optimization_value,
    estimate_drawdown_mode_sensitivity,
    estimate_first_passage,
    estimate_joint_first_passage,
    run_monte_carlo,
    run_parametric_simulation,
)
from app.services.risk import create_firm_mandate
from tests.optimization.usage._support import monte_carlo_request

RETURNS = (Decimal("0.02"), Decimal("-0.01"), Decimal("0.015"), Decimal("-0.005"))


def _mandate(account_id: str = "account-1") -> object:
    """Build a bounded verified mandate through Risk's public API."""
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


def fr_opt_035() -> None:
    """FR-OPT-035: Stage 1 — Monte Carlo Request Modeling.

    The system shall model bounded Monte Carlo inputs with method, simulations, seed, block size, and ruin thresholds.
    """
    _header("Stage 1: Monte Carlo Request - Model Monte Carlo Request (FR-OPT-035)")
    req = monte_carlo_request()
    print(_format_result(req))
    print(f"Data -> method='{req.method}'")


def fr_opt_039() -> None:
    """FR-OPT-039: Stage 2 — Monte Carlo Simulation Execution.

    The system shall run selected Monte Carlo methods with deterministic sub-seeds within approved caps.
    """
    _header("Stage 2: Monte Carlo Simulation - Run Monte Carlo (FR-OPT-039)")
    req = monte_carlo_request()
    mc_res = run_monte_carlo(req, max_simulations=5)
    print(_format_result(mc_res))
    print(f"Data -> simulations={mc_res.simulations}, method='{mc_res.method}'")


def fr_opt_040() -> None:
    """FR-OPT-040: Stage 2 — Probability of Ruin Calculation.

    The system shall calculate the fraction of drawdowns or equity paths crossing an explicit ruin threshold.
    """
    _header("Stage 2: Ruin Probability - Calculate Probability of Ruin (FR-OPT-040)")
    p_ruin = calculate_probability_of_ruin(
        (Decimal(1), Decimal(2)), ruin_threshold=Decimal(1)
    )
    print(_format_result(p_ruin))
    print(f"Data -> probability_of_ruin={p_ruin}")


def fr_opt_041() -> None:
    """FR-OPT-041: Stage 2 — Confidence Interval Calculation.

    The system shall calculate empirical confidence intervals for metric samples at a caller-supplied confidence level.
    """
    _header(
        "Stage 2: Confidence Intervals - Calculate Confidence Intervals (FR-OPT-041)"
    )
    lower, upper = calculate_confidence_intervals(
        (Decimal(1), Decimal(2)), confidence_level=0.5
    )
    print(_format_result((lower, upper)))
    print(f"Data -> confidence_interval_50=[{lower}, {upper}]")


def fr_opt_042() -> None:
    """FR-OPT-042: Stage 2 — Parametric Simulation Execution.

    The system shall simulate compounding outcomes from win rate, reward/risk, and risk per trade.
    """
    _header("Stage 2: Parametric Simulation - Run Parametric Simulation (FR-OPT-042)")
    param_res = run_parametric_simulation(
        win_rate=Decimal("0.5"),
        reward_risk=Decimal(1),
        risk_per_trade=Decimal("0.01"),
        trade_count=2,
        simulations=2,
        initial_balance=Decimal(100),
        seed=3,
        max_simulations=2,
    )
    print(_format_result(param_res))
    print(f"Data -> final_equity_points_count={len(param_res.final_equity)}")


def fr_opt_043() -> None:
    """FR-OPT-043: Stage 3 — Execution Cost Stress Testing.

    The system shall apply explicit spread, slippage, or commission stress without mutating inputs.
    """
    _header("Stage 3: Stress Testing - Apply Execution Cost Stress (FR-OPT-043)")
    stress_req = create_optimization_value(
        "ExecutionStressRequest", kind="spread", value=Decimal("0.5")
    )
    stressed_outcomes = apply_execution_cost_stress(({"pnl": Decimal(2)},), stress_req)
    print(_format_result(stressed_outcomes))
    print(f"Data -> stressed_pnl={stressed_outcomes[0]['pnl']}")


def fr_opt_044() -> None:
    """FR-OPT-044: Stage 3 — Strategy Robustness Assessment.

    The system shall combine applicable MC and stress checks into a robustness percentage and summary.
    """
    _header("Stage 3: Robustness Assessment - Assess Strategy Robustness (FR-OPT-044)")
    assessment = assess_strategy_robustness(
        monte_carlo=None,
        stress_checks=({"name": "spread", "passed": True},),
    )
    print(_format_result(assessment))
    print(
        f"Data -> applicable_check_count={assessment.get('applicable_check_count') if isinstance(assessment, dict) else None}"
    )


def fr_opt_066() -> None:
    """FR-OPT-066: Stage 3 — Estimate First-Passage Probabilities under Risk Mandate.

    The system shall estimate first-passage outcome probabilities for a candidate under a supplied Risk mandate.
    """
    _header(
        "Stage 3: First Passage - Estimate First Passage Probabilities (FR-OPT-066)"
    )
    first_passage = estimate_first_passage(RETURNS, _mandate(), paths=100, seed=7)
    print(_format_result(first_passage))
    print(
        f"Data -> target_probability={getattr(first_passage, 'probability_target', None)}"
    )


def fr_opt_067() -> None:
    """FR-OPT-067: Stage 3 — Joint Account Survival Simulation.

    The system shall simulate several accounts jointly at their measured cross-account correlation.
    """
    _header("Stage 3: Joint Survival - Estimate Joint First Passage (FR-OPT-067)")
    joint = estimate_joint_first_passage(
        {
            "account-1": RETURNS,
            "account-2": (
                Decimal("0.011"),
                Decimal("-0.004"),
                Decimal("0.018"),
                Decimal("-0.009"),
            ),
        },
        {"account-1": _mandate(), "account-2": _mandate("account-2")},
        paths=100,
        seed=7,
    )
    print(_format_result(joint))
    print(
        f"Data -> none_survive_probability={getattr(joint, 'probability_none_survive', None)}"
    )


def fr_opt_068() -> None:
    """FR-OPT-068: Stage 3 — Drawdown Mode Sensitivity Evaluation.

    The system shall report the sensitivity of first-passage probabilities to static and trailing drawdown modes.
    """
    _header(
        "Stage 3: Drawdown Sensitivity - Estimate Drawdown Mode Sensitivity (FR-OPT-068)"
    )
    sensitivity = estimate_drawdown_mode_sensitivity(
        RETURNS, _mandate(), paths=100, seed=7
    )
    print(_format_result(sensitivity))
    print(f"Data -> evaluated_drawdown_modes={tuple(sensitivity)}")


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-OPT-05 — robustness/ — Monte Carlo and Stress Analysis\n\n"
        "Purpose: Perform trade-sequence and return-resampling Monte Carlo simulations, execution cost stress testing, confidence interval estimation, and prop-firm first-passage barrier sensitivity.\n\n"
        "Module flow:\n"
        "-> Stage 1: Monte Carlo request input mapping\n"
        "-> Stage 2: Resampling, parametric equity path simulation, and ruin probability calculation\n"
        "-> Stage 3: Cost stress application, robustness summary generation, and joint first-passage barrier analysis"
    )

    # Stage 1: Request Mapping
    fr_opt_035()

    # Stage 2: Simulation & Calculations
    fr_opt_039()
    fr_opt_040()
    fr_opt_041()
    fr_opt_042()

    # Stage 3: Stress, Assessment & First Passage
    fr_opt_043()
    fr_opt_044()
    fr_opt_066()
    fr_opt_067()
    fr_opt_068()


if __name__ == "__main__":
    main()
