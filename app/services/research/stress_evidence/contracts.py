"""Stress-scenario evidence contract (FEAT-RES-16).

Provides the historical or reasoned basis for stress shocks across nine shock
types (price, spread, liquidity, correlation, FX, margin, halt, gap,
connectivity). Every shock magnitude must cite a historical event or an
explicit reasoned assumption; invented magnitudes are rejected (settled
decision: no invented data).
"""

from __future__ import annotations

import math
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal, cast

from app.kernel.serialization import canonical_digest, to_json_safe
from app.services.research.contracts.errors import ConfigurationError, ValidationError

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
# Closed shock taxonomy: every shock must name exactly one of these types.
_SHOCK_TYPES = frozenset(
    {
        "price",
        "spread",
        "liquidity",
        "correlation",
        "fx",
        "margin",
        "halt",
        "gap",
        "connectivity",
    }
)
_BASIS_KINDS = frozenset({"historical", "reasoned"})
_SHOCK_UNITS = {
    "price": "percentage",
    "spread": "basis_points",
    "liquidity": "percentage",
    "correlation": "correlation_delta",
    "fx": "percentage",
    "margin": "percentage",
    "halt": "seconds",
    "gap": "percentage",
    "connectivity": "seconds",
}
_MAX_SHOCKS = 64


def _utc(value: datetime) -> None:
    """Validate one UTC instant.

    Raises:
        ValidationError: If the value is not UTC-aware.
    """
    if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
        raise ValidationError("RES_INPUT_INVALID", "STRESS_TIME_NOT_UTC")


def _validate_shocks(shocks: tuple[Mapping[str, object], ...]) -> None:  # noqa: C901
    """Validate each shock cites a basis and a finite magnitude.

    Args:
        shocks: Shock mappings.

    Raises:
        ValidationError: If any shock is invalid or invented.
    """
    if not shocks or len(shocks) > _MAX_SHOCKS:
        raise ValidationError("RES_STRESS_SCENARIO_INVALID", "STRESS_SHOCK_COUNT")
    for shock in shocks:
        if not isinstance(shock, Mapping):
            raise ValidationError(
                "RES_STRESS_SCENARIO_INVALID", "STRESS_SHOCK_NOT_MAPPING"
            )
        shock_type = shock.get("shock_type")
        if shock_type not in _SHOCK_TYPES:
            raise ValidationError("RES_STRESS_SCENARIO_INVALID", "STRESS_SHOCK_TYPE")
        magnitude = shock.get("magnitude")
        if not isinstance(magnitude, (int, float)) or isinstance(magnitude, bool):
            raise ValidationError("RES_STRESS_SCENARIO_INVALID", "STRESS_MAGNITUDE")
        if not math.isfinite(magnitude):
            raise ValidationError("RES_STRESS_SCENARIO_INVALID", "STRESS_MAGNITUDE")
        basis_kind = shock.get("basis_kind")
        basis_ref = shock.get("basis_ref")
        rationale = shock.get("rationale")
        unit = shock.get("unit")
        if basis_kind not in _BASIS_KINDS:
            raise ValidationError("RES_STRESS_SCENARIO_INVALID", "STRESS_BASIS_KIND")
        # Every magnitude must cite its basis — no invented data. A historical
        # basis cites a real event; a reasoned basis cites an explicit
        # assumption with its rationale.
        if not isinstance(basis_ref, str) or not basis_ref.strip():
            raise ValidationError(
                "RES_STRESS_SCENARIO_INVALID", "STRESS_BASIS_REF_EMPTY"
            )
        if unit != _SHOCK_UNITS[shock_type]:
            raise ValidationError("RES_STRESS_SCENARIO_INVALID", "STRESS_UNIT_INVALID")
        if not isinstance(rationale, str) or not rationale.strip():
            raise ValidationError(
                "RES_STRESS_SCENARIO_INVALID", "STRESS_RATIONALE_EMPTY"
            )


@dataclass(frozen=True, slots=True)
class StressScenarioEvidence:
    """Immutable stress-scenario evidence with cited shock basis.

    Attributes:
        contract_version: Compatibility version; always ``v1``.
        schema_id: Stable namespaced schema identity.
        scenario_id: Research-owned scenario identifier.
        hypothesis: Tested stress question or declared stress objective.
        shocks: Cited shock mappings (shock_type, magnitude, basis_kind, basis_ref).
        generated_at_utc: Evidence generation instant.
        canonical_hash: Canonical SHA-256 of the evidence material.
        advisory_only: Always ``True``; Research is advisory-only.
    """

    contract_version: Literal["v1"]
    schema_id: Literal["research.stress_scenario_evidence.v1"]
    scenario_id: str
    hypothesis: str
    shocks: tuple[Mapping[str, object], ...]
    generated_at_utc: datetime
    canonical_hash: str
    advisory_only: Literal[True] = field(default=True, init=False)

    def __post_init__(self) -> None:
        """Validate scenario identity, shocks, and basis.

        Raises:
            ValidationError: If identity, shocks, or basis are invalid.
        """
        if not isinstance(self.scenario_id, str) or not self.scenario_id.strip():
            raise ValidationError("RES_INPUT_INVALID", "STRESS_SCENARIO_ID_EMPTY")
        if not isinstance(self.hypothesis, str) or not self.hypothesis.strip():
            raise ValidationError("RES_INPUT_INVALID", "STRESS_HYPOTHESIS_EMPTY")
        _validate_shocks(self.shocks)
        _utc(self.generated_at_utc)
        if (
            not isinstance(self.canonical_hash, str)
            or _SHA256.fullmatch(self.canonical_hash) is None
        ):
            raise ValidationError("RES_INPUT_INVALID", "STRESS_HASH_INVALID")


def _stress_material(evidence: StressScenarioEvidence) -> Mapping[str, object]:
    """Return the canonical hash material for stress evidence."""
    return {
        "contract_version": evidence.contract_version,
        "schema_id": evidence.schema_id,
        "scenario_id": evidence.scenario_id,
        "hypothesis": evidence.hypothesis,
        "shocks": tuple(
            {
                "shock_type": str(shock["shock_type"]),
                "magnitude": shock["magnitude"],
                "basis_kind": str(shock["basis_kind"]),
                "basis_ref": str(shock["basis_ref"]),
                "unit": str(shock["unit"]),
                "rationale": str(shock["rationale"]),
            }
            for shock in evidence.shocks
        ),
        "generated_at_utc": evidence.generated_at_utc.isoformat(),
    }


def build_stress_scenario_evidence(
    *,
    scenario_id: str,
    hypothesis: str,
    shocks: tuple[Mapping[str, object], ...],
    generated_at_utc: datetime,
) -> dict[str, Any]:
    """Build validated JSON-safe stress-scenario evidence v1.

    Args:
        scenario_id: Research-owned scenario identifier.
        hypothesis: Tested stress question or declared stress objective.
        shocks: Cited shock mappings (shock_type, magnitude, basis_kind, basis_ref).
        generated_at_utc: Evidence generation instant.

    Returns:
        JSON-safe stress evidence mapping.

    Raises:
        ValidationError: If identity, shocks, or basis are invalid.
    """
    material = {
        "contract_version": "v1",
        "schema_id": "research.stress_scenario_evidence.v1",
        "scenario_id": scenario_id,
        "hypothesis": hypothesis,
        "shocks": tuple(
            {
                "shock_type": str(shock["shock_type"]),
                "magnitude": shock["magnitude"],
                "basis_kind": str(shock["basis_kind"]),
                "basis_ref": str(shock["basis_ref"]),
                "unit": str(shock["unit"]),
                "rationale": str(shock["rationale"]),
            }
            for shock in shocks
        ),
        "generated_at_utc": generated_at_utc.isoformat(),
    }
    canonical_hash = canonical_digest(material)
    evidence = StressScenarioEvidence(
        contract_version="v1",
        schema_id="research.stress_scenario_evidence.v1",
        scenario_id=scenario_id,
        hypothesis=hypothesis,
        shocks=tuple(
            {
                "shock_type": str(shock["shock_type"]),
                "magnitude": shock["magnitude"],
                "basis_kind": str(shock["basis_kind"]),
                "basis_ref": str(shock["basis_ref"]),
                "unit": str(shock["unit"]),
                "rationale": str(shock["rationale"]),
            }
            for shock in shocks
        ),
        generated_at_utc=generated_at_utc,
        canonical_hash=canonical_hash,
    )
    return dict(to_json_safe(_stress_mapping(evidence)))  # type: ignore[arg-type]


def _stress_mapping(evidence: StressScenarioEvidence) -> Mapping[str, object]:
    """Return the full transport mapping for stress evidence."""
    return {
        "contract_version": evidence.contract_version,
        "schema_id": evidence.schema_id,
        "scenario_id": evidence.scenario_id,
        "hypothesis": evidence.hypothesis,
        "shocks": evidence.shocks,
        "generated_at_utc": evidence.generated_at_utc.isoformat(),
        "canonical_hash": evidence.canonical_hash,
        "advisory_only": True,
    }


def parse_stress_scenario_evidence(
    value: Mapping[str, object],
) -> dict[str, Any]:
    """Parse and fully validate a stress-scenario evidence v1 mapping.

    Args:
        value: Candidate JSON-safe stress evidence mapping.

    Returns:
        Re-validated JSON-safe stress evidence mapping.

    Raises:
        ConfigurationError: If the supplied canonical hash does not match.
        ValidationError: If the mapping is structurally or semantically invalid.
    """
    if not isinstance(value, Mapping):
        raise ValidationError("RES_INPUT_INVALID", "STRESS_NOT_MAPPING")
    if value.get("contract_version") != "v1":
        raise ValidationError("RES_VERSION_INCOMPATIBLE", "STRESS_VERSION")
    if value.get("schema_id") != "research.stress_scenario_evidence.v1":
        raise ValidationError("RES_VERSION_INCOMPATIBLE", "STRESS_SCHEMA")
    if value.get("advisory_only") is not True:
        raise ValidationError("RES_INPUT_INVALID", "STRESS_NOT_ADVISORY")
    shocks = value.get("shocks")
    if not isinstance(shocks, (tuple, list)):
        raise ValidationError("RES_INPUT_INVALID", "STRESS_SHOCKS_INVALID")
    parsed = build_stress_scenario_evidence(
        scenario_id=str(value["scenario_id"]),
        hypothesis=str(value["hypothesis"]),
        shocks=tuple(
            {
                "shock_type": str(cast("Mapping[str, object]", shock)["shock_type"]),
                "magnitude": cast("Mapping[str, object]", shock)["magnitude"],
                "basis_kind": str(cast("Mapping[str, object]", shock)["basis_kind"]),
                "basis_ref": str(cast("Mapping[str, object]", shock)["basis_ref"]),
                "unit": str(cast("Mapping[str, object]", shock)["unit"]),
                "rationale": str(cast("Mapping[str, object]", shock)["rationale"]),
            }
            for shock in shocks
        ),
        generated_at_utc=datetime.fromisoformat(str(value["generated_at_utc"])),
    )
    if parsed["canonical_hash"] != value.get("canonical_hash"):
        raise ConfigurationError("RES_CONFIGURATION_INVALID", "STRESS_HASH_MISMATCH")
    return parsed


def validate_shock_basis(
    shocks: tuple[Mapping[str, object], ...],
) -> tuple[str, ...]:
    """Validate shock basis and return any rejected shock types.

    Args:
        shocks: Candidate shock mappings.

    Returns:
        Empty tuple when all shocks cite a valid basis; otherwise the rejected
        shock types.

    Raises:
        ValidationError: If any shock is structurally invalid.
    """
    rejected: list[str] = []
    for shock in shocks:
        if not isinstance(shock, Mapping):
            raise ValidationError(
                "RES_STRESS_SCENARIO_INVALID", "STRESS_SHOCK_NOT_MAPPING"
            )
        basis_kind = shock.get("basis_kind")
        basis_ref = shock.get("basis_ref")
        rationale = shock.get("rationale")
        unit = shock.get("unit")
        shock_type = str(shock.get("shock_type", "unknown"))
        if (
            basis_kind not in _BASIS_KINDS
            or not isinstance(basis_ref, str)
            or not basis_ref.strip()
            or _SHOCK_UNITS.get(shock_type) != unit
            or not isinstance(rationale, str)
            or not rationale.strip()
        ):
            rejected.append(shock_type)
    return tuple(rejected)


__all__ = (
    "StressScenarioEvidence",
    "build_stress_scenario_evidence",
    "parse_stress_scenario_evidence",
    "validate_shock_basis",
)
