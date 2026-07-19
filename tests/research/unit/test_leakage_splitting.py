"""Unit tests for chronological Research splitting."""

import pandas as pd
from app.services.research.leakage import enforce_time_split
from app.utils import logger


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
