"""Unit tests for Research PCA decomposition (FR-RES-081)."""

import pandas as pd
from app.services.research import UnsupervisedResearchConfig
from app.services.research.modeling import run_pca
from app.utils import logger


def _config() -> UnsupervisedResearchConfig:
    """Build a modeling configuration."""
    return UnsupervisedResearchConfig(("a", "b"), True, 2, 2, 20, 7)


def _features(rows: int = 25) -> pd.DataFrame:
    """Build a finite numeric feature frame."""
    return pd.DataFrame({"a": range(rows), "b": [i * 2 for i in range(rows)]})


def test_pca_records_preprocessing() -> None:
    """FR-RES-081: PCA records preprocessing, scores, loadings, and variance."""
    logger.debug("Testing Research PCA decomposition")
    result = run_pca(_features(), config=_config())
    assert result["schema_version"] == "v1"
    assert result["n_components"] == 2
    assert "scores" in result
    assert "loadings" in result
    assert "explained_variance" in result
    assert result["preprocessing"]["scale"] is True
