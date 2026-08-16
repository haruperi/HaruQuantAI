"""Integration tests for paired semantic parity comparison."""

from typing import Any

from app.services.simulator import (
    compare_parity_evidence,
    get_parity_envelope,
)

from tests.simulator.integration.test_parity_relationships import (
    paired_evidence,
)

_ENVELOPE = get_parity_envelope("v1")


def test_paired_semantic_evidence_passes_envelope() -> None:
    """Standing regression: alpha-equivalent paired evidence passes v1."""
    left, right = paired_evidence()
    result = compare_parity_evidence(left, right, _ENVELOPE)
    assert result["passed"] is True, result["failures"]
    assert result["certificate_invalidated"] is False
    assert result["envelope_version"] == "v1"
    assert result["certificate_target"] == "demo"
    invariant_ids = {invariant["invariant_id"] for invariant in result["invariants"]}
    assert "gate.business_risk_sequence" in invariant_ids
    assert "ledger.conservation" in invariant_ids


def test_demo_evidence_certifies_v2_shared_operational_semantics_only() -> None:
    """Demo traces may pass v2 without creating an empirical live claim."""
    left, right = paired_evidence()
    result = compare_parity_evidence(left, right, get_parity_envelope("v2"))
    assert result["passed"] is True, result["failures"]
    assert result["envelope_version"] == "v2"
    invariant_ids = {invariant["invariant_id"] for invariant in result["invariants"]}
    assert "order.lifecycle_state" in invariant_ids
    assert "latency.submission_to_ack" not in invariant_ids
    assert "slippage.points" not in invariant_ids


def test_route_safety_gates_compared_against_declared_policy() -> None:
    """Route-specific safety gates must match their declared route policy."""
    left, right = paired_evidence()
    tampered: list[Any] = list(right["gates"])  # type: ignore[call-overload]
    tampered[1] = {**tampered[1], "outcome": "some-invented-outcome"}
    right["gates"] = tuple(tampered)  # type: ignore[assignment]
    result = compare_parity_evidence(left, right, _ENVELOPE)
    assert result["passed"] is False
    assert any("gate.route_safety_policy" in f for f in result["failures"])


def test_gate_outcome_drift_fails_business_gate_sequence() -> None:
    """A different business gate outcome breaks the paired gate sequence."""
    left, right = paired_evidence()
    gates: list[Any] = list(left["gates"])  # type: ignore[call-overload]
    gates[0] = {**gates[0], "outcome": "rejected"}
    left["gates"] = tuple(gates)  # type: ignore[assignment]
    result = compare_parity_evidence(left, right, _ENVELOPE)
    assert result["passed"] is False
    assert any("gate.business_risk_sequence" in f for f in result["failures"])
