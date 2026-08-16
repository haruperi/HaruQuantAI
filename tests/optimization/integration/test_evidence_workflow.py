"""Integration test for complete Optimization evidence assembly."""

# ruff: noqa: INP001
import asyncio

from app.services.optimization import (
    assess_strategy_robustness,
    build_optimization_evidence,
    build_report_package,
    run_bounded_search,
    run_monte_carlo,
    run_walk_forward_validation,
)
from tests.optimization.unit.test_evidence_contracts import evidence_request
from tests.optimization.unit.test_robustness_contracts import monte_carlo_request
from tests.optimization.unit.test_search_contracts import search_request
from tests.optimization.unit.test_sweep import FakeAdapter
from tests.optimization.unit.test_validation_contracts import walk_forward_request


def test_complete_evidence_workflow_is_ready_only_with_all_baselines() -> None:
    """Search, WFA, MC, and assessment evidence enable risk review."""
    adapter = FakeAdapter()
    monte_carlo = run_monte_carlo(monte_carlo_request(), max_simulations=5)
    request = evidence_request().model_copy(
        update={
            "search": asyncio.run(run_bounded_search(search_request(), adapter)),
            "walk_forward": asyncio.run(
                run_walk_forward_validation(walk_forward_request(), adapter)
            ),
            "monte_carlo": monte_carlo,
            "robustness": assess_strategy_robustness(
                monte_carlo=monte_carlo,
                stress_checks=({"name": "cost", "passed": True},),
            ),
        }
    )
    result = build_optimization_evidence(request)
    assert result.final_decision.value == "ready_for_risk_review"
    assert build_report_package(result)["decision"] == "ready_for_risk_review"
