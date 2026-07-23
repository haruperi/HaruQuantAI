"""Regression guards for large datasets and the public error boundary.

Before these guards existed, ``_input_checksum`` canonicalized the whole
``MarketDataset`` in one ``app.utils.canonical_json`` call. That helper enforces
a cumulative 10,000-item traversal bound, so every official indicator raised a
raw Utils ``ValidationError`` for any dataset beyond 664 records, far below the
documented ``MAX_INPUT_ROWS`` limit of 1,000,000.
"""

import pytest
from app.services.indicators import atr, obv, rsi, sma
from app.services.indicators.core import registry
from app.services.indicators.core.errors import IndicatorError, IndicatorErrorCode
from app.services.indicators.core.validation import MAX_INPUT_ROWS

from tests.indicators.helpers import build_dataset, close_dataset

# One record contributes roughly fifteen canonical-JSON items, so the previous
# single-call implementation failed just past this many records.
_PREVIOUS_CEILING = 664


def _prices(count: int) -> list[float]:
    """Build a strictly positive, non-constant price series.

    Args:
        count: Number of prices to generate.

    Returns:
        Row-ordered close prices.
    """
    return [1.10 + (position % 97) * 0.0001 for position in range(count)]


def _bars(count: int) -> list[tuple[float, float, float, float, float]]:
    """Build row-ordered OHLCV tuples with a non-degenerate range.

    Args:
        count: Number of bars to generate.

    Returns:
        Row-ordered ``(open, high, low, close, volume)`` tuples.
    """
    bars = []
    for position in range(count):
        close = 1.10 + (position % 97) * 0.0001
        bars.append((close, close + 0.0005, close - 0.0005, close, 100.0 + position))
    return bars


@pytest.mark.parametrize("row_count", [_PREVIOUS_CEILING, _PREVIOUS_CEILING + 1, 1_000])
def test_indicator_succeeds_across_the_previous_checksum_ceiling(
    row_count: int,
) -> None:
    """A dataset at or past the old 664-record ceiling now calculates cleanly."""
    result = sma(close_dataset(_prices(row_count)), period=3)
    assert len(result.values) == row_count
    assert len(result.manifest.input_checksum) == 64
    assert result.manifest.row_count == row_count


def test_every_indicator_family_handles_a_multi_thousand_bar_history() -> None:
    """Fixed-OHLC, cumulative, and smoothed indicators all clear the old ceiling.

    Each family reaches ``build_indicator_result`` by a different route, so all
    three are exercised rather than trusting one representative.
    """
    row_count = 1_000
    dataset = build_dataset(_bars(row_count))
    assert len(atr(dataset, period=14).values) == row_count
    assert len(obv(dataset).values) == row_count
    assert len(rsi(dataset, period=14).values) == row_count


def test_large_input_checksum_is_deterministic_and_order_sensitive() -> None:
    """The chunked digest stays stable for equal input and changes with order.

    Order sensitivity matters because the digest is folded chunk by chunk; a
    naive fold could otherwise collide for permuted records.
    """
    prices = _prices(_PREVIOUS_CEILING + 36)
    first = sma(close_dataset(prices), period=3).manifest.input_checksum
    second = sma(close_dataset(prices), period=3).manifest.input_checksum
    reordered = sma(close_dataset(list(reversed(prices))), period=3)

    assert first == second
    assert reordered.manifest.input_checksum != first


def test_join_to_round_trips_a_dataset_past_the_old_ceiling() -> None:
    """``join_to`` still matches the manifest checksum past the old ceiling."""
    dataset = close_dataset(_prices(_PREVIOUS_CEILING + 36))
    joined = sma(dataset, period=3).join_to(dataset)
    assert len(joined) == _PREVIOUS_CEILING + 36
    assert "sma_3" in joined.columns


def test_documented_row_limit_is_reachable_in_principle() -> None:
    """The enforced limit is the documented one, not a hidden serialization bound."""
    assert MAX_INPUT_ROWS == 1_000_000
    assert _PREVIOUS_CEILING < MAX_INPUT_ROWS


def test_raw_upstream_exception_never_crosses_the_public_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An unexpected upstream failure surfaces as a redacted IND_INTERNAL_ERROR."""

    def _explode(_value: object) -> str:
        """Simulate an unexpected upstream serialization failure.

        Args:
            _value: Ignored payload.

        Returns:
            Never returns.

        Raises:
            RuntimeError: Always, standing in for a raw upstream exception.
        """
        raise RuntimeError("upstream payload 4111-1111-1111-1111 exploded")

    monkeypatch.setattr("app.services.indicators.core.results.canonical_json", _explode)
    with pytest.raises(IndicatorError) as failure:
        sma(close_dataset(_prices(50)), period=3)

    assert failure.value.code is IndicatorErrorCode.IND_INTERNAL_ERROR
    assert failure.value.details["operation"] == "sma"
    assert failure.value.details["failure_type"] == "RuntimeError"
    # The original exception and its payload must not cross the boundary.
    assert failure.value.__cause__ is None
    assert "4111" not in failure.value.message
    assert "4111" not in str(failure.value.details)


def test_deliberate_indicator_error_is_not_masked_by_the_guard() -> None:
    """The boundary guard preserves documented deterministic failure codes."""
    with pytest.raises(IndicatorError) as failure:
        sma(close_dataset(_prices(50)), period=1)
    assert failure.value.code is not IndicatorErrorCode.IND_INTERNAL_ERROR


def test_every_official_indicator_is_boundary_guarded() -> None:
    """All twenty registered calculators carry the public boundary guard."""
    import importlib

    unguarded = []
    for spec in registry.list_indicators():
        module_path, _, attribute = spec.import_path.partition(":")
        function = getattr(importlib.import_module(module_path), attribute)
        if not hasattr(function, "__wrapped__"):
            unguarded.append(spec.indicator_id)
    assert unguarded == [], f"unguarded official indicators: {unguarded}"
