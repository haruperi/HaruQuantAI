"""Unit tests for monotonic standard response timing."""

import pytest
from app.utils import get_execution_ms


def test_get_execution_ms_uses_nanoseconds_and_rounds_to_three_decimals() -> None:
    assert get_execution_ms(1_000_000, clock=lambda: 2_234_567) == 1.235


def test_get_execution_ms_allows_zero_duration() -> None:
    assert get_execution_ms(5, clock=lambda: 5) == 0.0


def test_get_execution_ms_rejects_invalid_or_future_start() -> None:
    with pytest.raises(TypeError):
        get_execution_ms(1.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="non-negative"):
        get_execution_ms(-1)
    with pytest.raises(ValueError, match="cannot be after"):
        get_execution_ms(10, clock=lambda: 9)
