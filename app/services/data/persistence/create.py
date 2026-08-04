"""Create operations for Data-owned database records."""

from __future__ import annotations

from typing import Any

from app.services.data.persistence.contracts import (
    StatementPlan,
    TransactionRequest,
    TransactionResult,
)
from app.services.data.persistence.transactions import _execute_transaction_raw
from app.utils import get_logger

logger = get_logger(__name__)

_INSERT_CATALOG_DATASET = """
INSERT INTO data_datasets (
    dataset_id, dataset_kind, owner_domain, symbol_id, timeframe, provider_id,
    producer_ref, root_path, schema_version, normalization_version,
    timestamp_semantics, file_count, total_rows, total_bytes,
    min_ts_utc, max_ts_utc, state, request_id, correlation_id,
    created_at, updated_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""".strip()

_INSERT_CATALOG_FILE = """
INSERT INTO data_partition_files (
    file_id, dataset_id, artifact_id, relative_path, format, content_hash,
    row_count, byte_size, min_ts_utc, max_ts_utc, schema_version,
    normalization_version, source_revision, provenance_json, license_json,
    verify_state, verified_at, request_id, correlation_id, created_at, updated_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""".strip()

_INSERT_FETCH_LOG = """
INSERT INTO data_fetch_log (
    fetch_id, provider_id, symbol_id, data_kind, timeframe,
    range_start_utc, range_end_utc, rows_returned, materialized, dataset_id,
    served_from, fetch_latency_ms, state, error_code, request_id,
    correlation_id, started_at, finished_at, created_at, updated_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""".strip()

_INSERT_QUALITY_EVENT = """
INSERT OR IGNORE INTO data_quality_events (
    event_id, symbol_id, dataset_id, file_id, fetch_id, issue_type, severity,
    action_taken, ts_range_start, ts_range_end, affected_rows, detail_json,
    detected_at, request_id, correlation_id, created_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""".strip()


_INSERT_AUDIT_EVENT = """
INSERT OR IGNORE INTO data_audit_events (
    event_id, timestamp, domain, action, principal_id,
    request_id, correlation_id, causation_id, payload_json
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
""".strip()
_INSERT_FEED = """
INSERT INTO data_feeds (
    feed_id, source_id, symbol, data_kind, timeframe, source_capability,
    buffer_capacity, overflow_policy, heartbeat_timeout_seconds,
    reconnect_policy_json, state, heartbeat_at, last_event_at,
    buffer_depth, dropped_count, gap_count, reconnect_count,
    breaker_state, drift_ms, last_error, request_id, created_at, updated_at
) VALUES (
    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, 0, 0, 0, 0, 'closed',
    NULL, NULL, ?, ?, ?
)
""".strip()
_INSERT_SOURCE_ATTEMPT = """
INSERT INTO data_source_attempts (
    source_id, timestamp_ns, request_id, status, error_code
) VALUES (?, ?, ?, ?, ?)
""".strip()
_INSERT_UPDATE_JOB = """
INSERT INTO data_update_jobs (
    job_id, source_id, symbols_json, timeframes_json, data_kinds_json,
    start, end, interval_seconds, enabled, created_at, request_id,
    state, recovery_state
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'created', 'clean')
""".strip()
_INSERT_BACKFILL_CHECKPOINT = """
INSERT INTO data_backfill_checkpoints (
    idempotency_key, job_id, chunk_id, committed_start, committed_end,
    record_count, content_hash, checkpoint, artifact_temp, artifact_final,
    publication_state, request_id, created_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'prepared', ?, ?)
""".strip()
_INSERT_RESEARCH_SOURCE = """
INSERT INTO data_research_sources (
    document_id, source_id, source_kind, external_id, title, source_url,
    asset_scope_json, issuer_scope_json, language, event_at, published_at,
    first_seen_at, available_at, retrieved_at, revision, previous_document_id,
    original_hash, normalized_hash, original_content, normalized_text, license_id,
    retention_until, trust_status, manipulation_status, injection_status,
    currency, unit, provenance_json, document_kind, macro_series_scope_json,
    parser_version, record_status
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
          ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""".strip()
_INSERT_RESEARCH_OBSERVATION = """
INSERT INTO data_research_observations (
    observation_id, document_id, source_id, series_id, observation_period,
    value_json, unit, published_at, available_at, retrieved_at, revision,
    previous_observation_id, content_hash, parser_version, trust_status,
    provenance_json
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""".strip()
_APPEND_RUNTIME_RECORD = """
INSERT INTO data_runtime_records (
    namespace, collection_name, record_key, partition_key, sequence_number,
    codec_kind, payload_json, revision
) VALUES (?, ?, ?, ?, ?, ?, ?, 1)
""".strip()
_PUT_ONCE_RUNTIME_RECORD = """
INSERT OR IGNORE INTO data_runtime_records (
    namespace, collection_name, record_key, partition_key, sequence_number,
    codec_kind, payload_json, revision
) VALUES (?, ?, ?, '', 0, ?, ?, 1)
""".strip()


def _execute_create(
    statements: tuple[str, ...],
    parameter_sets: tuple[tuple[Any, ...], ...],
    *,
    request_id: str,
    max_rows: int = 1,
) -> TransactionResult:
    """Execute one bounded Data-owned create transaction."""
    return _execute_transaction_raw(
        TransactionRequest(
            plan=StatementPlan(
                statements=statements,
                parameter_sets=parameter_sets,
                max_rows=max_rows,
            ),
            request_id=request_id,
        )
    )


def create_audit_event_record(
    parameters: tuple[Any, ...], *, request_id: str
) -> TransactionResult:
    """Create one immutable audit-event record idempotently.

    Args:
        parameters: Ordered audit-event column values.
        request_id: Caller trace identity.

    Returns:
        Transaction result including the affected-row count.
    """
    logger.debug("Creating Data audit persistence record")
    return _execute_create(
        (_INSERT_AUDIT_EVENT,),
        (parameters,),
        request_id=request_id,
    )


def create_feed_record(
    parameters: tuple[Any, ...], *, request_id: str
) -> TransactionResult:
    """Create one initial persisted feed-state record."""
    logger.debug("Creating Data feed persistence record")
    return _execute_create((_INSERT_FEED,), (parameters,), request_id=request_id)


def create_source_attempt_record(
    parameters: tuple[Any, ...], *, request_id: str
) -> TransactionResult:
    """Create one immutable source-attempt record."""
    logger.debug("Creating Data source-attempt persistence record")
    return _execute_create(
        (_INSERT_SOURCE_ATTEMPT,),
        (parameters,),
        request_id=request_id,
    )


def create_update_job_record(
    parameters: tuple[Any, ...], *, request_id: str
) -> TransactionResult:
    """Create one persisted update-job definition."""
    logger.debug("Creating Data update-job persistence record")
    return _execute_create(
        (_INSERT_UPDATE_JOB,),
        (parameters,),
        request_id=request_id,
    )


def create_backfill_checkpoint_record(
    parameters: tuple[Any, ...], *, request_id: str
) -> TransactionResult:
    """Create one prepared backfill-checkpoint record."""
    logger.debug("Creating Data backfill-checkpoint persistence record")
    return _execute_create(
        (_INSERT_BACKFILL_CHECKPOINT,),
        (parameters,),
        request_id=request_id,
    )


def create_research_source_record(
    parameters: tuple[Any, ...], *, request_id: str
) -> TransactionResult:
    """Create one immutable research-source revision."""
    logger.debug("Creating Data research-source persistence record")
    return _execute_create(
        (_INSERT_RESEARCH_SOURCE,),
        (parameters,),
        request_id=request_id,
    )


def create_research_observation_record(
    parameters: tuple[Any, ...], *, request_id: str
) -> TransactionResult:
    """Create one immutable research-observation revision."""
    logger.debug("Creating Data research-observation persistence record")
    return _execute_create(
        (_INSERT_RESEARCH_OBSERVATION,),
        (parameters,),
        request_id=request_id,
    )


def create_runtime_append_record(
    parameters: tuple[Any, ...], *, request_id: str
) -> TransactionResult:
    """Append one immutable namespaced runtime record."""
    return _execute_create(
        (_APPEND_RUNTIME_RECORD,),
        (parameters,),
        request_id=request_id,
    )


def create_runtime_put_once_record(
    parameters: tuple[Any, ...], *, request_id: str
) -> TransactionResult:
    """Create one namespaced runtime record if its identity is unused."""
    return _execute_create(
        (_PUT_ONCE_RUNTIME_RECORD,),
        (parameters,),
        request_id=request_id,
    )


__all__ = [
    "create_audit_event_record",
    "create_backfill_checkpoint_record",
    "create_feed_record",
    "create_research_observation_record",
    "create_research_source_record",
    "create_runtime_append_record",
    "create_runtime_put_once_record",
    "create_source_attempt_record",
    "create_update_job_record",
]


def create_catalog_dataset_record(
    parameters: tuple[Any, ...], *, request_id: str
) -> TransactionResult:
    """Register one logical dataset in the artifact catalog.

    Args:
        parameters: Ordered ``data_datasets`` column values.
        request_id: Caller trace identity.

    Returns:
        Transaction result including the affected-row count.
    """
    logger.debug("Creating Data catalog dataset record")
    return _execute_create(
        (_INSERT_CATALOG_DATASET,), (parameters,), request_id=request_id
    )


def create_catalog_file_record(
    parameters: tuple[Any, ...], *, request_id: str
) -> TransactionResult:
    """Index one written artifact in the catalog.

    Written only after the artifact and its sidecar manifest are committed to
    disk. A catalog row naming a file that does not exist is a fail-closed read;
    an artifact with no catalog row is invisible and reclaimable, so the
    recoverable failure is the one this ordering produces.

    Args:
        parameters: Ordered ``data_partition_files`` column values.
        request_id: Caller trace identity.

    Returns:
        Transaction result including the affected-row count.
    """
    logger.info("Indexing one Data artifact in the catalog")
    return _execute_create(
        (_INSERT_CATALOG_FILE,), (parameters,), request_id=request_id
    )


def create_fetch_log_record(
    parameters: tuple[Any, ...], *, request_id: str
) -> TransactionResult:
    """Record one broker or catalog fetch, materialised or not.

    Args:
        parameters: Ordered ``data_fetch_log`` column values.
        request_id: Caller trace identity.

    Returns:
        Transaction result including the affected-row count.
    """
    logger.debug("Creating Data fetch-log record")
    return _execute_create((_INSERT_FETCH_LOG,), (parameters,), request_id=request_id)


def create_quality_event_record(
    parameters: tuple[Any, ...], *, request_id: str
) -> TransactionResult:
    """Record one data-quality finding idempotently.

    Args:
        parameters: Ordered ``data_quality_events`` column values.
        request_id: Caller trace identity.

    Returns:
        Transaction result including the affected-row count.
    """
    logger.debug("Creating Data quality-event record")
    return _execute_create(
        (_INSERT_QUALITY_EVENT,), (parameters,), request_id=request_id
    )
