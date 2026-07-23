"""Explicit audited admission of externally produced market-data artifacts.

`load_dataset` deliberately requires a Data-written manifest and performs no hidden
on-read conversion. This module is the only path by which a foreign CSV or Parquet
file becomes a canonical manifest-backed dataset, and it is always an explicit
operator action recorded in the audit store.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pandas as pd
from pydantic import ValidationError

from app.services.data._settings import get_data_settings
from app.services.data.audit.store import persist_audit_event
from app.services.data.contracts import (
    DataError,
    DataQualityReport,
    MarketDataset,
    OHLCVRecord,
    SpreadRecord,
    TickRecord,
)
from app.services.data.persistence.contracts import (
    IMPORT_DIALECTS,
    DatasetSaveRequest,
    ExternalImportRequest,
)
from app.services.data.persistence.dataset_writer import save_dataset
from app.services.data.quality import inspect_records_quality
from app.utils import AuditEvent, generate_id, logger

if TYPE_CHECKING:
    from collections.abc import Mapping

    from app.services.data.contracts.dataset import CanonicalRecord
    from app.services.data.persistence.contracts import ColumnMapping, StorageManifest

IMPORT_NORMALIZATION_VERSION = "v1"
_MT5_TIME_COLUMNS = ("<DATE>", "<TIME>")


def describe_import_dialects() -> Mapping[str, str]:
    """Return the supported deterministic header and delimiter dialects.

    Returns:
        An immutable mapping of dialect identifier to its exact meaning. A dialect
        outside this set is rejected by `ExternalImportRequest`.
    """
    logger.debug("Describing supported DATA import dialects")
    return IMPORT_DIALECTS


def _resolve_source_path(request: ExternalImportRequest) -> Path:
    """Resolve the artifact path under the configured data directory.

    Raises:
        DataError: If `DATA_DIR` is unset or the artifact is absent.
    """
    data_dir = get_data_settings().data_dir
    if data_dir is None:
        raise DataError(
            "DB_CONNECTION_ERROR",
            safe_details={"field": "DATA_DIR"},
            request_id=request.request_id,
        )
    path = (data_dir.expanduser().resolve() / request.relative_path).resolve()
    if not path.is_file():
        raise DataError(
            "FILE_CORRUPTED",
            safe_details={"reason": "artifact is missing"},
            request_id=request.request_id,
        )
    return path


def _read_frame(path: Path, request: ExternalImportRequest) -> pd.DataFrame:
    """Read the artifact under its declared dialect.

    Raises:
        DataError: If the artifact cannot be decoded under the declared dialect.
    """
    logger.info("Reading external artifact under dialect %s", request.dialect)
    try:
        if request.format == "parquet":
            return pd.read_parquet(path, engine="pyarrow")
        separator = "\t" if request.dialect == "mt5_export" else ","
        return pd.read_csv(path, sep=separator)
    except (OSError, ValueError) as error:
        logger.error("External artifact could not be decoded")
        raise DataError(
            "FILE_CORRUPTED",
            safe_details={"operation": "read_external_artifact"},
            request_id=request.request_id,
        ) from error


def _require_columns(frame: pd.DataFrame, request: ExternalImportRequest) -> None:
    """Fail closed when the declared mapping does not match the artifact.

    Raises:
        DataError: If any declared source column is absent.
    """
    mapping = request.mapping
    declared = [mapping.timestamp, *mapping.bar_columns()]
    for optional in (mapping.volume, mapping.bid, mapping.ask, mapping.last):
        if optional is not None:
            declared.append(optional)
    if request.mapping.spread is not None:
        declared.append(request.mapping.spread)
    missing = [name for name in declared if name not in frame.columns]
    if missing:
        logger.error("Declared import columns are absent from the artifact")
        raise DataError(
            "VALIDATION_FAILED",
            safe_details={"field": "mapping", "missing": ",".join(sorted(missing))},
            request_id=request.request_id,
        )


def _timestamp(
    row: pd.Series,
    request: ExternalImportRequest,
    frame_columns: tuple[str, ...],
) -> datetime:
    """Return one UTC timestamp from the declared column or MT5 date/time pair.

    Raises:
        DataError: If the timestamp cannot be parsed as UTC.
    """
    if (
        request.dialect == "mt5_export"
        and request.mapping.timestamp in _MT5_TIME_COLUMNS
        and all(column in frame_columns for column in _MT5_TIME_COLUMNS)
    ):
        raw: Any = f"{row['<DATE>']} {row['<TIME>']}"
    else:
        raw = row[request.mapping.timestamp]
    try:
        parsed: datetime = pd.to_datetime(raw, utc=True).to_pydatetime()
    except (TypeError, ValueError) as error:
        raise DataError(
            "DATA_QUALITY_FAILED",
            safe_details={"field": "timestamp"},
            request_id=request.request_id,
        ) from error
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


def _decimal(value: object, field: str, request_id: str) -> Decimal:
    """Convert one source value to an exact decimal without float rounding.

    Raises:
        DataError: If the value is absent or not an exact numeric.
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        raise DataError(
            "DATA_QUALITY_FAILED",
            safe_details={"field": field},
            request_id=request_id,
        )
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as error:
        raise DataError(
            "DATA_QUALITY_FAILED",
            safe_details={"field": field},
            request_id=request_id,
        ) from error


def _optional_decimal(value: object, field: str, request_id: str) -> Decimal | None:
    """Return an exact decimal or an explicit absence."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    return _decimal(value, field, request_id)


def _bar_record(
    row: pd.Series,
    timestamp: datetime,
    request: ExternalImportRequest,
    available_at: datetime,
) -> OHLCVRecord:
    """Build one canonical bar from a mapped source row."""
    mapping: ColumnMapping = request.mapping
    request_id = request.request_id
    return OHLCVRecord(
        timestamp=timestamp,
        open=_decimal(row[mapping.open], "open", request_id),
        high=_decimal(row[mapping.high], "high", request_id),
        low=_decimal(row[mapping.low], "low", request_id),
        close=_decimal(row[mapping.close], "close", request_id),
        volume=(
            _decimal(row[mapping.volume], "volume", request_id)
            if mapping.volume is not None
            else Decimal(0)
        ),
        spread=(
            _optional_decimal(row[mapping.spread], "spread", request_id)
            if mapping.spread is not None
            else None
        ),
        price_unit=request.price_unit,
        volume_unit=request.volume_unit,
        source=request.source_id,
        source_symbol=request.symbol,
        source_revision=IMPORT_NORMALIZATION_VERSION,
        available_at=available_at,
    )


def _tick_record(
    row: pd.Series,
    timestamp: datetime,
    request: ExternalImportRequest,
    available_at: datetime,
) -> TickRecord:
    """Build one canonical tick from a mapped source row."""
    mapping: ColumnMapping = request.mapping
    request_id = request.request_id
    return TickRecord(
        timestamp=timestamp,
        bid=_decimal(row[mapping.bid], "bid", request_id),
        ask=(
            _optional_decimal(row[mapping.ask], "ask", request_id)
            if mapping.ask is not None
            else None
        ),
        last=(
            _optional_decimal(row[mapping.last], "last", request_id)
            if mapping.last is not None
            else None
        ),
        volume=(
            _optional_decimal(row[mapping.volume], "volume", request_id)
            if mapping.volume is not None
            else None
        ),
        price_unit=request.price_unit,
        volume_unit=request.volume_unit,
        source=request.source_id,
        source_symbol=request.symbol,
        source_revision=IMPORT_NORMALIZATION_VERSION,
        available_at=available_at,
    )


def _spread_record(
    row: pd.Series,
    timestamp: datetime,
    request: ExternalImportRequest,
    available_at: datetime,
) -> SpreadRecord:
    """Build one canonical spread observation from a mapped source row."""
    mapping: ColumnMapping = request.mapping
    return SpreadRecord(
        timestamp=timestamp,
        spread=_decimal(row[mapping.spread], "spread", request.request_id),
        unit=request.price_unit,
        scale=0,
        source=request.source_id,
        source_symbol=request.symbol,
        source_revision=IMPORT_NORMALIZATION_VERSION,
        available_at=available_at,
    )


def _build_records(
    frame: pd.DataFrame,
    request: ExternalImportRequest,
) -> tuple[CanonicalRecord, ...]:
    """Map and validate every source row into canonical records.

    Raises:
        DataError: If any row violates the canonical contract or ordering.
    """
    logger.info("Mapping %d external rows to canonical records", len(frame))
    columns = tuple(str(column) for column in frame.columns)
    records: list[CanonicalRecord] = []
    try:
        for _, row in frame.iterrows():
            timestamp = _timestamp(row, request, columns)
            available_at = timestamp
            if request.data_kind == "bars":
                records.append(_bar_record(row, timestamp, request, available_at))
            elif request.data_kind == "ticks":
                records.append(_tick_record(row, timestamp, request, available_at))
            else:
                records.append(_spread_record(row, timestamp, request, available_at))
    except ValidationError as error:
        logger.error("External row violates the canonical record contract")
        raise DataError(
            "DATA_QUALITY_FAILED",
            safe_details={"operation": "import_record_validation"},
            request_id=request.request_id,
        ) from error
    if not records:
        raise DataError("EMPTY_RESULT", request_id=request.request_id)
    timestamps = [record.timestamp for record in records]
    if timestamps != sorted(timestamps):
        raise DataError(
            "DATA_QUALITY_FAILED",
            safe_details={"field": "timestamp_order"},
            request_id=request.request_id,
        )
    return tuple(records)


def _quality_report(
    records: tuple[CanonicalRecord, ...],
    timeframe: str | None,
    request_id: str,
) -> DataQualityReport:
    """Inspect imported records and return measured quality evidence.

    Args:
        records: Canonical records produced from the declared external artifact.
        timeframe: Declared bar frequency, or ``None`` for non-bar data.
        request_id: Trace identifier for quality-validation failures.

    Returns:
        A deterministic quality report computed from the imported records.
    """
    logger.info("Inspecting external import quality over %d records", len(records))
    return inspect_records_quality(
        records,
        timeframe,
        generated_at=records[-1].available_at,
        request_id=request_id,
    )


def _require_acceptable_quality(
    report: DataQualityReport,
    request: ExternalImportRequest,
) -> None:
    """Reject an external artifact carrying blocking quality evidence.

    Args:
        report: Measured quality evidence for the imported records.
        request: Import declaration supplying trace and symbol context.

    Raises:
        DataError: If the report has a failed status.
    """
    if report.quality_status == "failed":
        logger.warning("Rejecting external artifact with blocking quality evidence")
        raise DataError(
            "DATA_QUALITY_FAILED",
            safe_details={
                "symbol": request.symbol,
                "quality_status": report.quality_status,
            },
            request_id=request.request_id,
        )


def _audit_import(request: ExternalImportRequest, record_count: int) -> None:
    """Record the external origin of an admitted artifact."""
    logger.info("Recording external import provenance for %s", request.symbol)
    persist_audit_event(
        AuditEvent(
            contract_version="v1",
            schema_id="utils.audit_event.v1",
            event_id=generate_id("evt"),
            timestamp=datetime.now(UTC),
            domain="data",
            action="import_external_dataset",
            request_id=request.request_id,
            correlation_id=generate_id("cor"),
            payload={
                "source_id": request.source_id,
                "symbol": request.symbol,
                "data_kind": request.data_kind,
                "dialect": request.dialect,
                "relative_path": str(request.relative_path),
                "record_count": str(record_count),
                "origin": "external",
            },
        )
    )


def import_external_dataset(request: ExternalImportRequest) -> StorageManifest:
    """Admit one externally produced artifact into canonical manifest-backed form.

    No governed field is inferred from file contents: the caller declares the symbol,
    kind, timeframe, precision, units, and column mapping, and the import fails rather
    than guessing. The committed artifact is thereafter indistinguishable from
    Data-authored output, while its external origin remains recorded in the audit
    store and in dataset provenance.

    Args:
        request: The explicit import declaration.

    Returns:
        The manifest of the committed canonical artifact.

    Raises:
        DataError: If the path, dialect, mapping, records, or commit fail validation.
    """
    logger.info("Importing external artifact %s", request.relative_path)
    source_path = _resolve_source_path(request)
    frame = _read_frame(source_path, request)
    _require_columns(frame, request)
    records = _build_records(frame, request)
    quality_report = _quality_report(
        records,
        request.timeframe,
        request.request_id,
    )
    _require_acceptable_quality(quality_report, request)

    dataset = MarketDataset(
        normalization_version=IMPORT_NORMALIZATION_VERSION,
        data_kind=request.data_kind,
        symbol=request.symbol,
        timeframe=request.timeframe,
        records=records,
        start=records[0].timestamp,
        end=records[-1].timestamp,
        available_at=records[-1].timestamp,
        record_count=len(records),
        quality_report=quality_report,
        source_metadata={
            "source_id": request.source_id,
            "origin": "external_import",
            "dialect": request.dialect,
            "imported_from": str(request.relative_path),
        },
        license_metadata={"status": "operator_declared"},
        cache_status="not_used",
        workflow_context=request.workflow_context,
        precision_policy=request.precision_policy,
        request_id=request.request_id,
    )

    manifest = save_dataset(
        DatasetSaveRequest(
            dataset=dataset,
            relative_path=request.destination_path,
            format=request.format,
            overwrite=request.overwrite,
            request_id=request.request_id,
        )
    )
    _audit_import(request, len(records))
    return manifest


__all__ = ["describe_import_dialects", "import_external_dataset"]
