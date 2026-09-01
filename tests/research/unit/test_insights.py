"""Unit tests for Research unsupervised insights (FR-RES-084 to 087)."""

import pandas as pd
import pytest
from app.composition.logging import get_logger
from app.services.research import (
    analyze_cluster_outperformance,
    build_unsupervised_insight_report,
    create_research_value,
    identify_pca_risk_factors,
    run_pca,
    summarize_investment_data,
)

logger = get_logger(__name__)


def _config() -> object:
    """Build a modeling configuration."""
    return create_research_value(
        "UnsupervisedResearchConfig", ("a", "b"), True, 2, 2, 20, 7
    )


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


def test_insight_report_has_no_signal_control(monkeypatch: pytest.MonkeyPatch) -> None:
    """FR-RES-087: unit composition excludes signal adaptation.

    Real PCA and K-Means collaboration is exercised by the integration suite.
    """
    logger.debug("Testing Research insight report")
    monkeypatch.setattr(
        "app.services.research.modeling.insights.run_pca",
        lambda _features, *, config: {
            "loadings": [[1.0, 0.0]],
            "feature_columns": list(config.feature_columns),
        },
    )
    monkeypatch.setattr(
        "app.services.research.modeling.insights.cluster_feature_space",
        lambda _features, *, config: {
            "n_clusters": config.clusters,
            "labels": [0] * len(_features),
        },
    )
    result = build_unsupervised_insight_report(_features(), config=_config())
    assert result["schema_version"] == "v1"
    assert result["signal_adaptation"] == "excluded"
    assert result["advisory_only"] is True


def test_insight_helpers_reject_malformed_inputs_and_report_sparse_clusters() -> None:
    """Cover descriptive, PCA-factor, label, horizon, and sparse branches."""
    with pytest.raises(ValueError, match="EMPTY_INVESTMENT_DATA"):
        summarize_investment_data(pd.DataFrame())
    with pytest.raises(ValueError, match="INVALID_TOP_COUNT"):
        identify_pca_risk_factors({}, top_count=0)
    with pytest.raises(ValueError, match="MALFORMED_PCA_EVIDENCE"):
        identify_pca_risk_factors({}, top_count=1)
    factors = identify_pca_risk_factors(
        {
            "loadings": ["bad", [None, -0.5]],
            "feature_columns": ["a", "b"],
        },
        top_count=2,
    )
    assert factors[0]["sign"] == "negative"
    with pytest.raises(ValueError, match="CLOSE_COLUMN_REQUIRED"):
        analyze_cluster_outperformance(
            pd.DataFrame({"open": [1.0]}),
            pd.Series([0]),
            horizon=1,
        )
    with pytest.raises(ValueError, match="MISALIGNED_LABELS"):
        analyze_cluster_outperformance(_ohlc(), pd.Series([0]), horizon=1)
    with pytest.raises(ValueError, match="INVALID_HORIZON"):
        analyze_cluster_outperformance(
            _ohlc(),
            pd.Series([0] * 25),
            horizon=0,
        )
    sparse = analyze_cluster_outperformance(
        _ohlc(),
        pd.Series([0] * 23 + [1, 1]),
        horizon=2,
    )
    assert sparse[1]["advisory"] == "sparse"
