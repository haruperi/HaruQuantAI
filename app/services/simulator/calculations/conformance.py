"""Offline calculation artifact validation and differential execution."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping

from app.services.simulator.calculations.contracts import CalculationArtifact

_SCHEMA_ID = "simulation.calculation_conformance.v1"
_MODEL_ID = "simulation.mt5_fx_decimal.v1"


def _digest(value: object) -> str:
    """Return a canonical SHA-256 digest.

    Args:
        value: JSON-safe material.

    Returns:
        Lowercase checksum.
    """
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def model_identity() -> Mapping[str, str]:
    """Return stable calculation model identity.

    Returns:
        Model name and canonical implementation checksum.
    """
    material = {
        "model_id": _MODEL_ID,
        "modes": ["FOREX"],
        "rounding": ["ROUND_HALF_EVEN", "ROUND_HALF_UP"],
        "position_modes": ["HEDGING", "NETTING"],
    }
    return {"model_id": _MODEL_ID, "model_hash": _digest(material)}


def load(value: Mapping[str, object]) -> CalculationArtifact:
    """Load and verify one offline conformance artifact.

    Args:
        value: JSON-safe artifact mapping.

    Returns:
        Validated immutable artifact.

    Raises:
        ValueError: If schema, model, cases, or checksum is invalid.
    """
    if value.get("schema_id") != _SCHEMA_ID:
        raise ValueError("calculation artifact schema is unsupported")
    cases = value.get("cases")
    if not isinstance(cases, (tuple, list)) or not cases:
        raise ValueError("calculation artifact cases are required")
    normalized: list[Mapping[str, str]] = []
    for case in cases:
        if not isinstance(case, Mapping) or not case:
            raise ValueError("calculation artifact case is invalid")
        if any(
            not isinstance(key, str) or not isinstance(item, str)
            for key, item in case.items()
        ):
            raise ValueError("calculation artifact cases must be string mappings")
        normalized.append(dict(case))
    identity = value.get("model_identity")
    checksum = value.get("checksum")
    material = {
        "schema_id": _SCHEMA_ID,
        "model_identity": identity,
        "cases": normalized,
    }
    if (
        not isinstance(identity, str)
        or not isinstance(checksum, str)
        or checksum != _digest(material)
    ):
        raise ValueError("calculation artifact checksum mismatch")
    if identity != model_identity()["model_hash"]:
        raise ValueError("calculation artifact model identity mismatch")
    return CalculationArtifact(
        model_identity=identity,
        cases=tuple(normalized),
        checksum=checksum,
    )


def run(artifact: CalculationArtifact) -> Mapping[str, object]:
    """Compare exact expected and actual values without provider IO.

    Args:
        artifact: Validated offline artifact.

    Returns:
        Exact mismatch verdict.
    """
    mismatches = tuple(
        case.get("case_id", "unknown")
        for case in artifact.cases
        if case.get("expected") != case.get("actual")
    )
    return {
        "model_identity": artifact.model_identity,
        "artifact_checksum": artifact.checksum,
        "case_count": len(artifact.cases),
        "mismatches": mismatches,
        "passed": not mismatches,
    }


__all__ = ["load", "model_identity", "run"]
