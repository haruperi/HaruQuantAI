"""Unit tests for the Pinbar pattern."""

from app.services.indicators import pinbar

from tests.indicators.helpers import build_dataset, result_values, unwrap_response


def test_pinbar_matches_bullish_and_bearish_fixtures() -> None:
    """FR-INDI-033: long lower and upper shadows map to signed patterns."""
    data = build_dataset([(7, 10, 0, 8, 10), (2, 10, 0, 3, 10)])
    result = unwrap_response(pinbar(data))
    assert result_values(result)["pinbar"].tolist() == [1.0, -1.0]
