"""Unit tests for Research snapshots and summaries (FR-RES-090 to 092)."""

import pytest
from app.services.research import (
    build_dashboard_summary,
    build_profile_summary,
    build_research_profile_snapshot,
    create_research_value,
    is_research_value,
)
from app.utils import get_logger

logger = get_logger(__name__)

_HASH = "e" * 64


def _scorecard() -> object:
    """Build a canonical advisory scorecard."""
    return create_research_value(
        "ResearchScorecard",
        "v1",
        ({"criterion": "metrics", "score": 20.0},),
        75.0,
        "REVIEW_READY",
        ("evidence_assembled",),
        (),
        True,
    )


def test_snapshot_rejects_unversioned_stage() -> None:
    """FR-RES-090: unversioned stages are rejected."""
    logger.debug("Testing Research snapshot validation")
    with pytest.raises(ValueError, match="UNVERSIONED_SNAPSHOT_STAGE"):
        build_research_profile_snapshot(
            stages={"data": {"rows": 10}},
            scorecard=_scorecard(),
            dataset_hash=_HASH,
            configuration_hash=_HASH,
        )


def test_snapshot_builds_versioned() -> None:
    """FR-RES-090: versioned stages build successfully."""
    snapshot = build_research_profile_snapshot(
        stages={"data": {"schema_version": "v1", "rows": 10}},
        scorecard=_scorecard(),
        dataset_hash=_HASH,
        configuration_hash=_HASH,
    )
    assert is_research_value(snapshot, "ResearchProfileSnapshot")
    assert snapshot.schema_version == "v1"


def test_profile_summary_preserves_warnings() -> None:
    """FR-RES-091: summary preserves warning count and readiness."""
    snapshot = build_research_profile_snapshot(
        stages={"data": {"schema_version": "v1"}},
        scorecard=_scorecard(),
        dataset_hash=_HASH,
        configuration_hash=_HASH,
    )
    summary = build_profile_summary(snapshot)
    assert summary["schema_version"] == "v1"
    assert summary["readiness"] == "REVIEW_READY"
    assert "warning_count" in summary


def test_dashboard_summary_is_bounded() -> None:
    """FR-RES-092: dashboard summary is bounded and UI-ready."""
    snapshot = build_research_profile_snapshot(
        stages={"data": {"schema_version": "v1"}},
        scorecard=_scorecard(),
        dataset_hash=_HASH,
        configuration_hash=_HASH,
    )
    dashboard = build_dashboard_summary(snapshot)
    assert "top_reasons" in dashboard
    assert len(dashboard["top_reasons"]) <= 5
