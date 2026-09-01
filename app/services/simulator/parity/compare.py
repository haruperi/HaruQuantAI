"""Relationship-preserving parity comparator.

The comparator classifies every invariant as exact structural, bounded
numeric, or distributional; enforces both per-field tolerances and an
aggregate account-currency economic-error budget; checks the signed
ledger-conservation equation; and evaluates certificate scope, expiry, and
identity invalidation. Failures are deterministic and ordered.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from app.composition.logging import get_logger
from app.services.simulator.errors import SimulationError
from app.services.simulator.parity.contracts import (
    ComparisonOutcome,
    InvariantResult,
    NormalizedEvidence,
    ParityEnvelopeModel,
    ParityInvariantKind,
)
from app.services.simulator.parity.envelope import load_parity_envelope
from app.services.simulator.parity.normalize import normalize_parsed_evidence

logger = get_logger(__name__)


def _decimal(value: object) -> Decimal:
    """Parse one JSON-safe numeric view value into a Decimal.

    Returns:
        The parsed Decimal value.
    """
    return Decimal(str(value))


def _structural_view(normalized: NormalizedEvidence) -> dict[str, object]:
    """Return the exact-structural comparison view of one side."""
    return normalized.comparable()


def _operational_receipt_view(
    normalized: NormalizedEvidence,
) -> tuple[dict[str, object], ...]:
    """Return v2 request and response-classification semantics only."""
    return tuple(
        {
            "requested_quantity": str(receipt.requested_quantity),
            "status": receipt.status,
            "response_classification": receipt.response_classification,
            "retry_safe": receipt.retry_safe,
            "reconciliation_required": receipt.reconciliation_required,
        }
        for receipt in normalized.receipts
    )


def _operational_linkage_view(normalized: NormalizedEvidence) -> dict[str, object]:
    """Return v2 identifier topology without empirical economic observations."""
    return {
        "deals": tuple(
            {
                "deal_id": deal.deal_id,
                "order_id": deal.order_id,
                "position_id": deal.position_id,
                "entry": deal.entry,
                "reason": deal.reason,
            }
            for deal in normalized.deals
        ),
        "positions": tuple(position.position_id for position in normalized.positions),
        "causal_edges": normalized.causal_edges,
    }


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    """Return the arithmetic mean of non-empty Decimal samples."""
    return sum(values, Decimal(0)) / Decimal(len(values))


class _Comparator:
    """One comparison run of left and right evidence under one envelope."""

    def __init__(
        self,
        left: NormalizedEvidence,
        right: NormalizedEvidence,
        envelope: ParityEnvelopeModel,
    ) -> None:
        self._left = left
        self._right = right
        self._envelope = envelope
        self._failures: list[str] = []
        self._results: list[InvariantResult] = []
        self._economic_error = Decimal(0)
        self._invalidated = False

    def _record(
        self,
        invariant_id: str,
        kind: ParityInvariantKind,
        metric: str,
        unit: str,
        passed: bool,
        difference: Decimal | None = None,
        detail: str | None = None,
    ) -> None:
        """Record one invariant result and its ordered failure message."""
        self._results.append(
            InvariantResult(
                invariant_id=invariant_id,
                kind=kind,
                metric=metric,
                unit=unit,
                passed=passed,
                difference=(str(difference) if difference is not None else None),
                detail=detail,
            )
        )
        if not passed:
            self._failures.append(f"{invariant_id}: {detail or 'comparison mismatch'}")

    def _check_identity_and_scope(self) -> None:
        """Check certificate expiry and initial-authority-state identity."""
        for side in (self._left, self._right):
            if not self._envelope.validity.covers(side.evaluation_time):
                self._invalidated = True
                self._failures.append(
                    "certificate.validity: evaluation time outside the"
                    " validity interval; the certificate is invalidated"
                )
        left_state = self._left.initial_authority_state.state_hash
        right_state = self._right.initial_authority_state.state_hash
        if left_state != right_state:
            self._invalidated = True
            self._failures.append(
                "certificate.initial_authority_state: bound identity changed;"
                " the certificate is invalidated"
            )
        if self._left.identity != self._right.identity:
            self._invalidated = True
            self._failures.append(
                "certificate.execution_identity: execution/model/lineage"
                " identity changed; the certificate is invalidated"
            )
        for label, side in (("left", self._left), ("right", self._right)):
            if not side.foreign_activity_complete():
                self._failures.append(
                    f"certificate.foreign_activity: {label} side lacks an"
                    " exclusive account interval or complete ordered"
                    " foreign/manual activity evidence"
                )

    def _compare_exact(self) -> None:
        """Compare every exact-structural invariant view field."""
        left_view = _structural_view(self._left)
        right_view = _structural_view(self._right)
        operational = self._envelope.operational_applicability is not None
        structural_targets: dict[str, tuple[object, object]] = {
            "gate.business_risk_sequence": (
                self._left.business_gates(),
                self._right.business_gates(),
            ),
            "event.category_sequence": (
                (
                    tuple(event.event_type for event in self._left.events)
                    if operational
                    else left_view["events"]
                ),
                (
                    tuple(event.event_type for event in self._right.events)
                    if operational
                    else right_view["events"]
                ),
            ),
            "receipt.status_classification": (
                (
                    _operational_receipt_view(self._left)
                    if operational
                    else left_view["receipts"]
                ),
                (
                    _operational_receipt_view(self._right)
                    if operational
                    else right_view["receipts"]
                ),
            ),
        }
        for spec in self._envelope.invariants:
            if spec.kind is not ParityInvariantKind.EXACT_STRUCTURAL:
                continue
            if spec.invariant_id in structural_targets:
                left_value, right_value = structural_targets[spec.invariant_id]
                self._record(
                    spec.invariant_id,
                    spec.kind,
                    spec.metric,
                    spec.unit,
                    left_value == right_value,
                    detail=(
                        "normalized structural sequences differ"
                        if left_value != right_value
                        else None
                    ),
                )
                continue
            if spec.invariant_id == "gate.route_safety_policy":
                self._compare_route_gates()
                continue
            if spec.invariant_id == "order.lifecycle_state":
                left_states = [o.state for o in self._left.orders]
                right_states = [o.state for o in self._right.orders]
                self._record(
                    spec.invariant_id,
                    spec.kind,
                    spec.metric,
                    spec.unit,
                    left_states == right_states,
                    detail=(
                        "order lifecycle state sequences differ"
                        if left_states != right_states
                        else None
                    ),
                )
                continue
            if spec.invariant_id == "order.linkage_graph":
                left_graph = (
                    _operational_linkage_view(self._left)
                    if operational
                    else self._left.relationship_map()
                )
                right_graph = (
                    _operational_linkage_view(self._right)
                    if operational
                    else self._right.relationship_map()
                )
                equal = (
                    left_graph["deals"] == right_graph["deals"]
                    and left_graph["positions"] == right_graph["positions"]
                    and left_graph["causal_edges"] == right_graph["causal_edges"]
                )
                self._record(
                    spec.invariant_id,
                    spec.kind,
                    spec.metric,
                    spec.unit,
                    equal,
                    detail=(
                        "order/deal/position relationship graph differs"
                        if not equal
                        else None
                    ),
                )
                continue
            if spec.invariant_id == "causal.evidenced_partial_order":
                equal = self._left.causal_edges == self._right.causal_edges and (
                    operational
                    or self._left.ambiguous_time_groups
                    == self._right.ambiguous_time_groups
                )
                self._record(
                    spec.invariant_id,
                    spec.kind,
                    spec.metric,
                    spec.unit,
                    equal,
                    detail=(
                        "causal edges or ambiguous same-timestamp groups differ"
                        if not equal
                        else None
                    ),
                )
                continue
            if spec.invariant_id == "ledger.conservation":
                self._check_conservation()
                continue
            self._record(
                spec.invariant_id,
                spec.kind,
                spec.metric,
                spec.unit,
                False,
                detail="invariant target is not implemented; fail closed",
            )

    def _compare_route_gates(self) -> None:
        """Compare route-specific safety gates against their route policy.

        Each side's route-specific gates must be exactly the set declared by
        the envelope, and each observed outcome must equal its declared route
        policy; route-specific gates are never forced to share an identifier
        with business/risk gates.
        """
        declared = {
            gate.gate_id: (gate.route, gate.policy)
            for gate in self._envelope.route_gate_policies
        }
        passed = True
        detail: str | None = None
        for label, side in (("left", self._left), ("right", self._right)):
            observed = {
                gate.role: (gate.route, gate.route_policy, gate.outcome)
                for gate in side.gates
                if gate.route_specific
            }
            expected = {
                role: (route, policy, policy)
                for role, (route, policy) in declared.items()
            }
            if observed != expected:
                passed = False
                detail = (
                    f"{label} route-specific safety gates do not match the"
                    " declared route policies"
                )
        self._record(
            "gate.route_safety_policy",
            ParityInvariantKind.EXACT_STRUCTURAL,
            "declared_route_policy_outcome",
            "sequence",
            passed,
            detail=detail,
        )

    def _check_conservation(self) -> None:
        """Assert the signed ledger equation on both sides."""
        passed = True
        detail: str | None = None
        for label, side in (("left", self._left), ("right", self._right)):
            balance_error = side.ledger.conservation_error()
            equity_error = side.ledger.equity_error()
            if balance_error != 0 or equity_error != 0:
                passed = False
                detail = (
                    f"{label} ledger violates signed conservation"
                    f" (balance residual {balance_error}, equity residual"
                    f" {equity_error})"
                )
                logger.warning("Ledger conservation violation: %s", detail)
        self._record(
            "ledger.conservation",
            ParityInvariantKind.EXACT_STRUCTURAL,
            "signed_posting_equation_residual",
            "account_currency",
            passed,
            detail=detail,
        )

    def _numeric_pairs(self) -> dict[str, tuple[Decimal, Decimal]]:
        """Extract bounded-numeric comparison targets from both sides.

        Returns:
            Mapping of invariant id to the (left, right) Decimal pair.
        """
        left_fill = sum((o.filled for o in self._left.orders), Decimal(0))
        right_fill = sum((o.filled for o in self._right.orders), Decimal(0))
        left_prices = [d.price for d in self._left.deals]
        right_prices = [d.price for d in self._right.deals]
        price_delta = (
            sum(left_prices, Decimal(0)) - sum(right_prices, Decimal(0))
            if len(left_prices) == len(right_prices)
            else Decimal(0)
        )
        return {
            "account.final_balance": (
                self._left.ledger.final_balance,
                self._right.ledger.final_balance,
            ),
            "account.final_equity": (
                self._left.ledger.final_equity,
                self._right.ledger.final_equity,
            ),
            "order.fill_quantity": (left_fill, right_fill),
            "deal.execution_price": (
                price_delta,
                Decimal(0),
            ),
        }

    def _compare_numeric(self) -> None:
        """Compare bounded-numeric invariants with per-field tolerances."""
        pairs = self._numeric_pairs()
        for spec in self._envelope.invariants:
            if spec.kind is not ParityInvariantKind.BOUNDED_NUMERIC:
                continue
            left_value, right_value = pairs.get(
                spec.invariant_id, (Decimal(0), Decimal(0))
            )
            difference = abs(left_value - right_value)
            tolerance = spec.tolerance
            if tolerance is None:
                self._record(
                    spec.invariant_id,
                    spec.kind,
                    spec.metric,
                    spec.unit,
                    False,
                    difference=difference,
                    detail="tolerance is not declared; fail closed",
                )
                continue
            passed = difference <= tolerance
            self._economic_error += difference
            self._record(
                spec.invariant_id,
                spec.kind,
                spec.metric,
                spec.unit,
                passed,
                difference=difference,
                detail=(
                    f"difference {difference} exceeds tolerance {tolerance}"
                    if not passed
                    else None
                ),
            )

    def _compare_distributional(self) -> None:
        """Compare distributional invariants under predeclared tests.

        A distributional invariant whose calibration evidence has not been
        published yet (``awaiting_calibration_evidence``) is excluded from
        the certificate's bounded claim rather than failing it: envelope v1
        certifies semantic parity only, and no threshold may be invented
        before `FEAT-SIM-17` publishes calibrated artifacts (a later
        envelope version with evidenced tolerances tightens this).
        """
        left_latency = self._left.economic_observations.submission_to_ack_ms or tuple(
            r.submission_to_ack_ms for r in self._left.receipts
        )
        right_latency = self._right.economic_observations.submission_to_ack_ms or tuple(
            r.submission_to_ack_ms for r in self._right.receipts
        )
        pairs: dict[str, tuple[tuple[Decimal, ...], tuple[Decimal, ...]]] = {
            "latency.submission_to_ack": (left_latency, right_latency),
            "slippage.points": (
                self._left.economic_observations.slippage_points,
                self._right.economic_observations.slippage_points,
            ),
        }
        for spec in self._envelope.invariants:
            if spec.kind is not ParityInvariantKind.DISTRIBUTIONAL:
                continue
            left_samples, right_samples = pairs[spec.invariant_id]
            if spec.awaiting_calibration_evidence or spec.tolerance is None:
                self._results.append(
                    InvariantResult(
                        invariant_id=spec.invariant_id,
                        kind=spec.kind,
                        metric=spec.metric,
                        unit=spec.unit,
                        passed=True,
                        detail=(
                            "not_certified: awaiting calibration evidence;"
                            " excluded from this envelope's bounded claim"
                        ),
                    )
                )
                continue
            coverage = min(len(left_samples), len(right_samples))
            if coverage < spec.minimum_coverage:
                self._record(
                    spec.invariant_id,
                    spec.kind,
                    spec.metric,
                    spec.unit,
                    False,
                    detail=(
                        f"sample coverage {coverage} below required minimum"
                        f" {spec.minimum_coverage}"
                    ),
                )
                continue
            difference = abs(_mean(left_samples) - _mean(right_samples))
            self._record(
                spec.invariant_id,
                spec.kind,
                spec.metric,
                spec.unit,
                difference <= spec.tolerance,
                difference=difference,
                detail=(
                    f"mean difference {difference} exceeds tolerance {spec.tolerance}"
                    if difference > (spec.tolerance or Decimal(0))
                    else None
                ),
            )

    def run(self) -> ComparisonOutcome:
        """Execute every invariant comparison and return the outcome.

        Returns:
            Deterministic comparison outcome with ordered failures.
        """
        self._check_identity_and_scope()
        self._compare_exact()
        self._compare_numeric()
        self._compare_distributional()
        budget = self._envelope.aggregate_economic_error_budget
        if self._economic_error > budget:
            self._failures.append(
                "aggregate.economic_error_budget: cumulative account-currency"
                f" error {self._economic_error} exceeds budget {budget}"
            )
        return ComparisonOutcome(
            envelope_version=self._envelope.envelope_version,
            certificate_target=self._envelope.certificate_scope.certificate_target,
            passed=not self._failures and not self._invalidated,
            certificate_invalidated=self._invalidated,
            aggregate_economic_error=str(self._economic_error),
            invariant_results=tuple(self._results),
            failures=tuple(self._failures),
        )


def compare_parity_evidence(
    left: Mapping[str, object],
    right: Mapping[str, object],
    envelope: Mapping[str, object],
) -> Mapping[str, object]:
    """Compare left and right route evidence under one published envelope.

    Args:
        left: JSON-safe evidence mapping for the simulated route execution.
        right: JSON-safe evidence mapping for the paired provider execution.
        envelope: Envelope mapping obtained from ``get_parity_envelope``.

    Returns:
        Read-only comparison mapping with a top-level pass flag, certificate
        scope/version, per-invariant results, relationship map, aggregate
        account-currency economic error, and deterministic ordered failures.

    Raises:
        SimulationError: If the envelope version is unknown or either side's
            evidence fails validation, claims a scope outside the envelope,
            or contains a broken identifier reference.
    """
    version = envelope.get("envelope_version", "")
    if not isinstance(version, str):
        raise SimulationError("SIM_INVALID_CONFIG", "envelope version must be a string")
    parsed_envelope = load_parity_envelope(version)
    normalized_left = normalize_parsed_evidence(left, parsed_envelope)
    normalized_right = normalize_parsed_evidence(right, parsed_envelope)
    outcome = _Comparator(normalized_left, normalized_right, parsed_envelope).run()
    result = outcome.as_mapping()
    result["relationship_map"] = normalized_left.relationship_map()
    logger.info(
        "Parity comparison finished: passed=%s invalidated=%s failures=%d",
        result["passed"],
        result["certificate_invalidated"],
        len(outcome.failures),
    )
    return result


__all__ = ["compare_parity_evidence"]
