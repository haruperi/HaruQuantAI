"""Job-owned local history ingestion using existing codecs and canonical publication."""

from __future__ import annotations

import base64
import csv
import gzip
import io
import json
import math
import re
import tempfile
import uuid
import zipfile
from contextlib import suppress
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import APIRouter, Request

from app.host.response import ErrorCode
from app.host.transport import TransportError
from app.workspace.brokers.darwinex import decode_darwinex_dat
from app.workspace.brokers.files import decode_fxt_bytes, decode_hst_bytes
from app.workspace.data_manager.data._helpers import validate_dataset_updates
from app.workspace.data_manager.data.storage import publish_frame, require_data

from .download_jobs import manager

MAX_INPUT = 25_000_000
BATCH_ROWS = 50_000
MAX_FILES = 1000


def _cleanup_inputs(folder: str) -> None:
    """Retire only staged numbered inputs inside the OS temporary directory."""
    root = Path(folder).resolve()
    temporary = Path(tempfile.gettempdir()).resolve()
    if root == temporary or not root.is_relative_to(temporary) or not root.is_dir():
        return
    for path in root.iterdir():
        if path.is_file() and re.fullmatch(r"[0-9]+\.input", path.name):
            path.unlink(missing_ok=True)
    with suppress(OSError):
        root.rmdir()


def _csv_observation(
    cells: list[str], columns: list[str], skip: int, fmt: dict[str, Any]
) -> dict[str, Any]:
    """Decode one date/time and price row; the caller owns abort/skip policy."""
    values = {
        column: cells[index + skip]
        for index, column in enumerate(columns)
        if column and column != "Unused"
    }
    stamp = (
        values.get("Date & Time") or values.get("Datetime") or values.get("Timestamp")
    )
    if stamp is None:
        stamp = values.get("Date", "") + " " + values.get("Time", "")
    pattern = fmt.get("dateFormat") or None
    if pattern:
        for old, new in (
            ("yyyy", "%Y"),
            ("MM", "%m"),
            ("dd", "%d"),
            ("HH", "%H"),
            ("mm", "%M"),
            ("ss", "%S"),
            ("SSS", "%f"),
        ):
            pattern = pattern.replace(old, new)
        if values.get("Time") and "%H" not in pattern:
            pattern += " %H:%M:%S"
    parsed = pd.to_datetime(stamp.strip(), format=pattern)
    numeric = {
        key: float(value)
        for key, value in values.items()
        if key in {"Open", "High", "Low", "Close", "Bid", "Ask", "Volume"}
    }
    if not all(math.isfinite(value) for value in numeric.values()):
        raise ValueError("Nonfinite value")
    return {"DateTime": parsed, **numeric}


def _utc_clock(stamps: pd.DatetimeIndex, zone: str) -> pd.DatetimeIndex:
    """Resolve known broker clock aliases and reject ambiguous DST timestamps."""
    if stamps.tz is None:
        if zone == "EETUS":
            stamps = (stamps - pd.Timedelta(hours=7)).tz_localize(
                "America/New_York", ambiguous="raise", nonexistent="raise"
            )
        else:
            stamps = stamps.tz_localize(
                "Europe/Helsinki" if zone == "EET" else zone,
                ambiguous="raise",
                nonexistent="raise",
            )
    return stamps.tz_convert("UTC")


def _csv_frame(
    content: bytes, options: dict[str, Any]
) -> tuple[pd.DataFrame, list[str]]:
    """Apply explicit CSV mappings and resolve local clocks to UTC."""
    errors: list[str] = []
    text = content.decode("utf-8-sig")
    fmt = options.get("format") or {}
    separator = (
        fmt.get("separator")
        or csv.Sniffer().sniff(text[:8192], delimiters=",;\t|").delimiter
    )
    if len(separator) != 1:
        raise ValueError("Choose a single character delimiter")
    reader = csv.reader(io.StringIO(text), delimiter=separator)
    for _ in range(int(fmt.get("skipRows", 0))):
        next(reader, None)
    columns = fmt.get("columns")
    if not columns:
        columns = [str(cell).strip().strip("<>").title() for cell in next(reader)]
    skip = int(fmt.get("skipColumns", 0))
    decoded = []
    for line, cells in enumerate(reader, 1):
        if not cells or not any(cells):
            continue
        try:
            decoded.append(_csv_observation(cells, columns, skip, fmt))
        except (ValueError, TypeError, IndexError) as error:
            if not options.get("ignore_errors"):
                raise ValueError(f"Row {line}: {error}") from error
            errors.append(f"Row {line}: {error}")
    frame = pd.DataFrame(decoded)
    if frame.empty:
        raise ValueError("No valid price records")
    frame.index = _utc_clock(
        pd.DatetimeIndex(frame.pop("DateTime")), options.get("timezone") or "UTC"
    )
    return frame, errors


def _binary_frame(content: bytes, decoder: Any) -> pd.DataFrame:
    """Decode existing application/provider codecs without changing their algorithms."""
    rows = decoder(content)
    frame = pd.DataFrame(rows)
    if frame.empty:
        raise ValueError("No history records found in archive")
    timestamp = "time_msc" if "time_msc" in frame else "time"
    frame.index = pd.to_datetime(
        frame.pop(timestamp),
        unit="ms" if timestamp == "time_msc" else "s",
        utc=True,
    )
    return frame.rename(
        columns={
            key: "Volume" if key == "tick_volume" else key.capitalize()
            for key in frame.columns
        }
    )


def preview_import(
    content: bytes, name: str, options: dict[str, Any]
) -> tuple[pd.DataFrame, list[str]]:
    """Decode one bounded file with explicit columns, dates and timezone semantics."""
    if not content or len(content) > MAX_INPUT:
        raise ValueError("Choose a nonempty input up to 25 MB")
    suffix = Path(name).suffix.lower()
    errors: list[str] = []
    if suffix in {".hst", ".fxt", ".dat"}:
        decoder = {
            ".hst": decode_hst_bytes,
            ".fxt": decode_fxt_bytes,
            ".dat": decode_darwinex_dat,
        }[suffix]
        frame = _binary_frame(content, decoder)
    elif suffix == ".parquet":
        frame = pd.read_parquet(io.BytesIO(content))
        if "DateTime" in frame:
            frame.index = pd.to_datetime(frame.pop("DateTime"), utc=True)
    else:
        frame, errors = _csv_frame(content, options)
    tick = (
        "Bid" in frame
        if str(options.get("timeframe", "M1")).lower() == "auto"
        else str(options.get("timeframe", "M1")).upper() == "TICK"
    )
    required = ["Bid", "Ask"] if tick else ["Open", "High", "Low", "Close"]
    if set(required) - set(frame.columns):
        raise ValueError(f"Missing price columns: {required}")
    if (
        not tick
        and (
            (frame.High < frame[["Open", "Close", "Low"]].max(axis=1))
            | (frame.Low > frame[["Open", "Close", "High"]].min(axis=1))
        ).any()
    ):
        raise ValueError("Invalid OHLC relationship")
    if tick and (frame.Ask < frame.Bid).any():
        raise ValueError("Ask cannot be below bid")
    if not tick and "Volume" not in frame:
        frame["Volume"] = 0
    if options.get("bar_type") == "end" and not tick:
        timeframe = options.get("timeframe", "M1")
        units = {"M": "min", "H": "h", "D": "D", "W": "W"}
        frame.index -= pd.Timedelta(int(timeframe[1:]), unit=units[timeframe[0]])
    frame.index.name = "DateTime"
    return frame.sort_index(), errors


def import_files(
    context: Any, gateway: Any, folder: str, manifest: list[dict[str, Any]], logs: Any
) -> dict[str, Any]:
    """Publish actual file prices; failures retain only explicitly committed batches."""
    committed, errors = [], []
    try:
        for index, item in enumerate(manifest):
            context.wait_if_paused()
            context.raise_if_cancelled()
            frame, skipped = preview_import(
                Path(folder, item["staged"]).read_bytes(), item["name"], item
            )
            if str(item.get("timeframe")).lower() == "auto":
                item["timeframe"] = "TICK" if "Bid" in frame else "M1"
            record = validate_dataset_updates(item)
            require_data(gateway.ensure_datasets_schema())
            existing = require_data(
                gateway.read_records(
                    "datamgr_datasets",
                    filters={
                        "source": record["source"],
                        "symbol": record["symbol"],
                        "timeframe": record["timeframe"],
                    },
                    limit=1,
                )
            )["records"]
            if existing:
                record = existing[0]
            step = json.loads(record["lineage_json"])["tick_size"]
            storage_root = (
                Path(item.get("market_root") or "data/market") / record["source"]
            )
            for start in range(0, len(frame), BATCH_ROWS):
                context.wait_if_paused()
                context.raise_if_cancelled()
                batch = frame.iloc[start : start + BATCH_ROWS]
                publish_frame(
                    gateway,
                    storage_root,
                    record,
                    batch,
                    step,
                    overwrite=bool(item.get("overwrite")),
                    context=context,
                )
                progress = (
                    100
                    * (index + min(1, (start + len(batch)) / len(frame)))
                    / len(manifest)
                )
                context.report_progress(progress, f"Imported {item['name']}")
                logs.record_progress(
                    context.job_id,
                    progress=progress,
                    message=f"Committed {len(batch)} records from {item['name']}",
                )
            committed.append(record["id"])
            errors.extend(skipped)
        return {"datasets": committed, "completed": len(committed), "errors": errors}
    except BaseException:
        logs.record_progress(
            context.job_id,
            progress=-1,
            level="error",
            message="Import interrupted; committed batches retained",
        )
        raise
    finally:
        _cleanup_inputs(folder)


def _preview_import_request(body: dict[str, Any]) -> dict[str, Any]:
    """Return a bounded preview of an uploaded file."""
    try:
        raw = (
            base64.b64decode(body["base64"], validate=True)
            if "base64" in body
            else body.get("content", "").encode()
        )
        frame, errors = preview_import(raw, body.get("name", "data.csv"), body)
        return {
            "success": True,
            "data": {
                "count": len(frame),
                "columns": list(frame.columns),
                "errors": errors,
                "date_from": frame.index.min().isoformat(),
                "date_to": frame.index.max().isoformat(),
            },
        }
    except (ValueError, TypeError, KeyError, csv.Error) as error:
        raise TransportError(ErrorCode.VALIDATION, str(error)) from error


def _expanded_inputs(name: str, raw: bytes) -> list[tuple[str, bytes]]:
    """Expand supported archives only within explicit uncompressed size limits."""
    members = [(name, raw)]
    if name.lower().endswith(".gz"):
        with gzip.GzipFile(fileobj=io.BytesIO(raw)) as stream:
            members = [(name[:-3], stream.read(MAX_INPUT + 1))]
    elif name.lower().endswith(".zip"):
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            if (
                len(archive.infolist()) > MAX_FILES
                or sum(info.file_size for info in archive.infolist()) > MAX_INPUT
            ):
                raise ValueError("Expanded archive exceeds limits")
            members = [
                (info.filename, archive.read(info))
                for info in archive.infolist()
                if not info.is_dir()
            ]
    return members


def _submit_import_request(request: Request, body: dict[str, Any]) -> dict[str, Any]:
    """Stage uploaded files until the real import worker releases them."""
    from app.workspace.data_manager.logs import Logs

    job_id = "job-" + uuid.uuid4().hex[:20]
    folder = str(Path(tempfile.gettempdir()) / ("haru-history-import-" + job_id))
    Path(folder).mkdir()
    manifest: list[dict[str, Any]] = []
    try:
        inputs = body.get("files") or [body]
        if not isinstance(inputs, list) or not 1 <= len(inputs) <= MAX_FILES:
            raise ValueError("Select between 1 and 1000 files")  # noqa: TRY301 - enclosing scope owns rollback
        total = 0
        expanded_total = 0
        for item in inputs:
            raw = (
                base64.b64decode(item["base64"], validate=True)
                if "base64" in item
                else str(item.get("content", "")).encode()
            )
            total += len(raw)
            if not raw or total > MAX_INPUT:
                raise ValueError("Upload real file content, up to 25 MB per request")  # noqa: TRY301 - enclosing scope owns rollback
            name = item.get("name") or "data.csv"
            members = _expanded_inputs(name, raw)
            for member, content in members:
                expanded_total += len(content)
                if expanded_total > MAX_INPUT or len(manifest) >= MAX_FILES:
                    raise ValueError("Expanded files exceed upload limits")  # noqa: TRY301 - enclosing scope owns rollback
                staged = f"{len(manifest)}.input"
                Path(folder, staged).write_bytes(content)
                options = {**body, **item, "name": member, "staged": staged}
                options.pop("files", None)
                options.pop("base64", None)
                options.pop("content", None)
                options.setdefault("source", "files")
                options["market_root"] = str(
                    getattr(request.app.state, "data_market_root", Path("data/market"))
                )
                if "symbol" not in options:
                    options["symbol"] = Path(member).stem
                validate_dataset_updates(
                    {
                        **options,
                        "timeframe": "M1"
                        if str(options.get("timeframe")).lower() == "auto"
                        else options.get("timeframe", "M1"),
                    }
                )
                manifest.append(options)
        logs = getattr(request.app.state, "data_logs", None) or Logs()
        record = manager(request).submit_job(
            import_files,
            request.app.state.persistence,
            folder,
            manifest,
            logs,
            job_id=job_id,
            owner="data-manager",
            kind="market.import",
            executor_kind="thread",
            pass_context=True,
        )
        if record.status not in {"QUEUED", "RUNNING", "PAUSED", "COMPLETED"}:
            _cleanup_inputs(folder)
        return {"success": True, "data": record.to_dict()}
    except (ValueError, TypeError, KeyError, OSError, zipfile.BadZipFile) as error:
        _cleanup_inputs(folder)
        raise TransportError(ErrorCode.VALIDATION, str(error)) from error


def register_file_routes(router: APIRouter) -> None:
    """Register the two shared uploaded-history operations."""
    router.add_api_route(
        "/datasets/import-preview", _preview_import_request, methods=["POST"]
    )
    router.add_api_route("/datasets/import", _submit_import_request, methods=["POST"])
