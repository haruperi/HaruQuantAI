"""Temporal truth for the DATA domain: timeframes and UTC normalization.

Moved from ``transforms/timeframes.py`` by ``CAP-DATA-026``. The timeframe manifest is
not a transform â€” it is the definition of what a timeframe *is*, consumed by
resampling, aggregation, quality gap detection, and tick generation alike. Hosting it
under ``time`` gives every temporal fact one owner.

This module was pulled forward from Phase 6 into Phase 4 because it is a dependency-free
leaf (it imports only ``errors``) and tick generation needs it. Deferring it would have
required pinning a fourth legacy import.

``time/market_hours.py`` and ``time/gaps.py`` remain Phase 6: the former derives from
leaf (it imports only ``errors``) and tick generation needs it. Deferring it would have
"""

from collections.abc import Mapping
from datetime import timedelta
from typing import Final, NamedTuple

from app.services.data.contracts import DataError
from app.services.data.contracts.responses import (
    StandardResponse,
    data_start_time,
    run_data_operation,
)
from app.utils import generate_id, get_logger

logger = get_logger(__name__)


class TimeframeSpec(NamedTuple):
    """Specification of a canonical market timeframe.

    Attributes:
        key: The timeframe key (e.g. "M1", "D1").
        duration: The timedelta representing the timeframe size.
        pandas_freq: The pandas resampling frequency string.
        rank: An ordering rank to validate up-sampling/down-sampling directions.
    """

    key: str
    duration: timedelta
    pandas_freq: str
    rank: int


TIMEFRAME_MANIFEST: Final[Mapping[str, TimeframeSpec]] = {
    "M1": TimeframeSpec("M1", timedelta(minutes=1), "1min", 1),
    "M5": TimeframeSpec("M5", timedelta(minutes=5), "5min", 2),
    "M15": TimeframeSpec("M15", timedelta(minutes=15), "15min", 3),
    "M30": TimeframeSpec("M30", timedelta(minutes=30), "30min", 4),
    "H1": TimeframeSpec("H1", timedelta(hours=1), "1h", 5),
    "H4": TimeframeSpec("H4", timedelta(hours=4), "4h", 6),
    "D1": TimeframeSpec("D1", timedelta(days=1), "1d", 7),
    "W1": TimeframeSpec("W1", timedelta(weeks=1), "1W", 8),
    "MN1": TimeframeSpec("MN1", timedelta(days=30), "1ME", 9),
}


def _get_timeframe_spec_raw(key: str) -> TimeframeSpec:
    """Retrieve the spec for a timeframe key, raising if unsupported.

    Args:
        key: The ``key`` argument.

    Returns:
        The result produced by the operation.

    Raises:
        DataError: If the timeframe key is not supported.
    """
    logger.info("Retrieving timeframe spec for key: %s", key)
    if key not in TIMEFRAME_MANIFEST:
        raise DataError(
            "UNSUPPORTED_TIMEFRAME",
            safe_details={"timeframe": key},
        )
    return TIMEFRAME_MANIFEST[key]


def get_timeframe_spec(key: str) -> StandardResponse[TimeframeSpec]:
    """Retrieve the spec for a timeframe key, raising if unsupported.

    Args:
        key: The timeframe key to lookup.

    Returns:
        Standard response carrying the matching TimeframeSpec.

    Raises:
        (in-band) ``UNSUPPORTED_TIMEFRAME`` when the key is not supported.
    """
    return run_data_operation(
        operation="data.time_sessions.get_timeframe_spec",
        request_id=generate_id("req"),
        start_time=data_start_time(),
        raw=lambda: _get_timeframe_spec_raw(key),
    )


def _validate_resample_target_raw(source_key: str | None, target_key: str) -> None:
    """Validate that the target timeframe is strictly higher than the source.

    Args:
        source_key: The ``source_key`` argument.
        target_key: The ``target_key`` argument.

    Raises:
        DataError: If validation fails.
    """
    logger.info(
        "Validating resample target from source %s to target %s",
        source_key,
        target_key,
    )
    if source_key is None:
        raise DataError(
            "VALIDATION_FAILED",
            safe_details={
                "message": ("Resampling source dataset must have a valid timeframe.")
            },
        )

    source_spec = _get_timeframe_spec_raw(source_key)
    target_spec = _get_timeframe_spec_raw(target_key)

    if target_spec.rank <= source_spec.rank:
        raise DataError(
            "VALIDATION_FAILED",
            safe_details={
                "message": (
                    f"Target timeframe '{target_key}' must be "
                    f"strictly higher than source timeframe '{source_key}'."
                )
            },
        )


def validate_resample_target(
    source_key: str | None, target_key: str
) -> StandardResponse[None]:
    """Validate that the target timeframe is strictly higher than the source.

    Args:
        source_key: The timeframe key of the source dataset, if any.
        target_key: The timeframe key of the target resampled dataset.

    Returns:
        Standard response carrying ``None`` on success.

    Raises:
        (in-band) ``VALIDATION_FAILED`` or ``UNSUPPORTED_TIMEFRAME`` on failure.
    """
    return run_data_operation(
        operation="data.time_sessions.validate_resample_target",
        request_id=generate_id("req"),
        start_time=data_start_time(),
        raw=lambda: _validate_resample_target_raw(source_key, target_key),
    )
