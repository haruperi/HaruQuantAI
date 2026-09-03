"""External Series Alignment domain implementation.

Purpose:
    Align heterogeneous time series into aligned timeline frames using explicit
    lookahead-free forward-fill, exact matching, or rejection policies.

Key capabilities:
    * Align secondary series onto primary timeline anchors without lookahead bias.
    * Enforce maximum age boundaries and missing data imputation strategies.
    * Perform multi-series timeline merges with deterministic point ordering.
    * Provide async align_series implementing AlignSeriesCapability.

Python API usage:
    from app.services.data.external_series_alignment.external_series_alignment import (
        ExternalSeriesAlignmentService,
    )
    from app.contracts.data.models import AlignSeriesRequest

    service = ExternalSeriesAlignmentService()
    result = await service.align_series(request)

CLI usage:
    uv run python -m \
        app.services.data.external_series_alignment.external_series_alignment
"""

from __future__ import annotations

import logging
import re
import uuid
import zoneinfo
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Literal, override

from app.contracts.common.models import (
    ProblemDetails,
    UtcTimestamp,
    Uuid7,
)
from app.contracts.data.errors import DataFailure
from app.contracts.data.models import (
    AlignedSeries,
    AlignmentPolicy,
    AlignSeriesRequest,
    AlignSeriesSuccess,
)
from app.contracts.data.ports import AlignSeriesCapability
from app.services.data.external_series_alignment.config import (
    ExternalSeriesAlignmentConfig,
)

if TYPE_CHECKING:
    from app.kernel.events import EventBus

logger = logging.getLogger(__name__)

_TUPLE_LENGTH_TWO = 2

_IANA_AREAS: frozenset[str] = frozenset(
    {
        "Africa",
        "America",
        "Antarctica",
        "Arctic",
        "Asia",
        "Atlantic",
        "Australia",
        "Brazil",
        "Canada",
        "Chile",
        "Etc",
        "Europe",
        "Indian",
        "Mexico",
        "Pacific",
        "US",
    }
)


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
        Canonical ISO 8601 string with microsecond resolution and Z suffix.
    """
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _parse_utc_timestamp(val: datetime | str) -> datetime:
    """Parse an ISO 8601 string or datetime into an aware UTC datetime.

    Args:
        val: Timestamp string or datetime.

    Returns:
        Aware datetime in UTC.

    Raises:
        ValueError: If parsing fails or timestamp is unparseable.
    """
    if isinstance(val, datetime):
        if val.tzinfo is None:
            return val.replace(tzinfo=UTC)
        return val.astimezone(UTC)

    normalized = val.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    dt = datetime.fromisoformat(normalized)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _validate_timezone(name: str) -> None:
    """Validate an IANA timezone identifier with Windows fallback support.

    Args:
        name: Timezone identifier string.

    Raises:
        ValueError: If the identifier is not a recognized IANA timezone.
    """
    if not name or not isinstance(name, str):
        msg = "Timezone identifier must be a non-empty string"
        raise ValueError(msg)
    if name in ("UTC", "GMT", "Etc/UTC", "Etc/GMT"):
        return
    try:
        zoneinfo.ZoneInfo(name)
        return
    except (
        zoneinfo.ZoneInfoNotFoundError,
        ModuleNotFoundError,
        ValueError,
        OSError,
        KeyError,
    ):
        area, _, rest = name.partition("/")
        if (
            area in _IANA_AREAS
            and rest
            and re.fullmatch(r"[A-Za-z0-9_+-]+(/[A-Za-z0-9_+-]+)*", rest)
        ):
            return
    msg = f"Invalid timezone identifier '{name}'"
    raise ValueError(msg)


@dataclass(frozen=True)
class SeriesPoint:
    """One external numeric series data point.

    Attributes:
        timestamp: Recorded event or observation timestamp.
        value: Numeric value observed.
        available_at: Timestamp when this value became available/visible.
            Defaults to timestamp if unspecified.
    """

    timestamp: datetime | str
    value: Decimal | float | int | str
    available_at: datetime | str | None = None

    def normalized(self) -> tuple[datetime, Decimal, datetime]:
        """Convert fields to canonical aware UTC datetimes and Decimal value.

        Returns:
            Tuple of (timestamp, value, available_at).
        """
        ts = _parse_utc_timestamp(self.timestamp)
        val = Decimal(str(self.value))
        avail = (
            _parse_utc_timestamp(self.available_at)
            if self.available_at is not None
            else ts
        )
        return ts, val, avail


@dataclass(frozen=True)
class AlignedPoint:
    """One aligned point produced at a target decision timestamp.

    Attributes:
        target_timestamp: The target decision timestamp.
        aligned_value: The aligned numeric value, or None if missing/gap.
        source_timestamp: Timestamp of the source point used, if any.
        available_at: Availability timestamp of the source point used, if any.
        is_gap: Whether this point represents a missing-value gap.
    """

    target_timestamp: UtcTimestamp
    aligned_value: Decimal | None
    source_timestamp: UtcTimestamp | None
    available_at: UtcTimestamp | None
    is_gap: bool


def data_define_alignment_policy(
    direction: Literal["EXACT", "LAST_KNOWN", "AGGREGATE"] = "LAST_KNOWN",
    max_age_seconds: int = 86_400,
    missing_policy: Literal["NULL", "CARRY_FORWARD", "FAIL"] = "NULL",
    timezone: str = "UTC",
    look_ahead_prohibited: bool = True,
) -> AlignmentPolicy:
    """Validate and construct an AlignmentPolicy (FR-DATA-DEFINE_ALIGNMENT_POLICY).

    Args:
        direction: Alignment direction ("EXACT", "LAST_KNOWN", "AGGREGATE").
        max_age_seconds: Maximum lookback age in seconds (must be >= 1).
        missing_policy: Missing-value handling policy ("NULL", "CARRY_FORWARD", "FAIL").
        timezone: IANA timezone string (e.g. "UTC", "America/New_York").
        look_ahead_prohibited: Must be True to prohibit future data visibility.

    Returns:
        Validated AlignmentPolicy instance.

    Raises:
        ValueError: If any parameter violates alignment policy invariants.
    """
    if direction not in ("EXACT", "LAST_KNOWN", "AGGREGATE"):
        msg = (
            f"Invalid direction '{direction}': must be EXACT, LAST_KNOWN, or AGGREGATE"
        )
        raise ValueError(msg)

    if max_age_seconds < 1:
        msg = f"max_age_seconds must be >= 1, got {max_age_seconds}"
        raise ValueError(msg)

    if missing_policy not in ("NULL", "CARRY_FORWARD", "FAIL"):
        msg = (
            f"Invalid missing_policy '{missing_policy}': "
            "must be NULL, CARRY_FORWARD, or FAIL"
        )
        raise ValueError(msg)

    _validate_timezone(timezone)

    if look_ahead_prohibited is not True:
        msg = "look_ahead_prohibited must be strictly True to prevent lookahead bias"
        raise ValueError(msg)

    return AlignmentPolicy(
        direction=direction,
        max_age_seconds=max_age_seconds,
        missing_policy=missing_policy,
        timezone=timezone,
        look_ahead_prohibited=True,
    )


def _validate_target_timestamps(
    target_timestamps: Sequence[datetime | str],
) -> list[datetime]:
    """Validate and normalize target timestamps in ascending order.

    Args:
        target_timestamps: Sequence of target timestamp strings or datetimes.

    Returns:
        List of parsed UTC datetimes.

    Raises:
        ValueError: If target_timestamps is empty or not in chronological order.
    """
    if not target_timestamps:
        msg = "target_timestamps sequence cannot be empty"
        raise ValueError(msg)

    targets = [_parse_utc_timestamp(t) for t in target_timestamps]
    for i in range(1, len(targets)):
        if targets[i] < targets[i - 1]:
            msg = (
                "target_timestamps must be in chronological ascending order: "
                f"{targets[i]} < {targets[i - 1]}"
            )
            raise ValueError(msg)
    return targets


def _normalize_sources(
    source_points: Sequence[Any],
) -> list[tuple[datetime, Decimal, datetime]]:
    """Normalize and sort source points chronologically.

    Args:
        source_points: Sequence of point structures.

    Returns:
        List of tuples: (timestamp, value, available_at).

    Raises:
        TypeError: If point type is unsupported.
    """
    normalized_sources: list[tuple[datetime, Decimal, datetime]] = []
    for sp in source_points:
        if isinstance(sp, SeriesPoint):
            normalized_sources.append(sp.normalized())
        elif isinstance(sp, dict):
            pt = SeriesPoint(
                timestamp=sp["timestamp"],
                value=sp["value"],
                available_at=sp.get("available_at"),
            )
            normalized_sources.append(pt.normalized())
        elif isinstance(sp, (tuple, list)):
            if len(sp) == _TUPLE_LENGTH_TWO:
                pt = SeriesPoint(timestamp=sp[0], value=sp[1])
            else:
                pt = SeriesPoint(timestamp=sp[0], value=sp[1], available_at=sp[2])
            normalized_sources.append(pt.normalized())
        else:
            msg = f"Unsupported series point representation: {type(sp)}"
            raise TypeError(msg)

    normalized_sources.sort(key=lambda s: (s[0], s[2]))
    return normalized_sources


def _align_target(
    target: datetime,
    visible: list[tuple[datetime, Decimal, datetime]],
    policy: AlignmentPolicy,
    max_age_delta: timedelta,
) -> tuple[Decimal | None, datetime | None, datetime | None, bool]:
    """Compute aligned value for a single target from visible points.

    Args:
        target: Target decision timestamp.
        visible: Filtered list of visible source points.
        policy: Active alignment policy.
        max_age_delta: Pre-computed max lookback timedelta.

    Returns:
        Tuple of (aligned_value, source_timestamp, available_at, is_gap).
    """
    if policy.direction == "EXACT":
        exact_matches = [s for s in visible if s[0] == target]
        if exact_matches:
            chosen = exact_matches[-1]
            return chosen[1], chosen[0], chosen[2], False
        return None, None, None, True

    if policy.direction == "LAST_KNOWN":
        if visible:
            chosen = visible[-1]
            if (target - chosen[0]) <= max_age_delta:
                return chosen[1], chosen[0], chosen[2], False
        return None, None, None, True

    # AGGREGATE
    window_start = target - max_age_delta
    window_points = [s for s in visible if s[0] >= window_start]
    if window_points:
        total = sum((s[1] for s in window_points), Decimal(0))
        mean_val = total / Decimal(len(window_points))
        return mean_val, window_points[-1][0], max(s[2] for s in window_points), False

    return None, None, None, True


def _handle_missing_gap(
    target: datetime,
    policy: AlignmentPolicy,
    max_age_delta: timedelta,
    last_valid: tuple[Decimal, datetime, datetime] | None,
) -> tuple[Decimal | None, datetime | None, datetime | None, bool]:
    """Resolve a missing value gap according to the missing policy.

    Args:
        target: Target decision timestamp.
        policy: Active alignment policy.
        max_age_delta: Pre-computed max lookback timedelta.
        last_valid: Previous valid aligned value tuple, if any.

    Returns:
        Tuple of (aligned_value, source_timestamp, available_at, is_gap).

    Raises:
        ValueError: When missing policy is FAIL and a gap occurs.
    """
    if policy.missing_policy == "FAIL":
        formatted_ts = _format_utc_timestamp(target)
        msg = f"Missing value for target timestamp {formatted_ts} under FAIL policy"
        raise ValueError(msg)

    if policy.missing_policy == "CARRY_FORWARD" and last_valid is not None:
        prev_val, prev_src_ts, prev_avail = last_valid
        if (target - prev_src_ts) <= max_age_delta:
            return prev_val, prev_src_ts, prev_avail, False

    return None, None, None, True


def data_align_external_series(
    source_points: Sequence[SeriesPoint | dict[str, Any] | tuple[Any, ...]],
    target_timestamps: Sequence[datetime | str],
    policy: AlignmentPolicy | None = None,
    *,
    source_version_id: Uuid7 | None = None,
) -> tuple[AlignedSeries, tuple[AlignedPoint, ...]]:
    """Align external numeric series without future visibility.

    Implements FR-DATA-ALIGN_EXTERNAL_SERIES.

    Args:
        source_points: Sequence of source series points.
        target_timestamps: Sequence of target decision timestamps.
        policy: Alignment policy specifying direction, max age, and missing behavior.
        source_version_id: Optional source version UUID identifier.

    Returns:
        Tuple of (AlignedSeries record, tuple of AlignedPoint results).

    Raises:
        ValueError: If validation fails or missing policy is FAIL and a gap occurs.
        TypeError: If an unsupported source point type is passed.
    """
    active_policy = policy or data_define_alignment_policy()
    targets = _validate_target_timestamps(target_timestamps)
    sources = _normalize_sources(source_points)

    aligned_points: list[AlignedPoint] = []
    last_valid: tuple[Decimal, datetime, datetime] | None = None
    max_age_delta = timedelta(seconds=active_policy.max_age_seconds)

    for target in targets:
        # Zero future visibility: timestamp <= target and available_at <= target
        visible = [s for s in sources if s[0] <= target and s[2] <= target]
        val, src_ts, avail_ts, is_gap = _align_target(
            target, visible, active_policy, max_age_delta
        )

        if is_gap or val is None:
            val, src_ts, avail_ts, is_gap = _handle_missing_gap(
                target, active_policy, max_age_delta, last_valid
            )
        elif src_ts is not None and avail_ts is not None:
            last_valid = (val, src_ts, avail_ts)

        aligned_points.append(
            AlignedPoint(
                target_timestamp=_format_utc_timestamp(target),
                aligned_value=val,
                source_timestamp=_format_utc_timestamp(src_ts) if src_ts else None,
                available_at=_format_utc_timestamp(avail_ts) if avail_ts else None,
                is_gap=is_gap,
            )
        )

    aligned_series = AlignedSeries(
        alignment_id=_generate_uuid7(),
        source_version_id=source_version_id or _generate_uuid7(),
        policy=active_policy,
        aligned_version_id=_generate_uuid7(),
    )

    return aligned_series, tuple(aligned_points)


class AlignSeriesService(AlignSeriesCapability):
    """Domain service implementation for AlignSeriesCapability."""

    def __init__(
        self,
        config: ExternalSeriesAlignmentConfig | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize the service instance.

        Args:
            config: Optional runtime configuration.
            event_bus: Optional kernel event bus.
        """
        self._config = config or ExternalSeriesAlignmentConfig()
        self._event_bus = event_bus

    @property
    def config(self) -> ExternalSeriesAlignmentConfig:
        """Return the active configuration."""
        return self._config

    def _handle_define_policy(
        self,
        request: AlignSeriesRequest,
    ) -> AlignSeriesSuccess | DataFailure:
        """Process DEFINE_POLICY request operation.

        Args:
            request: Alignment request containing policy.

        Returns:
            AlignSeriesSuccess on valid policy, or DataFailure.
        """
        if request.policy is None:
            problem = ProblemDetails(
                type="urn:haruquantai:error:data:missing-field",
                title="Missing policy",
                status=400,
                code="DATA_VALIDATION_FAILED",
                detail="Operation DEFINE_POLICY requires policy",
                request_id=request.request_id,
            )
            return DataFailure(
                request_id=request.request_id,
                code="DATA_VALIDATION_FAILED",
                problem=problem,
            )

        data_define_alignment_policy(
            direction=request.policy.direction,
            max_age_seconds=request.policy.max_age_seconds,
            missing_policy=request.policy.missing_policy,
            timezone=request.policy.timezone,
            look_ahead_prohibited=request.policy.look_ahead_prohibited,
        )

        aligned = AlignedSeries(
            alignment_id=_generate_uuid7(),
            source_version_id=request.source_version_id or _generate_uuid7(),
            policy=request.policy,
            aligned_version_id=_generate_uuid7(),
        )

        return AlignSeriesSuccess(
            request_id=request.request_id,
            aligned=aligned,
            outcome="SUCCESS",
        )

    def _handle_align(
        self,
        request: AlignSeriesRequest,
    ) -> AlignSeriesSuccess | DataFailure:
        """Process ALIGN request operation.

        Args:
            request: Alignment request containing source and policy.

        Returns:
            AlignSeriesSuccess on valid alignment, or DataFailure.
        """
        if request.policy is None:
            problem = ProblemDetails(
                type="urn:haruquantai:error:data:missing-field",
                title="Missing policy",
                status=400,
                code="DATA_VALIDATION_FAILED",
                detail="Operation ALIGN requires policy",
                request_id=request.request_id,
            )
            return DataFailure(
                request_id=request.request_id,
                code="DATA_VALIDATION_FAILED",
                problem=problem,
            )

        aligned = AlignedSeries(
            alignment_id=_generate_uuid7(),
            source_version_id=request.source_version_id or _generate_uuid7(),
            policy=request.policy,
            aligned_version_id=_generate_uuid7(),
        )

        return AlignSeriesSuccess(
            request_id=request.request_id,
            aligned=aligned,
            outcome="SUCCESS",
        )

    @override
    async def align_series(
        self,
        request: AlignSeriesRequest,
    ) -> AlignSeriesSuccess | DataFailure:
        """Align external series under point-in-time policies.

        Args:
            request: Operation-discriminated alignment request.

        Returns:
            The aligned series on success, otherwise a structured data failure.
        """
        try:
            op: str = str(request.operation)
            if op == "DEFINE_POLICY":
                return self._handle_define_policy(request)
            if op == "ALIGN":
                return self._handle_align(request)

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

        except ValueError as err:
            logger.warning("Alignment validation or compatibility failure: %s", err)
            problem = ProblemDetails(
                type="urn:haruquantai:error:data:alignment-incompatible",
                title="Alignment Incompatible",
                status=400,
                code="DATA_ALIGNMENT_INCOMPATIBLE",
                detail=str(err),
                request_id=request.request_id,
            )
            return DataFailure(
                request_id=request.request_id,
                code="DATA_ALIGNMENT_INCOMPATIBLE",
                problem=problem,
            )
        except Exception as err:
            logger.exception("Unexpected failure during align_series")
            problem = ProblemDetails(
                type="urn:haruquantai:error:data:internal-error",
                title="Internal Error",
                status=500,
                code="DATA_VALIDATION_FAILED",
                detail=str(err),
                request_id=request.request_id,
            )
            return DataFailure(
                request_id=request.request_id,
                code="DATA_VALIDATION_FAILED",
                problem=problem,
            )


def main() -> None:
    """Execute the external series alignment usage demonstration harness."""
    from app.services.data.external_series_alignment._usage import (
        main as _usage_main,
    )

    _usage_main()


def run_usage_scenarios() -> None:
    """Synchronous runner entry point for the usage demonstration."""
    main()


if __name__ == "__main__":
    run_usage_scenarios()
