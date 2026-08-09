"""Unit evidence for FEAT-RES-16 stress evidence."""

from datetime import UTC, datetime

import pytest
from app.services.research import (
    build_reasoned_stress_shock,
    build_stress_scenario_evidence,
    derive_historical_stress_shock,
    parse_stress_scenario_evidence,
)


def test_historical_and_reasoned_shocks_are_explicit() -> None:
    """FR-RES-115/117: shocks preserve units, rationale, and basis."""
    shocks = (
        derive_historical_stress_shock(
            shock_type="price",
            observations=(100.0, 85.0),
            event_ref="event-2020",
            rationale="Observed close-to-trough move",
        ),
        build_reasoned_stress_shock(
            shock_type="connectivity",
            magnitude=30.0,
            assumption_ref="assumption-network-1",
            rationale="Recovery objective boundary",
        ),
    )
    evidence = build_stress_scenario_evidence(
        scenario_id="scenario-demo",
        hypothesis="combined disruption",
        shocks=shocks,
        generated_at_utc=datetime(2026, 1, 1, tzinfo=UTC),
    )
    assert parse_stress_scenario_evidence(evidence) == evidence
    assert evidence["shocks"][0]["unit"] == "percentage"


def test_invented_stress_basis_is_rejected() -> None:
    """FR-RES-118: missing basis evidence fails closed."""
    with pytest.raises(ValueError, match="RES_STRESS_SCENARIO_INVALID"):
        build_reasoned_stress_shock(
            shock_type="price", magnitude=10.0, assumption_ref="", rationale=""
        )
