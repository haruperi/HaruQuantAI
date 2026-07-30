"""Unit tests for immutable Research configuration contracts."""

from datetime import time
from pathlib import Path

import pytest
from app.services.research import (
    create_research_value,
)
from app.utils import get_logger

logger = get_logger(__name__)


def _limits() -> object:
    """Build valid test resource limits.

    Returns:
        Valid Research resource limits.
    """
    logger.debug("Building test Research limits")
    return create_research_value("ResearchResourceLimits", 500_000, 600.0, 52_428_800)


def _configs(root: Path) -> tuple[object, ...]:
    """Build the valid configuration graph.

    Args:
        root: Absolute artifact root.

    Returns:
        Ordered valid configurations.
    """
    logger.debug("Building valid Research test configurations")
    cleaning = create_research_value(
        "CleaningConfig", "UTC", "error", "none", "keep_warn", "error"
    )
    enrichment = create_research_value(
        "EnrichmentConfig", "EURUSD", True, True, False, True
    )
    features = create_research_value(
        "FeatureConfig", {"returns": 20}, (5,), (), "preserve"
    )
    statistics = create_research_value(
        "StatisticalConfig", 7, 100, 100, 5, 100, "benjamini_hochberg"
    )
    studies = create_research_value("StudyConfig", {}, {}, {})
    sessions = create_research_value(
        "SessionConfig", "UTC", {"london": (time(8), time(16))}, ("london",)
    )
    structure = create_research_value("MarketStructureConfig", {}, False, (20,), 4, 5)
    modeling = create_research_value(
        "UnsupervisedResearchConfig", ("a", "b"), True, 2, 2, 20, 7
    )
    artifacts = create_research_value("ArtifactWriteConfig", root, "json")
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
    with pytest.raises(ValueError, match=r"."):
        create_research_value("ResearchResourceLimits", 0, 1.0, 1)


def test_cleaning_requires_explicit_data_actions() -> None:
    """Verify cleaning strategies use the closed vocabulary."""
    logger.debug("Testing explicit Research cleaning actions")
    with pytest.raises(ValueError, match=r"."):
        create_research_value(
            "CleaningConfig", "UTC", "guess", "none", "keep_warn", "error"
        )


def test_enrichment_rejects_incompatible_fields() -> None:
    """Verify forward labels require returns."""
    logger.debug("Testing Research enrichment dependencies")
    with pytest.raises(ValueError, match=r"."):
        create_research_value("EnrichmentConfig", "EURUSD", True, False, True, True)


def test_feature_config_rejects_invalid_window() -> None:
    """Verify feature windows must exceed one row."""
    logger.debug("Testing Research feature window")
    with pytest.raises(ValueError, match=r"."):
        create_research_value("FeatureConfig", {"bad": 1}, (), (), "preserve")


def test_statistics_rejects_invalid_block_size() -> None:
    """Verify statistical blocks are positive and bounded."""
    logger.debug("Testing Research statistical block size")
    with pytest.raises(ValueError, match=r"."):
        create_research_value("StatisticalConfig", 1, 10, 10, 0, 10, None)


def test_study_config_fails_closed_by_default() -> None:
    """Verify isolated study failures default to fail-closed."""
    logger.debug("Testing Research study failure policy")
    assert (
        create_research_value("StudyConfig", {}, {}, {}).continue_on_study_error
        is False
    )


def test_session_config_requires_overlap_precedence() -> None:
    """Verify every session has one precedence entry."""
    logger.debug("Testing Research session precedence")
    with pytest.raises(ValueError, match=r"."):
        create_research_value(
            "SessionConfig", "UTC", {"london": (time(8), time(16))}, ()
        )


def test_market_structure_bounds_candidates() -> None:
    """Verify calibration candidates obey the hard bound."""
    logger.debug("Testing Research calibration bound")
    with pytest.raises(ValueError, match=r"."):
        create_research_value("MarketStructureConfig", {}, False, (), 129, 5)


def test_unsupervised_config_rejects_excess_clusters() -> None:
    """Verify K-Means cluster counts obey policy."""
    logger.debug("Testing Research cluster bound")
    with pytest.raises(ValueError, match=r"."):
        create_research_value("UnsupervisedResearchConfig", ("a",), True, 1, 65, 650, 1)


def test_artifact_config_rejects_relative_root() -> None:
    """Verify artifact roots are absolute."""
    logger.debug("Testing Research artifact root")
    with pytest.raises(ValueError, match=r"."):
        create_research_value("ArtifactWriteConfig", Path("relative"), "json")


def test_edge_lab_config_requires_stage_dependencies(tmp_path: Path) -> None:
    """Verify modeling requires feature and leakage stages.

    Args:
        tmp_path: Pytest temporary directory.
    """
    logger.debug("Testing Edge Lab stage dependencies")
    configs = _configs(tmp_path.resolve())
    with pytest.raises(ValueError, match=r"."):
        create_research_value("EdgeLabConfig", *configs, _limits(), ("modeling",))  # type: ignore[arg-type]
