"""Optimization provider evidence for FEAT-RES-16."""

from datetime import UTC, datetime
from typing import Any, cast

from app.services.optimization import resolve_stress_profile_calibration
from app.services.research import (
    build_reasoned_stress_shock,
    build_stress_calibration_provider,
    build_stress_scenario_evidence,
)


def test_optimization_consumes_research_stress_provider() -> None:
    """FR-RES-120: Optimization receives cited Research stress evidence."""
    evidence = build_stress_scenario_evidence(
        scenario_id="scenario-demo",
        hypothesis="network interruption",
        shocks=(
            build_reasoned_stress_shock(
                shock_type="connectivity",
                magnitude=30.0,
                assumption_ref="assumption-network-1",
                rationale="Recovery objective boundary",
            ),
        ),
        generated_at_utc=datetime(2026, 1, 1, tzinfo=UTC),
    )
    provider = build_stress_calibration_provider(evidence)
    result = resolve_stress_profile_calibration(
        strategy_ref="strategy-demo",
        market_data_ref="dataset-demo",
        provider=cast("Any", provider),
    )
    assert result["status"] == "STRESS_PROFILE_CALIBRATED"
    assert result["canonical_hash"] == evidence["canonical_hash"]
