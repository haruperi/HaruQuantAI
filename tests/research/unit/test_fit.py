"""Unit tests for Research advisory strategy fit (FR-RES-080)."""

import pytest
from app.services.research import build_strategy_fit, create_research_value
from app.utils import get_logger

logger = get_logger(__name__)


def _profile(verdict: str = "trending", score: float = 75.0) -> object:
    """Build a canonical market-structure profile for fit testing."""
    return create_research_value(
        "MarketStructureProfile",
        "v1",
        {"swing_window": 5},
        score,
        verdict,
        {"primary_archetype": "trend_follow", "advisory_only": True},
        (),
    )


def test_strategy_fit_is_advisory_only() -> None:
    """FR-RES-080: strategy fit is advisory-only and never approves."""
    logger.debug("Testing Research advisory strategy fit")
    result = build_strategy_fit(_profile())
    assert result["advisory_only"] is True
    assert result["primary_archetype"] == "trend_follow"
    assert "archetype_ranking" in result


@pytest.mark.parametrize(
    ("verdict", "expected"),
    [("ranging", "mean_revert"), ("mixed", "range")],
)
def test_strategy_fit_ranks_other_regimes(verdict: str, expected: str) -> None:
    """Cover the remaining advisory regime rankings."""
    assert (
        build_strategy_fit(_profile(verdict=verdict))["primary_archetype"] == expected
    )
