"""Unit tests for chronological Research splitting."""

import pandas as pd
import pytest
from app.services.research import enforce_time_split
from app.utils import get_logger

logger = get_logger(__name__)


def test_time_split_is_chronological_and_gapped() -> None:
    """Verify partitions are chronological with excluded embargo rows."""
    logger.debug("Testing Research chronological split")
    frame = pd.DataFrame(
        {"value": range(20)},
        index=pd.date_range("2026-01-01", periods=20, freq="h", tz="UTC"),
    )
    result = enforce_time_split(
        frame, train_fraction=0.5, validation_fraction=0.2, gap_rows=1
    )
    assert result.train.index.max() < result.validation.index.min()
    assert result.validation.index.max() < result.test.index.min()
    assert len(result.train) + len(result.validation) + len(result.test) == 18


@pytest.mark.parametrize(
    ("frame", "fractions", "gap", "message"),
    [
        (
            pd.DataFrame({"x": [1, 2]}, index=pd.RangeIndex(2)),
            (0.5, 0.2),
            0,
            "UTC_TIME_INDEX_REQUIRED",
        ),
        (
            pd.DataFrame(
                {"x": [1, 2]},
                index=pd.to_datetime(["2026-01-02", "2026-01-01"], utc=True),
            ),
            (0.5, 0.2),
            0,
            "ORDERED_UNIQUE_TIME_REQUIRED",
        ),
        (
            pd.DataFrame(
                {"x": range(5)},
                index=pd.date_range("2026-01-01", periods=5, tz="UTC"),
            ),
            (0.8, 0.3),
            0,
            "INVALID_SPLIT_FRACTIONS",
        ),
        (
            pd.DataFrame(
                {"x": range(5)},
                index=pd.date_range("2026-01-01", periods=5, tz="UTC"),
            ),
            (0.5, 0.2),
            -1,
            "INVALID_SPLIT_GAP",
        ),
        (
            pd.DataFrame(
                {"x": range(2)},
                index=pd.date_range("2026-01-01", periods=2, tz="UTC"),
            ),
            (0.5, 0.2),
            0,
            "EMPTY_TIME_PARTITION",
        ),
    ],
)
def test_time_split_rejects_invalid_boundaries(
    frame: pd.DataFrame,
    fractions: tuple[float, float],
    gap: int,
    message: str,
) -> None:
    """Exercise every chronological split safety gate."""
    with pytest.raises(ValueError, match=message):
        enforce_time_split(
            frame,
            train_fraction=fractions[0],
            validation_fraction=fractions[1],
            gap_rows=gap,
        )
