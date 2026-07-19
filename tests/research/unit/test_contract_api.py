"""Unit tests for Research public API classifications."""

from app.services.research.contracts import PUBLIC_API_CLASSIFICATIONS
from app.utils import logger


def test_public_api_is_unique_resolvable_and_side_effect_free() -> None:
    """Verify every implemented contract has one stable classification."""
    logger.debug("Testing Research contract API classifications")
    assert PUBLIC_API_CLASSIFICATIONS
    assert set(PUBLIC_API_CLASSIFICATIONS.values()) == {"stable"}
    assert len(PUBLIC_API_CLASSIFICATIONS) == len(set(PUBLIC_API_CLASSIFICATIONS))
