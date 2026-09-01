"""Relationship-preserving normalization of parity evidence.

Normalization alpha-renames order, deal, position, receipt, and trace
identifiers in encounter order while preserving cardinality, foreign-key
relationships, and causal edges; it strips only envelope-registered ignored
fields; and it preserves economic time, ordering, and evidenced partial
orders. Events whose provider order is unobservable at identical timestamps
form explicit ambiguous groups and are never rearranged into invented
provider truth.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TypeVar

from pydantic import BaseModel

from app.composition.logging import get_logger
from app.kernel.serialization import canonical_digest, canonical_json
from app.services.simulator.errors import SimulationError
from app.services.simulator.parity.contracts import (
    EvidenceEvent,
    NormalizedEvidence,
    ParityEnvelopeModel,
    ParityEvidenceModel,
)

logger = get_logger(__name__)

_T = TypeVar("_T", bound=BaseModel)


def _renamed(value: _T, **updates: object) -> _T:
    """Return one frozen-model copy with identifier updates applied.

    Args:
        value: Source frozen Pydantic model.
        **updates: Fields to replace.

    Returns:
        New immutable instance with the updates applied.
    """
    return value.model_copy(update=updates)


class _AlphaRenamer:
    """Encounter-order identifier renamer with one shared namespace."""

    def __init__(self) -> None:
        self._map: dict[str, str] = {}
        self._counter = 0

    def define(self, original: str) -> str:
        """Assign or return the alpha name for one defined identifier.

        Returns:
            The stable alpha name assigned in encounter order.
        """
        renamed = self._map.get(original)
        if renamed is None:
            self._counter += 1
            renamed = f"a{self._counter}"
            self._map[original] = renamed
        return renamed

    def reference(self, original: str | None) -> str | None:
        """Return the alpha name for one referenced identifier, if known.

        Returns:
            The alpha name, or None when the identifier is absent.
        """
        if original is None:
            return None
        return self._map.get(original)

    def require(self, original: str) -> str:
        """Return the alpha name for one reference, failing on broken FKs.

        Returns:
            The alpha name of the referenced identifier.

        Raises:
            SimulationError: If the referenced identifier is not defined.
        """
        renamed = self._map.get(original)
        if renamed is None:
            raise SimulationError(
                "SIM_INTEGRITY_FAILURE",
                "broken foreign key: referenced identifier is not defined",
                details={"missing_reference": True},
            )
        return renamed

    @property
    def mapping(self) -> dict[str, str]:
        """Return the applied original-to-alpha renaming map.

        Returns:
            Copy of the applied renaming map.
        """
        return dict(self._map)


def _check_scope(evidence: ParityEvidenceModel, envelope: ParityEnvelopeModel) -> None:
    """Fail closed when evidence claims a scope outside the envelope.

    Raises:
        SimulationError: When the evidence certificate target differs from
            the envelope certificate target.
    """
    target = envelope.certificate_scope.certificate_target
    if evidence.certificate_target is not target:
        logger.warning(
            "Rejecting parity evidence target %s under envelope target %s",
            evidence.certificate_target,
            target,
        )
        raise SimulationError(
            "SIM_INVALID_CONFIG",
            "parity evidence certificate target does not match the envelope"
            " scope; demo evidence can never claim live scope",
            details={
                "evidence_target": str(evidence.certificate_target),
                "envelope_target": str(target),
            },
        )


def _ambiguous_time_groups(
    events: tuple[EvidenceEvent, ...],
) -> tuple[tuple[str, ...], ...]:
    """Group event identifiers sharing one economic timestamp.

    Events at identical timestamps have an unobservable provider order; the
    group is recorded explicitly and input order is never rearranged.

    Returns:
        Ordered tuples of event identifiers that share one timestamp.
    """
    by_time: dict[str, list[str]] = {}
    for event in events:
        by_time.setdefault(event.occurred_at.isoformat(), []).append(event.event_id)
    return tuple(
        tuple(identifiers)
        for _, identifiers in sorted(by_time.items())
        if len(identifiers) > 1
    )


def _normalize_evidence(
    evidence: ParityEvidenceModel, envelope: ParityEnvelopeModel
) -> NormalizedEvidence:
    """Parse, scope-check, and alpha-rename one side's evidence.

    Args:
        evidence: Parsed evidence model.
        envelope: Parsed envelope the evidence is certified under.

    Returns:
        Normalized evidence with renamed identifiers, preserved causal edges,
        and explicit ambiguous same-timestamp groups.

    Raises:
        SimulationError: If the certificate scope mismatches or a referenced
            identifier is not defined (broken foreign key).
    """
    _check_scope(evidence, envelope)
    renamer = _AlphaRenamer()

    orders = tuple(
        _renamed(
            order,
            order_id=renamer.define(order.order_id),
            client_order_id=(
                renamer.define(order.client_order_id)
                if order.client_order_id is not None
                else None
            ),
            provider_timestamp=None,
            retrieved_at=None,
            receive_time=None,
        )
        for order in evidence.orders
    )
    receipts = tuple(
        _renamed(
            receipt,
            receipt_id=renamer.define(receipt.receipt_id),
            intent_id=renamer.define(receipt.intent_id),
            client_order_id=renamer.define(receipt.client_order_id),
            provider_order_id=(
                renamer.define(receipt.provider_order_id)
                if receipt.provider_order_id is not None
                else None
            ),
            provider_deal_ids=tuple(
                renamer.define(deal_id) for deal_id in receipt.provider_deal_ids
            ),
        )
        for receipt in evidence.receipts
    )
    positions = tuple(
        _renamed(position, position_id=renamer.define(position.position_id))
        for position in evidence.positions
    )
    deals = tuple(
        _renamed(
            deal,
            deal_id=renamer.define(deal.deal_id),
            order_id=renamer.require(deal.order_id),
            position_id=(
                renamer.require(deal.position_id)
                if deal.position_id is not None
                else None
            ),
            provider_timestamp=None,
        )
        for deal in evidence.deals
    )
    events = tuple(
        _renamed(
            event,
            event_id=renamer.define(event.event_id),
            causes=tuple(renamer.require(cause) for cause in event.causes),
        )
        for event in evidence.events
    )
    postings = tuple(
        _renamed(posting, posting_id=renamer.define(posting.posting_id))
        for posting in evidence.ledger.postings
    )
    ledger = _renamed(evidence.ledger, postings=postings)
    causal_edges = tuple(
        (cause, event.event_id) for event in events for cause in event.causes
    )
    return NormalizedEvidence(
        certificate_target=evidence.certificate_target,
        evaluation_time=evidence.evaluation_time,
        identity=evidence.identity,
        initial_authority_state=evidence.initial_authority_state,
        identifier_map=renamer.mapping,
        gates=evidence.gates,
        orders=orders,
        deals=deals,
        positions=positions,
        receipts=receipts,
        events=events,
        ledger=ledger,
        foreign_activity=evidence.foreign_activity,
        economic_observations=evidence.economic_observations,
        ambiguous_time_groups=_ambiguous_time_groups(events),
        causal_edges=causal_edges,
    )


def _parse_evidence(
    evidence: Mapping[str, object],
) -> ParityEvidenceModel:
    """Validate one raw evidence mapping into the typed model.

    Args:
        evidence: JSON-safe evidence mapping.

    Returns:
        Parsed evidence model.

    Raises:
        SimulationError: If the evidence shape is invalid or contains fields
            that are neither comparable nor registered as ignored.
    """
    try:
        return ParityEvidenceModel.model_validate(evidence)
    except (ValueError, TypeError) as error:
        logger.warning("Rejecting malformed parity evidence: %s", error)
        raise SimulationError(
            "SIM_INVALID_CONFIG",
            "parity evidence failed schema validation; unregistered fields are"
            " rejected rather than ignored",
            details={"validation_error": str(error)[:512]},
        ) from error


def normalize_parity_evidence(
    evidence: Mapping[str, object], envelope: Mapping[str, object]
) -> dict[str, object]:
    """Normalize one side's parity evidence under a published envelope.

    Args:
        evidence: JSON-safe evidence mapping for one route execution.
        envelope: Envelope mapping obtained from ``get_parity_envelope``.

    Returns:
        Normalized evidence mapping containing the alpha-renamed relationship
        graph, causal edges, ambiguous same-timestamp groups, identifier map,
        and a canonical digest for cold-determinism checks.

    Raises:
        SimulationError: If the envelope is unknown/malformed, the evidence
            claims a certificate scope outside the envelope, the evidence
            shape is invalid, or a referenced identifier is undefined.
    """
    from app.services.simulator.parity.envelope import load_parity_envelope

    version = envelope.get("envelope_version", "")
    if not isinstance(version, str):
        raise SimulationError("SIM_INVALID_CONFIG", "envelope version must be a string")
    parsed_envelope = load_parity_envelope(version)
    parsed = _parse_evidence(evidence)
    normalized = _normalize_evidence(parsed, parsed_envelope)
    view = normalized.comparable()
    # The digest covers the comparable view only; the side-specific
    # identifier map is excluded so alpha-equivalent evidence hashes
    # identically across cold re-executions from fresh roots.
    view["canonical_digest"] = canonical_digest(canonical_json(view))
    view["identifier_map"] = dict(normalized.identifier_map)
    logger.debug(
        "Normalized parity evidence with %d orders, %d deals, %d events",
        len(normalized.orders),
        len(normalized.deals),
        len(normalized.events),
    )
    return view


def normalize_parsed_evidence(
    evidence: Mapping[str, object], envelope: ParityEnvelopeModel
) -> NormalizedEvidence:
    """Return the internal normalized model for comparator use.

    Args:
        evidence: JSON-safe evidence mapping for one route execution.
        envelope: Parsed envelope model.

    Returns:
        Internal normalized evidence model.

    Raises:
        SimulationError: On the same fail-closed conditions as
            ``normalize_parity_evidence``.
    """
    return _normalize_evidence(_parse_evidence(evidence), envelope)


__all__ = ["normalize_parity_evidence", "normalize_parsed_evidence"]
