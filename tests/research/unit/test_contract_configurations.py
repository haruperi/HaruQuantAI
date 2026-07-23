"""Unit tests for immutable Research configuration contracts."""

from datetime import time
from pathlib import Path

import pytest
from app.services.research.contracts import (
    ArtifactWriteConfig,
    CleaningConfig,
    EdgeLabConfig,
    EnrichmentConfig,
    FeatureConfig,
    MarketStructureConfig,
    ResearchResourceLimits,
    SessionConfig,
    StatisticalConfig,
    StudyConfig,
    UnsupervisedResearchConfig,
)
from app.utils import ConfigurationError, logger


def _limits() -> ResearchResourceLimits:
    """Build valid test resource limits.

    Returns:
        Valid Research resource limits.
    """
    logger.debug("Building test Research limits")
    return ResearchResourceLimits(500_000, 600.0, 52_428_800)


def _configs(root: Path) -> tuple[object, ...]:
    """Build the valid configuration graph.

    Args:
        root: Absolute artifact root.

    Returns:
        Ordered valid configurations.
    """
    logger.debug("Building valid Research test configurations")
    cleaning = CleaningConfig("UTC", "error", "none", "keep_warn", "error")
    enrichment = EnrichmentConfig("EURUSD", True, True, False, True)
    features = FeatureConfig({"returns": 20}, (5,), (), "preserve")
    statistics = StatisticalConfig(7, 100, 100, 5, 100, "benjamini_hochberg")
    studies = StudyConfig({}, {}, {})
    sessions = SessionConfig("UTC", {"london": (time(8), time(16))}, ("london",))
    structure = MarketStructureConfig({}, False, (20,), 4, 5)
    modeling = UnsupervisedResearchConfig(("a", "b"), True, 2, 2, 20, 7)
    artifacts = ArtifactWriteConfig(root, "json")
    return (
        cleaning,
        enrichment,
        features,
        statistics,
        studies,
        sessions,
        structure,
        modeling,
        artifacts,
    )


def test_resource_limits_reject_non_positive() -> None:
    """Verify resource limits reject non-positive values."""
    logger.debug("Testing invalid Research resource limits")
    with pytest.raises(ConfigurationError):
        ResearchResourceLimits(0, 1.0, 1)


def test_cleaning_requires_explicit_data_actions() -> None:
    """Verify cleaning strategies use the closed vocabulary."""
    logger.debug("Testing explicit Research cleaning actions")
    with pytest.raises(ConfigurationError):
        CleaningConfig("UTC", "guess", "none", "keep_warn", "error")


def test_enrichment_rejects_incompatible_fields() -> None:
    """Verify forward labels require returns."""
    logger.debug("Testing Research enrichment dependencies")
    with pytest.raises(ConfigurationError):
        EnrichmentConfig("EURUSD", True, False, True, True)


def test_feature_config_rejects_invalid_window() -> None:
    """Verify feature windows must exceed one row."""
    logger.debug("Testing Research feature window")
    with pytest.raises(ConfigurationError):
        FeatureConfig({"bad": 1}, (), (), "preserve")


def test_statistics_rejects_invalid_block_size() -> None:
    """Verify statistical blocks are positive and bounded."""
    logger.debug("Testing Research statistical block size")
    with pytest.raises(ConfigurationError):
        StatisticalConfig(1, 10, 10, 0, 10, None)


def test_study_config_fails_closed_by_default() -> None:
    """Verify isolated study failures default to fail-closed."""
    logger.debug("Testing Research study failure policy")
    assert StudyConfig({}, {}, {}).continue_on_study_error is False


def test_session_config_requires_overlap_precedence() -> None:
    """Verify every session has one precedence entry."""
    logger.debug("Testing Research session precedence")
    with pytest.raises(ConfigurationError):
        SessionConfig("UTC", {"london": (time(8), time(16))}, ())


def test_market_structure_bounds_candidates() -> None:
    """Verify calibration candidates obey the hard bound."""
    logger.debug("Testing Research calibration bound")
    with pytest.raises(ConfigurationError):
        MarketStructureConfig({}, False, (), 129, 5)


def test_unsupervised_config_rejects_excess_clusters() -> None:
    """Verify K-Means cluster counts obey policy."""
    logger.debug("Testing Research cluster bound")
    with pytest.raises(ConfigurationError):
        UnsupervisedResearchConfig(("a",), True, 1, 65, 650, 1)


def test_artifact_config_rejects_relative_root() -> None:
    """Verify artifact roots are absolute."""
    logger.debug("Testing Research artifact root")
    with pytest.raises(ConfigurationError):
        ArtifactWriteConfig(Path("relative"), "json")


def test_edge_lab_config_requires_stage_dependencies(tmp_path: Path) -> None:
    """Verify modeling requires feature and leakage stages.

    Args:
        tmp_path: Pytest temporary directory.
    """
    logger.debug("Testing Edge Lab stage dependencies")
    configs = _configs(tmp_path.resolve())
    with pytest.raises(ConfigurationError):
        EdgeLabConfig(*configs, _limits(), ("modeling",))  # type: ignore[arg-type]
