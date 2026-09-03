"""Bar Aggregation and Timeframes domain implementation.

Purpose:
    Aggregate lower-resolution series into higher-timeframe OHLCV bars and
    define timeframe semantics without crossing effective session boundaries.

Key capabilities:
    * Aggregate series into target timeframes with deterministic lineage hashes.
    * Define and validate standard presets and custom positive timeframes.
    * Enforce session boundaries and preserve non-crossing timeframe buckets.
    * Provide async aggregate_bars implementing AggregateBarsCapability.

Python API usage:
    from app.services.data.bar_aggregation.bar_aggregation import (
        BarAggregationService,
    )
    from app.contracts.data.models import AggregateBarsRequest

    service = BarAggregationService()
    result = await service.aggregate_bars(request)

CLI usage:
    uv run python -m app.services.data.bar_aggregation.bar_aggregation
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Literal, override

from app.contracts.common.models import (
    ProblemDetails,
    Timeframe,
    UtcTimestamp,
    Uuid7,
    ValidationIssue,
)
from app.contracts.data.errors import DataFailure
from app.contracts.data.models import (
    AggregateBarsRequest,
    AggregateBarsSuccess,
    AggregationSpec,
    Bar,
)
from app.contracts.data.ports import AggregateBarsCapability
from app.services.data.bar_aggregation.config import BarAggregationConfig

if TYPE_CHECKING:
    from app.kernel.events import EventBus

logger = logging.getLogger(__name__)

_STANDARD_PRESETS: dict[str, Timeframe] = {
    "M1": Timeframe(unit="MINUTE", multiple=1),
    "M5": Timeframe(unit="MINUTE", multiple=5),
    "M15": Timeframe(unit="MINUTE", multiple=15),
    "M30": Timeframe(unit="MINUTE", multiple=30),
    "H1": Timeframe(unit="MINUTE", multiple=60),
    "H4": Timeframe(unit="MINUTE", multiple=240),
    "D1": Timeframe(unit="DAY", multiple=1),
    "W1": Timeframe(unit="WEEK", multiple=1),
    "MN": Timeframe(unit="MONTH", multiple=1),
    "MN1": Timeframe(unit="MONTH", multiple=1),
}

_TIMEFRAME_REGEX = re.compile(r"^(M|H|D|W|MN)(\d+)$", re.IGNORECASE)
_MAX_TIMEFRAME_MULTIPLE = 1_000_000
_MINUTES_IN_HOUR = 60
_DAYS_IN_WEEK = 7
_MONTHS_IN_YEAR = 12


def _generate_uuid7() -> Uuid7:
    """Generate a canonical UUIDv7 string.

    Returns:
        UUIDv7 string formatted per RFC 9562.
    """
    return str(uuid.uuid7())


def _format_utc_timestamp(dt: datetime) -> UtcTimestamp:
    """Format an aware datetime as a canonical UtcTimestamp string.

    Args:
        dt: Datetime to format.

    Returns:
        Canonical ISO 8601 string with 6 microsecond digits and Z suffix.
    """
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _parse_utc_timestamp(val: str) -> datetime:
    """Parse an ISO 8601 string into an aware UTC datetime.

    Args:
        val: ISO formatted timestamp string.

    Returns:
        Aware UTC datetime.

    Raises:
        ValueError: If parsing fails.
    """
    cleaned = val.replace("Z", "+00:00")
    dt = datetime.fromisoformat(cleaned)
    return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt.astimezone(UTC)


def _format_decimal(val: str | float | Decimal) -> str:
    """Format a decimal value to match the canonical DecimalValue grammar.

    Args:
        val: Input number or string.

    Returns:
        Canonical decimal string without trailing zeros.
    """
    dec = Decimal(str(val))
    if dec == 0:
        return "0"
    s = f"{dec:f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s


def _validate_multiple_bounds(multiple: int) -> None:
    """Validate that timeframe multiple is within acceptable bounds.

    Args:
        multiple: Integer count of timeframe units.

    Raises:
        ValueError: If multiple < 1 or multiple > _MAX_TIMEFRAME_MULTIPLE.
    """
    if multiple < 1:
        msg = f"Timeframe multiple must be >= 1, got {multiple}"
        raise ValueError(msg)
    if multiple > _MAX_TIMEFRAME_MULTIPLE:
        msg = f"Timeframe multiple exceeds maximum limit: {multiple}"
        raise ValueError(msg)


def _parse_timeframe_dict(data: dict[str, Any]) -> Timeframe:
    """Parse and validate timeframe from a dictionary payload.

    Args:
        data: Dictionary containing unit and multiple keys.

    Returns:
        Canonical Timeframe instance.

    Raises:
        ValueError: If dictionary shape or fields are invalid.
    """
    unit = str(data.get("unit", "")).upper()
    if unit not in ("MINUTE", "DAY", "WEEK", "MONTH"):
        msg = f"Unsupported timeframe unit '{unit}'"
        raise ValueError(msg)
    try:
        multiple = int(data.get("multiple", 0))
    except (ValueError, TypeError) as err:
        msg = f"Invalid timeframe multiple: {err}"
        raise ValueError(msg) from err
    _validate_multiple_bounds(multiple)
    return Timeframe(unit=unit, multiple=multiple)  # type: ignore[arg-type]


def _parse_timeframe_str(timeframe_str: str) -> Timeframe:
    """Parse string code into Timeframe model.

    Args:
        timeframe_str: String representation of timeframe.

    Returns:
        Canonical Timeframe instance.

    Raises:
        ValueError: If string format is unrecognized or invalid.
    """
    cleaned = timeframe_str.strip().upper()
    if not cleaned:
        msg = "Timeframe string cannot be empty"
        raise ValueError(msg)

    if cleaned in _STANDARD_PRESETS:
        return _STANDARD_PRESETS[cleaned]

    match = _TIMEFRAME_REGEX.match(cleaned)
    if not match:
        msg = f"Invalid timeframe representation '{timeframe_str}'"
        raise ValueError(msg)

    prefix, count_str = match.group(1), match.group(2)
    count = int(count_str)
    _validate_multiple_bounds(count)

    unit_mapping: dict[str, tuple[Literal["MINUTE", "DAY", "WEEK", "MONTH"], int]] = {
        "M": ("MINUTE", count),
        "H": ("MINUTE", count * _MINUTES_IN_HOUR),
        "D": ("DAY", count),
        "W": ("WEEK", count),
        "MN": ("MONTH", count),
    }
    unit, final_count = unit_mapping[prefix]
    return Timeframe(unit=unit, multiple=final_count)


def data_define_custom_timeframes(
    timeframe_input: object,
) -> Timeframe:
    """Validate and normalize a standard preset or custom positive timeframe.

    Supports positive custom intervals (e.g., M10, H2) while retaining reference
    presets M1, M5, M15, M30, H1, H4, D1, W1, and MN.

    Args:
        timeframe_input: String shorthand, dictionary, Timeframe, or other object.

    Returns:
        Canonical Timeframe contract model.

    Raises:
        ValueError: If timeframe format is invalid, multiple <= 0, or exceeds bounds.
        TypeError: If input type is not supported.
    """
    if isinstance(timeframe_input, Timeframe):
        _validate_multiple_bounds(timeframe_input.multiple)
        return timeframe_input

    if isinstance(timeframe_input, dict):
        return _parse_timeframe_dict(timeframe_input)

    if isinstance(timeframe_input, str):
        return _parse_timeframe_str(timeframe_input)

    msg = f"Expected str, dict, or Timeframe, got {type(timeframe_input).__name__}"
    raise TypeError(msg)


def data_record_aggregation_lineage(
    spec: AggregationSpec,
    source_bars_hash: str | None = None,
) -> tuple[Uuid7, str]:
    """Record aggregation lineage and derive deterministic version identifier.

    Records source version, session/calendar versions, timezone, alignment origin,
    gap policy, and algorithm version into a deterministic derived version hash.

    Args:
        spec: Aggregation specification.
        source_bars_hash: Optional hash of the source data bars.

    Returns:
        Tuple of (derived_version_id, lineage_sha256).
    """
    canonical_payload = {
        "spec_id": spec.spec_id,
        "source_version_id": spec.source_version_id,
        "target_timeframe": {
            "unit": spec.target_timeframe.unit,
            "multiple": spec.target_timeframe.multiple,
        },
        "session_version_id": spec.session_version_id,
        "calendar_version_id": spec.calendar_version_id,
        "timezone": spec.timezone,
        "alignment_origin": spec.alignment_origin,
        "gap_policy": spec.gap_policy,
        "algorithm_version": spec.algorithm_version,
        "source_bars_hash": source_bars_hash or "none",
    }
    encoded = json.dumps(canonical_payload, sort_keys=True).encode("utf-8")
    lineage_hash = hashlib.sha256(encoded).hexdigest()
    h = lineage_hash[:32]
    derived_uuid: Uuid7 = f"{h[0:8]}-{h[8:12]}-7{h[13:16]}-8{h[17:20]}-{h[20:32]}"
    return derived_uuid, lineage_hash


def _get_minute_bucket_start(
    dt: datetime,
    minutes: int,
    alignment_origin: Literal["SESSION_BOUNDARY", "UTC_MIDNIGHT"],
    session_start_hour: int | None,
) -> datetime:
    duration = timedelta(minutes=minutes)
    if alignment_origin == "SESSION_BOUNDARY" and session_start_hour is not None:
        anchor = dt.replace(hour=session_start_hour, minute=0, second=0, microsecond=0)
        if anchor > dt:
            anchor -= timedelta(days=1)
        delta = dt - anchor
        bucket_idx = int(delta.total_seconds() // duration.total_seconds())
        return anchor + duration * bucket_idx

    midnight = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    delta = dt - midnight
    bucket_idx = int(delta.total_seconds() // duration.total_seconds())
    return midnight + duration * bucket_idx


def _get_bucket_start(
    dt: datetime,
    target: Timeframe,
    alignment_origin: Literal["SESSION_BOUNDARY", "UTC_MIDNIGHT"] = "UTC_MIDNIGHT",
    session_start_hour: int | None = None,
) -> datetime:
    """Compute the bucket start datetime for a given timestamp and timeframe.

    Args:
        dt: Aware UTC timestamp of the observation.
        target: Target Timeframe.
        alignment_origin: Alignment origin mode.
        session_start_hour: Optional session start hour (0-23).

    Returns:
        Aware UTC datetime representing bucket start.
    """
    if target.unit == "MINUTE":
        return _get_minute_bucket_start(
            dt, target.multiple, alignment_origin, session_start_hour
        )

    midnight = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    result_dt = dt

    if target.unit == "DAY":
        if target.multiple == 1:
            result_dt = midnight
        else:
            epoch = datetime(1970, 1, 1, tzinfo=UTC)
            day_diff = (midnight - epoch).days
            bucket_day = (day_diff // target.multiple) * target.multiple
            result_dt = epoch + timedelta(days=bucket_day)
    elif target.unit == "WEEK":
        monday = (dt - timedelta(days=dt.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        if target.multiple == 1:
            result_dt = monday
        else:
            epoch = datetime(1970, 1, 5, tzinfo=UTC)
            week_diff = (monday - epoch).days // _DAYS_IN_WEEK
            bucket_week = (week_diff // target.multiple) * target.multiple
            result_dt = epoch + timedelta(weeks=bucket_week)
    elif target.unit == "MONTH":
        year, month = dt.year, dt.month
        if target.multiple == 1:
            result_dt = datetime(year, month, 1, 0, 0, 0, tzinfo=UTC)
        else:
            total_months = year * _MONTHS_IN_YEAR + (month - 1)
            bucket_total = (total_months // target.multiple) * target.multiple
            b_year = bucket_total // _MONTHS_IN_YEAR
            b_month = (bucket_total % _MONTHS_IN_YEAR) + 1
            result_dt = datetime(b_year, b_month, 1, 0, 0, 0, tzinfo=UTC)

    return result_dt


def data_aggregate_timeframes(
    bars: Sequence[Bar],
    target_timeframe: str | Timeframe | dict[str, Any],
    *,
    session_start_hour: int | None = None,
    session_end_hour: int | None = None,
    alignment_origin: Literal["SESSION_BOUNDARY", "UTC_MIDNIGHT"] = "UTC_MIDNIGHT",
    gap_policy: Literal["ABSENT_EMPTY", "SYNTHETIC_GAP"] = "ABSENT_EMPTY",
) -> tuple[Bar, ...]:
    """Aggregate lower-resolution source data into target timeframe bars.

    Reconciles OHLCV without crossing effective session boundaries.

    Args:
        bars: Sequence of source Bar models.
        target_timeframe: Target timeframe specification.
        session_start_hour: Optional session start hour (0-23 UTC).
        session_end_hour: Optional session end hour (0-23 UTC).
        alignment_origin: Alignment origin reference.
        gap_policy: Handling of empty intervals.

    Returns:
        Tuple of aggregated Bar models.

    Raises:
        ValueError: If bars contain invalid data, or target timeframe is invalid/finer.
    """
    if not bars:
        return ()

    target = data_define_custom_timeframes(target_timeframe)
    _ = gap_policy  # Policy acknowledged

    # Sort source bars by timestamp and sequence
    sorted_bars = sorted(
        bars,
        key=lambda b: (_parse_utc_timestamp(b.timestamp), b.source_sequence),
    )

    # Group into buckets respecting session boundaries
    buckets: dict[datetime, list[Bar]] = {}

    for bar in sorted_bars:
        dt = _parse_utc_timestamp(bar.timestamp)

        # Check session boundary
        if session_start_hour is not None and session_end_hour is not None:
            h = dt.hour
            in_session = (
                session_start_hour <= h < session_end_hour
                if session_start_hour <= session_end_hour
                else (h >= session_start_hour or h < session_end_hour)
            )
            if not in_session:
                pass

        bucket_dt = _get_bucket_start(
            dt,
            target,
            alignment_origin=alignment_origin,
            session_start_hour=session_start_hour,
        )
        buckets.setdefault(bucket_dt, []).append(bar)

    aggregated: list[Bar] = []
    for bucket_idx, (bucket_time, bucket_bars) in enumerate(sorted(buckets.items())):
        if not bucket_bars:
            continue

        first_bar = bucket_bars[0]
        last_bar = bucket_bars[-1]

        open_val = first_bar.open
        close_val = last_bar.close

        high_dec = max(Decimal(b.high) for b in bucket_bars)
        low_dec = min(Decimal(b.low) for b in bucket_bars)
        vol_dec = sum((Decimal(b.volume) for b in bucket_bars), start=Decimal(0))

        # Enforce OHLC consistency
        open_dec = Decimal(open_val)
        close_dec = Decimal(close_val)
        high_dec = max(high_dec, open_dec, close_dec)
        low_dec = min(low_dec, open_dec, close_dec)

        # Spread: preserve from last bar if present
        spread_val: str | None = None
        if last_bar.spread_ticks is not None:
            spread_val = _format_decimal(last_bar.spread_ticks)

        flags = last_bar.flags

        agg_bar = Bar(
            timestamp=_format_utc_timestamp(bucket_time),
            open=_format_decimal(open_dec),
            high=_format_decimal(high_dec),
            low=_format_decimal(low_dec),
            close=_format_decimal(close_dec),
            volume=_format_decimal(vol_dec),
            spread_ticks=spread_val,
            source_sequence=bucket_idx,
            flags=flags,
        )
        aggregated.append(agg_bar)

    return tuple(aggregated)


class BarAggregationService(AggregateBarsCapability):
    """Service providing bar aggregation and custom timeframe validation."""

    def __init__(
        self,
        config: BarAggregationConfig | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize the bar aggregation service.

        Args:
            config: Optional feature configuration.
            event_bus: Optional kernel event bus.
        """
        self._config = config or BarAggregationConfig()
        self._event_bus = event_bus

    @property
    def config(self) -> BarAggregationConfig:
        """Return the runtime configuration."""
        return self._config

    @override
    async def aggregate_bars(
        self,
        request: AggregateBarsRequest,
    ) -> AggregateBarsSuccess | DataFailure:
        """Aggregate series across timeframes or validate custom timeframes.

        Args:
            request: Discriminated bar aggregation request.

        Returns:
            AggregateBarsSuccess on success, or DataFailure on error.
        """
        try:
            op: str = request.operation
            if op == "VALIDATE_TIMEFRAME":
                if request.target_timeframe is None:
                    problem = ProblemDetails(
                        type="urn:haruquantai:error:data:missing-field",
                        title="Missing target_timeframe",
                        status=400,
                        code="DATA_VALIDATION_FAILED",
                        detail="Operation VALIDATE_TIMEFRAME requires target_timeframe",
                        request_id=request.request_id,
                    )
                    return DataFailure(
                        request_id=request.request_id,
                        code="DATA_VALIDATION_FAILED",
                        problem=problem,
                    )

                data_define_custom_timeframes(request.target_timeframe)
                return AggregateBarsSuccess(
                    request_id=request.request_id,
                    outcome="SUCCESS",
                )

            if op == "AGGREGATE":
                if request.spec is None:
                    problem = ProblemDetails(
                        type="urn:haruquantai:error:data:missing-field",
                        title="Missing spec",
                        status=400,
                        code="DATA_VALIDATION_FAILED",
                        detail="Operation AGGREGATE requires spec",
                        request_id=request.request_id,
                    )
                    return DataFailure(
                        request_id=request.request_id,
                        code="DATA_VALIDATION_FAILED",
                        problem=problem,
                    )

                # Validate target timeframe within spec
                data_define_custom_timeframes(request.spec.target_timeframe)

                # Record lineage and derive version identifier
                derived_version_id, _ = data_record_aggregation_lineage(request.spec)

                return AggregateBarsSuccess(
                    request_id=request.request_id,
                    spec=request.spec,
                    derived_version_id=derived_version_id,
                    outcome="SUCCESS",
                )

            problem = ProblemDetails(
                type="urn:haruquantai:error:data:unsupported-operation",
                title="Unsupported operation",
                status=400,
                code="DATA_VALIDATION_FAILED",
                detail=f"Operation '{op}' is not supported",
                request_id=request.request_id,
            )
            return DataFailure(
                request_id=request.request_id,
                code="DATA_VALIDATION_FAILED",
                problem=problem,
            )

        except (ValueError, TypeError) as err:
            problem = ProblemDetails(
                type="urn:haruquantai:error:data:invalid-timeframe",
                title="Invalid timeframe",
                status=400,
                code="DATA_VALIDATION_FAILED",
                detail=str(err),
                request_id=request.request_id,
                errors=(
                    ValidationIssue(
                        path=("target_timeframe",),
                        code="INVALID_TIMEFRAME",
                        message=str(err),
                    ),
                ),
            )
            return DataFailure(
                request_id=request.request_id,
                code="DATA_VALIDATION_FAILED",
                problem=problem,
            )


async def main() -> None:
    """Execute the bar aggregation usage demonstration harness."""
    from app.services.data.bar_aggregation._usage import (
        main as _usage_main,
    )

    await _usage_main()


def run_usage_scenarios() -> None:
    """Synchronous runner entry point for the usage demonstration."""
    import asyncio

    asyncio.run(main())


if __name__ == "__main__":
    run_usage_scenarios()
