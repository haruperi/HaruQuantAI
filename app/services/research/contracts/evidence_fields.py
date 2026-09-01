"""Research source evidence classification additions (feature).

Adds license/use classification, trust score, revisions, scope, coverage, and
quality state to the evidence contract surface. These are additive transport
mappings behind ``build_*``/``parse_*`` pairs that package source-evidence
metadata for downstream consumers without redefining Data-owned source records.
"""

from __future__ import annotations

import math
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from types import MappingProxyType
from typing import Any, Literal, cast

from app.kernel.serialization import canonical_digest, to_json_safe
from app.services.research.contracts.errors import ValidationError

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_LICENSE_USE = frozenset(
    {"unrestricted", "research_only", "redistribution_restricted", "proprietary"}
)
_MAX_SCOPE = 64


def _utc(value: datetime) -> None:
    """Validate one UTC instant.

    Raises:
        ValidationError: If the value is not UTC-aware.
    """
    if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
        raise ValidationError("RES_INPUT_INVALID", "EVIDENCE_TIME_NOT_UTC")


def _finite(value: float, *, detail: str, minimum: float, maximum: float) -> None:
    """Validate one finite bounded value.

    Raises:
        ValidationError: If the value is non-finite or out of range.
    """
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValidationError("RES_INPUT_INVALID", detail)
    if math.isnan(value) or value < minimum or value > maximum:
        raise ValidationError("RES_INPUT_INVALID", detail)


@dataclass(frozen=True, slots=True)
class ResearchSourceClassification:
    """Immutable research source evidence classification.

    Attributes:
        contract_version: Compatibility version; always ``v1``.
        schema_id: Stable namespaced schema identity.
        source_ref: Bounded source reference identity.
        license_use: License/use classification.
        trust_score: Normalized trust score in ``[0, 1]``.
        revision: Positive source revision number.
        scope: Bounded scope keys covered by the source.
        coverage: Bounded coverage fractions per scope key.
        quality_state: Closed quality-state label.
        classified_at_utc: Classification instant.
        canonical_hash: Canonical SHA-256 of the classification material.
        advisory_only: Always ``True``; Research is advisory-only.
    """

    contract_version: Literal["v1"]
    schema_id: Literal["research.source_classification.v1"]
    source_ref: str
    license_use: Literal[
        "unrestricted",
        "research_only",
        "redistribution_restricted",
        "proprietary",
    ]
    trust_score: float
    revision: int
    scope: tuple[str, ...]
    coverage: Mapping[str, float]
    quality_state: Literal["verified", "unverified", "disputed", "retracted"]
    classified_at_utc: datetime
    canonical_hash: str
    advisory_only: Literal[True] = field(default=True, init=False)

    def __post_init__(self) -> None:
        """Validate classification identity, trust, scope, and coverage.

        Raises:
            ValidationError: If identity, trust, scope, or coverage are invalid.
        """
        if not isinstance(self.source_ref, str) or not self.source_ref.strip():
            raise ValidationError("RES_INPUT_INVALID", "EVIDENCE_SOURCE_REF_EMPTY")
        if self.license_use not in _LICENSE_USE:
            raise ValidationError("RES_INPUT_INVALID", "EVIDENCE_LICENSE_USE")
        _finite(
            self.trust_score,
            detail="EVIDENCE_TRUST_SCORE",
            minimum=0.0,
            maximum=1.0,
        )
        if not isinstance(self.revision, int) or isinstance(self.revision, bool):
            raise ValidationError("RES_INPUT_INVALID", "EVIDENCE_REVISION")
        if self.revision < 1:
            raise ValidationError("RES_INPUT_INVALID", "EVIDENCE_REVISION")
        if not self.scope or len(self.scope) > _MAX_SCOPE:
            raise ValidationError("RES_INPUT_INVALID", "EVIDENCE_SCOPE")
        if not isinstance(self.coverage, Mapping):
            raise ValidationError("RES_INPUT_INVALID", "EVIDENCE_COVERAGE")
        for key, value in self.coverage.items():
            if key not in self.scope:
                raise ValidationError("RES_INPUT_INVALID", "EVIDENCE_COVERAGE_KEY")
            _finite(value, detail="EVIDENCE_COVERAGE_VALUE", minimum=0.0, maximum=1.0)
        _utc(self.classified_at_utc)
        if (
            not isinstance(self.canonical_hash, str)
            or _SHA256.fullmatch(self.canonical_hash) is None
        ):
            raise ValidationError("RES_INPUT_INVALID", "EVIDENCE_HASH_INVALID")
        object.__setattr__(self, "coverage", MappingProxyType(dict(self.coverage)))


def _classification_material(
    classification: ResearchSourceClassification,
) -> Mapping[str, object]:
    """Return the canonical hash material for one classification."""
    return {
        "contract_version": classification.contract_version,
        "schema_id": classification.schema_id,
        "source_ref": classification.source_ref,
        "license_use": classification.license_use,
        "trust_score": classification.trust_score,
        "revision": classification.revision,
        "scope": classification.scope,
        "coverage": dict(classification.coverage),
        "quality_state": classification.quality_state,
        "classified_at_utc": classification.classified_at_utc.isoformat(),
    }


def build_research_source_classification(
    *,
    source_ref: str,
    license_use: Literal[
        "unrestricted",
        "research_only",
        "redistribution_restricted",
        "proprietary",
    ],
    trust_score: float,
    revision: int,
    scope: tuple[str, ...],
    coverage: Mapping[str, float],
    quality_state: Literal["verified", "unverified", "disputed", "retracted"],
    classified_at_utc: datetime,
) -> dict[str, Any]:
    """Build a validated JSON-safe research source classification v1 mapping.

    Args:
        source_ref: Bounded source reference identity.
        license_use: License/use classification.
        trust_score: Normalized trust score in ``[0, 1]``.
        revision: Positive source revision number.
        scope: Bounded scope keys covered by the source.
        coverage: Bounded coverage fractions per scope key.
        quality_state: Closed quality-state label.
        classified_at_utc: Classification instant.

    Returns:
        JSON-safe classification mapping with ``canonical_hash``.

    Raises:
        ValidationError: If identity, trust, scope, or coverage are invalid.
    """
    material = {
        "contract_version": "v1",
        "schema_id": "research.source_classification.v1",
        "source_ref": source_ref,
        "license_use": license_use,
        "trust_score": trust_score,
        "revision": revision,
        "scope": tuple(scope),
        "coverage": dict(coverage),
        "quality_state": quality_state,
        "classified_at_utc": classified_at_utc.isoformat(),
    }
    canonical_hash = canonical_digest(material)
    classification = ResearchSourceClassification(
        contract_version="v1",
        schema_id="research.source_classification.v1",
        source_ref=source_ref,
        license_use=license_use,
        trust_score=trust_score,
        revision=revision,
        scope=tuple(scope),
        coverage=dict(coverage),
        quality_state=quality_state,
        classified_at_utc=classified_at_utc,
        canonical_hash=canonical_hash,
    )
    return dict(to_json_safe(_classification_mapping(classification)))  # type: ignore[arg-type]


def _classification_mapping(
    classification: ResearchSourceClassification,
) -> Mapping[str, object]:
    """Return the full transport mapping for one classification."""
    return {
        "contract_version": classification.contract_version,
        "schema_id": classification.schema_id,
        "source_ref": classification.source_ref,
        "license_use": classification.license_use,
        "trust_score": classification.trust_score,
        "revision": classification.revision,
        "scope": classification.scope,
        "coverage": dict(classification.coverage),
        "quality_state": classification.quality_state,
        "classified_at_utc": classification.classified_at_utc.isoformat(),
        "canonical_hash": classification.canonical_hash,
        "advisory_only": True,
    }


def parse_research_source_classification(
    value: Mapping[str, object],
) -> dict[str, Any]:
    """Parse and fully validate a research source classification v1 mapping.

    Args:
        value: Candidate JSON-safe classification mapping.

    Returns:
        Re-validated JSON-safe classification mapping.

    Raises:
        ValidationError: If the mapping is structurally or semantically invalid.
    """
    if not isinstance(value, Mapping):
        raise ValidationError("RES_INPUT_INVALID", "EVIDENCE_NOT_MAPPING")
    if value.get("contract_version") != "v1":
        raise ValidationError("RES_VERSION_INCOMPATIBLE", "EVIDENCE_VERSION")
    if value.get("schema_id") != "research.source_classification.v1":
        raise ValidationError("RES_VERSION_INCOMPATIBLE", "EVIDENCE_SCHEMA")
    if value.get("advisory_only") is not True:
        raise ValidationError("RES_INPUT_INVALID", "EVIDENCE_NOT_ADVISORY")
    scope = value.get("scope")
    if not isinstance(scope, (tuple, list)):
        raise ValidationError("RES_INPUT_INVALID", "EVIDENCE_SCOPE_INVALID")
    return build_research_source_classification(
        source_ref=str(value["source_ref"]),
        license_use=cast(
            'Literal["unrestricted", "research_only", '
            '"redistribution_restricted", "proprietary"]',
            str(value["license_use"]),
        ),
        trust_score=float(cast("Any", value["trust_score"])),
        revision=int(cast("Any", value["revision"])),
        scope=tuple(str(item) for item in scope),
        coverage=cast("Mapping[str, float]", value["coverage"]),
        quality_state=cast(
            'Literal["verified", "unverified", "disputed", "retracted"]',
            str(value["quality_state"]),
        ),
        classified_at_utc=datetime.fromisoformat(str(value["classified_at_utc"])),
    )


__all__ = (
    "ResearchSourceClassification",
    "build_research_source_classification",
    "parse_research_source_classification",
)
