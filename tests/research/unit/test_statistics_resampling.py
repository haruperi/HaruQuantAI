"""Unit tests for seeded Research resampling."""

import numpy as np
import pytest
from app.composition.logging import get_logger
from app.services.research import (
    block_bootstrap_ci,
    block_bootstrap_distribution,
    create_research_value,
    permutation_test,
)

logger = get_logger(__name__)


def _config() -> object:
    """Build test statistical settings.

    Returns:
        Seeded bounded configuration.
    """
    logger.debug("Building Research resampling test config")
    return create_research_value("StatisticalConfig", 7, 100, 100, 2, 100, None)


def test_distribution_is_seed_reproducible() -> None:
    """Verify fixed seeds reproduce bootstrap distributions."""
    logger.debug("Testing Research bootstrap reproducibility")
    values = np.arange(10, dtype="float64")
    first = block_bootstrap_distribution(values, statistic=np.mean, config=_config())
    second = block_bootstrap_distribution(values, statistic=np.mean, config=_config())
    assert np.array_equal(first, second)


def test_ci_rejects_non_finite_statistic() -> None:
    """Verify non-finite bootstrap statistics fail."""
    logger.debug("Testing Research bootstrap finite policy")
    with pytest.raises(ValueError, match=r"."):
        block_bootstrap_ci(
            np.arange(5, dtype="float64"),
            statistic=lambda _: float("nan"),
            confidence=0.95,
            config=_config(),
        )


def test_permutation_rejects_empty_sample() -> None:
    """Verify permutation tests reject empty samples."""
    logger.debug("Testing Research permutation sample")
    with pytest.raises(ValueError, match=r"."):
        permutation_test(0.0, np.asarray([]), alternative="two-sided", config=_config())
