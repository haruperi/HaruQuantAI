"""Unit tests for Money Flow Index."""

from app.services.indicators import mfi

from tests.indicators.helpers import build_dataset, result_values, unwrap_response


def test_mfi_rising_typical_price_reaches_upper_bound() -> None:
    """FR-INDI-029: all-positive money flow returns exactly 100."""
    data = build_dataset([(1, 1, 1, 1, 10), (2, 2, 2, 2, 10), (3, 3, 3, 3, 10)])
    result = unwrap_response(mfi(data, period=2))
    assert result_values(result)["mfi_2"].iloc[1:].tolist() == [100.0, 100.0]
