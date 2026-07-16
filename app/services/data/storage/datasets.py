"""Local dataset loading and atomic persistent storage."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import UTC, datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, cast

import pandas as pd
from pydantic import ValidationError

from app.services.data.config import get_data_settings
from app.services.data.contracts import (
    DataQualityReport,
    DatasetLoadRequest,
    DatasetSaveRequest,
    MarketDataset,
    OHLCVRecord,
    SpreadRecord,
    StorageManifest,
    TickRecord,
)
from app.services.data.contracts.errors import DataError
from app.services.data.storage.locking import acquire_write_lock
from app.utils import Clock, logger, utc_now

if TYPE_CHECKING:
    from app.services.data.contracts.market import CanonicalRecord

_APPROVED_ROOTS = "APPROVED_STORAGE_ROOTS"


def _resolve_data_dir(request_id: str) -> Path:
    """Resolve and validate the configured DATA_DIR."""
    logger.debug("Resolving configured DATA dataset directory")
    try:
        data_dir = get_data_settings().data_dir
    except ValueError:
        data_dir = None
    if data_dir is None:
        raise DataError(
            "DB_CONNECTION_ERROR",
            safe_details={"operation": "datasets", "reason": "DATA_DIR is missing"},
            request_id=request_id,
        )
    path = data_dir.expanduser().resolve()
    if not path.is_dir():
        raise DataError(
            "DB_CONNECTION_ERROR",
            safe_details={
                "operation": "datasets",
                "reason": "DATA_DIR is not a directory",
            },
            request_id=request_id,
        )
    return path


def _resolve_approved_roots(data_dir: Path, request_id: str) -> list[Path]:
    """Resolve the list of absolute approved storage roots."""
    logger.debug("Resolving approved DATA storage roots")
    try:
        roots_list = get_data_settings().approved_storage_roots
    except ValueError:
        roots_list = ()

    resolved: list[Path] = []
    for p in roots_list:
        if p.is_absolute() or ".." in p.parts:
            raise DataError(
                "PERMISSION_DENIED",
                safe_details={"field": _APPROVED_ROOTS},
                request_id=request_id,
            )
        resolved.append((data_dir / p).resolve())
    if not resolved:
        raise DataError(
            "PERMISSION_DENIED",
            safe_details={"field": _APPROVED_ROOTS},
            request_id=request_id,
        )
    return resolved


def _validate_path(
    target_path: Path, approved_roots: list[Path], request_id: str
) -> Path:
    """Validate that the target path resolved is strictly under an approved root."""
    logger.debug("Validating a DATA storage path against approved roots")
    resolved = target_path.resolve()
    for root in approved_roots:
        if resolved.is_relative_to(root):
            return resolved
    raise DataError(
        "PERMISSION_DENIED",
        safe_details={
            "path": str(target_path),
            "reason": "Path is not under any approved storage root",
        },
        request_id=request_id,
    )


def _compute_sha256(file_path: Path) -> str:
    """Compute the SHA256 checksum of a file."""
    logger.debug("Computing a DATA artifact content hash")
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()


def _check_overwrite_and_quality(
    request: DatasetSaveRequest, absolute_path: Path
) -> None:
    """Check overwrite permissions and dataset quality status."""
    logger.debug("Checking DATA overwrite and quality policy")
    if absolute_path.exists() and not request.overwrite:
        raise DataError(
            "DB_WRITE_FAILED",
            safe_details={
                "path": str(request.relative_path),
                "reason": "File exists and overwrite is disabled",
            },
            request_id=request.request_id,
        )

    if request.dataset.quality_report.quality_status == "failed":
        raise DataError(
            "DATA_QUALITY_FAILED",
            safe_details={
                "symbol": request.dataset.symbol,
                "reason": "Dataset failed quality validation",
            },
            request_id=request.request_id,
        )


def _serialize_to_dataframe(dataset: MarketDataset) -> pd.DataFrame:
    """Serialize market dataset records to a pandas DataFrame."""
    logger.debug("Serializing canonical records to a private DataFrame")
    rows = []
    for rec in dataset.records:
        row = rec.model_dump()
        for k, v in list(row.items()):
            if isinstance(v, Decimal):
                row[k] = str(v)
        rows.append(row)
    return pd.DataFrame(rows)


def _atomic_write_dataset(
    df: pd.DataFrame,
    request: DatasetSaveRequest,
    absolute_path: Path,
    manifest_path: Path,
    clock: Clock | None,
) -> StorageManifest:
    """Write DataFrame and manifest to temporary files, then atomic rename."""
    logger.info("Writing a DATA artifact and manifest atomically")
    temp_data_path = absolute_path.with_name(
        f"{absolute_path.name}.{request.request_id}.tmp"
    )
    temp_manifest_path = manifest_path.with_name(
        f"{manifest_path.name}.{request.request_id}.tmp"
    )

    try:
        if request.format == "csv":
            df.to_csv(temp_data_path, index=False)
        else:
            df.to_parquet(temp_data_path, index=False, engine="pyarrow")

        content_hash = _compute_sha256(temp_data_path)

        source_revisions = {
            record.source_revision
            for record in request.dataset.records
            if record.source_revision is not None
        }
        if len(source_revisions) != 1:
            _raise_manifest_field_error("source_revision", request.request_id)
        source_rev = next(iter(source_revisions))
        provenance = dict(request.dataset.source_metadata)
        provenance["data.symbol"] = request.dataset.symbol
        provenance["data.data_kind"] = request.dataset.data_kind
        provenance["data.available_at"] = request.dataset.available_at.isoformat()
        provenance["data.workflow_context"] = request.dataset.workflow_context
        provenance["data.precision_policy"] = request.dataset.precision_policy
        provenance["data.quality_report"] = (
            request.dataset.quality_report.model_dump_json()
        )
        if request.dataset.timeframe is not None:
            provenance["data.timeframe"] = request.dataset.timeframe

        manifest = StorageManifest(
            artifact_id=f"artifact-{content_hash}",
            relative_path=request.relative_path,
            format=request.format,
            content_hash=content_hash,
            schema_version=request.dataset.schema_id,
            normalization_version=request.dataset.normalization_version,
            source_revision=source_rev,
            row_count=len(request.dataset.records),
            start=request.dataset.start,
            end=request.dataset.end,
            license_metadata=request.dataset.license_metadata,
            provenance=provenance,
            created_at=utc_now(clock),
            request_id=request.request_id,
        )

        with temp_manifest_path.open("w", encoding="utf-8") as mf:
            mf.write(manifest.model_dump_json(indent=2))

        # Atomic rename/commits
        temp_data_path.replace(absolute_path)
        temp_manifest_path.replace(manifest_path)
        return manifest

    except Exception:
        if temp_manifest_path.exists():
            temp_manifest_path.unlink()
        if temp_data_path.exists():
            temp_data_path.unlink()
        raise


def save_dataset(
    request: DatasetSaveRequest,
    *,
    clock: Clock | None = None,
) -> StorageManifest:
    """Validate quality, lock target path, write temp files, and commit manifest.

    Args:
        request: The dataset save request.
        clock: Optional injected UTC clock.

    Returns:
        The generated storage manifest.

    Raises:
        DataError: For permission, validation, or write failures.
    """
    logger.info("Saving one canonical DATA dataset")
    data_dir = _resolve_data_dir(request.request_id)
    approved = _resolve_approved_roots(data_dir, request.request_id)
    absolute_path = (data_dir / request.relative_path).resolve()
    _validate_path(absolute_path, approved, request.request_id)

    if not absolute_path.parent.is_dir():
        raise DataError(
            "DB_WRITE_FAILED",
            safe_details={
                "path": str(request.relative_path),
                "reason": "Parent directory does not exist",
            },
            request_id=request.request_id,
        )

    _check_overwrite_and_quality(request, absolute_path)
    df = _serialize_to_dataframe(request.dataset)
    manifest_path = absolute_path.with_suffix(absolute_path.suffix + ".manifest.json")

    # Lock target to ensure exclusive lease
    with acquire_write_lock(absolute_path, request_id=request.request_id):
        try:
            return _atomic_write_dataset(
                df, request, absolute_path, manifest_path, clock
            )
        except Exception as error:
            logger.error("Dataset save failed")
            if isinstance(error, DataError):
                raise
            raise DataError(
                "DB_WRITE_FAILED",
                safe_details={"operation": "save_dataset"},
                request_id=request.request_id,
            ) from error


def _verify_manifest_integrity(
    absolute_path: Path, manifest: StorageManifest, request_id: str
) -> None:
    """Verify the content hash of the dataset matches the manifest."""
    logger.debug("Verifying DATA artifact integrity against its manifest")
    current_hash = _compute_sha256(absolute_path)
    if current_hash != manifest.content_hash:
        raise DataError(
            "FILE_CORRUPTED",
            safe_details={
                "path": str(absolute_path.name),
                "reason": "Content hash mismatch (corruption detected)",
            },
            request_id=request_id,
        )


def _raise_manifest_field_error(field: str, request_id: str) -> None:
    """Raise deterministic corruption for absent or conflicting manifest evidence."""
    logger.error("Required DATA manifest field is invalid: %s", field)
    raise DataError(
        "FILE_CORRUPTED",
        safe_details={"field": field},
        request_id=request_id,
    )


def _read_dataframe(
    absolute_path: Path, format_type: Literal["csv", "parquet"]
) -> pd.DataFrame:
    """Read DataFrame from either CSV or Parquet format."""
    logger.debug("Reading a private DATA artifact DataFrame")
    if format_type == "csv":
        return pd.read_csv(absolute_path)
    return pd.read_parquet(absolute_path, engine="pyarrow")


def _parse_row(row: pd.Series, tz: timezone) -> dict[str, Any]:
    """Parse a single pandas Series row into Pydantic-compatible dict."""
    logger.debug("Parsing one private DATA artifact row")
    row_dict: dict[str, Any] = {}
    for col, val in row.items():
        if pd.isna(val) or (
            isinstance(val, float) and (math.isnan(val) or math.isinf(val))
        ):
            row_dict[str(col)] = None
        else:
            row_dict[str(col)] = val

    ts = row_dict.get("timestamp")
    if ts is not None:
        dt = pd.to_datetime(ts).to_pydatetime()
        dt = dt.replace(tzinfo=tz) if dt.tzinfo is None else dt.astimezone(tz)
        row_dict["timestamp"] = dt
    return row_dict


def _parse_dataframe_to_records(
    df: pd.DataFrame,
    data_kind: Literal["bars", "ticks", "spreads"],
    request_id: str,
) -> list[CanonicalRecord]:
    """Parse a DataFrame into list of CanonicalRecord objects."""
    logger.info("Parsing canonical records from a DATA artifact")
    records: list[CanonicalRecord] = []
    tz = UTC
    for _, row in df.iterrows():
        row_dict = _parse_row(row, tz)
        try:
            if data_kind == "bars":
                records.append(OHLCVRecord.model_validate(row_dict))
            elif data_kind == "ticks":
                records.append(TickRecord.model_validate(row_dict))
            else:
                records.append(SpreadRecord.model_validate(row_dict))
        except ValidationError as error:
            raise DataError(
                "DATA_QUALITY_FAILED",
                safe_details={"operation": "parse_dataset_records"},
                request_id=request_id,
            ) from error
    return records


def load_dataset(request: DatasetLoadRequest) -> MarketDataset:
    """Load a dataset from an approved root and verify manifest integrity.

    Args:
        request: The dataset load request.

    Returns:
        The verified MarketDataset.

    Raises:
        DataError: If permission checks or hash verification fails.
    """
    logger.info("Loading one canonical DATA dataset")
    data_dir = _resolve_data_dir(request.request_id)
    approved = _resolve_approved_roots(data_dir, request.request_id)
    absolute_path = (data_dir / request.relative_path).resolve()
    _validate_path(absolute_path, approved, request.request_id)

    manifest_path = absolute_path.with_suffix(absolute_path.suffix + ".manifest.json")
    if not absolute_path.exists() or not manifest_path.exists():
        raise DataError(
            "FILE_CORRUPTED",
            safe_details={
                "path": str(request.relative_path),
                "reason": "Dataset file or manifest file is missing",
            },
            request_id=request.request_id,
        )

    try:
        with manifest_path.open(encoding="utf-8") as f:
            manifest_data = json.load(f)
        manifest = StorageManifest.model_validate(manifest_data)

        _verify_manifest_integrity(absolute_path, manifest, request.request_id)
        df = _read_dataframe(absolute_path, request.format)

        data_kind_value = manifest.provenance.get("data.data_kind")
        if data_kind_value not in {"bars", "ticks", "spreads"}:
            _raise_manifest_field_error("data_kind", request.request_id)
        data_kind = cast(
            "Literal['bars', 'ticks', 'spreads']",
            data_kind_value,
        )

        records = _parse_dataframe_to_records(df, data_kind, request.request_id)

        symbol = manifest.provenance.get("data.symbol")
        available_at_value = manifest.provenance.get("data.available_at")
        workflow_context = manifest.provenance.get("data.workflow_context")
        precision_policy = manifest.provenance.get("data.precision_policy")
        quality_value = manifest.provenance.get("data.quality_report")
        if None in {
            symbol,
            available_at_value,
            workflow_context,
            precision_policy,
            quality_value,
        }:
            _raise_manifest_field_error("dataset_manifest", request.request_id)
        timeframe = manifest.provenance.get("data.timeframe")
        quality_rep = DataQualityReport.model_validate_json(str(quality_value))
        available_at = datetime.fromisoformat(str(available_at_value))
        source_metadata = {
            key: value
            for key, value in manifest.provenance.items()
            if not key.startswith("data.")
        }

        return MarketDataset(
            normalization_version=manifest.normalization_version,
            data_kind=data_kind,
            symbol=str(symbol),
            timeframe=timeframe,
            records=tuple(records),
            start=manifest.start,
            end=manifest.end,
            available_at=available_at,
            record_count=len(records),
            quality_report=quality_rep,
            source_metadata=source_metadata,
            license_metadata=manifest.license_metadata,
            cache_status="miss",
            workflow_context=cast(
                "Literal['research', 'backtest', 'validation', "
                "'risk', 'execution_bound']",
                workflow_context,
            ),
            precision_policy=cast(
                "Literal['decimal_string', 'float_research_only', "
                "'source_native_decimal', 'reject_on_missing_metadata']",
                precision_policy,
            ),
            request_id=request.request_id,
        )

    except Exception as error:
        logger.error("Dataset load failed")
        if isinstance(error, DataError):
            raise
        raise DataError(
            "FILE_CORRUPTED",
            safe_details={"operation": "load_dataset"},
            request_id=request.request_id,
        ) from error
