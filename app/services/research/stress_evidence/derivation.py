"""Historical and reasoned stress-shock derivation."""

from __future__ import annotations

import math
from collections.abc import Sequence

from app.services.research.contracts.errors import ValidationError
from app.services.research.stress_evidence.contracts import validate_shock_basis

_UNITS = {
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
_MINIMUM_HISTORICAL_OBSERVATIONS = 2


def derive_historical_stress_shock(
    *, shock_type: str, observations: Sequence[float], event_ref: str, rationale: str
) -> dict[str, object]:
    """Derive one magnitude from bounded historical observations.

    Args:
        shock_type: Closed stress shock type.
        observations: Genuine ordered observations for the cited event.
        event_ref: Historical event evidence reference.
        rationale: Explanation of the selected derivation.

    Returns:
        Validated historical shock mapping.

    Raises:
        ValidationError: If evidence is missing or non-finite.
    """
    values = tuple(float(value) for value in observations)
    if (
        shock_type not in _UNITS
        or len(values) < _MINIMUM_HISTORICAL_OBSERVATIONS
        or not all(map(math.isfinite, values))
    ):
        raise ValidationError("RES_STRESS_SCENARIO_INVALID", "HISTORY_INVALID")
    if not event_ref.strip() or not rationale.strip():
        raise ValidationError("RES_STRESS_SCENARIO_INVALID", "HISTORY_BASIS_EMPTY")
    baseline = abs(values[0])
    if baseline == 0:
        raise ValidationError("RES_STRESS_SCENARIO_INVALID", "HISTORY_BASELINE_ZERO")
    magnitude = max(abs(value - values[0]) for value in values)
    if _UNITS[shock_type] in {"percentage", "basis_points"}:
        magnitude = (
            magnitude
            / baseline
            * (10_000 if _UNITS[shock_type] == "basis_points" else 100)
        )
    shock = {
        "shock_type": shock_type,
        "magnitude": magnitude,
        "unit": _UNITS[shock_type],
        "basis_kind": "historical",
        "basis_ref": event_ref,
        "rationale": rationale,
    }
    validate_shock_basis((shock,))
    return shock


def build_reasoned_stress_shock(
    *, shock_type: str, magnitude: float, assumption_ref: str, rationale: str
) -> dict[str, object]:
    """Build one explicitly reasoned, non-fabricated shock assumption.

    Args:
        shock_type: Closed stress shock type.
        magnitude: Explicit finite shock magnitude.
        assumption_ref: Durable assumption reference.
        rationale: Explanation supporting the magnitude.

    Returns:
        Validated reasoned shock mapping.

    Raises:
        ValidationError: If the assumption evidence is invalid.
    """
    shock = {
        "shock_type": shock_type,
        "magnitude": magnitude,
        "unit": _UNITS.get(shock_type, ""),
        "basis_kind": "reasoned",
        "basis_ref": assumption_ref,
        "rationale": rationale,
    }
    if validate_shock_basis((shock,)):
        raise ValidationError("RES_STRESS_SCENARIO_INVALID", "REASONED_BASIS_INVALID")
    return shock


__all__ = ("build_reasoned_stress_shock", "derive_historical_stress_shock")
