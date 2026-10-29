"""Canonical yearly/monthly Parquet files with staged, rollback-safe publication."""

from __future__ import annotations

import calendar
import json
import os
import uuid
from contextlib import nullcontext
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd  # type: ignore[import-untyped]
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

from app.core.host.persistence import HostPersistence
from app.include.market_storage import catalog_paths, encode_frame, safe_component

from .coverage import (
    add_completed_range,
    observation_coverage,
)
from .partition_files import (
    FilePublication,
    canonical_target,
    dataset_lock,
    recover_publications,
)

PART_ROWS = 65536
_MONTHS = 12
_PUBLICATION_ATTEMPTS = 3


def require_data(response: dict[str, Any]) -> Any:
    """Propagate persistence failure instead of reporting uncommitted success."""
    if not response["success"]:
        error = response.get("error") or {}
        raise RuntimeError(error.get("message", "Dataset persistence failed"))
    return response["data"]


def dataset_root(storage_root: Path, symbol: str, timeframe: str) -> Path:
    """Derive a dataset-owned root, including postfix and canonical ticks name."""
    safe_component(symbol)
    return (
        storage_root.resolve()
        / ("ticks" if timeframe == "TICK" else timeframe.lower())
        / symbol.lower()
    )


def _checkpoint(context: Any) -> None:
    if context is not None:
        context.raise_if_cancelled()


def _partition_key(date: datetime, timeframe: str) -> str:
    return (
        str(date.year)
        if timeframe != "TICK"
        else f"{date.year}/{date.month:02d}-{calendar.month_abbr[date.month].lower()}"
    )


def publish_frame(
    gateway: HostPersistence,
    storage_root: Path,
    record: dict[str, Any],
    frame: pd.DataFrame,
    tick_size: float,
    *,
    overwrite: bool = False,
    replace_snapshot: bool = False,
    metadata_updates: dict[str, Any] | None = None,
    locked: bool = False,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    context: Any = None,
    coverage: tuple[datetime, datetime] | None = None,
) -> dict[str, Any]:
    """Prepare files outside SQLite, then publish with a snapshot check."""
    root = dataset_root(storage_root, record["symbol"], record["timeframe"])
    with nullcontext() if locked else dataset_lock(root, context):
        recover_publications(root, gateway)
        for attempt in range(_PUBLICATION_ATTEMPTS):
            try:
                return _publish_frame_once(
                    gateway,
                    storage_root,
                    record,
                    frame,
                    tick_size,
                    overwrite=overwrite,
                    replace_snapshot=replace_snapshot,
                    metadata_updates=metadata_updates,
                    date_from=date_from,
                    date_to=date_to,
                    context=context,
                    coverage=coverage,
                )
            except _SnapshotChangedError:
                if attempt == _PUBLICATION_ATTEMPTS - 1:
                    raise
        raise AssertionError("Unreachable publication retry")


class _SnapshotChangedError(RuntimeError):
    """Another catalog writer committed while files were being prepared."""


def _check_snapshot(current: Any, previous: Any) -> None:
    if current != previous:
        raise _SnapshotChangedError("Dataset changed during file preparation")


def _publish_frame_once(  # noqa: C901 - one rollback scope for snapshot publication
    gateway: HostPersistence,
    storage_root: Path,
    record: dict[str, Any],
    frame: pd.DataFrame,
    tick_size: float,
    *,
    overwrite: bool = False,
    replace_snapshot: bool = False,
    metadata_updates: dict[str, Any] | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    context: Any = None,
    coverage: tuple[datetime, datetime] | None = None,
) -> dict[str, Any]:
    """Publish one consistent dataset snapshot; overwrite affects only its range."""
    table = encode_frame(frame, record["timeframe"], tick_size)
    root = dataset_root(storage_root, record["symbol"], record["timeframe"])
    created: list[Path] = []
    publication = None
    committed = False
    try:
        if context is not None:
            context.wait_if_paused()
        _checkpoint(context)
        rows = require_data(
            gateway.read_records(
                "datamgr_datasets", filters={"id": record["id"]}, limit=1
            )
        )["records"]
        previous = rows[0] if rows else None
        if previous is not None:
            _validate_previous(previous, record, storage_root, tick_size)
        result = _publish_parts(
            None if replace_snapshot else previous,
            table,
            root,
            record["timeframe"],
            overwrite=overwrite,
            date_from=date_from,
            date_to=date_to,
            context=context,
            created=created,
        )
        lineage = json.loads((previous or record).get("lineage_json") or "{}")
        if replace_snapshot:
            lineage.pop("covered_ranges", None)
        lineage.update(
            {
                "tick_size": tick_size,
                "partitions": [
                    str(canonical_target(Path(path))) if Path(path) in created else path
                    for path in result["partitions"]
                ],
                "storage": "canonical-partitions-v1",
            }
        )
        if previous and any(
            not Path(path).is_file() for path in catalog_paths(previous)
        ):
            lineage.pop("covered_ranges", None)
        if coverage is not None:
            add_completed_range(
                lineage, *observation_coverage(table, record["timeframe"], coverage)
            )
        values = {
            **record,
            "path": str(root),
            "bars": result["total_bars"],
            "date_from": result["date_from"],
            "date_to": result["date_to"],
            "lineage_json": json.dumps(lineage),
            "schema_version": 2,
            "updated_at": datetime.now(UTC).isoformat(),
        }
        publication = FilePublication(root, created, record["id"], values["updated_at"])
        publication.prepare()
        with gateway.transaction() as tx:
            current = require_data(
                tx.read_records(
                    "datamgr_datasets",
                    filters={"id": record["id"]},
                    limit=1,
                )
            )["records"]
            _check_snapshot(current[0] if current else None, previous)
            _checkpoint(context)
            publication.install()
            if previous:
                values["created_at"] = previous["created_at"]
                values["broker"] = previous["broker"]
                values.update(
                    {
                        key: value
                        for key, value in (metadata_updates or {}).items()
                        if key != "updated_at"
                    }
                )
                require_data(
                    tx.update_record(
                        "datamgr_datasets",
                        {key: value for key, value in values.items() if key != "id"},
                        filters={"id": record["id"]},
                    )
                )
            else:
                require_data(tx.create_records("datamgr_datasets", values))
            if context is not None:
                context.raise_if_cancelled()
        committed = True
        publication.finish()
        return {
            **result,
            "partitions": lineage["partitions"],
            "partitions_written": [str(canonical_target(path)) for path in created],
            "dataset_id": record["id"],
        }
    except BaseException:
        if publication is not None and not committed:
            publication.rollback()
        for path in created:
            path.unlink(missing_ok=True)
        raise


def _publish_parts(
    previous: dict[str, Any] | None,
    incoming: pa.Table,
    root: Path,
    timeframe: str,
    *,
    overwrite: bool,
    date_from: datetime | None,
    date_to: datetime | None,
    context: Any,
    created: list[Path],
) -> dict[str, Any]:
    bounds = pc.min_max(incoming["DateTime"]).as_py()
    lower, upper = date_from or bounds["min"], date_to or bounds["max"]
    if lower > upper:
        raise ValueError("From must not be after To")
    incoming = incoming.filter(
        pc.and_(
            pc.greater_equal(incoming["DateTime"], lower),
            pc.less_equal(incoming["DateTime"], upper),
        )
    )
    if not incoming.num_rows:
        raise ValueError("No observations in the requested interval")
    active = (
        [path for path in catalog_paths(previous) if Path(path).is_file()]
        if previous
        else []
    )
    groups: dict[str, list[str]] = {}
    for path in active:
        metadata = pq.read_metadata(path)
        if metadata.num_rows:
            # Legacy partition files are already sorted by date.
            statistics = metadata.row_group(0).column(0).statistics
            if statistics is None or not statistics.has_min_max:
                raise ValueError("Partition lacks DateTime statistics")
            date = statistics.min
            groups.setdefault(_partition_key(date, timeframe), []).append(path)
    # Values are already UTC; calendar extraction needs no external Windows tzdb.
    utc_values = pc.cast(incoming["DateTime"], pa.timestamp("us"))
    years = pc.year(utc_values)
    months = pc.month(utc_values)
    pairs = (
        {(year, 1) for year in pc.unique(years).to_pylist()}
        if timeframe != "TICK"
        else set(zip(years.to_pylist(), months.to_pylist(), strict=True))
    )
    keys = {
        _partition_key(datetime(year, month, 1, tzinfo=UTC), timeframe)
        for year, month in pairs
    }
    if overwrite:
        keys.update(key for key in groups if _overlaps(key, timeframe, lower, upper))
    output = [
        path for key, paths in groups.items() if key not in keys for path in paths
    ]
    for index, key in enumerate(sorted(keys)):
        _checkpoint(context)
        mask = pc.equal(years, int(key.split("/")[0]))
        if timeframe == "TICK":
            mask = pc.and_(mask, pc.equal(months, int(key.split("/")[1][:2])))
        part = incoming.filter(mask)
        output.extend(
            _merge_partition(
                groups.get(key, []),
                part,
                Path(f"{root / key}.parquet"),
                timeframe,
                overwrite=overwrite,
                lower=lower,
                upper=upper,
                context=context,
                created=created,
            )
        )
        if context is not None:
            context.report_progress(70 + 25 * (index + 1) / len(keys), f"Saved {key}")
    return _summary(output)


def _summary(output: list[str]) -> dict[str, Any]:
    """Read row counts and time bounds from Parquet statistics."""
    total, minimum, maximum = 0, None, None
    for path in output:
        metadata = pq.read_metadata(path)
        total += metadata.num_rows
        for index in range(metadata.num_row_groups):
            stats = metadata.row_group(index).column(0).statistics
            if stats is None or not stats.has_min_max:
                raise ValueError("Canonical partitions require DateTime statistics")
            minimum = stats.min if minimum is None else min(minimum, stats.min)
            maximum = stats.max if maximum is None else max(maximum, stats.max)
    return {
        "total_bars": total,
        "date_from": minimum.isoformat() if minimum else "",
        "date_to": maximum.isoformat() if maximum else "",
        "partitions": output,
    }


def _overlaps(key: str, timeframe: str, lower: datetime, upper: datetime) -> bool:
    year = int(key.split("/", maxsplit=1)[0])
    month = 1 if timeframe != "TICK" else int(key.split("/")[1][:2])
    start = datetime(year, month, 1, tzinfo=UTC)
    end = (
        datetime(year + 1, 1, 1, tzinfo=UTC)
        if timeframe != "TICK" or month == _MONTHS
        else datetime(year, month + 1, 1, tzinfo=UTC)
    )
    return start <= upper and lower < end


def _merge_partition(
    paths: list[str],
    part: pa.Table,
    directory: Path,
    timeframe: str,
    *,
    overwrite: bool,
    lower: datetime,
    upper: datetime,
    context: Any,
    created: list[Path],
) -> list[str]:
    directory.parent.mkdir(parents=True, exist_ok=True)
    with duckdb.connect() as connection:
        connection.register("incoming", part)
        connection.execute(
            "CREATE TEMP VIEW new_rows AS SELECT *, 1 AS priority FROM incoming"
        )
        if paths:
            expected = part.schema.remove_metadata()
            if any(
                not pq.read_schema(path).remove_metadata().equals(expected)
                for path in paths
            ):
                raise ValueError(
                    "Existing partition schema differs from canonical schema"
                )
            connection.read_parquet(paths).create_view("existing")
            if overwrite:
                connection.execute(
                    "CREATE TEMP TABLE old_rows AS SELECT *, 0 AS priority "
                    "FROM existing WHERE DateTime < ? OR DateTime > ?",
                    [lower, upper],
                )
            else:
                connection.execute(
                    "CREATE TEMP VIEW old_rows AS SELECT *, 0 AS priority FROM existing"
                )
        else:
            connection.execute(
                "CREATE TEMP VIEW old_rows AS SELECT * FROM new_rows WHERE false"
            )
        columns = part.column_names
        quoted = ", ".join(f'"{column}"' for column in columns)
        identity = '"DateTime"' if timeframe != "TICK" else quoted
        order = "DESC" if overwrite else "ASC"
        query = (
            f"SELECT {quoted} FROM (SELECT *, row_number() OVER ("  # noqa: S608
            f"PARTITION BY {identity} ORDER BY priority {order}) AS n "
            "FROM (SELECT * FROM old_rows UNION ALL SELECT * FROM new_rows)) "
            'WHERE n = 1 ORDER BY "DateTime"'
        )
        reader = connection.execute(query).to_arrow_reader(PART_ROWS)
        path = directory.with_name(
            f".{directory.stem}.{uuid.uuid4().hex}.pending.parquet"
        )
        created.append(path)
        with pq.ParquetWriter(
            path,
            part.schema,
            compression="zstd",
            compression_level=6,
        ) as writer:
            for batch in reader:
                _checkpoint(context)
                table = pa.Table.from_batches([batch]).cast(part.schema)
                writer.write_table(table, row_group_size=PART_ROWS)
        with path.open("rb+") as stream:
            os.fsync(stream.fileno())
        return [str(path)]


def _validate_previous(
    previous: dict[str, Any], record: dict[str, Any], root: Path, tick_size: float
) -> None:
    """Prevent accidental reuse of identity, units, or files outside storage."""
    if (
        previous["underlying"] != record["underlying"]
        or previous["timeframe"] != record["timeframe"]
    ):
        raise ValueError("Dataset identity does not match its registered definition")
    lineage = json.loads(previous.get("lineage_json") or "{}")
    if lineage.get("tick_size", tick_size) != tick_size:
        raise ValueError("Instrument tick size changed; explicit migration required")
    if any(
        not Path(path).resolve().is_relative_to(root.resolve())
        for path in catalog_paths(previous)
    ):
        raise ValueError("Dataset manifest references files outside its storage root")
