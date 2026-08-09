"""Versioned strategy evidence bundle (feature, EXTEND FEAT-RES-07).

Packages the hypothesis, instruments, regimes, sessions, methodology, sample,
costs, results, limitations, and versioned strategy linkage into one advisory
bundle so downstream domains receive a complete, citable evidence package
rather than scattered stage outputs. The bundle references (never redefines)
the owning domain's contracts.
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
_MAX_INSTRUMENTS = 64


def _utc(value: datetime) -> None:
    """Validate one UTC instant.

    Raises:
        ValidationError: If the value is not UTC-aware.
    """
    if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
        raise ValidationError("RES_INPUT_INVALID", "BUNDLE_TIME_NOT_UTC")


def _require_text(value: str, *, detail: str) -> None:
    """Reject empty/whitespace-only strings.

    Raises:
        ValidationError: If the value is empty or whitespace-only.
    """
    if not isinstance(value, str) or not value.strip():
        raise ValidationError("RES_INPUT_INVALID", detail)


@dataclass(frozen=True, slots=True)
class StrategyEvidenceBundle:
    """Immutable versioned strategy evidence bundle.

    Attributes:
        contract_version: Compatibility version; always ``v1``.
        schema_id: Stable namespaced schema identity.
        bundle_id: Research-owned bundle identifier.
        strategy_version: Versioned strategy linkage identity.
        hypothesis: Tested question or declared research objective.
        instruments: Instruments covered by the strategy.
        regimes: Regimes covered by the strategy.
        sessions: Sessions covered by the strategy.
        methodology: Declared methodology summary.
        sample_from_utc: Inclusive start of the evaluated sample.
        sample_to_utc: Inclusive end of the evaluated sample.
        sample_size: Number of evaluated observations.
        costs: Declared cost assumptions (spread, commission, slippage).
        results: Bounded result summary (advisory, not performance claims).
        limitations: Declared limitations and caveats.
        generated_at_utc: Bundle generation instant.
        canonical_hash: Canonical SHA-256 of the bundle material.
        advisory_only: Always ``True``; Research is advisory-only.
    """

    contract_version: Literal["v1"]
    schema_id: Literal["research.strategy_evidence_bundle.v1"]
    bundle_id: str
    strategy_version: str
    hypothesis: str
    instruments: tuple[str, ...]
    regimes: tuple[str, ...]
    sessions: tuple[str, ...]
    methodology: str
    sample_from_utc: datetime
    sample_to_utc: datetime
    sample_size: int
    costs: Mapping[str, object]
    results: Mapping[str, object]
    limitations: tuple[str, ...]
    generated_at_utc: datetime
    canonical_hash: str
    advisory_only: Literal[True] = field(default=True, init=False)

    def __post_init__(self) -> None:
        """Validate bundle identity, scope, and sample bounds.

        Raises:
            ValidationError: If identity, scope, or sample are invalid.
        """
        _require_text(self.bundle_id, detail="BUNDLE_ID_EMPTY")
        _require_text(self.strategy_version, detail="BUNDLE_STRATEGY_VERSION_EMPTY")
        _require_text(self.hypothesis, detail="BUNDLE_HYPOTHESIS_EMPTY")
        _require_text(self.methodology, detail="BUNDLE_METHODOLOGY_EMPTY")
        if not self.instruments or len(self.instruments) > _MAX_INSTRUMENTS:
            raise ValidationError("RES_INPUT_INVALID", "BUNDLE_INSTRUMENT_SCOPE")
        if self.sample_size < 1:
            raise ValidationError("RES_INPUT_INVALID", "BUNDLE_SAMPLE_SIZE")
        _utc(self.sample_from_utc)
        _utc(self.sample_to_utc)
        _utc(self.generated_at_utc)
        if self.sample_from_utc > self.sample_to_utc:
            raise ValidationError("RES_INPUT_INVALID", "BUNDLE_SAMPLE_WINDOW")
        if not isinstance(self.costs, Mapping):
            raise ValidationError("RES_INPUT_INVALID", "BUNDLE_COSTS_INVALID")
        if not isinstance(self.results, Mapping):
            raise ValidationError("RES_INPUT_INVALID", "BUNDLE_RESULTS_INVALID")
        if not isinstance(self.limitations, tuple):
            raise ValidationError("RES_INPUT_INVALID", "BUNDLE_LIMITATIONS_INVALID")
        if (
            not isinstance(self.canonical_hash, str)
            or _SHA256.fullmatch(self.canonical_hash) is None
        ):
            raise ValidationError("RES_INPUT_INVALID", "BUNDLE_HASH_INVALID")
        for field_name in ("costs", "results"):
            object.__setattr__(
                self, field_name, MappingProxyType(dict(getattr(self, field_name)))
            )


def _bundle_material(bundle: StrategyEvidenceBundle) -> Mapping[str, object]:
    """Return the canonical hash material for one bundle."""
    return {
        "contract_version": bundle.contract_version,
        "schema_id": bundle.schema_id,
        "bundle_id": bundle.bundle_id,
        "strategy_version": bundle.strategy_version,
        "hypothesis": bundle.hypothesis,
        "instruments": bundle.instruments,
        "regimes": bundle.regimes,
        "sessions": bundle.sessions,
        "methodology": bundle.methodology,
        "sample_from_utc": bundle.sample_from_utc.isoformat(),
        "sample_to_utc": bundle.sample_to_utc.isoformat(),
        "sample_size": bundle.sample_size,
        "costs": dict(bundle.costs),
        "results": dict(bundle.results),
        "limitations": bundle.limitations,
        "generated_at_utc": bundle.generated_at_utc.isoformat(),
    }


def build_strategy_evidence_bundle(
    *,
    bundle_id: str,
    strategy_version: str,
    hypothesis: str,
    instruments: tuple[str, ...],
    regimes: tuple[str, ...],
    sessions: tuple[str, ...],
    methodology: str,
    sample_from_utc: datetime,
    sample_to_utc: datetime,
    sample_size: int,
    costs: Mapping[str, object],
    results: Mapping[str, object],
    limitations: tuple[str, ...],
    generated_at_utc: datetime,
) -> dict[str, Any]:
    """Build a validated JSON-safe strategy evidence bundle v1 mapping.

    Args:
        bundle_id: Research-owned bundle identifier.
        strategy_version: Versioned strategy linkage identity.
        hypothesis: Tested question or declared research objective.
        instruments: Instruments covered by the strategy.
        regimes: Regimes covered by the strategy.
        sessions: Sessions covered by the strategy.
        methodology: Declared methodology summary.
        sample_from_utc: Inclusive start of the evaluated sample.
        sample_to_utc: Inclusive end of the evaluated sample.
        sample_size: Number of evaluated observations.
        costs: Declared cost assumptions (spread, commission, slippage).
        results: Bounded result summary (advisory, not performance claims).
        limitations: Declared limitations and caveats.
        generated_at_utc: Bundle generation instant.

    Returns:
        JSON-safe bundle mapping with ``canonical_hash``.

    Raises:
        ValidationError: If identity, scope, or sample are invalid.
    """
    material = {
        "contract_version": "v1",
        "schema_id": "research.strategy_evidence_bundle.v1",
        "bundle_id": bundle_id,
        "strategy_version": strategy_version,
        "hypothesis": hypothesis,
        "instruments": tuple(instruments),
        "regimes": tuple(regimes),
        "sessions": tuple(sessions),
        "methodology": methodology,
        "sample_from_utc": sample_from_utc.isoformat(),
        "sample_to_utc": sample_to_utc.isoformat(),
        "sample_size": sample_size,
        "costs": dict(costs),
        "results": dict(results),
        "limitations": tuple(limitations),
        "generated_at_utc": generated_at_utc.isoformat(),
    }
    canonical_hash = canonical_digest(material)
    bundle = StrategyEvidenceBundle(
        contract_version="v1",
        schema_id="research.strategy_evidence_bundle.v1",
        bundle_id=bundle_id,
        strategy_version=strategy_version,
        hypothesis=hypothesis,
        instruments=tuple(instruments),
        regimes=tuple(regimes),
        sessions=tuple(sessions),
        methodology=methodology,
        sample_from_utc=sample_from_utc,
        sample_to_utc=sample_to_utc,
        sample_size=sample_size,
        costs=dict(costs),
        results=dict(results),
        limitations=tuple(limitations),
        generated_at_utc=generated_at_utc,
        canonical_hash=canonical_hash,
    )
    return dict(to_json_safe(_bundle_mapping(bundle)))  # type: ignore[arg-type]


def _bundle_mapping(bundle: StrategyEvidenceBundle) -> Mapping[str, object]:
    """Return the full transport mapping for one bundle."""
    return {
        "contract_version": bundle.contract_version,
        "schema_id": bundle.schema_id,
        "bundle_id": bundle.bundle_id,
        "strategy_version": bundle.strategy_version,
        "hypothesis": bundle.hypothesis,
        "instruments": bundle.instruments,
        "regimes": bundle.regimes,
        "sessions": bundle.sessions,
        "methodology": bundle.methodology,
        "sample_from_utc": bundle.sample_from_utc.isoformat(),
        "sample_to_utc": bundle.sample_to_utc.isoformat(),
        "sample_size": bundle.sample_size,
        "costs": dict(bundle.costs),
        "results": dict(bundle.results),
        "limitations": bundle.limitations,
        "generated_at_utc": bundle.generated_at_utc.isoformat(),
        "canonical_hash": bundle.canonical_hash,
        "advisory_only": True,
    }


def parse_strategy_evidence_bundle(
    value: Mapping[str, object],
) -> dict[str, Any]:
    """Parse and fully validate a strategy evidence bundle v1 mapping.

    Args:
        value: Candidate JSON-safe bundle mapping.

    Returns:
        Re-validated JSON-safe bundle mapping.

    Raises:
        ValidationError: If the mapping is structurally or semantically invalid.
    """
    if not isinstance(value, Mapping):
        raise ValidationError("RES_INPUT_INVALID", "BUNDLE_NOT_MAPPING")
    if value.get("contract_version") != "v1":
        raise ValidationError("RES_VERSION_INCOMPATIBLE", "BUNDLE_VERSION")
    if value.get("schema_id") != "research.strategy_evidence_bundle.v1":
        raise ValidationError("RES_VERSION_INCOMPATIBLE", "BUNDLE_SCHEMA")
    if value.get("advisory_only") is not True:
        raise ValidationError("RES_INPUT_INVALID", "BUNDLE_NOT_ADVISORY")
    instruments = value.get("instruments")
    regimes = value.get("regimes")
    sessions = value.get("sessions")
    if not all(
        isinstance(item, (tuple, list)) for item in (instruments, regimes, sessions)
    ):
        raise ValidationError("RES_INPUT_INVALID", "BUNDLE_SCOPE_INVALID")
    return build_strategy_evidence_bundle(
        bundle_id=str(value["bundle_id"]),
        strategy_version=str(value["strategy_version"]),
        hypothesis=str(value["hypothesis"]),
        instruments=tuple(
            str(item) for item in cast("tuple[Any, ...] | list[Any]", instruments)
        ),
        regimes=tuple(
            str(item) for item in cast("tuple[Any, ...] | list[Any]", regimes)
        ),
        sessions=tuple(
            str(item) for item in cast("tuple[Any, ...] | list[Any]", sessions)
        ),
        methodology=str(value["methodology"]),
        sample_from_utc=datetime.fromisoformat(str(value["sample_from_utc"])),
        sample_to_utc=datetime.fromisoformat(str(value["sample_to_utc"])),
        sample_size=int(cast("Any", value["sample_size"])),
        costs=cast("Mapping[str, object]", value["costs"]),
        results=cast("Mapping[str, object]", value["results"]),
        limitations=tuple(
            str(item)
            for item in cast("tuple[Any, ...] | list[Any]", value["limitations"])
        ),
        generated_at_utc=datetime.fromisoformat(str(value["generated_at_utc"])),
    )


__all__ = (
    "StrategyEvidenceBundle",
    "build_strategy_evidence_bundle",
    "parse_strategy_evidence_bundle",
)
