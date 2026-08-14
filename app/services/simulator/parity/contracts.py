"""Private frozen contracts for the parity envelope, evidence, and comparator.

The parity feature is the sole owner of the versioned Parity Envelope, the
evidence normalizer registry, and the relationship-preserving comparator
(`FEAT-SIM-18`). Every model in this module is internal: the package root
exposes only standalone functions, per the function-only public API rule.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator


class ParityInvariantKind(StrEnum):
    """Classification of one parity invariant comparison strategy."""

    EXACT_STRUCTURAL = "exact_structural"
    BOUNDED_NUMERIC = "bounded_numeric"
    DISTRIBUTIONAL = "distributional"


class ParityCertificateTarget(StrEnum):
    """Explicitly distinct certificate scopes; demo never implies live."""

    DEMO = "demo"
    LIVE = "live"


#: Posting kinds admitted by the signed ledger-conservation equation.
POSTING_KINDS: tuple[str, ...] = (
    "realized_profit",
    "commission",
    "fees",
    "swap",
    "tax",
    "rebates",
    "deposits",
    "withdrawals",
    "credits",
    "corrections",
)


def _validate_aware_utc(value: datetime) -> datetime:
    """Return ``value`` when it is timezone-aware UTC, else fail closed.

    Args:
        value: Candidate timestamp.

    Returns:
        The unchanged aware-UTC timestamp.

    Raises:
        ValueError: If the timestamp is naive or not UTC-offset.
    """
    if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(None):
        raise ValueError("timestamp must be timezone-aware UTC")
    return value


def _reject_float_decimal(value: object) -> object:
    """Reject binary floats before Decimal parsing for money-like fields.

    Args:
        value: Candidate numeric value.

    Returns:
        The unchanged value when it is not a float.

    Raises:
        TypeError: If the value is a binary float.
    """
    if isinstance(value, float):
        raise TypeError("float values are forbidden; pass Decimal or str")
    return value


class _FrozenModel(BaseModel):
    """Base configuration shared by every parity contract model."""

    model_config = ConfigDict(frozen=True, extra="forbid")


class ParityIgnoredField(_FrozenModel):
    """One explicitly registered non-economic field exclusion.

    A field may be excluded from comparison only when the envelope version
    registers it here together with the proof that it carries no economic or
    state-transition meaning (plan decision: a new ignored field requires an
    envelope-version change and a covering test).
    """

    path: str
    reason: str


class ParityInvariantSpec(_FrozenModel):
    """One typed invariant with its metric, unit, tolerance, and coverage rule.

    ``tolerance`` is ``None`` only for ``distributional`` invariants whose
    calibration evidence has not been published yet; such invariants can never
    pass a comparison (fail-closed, never an invented threshold).
    """

    invariant_id: str
    group: str
    kind: ParityInvariantKind
    metric: str
    unit: str
    tolerance: Decimal | None
    aggregation: Literal["exact", "sum", "mean", "max"] = "exact"
    minimum_coverage: int = Field(default=1, ge=1)
    statistical_test: str | None = None
    awaiting_calibration_evidence: bool = False

    @field_validator("tolerance", mode="before")
    @classmethod
    def _no_float_tolerance(cls, value: object) -> object:
        return _reject_float_decimal(value)


class ParityRouteGatePolicy(_FrozenModel):
    """One route-specific safety gate compared against its own route policy.

    Route-specific safety gates are declared separately and never forced to
    share an identifier with business/risk gates (plan §Phase 2 comparison
    rules).
    """

    gate_id: str
    route: Literal["sim", "paper", "live"]
    policy: str


class ParityCertificateScope(_FrozenModel):
    """The falsifiable certification matrix bound to one envelope version."""

    certificate_target: ParityCertificateTarget
    provider: str
    environment: str
    server_account_mode: str
    asset_class: str
    market_evidence_class: str
    evidence_sources: tuple[str, ...]


class ParityValidityInterval(_FrozenModel):
    """Certificate lease window; expiry invalidates every bound claim."""

    issued_at: datetime
    valid_through: datetime

    @field_validator("issued_at", "valid_through")
    @classmethod
    def _aware_utc(cls, value: datetime) -> datetime:
        return _validate_aware_utc(value)

    def covers(self, evaluation_time: datetime) -> bool:
        """Return True when ``evaluation_time`` lies inside the interval."""
        return self.issued_at <= evaluation_time <= self.valid_through


class ParityInitialAuthorityState(_FrozenModel):
    """Complete initial authority state identity required for certification.

    The hash binds balance, equity, margin, free margin, positions, pending
    orders, protections, ownership, the last reconciled transaction/deal
    watermark, accrued costs, and the provider revision set. Certification
    requires an exclusive account interval or complete ordered foreign/manual
    activity evidence.
    """

    state_hash: str = Field(min_length=64, max_length=64)
    exclusive_account: bool
    foreign_activity_event_count: int = Field(default=0, ge=0)

    @property
    def activity_evidence_complete(self) -> bool:
        """Return True when exclusivity or complete replay evidence exists."""
        return self.exclusive_account or self.foreign_activity_event_count > 0


class ParityEnvelopeModel(_FrozenModel):
    """The immutable versioned Parity Envelope (v1 seeds MT5-FX demo scope)."""

    envelope_version: str
    certificate_scope: ParityCertificateScope
    invariants: tuple[ParityInvariantSpec, ...]
    route_gate_policies: tuple[ParityRouteGatePolicy, ...]
    ignored_fields: tuple[ParityIgnoredField, ...]
    initial_authority_state: ParityInitialAuthorityState
    validity: ParityValidityInterval
    aggregate_economic_error_budget: Decimal
    account_currency: str
    invalidation_triggers: tuple[str, ...]

    @field_validator("aggregate_economic_error_budget", mode="before")
    @classmethod
    def _no_float_budget(cls, value: object) -> object:
        return _reject_float_decimal(value)

    @field_validator("invariants")
    @classmethod
    def _unique_invariants(
        cls, value: tuple[ParityInvariantSpec, ...]
    ) -> tuple[ParityInvariantSpec, ...]:
        ids = [spec.invariant_id for spec in value]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate invariant ids are forbidden")
        for spec in value:
            if spec.kind is ParityInvariantKind.DISTRIBUTIONAL:
                if not spec.statistical_test:
                    raise ValueError(
                        "distributional invariants must declare a statistical test"
                    )
                if (
                    spec.tolerance is not None
                    and not spec.awaiting_calibration_evidence
                ):
                    continue
                if spec.tolerance is None and not spec.awaiting_calibration_evidence:
                    raise ValueError(
                        "distributional tolerance requires calibration evidence"
                        " or an explicit awaiting flag"
                    )
            elif spec.statistical_test is not None:
                raise ValueError(
                    "statistical tests apply to distributional invariants only"
                )
            elif spec.tolerance is None:
                raise ValueError("exact and numeric invariants require a tolerance")
        return value


class EvidenceGate(_FrozenModel):
    """One traversed business/risk or route-specific safety gate outcome."""

    role: str
    order: int = Field(ge=0)
    inputs: Mapping[str, str]
    outcome: str
    route: str | None = None
    route_specific: bool = False
    route_policy: str | None = None

    @field_validator("route_policy")
    @classmethod
    def _policy_required_when_route_specific(
        cls, value: str | None, info: ValidationInfo
    ) -> str | None:
        if info.data.get("route_specific") and value is None:
            raise ValueError("route-specific gates must name their route policy")
        return value


class EvidenceOrder(_FrozenModel):
    """One order observation; provider transport timestamps are ignored."""

    order_id: str
    client_order_id: str | None = None
    symbol: str
    side: str
    order_type: str
    state: str
    quantity: Decimal
    filled: Decimal
    price: Decimal | None = None
    placed_at: datetime
    provider_timestamp: datetime | None = None
    retrieved_at: datetime | None = None
    receive_time: datetime | None = None

    @field_validator("quantity", "filled", "price", mode="before")
    @classmethod
    def _reject_floats(cls, value: object) -> object:
        return _reject_float_decimal(value)

    @field_validator("placed_at", "provider_timestamp", "retrieved_at")
    @classmethod
    def _utc_times(cls, value: datetime) -> datetime:
        return _validate_aware_utc(value)


class EvidenceDeal(_FrozenModel):
    """One deal observation linked to its order and position identities."""

    deal_id: str
    order_id: str
    position_id: str | None = None
    entry: str
    reason: str
    quantity: Decimal
    price: Decimal
    executed_at: datetime
    provider_timestamp: datetime | None = None

    @field_validator("quantity", "price", mode="before")
    @classmethod
    def _reject_floats(cls, value: object) -> object:
        return _reject_float_decimal(value)

    @field_validator("executed_at")
    @classmethod
    def _utc_times(cls, value: datetime) -> datetime:
        return _validate_aware_utc(value)


class EvidencePosition(_FrozenModel):
    """One position observation."""

    position_id: str
    symbol: str
    side: str
    quantity: Decimal
    state: str
    profit: Decimal
    opened_at: datetime

    @field_validator("quantity", "profit", mode="before")
    @classmethod
    def _reject_floats(cls, value: object) -> object:
        return _reject_float_decimal(value)

    @field_validator("opened_at")
    @classmethod
    def _utc_times(cls, value: datetime) -> datetime:
        return _validate_aware_utc(value)


class EvidenceReceipt(_FrozenModel):
    """One Trading execution receipt observation.

    ``authority_timestamp`` is the economic authority time; ``received_at``
    enters the latency invariant and is never ignored by name.
    """

    receipt_id: str
    intent_id: str
    client_order_id: str
    route: str
    status: str
    requested_quantity: Decimal
    filled_quantity: Decimal
    average_price: Decimal | None = None
    authority_timestamp: datetime
    received_at: datetime
    response_classification: str
    retry_safe: bool
    reconciliation_required: bool
    provider_order_id: str | None = None
    provider_deal_ids: tuple[str, ...] = ()

    @field_validator(
        "requested_quantity", "filled_quantity", "average_price", mode="before"
    )
    @classmethod
    def _reject_floats(cls, value: object) -> object:
        return _reject_float_decimal(value)

    @field_validator("authority_timestamp", "received_at")
    @classmethod
    def _utc_times(cls, value: datetime) -> datetime:
        return _validate_aware_utc(value)

    @property
    def submission_to_ack_ms(self) -> Decimal:
        """Return the evidenced submission-to-acknowledgement duration in ms."""
        return Decimal(
            str((self.received_at - self.authority_timestamp).total_seconds() * 1000)
        )


class EvidenceEvent(_FrozenModel):
    """One authority event with preserved causal edges."""

    event_id: str
    event_type: str
    occurred_at: datetime
    causes: tuple[str, ...] = ()
    source_sequence: int = Field(ge=0)

    @field_validator("occurred_at")
    @classmethod
    def _utc_times(cls, value: datetime) -> datetime:
        return _validate_aware_utc(value)


class EvidencePosting(_FrozenModel):
    """One signed account-currency ledger posting."""

    posting_id: str
    kind: str
    amount: Decimal
    occurred_at: datetime
    source_sequence: int = Field(ge=0)

    @field_validator("amount", mode="before")
    @classmethod
    def _reject_floats(cls, value: object) -> object:
        return _reject_float_decimal(value)

    @field_validator("occurred_at")
    @classmethod
    def _utc_times(cls, value: datetime) -> datetime:
        return _validate_aware_utc(value)

    @field_validator("kind")
    @classmethod
    def _known_kind(cls, value: str) -> str:
        if value not in POSTING_KINDS:
            message = "unknown posting kind: " + value
            raise ValueError(message)
        return value


class EvidenceLedger(_FrozenModel):
    """Signed ledger totals subject to the conservation equation."""

    initial_balance: Decimal
    final_balance: Decimal
    final_equity: Decimal
    unrealized_profit: Decimal
    postings: tuple[EvidencePosting, ...] = ()

    @field_validator(
        "initial_balance",
        "final_balance",
        "final_equity",
        "unrealized_profit",
        mode="before",
    )
    @classmethod
    def _reject_floats(cls, value: object) -> object:
        return _reject_float_decimal(value)

    def conservation_error(self) -> Decimal:
        """Return the residual of the signed conservation equation.

        final_balance = initial_balance + sum(signed postings); the published
        equation holds exactly when the residual is zero. Withdrawals, fees,
        tax, and adverse commissions arrive as negative postings.
        """
        return self.final_balance - (
            self.initial_balance + sum((p.amount for p in self.postings), Decimal(0))
        )

    def equity_error(self) -> Decimal:
        """Return the residual of final_equity = final_balance + unrealized."""
        return self.final_equity - (self.final_balance + self.unrealized_profit)


class EvidenceIdentity(_FrozenModel):
    """Execution identity bound into the run identity and certificate."""

    execution_model_hash: str
    config_hash: str
    source_lineage_hash: str
    tick_lineage_hash: str
    market_evidence_class: str


class EvidenceForeignActivity(_FrozenModel):
    """One ordered foreign/manual activity event outside the owner's scope."""

    event_kind: str
    occurred_at: datetime
    source_sequence: int = Field(ge=0)

    @field_validator("occurred_at")
    @classmethod
    def _utc_times(cls, value: datetime) -> datetime:
        return _validate_aware_utc(value)


class EvidenceEconomicObservations(_FrozenModel):
    """Optional measured economic samples compared by distributional rules."""

    submission_to_ack_ms: tuple[Decimal, ...] = ()
    slippage_points: tuple[Decimal, ...] = ()

    @field_validator("submission_to_ack_ms", "slippage_points", mode="before")
    @classmethod
    def _reject_floats(cls, value: object) -> object:
        return _reject_float_decimal(value)


class ParityEvidenceModel(_FrozenModel):
    """Parsed parity evidence for exactly one route execution."""

    certificate_target: ParityCertificateTarget
    evaluation_time: datetime
    identity: EvidenceIdentity
    initial_authority_state: ParityInitialAuthorityState
    foreign_activity: tuple[EvidenceForeignActivity, ...] = ()
    gates: tuple[EvidenceGate, ...] = ()
    orders: tuple[EvidenceOrder, ...] = ()
    deals: tuple[EvidenceDeal, ...] = ()
    positions: tuple[EvidencePosition, ...] = ()
    receipts: tuple[EvidenceReceipt, ...] = ()
    events: tuple[EvidenceEvent, ...] = ()
    ledger: EvidenceLedger
    economic_observations: EvidenceEconomicObservations = EvidenceEconomicObservations()

    @field_validator("evaluation_time")
    @classmethod
    def _utc_times(cls, value: datetime) -> datetime:
        return _validate_aware_utc(value)

    @field_validator("initial_authority_state", mode="before")
    @classmethod
    def _coerce_state(cls, value: object) -> object:
        if isinstance(value, Mapping) and "state_hash" in value:
            return value
        if isinstance(value, str):
            return {
                "state_hash": value,
                "exclusive_account": True,
                "foreign_activity_event_count": 0,
            }
        return value

    def foreign_activity_complete(self) -> bool:
        """Return True when exclusivity or complete replay evidence exists."""
        if self.initial_authority_state.exclusive_account:
            return True
        expected = self.initial_authority_state.foreign_activity_event_count
        return len(self.foreign_activity) == expected and expected > 0


class NormalizedEvidence(_FrozenModel):
    """Relationship-preserving normalized evidence with alpha renaming."""

    certificate_target: ParityCertificateTarget
    evaluation_time: datetime
    identity: EvidenceIdentity
    initial_authority_state: ParityInitialAuthorityState
    identifier_map: Mapping[str, str]
    gates: tuple[EvidenceGate, ...]
    orders: tuple[EvidenceOrder, ...]
    deals: tuple[EvidenceDeal, ...]
    positions: tuple[EvidencePosition, ...]
    receipts: tuple[EvidenceReceipt, ...]
    events: tuple[EvidenceEvent, ...]
    ledger: EvidenceLedger
    foreign_activity: tuple[EvidenceForeignActivity, ...]
    economic_observations: EvidenceEconomicObservations
    ambiguous_time_groups: tuple[tuple[str, ...], ...]
    causal_edges: tuple[tuple[str, str], ...]

    def foreign_activity_complete(self) -> bool:
        """Return True when exclusivity or complete replay evidence exists.

        Returns:
            Whether the initial account interval is exclusive or every
            ordered foreign/manual activity event is replayed.
        """
        if self.initial_authority_state.exclusive_account:
            return True
        expected = self.initial_authority_state.foreign_activity_event_count
        return len(self.foreign_activity) == expected and expected > 0

    def relationship_map(self) -> dict[str, object]:
        """Return the comparable relationship graph of renamed identifiers."""
        return {
            "orders": [
                {
                    "order_id": o.order_id,
                    "client_order_id": o.client_order_id,
                    "state": o.state,
                    "quantity": str(o.quantity),
                    "filled": str(o.filled),
                    "placed_at": o.placed_at.isoformat(),
                }
                for o in self.orders
            ],
            "deals": [
                {
                    "deal_id": d.deal_id,
                    "order_id": d.order_id,
                    "position_id": d.position_id,
                    "entry": d.entry,
                    "reason": d.reason,
                    "quantity": str(d.quantity),
                    "price": str(d.price),
                    "executed_at": d.executed_at.isoformat(),
                }
                for d in self.deals
            ],
            "positions": [
                {
                    "position_id": p.position_id,
                    "state": p.state,
                    "quantity": str(p.quantity),
                    "profit": str(p.profit),
                }
                for p in self.positions
            ],
            "causal_edges": [[cause, effect] for cause, effect in self.causal_edges],
            "ambiguous_time_groups": [
                list(group) for group in self.ambiguous_time_groups
            ],
        }

    def business_gates(self) -> tuple[dict[str, object], ...]:
        """Return the route-independent business/risk gate sequence."""
        return tuple(
            {
                "role": g.role,
                "order": g.order,
                "inputs": dict(sorted(g.inputs.items())),
                "outcome": g.outcome,
            }
            for g in self.gates
            if not g.route_specific
        )

    def comparable(self) -> dict[str, object]:
        """Return the full canonical comparison view of this evidence."""
        return {
            "certificate_target": str(self.certificate_target),
            "evaluation_time": self.evaluation_time.isoformat(),
            "identity": {
                "execution_model_hash": self.identity.execution_model_hash,
                "config_hash": self.identity.config_hash,
                "source_lineage_hash": self.identity.source_lineage_hash,
                "tick_lineage_hash": self.identity.tick_lineage_hash,
                "market_evidence_class": self.identity.market_evidence_class,
            },
            "initial_state_hash": self.initial_authority_state.state_hash,
            "gates": [
                {
                    "role": g.role,
                    "order": g.order,
                    "inputs": dict(sorted(g.inputs.items())),
                    "outcome": g.outcome,
                    "route_specific": g.route_specific,
                    "route_policy": g.route_policy,
                }
                for g in self.gates
            ],
            **self.relationship_map(),
            "receipts": [
                {
                    "status": r.status,
                    "response_classification": r.response_classification,
                    "requested_quantity": str(r.requested_quantity),
                    "filled_quantity": str(r.filled_quantity),
                    "average_price": (
                        str(r.average_price) if r.average_price is not None else None
                    ),
                    "authority_timestamp": r.authority_timestamp.isoformat(),
                    "retry_safe": r.retry_safe,
                    "reconciliation_required": r.reconciliation_required,
                }
                for r in self.receipts
            ],
            "events": [
                {
                    "event_type": e.event_type,
                    "occurred_at": e.occurred_at.isoformat(),
                    "source_sequence": e.source_sequence,
                }
                for e in self.events
            ],
            "ledger": {
                "initial_balance": str(self.ledger.initial_balance),
                "final_balance": str(self.ledger.final_balance),
                "final_equity": str(self.ledger.final_equity),
                "unrealized_profit": str(self.ledger.unrealized_profit),
                "postings": [
                    {
                        "posting_id": p.posting_id,
                        "kind": p.kind,
                        "amount": str(p.amount),
                        "occurred_at": p.occurred_at.isoformat(),
                        "source_sequence": p.source_sequence,
                    }
                    for p in self.ledger.postings
                ],
            },
        }


class InvariantResult(_FrozenModel):
    """Outcome of one invariant comparison."""

    invariant_id: str
    kind: ParityInvariantKind
    metric: str
    unit: str
    passed: bool
    difference: str | None = None
    detail: str | None = None


class ComparisonOutcome(_FrozenModel):
    """Deterministic comparator result; failures are ordered by invariant id."""

    envelope_version: str
    certificate_target: ParityCertificateTarget
    passed: bool
    certificate_invalidated: bool
    aggregate_economic_error: str
    invariant_results: tuple[InvariantResult, ...]
    failures: tuple[str, ...]

    def as_mapping(self) -> dict[str, object]:
        """Return the public JSON-safe comparison mapping."""
        return {
            "envelope_version": self.envelope_version,
            "certificate_target": str(self.certificate_target),
            "passed": self.passed,
            "certificate_invalidated": self.certificate_invalidated,
            "aggregate_economic_error": self.aggregate_economic_error,
            "invariants": [
                {
                    "invariant_id": r.invariant_id,
                    "kind": str(r.kind),
                    "metric": r.metric,
                    "unit": r.unit,
                    "passed": r.passed,
                    "difference": r.difference,
                    "detail": r.detail,
                }
                for r in self.invariant_results
            ],
            "failures": list(self.failures),
        }


__all__ = [
    "POSTING_KINDS",
    "ComparisonOutcome",
    "EvidenceDeal",
    "EvidenceEconomicObservations",
    "EvidenceEvent",
    "EvidenceForeignActivity",
    "EvidenceGate",
    "EvidenceIdentity",
    "EvidenceLedger",
    "EvidenceOrder",
    "EvidencePosition",
    "EvidenceReceipt",
    "InvariantResult",
    "NormalizedEvidence",
    "ParityCertificateScope",
    "ParityCertificateTarget",
    "ParityEnvelopeModel",
    "ParityIgnoredField",
    "ParityInitialAuthorityState",
    "ParityInvariantKind",
    "ParityInvariantSpec",
    "ParityRouteGatePolicy",
    "ParityValidityInterval",
]
