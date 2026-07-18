"""Unit tests for Bollinger Bands."""

import pytest
from app.services.indicators.trend import bollinger_bands

from tests.indicators.helpers import close_dataset


def test_bollinger_bands_matches_sample_deviation_fixture() -> None:
    """FR-INDI-025: bands use SMA plus or minus sample deviation."""
    result = bollinger_bands(close_dataset([1.0, 2.0, 3.0]), period=3, std_dev=2.0)
    row = result.values.iloc[-1]
    assert row["bollinger_bands_middle_3"] == pytest.approx(2.0)
    assert row["bollinger_bands_upper_3"] == pytest.approx(4.0)
    assert row["bollinger_bands_lower_3"] == pytest.approx(0.0)
