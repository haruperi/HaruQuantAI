"""Update operations for Data-owned database records."""

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

_CLOSE_PROVIDER_SPECIFICATION_REVISION = """
UPDATE data_provider_specification_revisions
SET effective_to = ?
WHERE revision_id = ? AND effective_to IS NULL AND effective_from < ?
""".strip()
_INSERT_PROVIDER_SPECIFICATION_REVISION = """
INSERT INTO data_provider_specification_revisions (
    revision_id, broker, server, environment, account_digest, provider_symbol,
    snapshot_checksum, observed_at, effective_from, effective_to,
    retrieval_provenance, historical_provenance_json, payload_json,
    supersedes_revision_id, request_id, created_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""".strip()

_PUT_CACHE_ENTRY = """
INSERT OR REPLACE INTO data_cache (
    key, dataset_json, created_at, expires_at, source_revision,
    raw_data_hash, schema_version, normalization_version, request_id
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
""".strip()

_UPSERT_ECONOMIC_EVENT = """
INSERT INTO data_economic_events (
    event_id, title, country, scheduled_at, original_scheduled_at, impact,
    actual, forecast, previous, revised_previous, provider, source_url,
    first_seen_at, updated_at, request_id, provider_definition_id
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT (event_id) DO UPDATE SET
    title = excluded.title,
    country = excluded.country,
    scheduled_at = excluded.scheduled_at,
    original_scheduled_at = data_economic_events.original_scheduled_at,
    actual = COALESCE(excluded.actual, data_economic_events.actual),
    forecast = COALESCE(excluded.forecast, data_economic_events.forecast),
    previous = COALESCE(excluded.previous, data_economic_events.previous),
    revised_previous = COALESCE(
        excluded.revised_previous, data_economic_events.revised_previous
    ),
    provider = excluded.provider,
    source_url = excluded.source_url,
    provider_definition_id = COALESCE(
        excluded.provider_definition_id,
        data_economic_events.provider_definition_id
    ),
    impact = excluded.impact,
    updated_at = excluded.updated_at,
    request_id = excluded.request_id
""".strip()

_UPSERT_ECONOMIC_COVERAGE = """
INSERT INTO data_economic_calendar_coverage (
    provider, range_start, range_end, status, source_revision,
    synchronized_at, request_id
) VALUES (?, ?, ?, ?, ?, ?, ?)
ON CONFLICT (provider, range_start, range_end) DO UPDATE SET
    status = excluded.status,
    source_revision = excluded.source_revision,
    synchronized_at = excluded.synchronized_at,
    request_id = excluded.request_id
""".strip()
_UPSERT_ECONOMIC_EVENT_DEFINITION = """
INSERT INTO data_economic_event_definitions (
    provider, provider_definition_id, country, title, source_url,
    source_original, source_latest, measures, effect, frequency, also_called,
    event_type, first_seen_at, created_at, last_verified_at, request_id
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT (provider, provider_definition_id) DO UPDATE SET
    country = excluded.country,
    title = excluded.title,
    source_url = CASE
        WHEN length(excluded.source_url) > length(
            data_economic_event_definitions.source_url
        ) THEN excluded.source_url
        ELSE data_economic_event_definitions.source_url
    END,
    source_original = COALESCE(
        excluded.source_original,
        data_economic_event_definitions.source_original
    ),
    source_latest = COALESCE(
        excluded.source_latest,
        data_economic_event_definitions.source_latest
    ),
    measures = COALESCE(excluded.measures, data_economic_event_definitions.measures),
    effect = COALESCE(excluded.effect, data_economic_event_definitions.effect),
    frequency = COALESCE(
        excluded.frequency,
        data_economic_event_definitions.frequency
    ),
    also_called = COALESCE(
        excluded.also_called,
        data_economic_event_definitions.also_called
    ),
    event_type = COALESCE(
        excluded.event_type,
        data_economic_event_definitions.event_type
    ),
    last_verified_at = excluded.last_verified_at,
    request_id = excluded.request_id
""".strip()
_RECONCILE_ECONOMIC_EVENT_DEFINITIONS = """
UPDATE data_economic_events
SET provider_definition_id = (
        SELECT MIN(d.provider_definition_id)
        FROM data_economic_event_definitions d
        WHERE d.provider = 'forexfactory'
          AND d.country = data_economic_events.country
          AND d.title = data_economic_events.title
    ),
    source_url = (
        SELECT MIN(d.source_url)
        FROM data_economic_event_definitions d
        WHERE d.provider = 'forexfactory'
          AND d.country = data_economic_events.country
          AND d.title = data_economic_events.title
    )
WHERE (
      SELECT COUNT(*) FROM data_economic_event_definitions d
      WHERE d.provider = 'forexfactory'
        AND d.country = data_economic_events.country
        AND d.title = data_economic_events.title
  ) = 1
""".strip()
_UPDATE_FEED = """
UPDATE data_feeds SET
    state = ?, heartbeat_at = ?, last_event_at = ?, buffer_depth = ?,
    dropped_count = ?, gap_count = ?, reconnect_count = ?, breaker_state = ?,
    breaker_opened_at = ?, drift_ms = ?, last_error = ?, updated_at = ?
WHERE feed_id = ?
""".strip()
_UPSERT_SOURCE_STATE = """
INSERT INTO data_source_state (
    source_id, readiness, descriptor_revision, updated_at_ns, request_id
) VALUES (?, ?, ?, ?, ?)
ON CONFLICT(source_id) DO UPDATE SET
    readiness = excluded.readiness,
    descriptor_revision = excluded.descriptor_revision,
    updated_at_ns = excluded.updated_at_ns,
    request_id = excluded.request_id
""".strip()
_INSERT_SOURCE_PROMOTION_AUDIT = """
INSERT INTO data_audit_events (
    event_id, timestamp, domain, action, principal_id,
    request_id, correlation_id, causation_id, payload_json
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
""".strip()
_START_UPDATE_JOB = (
    "UPDATE data_update_jobs SET enabled = 1, state = 'created' WHERE job_id = ?"
)
_STOP_UPDATE_JOB = """
UPDATE data_update_jobs
SET enabled = 0, state = 'stopped', lease_owner = NULL, lease_expires_at = NULL
WHERE job_id = ?
""".strip()
_ACQUIRE_JOB_RUN_LEASE = """
UPDATE data_update_jobs
SET state = 'running', lease_owner = ?, lease_expires_at = ?
WHERE job_id = ?
""".strip()
_ACQUIRE_BACKFILL_LEASE = """
UPDATE data_update_jobs
SET state = 'running', lease_owner = ?, lease_expires_at = ?
WHERE job_id = ? AND (
    state != 'running' OR lease_owner = ? OR lease_expires_at IS NULL
    OR lease_expires_at <= ?
)
""".strip()
_MARK_BACKFILL_FAILURE = """
UPDATE data_update_jobs
SET last_run_status = 'failed', last_error = ?, recovery_state = 'required'
WHERE job_id = ?
""".strip()
_FINALIZE_BACKFILL_CHECKPOINT = """
UPDATE data_backfill_checkpoints
SET checkpoint = ?, publication_state = 'committed'
WHERE idempotency_key = ? AND publication_state = 'prepared'
""".strip()
_FINALIZE_BACKFILL_JOB = """
UPDATE data_update_jobs
SET last_run_status = 'succeeded', last_checkpoint = ?, last_error = NULL,
    recovery_state = 'clean', lease_owner = NULL, lease_expires_at = NULL
WHERE job_id = ?
""".strip()
_COMPLETE_UPDATE_JOB_RUN = """
UPDATE data_update_jobs
SET state = 'stopped', last_run_status = 'succeeded', last_checkpoint = ?,
    last_error = NULL, next_run_at = ?, lease_owner = NULL,
    lease_expires_at = NULL
WHERE job_id = ?
""".strip()
_FAIL_UPDATE_JOB_RUN = """
UPDATE data_update_jobs
SET state = 'failed', last_run_status = 'failed', last_error = ?,
    lease_owner = NULL, lease_expires_at = NULL
WHERE job_id = ?
""".strip()
_BLOCK_UPDATE_JOB_RECOVERY = """
UPDATE data_update_jobs
SET state = 'blocked', recovery_state = 'blocked',
    last_error = 'CHECKPOINT_CORRUPTED', lease_owner = NULL,
    lease_expires_at = NULL
WHERE job_id = ?
""".strip()
_UPSERT_VERIFIED_RESEARCH_SOURCE = """
INSERT INTO data_verified_research_sources (
    source_id, parser_version, verified_at, external_record_id,
    fixture_sha256, environments_json, license_policy
) VALUES (?, ?, ?, ?, ?, ?, ?)
ON CONFLICT (source_id, parser_version) DO UPDATE SET
    verified_at = excluded.verified_at,
    external_record_id = excluded.external_record_id,
    fixture_sha256 = excluded.fixture_sha256,
    environments_json = excluded.environments_json,
    license_policy = excluded.license_policy
""".strip()
_UPSERT_RUNTIME_RECORD = """
INSERT INTO data_runtime_records (
    namespace, collection_name, record_key, partition_key, sequence_number,
    codec_kind, payload_json, revision
) VALUES (?, ?, ?, '', 0, ?, ?, 1)
ON CONFLICT(namespace, collection_name, record_key) DO UPDATE SET
    codec_kind = excluded.codec_kind,
    payload_json = excluded.payload_json,
    revision = data_runtime_records.revision + 1
""".strip()
_COMPARE_AND_SWAP_RUNTIME_RECORD = """
UPDATE data_runtime_records
SET codec_kind = ?, payload_json = ?, revision = revision + 1
WHERE namespace = ? AND collection_name = ? AND record_key = ? AND revision = ?
""".strip()
_INSERT_RUNTIME_TRANSITION_STATE = """
INSERT OR IGNORE INTO data_runtime_records (
    namespace, collection_name, record_key, partition_key, sequence_number,
    codec_kind, payload_json, revision
) VALUES (?, ?, ?, '', 0, ?, ?, 1)
""".strip()
_UPDATE_RUNTIME_TRANSITION_STATE = _COMPARE_AND_SWAP_RUNTIME_RECORD
_APPEND_RUNTIME_TRANSITION_EVENT = """
INSERT INTO data_runtime_records (
    namespace, collection_name, record_key, partition_key, sequence_number,
    codec_kind, payload_json, revision
)
SELECT ?, ?, ?, ?, ?, ?, ?, 1 WHERE changes() = 1
""".strip()


def _execute_update(
    statements: tuple[str, ...],
    parameter_sets: tuple[tuple[Any, ...], ...],
    *,
    request_id: str,
    max_rows: int = 1,
) -> TransactionResult:
    """Execute one bounded Data-owned update transaction.

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


def update_cache_record(
    parameters: tuple[Any, ...], *, request_id: str
) -> TransactionResult:
    """Upsert one versioned cache record.

    Args:
        parameters: The ``parameters`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.
    """
    logger.debug("Updating Data cache persistence record")
    return _execute_update(
        (_PUT_CACHE_ENTRY,),
        (parameters,),
        request_id=request_id,
    )


def update_economic_event_records(
    parameter_sets: tuple[tuple[Any, ...], ...], *, request_id: str
) -> TransactionResult:
    """Upsert a bounded group of economic-event records atomically.

    Args:
        parameter_sets: The ``parameter_sets`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.
    """
    logger.debug("Updating Data economic-event persistence records")
    return _execute_update(
        tuple(_UPSERT_ECONOMIC_EVENT for _ in parameter_sets),
        parameter_sets,
        request_id=request_id,
        max_rows=max(1, len(parameter_sets)),
    )


def update_economic_calendar_coverage_record(
    parameters: tuple[Any, ...], *, request_id: str
) -> TransactionResult:
    """Upsert one explicit Economic Calendar coverage interval.

    Args:
        parameters: The ``parameters`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.
    """
    logger.debug("Updating Data economic-calendar coverage")
    return _execute_update(
        (_UPSERT_ECONOMIC_COVERAGE,), (parameters,), request_id=request_id
    )


def update_economic_event_definition_record(
    parameters: tuple[Any, ...], *, request_id: str
) -> TransactionResult:
    """Upsert one verified Economic Calendar event definition.

    Args:
        parameters: The ``parameters`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.
    """
    logger.debug("Updating one Economic Calendar event definition")
    return _execute_update(
        (_UPSERT_ECONOMIC_EVENT_DEFINITION,), (parameters,), request_id=request_id
    )


def reconcile_economic_event_definition_records(
    *, request_id: str
) -> TransactionResult:
    """Link exact unambiguous occurrence rows to verified definitions.

    Args:
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.
    """
    logger.info("Reconciling Economic Calendar event definitions")
    return _execute_update(
        (_RECONCILE_ECONOMIC_EVENT_DEFINITIONS,),
        ((),),
        request_id=request_id,
        max_rows=100_000,
    )


def update_feed_record(
    parameters: tuple[Any, ...], *, request_id: str
) -> TransactionResult:
    """Update one persisted feed-state record.

    Args:
        parameters: The ``parameters`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.
    """
    logger.debug("Updating Data feed persistence record")
    return _execute_update((_UPDATE_FEED,), (parameters,), request_id=request_id)


def update_source_state_with_audit(
    state_parameters: tuple[Any, ...],
    audit_parameters: tuple[Any, ...],
    *,
    request_id: str,
) -> TransactionResult:
    """Atomically update source readiness and append its audit evidence.

    Args:
        state_parameters: The ``state_parameters`` argument.
        audit_parameters: The ``audit_parameters`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.
    """
    logger.debug("Updating atomic Data source-state persistence records")
    return _execute_update(
        (_UPSERT_SOURCE_STATE, _INSERT_SOURCE_PROMOTION_AUDIT),
        (state_parameters, audit_parameters),
        request_id=request_id,
    )


def update_job_start(job_id: str, *, request_id: str) -> TransactionResult:
    """Enable one persisted update job.

    Args:
        job_id: The ``job_id`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.
    """
    return _execute_update((_START_UPDATE_JOB,), ((job_id,),), request_id=request_id)


def update_job_stop(job_id: str, *, request_id: str) -> TransactionResult:
    """Stop one persisted update job and release its lease.

    Args:
        job_id: The ``job_id`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.
    """
    return _execute_update((_STOP_UPDATE_JOB,), ((job_id,),), request_id=request_id)


def update_job_run_lease(
    parameters: tuple[Any, ...], *, request_id: str
) -> TransactionResult:
    """Acquire one update-job run lease.

    Args:
        parameters: The ``parameters`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.
    """
    return _execute_update(
        (_ACQUIRE_JOB_RUN_LEASE,), (parameters,), request_id=request_id
    )


def update_backfill_lease(
    parameters: tuple[Any, ...], *, request_id: str
) -> TransactionResult:
    """Conditionally acquire or renew one backfill lease.

    Args:
        parameters: The ``parameters`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.
    """
    return _execute_update(
        (_ACQUIRE_BACKFILL_LEASE,), (parameters,), request_id=request_id
    )


def update_backfill_failure(
    error_code: str, job_id: str, *, request_id: str
) -> TransactionResult:
    """Mark one backfill job as requiring recovery.

    Args:
        error_code: The ``error_code`` argument.
        job_id: The ``job_id`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.
    """
    return _execute_update(
        (_MARK_BACKFILL_FAILURE,),
        ((error_code, job_id),),
        request_id=request_id,
    )


def update_backfill_finalization(
    final_path: str,
    idempotency_key: str,
    job_id: str,
    *,
    request_id: str,
) -> TransactionResult:
    """Atomically commit checkpoint and job success evidence.

    Args:
        final_path: The ``final_path`` argument.
        idempotency_key: The ``idempotency_key`` argument.
        job_id: The ``job_id`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.
    """
    return _execute_update(
        (_FINALIZE_BACKFILL_CHECKPOINT, _FINALIZE_BACKFILL_JOB),
        ((final_path, idempotency_key), (final_path, job_id)),
        request_id=request_id,
    )


def update_job_run_success(
    last_checkpoint: str | None,
    next_run_at: str | None,
    job_id: str,
    *,
    request_id: str,
) -> TransactionResult:
    """Persist successful update-job completion.

    Args:
        last_checkpoint: The ``last_checkpoint`` argument.
        next_run_at: The ``next_run_at`` argument.
        job_id: The ``job_id`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.
    """
    return _execute_update(
        (_COMPLETE_UPDATE_JOB_RUN,),
        ((last_checkpoint, next_run_at, job_id),),
        request_id=request_id,
    )


def update_job_run_failure(
    error_code: str, job_id: str, *, request_id: str
) -> TransactionResult:
    """Persist failed update-job completion.

    Args:
        error_code: The ``error_code`` argument.
        job_id: The ``job_id`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.
    """
    return _execute_update(
        (_FAIL_UPDATE_JOB_RUN,),
        ((error_code, job_id),),
        request_id=request_id,
    )


def update_job_recovery_blocked(job_id: str, *, request_id: str) -> TransactionResult:
    """Block one update job after unprovable checkpoint recovery.

    Args:
        job_id: The ``job_id`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.
    """
    return _execute_update(
        (_BLOCK_UPDATE_JOB_RECOVERY,),
        ((job_id,),),
        request_id=request_id,
    )


def update_verified_research_source_record(
    parameters: tuple[Any, ...], *, request_id: str
) -> TransactionResult:
    """Upsert one verified research-source manifest.

    Args:
        parameters: The ``parameters`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.
    """
    return _execute_update(
        (_UPSERT_VERIFIED_RESEARCH_SOURCE,),
        (parameters,),
        request_id=request_id,
    )


def update_runtime_upsert_record(
    parameters: tuple[Any, ...], *, request_id: str
) -> TransactionResult:
    """Upsert one namespaced runtime record and advance its revision.

    Args:
        parameters: The ``parameters`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.
    """
    return _execute_update(
        (_UPSERT_RUNTIME_RECORD,),
        (parameters,),
        request_id=request_id,
    )


def update_runtime_compare_and_swap_record(
    parameters: tuple[Any, ...], *, request_id: str
) -> TransactionResult:
    """Compare-and-swap one namespaced runtime record.

    Args:
        parameters: The ``parameters`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.
    """
    return _execute_update(
        (_COMPARE_AND_SWAP_RUNTIME_RECORD,),
        (parameters,),
        request_id=request_id,
    )


def update_runtime_transition_records(
    state_parameters: tuple[Any, ...],
    event_parameters: tuple[Any, ...],
    *,
    create_state: bool,
    request_id: str,
) -> TransactionResult:
    """Atomically CAS runtime state and append its evidence event.

    Args:
        state_parameters: The ``state_parameters`` argument.
        event_parameters: The ``event_parameters`` argument.
        create_state: The ``create_state`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.
    """
    state_statement = (
        _INSERT_RUNTIME_TRANSITION_STATE
        if create_state
        else _UPDATE_RUNTIME_TRANSITION_STATE
    )
    return _execute_update(
        (state_statement, _APPEND_RUNTIME_TRANSITION_EVENT),
        (state_parameters, event_parameters),
        request_id=request_id,
    )


def update_provider_specification_revision(
    previous_revision_id: str,
    effective_from: str,
    parameters: tuple[Any, ...],
    *,
    request_id: str,
) -> TransactionResult:
    """Atomically close one revision and insert its immutable successor.

    Args:
        previous_revision_id: Open revision being superseded.
        effective_from: Successor's inclusive effective instant.
        parameters: Ordered successor column values.
        request_id: Caller trace identity.

    Returns:
        Committed two-statement transaction evidence.
    """
    logger.info("Superseding provider specification revision")
    return _execute_update(
        (
            _CLOSE_PROVIDER_SPECIFICATION_REVISION,
            _INSERT_PROVIDER_SPECIFICATION_REVISION,
        ),
        ((effective_from, previous_revision_id, effective_from), parameters),
        request_id=request_id,
        max_rows=2,
    )


__all__ = [
    "reconcile_economic_event_definition_records",
    "update_backfill_failure",
    "update_backfill_finalization",
    "update_backfill_lease",
    "update_cache_record",
    "update_economic_calendar_coverage_record",
    "update_economic_event_definition_record",
    "update_economic_event_records",
    "update_feed_record",
    "update_job_recovery_blocked",
    "update_job_run_failure",
    "update_job_run_lease",
    "update_job_run_success",
    "update_job_start",
    "update_job_stop",
    "update_provider_specification_revision",
    "update_runtime_compare_and_swap_record",
    "update_runtime_transition_records",
    "update_runtime_upsert_record",
    "update_source_state_with_audit",
    "update_verified_research_source_record",
]
