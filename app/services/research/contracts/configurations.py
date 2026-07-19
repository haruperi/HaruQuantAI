"""Immutable configuration contracts for the Research domain."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import time
from pathlib import Path
from types import MappingProxyType
from typing import Literal

from app.utils import logger
from app.utils.errors import ConfigurationError

type JSONValue = (
    None | bool | int | float | str | list["JSONValue"] | Mapping[str, "JSONValue"]
)

_MAX_ROWS = 500_000
_MAX_DURATION_SECONDS = 600.0
_MAX_ARTIFACT_BYTES = 52_428_800
_MAX_ITERATIONS = 10_000
_MAX_WINDOW = 10_000
_MAX_QUALITY_WINDOWS = 32
_MAX_CALIBRATION_CANDIDATES = 128
_MIN_CLUSTERS = 2
_MAX_CLUSTERS = 64
_KNOWN_STAGES = frozenset(
    {
        "data",
        "features",
        "leakage",
        "metrics",
        "statistics",
        "studies",
        "seasonality",
        "market_structure",
        "modeling",
        "profiles",
    }
)


def _raise_configuration(detail: str) -> None:
    """Raise one redacted Research configuration failure.

    Args:
        detail: Uppercase symbolic failure detail.

    Raises:
        ConfigurationError: Always.
    """
    logger.error("Rejecting Research configuration: %s", detail)
    raise ConfigurationError("RES_CONFIGURATION_INVALID", detail)


def _text(value: str, detail: str) -> str:
    """Validate one non-empty trimmed configuration string.

    Args:
        value: Candidate string.
        detail: Symbolic error detail.

    Returns:
        The validated string.
    """
    logger.debug("Validating Research configuration text")
    if not value or value != value.strip():
        _raise_configuration(detail)
    return value


def _freeze_mapping(value: Mapping[str, JSONValue]) -> Mapping[str, JSONValue]:
    """Copy and freeze one configuration mapping.

    Args:
        value: Mapping to freeze.

    Returns:
        An immutable shallow copy.
    """
    logger.debug("Freezing Research configuration mapping")
    return MappingProxyType(dict(value))


@dataclass(frozen=True, slots=True)
class ResearchResourceLimits:
    """Hard resource ceilings shared by Research operations."""

    max_rows: int
    max_duration_seconds: float
    max_artifact_bytes: int
    memory_budget_mb: int | None = None

    def __post_init__(self) -> None:
        """Validate approved resource ceilings.

        Raises:
            ConfigurationError: If a limit is invalid or exceeds policy.
        """
        logger.debug("Validating Research resource limits")
        if not 0 < self.max_rows <= _MAX_ROWS:
            _raise_configuration("INVALID_ROW_LIMIT")
        if not 0.0 < self.max_duration_seconds <= _MAX_DURATION_SECONDS:
            _raise_configuration("INVALID_DURATION_LIMIT")
        if not 0 < self.max_artifact_bytes <= _MAX_ARTIFACT_BYTES:
            _raise_configuration("INVALID_ARTIFACT_LIMIT")
        if self.memory_budget_mb is not None and self.memory_budget_mb <= 0:
            _raise_configuration("INVALID_MEMORY_LIMIT")


@dataclass(frozen=True, slots=True)
class CleaningConfig:
    """Explicit dataset-cleaning policies with no implicit actions."""

    timezone: str
    duplicate_strategy: str
    missing_bar_strategy: str
    non_trading_period_strategy: str
    spread_strategy: str

    def __post_init__(self) -> None:
        """Validate cleaning policy vocabulary.

        Raises:
            ConfigurationError: If any policy is unsupported.
        """
        logger.debug("Validating Research cleaning configuration")
        _text(self.timezone, "INVALID_TIMEZONE")
        policies = {
            "duplicate_strategy": (
                self.duplicate_strategy,
                {"error", "keep_first", "keep_last", "drop"},
            ),
            "missing_bar_strategy": (self.missing_bar_strategy, {"none", "drop"}),
            "non_trading_period_strategy": (
                self.non_trading_period_strategy,
                {"keep_warn", "drop"},
            ),
            "spread_strategy": (
                self.spread_strategy,
                {"error", "keep_warn", "drop_invalid"},
            ),
        }
        if any(value not in allowed for value, allowed in policies.values()):
            _raise_configuration("UNSUPPORTED_CLEANING_POLICY")


@dataclass(frozen=True, slots=True)
class EnrichmentConfig:
    """Explicit Research dataset-enrichment selections."""

    symbol: str
    include_geometry: bool
    include_returns: bool
    include_forward_labels: bool
    include_calendar: bool

    def __post_init__(self) -> None:
        """Validate enrichment selections.

        Raises:
            ConfigurationError: If selections are incompatible.
        """
        logger.debug("Validating Research enrichment configuration")
        _text(self.symbol, "INVALID_SYMBOL")
        if self.include_forward_labels and not self.include_returns:
            _raise_configuration("FORWARD_LABELS_REQUIRE_RETURNS")


@dataclass(frozen=True, slots=True)
class FeatureConfig:
    """Research feature windows and forward-field policy."""

    windows: Mapping[str, int]
    forward_horizons: tuple[int, ...]
    allowed_forward_columns: tuple[str, ...]
    nan_policy: str

    def __post_init__(self) -> None:
        """Validate and freeze feature configuration.

        Raises:
            ConfigurationError: If a feature setting is invalid.
        """
        logger.debug("Validating Research feature configuration")
        if not self.windows or any(
            not key or not 1 < value <= _MAX_WINDOW
            for key, value in self.windows.items()
        ):
            _raise_configuration("INVALID_FEATURE_WINDOW")
        if any(not 0 < horizon <= _MAX_WINDOW for horizon in self.forward_horizons):
            _raise_configuration("INVALID_FORWARD_HORIZON")
        if len(set(self.forward_horizons)) != len(self.forward_horizons):
            _raise_configuration("DUPLICATE_FORWARD_HORIZON")
        if self.nan_policy not in {"preserve", "drop_warmup"}:
            _raise_configuration("INVALID_NAN_POLICY")
        object.__setattr__(self, "windows", _freeze_mapping(self.windows))
        if any(not column for column in self.allowed_forward_columns):
            _raise_configuration("INVALID_FORWARD_COLUMN")


@dataclass(frozen=True, slots=True)
class StatisticalConfig:
    """Seeded and bounded statistical settings."""

    seed: int
    bootstrap_samples: int
    permutation_samples: int
    block_size: int
    null_samples: int
    correction: str | None

    def __post_init__(self) -> None:
        """Validate statistical settings.

        Raises:
            ConfigurationError: If an iteration, block, or correction is invalid.
        """
        logger.debug("Validating Research statistical configuration")
        if self.seed < 0:
            _raise_configuration("INVALID_SEED")
        counts = (self.bootstrap_samples, self.permutation_samples, self.null_samples)
        if any(not 0 < count <= _MAX_ITERATIONS for count in counts):
            _raise_configuration("INVALID_ITERATION_COUNT")
        if not 0 < self.block_size <= _MAX_ITERATIONS:
            _raise_configuration("INVALID_BLOCK_SIZE")
        if self.correction not in {None, "benjamini_hochberg"}:
            _raise_configuration("INVALID_CORRECTION")


@dataclass(frozen=True, slots=True)
class StudyConfig:
    """Closed configurations for the three approved edge-study families."""

    mean_reversion: Mapping[str, JSONValue]
    trend_persistence: Mapping[str, JSONValue]
    session: Mapping[str, JSONValue]
    continue_on_study_error: bool = False

    def __post_init__(self) -> None:
        """Validate and freeze study mappings.

        Raises:
            ConfigurationError: If a mapping contains an unknown key.
        """
        logger.debug("Validating Research study configuration")
        allowed = (
            {
                "lookback",
                "entry_zscore",
                "hold_bars",
                "side",
                "minimum_samples",
                "q",
                "null_quantile",
            },
            {
                "lookback",
                "minimum_move",
                "hold_bars",
                "side",
                "minimum_samples",
                "q",
                "null_quantile",
            },
            {"horizon", "minimum_samples", "q", "null_quantile"},
        )
        values = (self.mean_reversion, self.trend_persistence, self.session)
        if any(
            set(mapping) - keys for mapping, keys in zip(values, allowed, strict=True)
        ):
            _raise_configuration("UNSUPPORTED_STUDY_SETTING")
        for field_name, mapping in zip(
            ("mean_reversion", "trend_persistence", "session"), values, strict=True
        ):
            object.__setattr__(self, field_name, _freeze_mapping(mapping))


@dataclass(frozen=True, slots=True)
class SessionConfig:
    """Timezone-aware named session windows and overlap precedence."""

    timezone: str
    windows: Mapping[str, tuple[time, time]]
    overlap_precedence: tuple[str, ...]

    def __post_init__(self) -> None:
        """Validate and freeze the session policy.

        Raises:
            ConfigurationError: If names, windows, or precedence are invalid.
        """
        logger.debug("Validating Research session configuration")
        _text(self.timezone, "INVALID_TIMEZONE")
        if not self.windows or any(
            not name or start == end for name, (start, end) in self.windows.items()
        ):
            _raise_configuration("INVALID_SESSION_WINDOW")
        if set(self.overlap_precedence) != set(self.windows) or len(
            set(self.overlap_precedence)
        ) != len(self.windows):
            _raise_configuration("INVALID_SESSION_PRECEDENCE")
        object.__setattr__(self, "windows", MappingProxyType(dict(self.windows)))


@dataclass(frozen=True, slots=True)
class MarketStructureConfig:
    """Bounded market-structure, validation, and calibration settings."""

    profile: Mapping[str, JSONValue]
    enable_quality: bool
    quality_windows: tuple[int, ...]
    calibration_candidates: int
    validation_horizon: int

    def __post_init__(self) -> None:
        """Validate and freeze market-structure settings.

        Raises:
            ConfigurationError: If a bound or profile policy is invalid.
        """
        logger.debug("Validating Research market-structure configuration")
        allowed = {
            "efficiency_window",
            "swing_window",
            "atr_period",
            "reversal_atr_multiple",
            "trend_threshold",
            "range_threshold",
            "validation_atr_multiple",
            "calibration_grid",
        }
        if set(self.profile) - allowed:
            _raise_configuration("UNSUPPORTED_STRUCTURE_SETTING")
        if any(not 1 < window <= _MAX_WINDOW for window in self.quality_windows):
            _raise_configuration("INVALID_QUALITY_WINDOW")
        if len(set(self.quality_windows)) > _MAX_QUALITY_WINDOWS:
            _raise_configuration("TOO_MANY_QUALITY_WINDOWS")
        if not 0 < self.calibration_candidates <= _MAX_CALIBRATION_CANDIDATES:
            _raise_configuration("INVALID_CALIBRATION_COUNT")
        if not 0 < self.validation_horizon <= _MAX_WINDOW:
            _raise_configuration("INVALID_VALIDATION_HORIZON")
        object.__setattr__(self, "profile", _freeze_mapping(self.profile))


@dataclass(frozen=True, slots=True)
class UnsupervisedResearchConfig:
    """Deterministic PCA and K-Means configuration."""

    feature_columns: tuple[str, ...]
    scale: bool
    pca_components: int
    clusters: int
    minimum_samples: int
    seed: int

    def __post_init__(self) -> None:
        """Validate modeling dimensions and sample policy.

        Raises:
            ConfigurationError: If dimensions, samples, or seed are invalid.
        """
        logger.debug("Validating Research modeling configuration")
        if not self.feature_columns or len(set(self.feature_columns)) != len(
            self.feature_columns
        ):
            _raise_configuration("INVALID_FEATURE_COLUMNS")
        if not 0 < self.pca_components <= len(self.feature_columns):
            _raise_configuration("INVALID_PCA_COMPONENTS")
        if not _MIN_CLUSTERS <= self.clusters <= _MAX_CLUSTERS:
            _raise_configuration("INVALID_CLUSTER_COUNT")
        required = max(20, 10 * self.clusters, 2 * self.pca_components)
        if self.minimum_samples < required:
            _raise_configuration("INSUFFICIENT_MODELING_MINIMUM")
        if self.seed < 0:
            _raise_configuration("INVALID_SEED")


@dataclass(frozen=True, slots=True)
class ArtifactWriteConfig:
    """Safe Research artifact write policy."""

    allowed_root: Path
    format: Literal["json", "markdown"]
    overwrite: bool = False
    encoding: str = "utf-8"
    require_atomic: bool = True

    def __post_init__(self) -> None:
        """Validate artifact root and serialization policy.

        Raises:
            ConfigurationError: If the artifact policy is invalid.
        """
        logger.debug("Validating Research artifact configuration")
        if not self.allowed_root.is_absolute():
            _raise_configuration("ARTIFACT_ROOT_NOT_ABSOLUTE")
        if self.encoding.lower() != "utf-8":
            _raise_configuration("UNSUPPORTED_ARTIFACT_ENCODING")


@dataclass(frozen=True, slots=True)
class EdgeLabConfig:
    """Complete explicit configuration for the advisory Edge Lab workflow."""

    cleaning: CleaningConfig
    enrichment: EnrichmentConfig
    features: FeatureConfig
    statistics: StatisticalConfig
    studies: StudyConfig
    sessions: SessionConfig
    market_structure: MarketStructureConfig
    modeling: UnsupervisedResearchConfig
    artifacts: ArtifactWriteConfig
    limits: ResearchResourceLimits
    selected_stages: tuple[str, ...]

    def __post_init__(self) -> None:
        """Validate selected stages and their dependencies.

        Raises:
            ConfigurationError: If a stage is unknown, duplicated, or incompatible.
        """
        logger.debug("Validating complete Edge Lab configuration")
        if not self.selected_stages or len(set(self.selected_stages)) != len(
            self.selected_stages
        ):
            _raise_configuration("INVALID_SELECTED_STAGES")
        if set(self.selected_stages) - _KNOWN_STAGES:
            _raise_configuration("UNKNOWN_SELECTED_STAGE")
        selected = set(self.selected_stages)
        if "modeling" in selected and not {"features", "leakage"} <= selected:
            raise ConfigurationError(
                "RES_STAGE_DEPENDENCY_INVALID", "MODELING_REQUIRES_SAFE_FEATURES"
            )
        if "profiles" in selected and "metrics" not in selected:
            raise ConfigurationError(
                "RES_STAGE_DEPENDENCY_INVALID", "PROFILES_REQUIRE_METRICS"
            )


__all__ = (
    "ArtifactWriteConfig",
    "CleaningConfig",
    "EdgeLabConfig",
    "EnrichmentConfig",
    "FeatureConfig",
    "MarketStructureConfig",
    "ResearchResourceLimits",
    "SessionConfig",
    "StatisticalConfig",
    "StudyConfig",
    "UnsupervisedResearchConfig",
)
