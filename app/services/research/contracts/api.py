"""Classifications for the implemented Research contract surface."""

from __future__ import annotations

from types import MappingProxyType
from typing import Literal

from app.utils import logger

logger.debug("Defining implemented Research contract API classifications")

PUBLIC_API_CLASSIFICATIONS: MappingProxyType[str, Literal["stable"]] = MappingProxyType(
    dict.fromkeys(
        (
            "ArtifactReference",
            "ArtifactWriteConfig",
            "CleaningConfig",
            "CoreMetricProfile",
            "DataQualityReport",
            "EdgeLabConfig",
            "EdgeResult",
            "EnrichmentConfig",
            "FeatureConfig",
            "LeakageReport",
            "MarketStructureConfig",
            "MarketStructureProfile",
            "MarketStructureQualityReport",
            "PreparedDataset",
            "ResearchProfileSnapshot",
            "ResearchReport",
            "ResearchResourceLimits",
            "ResearchScorecard",
            "ResearchWarning",
            "SessionConfig",
            "StatisticalConfig",
            "StudyConfig",
            "TimeSplitResult",
            "UnsupervisedResearchConfig",
            "UnsupervisedResearchResult",
        ),
        "stable",
    )
)

__all__ = ("PUBLIC_API_CLASSIFICATIONS",)
