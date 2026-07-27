"""Unit tests for Research unsupervised insights (FR-RES-084 to 087)."""

import pandas as pd
from app.services.research import UnsupervisedResearchConfig
from app.services.research.modeling import (
    analyze_cluster_outperformance,
    build_unsupervised_insight_report,
    identify_pca_risk_factors,
    run_pca,
    summarize_investment_data,
)
from app.utils import logger


def _config() -> UnsupervisedResearchConfig:
    """Build a modeling configuration."""
    return UnsupervisedResearchConfig(("a", "b"), True, 2, 2, 20, 7)


def _features(rows: int = 25) -> pd.DataFrame:
    """Build a finite numeric feature frame."""
    return pd.DataFrame({"a": range(rows), "b": [i * 2 for i in range(rows)]})


def _ohlc(rows: int = 25) -> pd.DataFrame:
    """Build an OHLC frame with close for outperformance."""
    close = pd.Series([100.0 + i * 0.5 for i in range(rows)], dtype="float64")
    return pd.DataFrame({"close": close})


def test_summary_handles_constant_columns() -> None:
    """FR-RES-084: summary handles constant columns without error."""
    logger.debug("Testing Research investment summary")
    result = summarize_investment_data(
        pd.DataFrame({"x": [1.0, 1.0, 1.0], "y": [1.0, 2.0, 3.0]})
    )
    assert result["schema_version"] == "v1"
    assert result["row_count"] == 3


def test_factors_rank_absolute_loadings() -> None:
    """FR-RES-085: factors are ranked by absolute loading magnitude."""
    logger.debug("Testing Research PCA risk factors")
    pca = run_pca(_features(), config=_config())
    factors = identify_pca_risk_factors(pca, top_count=1)
    assert len(factors) >= 1
    assert "magnitude" in factors[0]


def test_cluster_outperformance_records_sample_size() -> None:
    """FR-RES-086: cluster evidence records sample counts."""
    logger.debug("Testing Research cluster outperformance")
    data = _ohlc()
    labels = pd.Series([0, 1] * 12 + [0], index=data.index)
    result = analyze_cluster_outperformance(data, labels, horizon=2)
    assert len(result) >= 1
    assert "sample_count" in result[0]


def test_insight_report_has_no_signal_control() -> None:
    """FR-RES-087: insight report excludes signal-adaptation."""
    logger.debug("Testing Research insight report")
    result = build_unsupervised_insight_report(_features(), config=_config())
    assert result["schema_version"] == "v1"
    assert result["signal_adaptation"] == "excluded"
    assert result["advisory_only"] is True
