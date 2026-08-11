"""Read operations for Data-owned database records."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from app.services.data.persistence.contracts import (
    StatementPlan,
    TransactionRequest,
    TransactionResult,
)
from app.services.data.persistence.transactions import _execute_transaction_raw
from app.utils import get_logger

logger = get_logger(__name__)

_CACHE_COLUMNS = (
    "dataset_json, created_at, expires_at, source_revision, raw_data_hash, "
    "schema_version, normalization_version, request_id"
)
_ECONOMIC_EVENT_COLUMNS = (
    "e.event_id, e.title, e.country, e.scheduled_at, "
    "e.original_scheduled_at, e.impact, e.actual, e.forecast, e.previous, "
    "e.revised_previous, e.provider, COALESCE(d.source_url, e.source_url) "
    "AS source_url, e.first_seen_at, e.updated_at, e.request_id, "
    "e.provider_definition_id, d.source_original, d.source_latest, d.measures, "
    "d.effect, d.frequency, d.also_called, d.event_type"
)
_FEED_COLUMNS = (
    "feed_id, source_id, symbol, data_kind, timeframe, source_capability, "
    "buffer_capacity, overflow_policy, heartbeat_timeout_seconds, state, "
    "heartbeat_at, last_event_at, buffer_depth, dropped_count, gap_count, "
    "reconnect_count, breaker_state, breaker_opened_at, drift_ms, last_error"
)
_RESEARCH_SOURCE_COLUMNS = (
    "document_id, source_id, source_kind, document_kind, external_id, title, "
    "source_url, asset_scope_json, issuer_scope_json, macro_series_scope_json, "
    "language, event_at, published_at, first_seen_at, available_at, retrieved_at, "
    "revision, previous_document_id, original_hash, normalized_hash, license_id, "
    "retention_until, trust_status, manipulation_status, injection_status, "
    "currency, unit, parser_version, record_status, provenance_json"
)
_RESEARCH_OBSERVATION_COLUMNS = (
    "observation_id, document_id, source_id, series_id, observation_period, "
    "value_json, unit, published_at, available_at, retrieved_at, revision, "
    "previous_observation_id, content_hash, parser_version, trust_status, "
    "provenance_json"
)


def _execute_read(
    statement: str,
    parameters: tuple[Any, ...],
    *,
    request_id: str,
    max_rows: int,
) -> TransactionResult:
    """Execute one bounded Data-owned read transaction.

    Args:
        statement: The ``statement`` argument.
        parameters: The ``parameters`` argument.
        request_id: The ``request_id`` argument.
        max_rows: The ``max_rows`` argument.

    Returns:
        The result produced by the operation.
    """
    return _execute_transaction_raw(
        TransactionRequest(
            plan=StatementPlan(
                statements=(statement,),
                parameter_sets=(parameters,),
                max_rows=max_rows,
            ),
            request_id=request_id,
        )
    )


def read_cache_record(key: str, *, request_id: str) -> TransactionResult:
    """Read one cache record by exact identity.

    Args:
        key: The ``key`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.
    """
    logger.debug("Reading Data cache persistence record")
    return _execute_read(
        f"SELECT {_CACHE_COLUMNS} FROM data_cache WHERE key = ?",  # noqa: S608
        (key,),
        request_id=request_id,
        max_rows=1,
    )


def read_cache_records(*, request_id: str, limit: int) -> TransactionResult:
    """Read a bounded cache-record candidate set for filtering.

    Args:
        request_id: The ``request_id`` argument.
        limit: The ``limit`` argument.

    Returns:
        The result produced by the operation.
    """
    logger.debug("Reading Data cache persistence records")
    return _execute_read(
        "SELECT key, dataset_json FROM data_cache",
        (),
        request_id=request_id,
        max_rows=limit,
    )


def read_audit_event_records(
    *,
    start: str,
    end: str,
    domain: str | None,
    action: str | None,
    principal_id: str | None,
    correlation_id: str | None,
    cursor_timestamp: str | None,
    cursor_event_id: str | None,
    limit: int,
    request_id: str,
) -> TransactionResult:
    """Read one bounded, deterministically ordered audit-event page.

    Args:
        start: The ``start`` argument.
        end: The ``end`` argument.
        domain: The ``domain`` argument.
        action: The ``action`` argument.
        principal_id: The ``principal_id`` argument.
        correlation_id: The ``correlation_id`` argument.
        cursor_timestamp: The ``cursor_timestamp`` argument.
        cursor_event_id: The ``cursor_event_id`` argument.
        limit: The ``limit`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.
    """
    sql_parts = [
        "SELECT event_id, timestamp, domain, action, principal_id, request_id, "
        "correlation_id, causation_id, payload_json FROM data_audit_events "
        "WHERE timestamp >= ? AND timestamp <= ?"
    ]
    parameters: list[Any] = [start, end]
    for column, value in (
        ("domain", domain),
        ("action", action),
        ("principal_id", principal_id),
        ("correlation_id", correlation_id),
    ):
        if value is not None:
            sql_parts.append(f"AND {column} = ?")
            parameters.append(value)
    if cursor_timestamp is not None and cursor_event_id is not None:
        sql_parts.append("AND (timestamp > ? OR (timestamp = ? AND event_id > ?))")
        parameters.extend([cursor_timestamp, cursor_timestamp, cursor_event_id])
    sql_parts.append("ORDER BY timestamp ASC, event_id ASC LIMIT ?")
    parameters.append(limit)
    logger.debug("Reading Data audit persistence records")
    return _execute_read(
        " ".join(sql_parts),
        tuple(parameters),
        request_id=request_id,
        max_rows=limit,
    )


def read_economic_event_records(
    *,
    start: str,
    end: str,
    currencies: Sequence[str] | None,
    countries: Sequence[str] | None,
    minimum_impact: int | None,
    provider: str | None,
    request_id: str,
    limit: int = 100_000,
) -> TransactionResult:
    """Read bounded stored economic events under optional filters.

    Args:
        start: The ``start`` argument.
        end: The ``end`` argument.
        currencies: The ``currencies`` argument.
        countries: The ``countries`` argument.
        minimum_impact: The ``minimum_impact`` argument.
        provider: The ``provider`` argument.
        request_id: The ``request_id`` argument.
        limit: The ``limit`` argument.

    Returns:
        The result produced by the operation.
    """
    sql = (
        f"SELECT {_ECONOMIC_EVENT_COLUMNS} FROM data_economic_events e "  # noqa: S608
        "LEFT JOIN data_economic_event_definitions d "
        "ON d.provider = 'forexfactory' "
        "AND d.provider_definition_id = e.provider_definition_id "
        "WHERE e.scheduled_at >= ? AND e.scheduled_at < ?"
    )
    clauses: list[str] = []
    parameters: list[Any] = [start, end]
    if currencies:
        clauses.append(f"e.country IN ({', '.join('?' for _ in currencies)})")
        parameters.extend(currencies)
    if countries:
        clauses.append(f"e.country IN ({', '.join('?' for _ in countries)})")
        parameters.extend(countries)
    if minimum_impact is not None:
        clauses.append("e.impact >= ?")
        parameters.append(minimum_impact)
    if provider is not None:
        clauses.append("e.provider = ?")
        parameters.append(provider)
    if clauses:
        sql = f"{sql} AND {' AND '.join(clauses)}"
    logger.debug("Reading Data economic-event persistence records")
    return _execute_read(
        f"{sql} ORDER BY e.scheduled_at ASC",
        tuple(parameters),
        request_id=request_id,
        max_rows=limit,
    )


def read_economic_calendar_coverage_records(
    *, start: str, end: str, request_id: str, limit: int = 1000
) -> TransactionResult:
    """Read complete coverage intervals overlapping one requested window.

    Args:
        start: The ``start`` argument.
        end: The ``end`` argument.
        request_id: The ``request_id`` argument.
        limit: The ``limit`` argument.

    Returns:
        The result produced by the operation.
    """
    return _execute_read(
        "SELECT provider, range_start, range_end, status, source_revision, "
        "synchronized_at FROM data_economic_calendar_coverage "
        "WHERE range_end > ? AND range_start < ? "
        "ORDER BY range_start ASC LIMIT ?",
        (start, end, limit),
        request_id=request_id,
        max_rows=limit,
    )


def read_feed_record(feed_id: str, *, request_id: str) -> TransactionResult:
    """Read one complete persisted feed-state record.

    Args:
        feed_id: The ``feed_id`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.
    """
    logger.debug("Reading Data feed persistence record")
    return _execute_read(
        f"SELECT {_FEED_COLUMNS} FROM data_feeds WHERE feed_id = ?",  # noqa: S608
        (feed_id,),
        request_id=request_id,
        max_rows=1,
    )


def read_recent_source_attempt_records(
    source_id: str, limit: int, *, request_id: str
) -> TransactionResult:
    """Read recent source attempts in reverse observation order.

    Args:
        source_id: The ``source_id`` argument.
        limit: The ``limit`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.
    """
    logger.debug("Reading Data source-attempt persistence records")
    return _execute_read(
        "SELECT status, timestamp_ns FROM data_source_attempts "
        "WHERE source_id = ? ORDER BY timestamp_ns DESC LIMIT ?",
        (source_id, limit),
        request_id=request_id,
        max_rows=limit,
    )


def read_source_attempt_count(
    source_id: str, minimum_timestamp_ns: str, *, request_id: str
) -> TransactionResult:
    """Count source attempts inside one durable policy window.

    Args:
        source_id: The ``source_id`` argument.
        minimum_timestamp_ns: The ``minimum_timestamp_ns`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.
    """
    logger.debug("Reading Data source-attempt persistence count")
    return _execute_read(
        "SELECT COUNT(*) AS count_val FROM data_source_attempts "
        "WHERE source_id = ? AND timestamp_ns >= ?",
        (source_id, minimum_timestamp_ns),
        request_id=request_id,
        max_rows=1,
    )


def read_source_state_record(source_id: str, *, request_id: str) -> TransactionResult:
    """Read one persisted source-readiness state.

    Args:
        source_id: The ``source_id`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.
    """
    logger.debug("Reading Data source-state persistence record")
    return _execute_read(
        "SELECT readiness, descriptor_revision FROM data_source_state "
        "WHERE source_id = ?",
        (source_id,),
        request_id=request_id,
        max_rows=1,
    )


def read_update_job_identity(job_id: str, *, request_id: str) -> TransactionResult:
    """Read whether one update-job identity exists.

    Args:
        job_id: The ``job_id`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.
    """
    return _execute_read(
        "SELECT job_id FROM data_update_jobs WHERE job_id = ?",
        (job_id,),
        request_id=request_id,
        max_rows=1,
    )


def read_update_job_start_state(job_id: str, *, request_id: str) -> TransactionResult:
    """Read update-job state required by the start transition.

    Args:
        job_id: The ``job_id`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.
    """
    return _execute_read(
        "SELECT job_id, interval_seconds, state, lease_owner, lease_expires_at "
        "FROM data_update_jobs WHERE job_id = ?",
        (job_id,),
        request_id=request_id,
        max_rows=1,
    )


def read_update_job_status_record(job_id: str, *, request_id: str) -> TransactionResult:
    """Read one update-job status record.

    Args:
        job_id: The ``job_id`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.
    """
    return _execute_read(
        "SELECT job_id, state, enabled, last_run_status, last_checkpoint, "
        "last_error, next_run_at, lease_owner, lease_expires_at, recovery_state "
        "FROM data_update_jobs WHERE job_id = ?",
        (job_id,),
        request_id=request_id,
        max_rows=1,
    )


def read_update_job_definition_record(
    job_id: str, *, request_id: str
) -> TransactionResult:
    """Read the persisted definition and lease state for one update job.

    Args:
        job_id: The ``job_id`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.
    """
    return _execute_read(
        "SELECT job_id, source_id, symbols_json, timeframes_json, data_kinds_json, "
        "start, end, interval_seconds, enabled, state, lease_owner, lease_expires_at, "
        "environment "
        "FROM data_update_jobs WHERE job_id = ?",
        (job_id,),
        request_id=request_id,
        max_rows=1,
    )


def read_update_job_enabled(job_id: str, *, request_id: str) -> TransactionResult:
    """Read the persisted enabled flag for one update job.

    Args:
        job_id: The ``job_id`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.
    """
    return _execute_read(
        "SELECT enabled FROM data_update_jobs WHERE job_id = ?",
        (job_id,),
        request_id=request_id,
        max_rows=1,
    )


def read_latest_backfill_end(job_id: str, *, request_id: str) -> TransactionResult:
    """Read the latest committed backfill end for one job.

    Args:
        job_id: The ``job_id`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.
    """
    return _execute_read(
        "SELECT MAX(committed_end) AS max_end FROM data_backfill_checkpoints "
        "WHERE job_id = ?",
        (job_id,),
        request_id=request_id,
        max_rows=1,
    )


def read_committed_backfill_record(
    idempotency_key: str, *, request_id: str
) -> TransactionResult:
    """Read one committed backfill checkpoint by idempotency identity.

    Args:
        idempotency_key: The ``idempotency_key`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.
    """
    return _execute_read(
        "SELECT job_id, chunk_id, idempotency_key, committed_start, "
        "committed_end, record_count, content_hash, artifact_final "
        "FROM data_backfill_checkpoints WHERE idempotency_key = ? "
        "AND publication_state = 'committed'",
        (idempotency_key,),
        request_id=request_id,
        max_rows=1,
    )


def read_prepared_backfill_records(*, request_id: str, limit: int) -> TransactionResult:
    """Read ordered prepared backfill checkpoints for recovery.

    Args:
        request_id: The ``request_id`` argument.
        limit: The ``limit`` argument.

    Returns:
        The result produced by the operation.
    """
    return _execute_read(
        "SELECT idempotency_key, job_id, content_hash, artifact_temp, "
        "artifact_final FROM data_backfill_checkpoints "
        "WHERE publication_state = 'prepared' "
        "ORDER BY created_at, idempotency_key",
        (),
        request_id=request_id,
        max_rows=limit,
    )


def read_latest_research_source_record(
    source_id: str, external_id: str, *, request_id: str
) -> TransactionResult:
    """Read the latest immutable revision for one research-source identity.

    Args:
        source_id: The ``source_id`` argument.
        external_id: The ``external_id`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.
    """
    return _execute_read(
        f"SELECT {_RESEARCH_SOURCE_COLUMNS} FROM data_research_sources "  # noqa: S608
        "WHERE source_id = ? AND external_id = ? "
        "ORDER BY revision DESC LIMIT 1",
        (source_id, external_id),
        request_id=request_id,
        max_rows=1,
    )


def read_research_source_records(
    decision_time: str,
    limit: int,
    offset: int,
    *,
    request_id: str,
) -> TransactionResult:
    """Read a decision-time ordered research-source page.

    Args:
        decision_time: The ``decision_time`` argument.
        limit: The ``limit`` argument.
        offset: The ``offset`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.
    """
    return _execute_read(
        f"SELECT {_RESEARCH_SOURCE_COLUMNS} FROM data_research_sources "  # noqa: S608
        "WHERE available_at <= ? "
        "ORDER BY available_at, source_id, external_id, revision LIMIT ? OFFSET ?",
        (decision_time, limit, offset),
        request_id=request_id,
        max_rows=limit,
    )


def read_latest_research_observation_record(
    source_id: str,
    series_id: str,
    observation_period: str,
    *,
    request_id: str,
) -> TransactionResult:
    """Read the latest immutable revision for one research observation.

    Args:
        source_id: The ``source_id`` argument.
        series_id: The ``series_id`` argument.
        observation_period: The ``observation_period`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.
    """
    return _execute_read(
        f"SELECT {_RESEARCH_OBSERVATION_COLUMNS} "  # noqa: S608
        "FROM data_research_observations WHERE source_id = ? AND series_id = ? "
        "AND observation_period = ? ORDER BY revision DESC LIMIT 1",
        (source_id, series_id, observation_period),
        request_id=request_id,
        max_rows=1,
    )


def read_research_observation_records(
    decision_time: str,
    source_id: str | None,
    series_id: str | None,
    limit: int,
    *,
    request_id: str,
) -> TransactionResult:
    """Read bounded research observations available by decision time.

    Args:
        decision_time: The ``decision_time`` argument.
        source_id: The ``source_id`` argument.
        series_id: The ``series_id`` argument.
        limit: The ``limit`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.
    """
    return _execute_read(
        f"SELECT {_RESEARCH_OBSERVATION_COLUMNS} "  # noqa: S608
        "FROM data_research_observations WHERE available_at <= ? "
        "AND (? IS NULL OR source_id = ?) AND (? IS NULL OR series_id = ?) "
        "ORDER BY available_at, source_id, series_id, revision LIMIT ?",
        (decision_time, source_id, source_id, series_id, series_id, limit),
        request_id=request_id,
        max_rows=limit,
    )


def read_runtime_record(
    namespace: str,
    collection: str,
    key: str,
    *,
    request_id: str,
) -> TransactionResult:
    """Read one namespaced runtime record by exact key.

    Args:
        namespace: The ``namespace`` argument.
        collection: The ``collection`` argument.
        key: The ``key`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.
    """
    return _execute_read(
        "SELECT codec_kind, payload_json, revision FROM data_runtime_records "
        "WHERE namespace = ? AND collection_name = ? AND record_key = ?",
        (namespace, collection, key),
        request_id=request_id,
        max_rows=1,
    )


def read_runtime_partition_records(
    namespace: str,
    collection: str,
    partition: str,
    limit: int,
    *,
    request_id: str,
) -> TransactionResult:
    """Read ordered runtime records from one exact partition.

    Args:
        namespace: The ``namespace`` argument.
        collection: The ``collection`` argument.
        partition: The ``partition`` argument.
        limit: The ``limit`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.
    """
    return _execute_read(
        "SELECT codec_kind, payload_json, revision FROM data_runtime_records "
        "WHERE namespace = ? AND collection_name = ? AND partition_key = ? "
        "ORDER BY sequence_number ASC LIMIT ?",
        (namespace, collection, partition, limit),
        request_id=request_id,
        max_rows=limit,
    )


def read_runtime_collection_records(
    namespace: str,
    collection: str,
    limit: int,
    *,
    request_id: str,
) -> TransactionResult:
    """Read deterministic runtime records across collection partitions.

    Args:
        namespace: The ``namespace`` argument.
        collection: The ``collection`` argument.
        limit: The ``limit`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.
    """
    return _execute_read(
        "SELECT codec_kind, payload_json, revision FROM data_runtime_records "
        "WHERE namespace = ? AND collection_name = ? "
        "ORDER BY sequence_number ASC, partition_key ASC LIMIT ?",
        (namespace, collection, limit),
        request_id=request_id,
        max_rows=limit,
    )


__all__ = [
    "read_audit_event_records",
    "read_cache_record",
    "read_cache_records",
    "read_catalog_coverage",
    "read_catalog_event_records",
    "read_catalog_files_for_range",
    "read_catalog_reference_records",
    "read_catalog_unverified_count",
    "read_committed_backfill_record",
    "read_economic_calendar_coverage_records",
    "read_economic_event_records",
    "read_feed_record",
    "read_latest_backfill_end",
    "read_latest_research_observation_record",
    "read_latest_research_source_record",
    "read_prepared_backfill_records",
    "read_recent_source_attempt_records",
    "read_research_observation_records",
    "read_research_source_records",
    "read_runtime_collection_records",
    "read_runtime_partition_records",
    "read_runtime_record",
    "read_source_attempt_count",
    "read_source_state_record",
    "read_update_job_definition_record",
    "read_update_job_enabled",
    "read_update_job_identity",
    "read_update_job_start_state",
    "read_update_job_status_record",
    "read_verified_research_source_record",
]


_SELECT_CATALOG_FILES_FOR_RANGE = """
SELECT f.file_id, f.relative_path, f.format, f.content_hash,
       f.min_ts_utc, f.max_ts_utc, f.row_count, f.verify_state
FROM data_partition_files f
JOIN data_datasets d ON d.dataset_id = f.dataset_id
WHERE f.dataset_id = ?
  AND f.max_ts_utc >= ?
  AND f.min_ts_utc <= ?
  AND d.state = 'ready'
ORDER BY f.min_ts_utc
""".strip()

_SELECT_CATALOG_UNVERIFIED_COUNT = """
SELECT COUNT(*) AS unverified
FROM data_partition_files
WHERE dataset_id = ? AND verify_state IN ('hash_mismatch', 'missing')
""".strip()

_SELECT_CATALOG_COVERAGE = """
SELECT MIN(min_ts_utc) AS have_from, MAX(max_ts_utc) AS have_to,
       SUM(row_count) AS total_rows, COUNT(*) AS artifact_count
FROM data_partition_files
WHERE dataset_id = ? AND verify_state <> 'missing'
""".strip()

_SELECT_CATALOG_DATASET = """
SELECT dataset_id, root_path, schema_version, normalization_version,
       timestamp_semantics, state
FROM data_datasets
WHERE dataset_kind = ? AND symbol_id IS ? AND timeframe IS ?
""".strip()


def read_catalog_dataset(
    dataset_kind: str,
    symbol_id: str | None,
    timeframe: str | None,
    *,
    request_id: str,
) -> TransactionResult:
    """Resolve one logical dataset by kind, symbol, and timeframe.

    Args:
        dataset_kind: Catalog dataset kind.
        symbol_id: Canonical symbol identity, or None for symbol-free datasets.
        timeframe: Bar timeframe, or None for tick and reference datasets.
        request_id: Caller trace identity.

    Returns:
        Transaction result carrying at most one dataset row.
    """
    logger.debug("Reading one Data catalog dataset")
    return _execute_read(
        _SELECT_CATALOG_DATASET,
        (dataset_kind, symbol_id, timeframe),
        request_id=request_id,
        max_rows=1,
    )


def read_catalog_files_for_range(
    dataset_id: str,
    range_start_utc: int,
    range_end_utc: int,
    *,
    request_id: str,
    limit: int,
) -> TransactionResult:
    """Select the artifacts covering one time range without opening any of them.

    The overlap predicate is ``max >= start AND min <= end``: an artifact that
    begins before the window and extends into it must be returned, which a
    ``BETWEEN`` on the lower bound alone would silently drop.

    Args:
        dataset_id: Owning dataset identity.
        range_start_utc: Inclusive range start.
        range_end_utc: Inclusive range end.
        request_id: Caller trace identity.
        limit: Bounded maximum artifact count.

    Returns:
        Transaction result carrying candidate artifact rows in time order.
    """
    logger.debug("Selecting Data catalog artifacts for a time range")
    return _execute_read(
        _SELECT_CATALOG_FILES_FOR_RANGE,
        (dataset_id, range_start_utc, range_end_utc),
        request_id=request_id,
        max_rows=limit,
    )


def read_catalog_unverified_count(
    dataset_id: str, *, request_id: str
) -> TransactionResult:
    """Count artifacts whose bytes no longer match their recorded hash.

    A non-zero result blocks a pinned read: an unverifiable artifact is missing
    evidence, and missing evidence fails closed.

    Args:
        dataset_id: Owning dataset identity.
        request_id: Caller trace identity.

    Returns:
        Transaction result carrying one count row.
    """
    logger.debug("Checking Data catalog artifact integrity")
    return _execute_read(
        _SELECT_CATALOG_UNVERIFIED_COUNT,
        (dataset_id,),
        request_id=request_id,
        max_rows=1,
    )


def read_catalog_coverage(dataset_id: str, *, request_id: str) -> TransactionResult:
    """Report the stored range and row count for one dataset.

    Answers "do I need to fetch?" from a handful of catalog rows rather than by
    scanning stored records.

    Args:
        dataset_id: Owning dataset identity.
        request_id: Caller trace identity.

    Returns:
        Transaction result carrying one coverage row.
    """
    logger.debug("Reading Data catalog coverage")
    return _execute_read(
        _SELECT_CATALOG_COVERAGE, (dataset_id,), request_id=request_id, max_rows=1
    )


def read_catalog_reference_records(
    symbol_id: str, provider_id: str, *, request_id: str, limit: int
) -> TransactionResult:
    """Read one provider/symbol reference and its bounded active sessions.

    Args:
        symbol_id: The ``symbol_id`` argument.
        provider_id: The ``provider_id`` argument.
        request_id: The ``request_id`` argument.
        limit: The ``limit`` argument.

    Returns:
        The result produced by the operation.
    """
    statement = """
SELECT s.symbol_id, s.canonical_symbol, s.state,
       p.provider_id, p.provider_code, p.enabled,
       m.session_id, m.day_of_week, m.open_time_utc, m.close_time_utc
FROM data_symbols s
JOIN data_providers p ON p.provider_id = ?
LEFT JOIN data_market_sessions m
  ON m.symbol_id = s.symbol_id AND m.effective_to IS NULL
WHERE s.symbol_id = ? AND s.deleted_at IS NULL
ORDER BY m.day_of_week, m.open_time_utc
""".strip()
    return _execute_read(
        statement,
        (provider_id, symbol_id),
        request_id=request_id,
        max_rows=limit,
    )


def read_catalog_event_records(
    symbol_id: str, *, request_id: str, limit: int
) -> TransactionResult:
    """Read bounded fetch and quality evidence for one canonical symbol.

    Args:
        symbol_id: The ``symbol_id`` argument.
        request_id: The ``request_id`` argument.
        limit: The ``limit`` argument.

    Returns:
        The result produced by the operation.
    """
    statement = """
SELECT 'fetch' AS record_kind, fetch_id AS record_id, state, error_code
FROM data_fetch_log WHERE symbol_id = ?
UNION ALL
SELECT 'quality' AS record_kind, event_id AS record_id, severity AS state,
       issue_type AS error_code
FROM data_quality_events WHERE symbol_id = ?
ORDER BY record_id
""".strip()
    return _execute_read(
        statement,
        (symbol_id, symbol_id),
        request_id=request_id,
        max_rows=limit,
    )


def read_verified_research_source_record(
    source_id: str, parser_version: str, *, request_id: str
) -> TransactionResult:
    """Read one persisted verified-source manifest exactly.

    Args:
        source_id: The ``source_id`` argument.
        parser_version: The ``parser_version`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.
    """
    statement = """
SELECT source_id, parser_version, verified_at, external_record_id,
       fixture_sha256, environments_json, license_policy
FROM data_verified_research_sources
WHERE source_id = ? AND parser_version = ?
""".strip()
    return _execute_read(
        statement,
        (source_id, parser_version),
        request_id=request_id,
        max_rows=1,
    )
