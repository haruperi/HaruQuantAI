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
    create_provider_specification_revision,
    create_quality_event_record,
    read_catalog_coverage,
    read_catalog_event_records,
    read_catalog_files_for_range,
    read_catalog_reference_records,
    read_catalog_unverified_count,
    read_provider_specification_revision_as_of,
    read_provider_specification_revision_interval,
    read_provider_specification_revisions,
    read_ready_dataset_catalog_records,
    read_verified_research_source_record,
    update_provider_specification_revision,
)
from app.services.data.persistence.contracts import StorageManifest
from app.services.data.persistence.dataset_writer import resolve_data_root
from app.utils import canonical_digest, canonical_json, get_logger, utc_now

logger = get_logger(__name__)

if TYPE_CHECKING:
    from app.services.data.contracts.dataset import MarketDataset

_MAX_TEXT_LENGTH = 256
_MAX_CATALOG_ROWS = 1000
_SHA256_HEX_LENGTH = 64
_SNAPSHOT_IDENTITY_FIELDS = (
    "broker",
    "server",
    "environment",
    "account_digest",
    "provider_symbol",
)


def list_verified_datasets(
    *, request_id: str, limit: int = 500
) -> tuple[dict[str, object], ...]:
    """List bounded integrity-verified dataset identities for selection.

    Args:
        request_id: Caller trace identifier.
        limit: Maximum joined artifact rows inspected.

    Returns:
        Dataset summaries whose complete artifact sets remain verified.

    Raises:
        DataError: If the requested bound is invalid.
    """
    if limit <= 0 or limit > _MAX_CATALOG_ROWS:
        raise DataError("LIMIT_EXCEEDED", request_id=request_id)
    rows = read_ready_dataset_catalog_records(request_id=request_id, limit=limit).rows
    grouped: dict[str, list[Mapping[str, object]]] = {}
    for row in rows:
        grouped.setdefault(str(row["dataset_id"]), []).append(row)
    result: list[dict[str, object]] = []
    for dataset_id, artifacts in grouped.items():
        first = artifacts[0]
        if len(artifacts) != int(str(first["file_count"])) or any(
            str(item["verify_state"]) != "verified" for item in artifacts
        ):
            continue
        hashes = [str(item["content_hash"]) for item in artifacts]
        revisions = [str(item["source_revision"]) for item in artifacts]
        result.append(
            {
                "dataset_id": dataset_id,
                "label": " ".join(
                    part
                    for part in (
                        str(first.get("canonical_symbol") or "Dataset"),
                        str(first.get("timeframe") or ""),
                    )
                    if part
                ),
                "dataset_kind": str(first["dataset_kind"]),
                "symbol": first.get("canonical_symbol"),
                "timeframe": first.get("timeframe"),
                "revision": hashlib.sha256("|".join(revisions).encode()).hexdigest(),
                "content_hash": hashlib.sha256("|".join(hashes).encode()).hexdigest(),
                "row_count": int(str(first["total_rows"])),
                "active": True,
            }
        )
    return tuple(result)


def _provider_identity(
    broker: str,
    server: str,
    environment: str,
    account_digest: str,
    provider_symbol: str,
) -> tuple[str, str, str, str, str]:
    """Validate and return one exact provider-specification identity.

    Args:
        broker: Broker/provider identity.
        server: Provider server identity.
        environment: Exact provider environment.
        account_digest: Redacted account digest.
        provider_symbol: Exact provider symbol.

    Returns:
        Validated fixed-width identity tuple.
    """
    values = (broker, server, environment, account_digest, provider_symbol)
    return (
        _text(values[0], _SNAPSHOT_IDENTITY_FIELDS[0]),
        _text(values[1], _SNAPSHOT_IDENTITY_FIELDS[1]),
        _text(values[2], _SNAPSHOT_IDENTITY_FIELDS[2]),
        _text(values[3], _SNAPSHOT_IDENTITY_FIELDS[3]),
        _text(values[4], _SNAPSHOT_IDENTITY_FIELDS[4]),
    )


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
    "data_provider_specification_revisions": (
        "register_provider_specification_revision",
        "get_provider_specification_revision",
        "get_provider_specification_revisions",
    ),
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
    """Validate one bounded catalog identity value.

    Args:
        value: The ``value`` argument.
        field: The ``field`` argument.

    Returns:
        The result produced by the operation.

    Raises:
        DataError: If the operation cannot be completed safely.
    """
    if not value or value != value.strip() or len(value) > _MAX_TEXT_LENGTH:
        raise DataError("INVALID_INPUT", safe_details={"field": field})
    return value


def _identity(prefix: str, *parts: str) -> str:
    """Build a stable opaque catalog identity.

    Args:
        prefix: The ``prefix`` argument.
        parts: The ``parts`` argument.

    Returns:
        The result produced by the operation.
    """
    digest = hashlib.sha256("\x1f".join(parts).encode()).hexdigest()
    return f"{prefix}-{digest}"


def _timestamp(value: datetime) -> str:
    """Serialize one aware UTC timestamp.

    Args:
        value: The ``value`` argument.

    Returns:
        The result produced by the operation.

    Raises:
        DataError: If the operation cannot be completed safely.
    """
    if value.tzinfo is None or value.utcoffset() is None:
        raise DataError("INVALID_INPUT", safe_details={"field": "timestamp"})
    return value.astimezone(UTC).isoformat()


def _snapshot_material(
    snapshot: Mapping[str, object], request_id: str
) -> tuple[dict[str, object], tuple[str, str, str, str, str], datetime]:
    """Validate one opaque Brokers snapshot mapping for persistence.

    Args:
        snapshot: Canonical JSON-safe snapshot mapping.
        request_id: Caller trace identity.

    Returns:
        Defensive payload, exact identity, and observation time.

    Raises:
        DataError: If required identity, timestamp, or checksum evidence is invalid.
    """
    payload = dict(snapshot)
    try:
        identity = _provider_identity(
            *(str(payload[field]) for field in _SNAPSHOT_IDENTITY_FIELDS)
        )
        checksum = _text(str(payload["checksum"]), "checksum")
        observed_at = datetime.fromisoformat(str(payload["observed_at"]))
        _text(str(payload["retrieval_provenance"]), "retrieval_provenance")
    except (KeyError, TypeError, ValueError) as error:
        raise DataError("INVALID_INPUT", request_id=request_id) from error
    if (
        len(checksum) != _SHA256_HEX_LENGTH
        or canonical_digest(
            {key: value for key, value in payload.items() if key != "checksum"}
        )
        != checksum
    ):
        raise DataError("DATA_QUALITY_FAILED", request_id=request_id)
    if observed_at.tzinfo is None or observed_at.utcoffset() is None:
        raise DataError("INVALID_INPUT", request_id=request_id)
    return payload, identity, observed_at.astimezone(UTC)


def _revision_row(row: Mapping[str, object]) -> dict[str, object]:
    """Decode one detached persistence row.

    Args:
        row: Normalized SQLite row.

    Returns:
        JSON-safe revision evidence.
    """
    result = dict(row)
    result["payload"] = json.loads(str(result.pop("payload_json")))
    provenance = result.pop("historical_provenance_json")
    result["historical_provenance"] = (
        None if provenance is None else json.loads(str(provenance))
    )
    return result


def register_provider_specification_revision(
    snapshot: Mapping[str, object],
    *,
    effective_from: datetime | None = None,
    historical_provenance: Mapping[str, object] | None = None,
    request_id: str,
) -> dict[str, object]:
    """Register one immutable effective-dated provider specification.

    Args:
        snapshot: Canonical Brokers snapshot mapping.
        effective_from: Optional verified inclusive effective instant.
        historical_provenance: Required provenance for a pre-observation boundary.
        request_id: Caller trace identity.

    Returns:
        Detached registered revision evidence.

    Raises:
        DataError: If identity, chronology, checksum, overlap, or immutability fails.
    """
    logger.info("Registering provider specification revision")
    payload, identity, observed_at = _snapshot_material(snapshot, request_id)
    start = observed_at if effective_from is None else effective_from
    if start.tzinfo is None or start.utcoffset() is None:
        raise DataError("INVALID_INPUT", request_id=request_id)
    start = start.astimezone(UTC)
    if start < observed_at and not historical_provenance:
        raise DataError("POLICY_BLOCKED", request_id=request_id)
    existing = read_provider_specification_revisions(
        identity, request_id=request_id
    ).rows
    checksum = str(payload["checksum"])
    matching = [row for row in existing if row["snapshot_checksum"] == checksum]
    if matching:
        if str(matching[0]["payload_json"]) != canonical_json(payload):
            raise DataError("DATA_QUALITY_FAILED", request_id=request_id)
        return _revision_row(matching[0])
    if existing and start <= datetime.fromisoformat(
        str(existing[-1]["effective_from"])
    ):
        raise DataError("VALIDATION_FAILED", request_id=request_id)
    previous_id = None if not existing else str(existing[-1]["revision_id"])
    start_text = _timestamp(start)
    observed_text = _timestamp(observed_at)
    revision_id = "provider-spec-" + canonical_digest(
        {"identity": identity, "effective_from": start_text, "checksum": checksum}
    )
    created_at = _timestamp(utc_now())
    parameters = (
        revision_id,
        *identity,
        checksum,
        observed_text,
        start_text,
        None,
        str(payload["retrieval_provenance"]),
        None
        if historical_provenance is None
        else canonical_json(dict(historical_provenance)),
        canonical_json(payload),
        previous_id,
        request_id,
        created_at,
    )
    if previous_id is None:
        create_provider_specification_revision(parameters, request_id=request_id)
    else:
        update_provider_specification_revision(
            previous_id, start_text, parameters, request_id=request_id
        )
    row = read_provider_specification_revision_as_of(
        identity, start_text, request_id=request_id
    ).rows
    if len(row) != 1:
        raise DataError("DATABASE_ERROR", request_id=request_id)
    return _revision_row(row[0])


def get_provider_specification_revision(
    *,
    provider: str,
    server: str,
    environment: str,
    account_digest: str,
    symbol: str,
    as_of: datetime,
    request_id: str,
) -> dict[str, object]:
    """Return the unique provider specification covering one instant.

    Args:
        provider: Broker/provider identity.
        server: Provider server identity.
        environment: Exact provider environment.
        account_digest: Redacted account digest.
        symbol: Exact provider symbol.
        as_of: Point-in-time query instant.
        request_id: Caller trace identity.

    Returns:
        Detached revision evidence with complete coverage.

    Raises:
        DataError: If the instant is invalid or uncovered.
    """
    identity = _provider_identity(provider, server, environment, account_digest, symbol)
    rows = read_provider_specification_revision_as_of(
        identity, _timestamp(as_of), request_id=request_id
    ).rows
    if len(rows) != 1:
        raise DataError("DATA_NOT_FOUND", request_id=request_id)
    return {**_revision_row(rows[0]), "complete_coverage": True}


def get_provider_specification_revisions(
    *,
    provider: str,
    server: str,
    environment: str,
    account_digest: str,
    symbol: str,
    interval_start: datetime,
    interval_end: datetime,
    request_id: str,
) -> dict[str, object]:
    """Return revisions proving complete coverage of a bounded interval.

    Args:
        provider: Broker/provider identity.
        server: Provider server identity.
        environment: Exact provider environment.
        account_digest: Redacted account digest.
        symbol: Exact provider symbol.
        interval_start: Inclusive query bound.
        interval_end: Exclusive query bound.
        request_id: Caller trace identity.

    Returns:
        Ordered detached revisions and explicit coverage proof.

    Raises:
        DataError: If bounds are invalid or coverage contains a gap.
    """
    start_text = _timestamp(interval_start)
    end_text = _timestamp(interval_end)
    if interval_start >= interval_end:
        raise DataError("INVALID_INPUT", request_id=request_id)
    identity = _provider_identity(provider, server, environment, account_digest, symbol)
    rows = read_provider_specification_revision_interval(
        identity, start_text, end_text, request_id=request_id
    ).rows
    if not rows or str(rows[0]["effective_from"]) > start_text:
        raise DataError("DATA_NOT_FOUND", request_id=request_id)
    cursor = start_text
    for row in rows:
        if str(row["effective_from"]) > cursor:
            raise DataError("DATA_NOT_FOUND", request_id=request_id)
        effective_to = row["effective_to"]
        if effective_to is None:
            cursor = end_text
            break
        cursor = max(cursor, str(effective_to))
    if cursor < end_text:
        raise DataError("DATA_NOT_FOUND", request_id=request_id)
    return {
        "interval_start": start_text,
        "interval_end": end_text,
        "complete_coverage": True,
        "revisions": tuple(_revision_row(row) for row in rows),
    }


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
    """Synchronize source-authoritative provider, symbol, and session evidence.

    Args:
        provider_code: The ``provider_code`` argument.
        provider_kind: The ``provider_kind`` argument.
        canonical_symbol: The ``canonical_symbol`` argument.
        asset_class: The ``asset_class`` argument.
        base_currency: The ``base_currency`` argument.
        quote_currency: The ``quote_currency`` argument.
        digits: The ``digits`` argument.
        tick_size: The ``tick_size`` argument.
        min_volume: The ``min_volume`` argument.
        max_volume: The ``max_volume`` argument.
        volume_step: The ``volume_step`` argument.
        sessions: The ``sessions`` argument.
        request_id: The ``request_id`` argument.
        correlation_id: The ``correlation_id`` argument.
        observed_at: The ``observed_at`` argument.

    Returns:
        The result produced by the operation.
    """
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
    """Register one committed dataset artifact and sidecar atomically.

    Args:
        dataset: The ``dataset`` argument.
        manifest: The ``manifest`` argument.
        byte_size: The ``byte_size`` argument.
        request_id: The ``request_id`` argument.
        correlation_id: The ``correlation_id`` argument.

    Returns:
        The result produced by the operation.
    """
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
    """Append one already-classified bounded fetch outcome.

    Args:
        values: The ``values`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.
    """
    logger.info("Recording Data catalog fetch evidence")
    return create_fetch_log_record(tuple(values), request_id=request_id)


def record_catalog_quality_event(
    *, values: Sequence[object], request_id: str
) -> object:
    """Append one already-computed bounded quality finding.

    Args:
        values: The ``values`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.
    """
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
    """Read bounded reference, artifact, integrity, coverage, and event evidence.

    Args:
        dataset_id: The ``dataset_id`` argument.
        symbol_id: The ``symbol_id`` argument.
        provider_id: The ``provider_id`` argument.
        range_start_utc: The ``range_start_utc`` argument.
        range_end_utc: The ``range_end_utc`` argument.
        request_id: The ``request_id`` argument.
        limit: The ``limit`` argument.

    Returns:
        The result produced by the operation.

    Raises:
        DataError: If the operation cannot be completed safely.
    """
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
    """Return one persisted verified-source manifest or explicit absence.

    Args:
        source_id: The ``source_id`` argument.
        parser_version: The ``parser_version`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.
    """
    result = read_verified_research_source_record(
        source_id, parser_version, request_id=request_id
    )
    return None if not result.rows else dict(result.rows[0])


def get_catalog_table_lifecycles() -> dict[str, tuple[str, ...]]:
    """Return application operation triggers for all declared Data tables.

    Returns:
        The result produced by the operation.
    """
    return dict(_CATALOG_TABLE_LIFECYCLES)


def reconcile_data_catalog(*, request_id: str, max_files: int = 1000) -> dict[str, int]:
    """Rebuild artifact rows from bounded authoritative sidecar manifests.

    Args:
        request_id: The ``request_id`` argument.
        max_files: The ``max_files`` argument.

    Returns:
        The result produced by the operation.

    Raises:
        DataError: If the operation cannot be completed safely.
    """
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
    "get_provider_specification_revision",
    "get_provider_specification_revisions",
    "get_verified_research_source",
    "list_verified_datasets",
    "reconcile_data_catalog",
    "record_catalog_fetch",
    "record_catalog_quality_event",
    "register_catalog_artifact",
    "register_provider_specification_revision",
    "sync_catalog_reference",
)
