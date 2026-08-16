"""Unit tests for the versioned parity envelope and maturity ladder."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from app.services.simulator.errors import SimulationError
from app.services.simulator.parity.contracts import (
    ParityCertificateScope,
    ParityCertificateTarget,
    ParityEnvelopeModel,
    ParityIgnoredField,
    ParityInitialAuthorityState,
    ParityInvariantKind,
    ParityInvariantSpec,
    ParityValidityInterval,
)
from app.services.simulator.parity.envelope import (
    get_parity_envelope,
    get_parity_maturity_ladder,
)
from pydantic import ValidationError


def test_unknown_envelope_version_fails_closed() -> None:
    """FR-SIM-236: an unknown envelope version is rejected, never approximated."""
    with pytest.raises(SimulationError) as raised:
        get_parity_envelope("v9")
    assert raised.value.code == "SIM_INVALID_CONFIG"


def test_envelope_v1_publishes_complete_matrix() -> None:
    """FR-SIM-187/236: the published envelope carries the full certification matrix."""
    envelope = get_parity_envelope("v1")
    assert envelope["envelope_version"] == "v1"
    scope = envelope["certificate_scope"]
    assert scope["certificate_target"] == "demo"
    assert scope["provider"] == "mt5"
    assert scope["asset_class"] == "FX"
    invariants = envelope["invariants"]
    kinds = {invariant["kind"] for invariant in invariants}
    assert kinds == {
        "exact_structural",
        "bounded_numeric",
        "distributional",
    }
    for invariant in invariants:
        assert invariant["metric"]
        assert invariant["unit"]
    assert envelope["ignored_fields"]
    assert envelope["invalidation_triggers"]
    assert Decimal(envelope["aggregate_economic_error_budget"]) == Decimal(0)
    assert "operational_applicability" not in envelope


def test_envelope_v2_certifies_only_shared_mt5_operational_semantics() -> None:
    """FR-SIM-236: v2 separates shared semantics from empirical claims."""
    envelope = get_parity_envelope("v2")
    assert (
        envelope["certificate_scope"]["asset_class"]
        == "MULTI_ASSET_OPERATIONAL_CONTRACT"
    )
    applicability = envelope["operational_applicability"]
    assert applicability["evidence_route"] == "demo"
    assert applicability["provider_routes"] == ["demo", "live"]
    assert "latency_distribution" in applicability["excluded_empirical_claims"]
    invariant_ids = {invariant["invariant_id"] for invariant in envelope["invariants"]}
    assert "order.lifecycle_state" in invariant_ids
    assert "ledger.conservation" in invariant_ids
    assert "latency.submission_to_ack" not in invariant_ids
    assert "slippage.points" not in invariant_ids
    assert "deal.execution_price" not in invariant_ids


def test_maturity_ladder_publishes_one_operational_certificate() -> None:
    """FR-SIM-193: the ladder publishes one bounded MT5 operational L5 rung."""
    ladder = get_parity_maturity_ladder()
    rungs = [rung["rung"] for rung in ladder]
    assert rungs == ["L1", "L2", "L3", "L4", "L5-MT5-Operational"]
    claim = ladder[4]["claim"]
    assert "shared by demo and live" in claim
    assert "empirical market behavior remains route-scoped" in claim


def _minimal_envelope(
    invariants: tuple[ParityInvariantSpec, ...],
) -> ParityEnvelopeModel:
    return ParityEnvelopeModel(
        envelope_version="test",
        certificate_scope=ParityCertificateScope(
            certificate_target=ParityCertificateTarget.DEMO,
            provider="mt5",
            environment="demo",
            server_account_mode="netting_demo_single_account",
            asset_class="FX",
            market_evidence_class="genuine_bid_ask_ticks",
            evidence_sources=("paired_separately_authorized_requests",),
        ),
        invariants=invariants,
        route_gate_policies=(),
        ignored_fields=(
            ParityIgnoredField(path="orders[].retrieved_at", reason="test"),
        ),
        initial_authority_state=ParityInitialAuthorityState(
            state_hash="f" * 64,
            exclusive_account=True,
        ),
        validity=ParityValidityInterval(
            issued_at=datetime(2026, 1, 1, tzinfo=UTC),
            valid_through=datetime(2027, 1, 1, tzinfo=UTC),
        ),
        aggregate_economic_error_budget=Decimal(0),
        account_currency="USD",
        invalidation_triggers=("detected_drift",),
    )


def _structural_invariant(invariant_id: str) -> ParityInvariantSpec:
    return ParityInvariantSpec(
        invariant_id=invariant_id,
        group="test",
        kind=ParityInvariantKind.EXACT_STRUCTURAL,
        metric="sequence",
        unit="sequence",
        tolerance=Decimal(0),
    )


def test_duplicate_invariant_ids_rejected() -> None:
    """FR-SIM-187: duplicate invariant ids fail envelope validation."""
    with pytest.raises(ValidationError):
        _minimal_envelope(
            (
                _structural_invariant("dup"),
                _structural_invariant("dup"),
            )
        )


def test_missing_tolerance_rejected() -> None:
    """FR-SIM-187: exact/numeric invariants must declare a metric tolerance."""
    broken = ParityInvariantSpec(
        invariant_id="broken",
        group="test",
        kind=ParityInvariantKind.BOUNDED_NUMERIC,
        metric="signed_decimal_difference",
        unit="account_currency",
        tolerance=None,
    )
    with pytest.raises(ValidationError):
        _minimal_envelope((_structural_invariant("ok"), broken))


def test_distributional_test_without_flag_rejected() -> None:
    """FR-SIM-187: an uncalibrated tolerance may not be invented silently."""
    invented = ParityInvariantSpec(
        invariant_id="invented",
        group="test",
        kind=ParityInvariantKind.DISTRIBUTIONAL,
        metric="mean_absolute_difference",
        unit="ms",
        tolerance=None,
        statistical_test=None,
    )
    with pytest.raises(ValidationError):
        _minimal_envelope((_structural_invariant("ok"), invented))
