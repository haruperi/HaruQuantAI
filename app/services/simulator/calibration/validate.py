"""Validation and drift invalidation for calibration artifacts."""

# ruff: noqa: DOC201, DOC501, TC001

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

from app.services.simulator.calibration.contracts import (
    _CalibrationArtifact,
    _Partition,
)


def validate(
    artifact: _CalibrationArtifact,
    validation: _Partition,
    *,
    evaluated_at: datetime,
) -> dict[str, object]:
    """Evaluate predeclared error tolerance without opening certification data."""
    if validation.name != "validation":
        raise ValueError("only the validation partition may be evaluated")
    if validation.checksum != artifact.partition_hashes["validation"]:
        raise ValueError("validation partition hash mismatch")
    if evaluated_at.tzinfo is None or evaluated_at.utcoffset() != timedelta(0):
        raise ValueError("evaluated_at must be aware UTC")
    if evaluated_at > artifact.valid_until:
        return {"valid": False, "reason": "calibration_expired", "observed_error": None}
    values = tuple(
        record.value
        for record in validation.records
        if record.component == artifact.component
    )
    if not values:
        return {
            "valid": False,
            "reason": "validation_coverage_absent",
            "observed_error": None,
        }
    predicted = Decimal(artifact.parameters.get("mean", "0"))
    if artifact.component != "spread":
        predicted = Decimal(artifact.parameters.get(f"{artifact.component}.mean", "0"))
    observed_error = sum(
        (abs(value - predicted) for value in values), Decimal(0)
    ) / len(values)
    valid = (
        observed_error <= artifact.threshold_tolerance
        and observed_error <= artifact.economic_error_budget
    )
    return {
        "valid": valid,
        "reason": "within_predeclared_budget" if valid else "detected_drift",
        "observed_error": str(observed_error),
        "metric": artifact.threshold_metric,
        "test": artifact.threshold_test,
    }


__all__ = []
