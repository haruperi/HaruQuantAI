"""Unit evidence for the approved FEAT-RES-16 scenario catalogue."""

from datetime import UTC, datetime

import pytest
from app.services.research import (
    build_registered_stress_scenario,
    get_stress_scenario_catalog,
)
from app.services.research.contracts.errors import ValidationError


def test_approved_stress_catalog_is_exact_and_detached() -> None:
    """Verify approved definitions, references, and detached reads."""
    catalog = get_stress_scenario_catalog()

    assert [item["scenario_key"] for item in catalog] == [
        "broad_market_dislocation",
        "severe_fx_repricing",
        "liquidity_withdrawal",
        "venue_connectivity_disruption",
        "extreme_combined_tail",
    ]
    assert catalog[0]["assumption_ref"] == "HQA-STRESS-ASSUMPTION-001-v1"
    assert catalog[-1]["shocks"][-1] == {
        "shock_type": "margin",
        "magnitude": 100.0,
    }
    catalog[0]["name"] = "changed"
    assert get_stress_scenario_catalog()[0]["name"] == "Broad market dislocation"


def test_registered_scenario_builds_cited_reasoned_evidence() -> None:
    """Verify every shock carries the approved reasoned basis."""
    evidence = build_registered_stress_scenario(
        scenario_key="venue_connectivity_disruption",
        hypothesis="Can operations tolerate a venue disruption?",
        generated_at_utc=datetime(2026, 8, 18, tzinfo=UTC),
    )

    assert evidence["advisory_only"] is True
    assert [shock["magnitude"] for shock in evidence["shocks"]] == [120.0, 300.0, 8.0]
    assert {shock["basis_kind"] for shock in evidence["shocks"]} == {"reasoned"}
    assert {shock["basis_ref"] for shock in evidence["shocks"]} == {
        "HQA-STRESS-ASSUMPTION-004-v1"
    }


def test_unknown_scenario_fails_closed() -> None:
    """Verify callers cannot supply unregistered scenario content."""
    with pytest.raises(ValidationError, match="SCENARIO_NOT_REGISTERED"):
        build_registered_stress_scenario(
            scenario_key="invented",
            hypothesis="invalid",
            generated_at_utc=datetime(2026, 8, 18, tzinfo=UTC),
        )
