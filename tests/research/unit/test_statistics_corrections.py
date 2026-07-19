"""Unit tests for Research multiple-comparison corrections."""

import pytest
from app.services.research.statistics import benjamini_hochberg, holm_bonferroni
from app.utils import logger
from app.utils.errors import ValidationError


def test_bh_preserves_original_order() -> None:
    """Verify BH adjusted values restore caller order."""
    logger.debug("Testing Research BH ordering")
    adjusted = benjamini_hochberg([0.04, 0.001, 0.02], q=0.05)
    assert adjusted[1] < adjusted[2] < adjusted[0]


def test_holm_rejects_invalid_p_value() -> None:
    """Verify Holm correction rejects values outside the unit interval."""
    logger.debug("Testing Research Holm inputs")
    with pytest.raises(ValidationError):
        holm_bonferroni([0.1, 1.2], alpha=0.05)
