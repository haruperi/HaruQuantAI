"""Executable Research studies usage example.

Demonstrates null baselines, edge studies (mean reversion, trend persistence,
session), comparison, acceptance criteria, and symbol classification.
"""

import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.research import (
    classify_symbol,
    compare_to_null,
    create_research_value,
    get_acceptance_criteria,
    run_eds_mean_reversion,
    run_eds_null_baseline,
    run_eds_session,
    run_eds_trend_persistence,
)

_HASH = "e" * 64


def _feature_header(title: str) -> None:
    """Print the feature header banner."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type name and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


def _edge_split() -> object:
    """Build a chronological split with an oscillating close in test."""
    idx = pd.date_range("2026-01-01", periods=50, freq="h", tz="UTC")
    close = pd.Series(
        [float(100 + 10 * (1 if i % 4 < 2 else -1)) for i in range(50)],
        index=idx,
        dtype="float64",
    )
    frame = pd.DataFrame({"close": close}, index=idx)
    return create_research_value(
        "TimeSplitResult",
        train=frame.iloc[:20],
        validation=frame.iloc[20:30],
        test=frame.iloc[30:],
        boundaries={
            "train_start": datetime(2026, 1, 1, tzinfo=UTC),
            "test_end": datetime(2026, 1, 3, 1, tzinfo=UTC),
        },
        split_hash=_HASH,
    )


def _statistics() -> object:
    """Build seeded statistical settings."""
    return create_research_value(
        "StatisticalConfig", 7, 20, 20, 2, 20, "benjamini_hochberg"
    )


def _study() -> object:
    """Build closed edge-study settings."""
    return create_research_value(
        "StudyConfig",
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


def _limits() -> object:
    """Build approved resource ceilings."""
    return create_research_value("ResearchResourceLimits", 500_000, 600.0, 52_428_800)


def fr_res_062() -> None:
    """FR-RES-062: Build seeded random-entry, R-space, and shuffled-return
    baselines with recorded data/split/config identity."""
    _header(
        "FR-RES-062: Build seeded random-entry, R-space, and shuffled-return baselines with recorded data/split/config identity."
    )
    print("Research Example 7: Edge Studies and Confirmation")
    split = _edge_split()
    study = create_research_value(
        "StudyConfig", {"side": "buy", "hold_bars": 2}, {}, {}
    )
    baseline = run_eds_null_baseline(
        split.test, split=split, statistics=_statistics(), study=study
    )
    print(f"FR-RES-062 baseline study={baseline.study} seed={baseline.seed}")


def fr_res_063() -> None:
    """FR-RES-063: Compare observed evidence to the correctly matched null and
    return percentile, threshold, p-value, and warnings."""
    _header(
        "FR-RES-063: Compare observed evidence to the correctly matched null and return percentile, threshold, p-value, and warnings."
    )
    split = _edge_split()
    study = create_research_value(
        "StudyConfig", {"side": "buy", "hold_bars": 2}, {}, {}
    )
    baseline = run_eds_null_baseline(
        split.test, split=split, statistics=_statistics(), study=study
    )
    observed = create_research_value(
        "EdgeResult", "v1", "observed", {"mean": 0.0}, {}, "inconclusive", 7, (), True
    )
    comparison = compare_to_null(observed, baseline)
    print(f"FR-RES-063 p_value={comparison['p_value']:.4f}")


def fr_res_064() -> None:
    """FR-RES-064: Extract versioned acceptance criteria from baseline evidence
    without hard-coded direction drift."""
    _header(
        "FR-RES-064: Extract versioned acceptance criteria from baseline evidence without hard-coded direction drift."
    )
    split = _edge_split()
    study = create_research_value(
        "StudyConfig", {"side": "buy", "hold_bars": 2}, {}, {}
    )
    baseline = run_eds_null_baseline(
        split.test, split=split, statistics=_statistics(), study=study
    )
    criteria = get_acceptance_criteria(baseline)
    print(f"FR-RES-064 confidence={criteria['confidence']}")


def fr_res_065() -> None:
    """FR-RES-065: Evaluate compression/z-score fade mean reversion on declared
    split data and return advisory uncertainty evidence."""
    _header(
        "FR-RES-065: Evaluate compression/z-score fade mean reversion on declared split data and return advisory uncertainty evidence."
    )
    split = _edge_split()
    result = run_eds_mean_reversion(
        split.test,
        split=split,
        study=_study(),
        statistics=_statistics(),
        limits=_limits(),
    )
    print(f"FR-RES-065 classification={result.classification}")


def fr_res_066() -> None:
    """FR-RES-066: Evaluate high-volatility breakout follow-through on declared
    split data and return advisory uncertainty evidence."""
    _header(
        "FR-RES-066: Evaluate high-volatility breakout follow-through on declared split data and return advisory uncertainty evidence."
    )
    split = _edge_split()
    result = run_eds_trend_persistence(
        split.test,
        split=split,
        study=_study(),
        statistics=_statistics(),
        limits=_limits(),
    )
    print(f"FR-RES-066 classification={result.classification}")


def fr_res_067() -> None:
    """FR-RES-067: Evaluate breakout/fade hypotheses on a frame already tagged
    by seasonality.tag_sessions and apply multiple-testing correction."""
    _header(
        "FR-RES-067: Evaluate breakout/fade hypotheses on a frame already tagged by seasonality.tag_sessions and apply multiple-testing correction."
    )
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
    count = result.statistics["session_count"]
    print(f"FR-RES-067 sessions={count}")


def fr_res_068() -> None:
    """FR-RES-068: Classify mean-reversion and trend evidence using one versioned
    confirmation policy and preserve uncertainty/advisory status."""
    _header(
        "FR-RES-068: Classify mean-reversion and trend evidence using one versioned confirmation policy and preserve uncertainty/advisory status."
    )
    mr = create_research_value(
        "EdgeResult", "v1", "mean_reversion", {}, {}, "confirmed", 7, (), True
    )
    tp = create_research_value(
        "EdgeResult", "v1", "trend_persistence", {}, {}, "inconclusive", 7, (), True
    )
    classification = classify_symbol(mr, tp, policy_version="v1")
    print(f"FR-RES-068 classification={classification['classification']}")


def main() -> None:
    """Run Research studies usage example."""
    _feature_header(
        "FEATURE: FEAT-RES-07 — studies/ — Edge Discovery and Confirmation\n\n"
        "Purpose: Evaluate mean-reversion, trend-persistence, and session edge hypotheses against null baselines.\n\n"
        "Module flow:\n"
        "-> Stage 1: Hypothesis parameter definition and edge study setup\n-> Stage 2: Null baseline sampling and statistical significance evaluation\n-> Stage 3: Edge confirmation decision rendering"
    )

    fr_res_062()
    fr_res_063()
    fr_res_064()
    fr_res_065()
    fr_res_066()
    fr_res_067()
    fr_res_068()


if __name__ == "__main__":
    main()
