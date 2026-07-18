"""Unit tests for Hull Moving Average."""

import pytest
from app.services.indicators.trend import hull_ma

from tests.indicators.helpers import close_dataset


def test_hull_ma_matches_nested_wma_fixture() -> None:
    """FR-INDI-024: Hull MA composes the approved three WMA passes."""
    result = hull_ma(close_dataset([1, 2, 3, 4, 5, 6]), period=4)
    assert result.values["hull_ma_4"].iloc[4] == pytest.approx(5.0)
    assert result.values["hull_ma_4"].iloc[5] == pytest.approx(6.0)
