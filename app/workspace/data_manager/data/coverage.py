"""Plan missing downloads from committed request coverage and actual bar gaps."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import duckdb
import pyarrow as pa
import pyarrow.compute as pc

from app.core.data.market_storage import catalog_paths
from app.core.enums import Timeframe
from app.core.host.persistence import HostPersistence

_STEP = timedelta(microseconds=1)
_MONTHS = 12


class RangeProgress:
    """Map a missing-range download into its parent job without losing controls."""

    def __init__(self, context: Any, index: int, total: int) -> None:
        self.context, self.index, self.total = context, index, total

    def wait_if_paused(self) -> None:
        """Observe pauses before reading or publishing history."""
        if self.context is not None:
            self.context.wait_if_paused()

    def raise_if_cancelled(self) -> None:
        """Prevent publication after cancellation."""
        if self.context is not None:
            self.context.raise_if_cancelled()

    def report_progress(self, progress: float, message: str = "") -> None:
        """Report monotonic progress across individual missing intervals."""
        if self.context is not None:
            self.context.report_progress(
                100 * (self.index + progress / 100) / self.total, message
            )


def merged_ranges(
    ranges: list[tuple[datetime, datetime]],
) -> list[tuple[datetime, datetime]]:
    """Merge overlapping or adjacent inclusive UTC intervals."""
    result: list[tuple[datetime, datetime]] = []
    for lower, upper in sorted(ranges):
        if lower > upper:
            continue
        if result and lower <= result[-1][1] + _STEP:
            result[-1] = (result[-1][0], max(result[-1][1], upper))
        else:
            result.append((lower, upper))
    return result


def completed_ranges(lineage: dict[str, Any]) -> list[tuple[datetime, datetime]]:
    """Read only explicit completed request intervals, never infer from min/max."""
    return [
        (
            datetime.fromisoformat(item["from"]).astimezone(UTC),
            datetime.fromisoformat(item["to"]).astimezone(UTC),
        )
        for item in lineage.get("covered_ranges", [])
    ]


def add_completed_range(
    lineage: dict[str, Any], lower: datetime, upper: datetime
) -> None:
    """Record fetched coverage without marking future history as already downloaded."""
    upper = min(upper, datetime.now(UTC))
    ranges = merged_ranges([*completed_ranges(lineage), (lower, upper)])
    lineage["covered_ranges"] = [
        {"from": start.isoformat(), "to": stop.isoformat()} for start, stop in ranges
    ]


def observation_coverage(
    table: pa.Table, timeframe: str, bounds: tuple[datetime, datetime]
) -> tuple[datetime, datetime]:
    """Do not mark an unavailable leading/trailing bar range as downloaded."""
    lower, upper = bounds
    if timeframe == "TICK":
        return bounds  # A verified quote-range response establishes tick coverage.
    dates = table["DateTime"]
    dates = pc.filter(
        dates, pc.and_(pc.greater_equal(dates, lower), pc.less_equal(dates, upper))
    )
    statistics = pc.min_max(dates).as_py()
    first, _ = _slot_bounds(statistics["min"], timeframe)
    _, last = _slot_bounds(statistics["max"], timeframe)
    return max(lower, first), min(upper, last)


def _slot_bounds(date: datetime, timeframe: str) -> tuple[datetime, datetime]:
    if timeframe in ("D1", "W1", "MN1"):
        start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        if timeframe == "MN1":
            start = start.replace(day=1)
            stop = start.replace(
                year=start.year + (start.month == _MONTHS),
                month=start.month % _MONTHS + 1,
            )
        elif timeframe == "W1":
            start -= timedelta(days=start.weekday())
            stop = start + timedelta(days=7)
        else:
            stop = start + timedelta(days=1)
    else:
        start = date
        stop = date + timedelta(seconds=Timeframe.resolve(timeframe).to_seconds())
    return start, stop - _STEP


def missing_ranges(
    row: dict[str, Any] | None,
    lower: datetime,
    upper: datetime,
    *,
    overwrite: bool = False,
) -> list[tuple[datetime, datetime]]:
    """Subtract committed coverage and actual bar slots from a requested range.

    A tick timestamp cannot prove that every quote between two ticks was fetched.
    Legacy tick files therefore require one verified fetch before coverage is known.
    """
    if overwrite or row is None:
        return [(lower, upper)]
    lineage = json.loads(row.get("lineage_json") or "{}")
    paths = catalog_paths(row)
    intact = bool(paths) and all(Path(path).is_file() for path in paths)
    covered = completed_ranges(lineage) if intact else []
    paths = [path for path in paths if Path(path).is_file()]
    gaps = _subtract(lower, upper, covered)
    if not gaps or row["timeframe"] == "TICK":
        return gaps
    if paths:
        covered.extend(_bar_ranges(paths, row["timeframe"], lower, upper))
    return _subtract(lower, upper, covered)


def _subtract(
    lower: datetime, upper: datetime, covered: list[tuple[datetime, datetime]]
) -> list[tuple[datetime, datetime]]:
    cursor, missing = lower, []
    for start, stop in merged_ranges(covered):
        if stop < cursor:
            continue
        if start > upper:
            break
        if start > cursor:
            missing.append((cursor, min(upper, start - _STEP)))
        cursor = max(cursor, stop + _STEP)
        if cursor > upper:
            return missing
    if cursor <= upper:
        missing.append((cursor, upper))
    return missing


def _bar_ranges(
    paths: list[str], timeframe: str, lower: datetime, upper: datetime
) -> list[tuple[datetime, datetime]]:
    calendar = {
        "D1": ("day", "1 day"),
        "W1": ("week", "1 week"),
        "MN1": ("month", "1 month"),
    }.get(timeframe)
    if calendar:
        unit, duration = calendar
        point = f"date_trunc('{unit}', DateTime)"
    else:
        duration = f"{Timeframe.resolve(timeframe).to_seconds()} seconds"
        point = "DateTime"
    # The SQL fragments above are generated solely from validated timeframe values.
    query = f"""
        WITH slots AS (
            SELECT DISTINCT {point} AS start,
                   {point} + INTERVAL '{duration}' AS stop
            FROM cached
        ), relevant AS (
            SELECT * FROM slots WHERE stop > ? AND start <= ?
        ), previous AS (
            SELECT *, max(stop) OVER (ORDER BY start ROWS BETWEEN
                UNBOUNDED PRECEDING AND 1 PRECEDING) AS previous_stop FROM relevant
        ), groups AS (
            SELECT *, sum(CASE WHEN previous_stop >= start THEN 0 ELSE 1 END)
                OVER (ORDER BY start) AS run FROM previous
        )
        SELECT CAST(min(start) AS TIMESTAMP),
               CAST(max(stop) - INTERVAL '1 microsecond' AS TIMESTAMP)
        FROM groups GROUP BY run ORDER BY min(start)
    """  # noqa: S608
    with duckdb.connect() as connection:
        connection.execute("SET TimeZone='UTC'")
        connection.read_parquet(paths).create_view("cached")
        rows = connection.execute(query, [lower, upper]).fetchall()
        return [
            (start.replace(tzinfo=UTC), stop.replace(tzinfo=UTC))
            for start, stop in rows
        ]


def record_checked_ranges(
    gateway: HostPersistence, dataset_id: str, ranges: list[tuple[datetime, datetime]]
) -> None:
    """Remember confirmed empty intervals after an otherwise successful download."""
    if not ranges:
        return
    with gateway.transaction() as tx:
        response = tx.read_records(
            "datamgr_datasets", filters={"id": dataset_id}, limit=1
        )
        if not response["success"] or not response["data"]["records"]:
            raise RuntimeError("Dataset changed while recording download coverage")
        row = response["data"]["records"][0]
        lineage = json.loads(row.get("lineage_json") or "{}")
        first = datetime.fromisoformat(row["date_from"]).astimezone(UTC)
        last = datetime.fromisoformat(row["date_to"]).astimezone(UTC)
        if row["timeframe"] != "TICK":
            first, _ = _slot_bounds(first, row["timeframe"])
            _, last = _slot_bounds(last, row["timeframe"])
        before = completed_ranges(lineage)
        for lower, upper in ranges:
            add_completed_range(lineage, max(lower, first), min(upper, last))
        if completed_ranges(lineage) == before:
            return
        response = tx.update_record(
            "datamgr_datasets",
            {
                "lineage_json": json.dumps(lineage),
                "updated_at": datetime.now(UTC).isoformat(),
            },
            filters={"id": dataset_id},
        )
        if not response["success"]:
            raise RuntimeError("Could not record download coverage")
