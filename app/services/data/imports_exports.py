"""Tabular file ingestion and multi-platform dataset egress.

Feature:
    FEAT-DATA-IMPORTS-EXPORTS

Purpose:
    Provides parsing, validation, and normalization of tabular CSV/TXT market data,
    registering immutable dataset versions. Exports normalized datasets into
    CSV, MetaTrader (MT4/MT5), and custom formats matching StrategyQuant X
    DataFormat, DataLoader, and DataExporter.

Invariants:
    * Malformed rows are logged and isolated; valid rows proceed with error ledger.
    * Dates are parsed into timezone-aware UTC instants.
    * Exported files are written atomically with SHA-256 integrity verification.
"""

from __future__ import annotations

import asyncio
import csv
import hashlib
import struct
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, override

from app.contracts.data import (
    DATA_DATASETS,
    DATA_IMPORTS_EXPORTS,
    DATA_PERSISTENCE,
    DATA_QUALITY,
    DATA_SESSIONS,
    BarRecord,
    DataFormatSpecification,
    DataPersistenceService,
    DatasetManifest,
    DatasetNotFoundError,
    DatasetService,
    ExportResult,
    ExportWriteError,
    ImportParseError,
    ImportResult,
    QualityReport,
    QualityService,
    SessionDefinition,
    SessionNotFoundError,
    SessionService,
    TickRecord,
    UnsupportedExportFormatError,
)
from app.contracts.data import (
    ImportExportService as IImportExportService,
)
from app.kernel.feature import FeatureSpec
from app.kernel.logging import get_logger

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext

logger = get_logger(__name__)


def _compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 digest of a local file."""
    hasher = hashlib.sha256()
    with file_path.open("rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def _parse_tabular_bars(
    file_path: Path,
    spec: DataFormatSpecification,
) -> tuple[list[BarRecord], list[str]]:
    """Parse CSV/TXT file into BarRecord objects with error tracking."""
    if not file_path.exists():
        msg = f"Import file does not exist: {file_path}"
        raise ImportParseError(msg)

    bars: list[BarRecord] = []
    errors: list[str] = []

    with file_path.open("r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f, delimiter=spec.delimiter)
        if spec.has_header:
            next(reader, None)

        for line_num, row in enumerate(reader, start=2 if spec.has_header else 1):
            if not row or not any(row):
                continue
            try:
                # 1. Parse timestamp
                if spec.time_col is not None:
                    d_val = row[spec.date_col].strip()
                    t_val = row[spec.time_col].strip()
                    dt_str = f"{d_val} {t_val}"
                else:
                    dt_str = row[spec.date_col].strip()

                parsed = datetime.strptime(  # noqa: DTZ007
                    dt_str, spec.datetime_format
                )
                dt = (
                    parsed.replace(tzinfo=UTC)
                    if parsed.tzinfo is None
                    else parsed.astimezone(UTC)
                )

                # 2. Parse prices
                open_p = float(row[spec.open_col].strip())
                high_p = float(row[spec.high_col].strip())
                low_p = float(row[spec.low_col].strip())
                close_p = float(row[spec.close_col].strip())
                volume = (
                    float(row[spec.volume_col].strip())
                    if spec.volume_col is not None and len(row) > spec.volume_col
                    else 0.0
                )

                bar = BarRecord(
                    timestamp=dt,
                    open=open_p,
                    high=high_p,
                    low=low_p,
                    close=close_p,
                    volume=volume,
                    source=file_path.name,
                )
                bars.append(bar)
            except (ValueError, IndexError, KeyError) as exc:
                errors.append(f"Line {line_num}: {exc}")

    return bars, errors


def _parse_tabular_ticks(
    file_path: Path,
    spec: DataFormatSpecification,
) -> tuple[list[TickRecord], list[str]]:
    """Parse CSV/TXT file into TickRecord objects with error tracking."""
    if not file_path.exists():
        msg = f"Import file does not exist: {file_path}"
        raise ImportParseError(msg)

    ticks: list[TickRecord] = []
    errors: list[str] = []

    bid_idx = spec.bid_col if spec.bid_col is not None else spec.open_col
    ask_idx = spec.ask_col if spec.ask_col is not None else spec.high_col

    with file_path.open("r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f, delimiter=spec.delimiter)
        if spec.has_header:
            next(reader, None)

        for line_num, row in enumerate(reader, start=2 if spec.has_header else 1):
            if not row or not any(row):
                continue
            try:
                if spec.time_col is not None:
                    d_val = row[spec.date_col].strip()
                    t_val = row[spec.time_col].strip()
                    dt_str = f"{d_val} {t_val}"
                else:
                    dt_str = row[spec.date_col].strip()

                parsed = datetime.strptime(  # noqa: DTZ007
                    dt_str, spec.datetime_format
                )
                dt = (
                    parsed.replace(tzinfo=UTC)
                    if parsed.tzinfo is None
                    else parsed.astimezone(UTC)
                )

                bid = float(row[bid_idx].strip())
                ask = float(row[ask_idx].strip())
                vol = (
                    float(row[spec.volume_col].strip())
                    if spec.volume_col is not None and len(row) > spec.volume_col
                    else 0.0
                )

                ticks.append(
                    TickRecord(
                        timestamp=dt,
                        bid=bid,
                        ask=ask,
                        sequence=line_num,
                        bid_volume=vol,
                        ask_volume=vol,
                    )
                )
            except (ValueError, IndexError, KeyError) as exc:
                errors.append(f"Line {line_num}: {exc}")

    return ticks, errors


def _export_bars_to_csv(
    bars: list[BarRecord],
    out_path: Path,
    delimiter: str,
    include_header: bool,
) -> tuple[int, int, str, str]:
    """Synchronous worker to write bars to CSV file."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = out_path.with_name(f"{out_path.stem}.tmp{out_path.suffix}")

    try:
        with temp_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=delimiter)
            if include_header:
                writer.writerow(
                    ["Date", "Time", "Open", "High", "Low", "Close", "Volume"]
                )

            for b in bars:
                date_str = b.timestamp.strftime("%Y.%m.%d")
                time_str = b.timestamp.strftime("%H:%M:%S")
                writer.writerow(
                    [
                        date_str,
                        time_str,
                        f"{b.open:.5f}",
                        f"{b.high:.5f}",
                        f"{b.low:.5f}",
                        f"{b.close:.5f}",
                        f"{b.volume:.2f}",
                    ]
                )

        temp_path.replace(out_path)
        bytes_written = out_path.stat().st_size
        sha256 = _compute_sha256(out_path)
        return len(bars), bytes_written, sha256, str(out_path.resolve())
    finally:
        temp_path.unlink(missing_ok=True)


def _export_ticks_to_csv(
    ticks: list[TickRecord],
    out_path: Path,
    delimiter: str,
    include_header: bool,
) -> tuple[int, int, str, str]:
    """Synchronous worker to write ticks to CSV file."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = out_path.with_name(f"{out_path.stem}.tmp{out_path.suffix}")

    try:
        with temp_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=delimiter)
            if include_header:
                writer.writerow(["Date", "Time", "Bid", "Ask", "Volume"])

            for t in ticks:
                date_str = t.timestamp.strftime("%Y.%m.%d")
                time_str = t.timestamp.strftime("%H:%M:%S.%f")[:-3]
                writer.writerow(
                    [
                        date_str,
                        time_str,
                        f"{t.bid:.5f}",
                        f"{t.ask:.5f}",
                        f"{t.bid_volume:.2f}",
                    ]
                )

        temp_path.replace(out_path)
        bytes_written = out_path.stat().st_size
        sha256 = _compute_sha256(out_path)
        return len(ticks), bytes_written, sha256, str(out_path.resolve())
    finally:
        temp_path.unlink(missing_ok=True)


def _timeframe_to_minutes(timeframe: str) -> int:
    """Convert standard timeframe string to integer period in minutes."""
    tf = timeframe.upper().strip()
    if tf.startswith("M") and tf[1:].isdigit():
        return int(tf[1:])
    if tf.startswith("H") and tf[1:].isdigit():
        return int(tf[1:]) * 60
    if tf == "D1":
        return 1440
    if tf == "W1":
        return 10080
    if tf in {"MN1", "MN"}:
        return 43200
    return 1


_MIN_SEPARATE_COL_COUNT: int = 7


def _sniff_delimiter(first_line: str) -> str:
    """Detect delimiter character from first line."""
    candidates = [",", ";", "\t", "|"]
    delimiter = max(candidates, key=first_line.count)
    return delimiter if first_line.count(delimiter) > 0 else ","


_HEADER_FIELD_MAP: dict[str, str] = {
    "open": "open",
    "o": "open",
    "high": "high",
    "h": "high",
    "low": "low",
    "l": "low",
    "close": "close",
    "c": "close",
    "vol": "volume",
    "volume": "volume",
    "v": "volume",
    "tick_volume": "volume",
    "bid": "bid",
    "b": "bid",
    "ask": "ask",
    "a": "ask",
}


def _map_header_columns(tokens_lower: list[str]) -> dict[str, int | None]:
    """Map column positions from header names."""
    cols: dict[str, int | None] = {
        "date": 0,
        "time": None,
        "open": 1,
        "high": 2,
        "low": 3,
        "close": 4,
        "volume": 5,
        "bid": None,
        "ask": None,
    }
    has_date_or_day = any(tok in {"date", "day"} for tok in tokens_lower)
    for idx, token in enumerate(tokens_lower):
        if token in _HEADER_FIELD_MAP:
            cols[_HEADER_FIELD_MAP[token]] = idx
        elif token in {"datetime", "date_time"}:
            cols["date"] = idx
            cols["time"] = None
        elif token in {"date", "day"} and cols["time"] is None:
            cols["date"] = idx
        elif token in {"time", "timestamp"}:
            if has_date_or_day:
                cols["time"] = idx
            else:
                cols["date"] = idx
    return cols


def _sniff_datetime_format(
    sample_tokens: list[str], date_col: int, time_col: int | None
) -> str:
    """Infer datetime format string from sample tokens."""
    if date_col >= len(sample_tokens):
        return "%Y-%m-%d %H:%M:%S"

    d_val = sample_tokens[date_col]
    fmt = "%Y-%m-%d %H:%M:%S"

    if time_col is not None and time_col < len(sample_tokens):
        if "." in d_val:
            fmt = "%Y.%m.%d %H:%M:%S"
        elif "/" in d_val:
            fmt = "%Y/%m/%d %H:%M:%S"
    elif "." in d_val:
        fmt = "%Y.%m.%d %H:%M:%S" if " " in d_val else "%Y.%m.%d"
    elif "T" in d_val:
        fmt = "%Y-%m-%dT%H:%M:%SZ" if d_val.endswith("Z") else "%Y-%m-%dT%H:%M:%S"

    return fmt


def _sniff_format_spec(file_path: Path) -> DataFormatSpecification:
    """Infer delimiter, header existence, and column mapping from file content."""
    lines: list[str] = []
    with file_path.open("r", encoding="utf-8", errors="replace") as f:
        for _ in range(10):
            line = f.readline()
            if not line:
                break
            line_stripped = line.strip()
            if line_stripped:
                lines.append(line_stripped)

    if not lines:
        return DataFormatSpecification()

    delimiter = _sniff_delimiter(lines[0])
    tokens = [t.strip() for t in lines[0].split(delimiter)]
    tokens_lower = [t.lower() for t in tokens]

    header_keywords = {
        "date",
        "time",
        "datetime",
        "timestamp",
        "open",
        "high",
        "low",
        "close",
        "vol",
        "volume",
        "bid",
        "ask",
    }
    has_header = any(t in header_keywords for t in tokens_lower)

    if has_header:
        cols = _map_header_columns(tokens_lower)
    elif len(tokens) >= _MIN_SEPARATE_COL_COUNT and ":" in tokens[1]:
        cols = {
            "date": 0,
            "time": 1,
            "open": 2,
            "high": 3,
            "low": 4,
            "close": 5,
            "volume": 6,
            "bid": None,
            "ask": None,
        }
    else:
        cols = {
            "date": 0,
            "time": None,
            "open": 1,
            "high": 2,
            "low": 3,
            "close": 4,
            "volume": 5,
            "bid": None,
            "ask": None,
        }

    sample_line = lines[1] if has_header and len(lines) > 1 else lines[0]
    sample_tokens = [t.strip() for t in sample_line.split(delimiter)]
    dt_fmt = _sniff_datetime_format(sample_tokens, cols["date"] or 0, cols["time"])

    return DataFormatSpecification(
        delimiter=delimiter,
        has_header=has_header,
        datetime_format=dt_fmt,
        date_col=cols["date"] or 0,
        time_col=cols["time"],
        open_col=cols["open"] or 1,
        high_col=cols["high"] or 2,
        low_col=cols["low"] or 3,
        close_col=cols["close"] or 4,
        volume_col=cols["volume"],
        bid_col=cols["bid"],
        ask_col=cols["ask"],
    )


def _export_bars_to_mt4_hst(
    bars: list[BarRecord],
    symbol: str,
    timeframe: str,
    out_path: Path,
) -> tuple[int, int, str, str]:
    """Export normalized bars into MetaTrader 4 HST format."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = out_path.with_name(f"{out_path.stem}.tmp{out_path.suffix}")

    version = 401
    copyright_str = b"HaruQuantAI MT4 HST\x00"[:64].ljust(64, b"\x00")
    sym_bytes = symbol.encode("ascii", errors="replace")[:11].ljust(12, b"\x00")
    period = _timeframe_to_minutes(timeframe)
    digits = 5
    timesign = int(bars[0].timestamp.timestamp()) if bars else 0
    last_sync = int(bars[-1].timestamp.timestamp()) if bars else 0
    unused = b"\x00" * 52

    header = struct.pack(
        "<i64s12siiii52s",
        version,
        copyright_str,
        sym_bytes,
        period,
        digits,
        timesign,
        last_sync,
        unused,
    )

    try:
        with temp_path.open("wb") as f:
            f.write(header)
            for b in bars:
                ctm = int(b.timestamp.timestamp())
                record = struct.pack(
                    "<qddddqiq",
                    ctm,
                    b.open,
                    b.low,
                    b.high,
                    b.close,
                    int(b.volume),
                    0,
                    int(b.volume),
                )
                f.write(record)

        temp_path.replace(out_path)
        bytes_written = out_path.stat().st_size
        sha256 = _compute_sha256(out_path)
        return len(bars), bytes_written, sha256, str(out_path.resolve())
    finally:
        temp_path.unlink(missing_ok=True)


def _export_to_mt4_fxt(
    bars: list[BarRecord],
    ticks: list[TickRecord],
    symbol: str,
    timeframe: str,
    out_path: Path,
) -> tuple[int, int, str, str]:
    """Export bars or ticks into MetaTrader 4 FXT tick model format."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = out_path.with_name(f"{out_path.stem}.tmp{out_path.suffix}")

    version = 405
    description = b"HaruQuantAI MT4 FXT\x00"[:64].ljust(64, b"\x00")
    server = b"HaruQuantAI Server\x00"[:128].ljust(128, b"\x00")
    sym_bytes = symbol.encode("ascii", errors="replace")[:11].ljust(12, b"\x00")
    period = _timeframe_to_minutes(timeframe)
    model = 0
    record_count = len(ticks) if ticks else len(bars)
    from_date = 0
    to_date = 0
    if ticks:
        from_date = int(ticks[0].timestamp.timestamp())
        to_date = int(ticks[-1].timestamp.timestamp())
    elif bars:
        from_date = int(bars[0].timestamp.timestamp())
        to_date = int(bars[-1].timestamp.timestamp())
    reserved = b"\x00" * 500

    header = struct.pack(
        "<i64s128s12siiiii500s",
        version,
        description,
        server,
        sym_bytes,
        period,
        model,
        record_count,
        from_date,
        to_date,
        reserved,
    )

    try:
        with temp_path.open("wb") as f:
            f.write(header)
            if ticks:
                for t in ticks:
                    ts = int(t.timestamp.timestamp())
                    record = struct.pack(
                        "<qddddqii",
                        ts,
                        t.bid,
                        t.bid,
                        t.ask,
                        t.ask,
                        int(t.bid_volume),
                        ts,
                        0,
                    )
                    f.write(record)
            else:
                for b in bars:
                    ts = int(b.timestamp.timestamp())
                    record = struct.pack(
                        "<qddddqii",
                        ts,
                        b.open,
                        b.low,
                        b.high,
                        b.close,
                        int(b.volume),
                        ts,
                        0,
                    )
                    f.write(record)

        temp_path.replace(out_path)
        bytes_written = out_path.stat().st_size
        sha256 = _compute_sha256(out_path)
        return record_count, bytes_written, sha256, str(out_path.resolve())
    finally:
        temp_path.unlink(missing_ok=True)


def _export_bars_to_mt5(
    bars: list[BarRecord],
    symbol: str,
    timeframe: str,
    out_path: Path,
) -> tuple[int, int, str, str]:
    """Export normalized bars into MetaTrader 5 binary format."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = out_path.with_name(f"{out_path.stem}.tmp{out_path.suffix}")

    magic = b"MT5B"
    version = 501
    sym_bytes = symbol.encode("ascii", errors="replace")[:15].ljust(16, b"\x00")
    period = _timeframe_to_minutes(timeframe)
    digits = 5
    count = len(bars)
    reserved = b"\x00" * 88

    header = struct.pack(
        "<4si16siiq88s",
        magic,
        version,
        sym_bytes,
        period,
        digits,
        count,
        reserved,
    )

    try:
        with temp_path.open("wb") as f:
            f.write(header)
            for b in bars:
                ts = int(b.timestamp.timestamp())
                record = struct.pack(
                    "<qddddqiq",
                    ts,
                    b.open,
                    b.high,
                    b.low,
                    b.close,
                    int(b.volume),
                    0,
                    int(b.volume),
                )
                f.write(record)

        temp_path.replace(out_path)
        bytes_written = out_path.stat().st_size
        sha256 = _compute_sha256(out_path)
        return len(bars), bytes_written, sha256, str(out_path.resolve())
    finally:
        temp_path.unlink(missing_ok=True)


@dataclass(slots=True, frozen=True)
class ImportExportConfig:
    """Configuration for import/export service."""

    default_delimiter: str = ","
    max_row_errors: int = 50


class ImportExportServiceImpl(IImportExportService):
    """Concrete implementation of ImportExportService protocol."""

    def __init__(
        self,
        dataset_service: DatasetService,
        quality_service: QualityService | None = None,
        session_service: SessionService | None = None,
        persistence: DataPersistenceService | None = None,
        config: ImportExportConfig | None = None,
    ) -> None:
        """Initialize import/export service.

        Args:
            dataset_service: Underlying dataset storage service.
            quality_service: Optional quality evaluation service.
            session_service: Optional session service.
            persistence: Optional database persistence service.
            config: Optional configuration.
        """
        self._dataset_service = dataset_service
        self._quality_service = quality_service
        self._session_service = session_service
        self._persistence = persistence
        self._config = config or ImportExportConfig()

    async def _import_ticks(
        self,
        path: Path,
        symbol: str,
        timeframe: str,
        spec: DataFormatSpecification,
    ) -> ImportResult:
        ticks, errors = await asyncio.to_thread(_parse_tabular_ticks, path, spec)
        if not ticks:
            msg = f"No valid tick records parsed from {path}"
            raise ImportParseError(msg)

        quality_score = 1.0
        tick_report: QualityReport | None = None
        if self._quality_service is not None and ticks:
            tick_report = self._quality_service.evaluate_tick_quality(ticks)
            quality_score = tick_report.quality_score

        manifest = await self._dataset_service.persist_ticks(
            symbol=symbol,
            source_id=f"file:{path.name}",
            ticks=ticks,
            lineage={
                "import_file": str(path),
                "error_count": len(errors),
                "quality_score": quality_score,
            },
            quality_score=quality_score,
        )
        if tick_report is not None and self._persistence is not None:
            bound_report = QualityReport(
                report_id=f"qr_{manifest.dataset_id}",
                dataset_id=manifest.dataset_id,
                quality_score=quality_score,
                total_records=len(ticks),
                anomalies=tick_report.anomalies,
                anomaly_counts=tick_report.anomaly_counts,
            )
            await self._persistence.save_quality_report(bound_report)

        return ImportResult(
            dataset_id=manifest.dataset_id,
            records_imported=len(ticks),
            error_count=len(errors),
            row_errors=tuple(errors[: self._config.max_row_errors]),
            timeframe=timeframe,
            data_kind="ticks",
        )

    async def _import_bars(
        self,
        path: Path,
        symbol: str,
        timeframe: str,
        spec: DataFormatSpecification,
        session: SessionDefinition | None,
    ) -> ImportResult:
        bars, errors = await asyncio.to_thread(_parse_tabular_bars, path, spec)
        if not bars:
            msg = f"No valid bar records parsed from {path}"
            raise ImportParseError(msg)

        quality_score = 1.0
        bar_report: QualityReport | None = None
        if self._quality_service is not None and bars:
            bar_report = self._quality_service.evaluate_quality(
                bars, session=session, timeframe=timeframe
            )
            quality_score = bar_report.quality_score

        manifest = await self._dataset_service.persist_bars(
            symbol=symbol,
            timeframe=timeframe,
            source_id=f"file:{path.name}",
            bars=bars,
            lineage={
                "import_file": str(path),
                "error_count": len(errors),
                "quality_score": quality_score,
            },
            quality_score=quality_score,
        )
        if bar_report is not None and self._persistence is not None:
            bound_report = QualityReport(
                report_id=f"qr_{manifest.dataset_id}",
                dataset_id=manifest.dataset_id,
                quality_score=quality_score,
                total_records=len(bars),
                anomalies=bar_report.anomalies,
                anomaly_counts=bar_report.anomaly_counts,
            )
            await self._persistence.save_quality_report(bound_report)

        return ImportResult(
            dataset_id=manifest.dataset_id,
            records_imported=len(bars),
            error_count=len(errors),
            row_errors=tuple(errors[: self._config.max_row_errors]),
            timeframe=timeframe,
            data_kind="bars",
        )

    @override
    async def import_tabular_file(
        self,
        file_path: str,
        symbol: str,
        timeframe: str,
        format_spec: DataFormatSpecification | None = None,
        session_name: str | None = None,
    ) -> ImportResult:
        """Parse, validate, and publish market data from a tabular CSV/TXT file."""
        session: SessionDefinition | None = None
        if session_name is not None:
            if self._session_service is None:
                msg = f"SessionService unavailable to resolve session '{session_name}'"
                raise SessionNotFoundError(msg)
            session = await self._session_service.get_session(session_name)
            if session is None:
                msg = f"Trading session '{session_name}' not found"
                raise SessionNotFoundError(msg)

        path = Path(file_path)
        spec = format_spec or _sniff_format_spec(path)
        if timeframe.lower() in {"tick", "t"}:
            return await self._import_ticks(path, symbol, timeframe, spec)
        return await self._import_bars(path, symbol, timeframe, spec, session)

    async def _execute_export(
        self,
        fmt: str,
        manifest: DatasetManifest,
        out_path: Path,
        delimiter: str,
        include_header: bool,
    ) -> tuple[int, int, str, str]:
        dataset_id = manifest.dataset_id
        if fmt == "csv":
            if manifest.data_kind == "ticks":
                ticks = await self._dataset_service.load_ticks(dataset_id)
                return await asyncio.to_thread(
                    _export_ticks_to_csv,
                    ticks,
                    out_path,
                    delimiter,
                    include_header,
                )
            bars = await self._dataset_service.load_bars(dataset_id)
            return await asyncio.to_thread(
                _export_bars_to_csv, bars, out_path, delimiter, include_header
            )
        if fmt in {"mt4_hst", "hst"}:
            bars = await self._dataset_service.load_bars(dataset_id)
            return await asyncio.to_thread(
                _export_bars_to_mt4_hst,
                bars,
                manifest.symbol,
                manifest.timeframe,
                out_path,
            )
        if fmt in {"mt4_fxt", "fxt"}:
            if manifest.data_kind == "ticks":
                ticks = await self._dataset_service.load_ticks(dataset_id)
                bars = []
            else:
                bars = await self._dataset_service.load_bars(dataset_id)
                ticks = []
            return await asyncio.to_thread(
                _export_to_mt4_fxt,
                bars,
                ticks,
                manifest.symbol,
                manifest.timeframe,
                out_path,
            )
        # MT5
        bars = await self._dataset_service.load_bars(dataset_id)
        return await asyncio.to_thread(
            _export_bars_to_mt5,
            bars,
            manifest.symbol,
            manifest.timeframe,
            out_path,
        )

    @override
    async def export_dataset(
        self,
        dataset_id: str,
        destination_path: str,
        format_name: str = "csv",
        delimiter: str = ",",
        include_header: bool = True,
    ) -> ExportResult:
        """Export a normalized dataset into a target format (CSV, MT4, MT5)."""
        fmt = format_name.strip().lower()
        if fmt not in {"csv", "mt4_hst", "mt4_fxt", "mt5", "hst", "fxt"}:
            msg = (
                f"Unsupported export format '{format_name}'. "
                "Supported formats: 'csv', 'mt4_hst', 'mt4_fxt', 'mt5'."
            )
            raise UnsupportedExportFormatError(msg)

        manifest = await self._dataset_service.get_manifest(dataset_id)
        if manifest is None:
            msg = f"Dataset {dataset_id} not found"
            raise DatasetNotFoundError(msg)

        out_path = Path(destination_path)
        try:
            count, bytes_written, sha256, resolved_path = await self._execute_export(
                fmt, manifest, out_path, delimiter, include_header
            )
            return ExportResult(
                destination_path=resolved_path,
                records_exported=count,
                sha256_hash=sha256,
                bytes_written=bytes_written,
            )
        except UnsupportedExportFormatError, DatasetNotFoundError:
            raise
        except Exception as exc:
            msg = f"Failed to export dataset {dataset_id} to {destination_path}: {exc}"
            raise ExportWriteError(msg) from exc


SPEC: FeatureSpec = FeatureSpec(
    name="data.imports_exports",
    provides=frozenset({DATA_IMPORTS_EXPORTS}),
    requires=frozenset({DATA_DATASETS}),
    optional=frozenset({DATA_PERSISTENCE, DATA_QUALITY, DATA_SESSIONS}),
    description="Tabular market data ingestion and multi-format egress.",
)


class ImportExportFeature:
    """Wire import/export feature into kernel composition lifecycle."""

    def __init__(self, config: ImportExportConfig | None = None) -> None:
        """Initialize feature with optional configuration.

        Args:
            config: Optional import/export configuration.
        """
        self._config = config or ImportExportConfig()

    @property
    def spec(self) -> FeatureSpec:
        """Return immutable feature specification."""
        return SPEC

    async def start(self, context: FeatureContext) -> None:
        """Resolve dependencies and provide import/export service.

        Args:
            context: Lifecycle feature context.
        """
        dataset_svc = context.require(DATA_DATASETS)
        quality_svc = context.optional(DATA_QUALITY)
        session_svc = context.optional(DATA_SESSIONS)
        persistence = context.optional(DATA_PERSISTENCE)
        service = ImportExportServiceImpl(
            dataset_service=dataset_svc,
            quality_service=quality_svc,
            session_service=session_svc,
            persistence=persistence,
            config=self._config,
        )
        context.provide(DATA_IMPORTS_EXPORTS, service)
        logger.info("data_imports_exports_feature_started")


def feature() -> ImportExportFeature:
    """Return an unmounted ImportExportFeature instance.

    Returns:
        New ImportExportFeature instance.
    """
    return ImportExportFeature()


__all__ = [
    "SPEC",
    "ImportExportConfig",
    "ImportExportFeature",
    "ImportExportServiceImpl",
    "feature",
]
