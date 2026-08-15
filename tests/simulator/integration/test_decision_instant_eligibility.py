"""Integration evidence for decision-instant and clock-edge eligibility."""

from datetime import timedelta

from app.services.simulator import (
    calculate_simulation_backtest_v2_config_hash,
    validate_market_evidence_lineage,
)

from tests.simulator.unit.test_market_evidence_lineage import (
    NOW,
    _validate,
    source_dataset,
    tick_dataset,
)


def test_fr_sim_209_future_available_evidence_is_rejected() -> None:
    """FR-SIM-209: event time never substitutes for future availability."""
    result = _validate(
        source_dataset(),
        tick_dataset(available_at=NOW + timedelta(minutes=3)),
    )
    assert result.status == "error"
    assert result.error.code == "SIM_LOOKAHEAD_DETECTED"


def test_missing_required_clock_edge_excludes_latency_eligibility() -> None:
    """Missing clock evidence narrows eligibility without inventing a timestamp."""
    result = validate_market_evidence_lineage(
        source_dataset(),
        tick_dataset(),
        decision_instant=NOW + timedelta(minutes=2),
        runtime_profile="simulation",
        path_sensitive=True,
        required_clock_edges=("acknowledgement", "availability", "decision"),
        clock_edges={
            "acknowledgement": None,
            "availability": NOW + timedelta(minutes=1),
            "decision": NOW + timedelta(minutes=2),
        },
    )
    evidence = result.data
    assert evidence.parity_eligible is False
    assert evidence.missing_clock_edges == ("acknowledgement",)


def test_complete_genuine_tick_evidence_is_parity_eligible() -> None:
    """Complete genuine bid/ask and clock evidence passes the lineage gate."""
    evidence = _validate(source_dataset(), tick_dataset()).data
    assert evidence.parity_eligible is True
    assert evidence.missing_clock_edges == ()


def test_request_v2_hash_binds_eligibility_and_clock_coverage() -> None:
    """FR-SIM-209: eligibility and evidenced edges change request identity."""
    base = {
        "source_lineage_hash": "a" * 64,
        "tick_lineage_hash": "b" * 64,
        "market_evidence_class": "genuine_bid_ask_ticks",
        "market_evidence_eligible": False,
        "required_clock_edges": ("availability", "decision"),
        "evidenced_clock_edges": ("availability",),
    }
    incomplete = calculate_simulation_backtest_v2_config_hash(base).data
    complete = calculate_simulation_backtest_v2_config_hash(
        {
            **base,
            "market_evidence_eligible": True,
            "evidenced_clock_edges": ("availability", "decision"),
        }
    ).data
    assert incomplete != complete
