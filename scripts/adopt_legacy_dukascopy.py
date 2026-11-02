"""Validate, convert and adopt existing Dukascopy archives without downloading history.

Description:
    Audit legacy Parquet files, validate their units against overlapping bars, stream
    canonical conversions with resumable checkpoints, and publish offline through host
    persistence. Originals are retired only after verified Volume preservation. Accepted
    legacy coverage is explicitly distinguished from app-verified download coverage.
Purpose:
    FEAT-LEGACY-DUKASCOPY-ADOPTION: reuse owner-supplied historical market observations.
Key Capabilities:
    - FR-LEGACY-ADOPTION-audit: INFO reports schemas, units and rejected partitions.
    - FR-LEGACY-ADOPTION-convert: INFO reports bounded conversion progress and checkpoints.
    - FR-LEGACY-ADOPTION-publish: INFO reports registrations; WARNING reports rollback.
    - FR-LEGACY-ADOPTION-volume: INFO verifies Volume preservation and original retirement.
      Temporary-store tests explicitly verify these execution logs and preserved sources.
Python API Usage:
    run(project, work, phase="audit")
CLI Usage:
    uv run python -m scripts.adopt_legacy_dukascopy --work-dir PATH --phase audit
    uv run python -m scripts.adopt_legacy_dukascopy --work-dir PATH --phase convert
    uv run python -m scripts.adopt_legacy_dukascopy --work-dir PATH --phase publish
"""

from __future__ import annotations

import argparse
import io
import json
import math
import os
import shutil
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from decimal import Decimal
from functools import lru_cache
from pathlib import Path
from typing import Any

import duckdb
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
from app.core.data.market_storage import M1_SCHEMA, TICK_SCHEMA
from app.core.host.logging import get_logger
from app.core.host.persistence import HostPersistence
from scripts.rename_sq_market_folders import ensure_offline, records, require

logger = get_logger(__name__)
BATCH = 131072
RESERVE = 8 * 1024**3
RAW_STEP = Decimal("0.000001")


def save(path: Path, value: Any) -> None:
    """Atomically persist a JSON checkpoint outside the source tree."""
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2), encoding="utf-8")
    with temporary.open("rb+") as stream:
        os.fsync(stream.fileno())
    temporary.replace(path)


def load(path: Path) -> Any:
    """Load a previous audit or conversion checkpoint."""
    return json.loads(path.read_text(encoding="utf-8"))


def fingerprint(path: Path) -> list[int]:
    """Detect any source replacement or write between audit and publication."""
    stat = path.stat()
    return [stat.st_size, stat.st_mtime_ns]


def catalog(root: Path) -> dict[str, dict[str, Any]]:
    """Read explicit host catalogue units, categories and display precision."""
    result = {}
    for line in (root / "dukascopy.csv").read_text(encoding="latin1").splitlines():
        fields = line.split(";")
        if len(fields) >= 11:
            result[fields[0].lower()] = {
                "step": min(float(fields[10]), 10.0 ** -int(fields[6])),
                "instrument_tick_size": float(fields[10]),
                "digits": int(fields[6]),
                "category": fields[2],
            }
    return result


def boundaries(file: pq.ParquetFile) -> tuple[str, str]:
    """Read verified row-group time bounds without materializing a partition."""
    values = []
    for index in range(file.metadata.num_row_groups):
        stats = file.metadata.row_group(index).column(0).statistics
        if stats is None or not stats.has_min_max:
            raise ValueError("Missing timestamp statistics")
        values.extend([stats.min, stats.max])
    if not values or any(value.tzinfo is None for value in values):
        raise ValueError("Empty history or timestamps without timezone")
    return min(values).astimezone(UTC).isoformat(), max(values).astimezone(
        UTC
    ).isoformat()


def sample_tick_scale(path: Path, root: Path, step: float) -> int:
    """Require the legacy millionths scale to match independent M1 observations."""
    file = pq.ParquetFile(path)
    symbol = path.relative_to(root / "ticks").parts[0]
    matches = 0
    with duckdb.connect(config={"threads": 1, "memory_limit": "128MB"}) as connection:
        connection.execute("SET TimeZone='UTC'")
        groups = sorted(
            {0, file.metadata.num_row_groups // 2, file.metadata.num_row_groups - 1}
        )
        for group in groups:
            batch = next(
                file.iter_batches(
                    batch_size=256, row_groups=[group], columns=["DateTime", "Bid"]
                )
            )
            sample = pa.Table.from_batches([batch])
            dates = sample["DateTime"].to_pylist()
            reference = root / "m1" / symbol / (str(dates[0].year) + ".parquet")
            if not reference.exists():
                continue
            reference_metadata = pq.read_schema(reference).metadata or {}
            bar_unit = float(reference_metadata.get(b"tick_size", str(step).encode()))
            tolerance = 2 * max(step, bar_unit)
            connection.register("sample", sample)
            bounds = [
                min(dates).replace(second=0, microsecond=0).isoformat(),
                max(dates).isoformat(),
            ]
            rows = connection.execute(
                "SELECT s.Bid, b.Low, b.High FROM sample s JOIN "
                "read_parquet(?) b ON b.DateTime=date_trunc('minute',s.DateTime) "
                "WHERE b.DateTime>=CAST(? AS TIMESTAMPTZ) "
                "AND b.DateTime<=CAST(? AS TIMESTAMPTZ)",
                [str(reference), *bounds],
            ).fetchall()
            for bid, low, high in rows:
                decoded = bid * float(RAW_STEP)
                if not low - tolerance <= decoded <= high + tolerance:
                    raise ValueError("Tick scale disagrees with overlapping M1 bar")
                matches += 1
            if matches >= 3:
                return matches
    if matches < 3:
        raise ValueError("Insufficient overlapping M1 evidence for tick price scale")
    return matches


@lru_cache(maxsize=128)
def scale_anchor(root: Path, symbol: str, step: float) -> int:
    """Independently establish the format using quotes paired to minute bars."""
    paths = sorted((root / "ticks" / symbol).rglob("*.parquet"))
    for index in dict.fromkeys([len(paths) // 2, len(paths) - 1, 0]):
        try:
            return sample_tick_scale(paths[index], root, step)
        except ValueError:
            continue
    raise ValueError("No independent M1 anchor verifies this symbol's tick scale")


@lru_cache(maxsize=1024)
def reference_bounds(path: Path) -> tuple[float, float]:
    """Read bar extrema from every row group of the overlapping reference year."""
    file = pq.ParquetFile(path)
    lows = []
    highs = []
    for index in range(file.metadata.num_row_groups):
        group = file.metadata.row_group(index)
        low = group.column(file.schema_arrow.get_field_index("Low")).statistics
        high = group.column(file.schema_arrow.get_field_index("High")).statistics
        if low is None or high is None or not low.has_min_max or not high.has_min_max:
            raise ValueError("Missing reference price statistics")
        lows.append(float(low.min))
        highs.append(float(high.max))
    return min(lows), max(highs)


def confirm_tick_scale(path: Path, root: Path, step: float) -> int:
    """Verify every tick partition's extrema uniquely imply the anchored scale."""
    file = pq.ParquetFile(path)
    symbol = path.relative_to(root / "ticks").parts[0]
    first, last = boundaries(file)
    if first[:4] != last[:4]:
        raise ValueError("Legacy tick partition crosses year boundary")
    low, high = reference_bounds(root / "m1" / symbol / (first[:4] + ".parquet"))
    lows = []
    highs = []
    for index in range(file.metadata.num_row_groups):
        stats = (
            file.metadata.row_group(index)
            .column(file.schema_arrow.get_field_index("Bid"))
            .statistics
        )
        if stats is None or not stats.has_min_max:
            raise ValueError("Missing tick price statistics")
        lows.append(stats.min)
        highs.append(stats.max)
    # Separate price series need not share exact extrema: retain original tick
    # outliers, but require every row group's price range to support one unit only.
    candidates = [
        10.0**exponent
        for exponent in range(-9, 1)
        if all(
            raw_low > 0
            and raw_low * 10.0**exponent <= high + 2 * step
            and raw_high * 10.0**exponent >= low - 2 * step
            for raw_low, raw_high in zip(lows, highs, strict=True)
        )
    ]
    if candidates != [float(RAW_STEP)]:
        raise ValueError("Tick scale disagrees with overlapping M1 price bounds")
    return scale_anchor(root, symbol, step)


def inspect_file(path: Path, root: Path, info: dict[str, Any]) -> dict[str, Any]:
    """Validate schema, identity, metadata and price-scale evidence for one file."""
    relative = path.relative_to(root)
    kind, symbol = relative.parts[:2]
    if path.is_symlink() or path.resolve() != path.absolute():
        raise ValueError("Linked input paths are not accepted")
    file = pq.ParquetFile(path)
    schema = file.schema_arrow
    expected = (
        ["DateTime", "Open", "High", "Low", "Close", "Volume"]
        if kind == "m1"
        else ["DateTime", "Ask", "Bid", "Volume"]
    )
    if schema.names != expected or not pa.types.is_timestamp(
        schema.field("DateTime").type
    ):
        raise ValueError("Unexpected legacy schema")
    first, last = boundaries(file)
    if kind == "m1":
        metadata = schema.metadata or {}
        recorded = Decimal(metadata.get(b"tick_size", b"0").decode())
        ratio = recorded / Decimal(str(info["step"]))
        if recorded <= 0 or ratio != ratio.to_integral_value() or ratio < 1:
            raise ValueError("M1 price unit is incompatible with the host catalogue")
        evidence = 0
    else:
        if not all(
            pa.types.is_int64(schema.field(name).type) for name in ["Ask", "Bid"]
        ):
            raise ValueError("Tick prices must use the audited integer format")
        evidence = confirm_tick_scale(path, root, info["step"])
    return {
        "relative": str(relative),
        "kind": kind,
        "symbol": symbol,
        "step": info["step"],
        "instrument_tick_size": info["instrument_tick_size"],
        "digits": info["digits"],
        "category": info["category"],
        "rows": file.metadata.num_rows,
        "first": first,
        "last": last,
        "fingerprint": fingerprint(path),
        "scale_matches": evidence,
    }


def audit_one(
    arguments: tuple[Path, Path, dict[str, dict[str, Any]]],
) -> tuple[dict[str, Any] | None, dict[str, str] | None]:
    """Validate one file in a bounded independent audit worker."""
    path, root, definitions = arguments
    relative = path.relative_to(root)
    try:
        return inspect_file(path, root, definitions[relative.parts[1]]), None
    except (ValueError, KeyError, OSError, pa.ArrowException) as error:
        return None, {"relative": str(relative), "error": str(error)}


def audit(project: Path, work: Path) -> dict[str, Any]:
    """Inventory every partition; reject complete datasets with ambiguous files."""
    root = project / "data/market/dukascopy"
    definitions = catalog(root)
    failures = []
    paths = sorted(
        [*(root / "m1").rglob("*.parquet"), *(root / "ticks").rglob("*.parquet")]
    )
    previous = (
        load(work / "audit.json") if (work / "audit.json").exists() else {"items": []}
    )
    available = {str(path.relative_to(root)): path for path in paths}
    cached = {
        item["relative"]: item
        for item in previous["items"]
        if item["relative"] in available
        and fingerprint(available[item["relative"]]) == item["fingerprint"]
        and definitions.get(item["symbol"], {}).get("step") == item["step"]
    }
    items = list(cached.values())
    pending = [path for path in paths if str(path.relative_to(root)) not in cached]
    with ThreadPoolExecutor(max_workers=4) as executor:
        checked = executor.map(
            audit_one, ((path, root, definitions) for path in pending)
        )
        for index, (item, error) in enumerate(checked):
            if item is not None:
                items.append(item)
            if error is not None:
                failures.append(error)
            if index % 100 == 0:
                logger.info(
                    "FR-LEGACY-ADOPTION-audit: checked %d/%d; rejected=%d",
                    len(cached) + index + 1,
                    len(paths),
                    len(failures),
                )
    items.sort(key=lambda item: item["relative"])
    result = {"project": str(project), "items": items, "failures": failures}
    save(work / "audit.json", result)
    logger.info(
        "FR-LEGACY-ADOPTION-audit: completed files=%d rejected=%d",
        len(items),
        len(failures),
    )
    return result


def all_true(value: pa.Array | pa.ChunkedArray) -> bool:
    """Treat null validation results as failures rather than silently accepting them."""
    return bool(pc.all(pc.fill_null(value, False)).as_py())


def tick_units(raw: pa.ChunkedArray, step: float) -> pa.ChunkedArray:
    """Rescale audited integer quotes exactly using integer arithmetic only."""
    divisor = Decimal(str(step)) / RAW_STEP
    if divisor < 1 or divisor != divisor.to_integral_value():
        raise ValueError("Unsupported legacy tick storage unit")
    units = pc.divide_checked(raw, int(divisor))
    if not all_true(pc.equal(pc.multiply_checked(units, int(divisor)), raw)):
        raise ValueError("Prices cannot be represented exactly in the host price unit")
    return units


def bar_units(raw: pa.ChunkedArray, step: float) -> pa.ChunkedArray:
    """Encode float bar prices only when round-trip units preserve each value."""
    scaled = pc.divide(pc.cast(raw, pa.float64()), step)
    rounded = pc.round(scaled)
    if not all_true(
        pc.and_(
            pc.is_finite(scaled),
            pc.less_equal(pc.abs(pc.subtract(scaled, rounded)), 0.000001),
        )
    ):
        raise ValueError("Prices cannot be represented exactly in the host price unit")
    return pc.cast(rounded, pa.int64())


def canonical(batch: pa.RecordBatch, item: dict[str, Any]) -> pa.Table:
    """Convert one bounded batch exactly; preserve unknown tick flags as null."""
    table = pa.Table.from_batches([batch])
    if any(table[name].null_count for name in table.column_names):
        raise ValueError("Legacy observations contain null required fields")
    dates = pc.cast(table["DateTime"], pa.timestamp("us", tz="UTC"))
    integers = pc.cast(dates, pa.int64())
    differences = pc.pairwise_diff(integers.combine_chunks())
    if pc.any(
        (pc.less_equal if item["kind"] == "m1" else pc.less)(differences, 0)
    ).as_py():
        raise ValueError("Legacy timestamps are not ordered")
    schema = M1_SCHEMA if item["kind"] == "m1" else TICK_SCHEMA
    columns: dict[str, Any] = {"DateTime": dates}
    prices = (
        ["Open", "High", "Low", "Close"] if item["kind"] == "m1" else ["Bid", "Ask"]
    )
    for name in prices:
        raw = table[name]
        if item["kind"] == "ticks":
            columns[name] = tick_units(raw, item["step"])
        else:
            columns[name] = bar_units(raw, item["step"])
        if not all_true(pc.greater(columns[name], 0)):
            raise ValueError("Prices must be positive")
    if item["kind"] == "m1":
        if pc.any(
            pc.not_equal(
                pc.multiply(pc.divide(integers, 60_000_000), 60_000_000), integers
            )
        ).as_py():
            raise ValueError("M1 timestamps are not minute aligned")
        for name in ["Open", "Close"]:
            if not all_true(
                pc.and_(
                    pc.greater_equal(columns[name], columns["Low"]),
                    pc.less_equal(columns[name], columns["High"]),
                )
            ):
                raise ValueError("Invalid OHLC ordering")
        columns["Volume"] = pc.cast(table["Volume"], pa.uint64())
    else:
        if not all_true(pc.greater_equal(columns["Ask"], columns["Bid"])):
            raise ValueError("Ask is below bid")
        columns["Flags"] = pa.nulls(table.num_rows, pa.uint16())
        columns["Volume"] = table["Volume"]
    metadata = {
        b"haruquantai.price_encoding": b"integer-ticks-v1",
        b"haruquantai.tick_size": str(item["step"]).encode(),
    }
    return pa.table(columns, schema=schema.with_metadata(metadata))


def parquet_options(schema: pa.Schema) -> dict[str, Any]:
    """Use lossless integer delta encoding for timestamps and canonical prices."""
    return {
        "compression": "zstd",
        "compression_level": 3,
        "use_dictionary": False,
        "column_encoding": {
            name: "DELTA_BINARY_PACKED" for name in schema.names if name != "Flags"
        },
    }


def convert_file(source: Path, target: Path, item: dict[str, Any]) -> dict[str, Any]:
    """Stream one partition to an atomic output without touching the source."""
    if fingerprint(source) != item["fingerprint"]:
        raise ValueError("Source changed since audit")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".converting")
    file = pq.ParquetFile(source)
    count = 0
    previous = None
    writer = None
    try:
        for batch in file.iter_batches(batch_size=BATCH):
            if shutil.disk_usage(target.parent).free < RESERVE:
                raise RuntimeError(
                    "Free-space reserve reached; conversion is resumable"
                )
            output = canonical(batch, item)
            first, last = output["DateTime"][0].as_py(), output["DateTime"][-1].as_py()
            if previous is not None and (
                first < previous or (item["kind"] == "m1" and first == previous)
            ):
                raise ValueError("Timestamp order crosses backwards between batches")
            previous = last
            if writer is None:
                writer = pq.ParquetWriter(
                    temporary, output.schema, **parquet_options(output.schema)
                )
            writer.write_table(output, row_group_size=BATCH)
            count += output.num_rows
    finally:
        if writer is not None:
            writer.close()
    if count != item["rows"] or fingerprint(source) != item["fingerprint"]:
        raise ValueError("Row reconciliation failed or input changed during conversion")
    if boundaries(pq.ParquetFile(temporary)) != (item["first"], item["last"]):
        raise ValueError("Output date bounds differ from the source")
    temporary.replace(target)
    return {
        "rows": count,
        "bytes": target.stat().st_size,
        "fingerprint": fingerprint(target),
        "input_fingerprint": item["fingerprint"],
    }


def eligible(report: dict[str, Any]) -> list[dict[str, Any]]:
    """Exclude the entire symbol/timeframe if any of its files failed audit."""
    rejected = {tuple(Path(item["relative"]).parts[:2]) for item in report["failures"]}
    return [
        item
        for item in report["items"]
        if (item["kind"], item["symbol"]) not in rejected
    ]


def estimate(project: Path, work: Path, items: list[dict[str, Any]]) -> int:
    """Estimate space using actual compressed batches from each symbol/timeframe."""
    samples: dict[tuple[str, str], float] = {}
    root = project / "data/market/dukascopy"
    for item in items:
        key = (item["kind"], item["symbol"])
        if key in samples:
            continue
        batch = next(
            pq.ParquetFile(root / item["relative"]).iter_batches(batch_size=BATCH)
        )
        output = canonical(batch, item)
        sink = io.BytesIO()
        pq.write_table(output, sink, **parquet_options(output.schema))
        samples[key] = len(sink.getvalue()) / output.num_rows
    required = math.ceil(
        sum(item["rows"] * samples[item["kind"], item["symbol"]] for item in items)
        * 1.2
    )
    save(
        work / "estimate.json",
        {"estimated_output_bytes": required, "reserve_bytes": RESERVE},
    )
    logger.info(
        "FR-LEGACY-ADOPTION-convert: estimated output=%d bytes; free=%d",
        required,
        shutil.disk_usage(work).free,
    )
    return int(required)


def convert_one(
    arguments: tuple[Path, Path, dict[str, Any]],
) -> tuple[str, dict[str, Any]]:
    """Convert an independent partition with one bounded worker allocation."""
    root, work, item = arguments
    relative = item["relative"]
    return relative, convert_file(root / relative, work / "output" / relative, item)


def convert(project: Path, work: Path) -> dict[str, Any]:
    """Resume only verified completed outputs and checkpoint after each partition."""
    report = load(work / "audit.json")
    if report["project"] != str(project):
        raise ValueError("Audit belongs to another project")
    items = eligible(report)
    progress = load(work / "progress.json") if (work / "progress.json").exists() else {}
    if (
        not progress
        and shutil.disk_usage(work).free < estimate(project, work, items) + RESERVE
    ):
        raise RuntimeError("Insufficient conversion space including reserve")
    pending = []
    root = project / "data/market/dukascopy"
    for item in items:
        relative = item["relative"]
        output = work / "output" / relative
        if fingerprint(root / relative) != item["fingerprint"]:
            raise ValueError("Source changed since audit")
        if (
            relative in progress
            and progress[relative].get("input_fingerprint") == item["fingerprint"]
            and output.exists()
            and fingerprint(output) == progress[relative]["fingerprint"]
        ):
            continue
        pending.append(item)
    with ThreadPoolExecutor(max_workers=6) as executor:
        converted = executor.map(
            convert_one, ((root, work, item) for item in pending), buffersize=6
        )
        for relative, result in converted:
            progress[relative] = result
            save(work / "progress.json", progress)
            logger.info(
                "FR-LEGACY-ADOPTION-convert: %d/%d %s rows=%d",
                len(progress),
                len(items),
                relative,
                result["rows"],
            )
    return progress


def dataset_records(
    project: Path, work: Path, items: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Build exact catalogue records and explicitly accepted per-file coverage spans."""
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for item in items:
        grouped.setdefault((item["kind"], item["symbol"]), []).append(item)
    result = []
    now = datetime.now(UTC).isoformat()
    for (kind, folder_symbol), files in grouped.items():
        root = project / "data/market/dukascopy" / kind / folder_symbol
        timeframe = "M1" if kind == "m1" else "TICK"
        symbol = folder_symbol.upper()
        lineage = {
            "tick_size": files[0]["step"],
            "instrument_tick_size": files[0].get(
                "instrument_tick_size", files[0]["step"]
            ),
            "digits": files[0]["digits"],
            "storage": "canonical-partitions-v1",
            "adoption": str(work),
            "provenance": "owner-supplied-legacy-history",
            "coverage_basis": "owner-accepted-legacy-file-spans",
            "partitions": [
                str(project / "data/market/dukascopy" / item["relative"])
                for item in files
            ],
            "covered_ranges": [
                {"from": item["first"], "to": item["last"]} for item in files
            ],
            "unknown_tick_flags": kind == "ticks",
            "original_tick_volume_retained_in_archive": kind == "ticks",
        }
        result.append(
            {
                "id": f"dukascopy:{symbol}:{timeframe}",
                "source": "dukascopy",
                "symbol": symbol,
                "underlying": symbol,
                "timeframe": timeframe,
                "broker": "Dukascopy",
                "timezone": "UTC",
                "category": files[0]["category"],
                "date_from": min(item["first"] for item in files),
                "date_to": max(item["last"] for item in files),
                "bars": sum(item["rows"] for item in files),
                "path": str(root),
                "data_kind": "bars" if kind == "m1" else "ticks",
                "created_at": now,
                "updated_at": now,
                "schema_version": 3 if kind == "ticks" else 2,
                "lineage_json": json.dumps(lineage),
            }
        )
    return result


def collision_error() -> None:
    """Reject duplicate dataset IDs without replacing existing records."""
    raise ValueError("Dataset identity collision; registration will not overwrite rows")


def archive_error() -> None:
    """Reject any pre-existing original archive destination."""
    raise FileExistsError("Original archive destination already exists")


def validate_publication(
    project: Path, work: Path, report: dict[str, Any], rows: list[dict[str, Any]]
) -> None:
    """Constrain every directory move and reject newly added or linked source files."""
    if report["project"] != str(project):
        raise ValueError("Audit belongs to another project")
    root = project / "data/market/dukascopy"
    for row in rows:
        destination = Path(row["path"])
        relative = destination.relative_to(root)
        if destination.resolve() != destination or not (
            work / "output" / relative
        ).resolve().is_relative_to(work):
            raise ValueError("Publication path escapes its approved root")
        expected = {
            str(Path(path).relative_to(root))
            for path in json.loads(row["lineage_json"])["partitions"]
        }
        observed = {
            str(path.relative_to(root)) for path in destination.rglob("*.parquet")
        }
        if expected != observed:
            raise ValueError("Source file inventory changed since audit")
        if (work / "original" / relative).exists():
            archive_error()


def publish(project: Path, work: Path) -> list[dict[str, Any]]:
    """Publish verified dataset directories offline with rollback and database backup."""
    ensure_offline()
    report = load(work / "audit.json")
    items = eligible(report)
    progress = load(work / "progress.json")
    root = project / "data/market/dukascopy"
    for item in items:
        relative = item["relative"]
        output = work / "output" / relative
        if (
            fingerprint(root / relative) != item["fingerprint"]
            or fingerprint(output) != progress[relative]["fingerprint"]
        ):
            raise ValueError("Source or converted partition changed before publication")
    rows = dataset_records(project, work, items)
    validate_publication(project, work, report, rows)
    gateway = HostPersistence(project / "data/database/haruquantai.db")
    moved: list[tuple[Path, Path]] = []
    try:
        with gateway.transaction() as tx:
            existing = {row["id"] for row in records(tx)}
            if any(row["id"] in existing for row in rows):
                collision_error()
            backup = work / "database-backup"
            backup.mkdir(exist_ok=True)
            for suffix in ("", "-wal"):
                path = Path(str(gateway.database_path) + suffix)
                if path.exists():
                    shutil.copy2(path, backup / path.name)
            for row in rows:
                destination = Path(row["path"])
                relative = destination.relative_to(root)
                archived = work / "original" / relative
                archived.parent.mkdir(parents=True, exist_ok=True)
                if archived.exists():
                    archive_error()
                destination.rename(archived)
                moved.append((destination, archived))
                (work / "output" / relative).rename(destination)
                moved.append((work / "output" / relative, destination))
            require(tx.create_records("datamgr_datasets", rows))
    except BaseException:
        for source, destination in reversed(moved):
            destination.rename(source)
        logger.warning("FR-LEGACY-ADOPTION-publish: rolled back publication")
        raise
    save(work / "registered.json", rows)
    logger.info("FR-LEGACY-ADOPTION-publish: registered %d datasets", len(rows))
    return rows


def guarded(path: Path, root: Path) -> Path:
    """Constrain destructive operations to an explicitly approved directory."""
    resolved = path.resolve()
    if (
        not resolved.is_relative_to(root.resolve())
        or resolved == root.resolve()
        or path.is_symlink()
        or path.is_junction()
    ):
        raise ValueError("Migration path escapes its approved directory")
    return resolved


def with_volume(old: pa.RecordBatch, original: pa.RecordBatch) -> pa.Table:
    """Attach the exact original volume after checking positional timestamp identity."""
    table = pa.Table.from_batches([old])
    raw = pa.Table.from_batches([original])
    dates = pc.cast(raw["DateTime"], pa.timestamp("us", tz="UTC"))
    if table.num_rows != raw.num_rows or not table["DateTime"].equals(dates):
        raise ValueError(
            "Original volume no longer aligns with active tick observations"
        )
    columns = {name: table[name] for name in ["DateTime", "Bid", "Ask", "Flags"]}
    columns["Volume"] = pc.cast(raw["Volume"], pa.uint64())
    metadata = dict(table.schema.metadata or {})
    metadata[b"haruquantai.schema_version"] = b"3"
    return pa.table(columns, schema=TICK_SCHEMA.with_metadata(metadata))


def verify_volume(active: Path, original: Path, upgraded: Path) -> int:
    """Compare every timestamp, price, flag and original volume in bounded batches."""
    old = pq.ParquetFile(active).iter_batches(batch_size=BATCH)
    raw = pq.ParquetFile(original).iter_batches(
        batch_size=BATCH, columns=["DateTime", "Volume"]
    )
    new = pq.ParquetFile(upgraded).iter_batches(batch_size=BATCH)
    count = 0
    for before, source, after in zip(old, raw, new, strict=True):
        if not with_volume(before, source).equals(pa.Table.from_batches([after])):
            raise ValueError("Volume upgrade changed recorded observations")
        count += after.num_rows
    return count


def stage_volume(
    arguments: tuple[Path, Path, Path, dict[str, Any]],
) -> tuple[str, Path, int]:
    """Write and independently reread a single bounded replacement partition."""
    project, work, archive, item = arguments
    relative = item["relative"]
    active = guarded(
        project / "data/market/dukascopy" / relative, project / "data/market/dukascopy"
    )
    original = guarded(archive / relative, archive)
    target = guarded(work / "volume-stage" / relative, work)
    target.parent.mkdir(parents=True, exist_ok=True)
    if "Volume" in pq.read_schema(active).names:
        return relative, active, verify_volume(active, original, active)
    old = pq.ParquetFile(active).iter_batches(batch_size=BATCH)
    raw = pq.ParquetFile(original).iter_batches(
        batch_size=BATCH, columns=["DateTime", "Volume"]
    )
    writer = None
    try:
        for before, source in zip(old, raw, strict=True):
            if shutil.disk_usage(work).free < RESERVE:
                raise RuntimeError("Free-space reserve reached")
            table = with_volume(before, source)
            if writer is None:
                writer = pq.ParquetWriter(
                    target, table.schema, **parquet_options(table.schema)
                )
            writer.write_table(table, row_group_size=BATCH)
    finally:
        if writer is not None:
            writer.close()
    with target.open("rb+") as stream:
        os.fsync(stream.fileno())
    return relative, target, verify_volume(active, original, target)


def retire_original(item: dict[str, Any], archive: Path) -> None:
    """Delete only a verified original at the exact audited location."""
    source = guarded(archive / item["relative"], archive)
    if source.exists():
        if fingerprint(source) != item["fingerprint"]:
            raise ValueError("Original changed before retirement")
        source.unlink()


def volume_preflight(
    project: Path, work: Path, items: list[dict[str, Any]], state: dict[str, Any]
) -> None:
    """Reject concurrent changes and recover interrupted atomic replacements."""
    initial = load(work / "progress.json")
    root = project / "data/market/dukascopy"
    for item in items:
        relative = item["relative"]
        active = guarded(root / relative, root)
        backup = guarded(active.with_name("." + active.name + ".volume-backup"), root)
        if backup.exists():
            if relative not in state:
                if active.exists():
                    active.unlink()
                backup.rename(active)
            elif fingerprint(active) == state[relative]["fingerprint"]:
                backup.unlink()
            else:
                raise ValueError("Checkpointed replacement changed; backup retained")
        expected = state.get(relative, initial[relative])["fingerprint"]
        if fingerprint(active) != expected:
            raise ValueError("Active data changed since the verified adoption snapshot")


def cleanup_originals(archive: Path) -> None:
    """Remove only known metadata after every observation file was retired."""
    if archive.exists():
        for path in archive.rglob("*"):
            if path.is_file():
                if path.name != "metadata.json":
                    raise ValueError("Unexpected legacy file remains; cleanup stopped")
                guarded(path, archive).unlink()
        for path in sorted(
            archive.rglob("*"), key=lambda path: len(path.parts), reverse=True
        ):
            if path.is_dir():
                guarded(path, archive).rmdir()
        archive.rmdir()


def pending_volume(
    project: Path, work: Path, items: list[dict[str, Any]], state: dict[str, Any]
) -> list[dict[str, Any]]:
    """Checkpoint verified bar files and queue untouched tick originals."""
    archive = work / "original"
    pending: list[dict[str, Any]] = []
    for item in items:
        relative = item["relative"]
        if relative in state:
            retire_original(item, archive)
        elif item["kind"] == "m1":
            state[relative] = {
                "fingerprint": fingerprint(
                    project / "data/market/dukascopy" / relative
                ),
                "rows": item["rows"],
            }
            save(work / "volume-progress.json", state)
            retire_original(item, archive)
        else:
            if fingerprint(archive / relative) != item["fingerprint"]:
                raise ValueError("Original tick partition changed")
            pending.append(item)
    return pending


def preserve_volume(project: Path, work: Path) -> dict[str, Any]:
    """Upgrade recorded volumes and retire originals after full verified replacement."""
    ensure_offline()
    archive = work / "original"
    report = load(work / "audit.json")
    items = eligible(report)
    state_path = work / "volume-progress.json"
    state = load(state_path) if state_path.exists() else {}
    volume_preflight(project, work, items, state)
    gateway = HostPersistence(project / "data/database/haruquantai.db")
    before = records(gateway)
    backup = work / "pre-volume-database"
    if not backup.exists():
        backup.mkdir()
        with gateway.transaction():
            for suffix in ("", "-wal"):
                path = Path(str(gateway.database_path) + suffix)
                if path.exists():
                    shutil.copy2(path, backup / path.name)
    pending = pending_volume(project, work, items, state)
    lookup = {item["relative"]: item for item in items}
    with ThreadPoolExecutor(max_workers=4) as executor:
        staged = executor.map(
            stage_volume,
            ((project, work, archive, item) for item in pending),
            buffersize=4,
        )
        for relative, stage, count in staged:
            item = lookup[relative]
            if count != item["rows"]:
                raise ValueError("Volume upgrade row count differs")
            active = project / "data/market/dukascopy" / relative
            old = active.with_name("." + active.name + ".volume-backup")
            if stage != active:
                active.rename(old)
                try:
                    stage.rename(active)
                except BaseException:
                    old.rename(active)
                    raise
            state[relative] = {"fingerprint": fingerprint(active), "rows": count}
            save(state_path, state)
            if old.exists():
                old.unlink()
            retire_original(item, archive)
            logger.info(
                "FR-LEGACY-ADOPTION-volume: %d/%d verified and retired %s",
                len(state),
                len(items),
                relative,
            )
    with gateway.transaction() as tx:
        for row in before:
            if row["id"] not in {r["id"] for r in load(work / "registered.json")}:
                continue
            lineage = json.loads(row["lineage_json"])
            lineage.update(
                original_tick_volume_retained_in_archive=False,
                legacy_originals_removed=True,
            )
            if row["timeframe"] == "TICK":
                lineage["tick_volume_storage"] = "canonical-uint64"
            require(
                tx.update_record(
                    "datamgr_datasets",
                    {
                        "schema_version": 3 if row["timeframe"] == "TICK" else 2,
                        "lineage_json": json.dumps(lineage),
                        "updated_at": datetime.now(UTC).isoformat(),
                    },
                    filters={"id": row["id"]},
                )
            )
    cleanup_originals(archive)
    result = {
        "verified_files": len(state),
        "rows": sum(item["rows"] for item in items),
        "legacy_originals_removed": True,
    }
    save(work / "volume-verification.json", result)
    logger.info("FR-LEGACY-ADOPTION-volume: completed with one market-data version")
    return result


def run(project: Path, work: Path, *, phase: str) -> Any:
    """Resolve operator paths and dispatch an explicitly selected migration phase."""
    project = project.resolve(strict=True)
    work = work.resolve()
    if work.is_relative_to(project) or work.drive != project.drive:
        raise ValueError(
            "Work/archive directory must be outside checkout on the same volume"
        )
    work.mkdir(parents=True, exist_ok=True)
    actions = {
        "audit": audit,
        "convert": convert,
        "publish": publish,
        "preserve-volume": preserve_volume,
    }
    return actions[phase](project, work)


def main() -> None:
    """Run only a named phase; final publication requires an offline host."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument(
        "--phase",
        choices=["audit", "convert", "publish", "preserve-volume"],
        required=True,
    )
    args = parser.parse_args()
    run(Path(__file__).resolve().parents[1], args.work_dir, phase=args.phase)


if __name__ == "__main__":
    main()
