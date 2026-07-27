"""Unit tests for Research advisory strategy fit (FR-RES-080)."""

from app.services.research import MarketStructureProfile
from app.services.research.market_structure import build_strategy_fit
from app.utils import logger


def _profile(verdict: str = "trending", score: float = 75.0) -> MarketStructureProfile:
    """Build a canonical market-structure profile for fit testing."""
    return MarketStructureProfile(
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
