"""Unit tests for the Engulfing pattern."""

import pandas as pd
from app.services.indicators.candles import engulfing

from tests.indicators.helpers import build_dataset


def test_engulfing_matches_bullish_fixture_with_warmup() -> None:
    """FR-INDI-032: a bullish body engulfing emits one after warmup."""
    data = build_dataset([(2.0, 2.5, 0.5, 1.0, 10), (0.5, 3.0, 0.0, 2.5, 10)])
    values = engulfing(data).values_only["engulfing"]
    assert pd.isna(values.iloc[0])
    assert values.iloc[1] == 1.0
