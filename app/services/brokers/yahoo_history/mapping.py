"""yfinance public table to canonical historical-bar mapping."""

# ruff: noqa: ANN401 - table rows are a transitive public interface.

import re
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from app.services.brokers.contracts import BrokerBar, BrokerPage
from app.services.brokers.contracts.protocols import _ProviderResponseError

_INTERVAL_PATTERN = re.compile(r"\A(\d+)(mo|wk|d|h|m)\Z")
_CANONICAL_INTERVALS = {
    "M1": "1m",
    "M2": "2m",
    "M5": "5m",
    "M15": "15m",
    "M30": "30m",
    "H1": "1h",
    "D1": "1d",
    "D5": "5d",
    "W1": "1wk",
    "MN1": "1mo",
    "MN3": "3mo",
}
_PROVIDER_INTERVALS = frozenset(_CANONICAL_INTERVALS.values())


def _provider_interval(timeframe: str) -> str:
    """Return the exact yfinance interval for one accepted timeframe.

    Args:
        timeframe: Canonical application or exact provider timeframe.

    Returns:
        Exact interval accepted by yfinance history.

    Raises:
        ValueError: If the timeframe has no verified yfinance mapping.
    """
    if timeframe in _PROVIDER_INTERVALS:
        return timeframe
    try:
        return _CANONICAL_INTERVALS[timeframe.upper()]
    except KeyError as error:
        raise ValueError("unsupported Yahoo timeframe") from error


def _interval_duration(interval: str) -> timedelta:
    """Return the exact closed-bar duration for one declared Yahoo interval.

    Raises:
        ValueError: If the interval syntax or unit is unsupported.
    """
    match = _INTERVAL_PATTERN.fullmatch(interval)
    if match is None:
        message = f"unsupported Yahoo interval: {interval}"
        raise ValueError(message)
    amount = int(match.group(1))
    unit = match.group(2)
    if unit == "mo":
        return timedelta(days=30 * amount)
    if unit == "wk":
        return timedelta(weeks=amount)
    if unit == "d":
        return timedelta(days=amount)
    if unit == "h":
        return timedelta(hours=amount)
    return timedelta(minutes=amount)


def _map_history(
    table: Any,
    *,
    symbol: str,
    timeframe: str,
    limit: int,
    requested_timeframe: str | None = None,
) -> BrokerPage[BrokerBar]:
    """Iterate public rows and reject empty or malformed OHLC evidence.

    Returns:
        Canonical bounded historical-bar page.

    Raises:
        ValueError: If the caller limit or interval is invalid.
        _ProviderResponseError: If the provider payload is empty or malformed.
    """
    if limit <= 0:
        raise ValueError("positive Yahoo history limit is required")
    rows = list(table.iterrows())
    if not rows:
        raise _ProviderResponseError("empty Yahoo history response")
    duration = _interval_duration(timeframe)
    bars: list[BrokerBar] = []
    for index, row in rows[:limit]:
        timestamp = index.to_pydatetime() if hasattr(index, "to_pydatetime") else index
        if not isinstance(timestamp, datetime):
            raise _ProviderResponseError("invalid Yahoo history timestamp")
        if timestamp.tzinfo is None:
            raise _ProviderResponseError("timezone-naive Yahoo history timestamp")
        opening = timestamp.astimezone(UTC)
        values = {name: row[name] for name in ("Open", "High", "Low", "Close")}
        if any(value is None for value in values.values()):
            raise _ProviderResponseError("malformed Yahoo OHLC response")
        bars.append(
            BrokerBar(
                symbol=symbol,
                opening_timestamp=opening,
                closing_timestamp=opening + duration,
                is_closed=True,
                open=Decimal(str(values["Open"])),
                high=Decimal(str(values["High"])),
                low=Decimal(str(values["Low"])),
                close=Decimal(str(values["Close"])),
                provider_timeframe=timeframe,
                requested_timeframe=requested_timeframe or timeframe,
                price_unit="provider_quote_currency",
                quantity_unit="provider_volume",
                trade_volume=(
                    Decimal(str(row["Volume"]))
                    if row.get("Volume") is not None
                    else None
                ),
            )
        )
    return BrokerPage(
        items=tuple(bars),
        limit=limit,
        truncated=len(rows) > limit,
        provider_metadata={"provider": "yahoo", "research_only": True},
    )
