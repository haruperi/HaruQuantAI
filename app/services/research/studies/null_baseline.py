"""Matched null baselines for Research edge studies."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Literal, cast

import numpy as np
import pandas as pd

from app.services.research.contracts import EdgeResult
from app.services.research.statistics import (
    compute_null_percentile,
    null_distribution_stats,
    random_entry_null,
)
from app.utils import ValidationError, logger

if TYPE_CHECKING:
    from app.services.research.contracts import (
        StatisticalConfig,
        StudyConfig,
        TimeSplitResult,
    )

type JSONValue = (
    None | bool | int | float | str | list["JSONValue"] | Mapping[str, "JSONValue"]
)


def run_eds_null_baseline(
    data: pd.DataFrame,
    *,
    split: TimeSplitResult,
    statistics: StatisticalConfig,
    study: StudyConfig,
) -> EdgeResult:
    """Build a seeded side- and horizon-matched random-entry baseline.

    Args:
        data: Source OHLC frame used for identity validation.
        split: Declared chronological split.
        statistics: Seeded statistical policy.
        study: Closed study settings.

    Returns:
        Advisory null-baseline result.

    Raises:
        ValidationError: If required study settings or data are absent.
    """
    logger.info("Building Research edge-study null baseline")
    settings = study.mean_reversion
    side = settings.get("side")
    hold = settings.get("hold_bars")
    if side not in {"buy", "sell", "mixed"} or not isinstance(hold, int):
        raise ValidationError("RES_INPUT_INVALID", "MATCHED_NULL_POLICY_REQUIRED")
    sample = split.test if "close" in split.test else data
    distribution = random_entry_null(
        sample,
        side=cast("Literal['buy', 'sell', 'mixed']", side),
        hold_bars=hold,
        config=statistics,
    )
    evidence: Mapping[str, JSONValue] = {
        "method": "random_entry_log_return",
        "side": side,
        "hold_bars": hold,
        "split_hash": split.split_hash,
        "distribution": distribution.tolist(),
        "summary": dict(null_distribution_stats(distribution)),
        "policy_version": "v1",
    }
    return EdgeResult(
        "v1", "null_baseline", {}, evidence, "inconclusive", statistics.seed, (), True
    )


def compare_to_null(
    observed: EdgeResult, baseline: EdgeResult
) -> Mapping[str, JSONValue]:
    """Compare observed evidence with its matched baseline.

    Args:
        observed: Observed edge result carrying a mean statistic.
        baseline: Matched null-baseline result.

    Returns:
        Percentile, threshold, and empirical p-value evidence.

    Raises:
        ValidationError: If results are incompatible or malformed.
    """
    logger.info("Comparing Research edge evidence to matched null")
    value = observed.statistics.get("mean")
    distribution = baseline.null_evidence.get("distribution")
    if not isinstance(value, int | float) or not isinstance(distribution, list):
        raise ValidationError("RES_INPUT_INVALID", "NULL_COMPARISON_EVIDENCE_MISSING")
    values = np.asarray(distribution, dtype="float64")
    percentile = compute_null_percentile(float(value), values)
    return {
        "percentile": percentile,
        "threshold": float(np.quantile(values, 0.95)),
        "p_value": float((np.sum(values >= float(value)) + 1) / (values.size + 1)),
        "policy_version": "v1",
    }


def get_acceptance_criteria(baseline: EdgeResult) -> Mapping[str, JSONValue]:
    """Extract the versioned confirmation criteria from baseline evidence.

    Args:
        baseline: Matched baseline result.

    Returns:
        Closed confirmation truth-table criteria.

    Raises:
        ValidationError: If the baseline is incompatible.
    """
    logger.debug("Reading Research edge acceptance criteria")
    if (
        baseline.study != "null_baseline"
        or baseline.null_evidence.get("policy_version") != "v1"
    ):
        raise ValidationError("RES_VERSION_INCOMPATIBLE", "BASELINE_POLICY_NOT_V1")
    return {
        "policy_version": "v1",
        "confidence": 0.95,
        "adjusted_p_at_or_below_q": True,
        "directional_ci_excludes_zero": True,
        "matched_null_quantile": 0.95,
    }


__all__ = ("compare_to_null", "get_acceptance_criteria", "run_eds_null_baseline")
