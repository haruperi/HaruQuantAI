"""Typed UI/API request boundary models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, field_serializer, field_validator

from app.services.research import EdgeLabConfig  # noqa: TC001 - Pydantic runtime model
from app.utils import get_logger

MarketDataset = Any

logger = get_logger(__name__)


class ResearchRunRequest(BaseModel):
    """Bounded authenticated request for one advisory Research run."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    hypothesis: str
    dataset: MarketDataset
    config: EdgeLabConfig

    @field_validator("hypothesis")
    @classmethod
    def _validate_hypothesis(cls, value: str) -> str:
        """Validate explicit researcher-supplied hypothesis text.

        Args:
            value: Candidate hypothesis.

        Returns:
            Validated hypothesis.

        Raises:
            ValueError: If the hypothesis is blank or padded.
        """
        logger.debug("Validating API Research hypothesis")
        if not value or value != value.strip():
            raise ValueError("hypothesis must be non-empty and trimmed")
        return value

    @field_serializer("config", when_used="json")
    def _serialize_config(self, value: EdgeLabConfig) -> dict[str, object]:
        """Serialize frozen Research configuration for HTTP transport.

        Args:
            value: Validated Research-owned configuration.

        Returns:
            JSON-compatible configuration mapping.
        """
        return {
            "cleaning": {
                "timezone": value.cleaning.timezone,
                "duplicate_strategy": value.cleaning.duplicate_strategy,
                "missing_bar_strategy": value.cleaning.missing_bar_strategy,
                "non_trading_period_strategy": (
                    value.cleaning.non_trading_period_strategy
                ),
                "spread_strategy": value.cleaning.spread_strategy,
            },
            "enrichment": {
                "symbol": value.enrichment.symbol,
                "include_geometry": value.enrichment.include_geometry,
                "include_returns": value.enrichment.include_returns,
                "include_forward_labels": value.enrichment.include_forward_labels,
                "include_calendar": value.enrichment.include_calendar,
            },
            "features": {
                "windows": dict(value.features.windows),
                "forward_horizons": value.features.forward_horizons,
                "allowed_forward_columns": value.features.allowed_forward_columns,
                "nan_policy": value.features.nan_policy,
            },
            "statistics": {
                "seed": value.statistics.seed,
                "bootstrap_samples": value.statistics.bootstrap_samples,
                "permutation_samples": value.statistics.permutation_samples,
                "block_size": value.statistics.block_size,
                "null_samples": value.statistics.null_samples,
                "correction": value.statistics.correction,
            },
            "studies": {
                "mean_reversion": dict(value.studies.mean_reversion),
                "trend_persistence": dict(value.studies.trend_persistence),
                "session": dict(value.studies.session),
                "continue_on_study_error": value.studies.continue_on_study_error,
            },
            "sessions": {
                "timezone": value.sessions.timezone,
                "windows": {
                    name: (window[0].isoformat(), window[1].isoformat())
                    for name, window in value.sessions.windows.items()
                },
                "overlap_precedence": value.sessions.overlap_precedence,
            },
            "market_structure": {
                "profile": dict(value.market_structure.profile),
                "enable_quality": value.market_structure.enable_quality,
                "quality_windows": value.market_structure.quality_windows,
                "calibration_candidates": (
                    value.market_structure.calibration_candidates
                ),
                "validation_horizon": value.market_structure.validation_horizon,
            },
            "modeling": {
                "feature_columns": value.modeling.feature_columns,
                "scale": value.modeling.scale,
                "pca_components": value.modeling.pca_components,
                "clusters": value.modeling.clusters,
                "minimum_samples": value.modeling.minimum_samples,
                "seed": value.modeling.seed,
            },
            "artifacts": {
                "allowed_root": str(value.artifacts.allowed_root),
                "format": value.artifacts.format,
                "overwrite": value.artifacts.overwrite,
                "encoding": value.artifacts.encoding,
                "require_atomic": value.artifacts.require_atomic,
            },
            "limits": {
                "max_rows": value.limits.max_rows,
                "max_duration_seconds": value.limits.max_duration_seconds,
                "max_artifact_bytes": value.limits.max_artifact_bytes,
                "memory_budget_mb": value.limits.memory_budget_mb,
            },
            "selected_stages": value.selected_stages,
        }


__all__ = ("ResearchRunRequest",)
