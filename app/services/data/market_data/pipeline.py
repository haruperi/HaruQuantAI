"""Fail-closed historical market-data retrieval orchestration."""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, Literal, cast

from pydantic import ValidationError

from app.services.data.contracts import (
    DataError,
    DataQualityReport,
    MarketDataset,
)
from app.services.data.contracts.records import OHLCVRecord, SpreadRecord, TickRecord
from app.services.data.contracts.responses import (
    StandardResponse,
    data_start_time,
    run_data_operation,
    unwrap_data_response,
)
from app.services.data.economic_calendar.closures import (
    CalendarClosureEvidence,
    resolve_calendar_closures,
)
from app.services.data.market_data.requests import (
    AvailabilityRequest,
    MarketDataRequest,
    QualityFailureBehavior,
    VolumeRequest,
)
from app.services.data.persistence.cache import (
    _get_cache_entry_raw as get_cache_entry,
)
from app.services.data.persistence.cache import (
    _put_cache_entry_raw as put_cache_entry,
)
from app.services.data.persistence.contracts import (
    CacheReadRequest,
    CacheWriteRequest,
)
from app.services.data.sources.contracts import (
    RawSourceBatch,
    SourceIdentityRequest,
    SourceReadRequest,
    WorkflowContext,
)
from app.services.data.sources.policy import (
    _evaluate_source_policy_raw,
    record_source_attempt,
)
from app.services.data.sources.registry import (
    _get_source_descriptor_raw,
    _resolve_source_raw,
    resolve_source_identity,
)
from app.utils import canonical_json, generate_id, get_logger

logger = get_logger(__name__)

if TYPE_CHECKING:
    from app.services.data.contracts.dataset import PrecisionPolicy

DATA_SCHEMA_VERSION = "v1"
NORMALIZATION_VERSION = "v1"
CACHE_TTL_MAX_SECONDS = 604_800
CACHE_TTL_DAILY_SECONDS = 86_400
CACHE_TTL_INTRADAY_SECONDS = 3_600
CACHE_TTL_TICK_SECONDS = 900
TICK_MAX_LIMIT = 250_000
SPREAD_MAX_LIMIT = 250_000

type CanonicalRecord = OHLCVRecord | TickRecord | SpreadRecord


def _max_limit(data_kind: str) -> int:
    """Return the approved maximum record bound for one data kind.

    Args:
        data_kind: The ``data_kind`` argument.

    Returns:
        The result produced by the operation.

    Raises:
        DataError: If the operation cannot be completed safely.
    """
    logger.debug("Resolving maximum historical record bound")
    limits = {
        "ticks": TICK_MAX_LIMIT,
        "spreads": SPREAD_MAX_LIMIT,
    }
    try:
        return limits[data_kind]
    except KeyError as error:
        raise DataError(
            "UNSUPPORTED_OPERATION",
            safe_details={"data_kind": data_kind},
        ) from error


def _validate_record_limit(request: MarketDataRequest) -> None:
    """Validate the governed record limit for non-OHLCV requests.

    Args:
        request: Typed market-data request to validate.

    Raises:
        DataError: If a tick or spread request exceeds its published limit.
    """
    if request.data_kind == "bars":
        return
    maximum = _max_limit(request.data_kind)
    if request.limit > maximum:
        raise DataError(
            "LIMIT_EXCEEDED",
            safe_details={"limit": request.limit, "max_limit": maximum},
            request_id=request.request_id,
        )


def _default_ttl(data_kind: str, timeframe: str | None) -> int:
    """Return the documented deterministic cache TTL for one request.

    Args:
        data_kind: The ``data_kind`` argument.
        timeframe: The ``timeframe`` argument.

    Returns:
        The result produced by the operation.
    """
    logger.debug("Resolving historical cache TTL")
    if data_kind in {"ticks", "spreads"}:
        return CACHE_TTL_TICK_SECONDS
    if timeframe is not None and timeframe.upper() in {"D1", "W1", "MN1"}:
        return CACHE_TTL_DAILY_SECONDS
    return CACHE_TTL_INTRADAY_SECONDS


def _cache_key(
    request: MarketDataRequest,
    source_id: str,
    source_revision: str,
    mapping_revision: str,
) -> str:
    """Hash every semantic cache identity input in canonical form.

    Args:
        request: The ``request`` argument.
        source_id: The ``source_id`` argument.
        source_revision: The ``source_revision`` argument.
        mapping_revision: The ``mapping_revision`` argument.

    Returns:
        The result produced by the operation.
    """
    logger.debug("Generating complete historical cache identity")
    material = canonical_json(
        {
            "schema_version": DATA_SCHEMA_VERSION,
            "normalization_version": NORMALIZATION_VERSION,
            "source_id": source_id,
            "source_revision": source_revision,
            "identity_mapping_revision": mapping_revision,
            "symbol": request.symbol,
            "data_kind": request.data_kind,
            "timeframe": request.timeframe,
            "start": request.start,
            "end": request.end,
            "limit": request.limit,
            "workflow_context": request.workflow_context,
            "precision_policy": request.precision_policy,
            "fallback_sources": list(request.fallback_sources),
        }
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _records_hash(records: tuple[CanonicalRecord, ...]) -> str:
    """Hash canonical record JSON with explicit record boundaries.

    Args:
        records: The ``records`` argument.

    Returns:
        The result produced by the operation.
    """
    logger.debug("Calculating canonical historical record hash")
    digest = hashlib.sha256()
    for record in records:
        encoded = record.model_dump_json().encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    return digest.hexdigest()


def _normalize_spread_payload(data: dict[str, object]) -> SpreadRecord:
    """Normalize spread evidence without inventing unit or precision metadata.

    Args:
        data: Provider-native spread fields.

    Returns:
        A canonical spread record preserving observed values and metadata.

    Raises:
        ValidationError: If required spread, unit, or scale evidence is absent.
    """
    if "spread" not in data and "ask" in data and "bid" in data:
        data["spread"] = Decimal(str(data["ask"])) - Decimal(str(data["bid"]))
    if "unit" not in data and "price_unit" in data:
        data["unit"] = data.pop("price_unit")
    spread_fields = {
        "available_at",
        "source",
        "spread",
        "unit",
        "scale",
        "source_symbol",
        "source_revision",
        "timestamp",
    }
    return SpreadRecord.model_validate(
        {key: value for key, value in data.items() if key in spread_fields}
    )


def _normalize(
    raw_batch: RawSourceBatch, request: MarketDataRequest
) -> tuple[CanonicalRecord, ...]:
    """Normalize every raw record through the exact canonical contract.

    Args:
        raw_batch: The ``raw_batch`` argument.
        request: The ``request`` argument.

    Returns:
        The result produced by the operation.

    Raises:
        DataError: If the operation cannot be completed safely.
    """
    logger.info("Normalizing %d source records", len(raw_batch.records))
    if not raw_batch.records:
        raise DataError("EMPTY_RESULT", request_id=request.request_id)
    try:
        normalized: list[CanonicalRecord] = []
        for record in raw_batch.records:
            data = dict(record)
            if request.data_kind == "bars":
                normalized.append(OHLCVRecord.model_validate(data))
            elif request.data_kind == "ticks":
                normalized.append(TickRecord.model_validate(data))
            else:
                normalized.append(_normalize_spread_payload(data))
        records = tuple(normalized)
    except (TypeError, ValueError, ValidationError) as error:
        logger.warning("Source record normalization failed: %s", error)
        raise DataError(
            "DATA_QUALITY_FAILED",
            safe_details={"stage": "normalization"},
            request_id=request.request_id,
        ) from error
    if tuple(record.timestamp for record in records) != tuple(
        sorted(record.timestamp for record in records)
    ):
        raise DataError(
            "DATA_QUALITY_FAILED",
            safe_details={"field": "timestamp_order"},
            request_id=request.request_id,
        )
    return records


def _quality_report(
    records: tuple[CanonicalRecord, ...],
    raw_batch: RawSourceBatch,
    warnings: tuple[str, ...] = (),
    timeframe: str | None = None,
    symbol: str | None = None,
) -> DataQualityReport:
    """Build truthful evidence for the complete canonical validation pass.

    When a dataset projection is available the report is computed by
    `inspect_dataset_quality` over the actual records; a constant or unexamined
    score is never emitted.

    Args:
        records: The ``records`` argument.
        raw_batch: The ``raw_batch`` argument.
        warnings: The ``warnings`` argument.
        timeframe: The ``timeframe`` argument.
        symbol: Exact symbol used to resolve registered calendar relevance.

    Returns:
        The result produced by the operation.
    """
    logger.debug("Building historical quality evidence")
    from app.services.data.integrity.series import _inspect_records_quality_raw

    # Internal public-to-public call resolved on the private raw core so the
    # migrated ``inspect_records_quality`` response boundary is not nested.
    calendar_closures: tuple[CalendarClosureEvidence, ...] = ()
    if records and timeframe is not None and symbol is not None:
        try:
            calendar_closures = resolve_calendar_closures(
                symbol,
                records[0].timestamp,
                records[-1].timestamp + timedelta(microseconds=1),
                request_id=raw_batch.request_id,
            )
        except DataError:
            logger.warning(
                "Persisted calendar closure evidence is unavailable | symbol=%s",
                symbol,
            )
    report = _inspect_records_quality_raw(
        records,
        timeframe,
        calendar_closures=calendar_closures,
        generated_at=raw_batch.retrieved_at,
        request_id=raw_batch.request_id,
    )
    if warnings:
        return report.model_copy(update={"warnings": (*report.warnings, *warnings)})
    return report


def _cached_dataset(
    request: MarketDataRequest,
    cache_key: str,
    source_revision: str,
) -> MarketDataset | None:
    """Return a verified cache entry or a deterministic miss.

    An expired entry is returned only under an explicit `serve_stale` request, which
    the request contract already restricts to the research context, and is always
    disclosed through `cache_status="stale_warning"`.

    Args:
        request: The ``request`` argument.
        cache_key: The ``cache_key`` argument.
        source_revision: The ``source_revision`` argument.

    Returns:
        The result produced by the operation.
    """
    logger.debug("Reading verified historical cache entry")
    serve_stale = request.stale_cache_policy == "serve_stale"
    entry = get_cache_entry(
        CacheReadRequest(
            key=cache_key,
            allow_stale=serve_stale,
            request_id=request.request_id,
        )
    )
    if entry is None:
        return None
    dataset = entry.dataset
    if (
        entry.source_revision != source_revision
        or entry.schema_version != dataset.schema_id
        or entry.normalization_version != NORMALIZATION_VERSION
        or entry.raw_data_hash != _records_hash(dataset.records)
    ):
        logger.warning("Rejecting incompatible historical cache entry")
        return None
    # `get_cache_entry` already stamped "hit" or "stale_warning" on the dataset;
    # preserve it so staleness is never silently upgraded to a clean hit.
    return dataset.model_copy(update={"request_id": request.request_id})


def _dataset(
    request: MarketDataRequest,
    raw_batch: RawSourceBatch,
    source_id: str,
    provider_symbol: str,
    mapping_revision: str,
    records: tuple[CanonicalRecord, ...],
    attempted_sources: tuple[str, ...],
    warnings: tuple[str, ...],
) -> MarketDataset:
    """Assemble one canonical dataset from verified observations.

    Args:
        request: The ``request`` argument.
        raw_batch: The ``raw_batch`` argument.
        source_id: The ``source_id`` argument.
        provider_symbol: The ``provider_symbol`` argument.
        mapping_revision: The ``mapping_revision`` argument.
        records: The ``records`` argument.
        attempted_sources: The ``attempted_sources`` argument.
        warnings: The ``warnings`` argument.

    Returns:
        The result produced by the operation.
    """
    logger.debug("Assembling canonical historical dataset")
    descriptor = _get_source_descriptor_raw(source_id)
    raw_hash = _records_hash(records)
    return MarketDataset(
        normalization_version=NORMALIZATION_VERSION,
        data_kind=request.data_kind,
        symbol=request.symbol,
        timeframe=request.timeframe,
        records=records,
        start=records[0].timestamp,
        end=records[-1].timestamp,
        available_at=raw_batch.retrieved_at,
        record_count=len(records),
        quality_report=_quality_report(
            records,
            raw_batch,
            warnings,
            request.timeframe,
            request.symbol,
        ),
        source_metadata={
            "source_id": source_id,
            "provider_symbol": provider_symbol,
            "source_revision": raw_batch.revision,
            "identity_mapping_revision": mapping_revision,
            "raw_data_hash": raw_hash,
            "attempted_sources": ",".join(attempted_sources),
        },
        license_metadata={
            "status": descriptor.license_policy.status,
            "export_allowed": str(descriptor.license_policy.export_allowed),
            "attribution_required": str(descriptor.license_policy.attribution_required),
        },
        cache_status="miss" if request.use_cache else "not_used",
        workflow_context=request.workflow_context,
        precision_policy=request.precision_policy,
        request_id=request.request_id,
    )


def _require_acceptable_quality(
    dataset: MarketDataset,
    behavior: QualityFailureBehavior,
) -> MarketDataset:
    """Apply the caller-selected outcome for blocking quality evidence.

    Args:
        dataset: Canonical dataset carrying computed quality evidence.
        behavior: ``warn`` returns disclosed evidence; ``reject`` raises.

    Returns:
        The unchanged dataset when quality is non-blocking or warnings are accepted.

    Raises:
        DataError: If the computed quality decision is not accepted.
    """
    decision = dataset.quality_report.quality_decision
    if decision in {"accepted", "accepted_with_warnings"}:
        return dataset

    issue_codes = ",".join(
        sorted({issue.code for issue in dataset.quality_report.issues})
    )
    if behavior == "warn" and decision != "not_evaluated":
        logger.warning(
            "Returning historical dataset with disclosed quality decision | "
            "symbol=%s decision=%s score=%s issues=%s",
            dataset.symbol,
            decision,
            dataset.quality_report.quality_score,
            issue_codes or "none",
        )
        return dataset

    logger.warning(
        "Rejecting historical dataset with blocking quality evidence | "
        "symbol=%s decision=%s score=%s issues=%s",
        dataset.symbol,
        decision,
        dataset.quality_report.quality_score,
        issue_codes or "none",
    )
    raise DataError(
        "DATA_QUALITY_FAILED",
        safe_details={
            "symbol": dataset.symbol,
            "quality_decision": decision,
            "quality_status": dataset.quality_report.quality_status,
        },
        request_id=dataset.request_id,
    )


def _fetch_market_dataset_raw(request: MarketDataRequest) -> MarketDataset:  # noqa: C901
    """Retrieve canonical observations through an explicit governed source plan.

    Args:
        request: The ``request`` argument.

    Returns:
        The result produced by the operation.

    Raises:
        DataError: If the operation cannot be completed safely.
        last_error: If the operation cannot be completed safely.
    """
    logger.info(
        "Fetching governed historical dataset for request %s", request.request_id
    )
    _validate_record_limit(request)
    ttl = request.cache_ttl_seconds or _default_ttl(
        request.data_kind,
        request.timeframe,
    )
    if not 0 <= ttl <= CACHE_TTL_MAX_SECONDS:
        raise DataError(
            "LIMIT_EXCEEDED",
            safe_details={"field": "cache_ttl_seconds"},
            request_id=request.request_id,
        )

    plan = _evaluate_source_policy_raw(request)
    attempted: list[str] = []
    last_error: DataError | None = None
    cache_warnings: list[str] = []
    for source_id in plan.ordered_sources:
        attempted.append(source_id)
        descriptor = _get_source_descriptor_raw(source_id)
        identity = resolve_source_identity(
            SourceIdentityRequest(
                source_id=source_id,
                identity=request.symbol,
                request_id=request.request_id,
            )
        )
        cache_key = _cache_key(
            request,
            source_id,
            descriptor.revision,
            identity.mapping_revision,
        )
        if request.use_cache:
            try:
                cached = _cached_dataset(request, cache_key, descriptor.revision)
            except DataError:
                logger.warning(
                    "Historical cache read failed; preserving warning evidence"
                )
                cache_warnings.append("cache_read_failed")
            else:
                if cached is not None:
                    return _require_acceptable_quality(
                        cached,
                        request.quality_failure_behavior,
                    )
                if request.stale_cache_policy == "fail_closed":
                    logger.info(
                        "Cache-only retrieval found no live entry; failing closed"
                    )
                    raise DataError(
                        "EMPTY_RESULT",
                        safe_details={"reason": "cache_only_miss"},
                        request_id=request.request_id,
                    )

        source_request = SourceReadRequest(
            source_id=source_id,
            provider_symbol=identity.provider_symbol,
            data_kind=request.data_kind,
            timeframe=request.timeframe,
            start=request.start,
            end=request.end,
            limit=request.limit,
            request_id=request.request_id,
        )
        try:
            source = _resolve_source_raw(source_id)
            fetch_response = source.fetch(source_request)
            raw_batch = cast(
                "RawSourceBatch",
                unwrap_data_response(
                    fetch_response,
                    operation="data.market_data.fetch_market_dataset",
                    request_id=request.request_id,
                ),
            )
            records = _normalize(raw_batch, request)
            record_source_attempt(source_id, request.request_id, "SUCCESS")
        except DataError as error:
            record_source_attempt(
                source_id,
                request.request_id,
                "FAILURE",
                error.code,
            )
            last_error = error
            continue

        dataset = _dataset(
            request,
            raw_batch,
            source_id,
            identity.provider_symbol,
            identity.mapping_revision,
            records,
            tuple(attempted),
            tuple(cache_warnings),
        )
        dataset = _require_acceptable_quality(
            dataset,
            request.quality_failure_behavior,
        )
        if request.use_cache:
            try:
                put_cache_entry(
                    CacheWriteRequest(
                        key=cache_key,
                        dataset=dataset,
                        ttl_seconds=ttl,
                        source_revision=descriptor.revision,
                        raw_data_hash=_records_hash(records),
                        request_id=request.request_id,
                    )
                )
            except DataError:
                logger.warning(
                    "Historical cache write failed; returning warning evidence"
                )
                warnings = (*dataset.quality_report.warnings, "cache_write_failed")
                dataset = dataset.model_copy(
                    update={
                        "quality_report": dataset.quality_report.model_copy(
                            update={
                                "quality_status": "passed_with_warnings",
                                "warnings": warnings,
                            }
                        )
                    }
                )
        return dataset

    if last_error is not None:
        raise last_error
    raise DataError("SOURCE_UNAVAILABLE", request_id=request.request_id)


def fetch_market_dataset(
    request: MarketDataRequest,
) -> StandardResponse[MarketDataset]:
    """Retrieve canonical observations through an explicit governed source plan.

    Args:
        request: The ``request`` argument.

    Returns:
        Standard response carrying the canonical market dataset.
    """
    return run_data_operation(
        operation="data.market_data.fetch_market_dataset",
        request_id=request.request_id,
        start_time=data_start_time(),
        raw=lambda: _fetch_market_dataset_raw(request),
    )


# --- Request construction and validation helpers ---


def _request_id(value: str | None) -> str:
    """Return an explicit request ID or generate one for a direct call.

    Args:
        value: The ``value`` argument.

    Returns:
        The result produced by the operation.
    """
    return value if value is not None else generate_id("req")


def _required(value: str | None, field: str, request_id: str) -> str:
    """Return a required direct-call value.

    Args:
        value: The ``value`` argument.
        field: The ``field`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.

    Raises:
        DataError: If the required value is absent.
    """
    if value is None:
        raise DataError(
            "VALIDATION_FAILED",
            safe_details={"field": field},
            request_id=request_id,
        )
    return value


def _reject_mixed(
    request: object | None,
    values: tuple[object | None, ...],
    request_id: str,
) -> None:
    """Reject combining a typed request with direct keyword arguments.

    Args:
        request: The ``request`` argument.
        values: The ``values`` argument.
        request_id: The ``request_id`` argument.

    Raises:
        DataError: If both call styles are mixed.
    """
    if request is not None and any(value is not None for value in values):
        raise DataError(
            "VALIDATION_FAILED",
            safe_details={"message": "request objects cannot be mixed with keywords"},
            request_id=request_id,
        )


def market_request(
    request: MarketDataRequest | None,
    *,
    data_kind: Literal["bars", "ticks", "spreads"] | None,
    source_id: str | None,
    symbol: str | None,
    timeframe: str | None,
    start: datetime | None,
    end: datetime | None,
    limit: int | None,
    use_cache: bool | None,
    cache_ttl_seconds: int | None,
    quality_failure_behavior: QualityFailureBehavior | None,
    workflow_context: WorkflowContext | None,
    precision_policy: PrecisionPolicy | None,
    stale_cache_policy: Literal["refresh", "fail_closed", "serve_stale"] | None,
    fallback_sources: tuple[str, ...] | None,
    source_timezone: str | None,
    request_id: str | None,
) -> MarketDataRequest:
    """Return a typed market request from either supported call style.

    Args:
        request: The ``request`` argument.
        data_kind: The ``data_kind`` argument.
        source_id: The ``source_id`` argument.
        symbol: The ``symbol`` argument.
        timeframe: The ``timeframe`` argument.
        start: The ``start`` argument.
        end: The ``end`` argument.
        limit: The ``limit`` argument.
        use_cache: The ``use_cache`` argument.
        cache_ttl_seconds: The ``cache_ttl_seconds`` argument.
        quality_failure_behavior: The ``quality_failure_behavior`` argument.
        workflow_context: The ``workflow_context`` argument.
        precision_policy: The ``precision_policy`` argument.
        stale_cache_policy: The ``stale_cache_policy`` argument.
        fallback_sources: The ``fallback_sources`` argument.
        source_timezone: The ``source_timezone`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.

    Raises:
        DataError: If call styles are mixed or the requested kind is invalid.
    """
    trace_id = request.request_id if request is not None else _request_id(request_id)
    _reject_mixed(
        request,
        (
            source_id,
            symbol,
            timeframe,
            start,
            end,
            limit,
            use_cache,
            cache_ttl_seconds,
            quality_failure_behavior,
            workflow_context,
            precision_policy,
            stale_cache_policy,
            fallback_sources,
            source_timezone,
        ),
        trace_id,
    )
    if request is not None:
        if data_kind is not None and request.data_kind != data_kind:
            kind_sub = data_kind[:-1]
            raise DataError(
                "VALIDATION_FAILED",
                safe_details={
                    "message": (
                        f"get_{kind_sub}_data requires {kind_sub} "
                        f"data_kind, got '{request.data_kind}'"
                    )
                },
                request_id=trace_id,
            )
        return request

    # Keyword Arguments Mapping
    default_precision: PrecisionPolicy = "decimal_string"
    default_quality: QualityFailureBehavior = "reject"
    default_workflow: WorkflowContext = "research"

    resolved_source_id = _required(source_id, "source_id", trace_id)
    resolved_symbol = _required(symbol, "symbol", trace_id)

    resolved_kind: Literal["bars", "ticks", "spreads"]
    if data_kind == "bars":
        resolved_kind = "bars"
        resolved_timeframe = _required(timeframe, "timeframe", trace_id)
    elif data_kind == "ticks":
        resolved_kind = "ticks"
        resolved_timeframe = None
    elif data_kind == "spreads":
        resolved_kind = "spreads"
        resolved_timeframe = None
    else:
        # Dual-style bars fallback
        resolved_kind = "bars"
        resolved_timeframe = _required(timeframe, "timeframe", trace_id)

    return MarketDataRequest(
        source_id=resolved_source_id,
        symbol=resolved_symbol,
        data_kind=resolved_kind,
        timeframe=resolved_timeframe,
        start=start,
        end=end,
        limit=limit if limit is not None else 10,
        use_cache=use_cache if use_cache is not None else False,
        cache_ttl_seconds=cache_ttl_seconds,
        quality_failure_behavior=(
            quality_failure_behavior
            if quality_failure_behavior is not None
            else default_quality
        ),
        workflow_context=(
            workflow_context if workflow_context is not None else default_workflow
        ),
        precision_policy=(
            precision_policy if precision_policy is not None else default_precision
        ),
        stale_cache_policy=(
            stale_cache_policy if stale_cache_policy is not None else "refresh"
        ),
        fallback_sources=fallback_sources if fallback_sources is not None else (),
        source_timezone=source_timezone if source_timezone is not None else "UTC",
        request_id=trace_id,
    )


def volume_request(
    request: VolumeRequest | None,
    *,
    source_id: str | None,
    symbol: str | None,
    start: datetime | None,
    end: datetime | None,
    mode: Literal["records", "buckets", "summary"] | None,
    bucket_seconds: int | None,
    limit: int | None,
    request_id: str | None,
) -> VolumeRequest:
    """Return a typed volume request from either supported call style.

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
        The result produced by the operation.

    Raises:
        DataError: If call styles are mixed or validation fails.
    """
    trace_id = request.request_id if request is not None else _request_id(request_id)
    _reject_mixed(
        request,
        (source_id, symbol, start, end, mode, bucket_seconds, limit),
        trace_id,
    )
    if request is not None:
        return request

    resolved_source_id = _required(source_id, "source_id", trace_id)
    resolved_symbol = _required(symbol, "symbol", trace_id)

    if start is None or end is None:
        raise DataError(
            "VALIDATION_FAILED",
            safe_details={"field": "start/end"},
            request_id=trace_id,
        )
    return VolumeRequest(
        source_id=resolved_source_id,
        symbol=resolved_symbol,
        start=start,
        end=end,
        mode=mode or "summary",
        bucket_seconds=bucket_seconds,
        limit=10 if limit is None else limit,
        request_id=trace_id,
    )


def availability_request(
    request: AvailabilityRequest | None,
    *,
    source_id: str | None,
    symbol: str | None,
    data_kind: Literal["ohlcv", "tick", "spread"] | None,
    timeframe: str | None,
    start: datetime | None,
    end: datetime | None,
    max_probe_records: int | None,
    request_id: str | None,
) -> AvailabilityRequest:
    """Return a typed availability request from either supported call style.

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
        The result produced by the operation.

    Raises:
        DataError: If call styles are mixed or validation fails.
    """
    trace_id = request.request_id if request is not None else _request_id(request_id)
    _reject_mixed(
        request,
        (
            source_id,
            symbol,
            data_kind,
            timeframe,
            start,
            end,
            max_probe_records,
        ),
        trace_id,
    )
    if request is not None:
        return request

    resolved_source_id = _required(source_id, "source_id", trace_id)
    resolved_symbol = _required(symbol, "symbol", trace_id)

    return AvailabilityRequest(
        source_id=resolved_source_id,
        symbol=resolved_symbol,
        data_kind=data_kind if data_kind is not None else "ohlcv",
        timeframe=timeframe,
        start=start,
        end=end,
        max_probe_records=max_probe_records if max_probe_records is not None else 1_000,
        request_id=trace_id,
    )


# --- Public Retrieval Operations ---


def get_market_data(
    request: MarketDataRequest | None = None,
    *,
    source_id: str | None = None,
    symbol: str | None = None,
    timeframe: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int | None = None,
    use_cache: bool | None = None,
    cache_ttl_seconds: int | None = None,
    quality_failure_behavior: QualityFailureBehavior | None = None,
    workflow_context: WorkflowContext | None = None,
    precision_policy: PrecisionPolicy | None = None,
    stale_cache_policy: Literal["refresh", "fail_closed", "serve_stale"] | None = None,
    fallback_sources: tuple[str, ...] | None = None,
    source_timezone: str | None = None,
    request_id: str | None = None,
) -> StandardResponse[MarketDataset]:
    """Retrieve bars using a typed request or direct keyword arguments.

    Args:
        request: The ``request`` argument.
        source_id: The ``source_id`` argument.
        symbol: The ``symbol`` argument.
        timeframe: The ``timeframe`` argument.
        start: The ``start`` argument.
        end: The ``end`` argument.
        limit: The ``limit`` argument.
        use_cache: The ``use_cache`` argument.
        cache_ttl_seconds: The ``cache_ttl_seconds`` argument.
        quality_failure_behavior: The ``quality_failure_behavior`` argument.
        workflow_context: The ``workflow_context`` argument.
        precision_policy: The ``precision_policy`` argument.
        stale_cache_policy: The ``stale_cache_policy`` argument.
        fallback_sources: The ``fallback_sources`` argument.
        source_timezone: The ``source_timezone`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        Standard response carrying the normalized market dataset.
    """
    logger.info("Executing public DATA market retrieval")

    def _raw() -> MarketDataset:
        """Implement raw behavior.

        Returns:
            The result produced by the operation.
        """
        resolved = market_request(
            request,
            data_kind=None,
            source_id=source_id,
            symbol=symbol,
            timeframe=timeframe,
            start=start,
            end=end,
            limit=limit,
            use_cache=use_cache,
            cache_ttl_seconds=cache_ttl_seconds,
            quality_failure_behavior=quality_failure_behavior,
            workflow_context=workflow_context,
            precision_policy=precision_policy,
            stale_cache_policy=stale_cache_policy,
            fallback_sources=fallback_sources,
            source_timezone=source_timezone,
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
        return _fetch_market_dataset_raw(resolved)

    resolved_id = request.request_id if request is not None else request_id
    return run_data_operation(
        operation="data.market_data.get_market_data",
        request_id=resolved_id,
        start_time=data_start_time(),
        raw=_raw,
    )


def get_tick_data(
    request: MarketDataRequest | None = None,
    *,
    source_id: str | None = None,
    symbol: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int | None = None,
    use_cache: bool | None = None,
    cache_ttl_seconds: int | None = None,
    quality_failure_behavior: QualityFailureBehavior | None = None,
    workflow_context: WorkflowContext | None = None,
    precision_policy: PrecisionPolicy | None = None,
    stale_cache_policy: Literal["refresh", "fail_closed", "serve_stale"] | None = None,
    fallback_sources: tuple[str, ...] | None = None,
    source_timezone: str | None = None,
    request_id: str | None = None,
) -> StandardResponse[MarketDataset]:
    """Retrieve ticks using a typed request or direct keyword arguments.

    Args:
        request: The ``request`` argument.
        source_id: The ``source_id`` argument.
        symbol: The ``symbol`` argument.
        start: The ``start`` argument.
        end: The ``end`` argument.
        limit: The ``limit`` argument.
        use_cache: The ``use_cache`` argument.
        cache_ttl_seconds: The ``cache_ttl_seconds`` argument.
        quality_failure_behavior: The ``quality_failure_behavior`` argument.
        workflow_context: The ``workflow_context`` argument.
        precision_policy: The ``precision_policy`` argument.
        stale_cache_policy: The ``stale_cache_policy`` argument.
        fallback_sources: The ``fallback_sources`` argument.
        source_timezone: The ``source_timezone`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        Standard response carrying the normalized tick dataset.
    """
    logger.info("Executing public DATA tick retrieval")

    def _raw() -> MarketDataset:
        """Implement raw behavior.

        Returns:
            The result produced by the operation.
        """
        resolved = market_request(
            request,
            data_kind="ticks",
            source_id=source_id,
            symbol=symbol,
            timeframe=None,
            start=start,
            end=end,
            limit=limit,
            use_cache=use_cache,
            cache_ttl_seconds=cache_ttl_seconds,
            quality_failure_behavior=quality_failure_behavior,
            workflow_context=workflow_context,
            precision_policy=precision_policy,
            stale_cache_policy=stale_cache_policy,
            fallback_sources=fallback_sources,
            source_timezone=source_timezone,
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
        return _fetch_market_dataset_raw(resolved)

    resolved_id = request.request_id if request is not None else request_id
    return run_data_operation(
        operation="data.market_data.get_tick_data",
        request_id=resolved_id,
        start_time=data_start_time(),
        raw=_raw,
    )


def get_spread_data(
    request: MarketDataRequest | None = None,
    *,
    source_id: str | None = None,
    symbol: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int | None = None,
    use_cache: bool | None = None,
    cache_ttl_seconds: int | None = None,
    quality_failure_behavior: QualityFailureBehavior | None = None,
    workflow_context: WorkflowContext | None = None,
    precision_policy: PrecisionPolicy | None = None,
    stale_cache_policy: Literal["refresh", "fail_closed", "serve_stale"] | None = None,
    fallback_sources: tuple[str, ...] | None = None,
    source_timezone: str | None = None,
    request_id: str | None = None,
) -> StandardResponse[MarketDataset]:
    """Retrieve spreads using a typed request or direct keyword arguments.

    Args:
        request: The ``request`` argument.
        source_id: The ``source_id`` argument.
        symbol: The ``symbol`` argument.
        start: The ``start`` argument.
        end: The ``end`` argument.
        limit: The ``limit`` argument.
        use_cache: The ``use_cache`` argument.
        cache_ttl_seconds: The ``cache_ttl_seconds`` argument.
        quality_failure_behavior: The ``quality_failure_behavior`` argument.
        workflow_context: The ``workflow_context`` argument.
        precision_policy: The ``precision_policy`` argument.
        stale_cache_policy: The ``stale_cache_policy`` argument.
        fallback_sources: The ``fallback_sources`` argument.
        source_timezone: The ``source_timezone`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        Standard response carrying the normalized spread dataset.
    """
    logger.info("Executing public DATA spread retrieval")

    def _raw() -> MarketDataset:
        """Implement raw behavior.

        Returns:
            The result produced by the operation.
        """
        resolved = market_request(
            request,
            data_kind="spreads",
            source_id=source_id,
            symbol=symbol,
            timeframe=None,
            start=start,
            end=end,
            limit=limit,
            use_cache=use_cache,
            cache_ttl_seconds=cache_ttl_seconds,
            quality_failure_behavior=quality_failure_behavior,
            workflow_context=workflow_context,
            precision_policy=precision_policy,
            stale_cache_policy=stale_cache_policy,
            fallback_sources=fallback_sources,
            source_timezone=source_timezone,
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
        return _fetch_market_dataset_raw(resolved)

    resolved_id = request.request_id if request is not None else request_id
    return run_data_operation(
        operation="data.market_data.get_spread_data",
        request_id=resolved_id,
        start_time=data_start_time(),
        raw=_raw,
    )
