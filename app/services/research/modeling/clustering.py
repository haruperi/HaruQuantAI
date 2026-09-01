"""Deterministic K-Means clustering evidence for Research."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from app.composition.logging import get_logger
from app.services.research.modeling.decomposition import _select_finite_features

logger = get_logger(__name__)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from app.services.research.contracts import UnsupervisedResearchConfig

type JSONValue = (
    None | bool | int | float | str | list["JSONValue"] | Mapping[str, "JSONValue"]
)


def cluster_feature_space(
    features: pd.DataFrame,
    *,
    config: UnsupervisedResearchConfig,
) -> Mapping[str, JSONValue]:
    """Cluster finite feature rows with deterministic seeded K-Means.

    Args:
        features: Frame containing declared feature columns.
        config: Modeling configuration with cluster count and seed.

    Returns:
        Versioned cluster evidence with labels, centers, and diagnostics.

    Raises:
        ValueError: If features or configuration are invalid.
    """
    logger.info("Running Research K-Means clustering")
    _selected, matrix = _select_finite_features(features, config)
    if config.scale:
        scaler = StandardScaler()
        scaled = scaler.fit_transform(matrix)
    else:
        scaled = matrix
    model = KMeans(
        n_clusters=config.clusters,
        random_state=config.seed,
        n_init=10,
    )
    labels = model.fit_predict(scaled)
    return {
        "schema_version": "v1",
        "n_clusters": config.clusters,
        "labels": labels.astype(int).tolist(),
        "centers": model.cluster_centers_.tolist(),
        "scale": config.scale,
        "diagnostics": {
            "sample_count": int(matrix.shape[0]),
            "inertia": float(model.inertia_),
        },
    }


def attach_cluster_labels(
    features: pd.DataFrame,
    labels: pd.Series,
    *,
    column: str = "cluster",
) -> pd.DataFrame:
    """Attach aligned labels to a copied frame without mutation.

    Args:
        features: Original feature frame.
        labels: Cluster labels aligned to the frame index.
        column: Output column name for the labels.

    Returns:
        A copied frame carrying the attached label column.

    Raises:
        ValueError: If labels are misaligned or the column exists.
    """
    logger.debug("Attaching Research cluster labels")
    if column in features.columns:
        raise ValueError("RES_INPUT_INVALID", "DUPLICATE_CLUSTER_COLUMN")
    if len(labels) != len(features):
        raise ValueError("RES_INPUT_INVALID", "MISALIGNED_CLUSTER_LABELS")
    result = features.copy()
    result[column] = labels.to_numpy()
    return result


__all__ = ("attach_cluster_labels", "cluster_feature_space")
