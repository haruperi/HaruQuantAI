"""Unit tests for Research K-Means clustering (FR-RES-082, 083)."""

import numpy as np
import pandas as pd
import pytest
from app.composition.logging import get_logger
from app.services.research import (
    attach_cluster_labels,
    cluster_feature_space,
    create_research_value,
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


def test_clusters_forward_deterministic_seed(monkeypatch: pytest.MonkeyPatch) -> None:
    """FR-RES-082: the unit boundary forwards the deterministic seed."""
    logger.debug("Testing Research K-Means reproducibility")

    class _KMeans:
        """Fast deterministic stand-in; real seeded behavior is integration-tested."""

        def __init__(self, *, n_clusters: int, random_state: int, n_init: int) -> None:
            assert (n_clusters, random_state, n_init) == (2, 7, 10)
            self.cluster_centers_ = np.array([[0.0, 0.0], [1.0, 1.0]])
            self.inertia_ = 1.0

        def fit_predict(self, matrix: np.ndarray) -> np.ndarray:
            """Return stable labels for the supplied bounded matrix."""
            return np.arange(len(matrix)) % 2

    monkeypatch.setattr("app.services.research.modeling.clustering.KMeans", _KMeans)
    result = cluster_feature_space(_features(), config=_config())
    assert result["labels"] == [index % 2 for index in range(25)]


def test_attach_labels_does_not_mutate() -> None:
    """FR-RES-083: attaching labels copies the frame without mutation."""
    logger.debug("Testing Research cluster label attachment")
    features = _features()
    labels = pd.Series([0, 1] * 12 + [0], index=features.index)
    result = attach_cluster_labels(features, labels)
    assert "cluster" in result.columns
    assert "cluster" not in features.columns
