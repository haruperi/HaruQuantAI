"""Unit tests for Research K-Means clustering (FR-RES-082, 083)."""

import pandas as pd
from app.services.research import (
    attach_cluster_labels,
    cluster_feature_space,
    create_research_value,
)
from app.utils import get_logger

logger = get_logger(__name__)


def _config() -> object:
    """Build a modeling configuration."""
    return create_research_value(
        "UnsupervisedResearchConfig", ("a", "b"), True, 2, 2, 20, 7
    )


def _features(rows: int = 25) -> pd.DataFrame:
    """Build a finite numeric feature frame."""
    return pd.DataFrame({"a": range(rows), "b": [i * 2 for i in range(rows)]})


def test_clusters_reproduce_with_seed() -> None:
    """FR-RES-082: K-Means labels are deterministic under the seed."""
    logger.debug("Testing Research K-Means reproducibility")
    first = cluster_feature_space(_features(), config=_config())
    second = cluster_feature_space(_features(), config=_config())
    assert first["labels"] == second["labels"]


def test_attach_labels_does_not_mutate() -> None:
    """FR-RES-083: attaching labels copies the frame without mutation."""
    logger.debug("Testing Research cluster label attachment")
    features = _features()
    labels = pd.Series([0, 1] * 12 + [0], index=features.index)
    result = attach_cluster_labels(features, labels)
    assert "cluster" in result.columns
    assert "cluster" not in features.columns
