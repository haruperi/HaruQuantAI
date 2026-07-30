"""Unit tests for Research PCA decomposition (FR-RES-081)."""

import pandas as pd
import pytest
from app.services.research import create_research_value, run_pca
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


def test_pca_guards_and_unscaled_branch() -> None:
    """Cover feature, finite, sample, dimension, and scaling branches."""
    with pytest.raises(ValueError, match="MISSING_FEATURE_COLUMNS"):
        run_pca(pd.DataFrame({"a": range(25)}), config=_config())
    nonfinite = _features()
    nonfinite.loc[0, "a"] = float("nan")
    with pytest.raises(ValueError, match="NONFINITE_FEATURE_VALUES"):
        run_pca(nonfinite, config=_config())
    with pytest.raises(ValueError, match="INSUFFICIENT_MODELING_SAMPLES"):
        run_pca(_features(2), config=_config())
    unscaled = create_research_value(
        "UnsupervisedResearchConfig",
        ("a", "b"),
        False,
        2,
        2,
        20,
        7,
    )
    assert run_pca(_features(), config=unscaled)["preprocessing"] == {"scale": False}
