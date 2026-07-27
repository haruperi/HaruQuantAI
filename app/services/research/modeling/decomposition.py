"""Deterministic PCA decomposition evidence for Research."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from app.utils import ValidationError, logger

if TYPE_CHECKING:
    from collections.abc import Mapping

    from app.services.research.contracts import UnsupervisedResearchConfig

type JSONValue = (
    None | bool | int | float | str | list["JSONValue"] | Mapping[str, "JSONValue"]
)


def _select_finite_features(
    features: pd.DataFrame, config: UnsupervisedResearchConfig
) -> tuple[pd.DataFrame, np.ndarray]:
    """Select and validate finite numeric feature columns.

    Args:
        features: Candidate frame.
        config: Modeling configuration with declared feature columns.

    Returns:
        The selected finite frame and its float64 matrix.

    Raises:
        ValidationError: If columns are missing, non-finite, or insufficient.
    """
    logger.debug("Selecting Research PCA feature columns")
    missing = [c for c in config.feature_columns if c not in features.columns]
    if missing:
        raise ValidationError("RES_INPUT_INVALID", "MISSING_FEATURE_COLUMNS")
    selected = features[list(config.feature_columns)].astype("float64")
    matrix = selected.to_numpy()
    if not np.isfinite(matrix).all():
        raise ValidationError("RES_INPUT_INVALID", "NONFINITE_FEATURE_VALUES")
    if matrix.shape[0] < config.minimum_samples:
        raise ValidationError("RES_INSUFFICIENT_DATA", "INSUFFICIENT_MODELING_SAMPLES")
    return selected, matrix


def run_pca(
    features: pd.DataFrame,
    *,
    config: UnsupervisedResearchConfig,
) -> Mapping[str, JSONValue]:
    """Scale selected features and compute PCA scores, loadings, and variance.

    Args:
        features: Frame containing declared feature columns.
        config: Modeling configuration with PCA dimensions.

    Returns:
        Versioned PCA evidence with preprocessing and diagnostics.

    Raises:
        ValidationError: If features are invalid, constant, or insufficient.
    """
    logger.info("Running Research PCA decomposition")
    _selected, matrix = _select_finite_features(features, config)
    if config.pca_components > matrix.shape[1]:
        raise ValidationError("RES_INPUT_INVALID", "PCA_COMPONENTS_EXCEED_FEATURES")
    preprocessing: dict[str, JSONValue] = {"scale": config.scale}
    if config.scale:
        scaler = StandardScaler()
        scaled = scaler.fit_transform(matrix)
        preprocessing["scaler_mean"] = scaler.mean_.tolist()
        preprocessing["scaler_std"] = scaler.scale_.tolist()
    else:
        scaled = matrix
    model = PCA(n_components=config.pca_components, random_state=config.seed)
    scores = model.fit_transform(scaled)
    return {
        "schema_version": "v1",
        "n_components": config.pca_components,
        "scores": scores.tolist(),
        "loadings": model.components_.tolist(),
        "explained_variance": model.explained_variance_ratio_.tolist(),
        "feature_columns": list(config.feature_columns),
        "preprocessing": preprocessing,
        "diagnostics": {"sample_count": int(matrix.shape[0])},
    }


__all__ = ("run_pca",)
