"""Component tests for the official aggressive-trade-imbalance calculator."""

import pytest
from app.services.indicators import aggressive_trade_imbalance

from tests.indicators.helpers import (
    assert_error,
    build_dataset,
    result_values,
    unwrap_response,
)

_BARS = [
    (10.0, 10.5, 9.5, 10.5, 100.0),  # buy: 100
    (10.5, 11.0, 10.0, 10.0, 300.0),  # sell: 300
]


def test_aggressive_trade_imbalance_matches_hand_calculation() -> None:
    """ATI matches a hand-derived close/open sign volume split."""
    data = build_dataset(_BARS)
    result = unwrap_response(aggressive_trade_imbalance(data, window=2))
    values = result_values(result)
    expected = (100.0 - 300.0) / (100.0 + 300.0)
    assert values["aggressive_trade_imbalance_2"].iloc[-1] == pytest.approx(expected)


def test_aggressive_trade_imbalance_short_history_is_entirely_warmup() -> None:
    """A dataset shorter than the window stays entirely unavailable."""
    data = build_dataset(_BARS)
    result = unwrap_response(aggressive_trade_imbalance(data, window=5))
    values = result_values(result)
    assert values["aggressive_trade_imbalance_5"].isna().all()
    assert (values["unavailable_reason"] == "warmup").all()


def test_aggressive_trade_imbalance_rejects_zero_window() -> None:
    """A non-positive window is rejected before calculation."""
    data = build_dataset(_BARS)
    assert_error(aggressive_trade_imbalance(data, window=0), "IND_INVALID_PARAMETER")


def test_aggressive_trade_imbalance_is_deterministic() -> None:
    """Identical inputs and configuration produce identical output values."""
    data = build_dataset(_BARS)
    first = unwrap_response(aggressive_trade_imbalance(data, window=2))
    second = unwrap_response(aggressive_trade_imbalance(data, window=2))
    assert result_values(first)[
        "aggressive_trade_imbalance_2"
    ].tolist() == pytest.approx(
        result_values(second)["aggressive_trade_imbalance_2"].tolist(), nan_ok=True
    )
