"""Stateless bounded unsupervised modeling workflow for Research."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from app.composition.logging import get_logger
from app.services.research.contracts import (
    ResearchWarning,
    UnsupervisedResearchResult,
)
from app.services.research.data.validation import _enforce_memory_budget
from app.services.research.modeling.clustering import cluster_feature_space
from app.services.research.modeling.insights import (
    build_unsupervised_insight_report,
)

logger = get_logger(__name__)

if TYPE_CHECKING:
    from pandas import DataFrame

    from app.services.research.contracts import (
        ResearchResourceLimits,
        UnsupervisedResearchConfig,
    )

type JSONValue = (
    None | bool | int | float | str | list["JSONValue"] | Mapping[str, "JSONValue"]
)


def run_unsupervised_research(
    features: DataFrame,
    *,
    config: UnsupervisedResearchConfig,
    limits: ResearchResourceLimits,
) -> UnsupervisedResearchResult:
    """Execute the stateless bounded modeling workflow.

    Args:
        features: Frame containing declared feature columns.
        config: Modeling configuration.
        limits: Approved resource ceilings.

    Returns:
        Complete advisory ``UnsupervisedResearchResult``.

    Raises:
        ValueError: If inputs, resources, or prerequisites are invalid.
    """
    logger.info("Running Research unsupervised workflow")
    if len(features) > limits.max_rows:
        raise ValueError("RES_RESOURCE_LIMIT_EXCEEDED", "ROW_LIMIT_EXCEEDED")
    # Scaling, PCA, clustering, and diagnostics coexist at the modeling peak.
    _enforce_memory_budget(features, limits, allocation_multiplier=6)
    if len(features) < config.minimum_samples:
        raise ValueError("RES_INSUFFICIENT_DATA", "INSUFFICIENT_MODELING_SAMPLES")
    clusters = cluster_feature_space(features, config=config)
    insights = build_unsupervised_insight_report(features, config=config)
    descriptive = insights.get("descriptive")
    pca = insights.get("pca")
    if not isinstance(descriptive, Mapping) or not isinstance(pca, Mapping):
        raise ValueError(  # noqa: TRY004 - Research validation taxonomy.
            "RES_INPUT_INVALID", "INVALID_INSIGHT_REPORT"
        )
    warnings: list[ResearchWarning] = []
    if not insights.get("pca"):
        warnings.append(
            ResearchWarning(
                "EMPTY_PCA",
                "PCA evidence is empty",
                "warning",
                "pca",
                {},
            )
        )
    return UnsupervisedResearchResult(
        "v1",
        descriptive,
        pca,
        clusters,
        insights,
        config.seed,
        tuple(warnings),
        True,
    )


__all__ = ("run_unsupervised_research",)
