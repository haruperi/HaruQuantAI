"""Application-triggered catalog transaction operations."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, cast

from app.services.data.contracts import DataError
from app.services.data.persistence import (
    create_catalog_artifact_records,
    create_catalog_reference_records,
    create_fetch_log_record,
    create_quality_event_record,
    read_catalog_coverage,
    read_catalog_event_records,
    read_catalog_files_for_range,
    read_catalog_reference_records,
    read_catalog_unverified_count,
    read_verified_research_source_record,
)
from app.services.data.persistence.contracts import StorageManifest
from app.services.data.persistence.dataset_writer import resolve_data_root
from app.utils import get_logger, utc_now

logger = get_logger(__name__)

if TYPE_CHECKING:
    from app.services.data.contracts.dataset import MarketDataset

_MAX_TEXT_LENGTH = 256
_MAX_CATALOG_ROWS = 1000

_CATALOG_TABLE_LIFECYCLES: Mapping[str, tuple[str, ...]] = {
    "data_audit_events": ("persist_audit_event", "query_audit_events"),
    "data_backfill_checkpoints": ("run_data_update_job_once", "recover_update_jobs"),
    "data_cache": ("get_cache_entry", "put_cache_entry", "clear_data_cache"),
    "data_datasets": ("register_catalog_artifact", "get_catalog_evidence"),
    "data_economic_events": ("scrape_economic_calendar", "get_economic_events"),
    "data_economic_event_definitions": (
        "crawl_forexfactory_event_definitions",
        "get_economic_events",
    ),
    "data_economic_calendar_coverage": (
        "get_economic_events",
        "import_economic_calendar_csv",
        "sync_current_week_economic_calendar",
    ),
    "data_feeds": ("start_internal_feed", "get_feed_status"),
    "data_fetch_log": ("record_catalog_fetch", "get_catalog_evidence"),
    "data_market_sessions": ("sync_catalog_reference", "get_catalog_evidence"),
    "data_migration_ledger": ("run_data_migrations",),
    "data_partition_files": ("register_catalog_artifact", "get_catalog_evidence"),
    "data_providers": ("sync_catalog_reference", "get_catalog_evidence"),
    "data_quality_events": ("record_catalog_quality_event", "get_catalog_evidence"),
    "data_research_observations": (
        "persist_research_source_observations",
        "query_research_source_observations",
    ),
    "data_research_sources": ("ingest_research_source", "query_research_sources"),
    "data_runtime_records": ("execute_runtime_store_operation",),
    "data_source_attempts": ("evaluate_source_policy",),
    "data_source_state": ("promote_source", "get_source_descriptor"),
    "data_symbols": ("sync_catalog_reference", "get_catalog_evidence"),
    "data_update_jobs": ("create_data_update_job", "run_data_update_job_once"),
    "data_verified_research_sources": (
        "persist_verified_research_source",
        "get_verified_research_source",
    ),
    "data_write_locks": ("acquire_write_lock",),
}


def _text(value: str, field: str) -> str:
    """Validate one bounded catalog identity value."""
    if not value or value != value.strip() or len(value) > _MAX_TEXT_LENGTH:
        raise DataError("INVALID_INPUT", safe_details={"field": field})
    return value


def _identity(prefix: str, *parts: str) -> str:
    """Build a stable opaque catalog identity."""
    digest = hashlib.sha256("\x1f".join(parts).encode()).hexdigest()
    return f"{prefix}-{digest}"


def _timestamp(value: datetime) -> str:
    """Serialize one aware UTC timestamp."""
    if value.tzinfo is None or value.utcoffset() is None:
        raise DataError("INVALID_INPUT", safe_details={"field": "timestamp"})
    return value.astimezone(UTC).isoformat()


def sync_catalog_reference(
    *,
    provider_code: str,
    provider_kind: str,
    canonical_symbol: str,
    asset_class: str,
    base_currency: str,
    quote_currency: str,
    digits: int,
    tick_size: Decimal,
    min_volume: Decimal,
    max_volume: Decimal,
    volume_step: Decimal,
    sessions: Sequence[Mapping[str, object]] = (),
    request_id: str,
    correlation_id: str = "",
    observed_at: datetime | None = None,
) -> object:
    """Synchronize source-authoritative provider, symbol, and session evidence."""
    logger.info("Synchronizing Data catalog reference evidence")
    provider_code = _text(provider_code, "provider_code")
    canonical_symbol = _text(canonical_symbol, "canonical_symbol")
    now = _timestamp(observed_at or utc_now())
    provider_id = _identity("provider", provider_code)
    symbol_id = _identity("symbol", canonical_symbol)
    provider_parameters = (
        provider_id,
        provider_code,
        _text(provider_kind, "provider_kind"),
        100,
        "observed",
        0,
        1,
        "{}",
        1,
        request_id,
        correlation_id,
        now,
        now,
    )
    symbol_parameters = (
        symbol_id,
        canonical_symbol,
        _text(asset_class, "asset_class"),
        _text(base_currency, "base_currency"),
        _text(quote_currency, "quote_currency"),
        digits,
        str(tick_size),
        str(min_volume),
        str(max_volume),
        str(volume_step),
        "1",
        "{}",
        "active",
        request_id,
        correlation_id,
        now,
        now,
    )
    session_parameters = tuple(
        (
            _identity(
                "session",
                symbol_id,
                str(item["session_name"]),
                str(item["day_of_week"]),
                str(item["effective_from"]),
            ),
            symbol_id,
            _text(str(item["session_name"]), "session_name"),
            int(str(item["day_of_week"])),
            _text(str(item["open_time_utc"]), "open_time_utc"),
            _text(str(item["close_time_utc"]), "close_time_utc"),
            int(bool(item.get("is_trading", True))),
            _text(str(item["effective_from"]), "effective_from"),
            None if item.get("effective_to") is None else str(item["effective_to"]),
            request_id,
            correlation_id,
            now,
            now,
        )
        for item in sessions
    )
    return create_catalog_reference_records(
        provider_parameters,
        symbol_parameters,
        session_parameters,
        request_id=request_id,
    )


def register_catalog_artifact(
    dataset: MarketDataset,
    manifest: StorageManifest,
    *,
    byte_size: int,
    request_id: str,
    correlation_id: str = "",
) -> object:
    """Register one committed dataset artifact and sidecar atomically."""
    logger.info("Registering one committed Data artifact")
    symbol_id = _identity("symbol", str(dataset.symbol))
    provider_code = str(dataset.source_metadata.get("actual_source", "unknown"))
    provider_id = _identity("provider", provider_code)
    dataset_id = _identity(
        "dataset",
        str(dataset.data_kind),
        str(dataset.symbol),
        str(dataset.timeframe or ""),
        provider_code,
    )
    now = _timestamp(manifest.created_at)
    dataset_parameters = (
        dataset_id,
        str(dataset.data_kind),
        "data",
        symbol_id,
        dataset.timeframe,
        provider_id,
        str(manifest.artifact_id),
        str(manifest.relative_path),
        str(manifest.schema_version),
        str(manifest.normalization_version),
        "bar_open",
        1,
        int(manifest.row_count),
        byte_size,
        int(manifest.start.timestamp()),
        int(manifest.end.timestamp()),
        "ready",
        request_id,
        correlation_id,
        now,
        now,
    )
    file_parameters = (
        _identity("file", str(manifest.artifact_id)),
        dataset_id,
        str(manifest.artifact_id),
        str(manifest.relative_path),
        str(manifest.format),
        str(manifest.content_hash),
        int(manifest.row_count),
        byte_size,
        int(manifest.start.timestamp()),
        int(manifest.end.timestamp()),
        str(manifest.schema_version),
        str(manifest.normalization_version),
        str(manifest.source_revision),
        json.dumps(dict(manifest.provenance), sort_keys=True),
        json.dumps(dict(manifest.license_metadata), sort_keys=True),
        "verified",
        now,
        request_id,
        correlation_id,
        now,
        now,
    )
    return create_catalog_artifact_records(
        dataset_parameters, file_parameters, request_id=request_id
    )


def record_catalog_fetch(*, values: Sequence[object], request_id: str) -> object:
    """Append one already-classified bounded fetch outcome."""
    logger.info("Recording Data catalog fetch evidence")
    return create_fetch_log_record(tuple(values), request_id=request_id)


def record_catalog_quality_event(
    *, values: Sequence[object], request_id: str
) -> object:
    """Append one already-computed bounded quality finding."""
    logger.info("Recording Data catalog quality evidence")
    return create_quality_event_record(tuple(values), request_id=request_id)


def get_catalog_evidence(
    *,
    dataset_id: str,
    symbol_id: str,
    provider_id: str,
    range_start_utc: int,
    range_end_utc: int,
    request_id: str,
    limit: int = 100,
) -> dict[str, object]:
    """Read bounded reference, artifact, integrity, coverage, and event evidence."""
    if limit <= 0 or limit > _MAX_CATALOG_ROWS or range_end_utc < range_start_utc:
        raise DataError("LIMIT_EXCEEDED", request_id=request_id)
    return {
        "reference": read_catalog_reference_records(
            symbol_id, provider_id, request_id=request_id, limit=limit
        ).rows,
        "artifacts": read_catalog_files_for_range(
            dataset_id,
            range_start_utc,
            range_end_utc,
            request_id=request_id,
            limit=limit,
        ).rows,
        "integrity": read_catalog_unverified_count(
            dataset_id, request_id=request_id
        ).rows,
        "coverage": read_catalog_coverage(dataset_id, request_id=request_id).rows,
        "events": read_catalog_event_records(
            symbol_id, request_id=request_id, limit=limit
        ).rows,
    }


def get_verified_research_source(
    source_id: str, parser_version: str, *, request_id: str
) -> dict[str, object] | None:
    """Return one persisted verified-source manifest or explicit absence."""
    result = read_verified_research_source_record(
        source_id, parser_version, request_id=request_id
    )
    return None if not result.rows else dict(result.rows[0])


def get_catalog_table_lifecycles() -> dict[str, tuple[str, ...]]:
    """Return application operation triggers for all declared Data tables."""
    return dict(_CATALOG_TABLE_LIFECYCLES)


def reconcile_data_catalog(*, request_id: str, max_files: int = 1000) -> dict[str, int]:
    """Rebuild artifact rows from bounded authoritative sidecar manifests."""
    if max_files <= 0 or max_files > _MAX_CATALOG_ROWS:
        raise DataError("LIMIT_EXCEEDED", request_id=request_id)
    data_root = resolve_data_root(request_id)
    sidecars = sorted(data_root.rglob("*.manifest.json"))
    if len(sidecars) > max_files:
        raise DataError("LIMIT_EXCEEDED", request_id=request_id)
    indexed = 0
    for sidecar in sidecars:
        manifest = StorageManifest.model_validate_json(
            sidecar.read_text(encoding="utf-8")
        )
        artifact = data_root / Path(manifest.relative_path)
        if not artifact.is_file():
            raise DataError("FILE_CORRUPTED", request_id=request_id)
        digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
        if digest != manifest.content_hash:
            raise DataError("FILE_CORRUPTED", request_id=request_id)
        provenance = dict(manifest.provenance)
        dataset = cast(
            "MarketDataset",
            SimpleNamespace(
                symbol=provenance.get("data.symbol", "UNKNOWN"),
                data_kind=provenance.get("data.data_kind", "bars"),
                timeframe=provenance.get("data.timeframe"),
                source_metadata=provenance,
            ),
        )
        register_catalog_artifact(
            dataset,
            manifest,
            byte_size=artifact.stat().st_size,
            request_id=request_id,
        )
        indexed += 1
    return {"scanned": len(sidecars), "indexed": indexed}


__all__ = (
    "get_catalog_evidence",
    "get_catalog_table_lifecycles",
    "get_verified_research_source",
    "reconcile_data_catalog",
    "record_catalog_fetch",
    "record_catalog_quality_event",
    "register_catalog_artifact",
    "sync_catalog_reference",
)
