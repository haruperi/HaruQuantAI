"""Integration evidence for seeded Analytics statistical validation."""

# ruff: noqa: INP001

from app.services.analytics.metrics.statistics import run_statistical_validation
from app.utils import logger
from tests.analytics._support import _configured_result


def test_seeded_validation_is_reproducible() -> None:
    """The full bounded validation workflow reproduces identical evidence."""
    logger.debug("Testing Analytics statistical workflow reproducibility")
    _, config = _configured_result()
    values = tuple(float(index - 15) for index in range(30))
    assert run_statistical_validation(
        values, config=config
    ) == run_statistical_validation(values, config=config)
