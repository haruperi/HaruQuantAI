"""Reference data and availability orchestration."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, Final, Literal

from app.services.data._settings import get_data_settings
from app.services.data.contracts import (
    DataError,
    DataGap,
    DataRange,
)
from app.services.data.contracts.responses import (
    StandardResponse,
    data_start_time,
    run_data_operation,
    unwrap_data_response,
)
from app.services.data.market_data.pipeline import (
    _fetch_market_dataset_raw,
    availability_request,
    volume_request,
)
from app.services.data.market_data.requests import (
    AvailabilityRequest,
    MarketDataRequest,
    VolumeRequest,
)
from app.services.data.market_data.results import DataAvailability
from app.services.data.market_data.symbol_metadata import (
    SymbolListRequest,
    SymbolMetadata,
    SymbolMetadataRequest,
    SymbolPage,
    VolumeRecord,
    VolumeResult,
    VolumeSummary,
)
from app.services.data.persistence.contracts import (
    StorageManifest,
)
from app.services.data.sources.registry import (
    _get_source_descriptor_raw,
    _resolve_source_raw,
)
from app.utils import get_logger

logger = get_logger(__name__)

if TYPE_CHECKING:
    from app.services.data.sources.contracts import SourceDescriptor

# Configuration Limits
SYMBOL_LIST_DEFAULT_LIMIT: Final = 1_000
SYMBOL_LIST_MAX_LIMIT: Final = 10_000
AVAILABILITY_SCAN_MAX_RECORDS: Final = 1_000_000


def _configured_limit(name: str, request_id: str) -> int:
    """Resolve one positive bounded configuration value at call time.

    Args:
        name: The ``name`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.

    Raises:
        DataError: If the operation cannot be completed safely.
    """
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


def _discover_symbols_raw(request: SymbolListRequest) -> SymbolPage:
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

    desc = _get_source_descriptor_raw(request.source_id)
    if desc.readiness == "disabled":
        raise DataError(
            "SOURCE_UNAVAILABLE",
            safe_details={"message": f"Source {request.source_id} is disabled"},
            request_id=request.request_id,
        )

    src = _resolve_source_raw(request.source_id)
    list_response = src.list_symbols(request)
    return unwrap_data_response(
        list_response,
        operation="data.market_data.discover_symbols",
        request_id=request.request_id,
    )


def discover_symbols(
    request: SymbolListRequest,
) -> StandardResponse[SymbolPage]:
    """Return a bounded deterministic symbol page.

    Args:
        request: Paginated symbol discovery request.

    Returns:
        Standard response carrying the symbol page.

    Raises:
        DataError: If limits are exceeded, or source is unavailable.
    """
    return run_data_operation(
        operation="data.market_data.discover_symbols",
        request_id=request.request_id,
        start_time=data_start_time(),
        raw=lambda: _discover_symbols_raw(request),
    )


def _fetch_symbol_metadata_raw(
    request: SymbolMetadataRequest,
) -> SymbolMetadata:
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

    desc = _get_source_descriptor_raw(request.source_id)
    if desc.readiness == "disabled":
        raise DataError(
            "SOURCE_UNAVAILABLE",
            safe_details={"message": f"Source {request.source_id} is disabled"},
            request_id=request.request_id,
        )

    src = _resolve_source_raw(request.source_id)
    metadata_response = src.get_symbol_metadata(request)
    return unwrap_data_response(
        metadata_response,
        operation="data.market_data.fetch_symbol_metadata",
        request_id=request.request_id,
    )


def fetch_symbol_metadata(
    request: SymbolMetadataRequest,
) -> StandardResponse[SymbolMetadata]:
    """Return normalized asset-aware symbol metadata.

    Args:
        request: Target symbol metadata request.

    Returns:
        Standard response carrying the symbol metadata.

    Raises:
        DataError: If symbol metadata is not found or source is unavailable.
    """
    return run_data_operation(
        operation="data.market_data.fetch_symbol_metadata",
        request_id=request.request_id,
        start_time=data_start_time(),
        raw=lambda: _fetch_symbol_metadata_raw(request),
    )


def _load_local_manifest(
    request: AvailabilityRequest,
) -> tuple[datetime, datetime, int, str, dict[str, str]]:
    """Resolve local csv/parquet paths and load their manifest.

    Args:
        request: The ``request`` argument.

    Returns:
        The result produced by the operation.

    Raises:
        DataError: If the operation cannot be completed safely.
    """
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
    root = data_dir.expanduser().resolve()
    if not root.is_dir():
        raise DataError(
            "DB_CONNECTION_ERROR",
            safe_details={"field": "DATA_DIR"},
            request_id=request.request_id,
        )
    raw_root = (root / get_data_settings().data_raw_root).resolve()

    # Prefer the timeframe-scoped stem so availability agrees with retrieval about
    # which artifact backs a symbol; the bare stem covers kinds without a timeframe.
    stems = (
        [request.symbol]
        if request.timeframe is None
        else [f"{request.symbol}_{request.timeframe}", request.symbol]
    )
    manifest_path = None
    for stem in stems:
        csv_path = raw_root / f"{stem}.csv"
        parquet_path = raw_root / f"{stem}.parquet"
        if csv_path.exists():
            manifest_path = csv_path.with_suffix(".csv.manifest.json")
            break
        if parquet_path.exists():
            manifest_path = parquet_path.with_suffix(".parquet.manifest.json")
            break

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
    """Return one exact integer duration for deterministic ratios.

    Args:
        start: The ``start`` argument.
        end: The ``end`` argument.

    Returns:
        The result produced by the operation.
    """
    logger.debug("Computing exact availability duration")
    delta = end - start
    return delta.days * 86_400_000_000 + delta.seconds * 1_000_000 + delta.microseconds


def _compute_overlap_and_gaps(
    request: AvailabilityRequest,
    observed_start: datetime,
    observed_end: datetime,
) -> tuple[Decimal, tuple[DataRange, ...], tuple[DataGap, ...]]:
    """Calculate completeness, ranges, and gaps from measured boundaries.

    Args:
        request: The ``request`` argument.
        observed_start: The ``observed_start`` argument.
        observed_end: The ``observed_end`` argument.

    Returns:
        The result produced by the operation.

    Raises:
        DataError: If the operation cannot be completed safely.
    """
    logger.debug("Running DATA function: _compute_overlap_and_gaps")
    if request.start is None or request.end is None:
        return (
            Decimal("1.0"),
            (DataRange(start=observed_start, end=observed_end),),
            (),
        )

    total_microseconds = _duration_microseconds(request.start, request.end)
    if total_microseconds <= 0:
        raise DataError(
            "INVALID_INPUT",
            safe_details={"message": "Invalid query range where start >= end"},
            request_id=request.request_id,
        )

    overlap_start = max(request.start, observed_start)
    overlap_end = min(request.end, observed_end)

    if overlap_start < overlap_end:
        overlap_microseconds = _duration_microseconds(overlap_start, overlap_end)
        completeness = Decimal(overlap_microseconds) / Decimal(total_microseconds)
        ranges = (DataRange(start=overlap_start, end=overlap_end),)
        gaps = []
        if request.start < observed_start:
            gaps.append(DataGap(start=request.start, end=observed_start))
        if request.end > observed_end:
            gaps.append(DataGap(start=observed_end, end=request.end))
        return completeness, ranges, tuple(gaps)

    return (
        Decimal("0.0"),
        (),
        (DataGap(start=request.start, end=request.end),),
    )


def _probe_provider_availability(
    request: AvailabilityRequest,
    descriptor: SourceDescriptor,
    data_kind: Literal["bars", "ticks", "spreads"],
) -> DataAvailability:
    """Measure provider availability through one bounded canonical read.

    Args:
        request: Availability scope and probe bound.
        descriptor: Registered provider policy declaration.
        data_kind: Canonical retrieval kind corresponding to the request.

    Returns:
        Availability derived only from records observed by the bounded probe.

    Raises:
        DataError: If provider identity, retrieval, or evidence is unavailable.
    """
    from app.services.data.market_data import pipeline
    from app.services.data.sources import composition

    composition.ensure_storage(request.request_id)
    composition.ensure_identity(request.source_id, request.symbol, request.request_id)
    dataset = pipeline._fetch_market_dataset_raw(  # noqa: SLF001
        MarketDataRequest(
            source_id=request.source_id,
            symbol=request.symbol,
            data_kind=data_kind,
            timeframe=request.timeframe,
            start=request.start,
            end=request.end,
            limit=request.max_probe_records,
            use_cache=False,
            quality_failure_behavior="reject",
            workflow_context="research",
            precision_policy="decimal_string",
            request_id=request.request_id,
        )
    )
    completeness, ranges, gaps = _compute_overlap_and_gaps(
        request,
        dataset.start,
        dataset.end,
    )
    provenance = dict(dataset.source_metadata)
    provenance.update(
        {
            "inspection_method": "bounded_provider_probe",
            "probe_limit_reached": str(
                dataset.record_count >= request.max_probe_records
            ).lower(),
        }
    )
    return DataAvailability(
        source_id=request.source_id,
        symbol=request.symbol,
        data_kind=data_kind,
        timeframe=request.timeframe,
        ranges=ranges,
        gaps=gaps,
        completeness=completeness,
        record_count=dataset.record_count,
        source_revision=dataset.source_metadata.get(
            "source_revision", descriptor.revision
        ),
        source_readiness=descriptor.readiness,
        provenance=provenance,
        request_id=request.request_id,
    )


def _inspect_availability_raw(request: AvailabilityRequest) -> DataAvailability:
    """Compute data availability ranges, gaps, and completeness.

    Never hard-codes certainty; inspects local manifests or performs one bounded
    provider probe.

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

    desc = _get_source_descriptor_raw(request.source_id)
    if desc.readiness == "disabled":
        raise DataError(
            "SOURCE_UNAVAILABLE",
            safe_details={"message": f"Source {request.source_id} is disabled"},
            request_id=request.request_id,
        )

    kind_map: dict[str, Literal["bars", "ticks", "spreads"]] = {
        "ohlcv": "bars",
        "tick": "ticks",
        "spread": "spreads",
    }
    mapped_kind = kind_map[request.data_kind]
    if desc.requires_network:
        return _probe_provider_availability(request, desc, mapped_kind)

    m_start, m_end, row_count, rev, prov = _load_local_manifest(request)
    comp, ranges, gaps = _compute_overlap_and_gaps(request, m_start, m_end)

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


def inspect_availability(
    request: AvailabilityRequest,
) -> StandardResponse[DataAvailability]:
    """Compute data availability ranges, gaps, and completeness.

    Never hard-codes certainty; inspects local manifests or performs one bounded
    provider probe.

    Args:
        request: Bounded availability inspect request.

    Returns:
        Standard response carrying the DataAvailability metadata.

    Raises:
        DataError: If limit bounds are exceeded, source is unavailable,
            or data not found.
    """
    return run_data_operation(
        operation="data.market_data.inspect_availability",
        request_id=request.request_id,
        start_time=data_start_time(),
        raw=lambda: _inspect_availability_raw(request),
    )


# --- Request construction and validation helpers ---


def symbol_metadata_request(
    request: SymbolMetadataRequest | None,
    *,
    source_id: str | None,
    symbol: str | None,
    request_id: str | None,
) -> SymbolMetadataRequest:
    """Return a typed symbol metadata request from either supported call style.

    Args:
        request: The ``request`` argument.
        source_id: The ``source_id`` argument.
        symbol: The ``symbol`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.

    Raises:
        DataError: If call styles are mixed or validation fails.
    """
    from app.services.data.market_data.pipeline import (
        _reject_mixed,
        _request_id,
        _required,
    )

    trace_id = request.request_id if request is not None else _request_id(request_id)
    _reject_mixed(request, (source_id, symbol), trace_id)
    if request is not None:
        return request

    resolved_source_id = _required(source_id, "source_id", trace_id)
    resolved_symbol = _required(symbol, "symbol", trace_id)

    return SymbolMetadataRequest(
        source_id=resolved_source_id,
        symbol=resolved_symbol,
        request_id=trace_id,
    )


def symbol_list_request(
    request: SymbolListRequest | None,
    *,
    source_id: str | None,
    query: str | None,
    cursor: str | None,
    limit: int | None,
    request_id: str | None,
) -> SymbolListRequest:
    """Return a typed symbol listing request from either supported call style.

    Args:
        request: The ``request`` argument.
        source_id: The ``source_id`` argument.
        query: The ``query`` argument.
        cursor: The ``cursor`` argument.
        limit: The ``limit`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.

    Raises:
        DataError: If call styles are mixed or validation fails.
    """
    from app.services.data.market_data.pipeline import (
        _reject_mixed,
        _request_id,
        _required,
    )

    trace_id = request.request_id if request is not None else _request_id(request_id)
    _reject_mixed(request, (source_id, query, cursor, limit), trace_id)
    if request is not None:
        return request

    resolved_source_id = _required(source_id, "source_id", trace_id)

    return SymbolListRequest(
        source_id=resolved_source_id,
        query=query,
        cursor=cursor,
        limit=100 if limit is None else limit,
        request_id=trace_id,
    )


# --- Public reference data retrieval operations ---


def get_symbol_metadata(
    request: SymbolMetadataRequest | None = None,
    *,
    source_id: str | None = None,
    symbol: str | None = None,
    request_id: str | None = None,
) -> StandardResponse[SymbolMetadata]:
    """Retrieve symbol metadata using a request or direct keywords.

    Args:
        request: The ``request`` argument.
        source_id: The ``source_id`` argument.
        symbol: The ``symbol`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        Standard response carrying normalized provider symbol metadata.
    """
    logger.info("Executing public DATA symbol metadata retrieval")

    def _raw() -> SymbolMetadata:
        """Implement raw behavior.

        Returns:
            The result produced by the operation.
        """
        resolved = symbol_metadata_request(
            request,
            source_id=source_id,
            symbol=symbol,
            request_id=request_id,
        )
        from app.services.data.sources.composition import _ensure_source_access_raw

        _ensure_source_access_raw(resolved.source_id, resolved.request_id)
        return _fetch_symbol_metadata_raw(resolved)

    resolved_id = request.request_id if request is not None else request_id
    return run_data_operation(
        operation="data.market_data.get_symbol_metadata",
        request_id=resolved_id,
        start_time=data_start_time(),
        raw=_raw,
    )


def list_symbols(
    request: SymbolListRequest | None = None,
    *,
    source_id: str | None = None,
    query: str | None = None,
    cursor: str | None = None,
    limit: int | None = None,
    request_id: str | None = None,
) -> StandardResponse[SymbolPage]:
    """List provider symbols using a request or direct keywords.

    Args:
        request: The ``request`` argument.
        source_id: The ``source_id`` argument.
        query: The ``query`` argument.
        cursor: The ``cursor`` argument.
        limit: The ``limit`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        Standard response carrying a bounded provider symbol page.
    """
    logger.info("Executing public DATA symbol listing")

    def _raw() -> SymbolPage:
        """Implement raw behavior.

        Returns:
            The result produced by the operation.
        """
        resolved = symbol_list_request(
            request,
            source_id=source_id,
            query=query,
            cursor=cursor,
            limit=limit,
            request_id=request_id,
        )
        from app.services.data.sources.composition import _ensure_source_access_raw

        _ensure_source_access_raw(resolved.source_id, resolved.request_id)
        return _discover_symbols_raw(resolved)

    resolved_id = request.request_id if request is not None else request_id
    return run_data_operation(
        operation="data.market_data.list_symbols",
        request_id=resolved_id,
        start_time=data_start_time(),
        raw=_raw,
    )


# Volume-half dependencies, carried over from the former `gateway/sessions.py`.
# `fetch_market_dataset` is imported lazily: `retrieval/sources.py` already defers an
# import of this module, so a module-level import here would be a cycle.
VOLUME_RESPONSE_MODES = ("records", "buckets", "summary")

# Historical volume, moved here with `CAP-DATA-026` Phase 4. Volume is discovery
# evidence â€” "how much traded" alongside "what exists" â€” not a schedule concern. The
# hours/session half of the former `gateway/sessions.py` goes to `time/market_hours.py`
# in Phase 6. The split is along a clean seam: no volume function references
# `MarketCalendar`.


def _compute_volume_summary(
    request: VolumeRequest,
    records: tuple[VolumeRecord, ...],
    volume_unit: str,
    provenance: dict[str, str],
) -> VolumeResult:
    """Helper to compute VolumeSummary and construct VolumeResult.

    Args:
        request: The ``request`` argument.
        records: The ``records`` argument.
        volume_unit: The ``volume_unit`` argument.
        provenance: The ``provenance`` argument.

    Returns:
        The result produced by the operation.
    """
    logger.debug("Running DATA function: _compute_volume_summary")
    total = Decimal(str(sum(rec.volume for rec in records)))
    average = Decimal(str(total / len(records)))
    minimum = Decimal(str(min(rec.volume for rec in records)))
    maximum = Decimal(str(max(rec.volume for rec in records)))

    summary = VolumeSummary(
        total=total,
        average=average,
        minimum=minimum,
        maximum=maximum,
        record_count=len(records),
    )
    return VolumeResult(
        source_id=request.source_id,
        symbol=request.symbol,
        mode="summary",
        volume_kind="trade",
        volume_unit=volume_unit,
        records=(),
        summary=summary,
        provenance=provenance,
        truncated=False,
        request_id=request.request_id,
    )


def _compute_volume_buckets(
    request: VolumeRequest,
    records: tuple[VolumeRecord, ...],
    volume_unit: str,
    provenance: dict[str, str],
) -> VolumeResult:
    """Helper to group volume records into buckets.

    Args:
        request: The ``request`` argument.
        records: The ``records`` argument.
        volume_unit: The ``volume_unit`` argument.
        provenance: The ``provenance`` argument.

    Returns:
        The result produced by the operation.

    Raises:
        DataError: If the operation cannot be completed safely.
    """
    logger.debug("Running DATA function: _compute_volume_buckets")
    if not request.bucket_seconds:
        raise DataError(
            "INVALID_INPUT",
            safe_details={"message": "Bucket mode requires positive bucket_seconds"},
            request_id=request.request_id,
        )

    bucket_duration = timedelta(seconds=request.bucket_seconds)
    buckets_dict: dict[datetime, Decimal] = {}

    for rec in records:
        offset = (rec.timestamp - request.start).total_seconds()
        bucket_idx = int(offset // request.bucket_seconds)
        bucket_start = request.start + bucket_idx * bucket_duration
        buckets_dict[bucket_start] = (
            buckets_dict.get(bucket_start, Decimal(0)) + rec.volume
        )

    grouped_records = tuple(
        VolumeRecord(timestamp=ts, volume=vol)
        for ts, vol in sorted(buckets_dict.items())
    )
    truncated = len(grouped_records) >= request.limit

    return VolumeResult(
        source_id=request.source_id,
        symbol=request.symbol,
        mode="buckets",
        volume_kind="trade",
        volume_unit=volume_unit,
        records=grouped_records[: request.limit],
        summary=None,
        provenance=provenance,
        truncated=truncated,
        request_id=request.request_id,
    )


def _fetch_historical_volume_raw(request: VolumeRequest) -> VolumeResult:
    """Return bounded source-native or derived volume as records, buckets, or summary.

    Args:
        request: Historical volume request.

    Returns:
        The VolumeResult contract.

    Raises:
        DataError: On invalid input, limits exceeded, or quality failures.
    """
    logger.info(
        "Fetching historical volume for %s on %s (Request: %s)",
        request.symbol,
        request.source_id,
        request.request_id,
    )

    if request.mode not in VOLUME_RESPONSE_MODES:
        raise DataError(
            "INVALID_INPUT",
            safe_details={
                "message": f"Response mode {request.mode} not supported",
                "supported": ", ".join(VOLUME_RESPONSE_MODES),
            },
            request_id=request.request_id,
        )

    # Delegate fetch of the raw market bars to construct volume
    data_req = MarketDataRequest(
        source_id=request.source_id,
        symbol=request.symbol,
        data_kind="bars",
        timeframe="M1",
        start=request.start,
        end=request.end,
        limit=request.limit,
        use_cache=True,
        quality_failure_behavior="warn",
        workflow_context="research",
        precision_policy="decimal_string",
        request_id=request.request_id,
    )
    dataset = _fetch_market_dataset_raw(data_req)

    # Filter and extract OHLCVRecord elements
    from app.services.data.contracts.records import OHLCVRecord

    ohlcv_records = [r for r in dataset.records if isinstance(r, OHLCVRecord)]

    if not ohlcv_records:
        raise DataError(
            "EMPTY_RESULT",
            safe_details={
                "message": "No historical volume records found in requested range"
            },
            request_id=request.request_id,
        )

    provenance = dict(dataset.source_metadata)
    volume_unit = ohlcv_records[0].volume_unit
    records = tuple(
        VolumeRecord(timestamp=rec.timestamp, volume=rec.volume)
        for rec in ohlcv_records
    )

    if request.mode == "summary":
        return _compute_volume_summary(request, records, volume_unit, provenance)

    if request.mode == "buckets":
        return _compute_volume_buckets(request, records, volume_unit, provenance)

    truncated = len(records) >= request.limit
    return VolumeResult(
        source_id=request.source_id,
        symbol=request.symbol,
        mode="records",
        volume_kind="trade",
        volume_unit=volume_unit,
        records=records[: request.limit],
        summary=None,
        provenance=provenance,
        truncated=truncated,
        request_id=request.request_id,
    )


def fetch_historical_volume(
    request: VolumeRequest,
) -> StandardResponse[VolumeResult]:
    """Return bounded source-native or derived volume as records, buckets, or summary.

    Args:
        request: Historical volume request.

    Returns:
        Standard response carrying the VolumeResult contract.

    Raises:
        DataError: On invalid input, limits exceeded, or quality failures.
    """
    return run_data_operation(
        operation="data.market_data.fetch_historical_volume",
        request_id=request.request_id,
        start_time=data_start_time(),
        raw=lambda: _fetch_historical_volume_raw(request),
    )


# --- Request construction and validation helpers ---


def get_data_availability(
    request: AvailabilityRequest | None = None,
    *,
    source_id: str | None = None,
    symbol: str | None = None,
    data_kind: Literal["ohlcv", "tick", "spread"] | None = None,
    timeframe: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    max_probe_records: int | None = None,
    request_id: str | None = None,
) -> StandardResponse[DataAvailability]:
    """Inspect local or provider availability using a typed bounded request.

    Args:
        request: The ``request`` argument.
        source_id: The ``source_id`` argument.
        symbol: The ``symbol`` argument.
        data_kind: The ``data_kind`` argument.
        timeframe: The ``timeframe`` argument.
        start: The ``start`` argument.
        end: The ``end`` argument.
        max_probe_records: The ``max_probe_records`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        Standard response carrying stored-range and completeness evidence.
    """
    logger.info("Executing public DATA availability query")

    def _raw() -> DataAvailability:
        """Implement raw behavior.

        Returns:
            The result produced by the operation.
        """
        resolved = availability_request(
            request,
            source_id=source_id,
            symbol=symbol,
            data_kind=data_kind,
            timeframe=timeframe,
            start=start,
            end=end,
            max_probe_records=max_probe_records,
            request_id=request_id,
        )
        from app.services.data.sources.composition import (
            ensure_source as _ensure_source_raw,
        )

        _ensure_source_raw(resolved.source_id, resolved.request_id)
        return _inspect_availability_raw(resolved)

    resolved_id = request.request_id if request is not None else request_id
    return run_data_operation(
        operation="data.market_data.get_data_availability",
        request_id=resolved_id,
        start_time=data_start_time(),
        raw=_raw,
    )


def get_historical_volume(
    request: VolumeRequest | None = None,
    *,
    source_id: str | None = None,
    symbol: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    mode: Literal["records", "buckets", "summary"] | None = None,
    bucket_seconds: int | None = None,
    limit: int | None = None,
    request_id: str | None = None,
) -> StandardResponse[VolumeResult]:
    """Retrieve historical volume using a request or direct keywords.

    Args:
        request: The ``request`` argument.
        source_id: The ``source_id`` argument.
        symbol: The ``symbol`` argument.
        start: The ``start`` argument.
        end: The ``end`` argument.
        mode: The ``mode`` argument.
        bucket_seconds: The ``bucket_seconds`` argument.
        limit: The ``limit`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        Standard response carrying historical volume records, buckets, or summary.
    """
    logger.info("Executing public DATA historical-volume query")

    def _raw() -> VolumeResult:
        """Implement raw behavior.

        Returns:
            The result produced by the operation.
        """
        resolved = volume_request(
            request,
            source_id=source_id,
            symbol=symbol,
            start=start,
            end=end,
            mode=mode,
            bucket_seconds=bucket_seconds,
            limit=limit,
            request_id=request_id,
        )
        from app.services.data.sources.composition import (
            ensure_identity,
            ensure_storage,
        )

        ensure_storage(resolved.request_id)
        ensure_identity(
            resolved.source_id,
            resolved.symbol,
            resolved.request_id,
        )
        return _fetch_historical_volume_raw(resolved)

    resolved_id = request.request_id if request is not None else request_id
    return run_data_operation(
        operation="data.market_data.get_historical_volume",
        request_id=resolved_id,
        start_time=data_start_time(),
        raw=_raw,
    )


__all__ = [
    "VOLUME_RESPONSE_MODES",
    "discover_symbols",
    "fetch_historical_volume",
    "fetch_symbol_metadata",
    "get_data_availability",
    "get_historical_volume",
    "get_symbol_metadata",
    "inspect_availability",
    "list_symbols",
    "symbol_list_request",
    "symbol_metadata_request",
]
