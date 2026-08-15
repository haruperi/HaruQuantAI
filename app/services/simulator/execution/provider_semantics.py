"""Fail-closed provider-revision semantics for canonical Simulation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, time, timedelta
from decimal import Decimal
from typing import cast


def _payload(revision: Mapping[str, object], at: datetime) -> Mapping[str, object]:
    """Return payload from one complete effective revision.

    Raises:
        ValueError: If coverage or effective chronology is invalid.
        TypeError: If the typed revision payload is absent.
    """
    if at.tzinfo is None or at.utcoffset() != timedelta(0):
        raise ValueError("provider semantics require an aware UTC instant")
    if revision.get("complete_coverage") is not True:
        raise ValueError("provider revision lacks complete coverage")
    start = revision.get("effective_from")
    end = revision.get("effective_to")
    if not isinstance(start, datetime) or at < start:
        raise ValueError("provider revision is not effective")
    if end is not None and (not isinstance(end, datetime) or at >= end):
        raise ValueError("provider revision is not effective")
    payload = revision.get("payload")
    if not isinstance(payload, Mapping):
        raise TypeError("provider revision payload is missing")
    return cast("Mapping[str, object]", payload)


def select_provider_revision(
    revisions: Sequence[Mapping[str, object]], *, at: datetime
) -> Mapping[str, object]:
    """Return the unique complete provider revision effective at an instant.

    Args:
        revisions: Data-returned effective-dated revision records.
        at: UTC authority instant to cover.

    Returns:
        The single revision whose half-open interval covers ``at``.

    Raises:
        ValueError: If coverage is absent, ambiguous, or incomplete.
    """
    matches: list[Mapping[str, object]] = []
    for revision in revisions:
        try:
            _payload(revision, at)
        except ValueError as error:
            if str(error) == "provider revision is not effective":
                continue
            raise
        matches.append(revision)
    if len(matches) != 1:
        raise ValueError("provider revision coverage is not unique")
    return matches[0]


def validate_provider_order(
    revision: Mapping[str, object],
    *,
    at: datetime,
    action: str,
    fill_policy: str,
    execution_mode: str,
    requested_volume: Decimal,
    same_direction_position_volume: Decimal,
    same_direction_pending_volume: Decimal,
    reference_price: Decimal,
    stop_price: Decimal | None = None,
    modifying_frozen_order: bool = False,
) -> None:
    """Validate one order against exact effective MT5 provider rules.

    Raises:
        ValueError: If coverage or any provider rule rejects the order.
    """
    payload = _payload(revision, at)
    trade_mode = str(payload.get("trade_mode", "UNKNOWN"))
    if trade_mode in {"DISABLED", "UNKNOWN"}:
        raise ValueError("symbol trade mode blocks orders")
    if trade_mode == "CLOSE_ONLY" and action != "CLOSE":
        raise ValueError("close-only symbol blocks opening orders")
    filling_modes = cast("Sequence[object]", payload.get("filling_modes", ()))
    if fill_policy not in filling_modes:
        raise ValueError("filling mode is unsupported")
    if execution_mode != str(payload.get("execution_mode")):
        raise ValueError("execution mode does not match revision")
    raw_limit = payload.get("directional_volume_limit")
    limit = Decimal(0) if raw_limit is None else Decimal(str(raw_limit))
    directional = (
        requested_volume
        + same_direction_position_volume
        + same_direction_pending_volume
    )
    if limit > 0 and directional > limit:
        raise ValueError("directional volume limit exceeded")
    point = Decimal(str(payload.get("point", "0")))
    if stop_price is not None:
        minimum = Decimal(str(payload.get("stops_level_points", "0"))) * point
        if abs(reference_price - stop_price) < minimum:
            raise ValueError("stop level is too close")
    if modifying_frozen_order:
        freeze = Decimal(str(payload.get("freeze_level_points", "0"))) * point
        if stop_price is not None and abs(reference_price - stop_price) <= freeze:
            raise ValueError("order is inside the freeze level")


def is_provider_session_open(  # noqa: C901 - weekly/dated/overnight matrix is explicit.
    revision: Mapping[str, object], *, at: datetime
) -> bool:
    """Return session eligibility from weekly and dated revision evidence.

    Raises:
        ValueError: If dated-exception coverage is required but absent.
    """
    payload = _payload(revision, at)
    date_key = at.date().isoformat()
    exceptions = payload.get("dated_exceptions", {})
    covered_dates = cast("Sequence[object]", payload.get("exception_coverage", ()))
    exception_map = cast("Mapping[str, object]", exceptions)
    weekly = cast("Mapping[str, object]", payload.get("weekly_sessions", {}))
    current_time = at.timetz().replace(tzinfo=None)
    if date_key in exception_map:
        dated_windows = exception_map[date_key]
        if dated_windows is None:
            return False
        for raw_start, raw_end in cast("Sequence[Sequence[str]]", dated_windows):
            start = time.fromisoformat(raw_start)
            end = time.fromisoformat(raw_end)
            if (start < end and start <= current_time < end) or (
                start >= end and current_time >= start
            ):
                return True
        return False
    for day_offset in (0, -1):
        candidate = at + timedelta(days=day_offset)
        candidate_key = candidate.date().isoformat()
        if candidate_key in exception_map:
            windows = exception_map[candidate_key]
        else:
            if (
                payload.get("exception_coverage_required") is True
                and candidate_key not in covered_dates
            ):
                raise ValueError("dated session exception is uncovered")
            windows = weekly.get(str(candidate.weekday()), ())
        if windows is None:
            continue
        for raw_start, raw_end in cast("Sequence[Sequence[str]]", windows):
            start = time.fromisoformat(raw_start)
            end = time.fromisoformat(raw_end)
            if day_offset == 0 and start < end and start <= current_time < end:
                return True
            if start >= end and (
                (day_offset == 0 and current_time >= start)
                or (day_offset == -1 and current_time < end)
            ):
                return True
    return False


__all__ = [
    "is_provider_session_open",
    "select_provider_revision",
    "validate_provider_order",
]
