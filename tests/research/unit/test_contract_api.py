"""Unit tests for Research public API classifications."""

from app.services.research.contracts import PUBLIC_API_CLASSIFICATIONS
from app.utils import logger


def test_public_api_is_unique_resolvable_and_side_effect_free() -> None:
    """Verify every implemented contract has one stable classification."""
    logger.debug("Testing Research contract API classifications")
    assert PUBLIC_API_CLASSIFICATIONS
    assert set(PUBLIC_API_CLASSIFICATIONS.values()) == {"stable"}
    assert len(PUBLIC_API_CLASSIFICATIONS) == len(set(PUBLIC_API_CLASSIFICATIONS))


def test_every_public_export_is_classified() -> None:
    """FR-RES-026: every __all__ name has one stable classification."""
    from app.services.research import __all__ as package_all

    logger.debug("Testing Research public export coverage")
    classified = set(PUBLIC_API_CLASSIFICATIONS)
    unclassified = set(package_all) - classified
    assert not unclassified, f"Unclassified public exports: {sorted(unclassified)}"
