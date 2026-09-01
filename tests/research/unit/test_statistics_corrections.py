"""Unit tests for Research multiple-comparison corrections."""

import pytest
from app.composition.logging import get_logger
from app.services.research import benjamini_hochberg, holm_bonferroni

logger = get_logger(__name__)


def test_bh_preserves_original_order() -> None:
    """Verify BH adjusted values restore caller order."""
    logger.debug("Testing Research BH ordering")
    adjusted = benjamini_hochberg([0.04, 0.001, 0.02], q=0.05)
    assert adjusted[1] < adjusted[2] < adjusted[0]


def test_holm_rejects_invalid_p_value() -> None:
    """Verify Holm correction rejects values outside the unit interval."""
    logger.debug("Testing Research Holm inputs")
    with pytest.raises(ValueError, match=r"."):
        holm_bonferroni([0.1, 1.2], alpha=0.05)


@pytest.mark.parametrize(
    ("values", "level", "message"),
    [
        ([], 0.05, "INVALID_P_VALUES"),
        ([0.1, float("nan")], 0.05, "INVALID_P_VALUES"),
        ([0.1], 1.0, "INVALID_CONTROL_LEVEL"),
    ],
)
def test_corrections_reject_empty_nonfinite_and_invalid_levels(
    values: list[float],
    level: float,
    message: str,
) -> None:
    """Cover every shared correction input gate."""
    with pytest.raises(ValueError, match=message):
        benjamini_hochberg(values, q=level)


def test_holm_restores_original_order() -> None:
    """Exercise the valid Holm correction path."""
    adjusted = holm_bonferroni([0.04, 0.001, 0.02], alpha=0.05)
    assert adjusted[1] < adjusted[2] <= adjusted[0]
