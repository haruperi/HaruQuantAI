"""Limits, precision, and timeframe validation rules.

Consolidates the functionality of limits, precision, and timeframe logic into a
single data-validation layer.
"""

from __future__ import annotations

import zoneinfo
from collections.abc import Iterable
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Protocol

from app.services.utils.errors import ValidationError
from app.services.utils.logger import logger


class BarProtocol(Protocol):
    """Protocol for bar-like objects validated by the data service."""

    open_time: datetime


# --- 1. Limits Rules ---
DEFAULT_OHLCV_LIMIT: int = 5000
MAX_OHLCV_LIMIT: int = 50000

DEFAULT_TICK_LIMIT: int = 10000
MAX_TICK_LIMIT: int = 250000

DEFAULT_SPREAD_LIMIT: int = 10000
MAX_SPREAD_LIMIT: int = 250000

MAX_SYNTHETIC_BARS: int = 100000
MAX_SYNTHETIC_TICKS: int = 250000
MAX_PERSISTED_SYNTHETIC_SIZE: int = 1000000

DEFAULT_BACKFILL_OHLCV_CHUNK_RECORDS: int = 100000
DEFAULT_BACKFILL_OHLCV_CHUNK_DAYS: int = 30

DEFAULT_BACKFILL_TICK_CHUNK_RECORDS: int = 1000000
DEFAULT_BACKFILL_TICK_CHUNK_DAYS: int = 1

DEFAULT_CACHE_TTL_DAILY: int = 86400
DEFAULT_CACHE_TTL_INTRADAY: int = 3600
DEFAULT_CACHE_TTL_TICK: int = 900
DEFAULT_CACHE_TTL_LIVE: int = 0
MAX_CACHE_TTL_OVERRIDE_DAYS: int = 7

MAX_SYMBOLS_PER_JOB: int = 500
MAX_TIMEFRAMES_PER_JOB: int = 20
MIN_SCHEDULER_FREQUENCY_SECONDS: int = 60


def validate_limit(limit: int | None, max_allowed: int, default_value: int) -> int:
    """Description.
        Validate and return a query limit.

    Args:
        limit: int | None.
        max_allowed: int.
        default_value: int.

    Returns:
        int.
    """
    if limit is None:
        return default_value

    if limit <= 0:
        logger.error(f"Requested limit {limit} is non-positive.")
        raise ValidationError("Requested limit must be positive.")

    if limit > max_allowed:
        err_msg = (
            f"Requested limit {limit} exceeds maximum allowed limit {max_allowed}."
        )
        logger.error(err_msg)
        raise ValidationError(err_msg)
    logger.debug(f"Validated limit: {limit}.")
    return limit


# --- 2. Precision Rounding Policies ---
NumericType = int | float | str | Decimal


def normalize_numeric(
    value: NumericType, digits: int, workflow_context: str
) -> str | float:
    """Description.
        Normalize numeric values according to workflow rules.

    Args:
        value: NumericType.
        digits: int.
        workflow_context: str.

    Returns:
        str | float.
    """
    if value is None:
        raise ValidationError("Numeric value cannot be None.")

    try:
        dec_val = Decimal(str(value))
    except Exception as e:
        err_msg = f"Failed to convert value {value} to Decimal: {e}"
        logger.error(err_msg)
        raise ValidationError(err_msg) from e

    # Quantize using ROUND_HALF_UP
    quant_str = f"1.{'0' * digits}" if digits > 0 else "1"
    quantized = dec_val.quantize(Decimal(quant_str), rounding=ROUND_HALF_UP)

    if workflow_context in (
        "backtest",
        "validation",
        "risk",
        "execution_bound",
    ):
        logger.debug(
            f"Normalized value: {value} -> {quantized:.{digits}f} for workflow context {workflow_context}."
        )
        return f"{quantized:.{digits}f}"

    return float(quantized)


def validate_step_alignment(
    value: NumericType, step_size: NumericType, workflow_context: str
) -> None:
    """Description.
        Validate that a value aligns perfectly with the allowed step size.

    Args:
        value: NumericType.
        step_size: NumericType.
        workflow_context: str.

    Returns:
        None.
    """
    if value is None or step_size is None:
        raise ValidationError("Value and step size must be defined.")

    try:
        dec_val = Decimal(str(value))
        dec_step = Decimal(str(step_size))
    except Exception as e:
        err_conv = (
            f"Failed step alignment conversion. value={value}, step={step_size}: {e}"
        )
        logger.error(err_conv)
        raise ValidationError("Invalid numeric/step conversion.") from e

    if dec_step <= 0:
        raise ValidationError("Step size must be strictly positive.")

    remainder = dec_val % dec_step
    tolerance = Decimal("1e-9")
    if remainder > tolerance and (dec_step - remainder) > tolerance:
        warn_msg = (
            f"Precision mismatch detected: value={value} "
            f"is not a multiple of step={step_size}"
        )
        logger.warning(warn_msg)
        if workflow_context in ("risk", "execution_bound"):
            err_msg = (
                f"Precision mismatch. value {value} "
                f"does not align with step {step_size}."
            )
            raise ValidationError(err_msg)
    logger.debug(
        f"Validated step alignment: value={value}, step={step_size} for workflow context {workflow_context}."
    )


# --- 3. Timeframes & Sessions ---
VALID_TIMEFRAMES: set[str] = {
    "M1",
    "M2",
    "M3",
    "M4",
    "M5",
    "M6",
    "M10",
    "M12",
    "M15",
    "M20",
    "M30",
    "H1",
    "H2",
    "H3",
    "H4",
    "H6",
    "H8",
    "H12",
    "D1",
    "W1",
    "MN1",
}


def validate_timeframe(timeframe: str) -> str:
    """Description.
        Validate that a timeframe name is supported.

    Args:
        timeframe: str.

    Returns:
        str.
    """
    if not timeframe:
        raise ValidationError("Timeframe cannot be empty.")

    upper_tf = timeframe.upper()
    if upper_tf not in VALID_TIMEFRAMES:
        err_msg = f"Unsupported timeframe: {timeframe}"
        logger.error(err_msg)
        raise ValidationError(err_msg)
    logger.debug(f"Validated timeframe: {timeframe} -> {upper_tf}.")
    return upper_tf


def validate_timezone(tz_name: str) -> str:
    """Description.
        Validate that a timezone string is a valid IANA timezone.

    Args:
        tz_name: str.

    Returns:
        str.
    """
    try:
        zoneinfo.ZoneInfo(tz_name)
    except Exception as e:
        err_msg = f"Invalid timezone: {tz_name}"
        logger.error(f"Invalid IANA timezone name {tz_name}: {e}")
        raise ValidationError(err_msg) from e
    logger.debug(f"Validated timezone: {tz_name}.")
    return tz_name


def validate_bars(
    bars: Iterable[BarProtocol],
) -> tuple[BarProtocol, ...]:
    """Description.
        Return bars as an increasing, non-empty tuple after validation.

    Args:
        bars: Iterable[BarProtocol].

    Returns:
        tuple[BarProtocol, ...].
    """
    normalized = tuple(bars)
    if not normalized:
        raise ValueError("At least one OHLCV bar is required.")
    previous: datetime | None = None
    for bar in normalized:
        if previous is not None and bar.open_time <= previous:
            raise ValueError(
                "Bar open times must be strictly increasing with no duplicates."
            )
        previous = bar.open_time
    logger.debug(
        f"Validated {len(normalized)} OHLCV bars for strict chronological order."
    )
    return normalized


__all__ = [
    "BarProtocol",
    "normalize_numeric",
    "validate_bars",
    "validate_limit",
    "validate_step_alignment",
    "validate_timeframe",
    "validate_timezone",
]
