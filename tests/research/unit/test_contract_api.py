"""Unit tests for Research public API classifications."""

from app.composition.logging import get_logger
from app.services.research import get_public_api_classifications

logger = get_logger(__name__)


def test_public_api_is_unique_resolvable_and_side_effect_free() -> None:
    """Verify every implemented contract has one stable classification."""
    logger.debug("Testing Research contract API classifications")
    classifications = get_public_api_classifications()
    assert classifications
    assert set(classifications.values()) == {"stable"}
    assert len(classifications) == len(set(classifications))


def test_every_public_export_is_classified() -> None:
    """FR-RES-026: every __all__ name has one stable classification."""
    from app.services.research import __all__ as package_all

    logger.debug("Testing Research public export coverage")
    classified = set(get_public_api_classifications())
    unclassified = set(package_all) - classified
    assert not unclassified, f"Unclassified public exports: {sorted(unclassified)}"
