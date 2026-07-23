"""Yahoo public table mapping tests."""

from datetime import UTC, datetime, timedelta

import pytest
from app.services.brokers.yahoo_history.mapping import _map_history, _provider_interval


class _Table:
    def __init__(self, rows: list[tuple[datetime, dict[str, object]]]) -> None:
        self._rows = rows

    def iterrows(self) -> object:
        return iter(self._rows)


def test_yahoo_mapping_never_synthesizes_observations() -> None:
    """Exact OHLC table values map without generated observations."""
    page = _map_history(
        _Table(
            [
                (
                    datetime(2026, 1, 1, tzinfo=UTC),
                    {"Open": 1, "High": 2, "Low": 0.5, "Close": 1.5, "Volume": 3},
                )
            ]
        ),
        symbol="AAPL",
        timeframe="1d",
        limit=1,
    )
    assert str(page.items[0].close) == "1.5"


def test_yahoo_empty_success_is_invalid() -> None:
    """An empty successful table never becomes fabricated bars."""
    with pytest.raises(ValueError, match="empty Yahoo"):
        _map_history(_Table([]), symbol="AAPL", timeframe="1d", limit=1)


def test_yahoo_bar_closes_after_it_opens() -> None:
    """The closing timestamp is derived from the interval, never zero-duration."""
    page = _map_history(
        _Table(
            [
                (
                    datetime(2026, 1, 1, tzinfo=UTC),
                    {"Open": 1, "High": 2, "Low": 0.5, "Close": 1.5, "Volume": 3},
                )
            ]
        ),
        symbol="AAPL",
        timeframe="1d",
        limit=1,
    )
    bar = page.items[0]
    assert bar.opening_timestamp < bar.closing_timestamp
    assert bar.closing_timestamp - bar.opening_timestamp == timedelta(days=1)


def test_yahoo_unsupported_interval_is_rejected() -> None:
    """An unparseable interval never silently falls back to a guessed duration."""
    with pytest.raises(ValueError, match="unsupported Yahoo interval"):
        _map_history(
            _Table(
                [
                    (
                        datetime(2026, 1, 1, tzinfo=UTC),
                        {"Open": 1, "High": 1, "Low": 1, "Close": 1},
                    )
                ]
            ),
            symbol="AAPL",
            timeframe="weird",
            limit=1,
        )


def test_yahoo_intervals() -> None:
    """All standard Yahoo interval types map correctly to duration offsets."""
    from app.services.brokers.yahoo_history.mapping import _interval_duration

    assert _interval_duration("1mo") == timedelta(days=30)
    assert _interval_duration("2wk") == timedelta(weeks=2)
    assert _interval_duration("3h") == timedelta(hours=3)
    assert _interval_duration("4m") == timedelta(minutes=4)


def test_yahoo_canonical_intervals_map_without_fallback() -> None:
    """Canonical application timeframes map only to verified yfinance intervals."""
    assert _provider_interval("H1") == "1h"
    assert _provider_interval("D1") == "1d"
    assert _provider_interval("1wk") == "1wk"
    with pytest.raises(ValueError, match="unsupported Yahoo timeframe"):
        _provider_interval("H4")


def test_yahoo_invalid_limit() -> None:
    """An invalid history limit raises ValueError."""
    with pytest.raises(ValueError, match="positive Yahoo history limit"):
        _map_history(_Table([]), symbol="AAPL", timeframe="1d", limit=0)


def test_yahoo_invalid_timestamp() -> None:
    """A non-datetime timestamp index raises ValueError."""
    with pytest.raises(ValueError, match="invalid Yahoo history timestamp"):
        _map_history(
            _Table(
                [
                    (
                        "not-a-datetime",
                        {"Open": 1, "High": 2, "Low": 0.5, "Close": 1.5, "Volume": 3},
                    )
                ]
            ),
            symbol="AAPL",
            timeframe="1d",
            limit=1,
        )


def test_yahoo_naive_timestamp() -> None:
    """A timezone-naive timestamp raises ValueError."""
    with pytest.raises(ValueError, match="timezone-naive Yahoo history timestamp"):
        _map_history(
            _Table(
                [
                    (
                        datetime(2026, 1, 1),  # noqa: DTZ001
                        {
                            "Open": 1,
                            "High": 2,
                            "Low": 0.5,
                            "Close": 1.5,
                            "Volume": 3,
                        },
                    )
                ]
            ),
            symbol="AAPL",
            timeframe="1d",
            limit=1,
        )


def test_yahoo_malformed_ohlc() -> None:
    """A row with missing OHLC values raises ValueError."""
    with pytest.raises(ValueError, match="malformed Yahoo OHLC response"):
        _map_history(
            _Table(
                [
                    (
                        datetime(2026, 1, 1, tzinfo=UTC),
                        {
                            "Open": None,
                            "High": 2,
                            "Low": 0.5,
                            "Close": 1.5,
                            "Volume": 3,
                        },
                    )
                ]
            ),
            symbol="AAPL",
            timeframe="1d",
            limit=1,
        )
