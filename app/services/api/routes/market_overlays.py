"""Composed technical overlays (Volatility, ADR, Range) for the Markets widget.

Volatility and ADR are Indicators-owned formulas; the underlying D1 bars are
Data-owned. Neither domain may depend on the other (Data does not import
Indicators, avoiding a domain cycle), so composing "bars + indicator" into one
display row is API-layer orchestration — the same shape demonstrated in
``tests/api/usage/widget/market.py``. This module holds that composition so
the route handler still delegates rather than calculating.

Every value here is a read-only overlay computed from already-public Data and
Indicators functions; nothing is persisted and nothing is invented when a
symbol lacks enough history — an unavailable overlay is ``None``, never a
fabricated number.
"""

from __future__ import annotations

import math
import threading
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Final, Protocol, cast

from app.services.data import (
    build_market_data_request,
    build_symbol_metadata_request,
    get_market_data,
    get_symbol_metadata,
)
from app.services.indicators import adr, rolling_volatility
from app.utils import generate_id, get_logger

logger = get_logger(__name__)

# D1 bars for a 10-period indicator; 40 calendar days comfortably covers
# weekends/holidays to guarantee at least 11 trading-day bars.
_HISTORY_DAYS: Final = 40
_ADR_PERIOD: Final = 10
_VOLATILITY_PERIOD: Final = 10
_ANNUALIZATION_FACTOR: Final = 252.0
_DIGITS_WITH_FRACTIONAL_PIP: Final = frozenset({3, 5})
_DEFAULT_POINT: Final = 0.00001
# Need the *prior* settled bar's indicator value (index -2): period bars to
# warm up, one more so a prior (non-warmup) value actually exists.
_MIN_BARS_REQUIRED: Final = _ADR_PERIOD + 2

# Indicators are D1-granularity and only change once a session closes, so a
# longer cache than the quote/directory caches is safe and avoids repeating
# the historical fetch plus two indicator calculations on every request.
_OVERLAY_CACHE_TTL_SECONDS: Final = 300.0
_overlay_cache_lock: Final = threading.Lock()
_OverlayCacheKey = tuple[str, str]
_overlay_cache: dict[_OverlayCacheKey, tuple[float, TechnicalOverlay]] = {}


class _IndicatorValues(Protocol):
    """Private structural view of an indicator values table."""

    def __getitem__(self, key: str) -> object:
        """Return one named indicator series."""


class _IndicatorData(Protocol):
    """Private structural view of Indicators result data."""

    output_columns: tuple[str, ...]
    values: _IndicatorValues


class _IndicatorResponse(Protocol):
    """Private structural view of an Indicators standard response."""

    status: str
    data: _IndicatorData | None


@dataclass(frozen=True, slots=True)
class TechnicalOverlay:
    """One symbol's composed D1 display evidence.

    Values remain nullable because the API must never invent market evidence
    when history, metadata, or an indicator result is unavailable.
    """

    volatility_percent: float | None = None
    adr_pips: float | None = None
    range_percent_of_adr: float | None = None
    pip_size: float | None = None
    open: float | None = None
    high: float | None = None
    low: float | None = None


_EMPTY_OVERLAY: Final = TechnicalOverlay()


def _reset_overlay_cache_for_tests() -> None:
    """Clear the in-process technical-overlay cache (test-only reset hook)."""
    with _overlay_cache_lock:
        _overlay_cache.clear()


def _pip_size(digits: int, point: float) -> float:
    """Return the pip size for one symbol's quote precision.

    MT5 quotes fractional-pip symbols (3 or 5 digits) at one-tenth of the
    tick; every other precision quotes directly in pips.

    Returns:
        Pip size in price units.
    """
    return point * 10.0 if digits in _DIGITS_WITH_FRACTIONAL_PIP else point


def _resolve_pip_size(source_id: str, symbol: str, request_id: str) -> float | None:
    """Resolve one symbol's pip size from its broker metadata.

    Returns:
        Pip size, or ``None`` if metadata is unavailable.
    """
    try:
        response = get_symbol_metadata(
            build_symbol_metadata_request(
                source_id=source_id, symbol=symbol, request_id=request_id
            )
        )
    except Exception:  # noqa: BLE001 - degrade to unavailable, never fail closed
        logger.debug("Symbol metadata unavailable for pip size: %s", symbol)
        return None
    if response.status != "success" or response.data is None:
        return None
    digits = int(getattr(response.data, "digits", None) or 5)
    point = float(getattr(response.data, "point", None) or _DEFAULT_POINT)
    return _pip_size(digits, point)


def _fetch_daily_bars(source_id: str, symbol: str, request_id: str) -> object | None:
    """Fetch a bounded D1 history window for one symbol.

    Returned as the opaque ``MarketDataset`` Data hands back — passed
    straight through to Indicators' public functions, which own its precise
    type; this boundary never re-declares it.

    Returns:
        The dataset, or ``None`` if unavailable or too short to warm up.
    """
    end = datetime.now(UTC)
    start = end - timedelta(days=_HISTORY_DAYS)
    try:
        response = get_market_data(
            build_market_data_request(
                source_id=source_id,
                symbol=symbol,
                data_kind="bars",
                timeframe="D1",
                start=start,
                end=end,
                limit=_HISTORY_DAYS,
                use_cache=True,
                quality_failure_behavior="warn",
                workflow_context="research",
                precision_policy="decimal_string",
                request_id=request_id,
            )
        )
    except Exception:  # noqa: BLE001 - degrade to unavailable, never fail closed
        logger.debug("D1 history unavailable for overlay: %s", symbol)
        return None
    if response.status != "success" or response.data is None:
        return None
    records = cast("tuple[object, ...]", response.data.records)
    if len(records) < _MIN_BARS_REQUIRED:
        return None
    return cast("object", response.data)


def _prior_settled_value(series_values: object) -> float | None:
    """Return one indicator series' prior (already-settled) value.

    Row ``-1`` is today's still-forming bar; row ``-2`` is the last fully
    closed session, matching the ``.shift(1)`` convention used to avoid
    displaying a value derived from an incomplete bar.

    Returns:
        The prior value, or ``None`` if absent or not-a-number.
    """
    prior = series_values.iloc[-2]  # type: ignore[attr-defined]
    if prior is None or (isinstance(prior, float) and math.isnan(prior)):
        return None
    return float(prior)


def _first_output_series(result: object) -> object | None:
    """Return the first indicator output series when one exists.

    Args:
        result: Indicators-owned standard response.

    Returns:
        First output series, or ``None`` when the calculation is unavailable.
    """
    response = cast("_IndicatorResponse", result)
    if response.status != "success" or response.data is None:
        return None
    if not response.data.output_columns:
        return None
    return response.data.values[response.data.output_columns[0]]


def _compute_volatility_percent(dataset: object, symbol: str) -> float | None:
    """Compute the prior settled annualized volatility, as a percentage.

    Returns:
        Volatility in percent, or ``None`` if unavailable.
    """
    try:
        result = rolling_volatility(
            cast("Any", dataset),
            period=_VOLATILITY_PERIOD,
            annualization_factor=_ANNUALIZATION_FACTOR,
        )
    except Exception:  # noqa: BLE001 - one failed leg does not fail the row
        logger.debug("Volatility unavailable for overlay: %s", symbol)
        return None
    series = _first_output_series(result)
    if series is None:
        return None
    prior = _prior_settled_value(series)
    return prior * 100.0 if prior is not None else None


def _compute_adr_and_range(
    dataset: object, pip_size: float, symbol: str
) -> tuple[float | None, float | None]:
    """Compute the prior settled ADR (in pips) and today's range as % of it.

    Returns:
        ``(adr_pips, range_percent_of_adr)``, either possibly ``None``.
    """
    try:
        result = adr(cast("Any", dataset), period=_ADR_PERIOD)
    except Exception:  # noqa: BLE001 - one failed leg does not fail the row
        logger.debug("ADR unavailable for overlay: %s", symbol)
        return None, None
    series = _first_output_series(result)
    if series is None:
        return None, None
    prior_raw = _prior_settled_value(series)
    if prior_raw is None or prior_raw <= 0:
        return None, None
    today = cast("tuple[Any, ...]", getattr(dataset, "records", ()))[-1]
    today_range = float(today.high) - float(today.low)
    adr_pips = round(prior_raw / pip_size, 1)
    range_percent_of_adr = round((today_range / prior_raw) * 100.0, 1)
    return adr_pips, range_percent_of_adr


def _latest_daily_prices(
    dataset: object,
) -> tuple[float | None, float | None, float | None]:
    """Return the latest D1 open, high, and low prices.

    Args:
        dataset: Data-owned market dataset.

    Returns:
        ``(open, high, low)`` as floats, or nullable legs when absent.
    """
    records = cast("tuple[Any, ...]", getattr(dataset, "records", ()))
    if not records:
        return None, None, None
    latest = records[-1]
    try:
        return float(latest.open), float(latest.high), float(latest.low)
    except AttributeError, TypeError, ValueError:
        return None, None, None


def _build_overlay_raw(
    source_id: str, symbol: str, request_id: str
) -> TechnicalOverlay:
    """Compose one symbol's Volatility/ADR/Range overlay from D1 bars.

    Returns:
        The composed overlay, with any unavailable leg as ``None``.
    """
    pip_size = _resolve_pip_size(source_id, symbol, request_id)
    if pip_size is None or pip_size <= 0:
        return _EMPTY_OVERLAY
    dataset = _fetch_daily_bars(source_id, symbol, request_id)
    if dataset is None:
        return _EMPTY_OVERLAY
    volatility_percent = _compute_volatility_percent(dataset, symbol)
    adr_pips, range_percent_of_adr = _compute_adr_and_range(dataset, pip_size, symbol)
    open_price, high, low = _latest_daily_prices(dataset)
    return TechnicalOverlay(
        volatility_percent=volatility_percent,
        adr_pips=adr_pips,
        range_percent_of_adr=range_percent_of_adr,
        pip_size=pip_size,
        open=open_price,
        high=high,
        low=low,
    )


def build_technical_overlay(
    source_id: str, symbol: str, *, request_id: str | None = None
) -> TechnicalOverlay:
    """Return one symbol's cached-or-fresh technical overlay.

    Args:
        source_id: Owning data source identifier.
        symbol: Broker-native symbol string.
        request_id: Optional trace identifier for the underlying reads.

    Returns:
        The composed overlay, with any unavailable leg as ``None``.
    """
    key: _OverlayCacheKey = (source_id, symbol)
    now = time.monotonic()
    with _overlay_cache_lock:
        cached = _overlay_cache.get(key)
        if cached is not None and now - cached[0] < _OVERLAY_CACHE_TTL_SECONDS:
            return cached[1]
    trace_id = request_id if request_id is not None else generate_id("req")
    overlay = _build_overlay_raw(source_id, symbol, trace_id)
    # Do not negative-cache missing evidence. Provider readiness and the
    # current D1 bar can recover between requests, so caching an empty result
    # would keep the UI blank for the full positive-evidence TTL.
    if overlay != _EMPTY_OVERLAY:
        with _overlay_cache_lock:
            _overlay_cache[key] = (now, overlay)
    return overlay


__all__ = ("TechnicalOverlay", "build_technical_overlay")
