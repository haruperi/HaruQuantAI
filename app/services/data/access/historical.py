"""Fail-closed historical market-data retrieval orchestration."""

from __future__ import annotations

import hashlib
from decimal import Decimal

from pydantic import ValidationError

from app.services.data.contracts import (
    CacheReadRequest,
    CacheWriteRequest,
    DataQualityReport,
    MarketDataRequest,
    MarketDataset,
    SourceIdentityRequest,
)
from app.services.data.contracts.errors import DataError
from app.services.data.contracts.records import OHLCVRecord, SpreadRecord, TickRecord
from app.services.data.contracts.sources import RawSourceBatch, SourceReadRequest
from app.services.data.sources.policy import (
    evaluate_source_policy,
    record_source_attempt,
)
from app.services.data.sources.registry import (
    get_source_descriptor,
    resolve_source,
    resolve_source_identity,
)
from app.services.data.storage.cache import get_cache_entry, put_cache_entry
from app.utils import canonical_json, logger

DATA_SCHEMA_VERSION = "v1"
NORMALIZATION_VERSION = "v1"
CACHE_TTL_MAX_SECONDS = 604_800
CACHE_TTL_DAILY_SECONDS = 86_400
CACHE_TTL_INTRADAY_SECONDS = 3_600
CACHE_TTL_TICK_SECONDS = 900
OHLCV_MAX_LIMIT = 50_000
TICK_MAX_LIMIT = 250_000
SPREAD_MAX_LIMIT = 250_000

type CanonicalRecord = OHLCVRecord | TickRecord | SpreadRecord


def _max_limit(data_kind: str) -> int:
    """Return the approved maximum record bound for one data kind."""
    logger.debug("Resolving maximum historical record bound")
    limits = {
        "bars": OHLCV_MAX_LIMIT,
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


def _default_ttl(data_kind: str, timeframe: str | None) -> int:
    """Return the documented deterministic cache TTL for one request."""
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
    """Hash every semantic cache identity input in canonical form."""
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
    """Hash canonical record JSON with explicit record boundaries."""
    logger.debug("Calculating canonical historical record hash")
    digest = hashlib.sha256()
    for record in records:
        encoded = record.model_dump_json().encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    return digest.hexdigest()


def _normalize(
    raw_batch: RawSourceBatch, request: MarketDataRequest
) -> tuple[CanonicalRecord, ...]:
    """Normalize every raw record through the exact canonical contract."""
    logger.info("Normalizing %d source records", len(raw_batch.records))
    if not raw_batch.records:
        raise DataError("EMPTY_RESULT", request_id=request.request_id)
    try:
        normalized: list[CanonicalRecord] = []
        for record in raw_batch.records:
            if request.data_kind == "bars":
                normalized.append(OHLCVRecord.model_validate(dict(record)))
            elif request.data_kind == "ticks":
                normalized.append(TickRecord.model_validate(dict(record)))
            else:
                normalized.append(SpreadRecord.model_validate(dict(record)))
        records = tuple(normalized)
    except (TypeError, ValueError, ValidationError) as error:
        logger.warning("Source record normalization failed")
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
) -> DataQualityReport:
    """Build truthful evidence for the complete canonical validation pass."""
    logger.debug("Building historical quality evidence")
    return DataQualityReport(
        quality_status="passed_with_warnings" if warnings else "passed",
        quality_score=Decimal(1),
        warnings=warnings,
        record_count=len(records),
        checked_count=len(records),
        sample_limit=max(1, min(1_000, len(records))),
        truncated=False,
        schema_version=DATA_SCHEMA_VERSION,
        generated_at=raw_batch.retrieved_at,
    )


def _cached_dataset(
    request: MarketDataRequest,
    cache_key: str,
    source_revision: str,
) -> MarketDataset | None:
    """Return a verified fresh cache entry or a deterministic miss."""
    logger.debug("Reading verified historical cache entry")
    entry = get_cache_entry(
        CacheReadRequest(
            key=cache_key,
            allow_stale=False,
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
    return dataset.model_copy(
        update={"cache_status": "hit", "request_id": request.request_id}
    )


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
    """Assemble one canonical dataset from verified observations."""
    logger.debug("Assembling canonical historical dataset")
    descriptor = get_source_descriptor(source_id)
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
        quality_report=_quality_report(records, raw_batch, warnings),
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


def fetch_market_dataset(request: MarketDataRequest) -> MarketDataset:  # noqa: C901
    """Retrieve canonical observations through an explicit governed source plan."""
    logger.info(
        "Fetching governed historical dataset for request %s", request.request_id
    )
    maximum = _max_limit(request.data_kind)
    if request.limit > maximum:
        raise DataError(
            "LIMIT_EXCEEDED",
            safe_details={"limit": request.limit, "max_limit": maximum},
            request_id=request.request_id,
        )
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

    plan = evaluate_source_policy(request)
    attempted: list[str] = []
    last_error: DataError | None = None
    cache_warnings: list[str] = []
    for source_id in plan.ordered_sources:
        attempted.append(source_id)
        descriptor = get_source_descriptor(source_id)
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
                    return cached

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
            raw_batch = resolve_source(source_id).fetch(source_request)
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


__all__ = ["fetch_market_dataset"]
