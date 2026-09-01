"""Unit tests for matched Research null models."""

import numpy as np
import pandas as pd
import pytest
from app.composition.logging import get_logger
from app.services.research import (
    compute_null_percentile,
    create_research_value,
    exceeds_null_threshold,
    null_distribution_stats,
    r_space_null,
    random_entry_null,
    session_randomized_null,
    shuffle_returns_null,
)

logger = get_logger(__name__)


def _config(block: int = 2) -> object:
    """Build null-model settings.

    Args:
        block: Block length.

    Returns:
        Seeded bounded settings.
    """
    logger.debug("Building Research null-model config")
    return create_research_value("StatisticalConfig", 7, 20, 20, block, 20, None)


def test_random_entry_null_matches_side() -> None:
    """Verify sell nulls invert buy outcomes under the same seed."""
    logger.debug("Testing Research matched null direction")
    frame = pd.DataFrame({"close": np.linspace(100.0, 110.0, 20)})
    buy = random_entry_null(frame, side="buy", hold_bars=2, config=_config())
    sell = random_entry_null(frame, side="sell", hold_bars=2, config=_config())
    assert np.allclose(buy, -sell)


def test_r_space_null_rejects_non_finite() -> None:
    """Verify R-space nulls reject non-finite samples."""
    logger.debug("Testing Research R-space finite policy")
    with pytest.raises(ValueError, match=r"."):
        r_space_null(np.asarray([1.0, np.nan]), config=_config())


def test_session_null_preserves_session_groups() -> None:
    """Verify session randomization returns the requested sample count."""
    logger.debug("Testing Research session null groups")
    frame = pd.DataFrame(
        {"session": ["a", "a", "b", "b"], "log_return": [1.0, 2.0, 3.0, 4.0]}
    )
    assert (
        session_randomized_null(frame, session_column="session", config=_config()).size
        == 20
    )


def test_shuffle_null_rejects_large_block() -> None:
    """Verify shuffled blocks cannot exceed the sample."""
    logger.debug("Testing Research shuffled-null block")
    with pytest.raises(ValueError, match=r"."):
        shuffle_returns_null(pd.Series([1.0, 2.0]), config=_config(3))


def test_percentile_outside_sample_range() -> None:
    """Verify observations above the null range have percentile 100."""
    logger.debug("Testing Research null percentile")
    assert compute_null_percentile(5.0, np.asarray([1.0, 2.0])) == 100.0


def test_null_stats_reject_empty() -> None:
    """Verify empty null summaries fail."""
    logger.debug("Testing Research null summary input")
    with pytest.raises(ValueError, match=r"."):
        null_distribution_stats(np.asarray([]))


def test_threshold_direction_is_explicit() -> None:
    """Verify upper and lower threshold directions differ."""
    logger.debug("Testing Research null threshold direction")
    values = np.asarray([-2.0, -1.0, 1.0, 2.0])
    assert exceeds_null_threshold(3.0, values, quantile=0.75, alternative="upper")
    assert not exceeds_null_threshold(3.0, values, quantile=0.75, alternative="lower")


def test_null_models_cover_mixed_blocks_summaries_and_policy_guards() -> None:
    """Exercise remaining valid variants and fail-closed policies."""
    frame = pd.DataFrame({"close": np.linspace(100.0, 110.0, 20)})
    mixed = random_entry_null(frame, side="mixed", hold_bars=2, config=_config())
    assert mixed.size == 20
    with pytest.raises(ValueError, match="INVALID_RANDOM_ENTRY_INPUT"):
        random_entry_null(
            pd.DataFrame({"open": [1.0]}),
            side="buy",
            hold_bars=1,
            config=_config(),
        )
    with pytest.raises(ValueError, match="INVALID_HOLD_HORIZON"):
        random_entry_null(frame, side="buy", hold_bars=20, config=_config())
    with pytest.raises(ValueError, match="SESSION_RETURN_COLUMNS_REQUIRED"):
        session_randomized_null(
            pd.DataFrame({"session": ["a"]}),
            session_column="session",
            config=_config(),
        )
    shuffled = shuffle_returns_null(pd.Series(range(8)), config=_config(2))
    assert shuffled.size == 20
    with pytest.raises(ValueError, match="OBSERVED_NONFINITE"):
        compute_null_percentile(float("nan"), np.asarray([1.0]))
    assert null_distribution_stats(np.asarray([1.0, 2.0]))["count"] == 2.0
    values = np.asarray([-2.0, -1.0, 1.0, 2.0])
    assert exceeds_null_threshold(
        3.0,
        values,
        quantile=0.75,
        alternative="two-sided",
    )
    with pytest.raises(ValueError, match="INVALID_NULL_THRESHOLD_POLICY"):
        exceeds_null_threshold(
            1.0,
            values,
            quantile=1.0,
            alternative="upper",
        )
