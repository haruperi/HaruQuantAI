"""Unit tests for Research edge studies (FR-RES-065 to 067)."""

from datetime import UTC, datetime

import pandas as pd
from app.services.research.contracts import (
    EdgeResult,
    ResearchResourceLimits,
    StatisticalConfig,
    StudyConfig,
    TimeSplitResult,
)
from app.services.research.studies import (
    run_eds_mean_reversion,
    run_eds_session,
    run_eds_trend_persistence,
)
from app.utils import logger

_HASH = "e" * 64


def _edge_split() -> TimeSplitResult:
    """Build a chronological split with an oscillating close in test."""
    idx = pd.date_range("2026-01-01", periods=50, freq="h", tz="UTC")
    close = pd.Series(
        [float(100 + 10 * (1 if i % 4 < 2 else -1)) for i in range(50)],
        index=idx,
        dtype="float64",
    )
    frame = pd.DataFrame({"close": close}, index=idx)
    return TimeSplitResult(
        train=frame.iloc[:20],
        validation=frame.iloc[20:30],
        test=frame.iloc[30:],
        boundaries={
            "train_start": datetime(2026, 1, 1, tzinfo=UTC),
            "test_end": datetime(2026, 1, 3, 1, tzinfo=UTC),
        },
        split_hash=_HASH,
    )


def _study() -> StudyConfig:
    """Build closed edge-study settings."""
    return StudyConfig(
        mean_reversion={
            "lookback": 5,
            "entry_zscore": 0.5,
            "hold_bars": 2,
            "side": "buy",
            "minimum_samples": 1,
            "q": 0.05,
            "null_quantile": 0.95,
        },
        trend_persistence={
            "lookback": 5,
            "minimum_move": 0.01,
            "hold_bars": 2,
            "side": "buy",
            "minimum_samples": 1,
            "q": 0.05,
            "null_quantile": 0.95,
        },
        session={
            "horizon": 2,
            "minimum_samples": 1,
            "q": 0.05,
            "null_quantile": 0.95,
        },
    )


def _statistics() -> StatisticalConfig:
    """Build seeded statistical settings."""
    return StatisticalConfig(7, 20, 20, 2, 20, "benjamini_hochberg")


def _limits() -> ResearchResourceLimits:
    """Build approved resource ceilings."""
    return ResearchResourceLimits(500_000, 600.0, 52_428_800)


def test_mean_reversion_uses_matched_null() -> None:
    """FR-RES-065: mean-reversion study builds a matched null baseline."""
    logger.debug("Testing Research mean-reversion edge study")
    result = run_eds_mean_reversion(
        _edge_split().test,
        split=_edge_split(),
        study=_study(),
        statistics=_statistics(),
        limits=_limits(),
    )
    assert isinstance(result, EdgeResult)
    assert result.study == "mean_reversion"
    assert result.advisory_only is True
    assert result.seed == 7
    assert "distribution" in result.null_evidence
    assert result.null_evidence["policy_version"] == "v1"
    assert "mean" in result.statistics
    assert result.statistics["lookback"] == 5


def test_trend_study_records_rule_config() -> None:
    """FR-RES-066: trend-persistence study records its declared rule config."""
    logger.debug("Testing Research trend-persistence edge study")
    result = run_eds_trend_persistence(
        _edge_split().test,
        split=_edge_split(),
        study=_study(),
        statistics=_statistics(),
        limits=_limits(),
    )
    assert isinstance(result, EdgeResult)
    assert result.study == "trend_persistence"
    assert result.statistics["lookback"] == 5
    assert result.statistics["minimum_move"] == 0.01
    assert result.statistics["hold_bars"] == 2
    assert "distribution" in result.null_evidence


def test_session_study_applies_fdr() -> None:
    """FR-RES-067: session study applies FDR across session evidence."""
    logger.debug("Testing Research session edge study")
    split = _edge_split()
    tagged = split.test.copy()
    tagged["session"] = ["A"] * 5 + ["B"] * 5 + ["A"] * 5 + ["B"] * 5
    result = run_eds_session(
        tagged,
        split=split,
        study=_study(),
        statistics=_statistics(),
        limits=_limits(),
    )
    assert isinstance(result, EdgeResult)
    assert result.study == "session"
    assert result.null_evidence["correction"] == "benjamini_hochberg"
    sessions = result.null_evidence["sessions"]
    assert isinstance(sessions, list)
    assert len(sessions) >= 1
    for entry in sessions:
        assert "adjusted_p_value" in entry
        assert "p_value" in entry
