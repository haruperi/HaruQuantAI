"""Descriptive, factor, cluster-outperformance, and insight reports for Research."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

from app.services.research.features import forward_returns
from app.services.research.modeling.clustering import cluster_feature_space
from app.services.research.modeling.decomposition import run_pca
from app.utils import ValidationError, logger

if TYPE_CHECKING:
    from collections.abc import Mapping

    from app.services.research.contracts import UnsupervisedResearchConfig

type JSONValue = (
    None | bool | int | float | str | list["JSONValue"] | Mapping[str, "JSONValue"]
)


def summarize_investment_data(
    data: pd.DataFrame,
) -> Mapping[str, JSONValue]:
    """Return descriptive finite-value, missingness, and duplicate evidence.

    Args:
        data: Numeric investment frame.

    Returns:
        Versioned descriptive summary.

    Raises:
        ValidationError: If the frame is empty.
    """
    logger.debug("Summarizing Research investment data")
    if data.empty:
        raise ValidationError("RES_INPUT_INVALID", "EMPTY_INVESTMENT_DATA")
    numeric = data.select_dtypes(include=[np.number])
    return {
        "schema_version": "v1",
        "row_count": len(data),
        "column_count": int(data.shape[1]),
        "numeric_column_count": int(numeric.shape[1]),
        "missing_values": {col: int(data[col].isna().sum()) for col in data.columns},
        "duplicate_rows": int(data.duplicated().sum()),
        "describe": {
            col: {
                "mean": float(numeric[col].mean()) if col in numeric.columns else None,
                "std": float(numeric[col].std(ddof=0))
                if col in numeric.columns
                else None,
                "min": float(numeric[col].min()) if col in numeric.columns else None,
                "max": float(numeric[col].max()) if col in numeric.columns else None,
            }
            for col in data.columns
        },
    }


def identify_pca_risk_factors(
    pca: Mapping[str, JSONValue],
    *,
    top_count: int,
) -> tuple[Mapping[str, JSONValue], ...]:
    """Extract the largest absolute PCA loadings as interpretable factors.

    Args:
        pca: PCA evidence from ``run_pca``.
        top_count: Positive number of factors to extract per component.

    Returns:
        Tuple of factor mappings with component, feature, sign, and magnitude.

    Raises:
        ValidationError: If PCA evidence is malformed or count is invalid.
    """
    logger.debug("Identifying Research PCA risk factors")
    if not isinstance(top_count, int) or top_count <= 0:
        raise ValidationError("RES_INPUT_INVALID", "INVALID_TOP_COUNT")
    loadings = pca.get("loadings")
    feature_columns = pca.get("feature_columns")
    if not isinstance(loadings, list) or not isinstance(feature_columns, list):
        raise ValidationError("RES_INPUT_INVALID", "MALFORMED_PCA_EVIDENCE")
    factors: list[Mapping[str, JSONValue]] = []
    for component_index, component in enumerate(loadings):
        if not isinstance(component, list):
            continue
        ranked = sorted(
            enumerate(component),
            key=lambda item: abs(item[1]) if isinstance(item[1], int | float) else 0,
            reverse=True,
        )[:top_count]
        for feature_index, magnitude in ranked:
            if not isinstance(magnitude, int | float):
                continue
            factors.append(
                {
                    "component": component_index,
                    "feature": feature_columns[feature_index],
                    "sign": "positive" if magnitude >= 0 else "negative",
                    "magnitude": abs(float(magnitude)),
                }
            )
    return tuple(factors)


def analyze_cluster_outperformance(
    data: pd.DataFrame,
    labels: pd.Series,
    *,
    horizon: int,
) -> tuple[Mapping[str, JSONValue], ...]:
    """Compare clusters using canonical forward returns and sample counts.

    Args:
        data: Frame with a close column.
        labels: Cluster labels aligned to the data index.
        horizon: Forward-return horizon for outperformance comparison.

    Returns:
        Tuple of per-cluster evidence with mean return, sample, and uncertainty.

    Raises:
        ValidationError: If data or labels are invalid/misaligned.
    """
    logger.debug("Analyzing Research cluster outperformance")
    if "close" not in data.columns:
        raise ValidationError("RES_INPUT_INVALID", "CLOSE_COLUMN_REQUIRED")
    if len(labels) != len(data):
        raise ValidationError("RES_INPUT_INVALID", "MISALIGNED_LABELS")
    if horizon <= 0:
        raise ValidationError("RES_INPUT_INVALID", "INVALID_HORIZON")
    close = data["close"].astype("float64")
    returns = forward_returns(close, horizon=horizon, mode="log", output_label="cf")
    results: list[Mapping[str, JSONValue]] = []
    for cluster_id in sorted(set(labels.dropna().to_numpy())):
        mask = labels == cluster_id
        values = returns[mask].dropna()
        if values.empty:
            results.append(
                {"cluster": int(cluster_id), "sample_count": 0, "advisory": "sparse"}
            )
            continue
        values_arr = values.to_numpy(dtype="float64")
        results.append(
            {
                "cluster": int(cluster_id),
                "sample_count": int(values.size),
                "mean_forward_return": float(values_arr.mean()),
                "std_forward_return": float(values_arr.std(ddof=0)),
                "win_rate": float(np.mean(values_arr > 0)),
                "advisory_only": True,
            }
        )
    return tuple(results)


def build_unsupervised_insight_report(
    features: pd.DataFrame,
    *,
    config: UnsupervisedResearchConfig,
) -> Mapping[str, JSONValue]:
    """Combine descriptive, PCA, cluster, and factor evidence.

    Signal-adaptation behavior is excluded by design.

    Args:
        features: Frame containing declared feature columns.
        config: Modeling configuration.

    Returns:
        Versioned insight report with no signal-control fields.

    Raises:
        ValidationError: If features or configuration are invalid.
    """
    logger.info("Building Research unsupervised insight report")
    descriptive = summarize_investment_data(features)
    pca = run_pca(features, config=config)
    clusters = cluster_feature_space(features, config=config)
    factors = identify_pca_risk_factors(pca, top_count=3)
    return {
        "schema_version": "v1",
        "descriptive": descriptive,
        "pca": pca,
        "clusters": clusters,
        "factors": [dict(f) for f in factors],
        "signal_adaptation": "excluded",
        "advisory_only": True,
    }


__all__ = (
    "analyze_cluster_outperformance",
    "build_unsupervised_insight_report",
    "identify_pca_risk_factors",
    "summarize_investment_data",
)
