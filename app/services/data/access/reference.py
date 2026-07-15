"""Reference data and availability orchestration."""

from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal
from typing import Final, Literal

from app.services.data.config import get_data_settings
from app.services.data.contracts import (
    AvailabilityRequest,
    DataAvailability,
    DataGap,
    DataRange,
    StorageManifest,
    SymbolListRequest,
    SymbolMetadata,
    SymbolMetadataRequest,
    SymbolPage,
)
from app.services.data.contracts.errors import DataError
from app.services.data.sources.registry import get_source_descriptor, resolve_source
from app.utils import logger

# Configuration Limits
SYMBOL_LIST_DEFAULT_LIMIT: Final = 1_000
SYMBOL_LIST_MAX_LIMIT: Final = 10_000
AVAILABILITY_SCAN_MAX_RECORDS: Final = 1_000_000


def _configured_limit(name: str, request_id: str) -> int:
    """Resolve one positive bounded configuration value at call time."""
    logger.debug("Resolving DATA reference limit %s", name)
    try:
        settings = get_data_settings()
    except ValueError:
        raise DataError(
            "INVALID_INPUT",
            safe_details={"field": name},
            request_id=request_id,
        ) from None
    if name == "SYMBOL_LIST_MAX_LIMIT":
        return settings.symbol_list_max_limit
    if name == "AVAILABILITY_SCAN_MAX_RECORDS":
        return settings.availability_scan_max_records
    raise DataError(
        "INVALID_INPUT",
        safe_details={"field": name},
        request_id=request_id,
    )


def discover_symbols(request: SymbolListRequest) -> SymbolPage:
    """Return a bounded deterministic symbol page.

    Args:
        request: Paginated symbol discovery request.

    Returns:
        The SymbolPage.

    Raises:
        DataError: If limits are exceeded, or source is unavailable.
    """
    logger.info(
        "Discovering symbols for source %s (Request: %s)",
        request.source_id,
        request.request_id,
    )

    maximum = _configured_limit("SYMBOL_LIST_MAX_LIMIT", request.request_id)
    if request.limit > maximum:
        raise DataError(
            "LIMIT_EXCEEDED",
            safe_details={
                "limit": request.limit,
                "max_limit": maximum,
            },
            request_id=request.request_id,
        )

    desc = get_source_descriptor(request.source_id)
    if desc.readiness == "disabled":
        raise DataError(
            "SOURCE_UNAVAILABLE",
            safe_details={"message": f"Source {request.source_id} is disabled"},
            request_id=request.request_id,
        )

    src = resolve_source(request.source_id)
    return src.list_symbols(request)


def fetch_symbol_metadata(request: SymbolMetadataRequest) -> SymbolMetadata:
    """Return normalized asset-aware symbol metadata.

    Args:
        request: Target symbol metadata request.

    Returns:
        The SymbolMetadata.

    Raises:
        DataError: If symbol metadata is not found or source is unavailable.
    """
    logger.info(
        "Fetching symbol metadata for %s from %s (Request: %s)",
        request.symbol,
        request.source_id,
        request.request_id,
    )

    desc = get_source_descriptor(request.source_id)
    if desc.readiness == "disabled":
        raise DataError(
            "SOURCE_UNAVAILABLE",
            safe_details={"message": f"Source {request.source_id} is disabled"},
            request_id=request.request_id,
        )

    src = resolve_source(request.source_id)
    return src.get_symbol_metadata(request)


def _load_local_manifest(
    request: AvailabilityRequest,
) -> tuple[datetime, datetime, int, str, dict[str, str]]:
    """Resolve local csv/parquet paths and load their manifest."""
    logger.debug("Running DATA function: _load_local_manifest")
    try:
        data_dir = get_data_settings().data_dir
    except ValueError:
        data_dir = None
    if data_dir is None:
        raise DataError(
            "DB_CONNECTION_ERROR",
            safe_details={"field": "DATA_DIR"},
            request_id=request.request_id,
        )
    root = data_dir.resolve()
    if not root.is_dir():
        raise DataError(
            "DB_CONNECTION_ERROR",
            safe_details={"field": "DATA_DIR"},
            request_id=request.request_id,
        )
    raw_root = (root / "data" / "raw").resolve()

    csv_path = raw_root / f"{request.symbol}.csv"
    parquet_path = raw_root / f"{request.symbol}.parquet"

    manifest_path = None
    if csv_path.exists():
        manifest_path = csv_path.with_suffix(".csv.manifest.json")
    elif parquet_path.exists():
        manifest_path = parquet_path.with_suffix(".parquet.manifest.json")

    if not manifest_path or not manifest_path.exists():
        raise DataError(
            "DATA_NOT_FOUND",
            safe_details={
                "message": (
                    f"No data file or manifest found for symbol "
                    f"{request.symbol} in raw storage"
                )
            },
            request_id=request.request_id,
        )

    try:
        with manifest_path.open("r", encoding="utf-8") as stream:
            manifest = StorageManifest.model_validate(json.load(stream))
        return (
            manifest.start,
            manifest.end,
            manifest.row_count,
            manifest.source_revision,
            dict(manifest.provenance),
        )
    except Exception as error:
        if isinstance(error, DataError):
            raise
        raise DataError(
            "FILE_CORRUPTED",
            safe_details={"operation": "availability_manifest"},
            request_id=request.request_id,
        ) from error


def _duration_microseconds(start: datetime, end: datetime) -> int:
    """Return one exact integer duration for deterministic ratios."""
    logger.debug("Computing exact availability duration")
    delta = end - start
    return delta.days * 86_400_000_000 + delta.seconds * 1_000_000 + delta.microseconds


def _compute_overlap_and_gaps(
    request: AvailabilityRequest,
    manifest_start: datetime,
    manifest_end: datetime,
) -> tuple[Decimal, tuple[DataRange, ...], tuple[DataGap, ...]]:
    """Calculate completeness, ranges, and gap details."""
    logger.debug("Running DATA function: _compute_overlap_and_gaps")
    if request.start is None or request.end is None:
        return (
            Decimal("1.0"),
            (DataRange(start=manifest_start, end=manifest_end),),
            (),
        )

    total_microseconds = _duration_microseconds(request.start, request.end)
    if total_microseconds <= 0:
        raise DataError(
            "INVALID_INPUT",
            safe_details={"message": "Invalid query range where start >= end"},
            request_id=request.request_id,
        )

    overlap_start = max(request.start, manifest_start)
    overlap_end = min(request.end, manifest_end)

    if overlap_start < overlap_end:
        overlap_microseconds = _duration_microseconds(overlap_start, overlap_end)
        completeness = Decimal(overlap_microseconds) / Decimal(total_microseconds)
        ranges = (DataRange(start=overlap_start, end=overlap_end),)
        gaps = []
        if request.start < manifest_start:
            gaps.append(DataGap(start=request.start, end=manifest_start))
        if request.end > manifest_end:
            gaps.append(DataGap(start=manifest_end, end=request.end))
        return completeness, ranges, tuple(gaps)

    return (
        Decimal("0.0"),
        (),
        (DataGap(start=request.start, end=request.end),),
    )


def inspect_availability(request: AvailabilityRequest) -> DataAvailability:
    """Compute data availability ranges, gaps, and completeness.

    Never hard-codes certainty; inspects local manifests.

    Args:
        request: Bounded availability inspect request.

    Returns:
        The DataAvailability metadata.

    Raises:
        DataError: If limit bounds are exceeded, source is unavailable,
            or data not found.
    """
    logger.info(
        "Inspecting availability for %s from %s (Request: %s)",
        request.symbol,
        request.source_id,
        request.request_id,
    )

    maximum = _configured_limit(
        "AVAILABILITY_SCAN_MAX_RECORDS",
        request.request_id,
    )
    if request.max_probe_records > maximum:
        raise DataError(
            "LIMIT_EXCEEDED",
            safe_details={
                "max_probe_records": request.max_probe_records,
                "max_allowed": maximum,
            },
            request_id=request.request_id,
        )

    desc = get_source_descriptor(request.source_id)
    if desc.readiness == "disabled":
        raise DataError(
            "SOURCE_UNAVAILABLE",
            safe_details={"message": f"Source {request.source_id} is disabled"},
            request_id=request.request_id,
        )

    m_start, m_end, row_count, rev, prov = _load_local_manifest(request)
    comp, ranges, gaps = _compute_overlap_and_gaps(request, m_start, m_end)

    kind_map: dict[str, Literal["bars", "ticks", "spreads"]] = {
        "ohlcv": "bars",
        "tick": "ticks",
        "spread": "spreads",
    }
    mapped_kind = kind_map[request.data_kind]

    return DataAvailability(
        source_id=request.source_id,
        symbol=request.symbol,
        data_kind=mapped_kind,
        timeframe=request.timeframe,
        ranges=ranges,
        gaps=gaps,
        completeness=comp,
        record_count=row_count,
        source_revision=rev,
        source_readiness=desc.readiness,
        provenance=prov,
        request_id=request.request_id,
    )
