"""Bounded candidate calibration using the canonical structure score."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from app.services.research.contracts import ResearchWarning
from app.services.research.market_structure.profile import (
    canonical_structure_score,
)
from app.utils import ValidationError, logger

if TYPE_CHECKING:
    from app.services.research.contracts import (
        MarketStructureConfig,
        ResearchResourceLimits,
    )

type JSONValue = (
    None | bool | int | float | str | list["JSONValue"] | Mapping[str, "JSONValue"]
)


def calibrate_market_structure(
    run_rows: Sequence[Mapping[str, JSONValue]],
    validation_rows: Sequence[Mapping[str, JSONValue]],
    *,
    config: MarketStructureConfig,
    limits: ResearchResourceLimits,  # noqa: ARG001 - documented resource gate
) -> Mapping[str, JSONValue]:
    """Rank a bounded candidate grid against approved validation truth.

    Uses the same canonical score as ``build_market_structure_profile``.

    Args:
        run_rows: Run-evidence rows carrying efficiency ratios.
        validation_rows: Validation-truth rows for accuracy weighting.
        config: Bounded market-structure settings with calibration_grid.
        limits: Approved resource ceilings.

    Returns:
        Versioned calibration evidence with ranked candidates and warnings.

    Raises:
        ValidationError: If truth/candidate/resource inputs are invalid.
    """
    logger.info("Calibrating Research market-structure candidates")
    if not run_rows:
        raise ValidationError("RES_INPUT_INVALID", "EMPTY_RUN_ROWS")
    grid = config.profile.get("calibration_grid")
    if not isinstance(grid, list) or not grid:
        raise ValidationError("RES_INPUT_INVALID", "MISSING_CALIBRATION_GRID")
    if len(grid) > config.calibration_candidates:
        raise ValidationError("RES_RESOURCE_LIMIT_EXCEEDED", "CANDIDATE_LIMIT_EXCEEDED")
    trend_threshold = float(
        config.profile.get("trend_threshold", 0.5)  # type: ignore[arg-type]
    )
    range_threshold = float(
        config.profile.get("range_threshold", 0.2)  # type: ignore[arg-type]
    )
    validation_verdicts = {
        str(row.get("symbol", "")): str(row.get("verdict", "mixed"))
        for row in validation_rows
    }
    warnings: list[ResearchWarning] = []
    if not validation_rows:
        warnings.append(
            ResearchWarning(
                "NO_VALIDATION_TRUTH",
                "Calibration ran without approved validation truth",
                "warning",
                "validation",
                {},
            )
        )
    ranked: list[tuple[float, JSONValue]] = []
    for candidate in grid:
        if not isinstance(candidate, Mapping):
            continue
        threshold = float(candidate.get("trend_threshold", trend_threshold))  # type: ignore[arg-type]
        correct = 0
        total = 0
        for row in run_rows:
            ratio = row.get("efficiency_ratio")
            verdict = row.get("verdict")
            if not isinstance(ratio, int | float) or verdict is None:
                continue
            score = canonical_structure_score(
                efficiency_ratio=float(ratio),
                trend_threshold=threshold,
                range_threshold=range_threshold,
            )
            predicted = "trend" if score >= 100.0 * threshold else "range"
            symbol = str(row.get("symbol", ""))
            truth = validation_verdicts.get(symbol)
            total += 1
            if truth and predicted in truth:
                correct += 1
        accuracy = correct / total if total > 0 else 0.0
        ranked.append((accuracy, {"candidate": dict(candidate), "accuracy": accuracy}))
    ranked.sort(key=lambda item: item[0], reverse=True)
    warning_values: list[JSONValue] = [
        {
            "code": warning.code,
            "message": warning.message,
            "severity": warning.severity,
            "field_path": warning.field_path,
            "details": warning.details,
        }
        for warning in warnings
    ]
    return {
        "schema_version": "v1",
        "candidate_count": len(ranked),
        "ranked": [entry for _, entry in ranked],
        "criteria": "canonical_structure_score",
        "warnings": warning_values,
    }


__all__ = ("calibrate_market_structure",)
