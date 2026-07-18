"""Unit tests for the Pinbar pattern."""

from app.services.indicators.candles import pinbar

from tests.indicators.helpers import build_dataset


def test_pinbar_matches_bullish_and_bearish_fixtures() -> None:
    """FR-INDI-033: long lower and upper shadows map to signed patterns."""
    data = build_dataset([(7, 10, 0, 8, 10), (2, 10, 0, 3, 10)])
    assert pinbar(data).values["pinbar"].tolist() == [1.0, -1.0]
