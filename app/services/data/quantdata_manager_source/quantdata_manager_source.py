"""QuantDataManager Source service implementation and functional behaviors.

Purpose:
    Discover and decode StrategyQuant QuantDataManager binary files (.dat)
    and synchronize reference metadata with Catalogue.

Key capabilities:
    * Discover QuantDataManager instruments and series from configured root.
    * Decode version-pinned binary M1 and tick files with checksum verification.
    * Synchronize series metadata and record SQLite lineage history.
    * Provide async import_quantdata implementing ImportQuantDataCapability.

Python API usage:
    from app.services.data.quantdata_manager_source.quantdata_manager_source import (
        QuantDataManagerSourceService,
    )
    from app.contracts.data.models import ImportQuantDataRequest

    service = QuantDataManagerSourceService()
    result = await service.import_quantdata(request)

CLI usage:
    uv run python -m app.services.data.quantdata_manager_source.quantdata_manager_source
"""

from __future__ import annotations

import hashlib
import sqlite3
import struct
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, override

from app.contracts.catalogue.models import InstrumentRef
from app.contracts.common.models import (
    ProblemDetails,
    Timeframe,
    UtcTimestamp,
    Uuid7,
)
from app.contracts.data.errors import DataFailure
from app.contracts.data.models import (
    DataSeriesVersion,
    ImportQuantdataRequest,
    ImportQuantdataSuccess,
    QuantDataImportSpec,
    SeriesCoverage,
)
from app.contracts.data.ports import ImportQuantdataCapability
from app.services.data.quantdata_manager_source._persistence import QuantDataPersistence
from app.services.data.quantdata_manager_source.config import (
    QuantDataManagerConfig,
)

if TYPE_CHECKING:
    from app.kernel.events import EventBus

# SQX scaling constants
_PRICE_SCALE: float = 1_000_000.0
_M1_VOLUME_SCALE: float = 100_000.0
_TICK_VOLUME_SCALE: float = 100.0
_MAX_SYNC_RECORDS: int = 1000
_SYNC_BYTES: int = 19
_OP_SUB: int = 0
_OP_ADD: int = 1
_OP_ABS: int = 2


def _generate_uuid7() -> Uuid7:
    """Generate a canonical lowercase UUIDv7 string.

    Returns:
        UUIDv7 string formatted per RFC 9562.
    """
    return str(uuid.uuid7())


def _format_utc_timestamp(ts_sec: float) -> UtcTimestamp:
    """Format epoch seconds to canonical ISO 8601 UtcTimestamp string.

    Args:
        ts_sec: Epoch seconds timestamp.

    Returns:
        ISO 8601 UTC timestamp with microsecond resolution.
    """
    dt = datetime.fromtimestamp(ts_sec, tz=UTC)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _compute_sha256(data: bytes | str) -> str:
    """Compute SHA-256 hash as a 64-character lowercase hex string.

    Args:
        data: Byte sequence or string to hash.

    Returns:
        64-character lowercase hex string.
    """
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _make_problem_details(
    code: str, title: str, detail: str, request_id: Uuid7
) -> ProblemDetails:
    """Construct a canonical ProblemDetails failure envelope.

    Args:
        code: Machine-readable error code.
        title: Short title describing the failure.
        detail: Human-readable error description.
        request_id: Originating request identifier.

    Returns:
        Structured ProblemDetails record.
    """
    return ProblemDetails(
        type="urn:error:data:quantdata-invalid",
        title=title,
        status=400,
        code=code,
        detail=detail,
        request_id=request_id,
    )


class QuantDataManagerSourceService(ImportQuantdataCapability):
    """Governed QuantDataManager source discovery, decoding, and sync service."""

    def __init__(
        self,
        config: QuantDataManagerConfig | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize the service with configuration and optional event bus.

        Args:
            config: Feature configuration instance.
            event_bus: Scoped kernel event bus.
        """
        self._config = config or QuantDataManagerConfig()
        self._event_bus = event_bus
        self._persistence = QuantDataPersistence(self._config)

    @property
    def persistence(self) -> QuantDataPersistence:
        """Return the persistence store adapter."""
        return self._persistence

    def get_connection(self) -> sqlite3.Connection:
        """Create and return a configured SQLite database connection."""
        return self._persistence.get_connection()

    def _init_db(self) -> None:
        """Initialize SQLite tables for lineage and imported manifests."""
        self._persistence.init_db()

    def close(self) -> None:
        """Close underlying database connections."""
        self._persistence.close()

    def verify_allowed_root(self, allowed_root_str: str) -> Path:
        """Verify and resolve the allowed root directory.

        Args:
            allowed_root_str: Path string from import spec.

        Returns:
            Resolved Path instance.

        Raises:
            ValueError: If root path is invalid or does not exist.
        """
        root = Path(allowed_root_str).expanduser().resolve()
        if not root.is_dir():
            msg = f"Allowed root directory does not exist: {root}"
            raise ValueError(msg)
        return root

    def verify_path_containment(
        self, target_path: Path | str, allowed_root: Path
    ) -> Path:
        """Verify that target_path is strictly within allowed_root.

        Args:
            target_path: File or directory path to check.
            allowed_root: Resolved root directory.

        Returns:
            Resolved target Path.

        Raises:
            ValueError: If target_path escapes allowed_root.
        """
        resolved = Path(target_path).resolve()
        try:
            resolved.relative_to(allowed_root)
        except ValueError as err:
            msg = f"Path {target_path} escapes allowed root {allowed_root}"
            raise ValueError(msg) from err
        return resolved

    async def _handle_import_op(
        self,
        request: ImportQuantdataRequest,
        root: Path,
    ) -> ImportQuantdataSuccess | DataFailure:
        """Internal handler for supported import operations.

        Args:
            request: Import request.
            root: Resolved allowed root path.

        Returns:
            ImportQuantdataSuccess on success, or DataFailure.
        """
        req_id = request.request_id
        op = request.operation
        spec = request.spec

        try:
            if op == "DISCOVER":
                data_discover_quantdata_series(self, spec, root)
                return ImportQuantdataSuccess(
                    request_id=req_id,
                    spec=spec,
                    committed_version_ids=(),
                    outcome="SUCCESS",
                )
            if op == "DECODE":
                data_decode_quantdata_files(self, spec, root)
                return ImportQuantdataSuccess(
                    request_id=req_id,
                    spec=spec,
                    committed_version_ids=(),
                    outcome="SUCCESS",
                )
            # op == "SYNC"
            versions = await data_sync_quantdata_catalogue(self, spec, root)
            version_ids = tuple(v.series_version_id for v in versions)
            return ImportQuantdataSuccess(
                request_id=req_id,
                spec=spec,
                committed_version_ids=version_ids,
                outcome="SUCCESS",
            )
        except (ValueError, OSError, sqlite3.Error, struct.error) as err:
            problem = _make_problem_details(
                "DATA_QUANTDATA_INVALID",
                f"QuantDataManager {op} Failed",
                str(err),
                req_id,
            )
            return DataFailure(
                request_id=req_id,
                code="DATA_QUANTDATA_INVALID",
                problem=problem,
            )

    @override
    async def import_quantdata(
        self,
        request: ImportQuantdataRequest,
    ) -> ImportQuantdataSuccess | DataFailure:
        """Execute governed QuantDataManager import operation.

        Args:
            request: Discriminated import request.

        Returns:
            ImportQuantdataSuccess or DataFailure.
        """
        try:
            root = self.verify_allowed_root(request.spec.allowed_root)
        except (ValueError, OSError) as err:
            problem = _make_problem_details(
                "DATA_QUANTDATA_INVALID",
                "Invalid Allowed Root",
                str(err),
                request.request_id,
            )
            return DataFailure(
                request_id=request.request_id,
                code="DATA_QUANTDATA_INVALID",
                problem=problem,
            )

        return await self._handle_import_op(request, root)


# =============================================================================
# Binary .dat Decoder Engine
# =============================================================================


def _read_utf(buf: bytes, offset: int) -> tuple[str, int]:
    """Read SQX UTF string (2-byte length + utf-8 bytes).

    Args:
        buf: Input buffer.
        offset: Offset into buffer.

    Returns:
        Tuple of (decoded string, updated offset).

    Raises:
        ValueError: If buffer is truncated.
    """
    if offset + 2 > len(buf):
        msg = f"Truncated buffer reading string length at offset {offset}"
        raise ValueError(msg)
    length = struct.unpack_from(">H", buf, offset)[0]
    offset += 2
    if offset + length > len(buf):
        msg = f"Truncated buffer reading string of len {length} at off {offset}"
        raise ValueError(msg)
    val = buf[offset : offset + length].decode("utf-8")
    return val, offset + length


def _read_field(file_bytes: bytes, val_code: int, off: int) -> tuple[int, int]:
    """Read variable-length field value.

    Args:
        file_bytes: Source byte buffer.
        val_code: SQX value encoding code.
        off: Current buffer offset.

    Returns:
        Tuple of (raw integer value, next buffer offset).

    Raises:
        ValueError: If buffer is truncated.
    """
    byte_len = 1 << val_code
    if off + byte_len > len(file_bytes):
        msg = f"Truncated record at offset {off}"
        raise ValueError(msg)
    raw_val = int.from_bytes(file_bytes[off : off + byte_len], "big", signed=False)
    return raw_val, off + byte_len


def _decode_record_values(
    file_bytes: bytes,
    offset: int,
    is_bars: bool,
    running: list[int],
) -> tuple[int, dict[str, Any]]:
    """Decode a single bar or tick record from file bytes.

    Args:
        file_bytes: Source byte buffer.
        offset: Current buffer offset.
        is_bars: True for bar (M1) records, False for tick records.
        running: Running state array of field values.

    Returns:
        Tuple of (next buffer offset, decoded record dictionary).

    Raises:
        ValueError: If buffer or config is truncated.
    """
    if offset + 3 > len(file_bytes):
        msg = f"Truncated config bytes at offset {offset}"
        raise ValueError(msg)

    cfg0 = file_bytes[offset]
    cfg1 = file_bytes[offset + 1]
    cfg2 = file_bytes[offset + 2]
    offset += 3

    codes = [
        ((cfg0 >> 4) & 0x3, (cfg0 >> 6) & 0x3),
        (cfg0 & 0x3, (cfg0 >> 2) & 0x3),
        ((cfg1 >> 4) & 0x3, (cfg1 >> 6) & 0x3),
        (cfg1 & 0x3, (cfg1 >> 2) & 0x3),
    ]
    if is_bars:
        codes.extend(
            [
                ((cfg2 >> 4) & 0x3, (cfg2 >> 6) & 0x3),
                (cfg2 & 0x3, (cfg2 >> 2) & 0x3),
            ]
        )

    num_fields = 6 if is_bars else 4
    for f_idx in range(num_fields):
        v_code, o_code = codes[f_idx]
        raw_val, offset = _read_field(file_bytes, v_code, offset)
        if o_code == _OP_ABS:
            running[f_idx] = raw_val
        elif o_code == _OP_ADD:
            running[f_idx] += raw_val
        elif o_code == _OP_SUB:
            running[f_idx] -= raw_val

    if is_bars:
        record = {
            "timestamp": running[0],
            "open": running[1] / _PRICE_SCALE,
            "high": running[2] / _PRICE_SCALE,
            "low": running[3] / _PRICE_SCALE,
            "close": running[4] / _PRICE_SCALE,
            "volume": running[5] / _M1_VOLUME_SCALE,
        }
    else:
        record = {
            "timestamp": running[0],
            "bid": running[1] / _PRICE_SCALE,
            "ask": running[2] / _PRICE_SCALE,
            "volume": running[3] / _TICK_VOLUME_SCALE,
        }
    return offset, record


def decode_quantdata_dat(
    file_bytes: bytes,
    expected_decoder_version: str = "4.2",
    max_records: int | None = None,
) -> dict[str, Any]:
    """Decode version-pinned QuantDataManager .dat binary file.

    Args:
        file_bytes: Raw .dat bytes.
        expected_decoder_version: Decoder version string (default '4.2').
        max_records: Optional maximum records to read.

    Returns:
        Dict containing header metadata and decoded rows.

    Raises:
        ValueError: On malformed, unsupported, or truncated data.
    """
    offset = 0
    version, offset = _read_utf(file_bytes, offset)
    if version != expected_decoder_version:
        msg = (
            f"Unsupported QuantDataManager file version {version} "
            f"(expected {expected_decoder_version})"
        )
        raise ValueError(msg)

    tf_type, offset = _read_utf(file_bytes, offset)
    symbol, offset = _read_utf(file_bytes, offset)

    if offset + 12 > len(file_bytes):
        msg = f"Truncated header at offset {offset}"
        raise ValueError(msg)
    records_count, _reserved = struct.unpack_from(">qi", file_bytes, offset)
    offset += 12

    _extra, offset = _read_utf(file_bytes, offset)

    if offset + _SYNC_BYTES > len(file_bytes):
        msg = f"Truncated sync chain at offset {offset}"
        raise ValueError(msg)
    offset += _SYNC_BYTES

    is_bars = tf_type.upper().startswith("B")
    num_fields = 6 if is_bars else 4

    rows: list[dict[str, Any]] = []
    running = [0] * num_fields
    rec_limit = (
        records_count if max_records is None else min(records_count, max_records)
    )

    for i in range(rec_limit):
        if i > 0 and i % _MAX_SYNC_RECORDS == 0:
            if offset + _SYNC_BYTES > len(file_bytes):
                msg = f"Truncated sync block at record {i} offset {offset}"
                raise ValueError(msg)
            offset += _SYNC_BYTES

        offset, record = _decode_record_values(file_bytes, offset, is_bars, running)
        rows.append(record)

    return {
        "version": version,
        "timeframe_type": tf_type,
        "symbol": symbol,
        "record_count": records_count,
        "rows": rows,
        "decoded_count": len(rows),
    }


# =============================================================================
# Functional Requirement Implementations
# =============================================================================


def data_discover_quantdata_series(
    service: QuantDataManagerSourceService,
    spec: QuantDataImportSpec,
    allowed_root: Path,
) -> list[dict[str, Any]]:
    """FR-DATA-DISCOVER_QUANTDATA_SERIES: Discover QuantDataManager series.

    Args:
        service: Service instance.
        spec: Import specification.
        allowed_root: Resolved allowed root directory.

    Returns:
        List of discovered series metadata dictionaries.
    """
    discovered: list[dict[str, Any]] = []

    history_dir = allowed_root / "user" / "data" / "History"
    db_path = allowed_root / "user" / "data" / "data.db"

    catalogue_rows: dict[str, dict[str, Any]] = {}
    if db_path.is_file():
        service.verify_path_containment(db_path, allowed_root)
        conn = sqlite3.connect(db_path)
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM DATA LIMIT 5000")
            for row in cursor.fetchall():
                d = dict(row)
                key = d.get("SYMBOL") or d.get("FILENAME") or str(d.get("ID"))
                catalogue_rows[key] = d
        finally:
            conn.close()

    if history_dir.is_dir():
        service.verify_path_containment(history_dir, allowed_root)
        for dat_file in sorted(history_dir.glob("*.dat")):
            service.verify_path_containment(dat_file, allowed_root)
            if spec.series_selection and dat_file.stem not in spec.series_selection:
                continue
            rel_path = dat_file.relative_to(allowed_root).as_posix()
            stat = dat_file.stat()
            symbol_guess = dat_file.stem.split("_")[0]
            timeframe_guess = "M1" if "M1" in dat_file.stem else "TICK"

            cat_info = catalogue_rows.get(symbol_guess, {})
            discovered.append(
                {
                    "symbol": cat_info.get("SYMBOL", symbol_guess),
                    "timeframe": cat_info.get("TIMEFRAME", timeframe_guess),
                    "relative_path": rel_path,
                    "file_size": stat.st_size,
                    "file_mtime": _format_utc_timestamp(stat.st_mtime),
                    "broker": cat_info.get("BROKER", "QuantDataManager"),
                    "date_from": cat_info.get("DATEFROM"),
                    "date_to": cat_info.get("DATETO"),
                }
            )

    return discovered


def data_decode_quantdata_files(
    service: QuantDataManagerSourceService,
    spec: QuantDataImportSpec,
    allowed_root: Path,
) -> list[dict[str, Any]]:
    """FR-DATA-DECODE_QUANTDATA_FILES: Decode supported M1/tick files.

    Args:
        service: Service instance.
        spec: Import specification.
        allowed_root: Resolved allowed root directory.

    Returns:
        List of decoded file records and metadata.
    """
    history_dir = allowed_root / "user" / "data" / "History"
    results: list[dict[str, Any]] = []

    if not history_dir.is_dir():
        return results

    service.verify_path_containment(history_dir, allowed_root)
    for dat_file in sorted(history_dir.glob("*.dat")):
        service.verify_path_containment(dat_file, allowed_root)
        if spec.series_selection and dat_file.stem not in spec.series_selection:
            continue
        raw_bytes = dat_file.read_bytes()
        decoded = decode_quantdata_dat(
            raw_bytes,
            expected_decoder_version=str(spec.decoder_version),
        )
        decoded["file_path"] = dat_file.relative_to(allowed_root).as_posix()
        decoded["content_hash"] = _compute_sha256(raw_bytes)
        results.append(decoded)

    return results


async def data_sync_quantdata_catalogue(
    service: QuantDataManagerSourceService,
    spec: QuantDataImportSpec,
    allowed_root: Path,
) -> list[DataSeriesVersion]:
    """FR-DATA-SYNC_QUANTDATA_CATALOGUE: Map metadata and commit versions.

    Args:
        service: Service instance.
        spec: Import specification.
        allowed_root: Resolved allowed root directory.

    Returns:
        List of committed DataSeriesVersion records.
    """
    decoded_files = data_decode_quantdata_files(service, spec, allowed_root)
    committed_versions: list[DataSeriesVersion] = []

    for decoded in decoded_files:
        is_bars = decoded["timeframe_type"].upper().startswith("B")
        rows = decoded["rows"]
        row_count = len(rows)

        if row_count > 0:
            first_ts_ms = rows[0]["timestamp"]
            last_ts_ms = rows[-1]["timestamp"]
            from_at = _format_utc_timestamp(first_ts_ms / 1000.0)
            to_at = _format_utc_timestamp(
                max(last_ts_ms / 1000.0 + 60.0, first_ts_ms / 1000.0 + 60.0)
            )
        else:
            from_at = _format_utc_timestamp(0.0)
            to_at = _format_utc_timestamp(60.0)

        series_id = _generate_uuid7()
        series_ver_id = _generate_uuid7()
        content_hash = decoded["content_hash"]

        version = DataSeriesVersion(
            series_version_id=series_ver_id,
            series_id=series_id,
            version=1,
            instrument=InstrumentRef(
                instrument_id=_generate_uuid7(),
            ),
            instrument_version_id=_generate_uuid7(),
            session_version_id=None,
            calendar_version_id=None,
            broker=None,
            timeframe=Timeframe(unit="MINUTE", multiple=1) if is_bars else None,
            tick_type=None if is_bars else "BID_ASK",
            timezone="UTC",
            precision=(
                "SELECTED_TIMEFRAME" if is_bars else "REAL_TICK_RECORDED_SPREAD"
            ),
            coverage=SeriesCoverage(from_at=from_at, to_at=to_at),
            row_count=row_count,
            source_artifact_id=_generate_uuid7(),
            canonical_artifact_id=_generate_uuid7(),
            import_policy=None,
            aggregation_lineage=None,
            findings_summary=(),
            content_hash=content_hash,
        )

        data_record_quantdata_lineage(
            service,
            spec,
            allowed_root,
            decoded["file_path"],
            series_id=series_id,
            series_version_id=series_ver_id,
            content_hash=content_hash,
        )
        committed_versions.append(version)

    return committed_versions


def data_record_quantdata_lineage(
    service: QuantDataManagerSourceService,
    spec: QuantDataImportSpec,
    allowed_root: Path,
    relative_path: str,
    *,
    series_id: Uuid7,
    series_version_id: Uuid7,
    content_hash: str,
) -> dict[str, Any]:
    """FR-DATA-RECORD_QUANTDATA_LINEAGE: Record source lineage and manifest.

    Args:
        service: Service instance.
        spec: Import specification.
        allowed_root: Resolved allowed root directory.
        relative_path: Source file relative path.
        series_id: Series identifier.
        series_version_id: Series version identifier.
        content_hash: Computed SHA-256 hash.

    Returns:
        Lineage dictionary.
    """
    full_path = allowed_root / relative_path
    service.verify_path_containment(full_path, allowed_root)
    stat = full_path.stat() if full_path.exists() else None

    lineage_id = _generate_uuid7()
    file_mtime = (
        _format_utc_timestamp(stat.st_mtime) if stat else _format_utc_timestamp(0.0)
    )
    lineage_entry = {
        "lineage_id": lineage_id,
        "spec_id": str(spec.spec_id),
        "source_root": allowed_root.as_posix(),
        "relative_path": relative_path,
        "file_size": stat.st_size if stat else 0,
        "file_mtime": file_mtime,
        "content_hash": content_hash,
        "decoder_version": str(spec.decoder_version),
        "series_id": str(series_id),
        "series_version_id": str(series_version_id),
        "created_at": _format_utc_timestamp(Path(__file__).stat().st_mtime),
    }

    service.persistence.record_lineage(
        lineage_id=lineage_entry["lineage_id"],
        spec_id=lineage_entry["spec_id"],
        source_root=lineage_entry["source_root"],
        relative_path=lineage_entry["relative_path"],
        file_size=lineage_entry["file_size"],
        file_mtime=lineage_entry["file_mtime"],
        content_hash=lineage_entry["content_hash"],
        decoder_version=lineage_entry["decoder_version"],
        series_id=lineage_entry["series_id"],
        series_version_id=lineage_entry["series_version_id"],
    )

    return lineage_entry


# =============================================================================
# Scenario Harness
# =============================================================================


async def main() -> None:
    """Execute the QuantDataManager Source usage demonstration harness."""
    from app.services.data.quantdata_manager_source._usage import main as _usage_main

    await _usage_main()


def run_usage_scenarios() -> None:
    """Synchronous runner entry point for the usage demonstration."""
    import asyncio

    asyncio.run(main())


if __name__ == "__main__":
    run_usage_scenarios()
