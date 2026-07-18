"""Unit tests for the Doji pattern."""

from app.services.indicators.candles import doji

from tests.indicators.helpers import build_dataset


def test_doji_matches_body_to_range_fixture() -> None:
    """FR-INDI-031: Doji uses the explicit body-to-range threshold."""
    data = build_dataset([(1.0, 1.5, 0.5, 1.05, 10.0), (1.0, 1.5, 0.5, 1.2, 10.0)])
    assert doji(data, threshold=0.1).values["doji"].tolist() == [1.0, 0.0]


def test_doji_zero_range_candle_is_doji_when_open_equals_close() -> None:
    """FR-INDI-031: a zero-range candle (open == close) is a Doji."""
    data = build_dataset([(1.0, 1.0, 1.0, 1.0, 10.0), (1.0, 1.5, 0.5, 1.2, 10.0)])
    assert doji(data, threshold=0.1).values["doji"].tolist() == [1.0, 0.0]
