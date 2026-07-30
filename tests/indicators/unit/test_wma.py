"""Unit tests for Weighted Moving Average."""

import pytest
from app.services.indicators import wma

from tests.indicators.helpers import close_dataset, result_values, unwrap_response


def test_wma_matches_hand_calculated_fixture() -> None:
    """FR-INDI-023: WMA applies weights oldest one through newest period."""
    result = unwrap_response(wma(close_dataset([1.0, 2.0, 3.0, 4.0]), period=3))
    values = result_values(result)
    assert values["wma_3"].iloc[2] == pytest.approx(14.0 / 6.0)
    assert values["wma_3"].iloc[3] == pytest.approx(20.0 / 6.0)
