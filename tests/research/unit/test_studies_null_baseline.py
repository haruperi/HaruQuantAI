"""Unit tests for Research edge-study null baselines (FR-RES-062 to 064)."""

from datetime import UTC, datetime

import pandas as pd
import pytest
from app.composition.logging import get_logger
from app.services.research import (
    compare_to_null,
    create_research_value,
    get_acceptance_criteria,
    is_research_value,
    run_eds_null_baseline,
)

logger = get_logger(__name__)

_HASH = "e" * 64


def _split() -> object:
    """Build a valid chronological split carrying a close column in test."""
    idx = pd.date_range("2026-01-01", periods=30, freq="h", tz="UTC")
    prices = pd.Series(range(1, 31), index=idx, dtype=float)
    return create_research_value(
        "TimeSplitResult",
        train=pd.DataFrame({"close": prices.iloc[:10]}, index=idx[:10]),
        validation=pd.DataFrame({"close": prices.iloc[10:20]}, index=idx[10:20]),
        test=pd.DataFrame({"close": prices.iloc[20:]}, index=idx[20:]),
        boundaries={
            "train_start": datetime(2026, 1, 1, tzinfo=UTC),
            "test_end": datetime(2026, 1, 2, 5, tzinfo=UTC),
        },
        split_hash=_HASH,
    )


def _statistics() -> object:
    """Build seeded statistical settings."""
    return create_research_value(
        "StatisticalConfig", 7, 20, 20, 2, 20, "benjamini_hochberg"
    )


def _study() -> object:
    """Build a mean-reversion study policy with matched null settings."""
    return create_research_value("StudyConfig", {"side": "buy", "hold_bars": 2}, {}, {})


def test_baseline_records_seed_and_split() -> None:
    """FR-RES-062: baseline records seed and split identity."""
    logger.debug("Testing Research null baseline identity")
    baseline = run_eds_null_baseline(
        pd.DataFrame({"close": [1.0]}),
        split=_split(),
        statistics=_statistics(),
        study=_study(),
    )
    assert is_research_value(baseline, "EdgeResult")
    assert baseline.study == "null_baseline"
    assert baseline.seed == 7
    assert baseline.advisory_only is True
    assert baseline.null_evidence["split_hash"] == _HASH
    assert baseline.null_evidence["policy_version"] == "v1"
    assert isinstance(baseline.null_evidence["distribution"], list)


def test_baseline_rejects_missing_matched_policy() -> None:
    """FR-RES-062: fail closed when matched null policy is absent."""
    logger.debug("Testing Research null baseline policy rejection")
    bad_study = create_research_value("StudyConfig", {}, {}, {})
    with pytest.raises(ValueError, match="MATCHED_NULL_POLICY_REQUIRED"):
        run_eds_null_baseline(
            pd.DataFrame({"close": [1.0]}),
            split=_split(),
            statistics=_statistics(),
            study=bad_study,
        )


def test_compare_to_null_returns_percentile_and_pvalue() -> None:
    """FR-RES-063: comparison returns percentile, threshold, and p-value."""
    logger.debug("Testing Research null comparison evidence")
    baseline = run_eds_null_baseline(
        pd.DataFrame({"close": [1.0]}),
        split=_split(),
        statistics=_statistics(),
        study=_study(),
    )
    observed = create_research_value(
        "EdgeResult", "v1", "observed", {"mean": 0.0}, {}, "inconclusive", 7, (), True
    )
    comparison = compare_to_null(observed, baseline)
    assert "percentile" in comparison
    assert "threshold" in comparison
    assert "p_value" in comparison
    assert 0.0 <= comparison["p_value"] <= 1.0


def test_compare_rejects_mismatched_side() -> None:
    """FR-RES-063: fail closed when comparison evidence is malformed."""
    logger.debug("Testing Research null comparison rejection")
    baseline = run_eds_null_baseline(
        pd.DataFrame({"close": [1.0]}),
        split=_split(),
        statistics=_statistics(),
        study=_study(),
    )
    observed = create_research_value(
        "EdgeResult", "v1", "observed", {}, {}, "inconclusive", 7, (), True
    )
    with pytest.raises(ValueError, match="NULL_COMPARISON_EVIDENCE_MISSING"):
        compare_to_null(observed, baseline)


def test_criteria_follow_confirmation_policy() -> None:
    """FR-RES-064: acceptance criteria follow the v1 confirmation policy."""
    logger.debug("Testing Research acceptance criteria")
    baseline = run_eds_null_baseline(
        pd.DataFrame({"close": [1.0]}),
        split=_split(),
        statistics=_statistics(),
        study=_study(),
    )
    criteria = get_acceptance_criteria(baseline)
    assert criteria["policy_version"] == "v1"
    assert criteria["confidence"] == 0.95
    assert criteria["matched_null_quantile"] == 0.95


def test_criteria_rejects_incompatible_baseline() -> None:
    """FR-RES-064: fail closed when baseline policy is incompatible."""
    logger.debug("Testing Research acceptance criteria rejection")
    incompatible = create_research_value(
        "EdgeResult", "v1", "observed", {}, {}, "inconclusive", 7, (), True
    )
    with pytest.raises(ValueError, match="BASELINE_POLICY_NOT_V1"):
        get_acceptance_criteria(incompatible)
