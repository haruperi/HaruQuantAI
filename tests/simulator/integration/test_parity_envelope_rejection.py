"""Integration tests for envelope rejection and certificate invalidation."""

import pytest
from app.services.simulator import (
    compare_parity_evidence,
    get_parity_envelope,
)
from app.services.simulator.errors import SimulationError

from tests.simulator.integration.test_parity_relationships import (
    paired_evidence,
)

_ENVELOPE = get_parity_envelope("v1")


def test_unregistered_ignored_field_is_rejected() -> None:
    """Standing regression: a field outside the registry is rejected."""
    left, _right = paired_evidence()
    tainted = {**left, "transport_padding_field": "ignored-by-no-one"}
    with pytest.raises(SimulationError) as raised:
        compare_parity_evidence(tainted, left, _ENVELOPE)
    assert raised.value.code == "SIM_INVALID_CONFIG"


def test_demo_evidence_cannot_claim_live_scope() -> None:
    """Standing regression: demo evidence never claims the live envelope."""
    left, right = paired_evidence()
    relabelled = {**left, "certificate_target": "live"}
    with pytest.raises(SimulationError) as raised:
        compare_parity_evidence(relabelled, right, _ENVELOPE)
    assert raised.value.code == "SIM_INVALID_CONFIG"
    assert "live" in raised.value.message


def test_certificate_invalidates_when_bound_identity_changes() -> None:
    """Standing regression: execution-identity change invalidates the certificate."""
    left, right = paired_evidence()
    mutated = {
        **left,
        "identity": {
            **left["identity"],  # type: ignore[index]
            "execution_model_hash": "d" * 64,
        },
    }
    result = compare_parity_evidence(mutated, right, _ENVELOPE)
    assert result["passed"] is False
    assert result["certificate_invalidated"] is True
    assert any("certificate.execution_identity" in f for f in result["failures"])


def test_unknown_envelope_version_rejected_at_comparison() -> None:
    """A comparison under an unknown envelope version fails closed."""
    left, _right = paired_evidence()
    with pytest.raises(SimulationError):
        compare_parity_evidence(left, left, {"envelope_version": "v9"})
