"""Executable Research modeling usage example.

Demonstrates PCA, K-Means clustering, insights, and the workflow.
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.research import (
    ResearchResourceLimits,
    UnsupervisedResearchConfig,
)
from app.services.research.modeling import (
    analyze_cluster_outperformance,
    attach_cluster_labels,
    build_unsupervised_insight_report,
    cluster_feature_space,
    identify_pca_risk_factors,
    run_pca,
    run_unsupervised_research,
    summarize_investment_data,
)


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _config() -> UnsupervisedResearchConfig:
    """Build a modeling configuration."""
    return UnsupervisedResearchConfig(("a", "b"), True, 2, 2, 20, 7)


def _features(rows: int = 25) -> pd.DataFrame:
    """Build a finite numeric feature frame."""
    return pd.DataFrame({"a": range(rows), "b": [i * 2 for i in range(rows)]})


def _ohlc(rows: int = 25) -> pd.DataFrame:
    """Build an OHLC frame."""
    close = pd.Series([100.0 + i * 0.5 for i in range(rows)], dtype="float64")
    return pd.DataFrame({"close": close})


def fr_res_081() -> None:
    """FR-RES-081: Scale selected finite features and return PCA evidence."""
    _header("FR-RES-081: Scale selected finite features and return PCA evidence.")
    print("Research Example 10: Unsupervised Modeling")
    pca = run_pca(_features(), config=_config())
    print(f"FR-RES-081 components={pca['n_components']}")


def fr_res_082() -> None:
    """FR-RES-082: Cluster finite feature rows with seeded K-Means."""
    _header("FR-RES-082: Cluster finite feature rows with seeded K-Means.")
    clusters = cluster_feature_space(_features(), config=_config())
    print(f"FR-RES-082 n_clusters={clusters['n_clusters']}")


def fr_res_083() -> None:
    """FR-RES-083: Attach aligned labels to a copied frame."""
    _header("FR-RES-083: Attach aligned labels to a copied frame.")
    features = _features()
    labels = pd.Series([0, 1] * 12 + [0], index=features.index)
    tagged = attach_cluster_labels(features, labels)
    print(f"FR-RES-083 columns={list(tagged.columns)}")


def fr_res_084() -> None:
    """FR-RES-084: Return descriptive evidence for investment data."""
    _header("FR-RES-084: Return descriptive evidence for investment data.")
    summary = summarize_investment_data(_features())
    print(f"FR-RES-084 row_count={summary['row_count']}")


def fr_res_085() -> None:
    """FR-RES-085: Extract largest absolute PCA loadings as factors."""
    _header("FR-RES-085: Extract largest absolute PCA loadings as factors.")
    pca = run_pca(_features(), config=_config())
    factors = identify_pca_risk_factors(pca, top_count=1)
    print(f"FR-RES-085 factor_count={len(factors)}")


def fr_res_086() -> None:
    """FR-RES-086: Compare clusters using canonical forward returns."""
    _header("FR-RES-086: Compare clusters using canonical forward returns.")
    data = _ohlc()
    labels = pd.Series([0, 1] * 12 + [0], index=data.index)
    result = analyze_cluster_outperformance(data, labels, horizon=2)
    print(f"FR-RES-086 clusters={len(result)}")


def fr_res_087() -> None:
    """FR-RES-087: Combine all evidence; omit signal-adaptation."""
    _header("FR-RES-087: Combine all evidence; omit signal-adaptation.")
    report = build_unsupervised_insight_report(_features(), config=_config())
    print(f"FR-RES-087 signal_adaptation={report['signal_adaptation']}")


def fr_res_088() -> None:
    """FR-RES-088: Execute the stateless bounded modeling workflow."""
    _header("FR-RES-088: Execute the stateless bounded modeling workflow.")
    result = run_unsupervised_research(
        _features(),
        config=_config(),
        limits=ResearchResourceLimits(500_000, 600.0, 52_428_800),
    )
    print(f"FR-RES-088 seed={result.seed} advisory={result.advisory_only}")


def main() -> None:
    """Run Research modeling usage example."""
    fr_res_081()
    fr_res_082()
    fr_res_083()
    fr_res_084()
    fr_res_085()
    fr_res_086()
    fr_res_087()
    fr_res_088()


if __name__ == "__main__":
    main()
