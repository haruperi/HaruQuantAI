"""Closed-bar returns construction and alignment services."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from datetime import datetime
from decimal import Decimal
from typing import Any, overload

from app.services.risk.correlation.contracts import (
    AlignedReturns,
    ClosedBar,
    CorrelationAlignmentPolicy,
    ReturnMethod,
    ReturnSeries,
)
from app.utils.errors import ValidationError
from app.utils.logger import logger

MIN_BARS_FOR_RETURNS = 2
MIN_SAMPLES_FOR_PEARSON = 2


def _parse_bar_fields(
    bar: dict[str, Any] | object,
) -> tuple[datetime, Decimal, Decimal]:
    """Parse opening time, open price, and close price from a bar dict or object."""
    if isinstance(bar, dict):
        time_val = bar.get("time") or bar.get("timestamp")
        open_val = bar.get("open")
        close_val = bar.get("close")
    else:
        time_val = getattr(bar, "time", None) or getattr(bar, "timestamp", None)
        open_val = getattr(bar, "open", None)
        close_val = getattr(bar, "close", None)

    if time_val is None or open_val is None or close_val is None:
        msg = f"Missing required fields (time, open, close) in bar: {bar}"
        raise ValidationError(msg)

    if isinstance(time_val, str):
        try:
            from app.utils.normalization import to_utc_datetime

            dt = to_utc_datetime(time_val)
        except (ValueError, TypeError, AttributeError):
            dt = datetime.fromisoformat(time_val)
    elif isinstance(time_val, datetime):
        dt = time_val
    else:
        dt = datetime.fromtimestamp(float(time_val), datetime.now().astimezone().tzinfo)

    return dt, Decimal(str(open_val)), Decimal(str(close_val))


def _calculate_open_to_close(
    parsed_bars: list[tuple[datetime, Decimal, Decimal]],
) -> dict[datetime, Decimal]:
    """Compute open-to-close returns."""
    returns = {}
    for dt, o, c in parsed_bars:
        returns[dt] = (c - o) / o if o != 0 else Decimal("0.0")
    return returns


def _calculate_close_to_close(
    parsed_bars: list[tuple[datetime, Decimal, Decimal]],
) -> dict[datetime, Decimal]:
    """Compute close-to-close returns."""
    returns = {}
    for i in range(1, len(parsed_bars)):
        dt = parsed_bars[i][0]
        prev_c = parsed_bars[i - 1][2]
        curr_c = parsed_bars[i][2]
        returns[dt] = (curr_c - prev_c) / prev_c if prev_c != 0 else Decimal("0.0")
    return returns


def _calculate_log(
    parsed_bars: list[tuple[datetime, Decimal, Decimal]],
) -> dict[datetime, Decimal]:
    """Compute logarithmic returns."""
    returns = {}
    for i in range(1, len(parsed_bars)):
        dt = parsed_bars[i][0]
        prev_c = parsed_bars[i - 1][2]
        curr_c = parsed_bars[i][2]
        if prev_c <= 0 or curr_c <= 0:
            returns[dt] = Decimal("0.0")
        else:
            ratio = float(curr_c / prev_c)
            returns[dt] = Decimal(str(math.log(ratio)))
    return returns


def _calculate_sigma_normalized(
    parsed_bars: list[tuple[datetime, Decimal, Decimal]],
) -> dict[datetime, Decimal]:
    """Compute standard-deviation normalized returns."""
    raw_rets = []
    dts = []
    for i in range(1, len(parsed_bars)):
        dt = parsed_bars[i][0]
        prev_c = parsed_bars[i - 1][2]
        curr_c = parsed_bars[i][2]
        val = (curr_c - prev_c) / prev_c if prev_c != 0 else Decimal("0.0")
        raw_rets.append(val)
        dts.append(dt)

    if not raw_rets:
        return {}

    n = len(raw_rets)
    mean_val = sum(raw_rets, Decimal("0.0")) / Decimal(n)
    var_val = sum(((r - mean_val) ** 2 for r in raw_rets), Decimal("0.0")) / Decimal(n)
    std_val = Decimal(str(math.sqrt(float(var_val))))

    returns = {}
    if std_val == 0:
        for dt in dts:
            returns[dt] = Decimal("0.0")
    else:
        for dt, r in zip(dts, raw_rets, strict=True):
            returns[dt] = r / std_val
    return returns


def _compute_returns(
    parsed_bars: list[tuple[datetime, Decimal, Decimal]], method: ReturnMethod
) -> dict[datetime, Decimal]:
    """Route returns computation to specific formula."""
    if method == ReturnMethod.OPEN_TO_CLOSE:
        return _calculate_open_to_close(parsed_bars)
    if len(parsed_bars) < MIN_BARS_FOR_RETURNS:
        return {}
    if method == ReturnMethod.CLOSE_TO_CLOSE:
        return _calculate_close_to_close(parsed_bars)
    if method == ReturnMethod.LOG:
        return _calculate_log(parsed_bars)
    if method == ReturnMethod.SIGMA_NORMALIZED:
        return _calculate_sigma_normalized(parsed_bars)
    return {}


def build_return_series(
    bars: Sequence[ClosedBar] | list[Any], method: ReturnMethod
) -> ReturnSeries:
    """Derive return series from bars.

    Args:
        bars: Historical closed bars.
        method: Method to calculate returns (e.g. log, close_to_close).

    Returns:
        ReturnSeries: Calculated returns.
    """
    logger.info("build_return_series called for method %s.", method)
    parsed_bars: list[tuple[datetime, Decimal, Decimal]] = []
    for bar in bars:
        if isinstance(bar, ClosedBar):
            parsed_bars.append((bar.time, bar.open, bar.close))
        elif isinstance(bar, tuple) and len(bar) == 3:  # noqa: PLR2004
            parsed_bars.append(bar)
        else:
            try:
                parsed_bars.append(_parse_bar_fields(bar))
            except ValidationError:
                continue

    parsed_bars.sort(key=lambda x: x[0])
    rets = _compute_returns(parsed_bars, method)

    symbol = ""
    if bars and hasattr(bars[0], "symbol"):
        symbol = str(bars[0].symbol)

    return ReturnSeries(symbol=symbol, returns=rets)


@overload
def align_return_series(
    returns_a: dict[datetime, Decimal],
    returns_b: dict[datetime, Decimal],
) -> tuple[list[Decimal], list[Decimal]]: ...


@overload
def align_return_series(
    series: Mapping[str, ReturnSeries],
    policy: CorrelationAlignmentPolicy,
) -> AlignedReturns: ...


def align_return_series(*args: Any, **_kwargs: Any) -> Any:
    """Align return series by identical timestamps.

    Supports both:
    1. V1 signature: (returns_a, returns_b) -> (aligned_a, aligned_b)
    2. V2 signature: (series_map, policy) -> AlignedReturns
    """
    logger.debug("align_return_series called.")
    if (
        len(args) == 2  # noqa: PLR2004
        and isinstance(args[0], dict)
        and isinstance(args[1], dict)
    ):
        # V1 logic
        returns_a = args[0]
        returns_b = args[1]
        common_keys = sorted(set(returns_a.keys()) & set(returns_b.keys()))
        aligned_a = [returns_a[k] for k in common_keys]
        aligned_b = [returns_b[k] for k in common_keys]
        return aligned_a, aligned_b

    # V2 logic
    series_map: Mapping[str, ReturnSeries] = args[0]
    policy: CorrelationAlignmentPolicy = args[1]
    _ = policy

    common_keys_v2: set[datetime] | None = None
    for s in series_map.values():
        times = set(s.returns.keys())
        if common_keys_v2 is None:
            common_keys_v2 = times
        else:
            common_keys_v2 &= times

    sorted_keys = sorted(common_keys_v2) if common_keys_v2 else []
    aligned_returns = {}
    for symbol, s in series_map.items():
        aligned_returns[symbol] = [s.returns[t] for t in sorted_keys]

    return AlignedReturns(timestamps=sorted_keys, returns=aligned_returns)


def validate_correlation_inputs(
    aligned: AlignedReturns, minimum_samples: int
) -> dict[str, Any]:
    """Validate that aligned return series meet requirements.

    Args:
        aligned: Aligned return series matrix.
        minimum_samples: Required sample count threshold.

    Returns:
        dict[str, Any]: Validation result representation.
    """
    logger.info("Validating correlation inputs against sample threshold.")
    count = len(aligned.timestamps)
    if count < minimum_samples:
        msg = f"Insufficient aligned sample size ({count} < {minimum_samples})."
        logger.warning(msg)
        return {"valid": False, "reason": msg, "details": {"sample_count": count}}

    return {"valid": True, "reason": "Input sample count is sufficient.", "details": {}}


def calculate_returns(
    bars: list[Any],
    return_type: str,
    exclude_last: bool = True,
) -> dict[datetime, Decimal]:
    """Calculate returns series for a list of bars (V1 compatibility wrapper)."""
    logger.info("calculate_returns wrapper called.")
    if not bars:
        return {}

    parsed_bars = []
    for bar in bars:
        try:
            parsed_bars.append(_parse_bar_fields(bar))
        except ValidationError:
            continue

    parsed_bars.sort(key=lambda x: x[0])
    if exclude_last and parsed_bars:
        parsed_bars.pop()

    try:
        method = ReturnMethod(return_type)
    except ValueError as e:
        err_msg = f"Unsupported return type: {return_type}"
        raise ValueError(err_msg) from e

    ret_series = build_return_series(parsed_bars, method)
    return dict(ret_series.returns)


def calculate_pearson(x: Sequence[Decimal], y: Sequence[Decimal]) -> Decimal:
    """Calculate Pearson correlation coefficient between two aligned list series."""
    logger.debug("Calculating Pearson correlation coefficient.")
    n = len(x)
    if n < MIN_SAMPLES_FOR_PEARSON:
        return Decimal("0.0")

    mean_x = sum(x, Decimal("0.0")) / Decimal(n)
    mean_y = sum(y, Decimal("0.0")) / Decimal(n)

    diff_x = [val - mean_x for val in x]
    diff_y = [val - mean_y for val in y]

    numerator = sum(dx * dy for dx, dy in zip(diff_x, diff_y, strict=True))
    denom_x = sum(dx * dx for dx in diff_x)
    denom_y = sum(dy * dy for dy in diff_y)

    if denom_x == 0 or denom_y == 0:
        return Decimal("0.0")

    denom = Decimal(str(math.sqrt(float(denom_x * denom_y))))
    if denom == 0:
        return Decimal("0.0")

    return numerator / denom
