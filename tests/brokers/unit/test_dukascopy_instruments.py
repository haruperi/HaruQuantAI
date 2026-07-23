"""Dukascopy exact-instrument declaration tests."""

import pytest
from app.services.brokers.dukascopy_ticks.instruments import (
    _INSTRUMENT_PRICE_DIVISORS,
    _price_divisor,
)


def test_declared_instruments_are_exact_and_bounded() -> None:
    """Only explicitly fixture-verified provider symbols are declared."""
    assert _INSTRUMENT_PRICE_DIVISORS == {"EURUSD": 100_000}


def test_price_divisor_returns_declared_value() -> None:
    """A declared symbol returns its exact documented price divisor."""
    assert _price_divisor("EURUSD") == 100_000


def test_price_divisor_rejects_undeclared_symbol() -> None:
    """An undeclared symbol never falls back to an invented divisor."""
    with pytest.raises(ValueError, match="unsupported exact Dukascopy"):
        _price_divisor("GBPUSD")
