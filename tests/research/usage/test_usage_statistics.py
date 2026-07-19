"""Runnable usage examples for Research statistics."""

import numpy as np
import pandas as pd
from app.services.research.contracts import StatisticalConfig
from app.services.research.statistics import (
    benjamini_hochberg,
    block_bootstrap_ci,
    block_bootstrap_distribution,
    compute_null_percentile,
    exceeds_null_threshold,
    holm_bonferroni,
    null_distribution_stats,
    permutation_test,
    r_space_null,
    random_entry_null,
    session_randomized_null,
    shuffle_returns_null,
)
from app.utils import logger


def _config() -> StatisticalConfig:
    """Build usage statistical settings.

    Returns:
        Seeded bounded configuration.
    """
    logger.debug("Building Research statistics usage config")
    return StatisticalConfig(7, 20, 20, 2, 20, "benjamini_hochberg")


def test_usage_resampling_distribution() -> None:
    """Generate a block-bootstrap distribution."""
    logger.debug("Running bootstrap distribution usage")
    assert (
        block_bootstrap_distribution(
            np.arange(10.0), statistic=np.mean, config=_config()
        ).size
        == 20
    )


def test_usage_resampling_ci() -> None:
    """Compute a bootstrap confidence interval."""
    logger.debug("Running bootstrap interval usage")
    assert (
        len(
            block_bootstrap_ci(
                np.arange(10.0), statistic=np.mean, confidence=0.95, config=_config()
            )
        )
        == 2
    )


def test_usage_resampling_permutation() -> None:
    """Compute an empirical permutation p-value."""
    logger.debug("Running permutation usage")
    assert (
        0
        <= permutation_test(1.0, np.arange(5.0), alternative="upper", config=_config())
        <= 1
    )


def test_usage_null_models_random_entry() -> None:
    """Generate a matched random-entry null."""
    logger.debug("Running random-entry null usage")
    assert (
        random_entry_null(
            pd.DataFrame({"close": np.arange(1.0, 21.0)}),
            side="buy",
            hold_bars=2,
            config=_config(),
        ).size
        == 20
    )


def test_usage_null_models_r_space() -> None:
    """Generate an R-space null."""
    logger.debug("Running R-space null usage")
    assert r_space_null(np.asarray([-1.0, 1.0]), config=_config()).size == 20


def test_usage_null_models_session_randomized() -> None:
    """Generate a within-session null."""
    logger.debug("Running session-null usage")
    frame = pd.DataFrame(
        {"session": ["a", "a", "b", "b"], "log_return": [1.0, 2.0, 3.0, 4.0]}
    )
    assert (
        session_randomized_null(frame, session_column="session", config=_config()).size
        == 20
    )


def test_usage_null_models_shuffle_returns() -> None:
    """Generate a shuffled-return null."""
    logger.debug("Running shuffled-null usage")
    assert shuffle_returns_null(pd.Series(np.arange(10.0)), config=_config()).size == 20


def test_usage_null_models_percentile() -> None:
    """Compute an observed null percentile."""
    logger.debug("Running null-percentile usage")
    assert compute_null_percentile(2.0, np.asarray([1.0, 2.0, 3.0])) > 0


def test_usage_null_models_stats() -> None:
    """Summarize a null distribution."""
    logger.debug("Running null-summary usage")
    assert null_distribution_stats(np.asarray([1.0, 2.0]))["count"] == 2


def test_usage_null_models_threshold() -> None:
    """Evaluate an explicit null threshold."""
    logger.debug("Running null-threshold usage")
    assert exceeds_null_threshold(
        3.0, np.asarray([1.0, 2.0]), quantile=0.9, alternative="upper"
    )


def test_usage_corrections_bh() -> None:
    """Apply BH FDR correction."""
    logger.debug("Running BH correction usage")
    assert benjamini_hochberg([0.01, 0.1], q=0.05).size == 2


def test_usage_corrections_holm() -> None:
    """Apply Holm family-wise correction."""
    logger.debug("Running Holm correction usage")
    assert holm_bonferroni([0.01, 0.1], alpha=0.05).size == 2
