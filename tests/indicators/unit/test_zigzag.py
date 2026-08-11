"""Unit tests for the ZigZag indicator."""

from app.services.indicators import zigzag

from tests.indicators.helpers import assert_error, build_dataset, unwrap_response


def _swing_bars(count: int = 60) -> list[tuple[float, float, float, float, float]]:
    """Build price bars with valid low/high ranges."""
    bars = []
    for i in range(count):
        base = 10.0 + i * 0.1
        high = base + (5.0 if i % 10 == 5 else 1.0)
        low = base - (5.0 if i % 10 == 0 else 0.5)
        open_val = base
        close_val = base + 0.2
        bars.append((open_val, high, low, close_val, 100.0))
    return bars


def test_zigzag_calculates_pivots() -> None:
    """zigzag identifies swing high/low points."""
    data = build_dataset(_swing_bars(60))
    result = unwrap_response(zigzag(data, depth=5))
    assert result.indicator_id == "zigzag"
    assert any("zigzag" in col for col in result.values.columns)


def test_zigzag_rejects_invalid_depth() -> None:
    """Depth < 2 is rejected fail-fast."""
    data = build_dataset(_swing_bars(20))
    assert_error(zigzag(data, depth=1), "IND_INVALID_PARAMETER")
