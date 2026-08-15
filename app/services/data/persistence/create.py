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

_INSERT_PROVIDER_SPECIFICATION_REVISION = """
INSERT INTO data_provider_specification_revisions (
    revision_id, broker, server, environment, account_digest, provider_symbol,
    snapshot_checksum, observed_at, effective_from, effective_to,
    retrieval_provenance, historical_provenance_json, payload_json,
    supersedes_revision_id, request_id, created_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""".strip()

_UPSERT_CATALOG_SYMBOL = """
INSERT INTO data_symbols (
    symbol_id, canonical_symbol, asset_class, base_currency, quote_currency,
    digits, tick_size_decimal, min_volume_decimal, max_volume_decimal,
    volume_step_decimal, contract_size_decimal, spec_json, state,
    request_id, correlation_id, created_at, updated_at, deleted_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
ON CONFLICT(symbol_id) DO UPDATE SET
    canonical_symbol = excluded.canonical_symbol,
    asset_class = excluded.asset_class,
    base_currency = excluded.base_currency,
    quote_currency = excluded.quote_currency,
    digits = excluded.digits,
    tick_size_decimal = excluded.tick_size_decimal,
    min_volume_decimal = excluded.min_volume_decimal,
    max_volume_decimal = excluded.max_volume_decimal,
    volume_step_decimal = excluded.volume_step_decimal,
    contract_size_decimal = excluded.contract_size_decimal,
    spec_json = excluded.spec_json,
    state = excluded.state,
    request_id = excluded.request_id,
    correlation_id = excluded.correlation_id,
    updated_at = excluded.updated_at,
    deleted_at = NULL
""".strip()

_UPSERT_CATALOG_PROVIDER = """
INSERT INTO data_providers (
    provider_id, provider_code, provider_kind, priority, trust_tier,
    rate_limit, rate_window_seconds, license_json, enabled,
    request_id, correlation_id, created_at, updated_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(provider_id) DO UPDATE SET
    provider_code = excluded.provider_code,
    provider_kind = excluded.provider_kind,
    priority = excluded.priority,
    trust_tier = excluded.trust_tier,
    rate_limit = excluded.rate_limit,
    rate_window_seconds = excluded.rate_window_seconds,
    license_json = excluded.license_json,
    enabled = excluded.enabled,
    request_id = excluded.request_id,
    correlation_id = excluded.correlation_id,
    updated_at = excluded.updated_at
""".strip()

_UPSERT_CATALOG_SESSION = """
INSERT INTO data_market_sessions (
    session_id, symbol_id, session_name, day_of_week, open_time_utc,
    close_time_utc, is_trading, effective_from, effective_to,
    request_id, correlation_id, created_at, updated_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(session_id) DO UPDATE SET
    symbol_id = excluded.symbol_id,
    session_name = excluded.session_name,
    day_of_week = excluded.day_of_week,
    open_time_utc = excluded.open_time_utc,
    close_time_utc = excluded.close_time_utc,
    is_trading = excluded.is_trading,
    effective_from = excluded.effective_from,
    effective_to = excluded.effective_to,
    request_id = excluded.request_id,
    correlation_id = excluded.correlation_id,
    updated_at = excluded.updated_at
""".strip()

_INSERT_CATALOG_DATASET = """
INSERT INTO data_datasets (
    dataset_id, dataset_kind, owner_domain, symbol_id, timeframe, provider_id,
    producer_ref, root_path, schema_version, normalization_version,
    timestamp_semantics, file_count, total_rows, total_bytes,
    min_ts_utc, max_ts_utc, state, request_id, correlation_id,
    created_at, updated_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(dataset_id) DO UPDATE SET
    producer_ref = excluded.producer_ref,
    root_path = excluded.root_path,
    schema_version = excluded.schema_version,
    normalization_version = excluded.normalization_version,
    file_count = excluded.file_count,
    total_rows = excluded.total_rows,
    total_bytes = excluded.total_bytes,
    min_ts_utc = excluded.min_ts_utc,
    max_ts_utc = excluded.max_ts_utc,
    state = excluded.state,
    request_id = excluded.request_id,
    correlation_id = excluded.correlation_id,
    updated_at = excluded.updated_at
""".strip()

_INSERT_CATALOG_FILE = """
INSERT INTO data_partition_files (
    file_id, dataset_id, artifact_id, relative_path, format, content_hash,
    row_count, byte_size, min_ts_utc, max_ts_utc, schema_version,
    normalization_version, source_revision, provenance_json, license_json,
    verify_state, verified_at, request_id, correlation_id, created_at, updated_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(dataset_id, relative_path) DO UPDATE SET
    artifact_id = excluded.artifact_id,
    file_id = excluded.file_id,
    format = excluded.format,
    content_hash = excluded.content_hash,
    row_count = excluded.row_count,
    byte_size = excluded.byte_size,
    min_ts_utc = excluded.min_ts_utc,
    max_ts_utc = excluded.max_ts_utc,
    schema_version = excluded.schema_version,
    normalization_version = excluded.normalization_version,
    source_revision = excluded.source_revision,
    provenance_json = excluded.provenance_json,
    license_json = excluded.license_json,
    verify_state = excluded.verify_state,
    verified_at = excluded.verified_at,
    request_id = excluded.request_id,
    correlation_id = excluded.correlation_id,
    updated_at = excluded.updated_at
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
    start, end, interval_seconds, enabled, created_at, request_id, environment,
    state, recovery_state
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'created', 'clean')
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
    """Execute one bounded Data-owned create transaction.

    Args:
        statements: The ``statements`` argument.
        parameter_sets: The ``parameter_sets`` argument.
        request_id: The ``request_id`` argument.
        max_rows: The ``max_rows`` argument.

    Returns:
        The result produced by the operation.
    """
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
    """Create one initial persisted feed-state record.

    Args:
        parameters: The ``parameters`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.
    """
    logger.debug("Creating Data feed persistence record")
    return _execute_create((_INSERT_FEED,), (parameters,), request_id=request_id)


def create_source_attempt_record(
    parameters: tuple[Any, ...], *, request_id: str
) -> TransactionResult:
    """Create one immutable source-attempt record.

    Args:
        parameters: The ``parameters`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.
    """
    logger.debug("Creating Data source-attempt persistence record")
    return _execute_create(
        (_INSERT_SOURCE_ATTEMPT,),
        (parameters,),
        request_id=request_id,
    )


def create_update_job_record(
    parameters: tuple[Any, ...], *, request_id: str
) -> TransactionResult:
    """Create one persisted update-job definition.

    Args:
        parameters: The ``parameters`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.
    """
    logger.debug("Creating Data update-job persistence record")
    return _execute_create(
        (_INSERT_UPDATE_JOB,),
        (parameters,),
        request_id=request_id,
    )


def create_backfill_checkpoint_record(
    parameters: tuple[Any, ...], *, request_id: str
) -> TransactionResult:
    """Create one prepared backfill-checkpoint record.

    Args:
        parameters: The ``parameters`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.
    """
    logger.debug("Creating Data backfill-checkpoint persistence record")
    return _execute_create(
        (_INSERT_BACKFILL_CHECKPOINT,),
        (parameters,),
        request_id=request_id,
    )


def create_research_source_record(
    parameters: tuple[Any, ...], *, request_id: str
) -> TransactionResult:
    """Create one immutable research-source revision.

    Args:
        parameters: The ``parameters`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.
    """
    logger.debug("Creating Data research-source persistence record")
    return _execute_create(
        (_INSERT_RESEARCH_SOURCE,),
        (parameters,),
        request_id=request_id,
    )


def create_research_observation_record(
    parameters: tuple[Any, ...], *, request_id: str
) -> TransactionResult:
    """Create one immutable research-observation revision.

    Args:
        parameters: The ``parameters`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.
    """
    logger.debug("Creating Data research-observation persistence record")
    return _execute_create(
        (_INSERT_RESEARCH_OBSERVATION,),
        (parameters,),
        request_id=request_id,
    )


def create_runtime_append_record(
    parameters: tuple[Any, ...], *, request_id: str
) -> TransactionResult:
    """Append one immutable namespaced runtime record.

    Args:
        parameters: The ``parameters`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.
    """
    return _execute_create(
        (_APPEND_RUNTIME_RECORD,),
        (parameters,),
        request_id=request_id,
    )


def create_runtime_put_once_record(
    parameters: tuple[Any, ...], *, request_id: str
) -> TransactionResult:
    """Create one namespaced runtime record if its identity is unused.

    Args:
        parameters: The ``parameters`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.
    """
    return _execute_create(
        (_PUT_ONCE_RUNTIME_RECORD,),
        (parameters,),
        request_id=request_id,
    )


__all__ = [
    "create_audit_event_record",
    "create_backfill_checkpoint_record",
    "create_catalog_artifact_records",
    "create_catalog_reference_records",
    "create_feed_record",
    "create_fetch_log_record",
    "create_provider_specification_revision",
    "create_quality_event_record",
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


def create_catalog_artifact_records(
    dataset_parameters: tuple[Any, ...],
    file_parameters: tuple[Any, ...],
    *,
    request_id: str,
) -> TransactionResult:
    """Register one dataset and artifact atomically.

    Args:
        dataset_parameters: The ``dataset_parameters`` argument.
        file_parameters: The ``file_parameters`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.
    """
    return _execute_create(
        (_INSERT_CATALOG_DATASET, _INSERT_CATALOG_FILE),
        (dataset_parameters, file_parameters),
        request_id=request_id,
        max_rows=2,
    )


def create_catalog_reference_records(
    provider_parameters: tuple[Any, ...],
    symbol_parameters: tuple[Any, ...],
    session_parameter_sets: tuple[tuple[Any, ...], ...],
    *,
    request_id: str,
) -> TransactionResult:
    """Synchronize one provider, symbol, and optional session set atomically.

    Args:
        provider_parameters: The ``provider_parameters`` argument.
        symbol_parameters: The ``symbol_parameters`` argument.
        session_parameter_sets: The ``session_parameter_sets`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.
    """
    statements = (
        _UPSERT_CATALOG_PROVIDER,
        _UPSERT_CATALOG_SYMBOL,
        *(_UPSERT_CATALOG_SESSION for _ in session_parameter_sets),
    )
    parameters = (provider_parameters, symbol_parameters, *session_parameter_sets)
    return _execute_create(
        statements,
        parameters,
        request_id=request_id,
        max_rows=max(2, len(statements)),
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


def create_provider_specification_revision(
    parameters: tuple[Any, ...], *, request_id: str
) -> TransactionResult:
    """Insert one immutable provider-specification revision.

    Args:
        parameters: Ordered revision column values.
        request_id: Caller trace identity.

    Returns:
        Committed transaction evidence.
    """
    logger.info("Registering initial provider specification revision")
    return _execute_create(
        (_INSERT_PROVIDER_SPECIFICATION_REVISION,),
        (parameters,),
        request_id=request_id,
    )
