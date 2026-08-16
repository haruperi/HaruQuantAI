"""Provider-M1 spread calibration from eligible evidence."""

# ruff: noqa: DOC201, DOC501, TC001

from __future__ import annotations

from decimal import Decimal

from app.services.simulator.calibration.contracts import _EvidenceRecord


def fit(
    records: tuple[_EvidenceRecord, ...], *, minimum_samples: int
) -> dict[str, str]:
    """Fit deterministic empirical spread quantiles by scheduled regime."""
    selected = tuple(record for record in records if record.component == "spread")
    if len(selected) < minimum_samples:
        raise ValueError("insufficient spread evidence")
    if {record.regime for record in selected} - {"ordinary", "scheduled_event"}:
        raise ValueError("only scheduled metadata regimes are canonical")
    parameters: dict[str, str] = {
        "interpretation": "provider_m1_end_of_minute_lower_bound"
    }
    for regime in ("ordinary", "scheduled_event"):
        values = sorted(record.value for record in selected if record.regime == regime)
        if not values:
            continue
        parameters[f"{regime}.p50"] = str(values[(len(values) - 1) // 2])
        parameters[f"{regime}.p95"] = str(values[(len(values) - 1) * 95 // 100])
        parameters[f"{regime}.maximum"] = str(max(values))
    parameters["mean"] = str(
        sum((record.value for record in selected), Decimal(0)) / len(selected)
    )
    return parameters


__all__ = []
