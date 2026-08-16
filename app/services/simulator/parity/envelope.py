"""Versioned Parity Envelope registry and maturity-ladder publication.

The envelope is the falsifiable certification matrix: provider, environment,
server/account mode, symbol specification revisions, order operations,
execution model, market-evidence class, initial authority state, and evidence
sources (plan §0.1). Anything outside the matrix fails canonical eligibility;
it is never silently approximated. Envelope v1 preserves the original MT5-FX
demo scope, including empirical invariants. Envelope v2 admits only shared MT5
operational semantics evidenced on demo and explicitly excludes empirical
transfer to live.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from decimal import Decimal

from app.services.simulator.errors import SimulationError
from app.services.simulator.parity.contracts import (
    ParityCertificateScope,
    ParityCertificateTarget,
    ParityEnvelopeModel,
    ParityIgnoredField,
    ParityInitialAuthorityState,
    ParityInvariantKind,
    ParityInvariantSpec,
    ParityOperationalApplicability,
    ParityRouteGatePolicy,
    ParityValidityInterval,
)
from app.utils import get_logger

logger = get_logger(__name__)

_ENVELOPE_V1 = ParityEnvelopeModel(
    envelope_version="v1",
    certificate_scope=ParityCertificateScope(
        certificate_target=ParityCertificateTarget.DEMO,
        provider="mt5",
        environment="demo",
        server_account_mode="netting_demo_single_account",
        asset_class="FX",
        market_evidence_class="genuine_bid_ask_ticks",
        evidence_sources=(
            "paired_separately_authorized_requests",
            "captured_authority_traces",
        ),
    ),
    invariants=(
        ParityInvariantSpec(
            invariant_id="gate.business_risk_sequence",
            group="gates",
            kind=ParityInvariantKind.EXACT_STRUCTURAL,
            metric="role_order_inputs_outcome",
            unit="sequence",
            tolerance=Decimal(0),
        ),
        ParityInvariantSpec(
            invariant_id="gate.route_safety_policy",
            group="gates",
            kind=ParityInvariantKind.EXACT_STRUCTURAL,
            metric="declared_route_policy_outcome",
            unit="sequence",
            tolerance=Decimal(0),
        ),
        ParityInvariantSpec(
            invariant_id="order.lifecycle_state",
            group="orders",
            kind=ParityInvariantKind.EXACT_STRUCTURAL,
            metric="state_sequence",
            unit="sequence",
            tolerance=Decimal(0),
        ),
        ParityInvariantSpec(
            invariant_id="order.linkage_graph",
            group="orders",
            kind=ParityInvariantKind.EXACT_STRUCTURAL,
            metric="order_deal_position_foreign_keys",
            unit="graph",
            tolerance=Decimal(0),
        ),
        ParityInvariantSpec(
            invariant_id="receipt.status_classification",
            group="receipts",
            kind=ParityInvariantKind.EXACT_STRUCTURAL,
            metric="status_and_response_classification",
            unit="sequence",
            tolerance=Decimal(0),
        ),
        ParityInvariantSpec(
            invariant_id="event.category_sequence",
            group="events",
            kind=ParityInvariantKind.EXACT_STRUCTURAL,
            metric="event_type_sequence",
            unit="sequence",
            tolerance=Decimal(0),
        ),
        ParityInvariantSpec(
            invariant_id="causal.evidenced_partial_order",
            group="events",
            kind=ParityInvariantKind.EXACT_STRUCTURAL,
            metric="causal_edges_and_ambiguous_groups",
            unit="graph",
            tolerance=Decimal(0),
        ),
        ParityInvariantSpec(
            invariant_id="account.final_balance",
            group="accounting",
            kind=ParityInvariantKind.BOUNDED_NUMERIC,
            metric="signed_decimal_difference",
            unit="account_currency",
            tolerance=Decimal(0),
        ),
        ParityInvariantSpec(
            invariant_id="account.final_equity",
            group="accounting",
            kind=ParityInvariantKind.BOUNDED_NUMERIC,
            metric="signed_decimal_difference",
            unit="account_currency",
            tolerance=Decimal(0),
        ),
        ParityInvariantSpec(
            invariant_id="order.fill_quantity",
            group="orders",
            kind=ParityInvariantKind.BOUNDED_NUMERIC,
            metric="signed_decimal_difference",
            unit="lots",
            tolerance=Decimal(0),
        ),
        ParityInvariantSpec(
            invariant_id="deal.execution_price",
            group="orders",
            kind=ParityInvariantKind.BOUNDED_NUMERIC,
            metric="signed_decimal_difference",
            unit="quote_currency",
            tolerance=Decimal(0),
        ),
        ParityInvariantSpec(
            invariant_id="ledger.conservation",
            group="accounting",
            kind=ParityInvariantKind.EXACT_STRUCTURAL,
            metric="signed_posting_equation_residual",
            unit="account_currency",
            tolerance=Decimal(0),
        ),
        ParityInvariantSpec(
            invariant_id="latency.submission_to_ack",
            group="realism",
            kind=ParityInvariantKind.DISTRIBUTIONAL,
            metric="mean_absolute_difference",
            unit="ms",
            tolerance=None,
            statistical_test="two_sample_mean_within_tolerance",
            minimum_coverage=30,
            aggregation="mean",
            awaiting_calibration_evidence=True,
        ),
        ParityInvariantSpec(
            invariant_id="slippage.points",
            group="realism",
            kind=ParityInvariantKind.DISTRIBUTIONAL,
            metric="mean_absolute_difference",
            unit="points",
            tolerance=None,
            statistical_test="two_sample_mean_within_tolerance",
            minimum_coverage=30,
            aggregation="mean",
            awaiting_calibration_evidence=True,
        ),
    ),
    route_gate_policies=(
        ParityRouteGatePolicy(
            gate_id="live_mutation_authorization",
            route="live",
            policy="require_allow_live_mutations_true",
        ),
        ParityRouteGatePolicy(
            gate_id="pre_mutation_audit",
            route="live",
            policy="audit_failed_stops_dispatch",
        ),
        ParityRouteGatePolicy(
            gate_id="adapter_capability_validation",
            route="demo",
            policy="validate_adapter_capability_exact_match",
        ),
    ),
    ignored_fields=(
        ParityIgnoredField(
            path="orders[].provider_timestamp",
            reason="provider observation clock; no economic or transition meaning",
        ),
        ParityIgnoredField(
            path="orders[].retrieved_at",
            reason="read-side retrieval observation time; not economic time",
        ),
        ParityIgnoredField(
            path="orders[].receive_time",
            reason="network transport receive time; excluded transport evidence",
        ),
        ParityIgnoredField(
            path="deals[].provider_timestamp",
            reason="provider observation clock; no economic or transition meaning",
        ),
    ),
    initial_authority_state=ParityInitialAuthorityState(
        state_hash="f" * 64,
        exclusive_account=True,
        foreign_activity_event_count=0,
    ),
    validity=ParityValidityInterval(
        issued_at=datetime(2026, 8, 14, tzinfo=UTC),
        valid_through=datetime(2027, 8, 14, tzinfo=UTC),
    ),
    aggregate_economic_error_budget=Decimal(0),
    account_currency="USD",
    invalidation_triggers=(
        "build_identity_change",
        "contract_change",
        "code_or_config_identity_change",
        "specification_revision_change",
        "source_or_tick_model_change",
        "calibration_validity_change",
        "detected_drift",
        "initial_authority_state_change",
    ),
)

_OPERATIONAL_INVARIANT_IDS = frozenset(
    {
        "gate.business_risk_sequence",
        "gate.route_safety_policy",
        "order.lifecycle_state",
        "order.linkage_graph",
        "receipt.status_classification",
        "event.category_sequence",
        "causal.evidenced_partial_order",
        "ledger.conservation",
    }
)

_ENVELOPE_V2 = _ENVELOPE_V1.model_copy(
    update={
        "envelope_version": "v2",
        "certificate_scope": _ENVELOPE_V1.certificate_scope.model_copy(
            update={
                "market_evidence_class": "operational_contract_trace",
                "evidence_sources": (
                    "verified_mt5_demo_operational_trace",
                    "paired_simulation_operational_trace",
                ),
            }
        ),
        "invariants": tuple(
            invariant
            for invariant in _ENVELOPE_V1.invariants
            if invariant.invariant_id in _OPERATIONAL_INVARIANT_IDS
        ),
        "operational_applicability": ParityOperationalApplicability(
            evidence_route="demo",
            provider_routes=("demo", "live"),
            certified_semantics=(
                "order_request_and_response_contracts",
                "order_lifecycle_and_relationships",
                "event_categories_and_causality",
                "risk_and_route_gate_semantics",
                "ledger_conservation_and_accounting_rules",
                "persistence_identity_and_route_tagging",
            ),
            excluded_empirical_claims=(
                "spread_distribution",
                "latency_distribution",
                "fill_distribution",
                "liquidity_distribution",
                "slippage_distribution",
                "execution_price_distribution",
                "calibration_transfer",
                "profitability_or_performance",
            ),
        ),
    }
)

_ENVELOPES: Mapping[str, ParityEnvelopeModel] = {
    "v1": _ENVELOPE_V1,
    "v2": _ENVELOPE_V2,
}

_MATURITY_LADDER: tuple[dict[str, object], ...] = (
    {
        "rung": "L1",
        "name": "mutation_path_convergence",
        "delivered_by": "phase_14",
        "claim": (
            "Equivalent business/risk gates and the same authority boundary are"
            " traversed; route-specific safety gates remain explicit"
        ),
    },
    {
        "rung": "L2",
        "name": "evaluation_path_convergence",
        "delivered_by": "phase_15",
        "claim": (
            "Indicators, Strategy, and Risk evaluate incrementally against"
            " evolving point-in-time state using the same Trading cycle"
        ),
    },
    {
        "rung": "L3",
        "name": "account_order_semantics",
        "delivered_by": "phases_16_18",
        "claim": (
            "Verified account, margin, order, deal, protection, and position"
            " behavior matches within the admitted matrix"
        ),
    },
    {
        "rung": "L4",
        "name": "execution_realism",
        "delivered_by": "phases_19_20",
        "claim": (
            "Every stochastic component is calibrated from eligible evidence or"
            " excluded from canonical execution"
        ),
    },
    {
        "rung": "L5-MT5-Operational",
        "name": "shared_mt5_operational_semantics",
        "delivered_by": "verified_demo_operational_evidence",
        "claim": (
            "Verified demo evidence certifies only the MT5 operational"
            " semantics shared by demo and live credential routes; empirical"
            " market behavior remains route-scoped"
        ),
    },
)


def _envelope_mapping(envelope: ParityEnvelopeModel) -> dict[str, object]:
    """Return the JSON-safe public mapping of one envelope.

    Args:
        envelope: Parsed envelope model.

    Returns:
        Immutable-shaped public mapping (the caller wraps it read-only).
    """
    mapping = envelope.model_dump(mode="json")
    if envelope.operational_applicability is None:
        mapping.pop("operational_applicability", None)
    return mapping


def get_parity_envelope(version: str = "v1") -> Mapping[str, object]:
    """Return the published Parity Envelope for one version.

    Args:
        version: Published envelope version identifier.

    Returns:
        Read-only envelope mapping containing certificate scope, invariants,
        route gate policies, ignored-field registry, initial authority state,
        validity interval, aggregate economic-error budget, and invalidation
        triggers.

    Raises:
        SimulationError: If the version is unknown (fail closed; unknown
            versions are never approximated by the nearest known one).
    """
    envelope = _ENVELOPES.get(version)
    if envelope is None:
        logger.warning("Rejecting unknown parity envelope version %s", version)
        raise SimulationError(
            "SIM_INVALID_CONFIG",
            f"unknown parity envelope version: {version}",
            details={"known_versions": sorted(_ENVELOPES)},
        )
    return _envelope_mapping(envelope)


def load_parity_envelope(version: str = "v1") -> ParityEnvelopeModel:
    """Return the parsed internal envelope model for one version.

    Args:
        version: Envelope version identifier.

    Returns:
        Parsed immutable envelope model.

    Raises:
        SimulationError: If the version is unknown.
    """
    envelope = _ENVELOPES.get(version)
    if envelope is None:
        raise SimulationError(
            "SIM_INVALID_CONFIG",
            f"unknown parity envelope version: {version}",
            details={"known_versions": sorted(_ENVELOPES)},
        )
    return envelope


def get_parity_maturity_ladder() -> tuple[Mapping[str, object], ...]:
    """Return the published L1 through L5 MT5-operational maturity ladder.

    Returns:
        Tuple of read-only rung mappings. No implementation phase may claim
        parity; only a completed L5 certificate recorded in an immutable
        envelope may make the bounded claim.
    """
    return _MATURITY_LADDER


__all__ = [
    "get_parity_envelope",
    "get_parity_maturity_ladder",
    "load_parity_envelope",
]
