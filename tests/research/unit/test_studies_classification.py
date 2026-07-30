"""Unit tests for Research symbol classification (FR-RES-068)."""

import pytest
from app.services.research import classify_symbol, create_research_value
from app.utils import get_logger

logger = get_logger(__name__)


def _edge(classification: str, study: str = "mean_reversion") -> object:
    """Build an advisory edge result for classification testing."""
    return create_research_value(
        "EdgeResult", "v1", study, {}, {}, classification, 7, (), True
    )


def test_classification_matches_report_policy() -> None:
    """FR-RES-068: classify a confirmed mean-reversion edge."""
    logger.debug("Testing Research mean-reversion classification")
    result = classify_symbol(
        _edge("confirmed", "mean_reversion"),
        _edge("inconclusive", "trend_persistence"),
        policy_version="v1",
    )
    assert result["classification"] == "mean_reversion"
    assert result["policy_version"] == "v1"
    assert result["advisory_only"] is True


def test_classification_reports_mixed_when_both_confirmed() -> None:
    """FR-RES-068: report mixed when both edges are confirmed."""
    logger.debug("Testing Research mixed classification")
    result = classify_symbol(
        _edge("confirmed"),
        _edge("confirmed", "trend_persistence"),
        policy_version="v1",
    )
    assert result["classification"] == "mixed"


def test_classification_is_inconclusive_without_confirmation() -> None:
    """FR-RES-068: report inconclusive when no edge is confirmed."""
    logger.debug("Testing Research inconclusive classification")
    result = classify_symbol(
        _edge("contradicted"),
        _edge("inconclusive", "trend_persistence"),
        policy_version="v1",
    )
    assert result["classification"] == "inconclusive"


def test_classification_rejects_unsupported_policy() -> None:
    """FR-RES-068: fail closed for an unsupported confirmation policy."""
    logger.debug("Testing Research classification policy rejection")
    with pytest.raises(ValueError, match="CONFIRMATION_POLICY_NOT_V1"):
        classify_symbol(
            _edge("confirmed"),
            _edge("inconclusive", "trend_persistence"),
            policy_version="v2",
        )
