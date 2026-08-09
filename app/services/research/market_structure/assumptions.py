"""Market and instrument research assumption evidence (feature).

Provides advisory evidence supporting session, liquidity, cost, margin,
lifecycle, and event assumptions drawn from Research's market-structure and
seasonality work. This does not replace Brokers profiles: Brokers owns live
instrument/margin specification; Research owns the research-baseline evidence
that informs operational assumptions.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from types import MappingProxyType
from typing import Any, Literal, cast

from app.services.research.contracts.errors import ValidationError
from app.utils import canonical_digest, to_json_safe

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_ASSUMPTION_KINDS = frozenset(
    {"session", "liquidity", "cost", "margin", "lifecycle", "event"}
)


def _utc(value: datetime) -> None:
    """Validate one UTC instant.

    Raises:
        ValidationError: If the value is not UTC-aware.
    """
    if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
        raise ValidationError("RES_INPUT_INVALID", "ASSUMPTION_TIME_NOT_UTC")


def _require_text(value: str, *, detail: str) -> None:
    """Reject empty/whitespace-only strings.

    Raises:
        ValidationError: If the value is empty or whitespace-only.
    """
    if not isinstance(value, str) or not value.strip():
        raise ValidationError("RES_INPUT_INVALID", detail)


@dataclass(frozen=True, slots=True)
class MarketAssumptionEvidence:
    """Immutable advisory market assumption evidence.

    Attributes:
        contract_version: Compatibility version; always ``v1``.
        schema_id: Stable namespaced schema identity.
        assumption_id: Research-owned assumption identifier.
        instrument: Instrument the assumption covers.
        assumption_kind: Closed assumption kind
            (session/liquidity/cost/margin/lifecycle/event).
        basis: Declared research basis for the assumption.
        details: Bounded assumption details (advisory, not live specification).
        evidence_ref: Bounded evidence reference backing the assumption.
        generated_at_utc: Evidence generation instant.
        canonical_hash: Canonical SHA-256 of the assumption material.
        advisory_only: Always ``True``; Research is advisory-only.
    """

    contract_version: Literal["v1"]
    schema_id: Literal["research.market_assumption.v1"]
    assumption_id: str
    instrument: str
    assumption_kind: Literal[
        "session", "liquidity", "cost", "margin", "lifecycle", "event"
    ]
    basis: str
    details: Mapping[str, object]
    evidence_ref: str
    generated_at_utc: datetime
    canonical_hash: str
    advisory_only: Literal[True] = field(default=True, init=False)

    def __post_init__(self) -> None:
        """Validate assumption identity, kind, and basis.

        Raises:
            ValidationError: If identity, kind, or basis are invalid.
        """
        _require_text(self.assumption_id, detail="ASSUMPTION_ID_EMPTY")
        _require_text(self.instrument, detail="ASSUMPTION_INSTRUMENT_EMPTY")
        if self.assumption_kind not in _ASSUMPTION_KINDS:
            raise ValidationError("RES_INPUT_INVALID", "ASSUMPTION_KIND")
        _require_text(self.basis, detail="ASSUMPTION_BASIS_EMPTY")
        _require_text(self.evidence_ref, detail="ASSUMPTION_EVIDENCE_REF_EMPTY")
        if not isinstance(self.details, Mapping):
            raise ValidationError("RES_INPUT_INVALID", "ASSUMPTION_DETAILS_INVALID")
        _utc(self.generated_at_utc)
        if (
            not isinstance(self.canonical_hash, str)
            or _SHA256.fullmatch(self.canonical_hash) is None
        ):
            raise ValidationError("RES_INPUT_INVALID", "ASSUMPTION_HASH_INVALID")
        object.__setattr__(self, "details", MappingProxyType(dict(self.details)))


def _assumption_material(evidence: MarketAssumptionEvidence) -> Mapping[str, object]:
    """Return the canonical hash material for one assumption."""
    return {
        "contract_version": evidence.contract_version,
        "schema_id": evidence.schema_id,
        "assumption_id": evidence.assumption_id,
        "instrument": evidence.instrument,
        "assumption_kind": evidence.assumption_kind,
        "basis": evidence.basis,
        "details": dict(evidence.details),
        "evidence_ref": evidence.evidence_ref,
        "generated_at_utc": evidence.generated_at_utc.isoformat(),
    }


def build_market_assumption_evidence(
    *,
    assumption_id: str,
    instrument: str,
    assumption_kind: Literal[
        "session", "liquidity", "cost", "margin", "lifecycle", "event"
    ],
    basis: str,
    details: Mapping[str, object],
    evidence_ref: str,
    generated_at_utc: datetime,
) -> dict[str, Any]:
    """Build a validated JSON-safe market assumption evidence v1 mapping.

    Args:
        assumption_id: Research-owned assumption identifier.
        instrument: Instrument the assumption covers.
        assumption_kind: Closed assumption kind.
        basis: Declared research basis for the assumption.
        details: Bounded assumption details (advisory, not live specification).
        evidence_ref: Bounded evidence reference backing the assumption.
        generated_at_utc: Evidence generation instant.

    Returns:
        JSON-safe assumption evidence mapping with ``canonical_hash``.

    Raises:
        ValidationError: If identity, kind, or basis are invalid.
    """
    material = {
        "contract_version": "v1",
        "schema_id": "research.market_assumption.v1",
        "assumption_id": assumption_id,
        "instrument": instrument,
        "assumption_kind": assumption_kind,
        "basis": basis,
        "details": dict(details),
        "evidence_ref": evidence_ref,
        "generated_at_utc": generated_at_utc.isoformat(),
    }
    canonical_hash = canonical_digest(material)
    evidence = MarketAssumptionEvidence(
        contract_version="v1",
        schema_id="research.market_assumption.v1",
        assumption_id=assumption_id,
        instrument=instrument,
        assumption_kind=assumption_kind,
        basis=basis,
        details=dict(details),
        evidence_ref=evidence_ref,
        generated_at_utc=generated_at_utc,
        canonical_hash=canonical_hash,
    )
    return dict(to_json_safe(_assumption_mapping(evidence)))  # type: ignore[arg-type]


def _assumption_mapping(evidence: MarketAssumptionEvidence) -> Mapping[str, object]:
    """Return the full transport mapping for one assumption."""
    return {
        "contract_version": evidence.contract_version,
        "schema_id": evidence.schema_id,
        "assumption_id": evidence.assumption_id,
        "instrument": evidence.instrument,
        "assumption_kind": evidence.assumption_kind,
        "basis": evidence.basis,
        "details": dict(evidence.details),
        "evidence_ref": evidence.evidence_ref,
        "generated_at_utc": evidence.generated_at_utc.isoformat(),
        "canonical_hash": evidence.canonical_hash,
        "advisory_only": True,
    }


def parse_market_assumption_evidence(
    value: Mapping[str, object],
) -> dict[str, Any]:
    """Parse and fully validate a market assumption evidence v1 mapping.

    Args:
        value: Candidate JSON-safe assumption evidence mapping.

    Returns:
        Re-validated JSON-safe assumption evidence mapping.

    Raises:
        ValidationError: If the mapping is structurally or semantically invalid.
    """
    if not isinstance(value, Mapping):
        raise ValidationError("RES_INPUT_INVALID", "ASSUMPTION_NOT_MAPPING")
    if value.get("contract_version") != "v1":
        raise ValidationError("RES_VERSION_INCOMPATIBLE", "ASSUMPTION_VERSION")
    if value.get("schema_id") != "research.market_assumption.v1":
        raise ValidationError("RES_VERSION_INCOMPATIBLE", "ASSUMPTION_SCHEMA")
    if value.get("advisory_only") is not True:
        raise ValidationError("RES_INPUT_INVALID", "ASSUMPTION_NOT_ADVISORY")
    return build_market_assumption_evidence(
        assumption_id=str(value["assumption_id"]),
        instrument=str(value["instrument"]),
        assumption_kind=cast(
            'Literal["session", "liquidity", "cost", "margin", "lifecycle", "event"]',
            str(value["assumption_kind"]),
        ),
        basis=str(value["basis"]),
        details=cast("Mapping[str, object]", value["details"]),
        evidence_ref=str(value["evidence_ref"]),
        generated_at_utc=datetime.fromisoformat(str(value["generated_at_utc"])),
    )


__all__ = (
    "MarketAssumptionEvidence",
    "build_market_assumption_evidence",
    "parse_market_assumption_evidence",
)
