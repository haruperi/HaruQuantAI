"""Evidence-only execution-component calibration."""

# ruff: noqa: DOC201, DOC501, TC001

from __future__ import annotations

from decimal import Decimal

from app.services.simulator.calibration.contracts import _EvidenceRecord


def fit(
    records: tuple[_EvidenceRecord, ...],
    *,
    components: tuple[str, ...],
    minimum_samples: int,
) -> tuple[dict[str, str], tuple[str, ...]]:
    """Fit only components meeting explicit evidence coverage."""
    parameters: dict[str, str] = {}
    exclusions: list[str] = []
    for component in sorted(set(components)):
        values = sorted(
            record.value for record in records if record.component == component
        )
        if len(values) < minimum_samples:
            exclusions.append(f"{component}:insufficient_evidence")
            continue
        parameters[f"{component}.sample_count"] = str(len(values))
        parameters[f"{component}.mean"] = str(sum(values, Decimal(0)) / len(values))
        parameters[f"{component}.p95"] = str(values[(len(values) - 1) * 95 // 100])
    if not parameters:
        raise ValueError("no execution component has sufficient evidence")
    return parameters, tuple(exclusions)


__all__ = []
